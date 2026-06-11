# -*- coding: utf-8 -*-
__title__ = 'Check Column Dimensions by EXR Geometry'
__author__ = 'PrasKaa'
__version__ = 'Version: 3.0'
__doc__ = """Version: 3.0
Date    = 20.05.2026
_____________________________________________________________________
Description:
Validates structural column dimensions by comparing host model columns
against a linked EXR (ETABS export) model using 3-pass geometry
intersection. Each host column is stamped with a validation status
in the Comments parameter.

Status values written to Comments parameter:
  Approved           — match found, dimensions already match
  Dimension Mismatch — match found but dimensions differ, or
                       dimension parameters could not be read
  Unmatched          — no geometric match found across all passes
_____________________________________________________________________
How-to:
1. Ensure the EXR model is linked to your Revit project
2. Optionally pre-select specific structural column elements
3. Run the script and select the linked EXR model
4. Review the Comments parameter on each column and the CSV output
5. A 3D issues view is automatically created for problematic columns
_____________________________________________________________________
Last update:
- 20.05.2026 - 3.0  Major refactor:
                      · Shared logic extracted to lib/exr_*.py
                      · 3-pass geometric matching (was 1-pass)
                      · Transaction pattern: try/except RollbackIfPending + finally gc.collect()
                      · No debug output
                      · Consistent CSV headers and dimension strings
                      · Cross-version safe (compat.get_element_id_value)
- 20.05.2026 - 3.1  Bug fixes:
                      · get_geometry_type imported at module level (was broken inline import)
                      · _elem ref carried in row dict — eliminates Int64.Parse risk in write loop
                      · t.HasStarted()/HasEnded() removed — use RollbackIfPending() unconditionally
                      · create_issues_view() moved before output.print_md() — fixes multiple console split
                      · Top-level try/finally in main() — gc always runs on cancel/error/normal exit
Author: PrasKaa Team
"""

import gc
import csv
import os
import io
from datetime import datetime

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    RevitLinkInstance,
    ElementId,
    Transaction,
    TransactionStatus,
    View,
    View3D,
    ViewFamilyType,
    ViewFamily,
    ViewType,
    OverrideGraphicSettings,
    Color,
    BuiltInParameter,
)
from System.Collections.Generic import List
from System import Int64
from pyrevit import revit, forms, script
from pyrevit.forms import ProgressBar

# Shared EXR modules
from exr_collectors import select_linked_model, build_geometry_options
from exr_geometry import get_solid
# FIX 1: get_geometry_type imported here at module level — was broken inline import inside validate_column()
from exr_dimensions import get_dimensions, dims_to_mm_str, get_geometry_type
from exr_matching import find_best_match
from compat import get_element_id_value

# Graphic overrides utility (optional)
try:
    from graphicOverrides import get_solid_fill_pattern
except ImportError:
    get_solid_fill_pattern = None

# ─── Config ────────────────────────────────────────────────────────────────────

SCRIPT_SUBFOLDER   = "Check Column Dimensions"
CSV_BASE_DIR       = os.path.join(os.path.expanduser("~"), "Documents", "PrasKaaPyKit")
CREATE_ISSUES_VIEW = True

# Status values — consistent across tools
STATUS_APPROVED        = "Approved"
STATUS_DIM_MISMATCH    = "Dimension Mismatch"
STATUS_FAMILY_MISMATCH = "Family Mismatch"
STATUS_UNMATCHED       = "Unmatched"

# 3D issues view color map
COLOR_MAP = {
    STATUS_UNMATCHED       : Color(255, 0,   0),   # red
    STATUS_DIM_MISMATCH    : Color(255, 165, 0),   # orange
    STATUS_FAMILY_MISMATCH : Color(255, 165, 0),   # orange
}

# ─── Setup ─────────────────────────────────────────────────────────────────────

doc    = revit.doc
uidoc  = revit.uidoc
output = script.get_output()
logger = script.get_logger()

geo_opts = build_geometry_options(doc)

# ─── Safe name helper ──────────────────────────────────────────────────────────

def _safe_name(elem):
    """Get element/type name via BuiltInParameter — avoids AttributeError on linked-doc types."""
    for bip in [BuiltInParameter.SYMBOL_NAME_PARAM, BuiltInParameter.ALL_MODEL_TYPE_NAME]:
        try:
            p = elem.get_Parameter(bip)
            if p and p.HasValue:
                val = p.AsString()
                if val:
                    return val
        except Exception:
            pass
    try:
        return elem.Name
    except Exception:
        return None


# ─── Comment helper ────────────────────────────────────────────────────────────

def set_comment(column, text):
    """Set the Comments parameter via BuiltInParameter — cross-version safe."""
    p = column.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    if p and not p.IsReadOnly:
        p.Set(text)


# ─── Collection helpers (category-specific) ────────────────────────────────────

def collect_host_columns():
    """Return pre-selected structural columns, or all columns if nothing selected."""
    sel_ids = uidoc.Selection.GetElementIds()
    if sel_ids:
        columns = []
        for eid in sel_ids:
            elem = doc.GetElement(eid)
            if elem and elem.Category:
                cat_name = elem.Category.Name or ''
                if 'Structural Column' in cat_name or 'StructuralColumns' in cat_name:
                    columns.append(elem)
        if columns:
            return columns

    all_columns = list(
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_StructuralColumns)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    if not all_columns:
        forms.alert("No structural column elements found in the host model.",
                    exitscript=True)
    return all_columns


def collect_linked_columns(link_doc):
    """Collect all structural columns from a linked document."""
    return list(
        FilteredElementCollector(link_doc)
        .OfCategory(BuiltInCategory.OST_StructuralColumns)
        .WhereElementIsNotElementType()
        .ToElements()
    )


# ─── Per-column validation ─────────────────────────────────────────────────────

def validate_column(host_col, linked_dict):
    """Validate a single host column against the linked column cache."""
    row = {
        'host_column_id'   : str(host_col.Id),
        'linked_column_id' : None,
        'host_type_name'   : None,
        'linked_type_name' : None,
        'host_dimensions'  : None,
        'linked_dimensions': None,
        'status'           : None,
        'note'             : None,
        # FIX 2: carry element ref so main() write loop never needs Int64.Parse
        '_elem'            : host_col,
    }

    try:
        host_type = doc.GetElement(host_col.GetTypeId())
        row['host_type_name'] = _safe_name(host_type) if host_type else None
    except Exception:
        pass

    host_dims = get_dimensions(host_col)
    row['host_dimensions'] = dims_to_mm_str(host_dims)

    host_solid = get_solid(host_col, geo_opts)
    if not host_solid:
        row['status'] = STATUS_UNMATCHED
        row['note']   = 'Failed to extract host solid geometry'
        return STATUS_UNMATCHED, row

    # FIX 1 (continued): get_geometry_type is now a clean top-level import — no inline import needed
    host_geom_type = get_geometry_type(host_col)

    best, fail_reason = find_best_match(host_col, host_solid, linked_dict, host_dims, host_geom_type)

    if not best:
        status = fail_reason or STATUS_UNMATCHED
        row['status'] = status
        row['note']   = 'No valid match found across all passes'
        return status, row

    row['linked_column_id'] = str(best.Id)

    try:
        linked_type = best.Document.GetElement(best.GetTypeId())
        row['linked_type_name'] = _safe_name(linked_type) if linked_type else None
    except Exception:
        pass

    linked_dims = get_dimensions(best)
    row['linked_dimensions'] = dims_to_mm_str(linked_dims)

    row['status'] = STATUS_APPROVED
    row['note']   = 'Dimensions match within tolerance'
    return STATUS_APPROVED, row


# ─── CSV export ────────────────────────────────────────────────────────────────

def export_csv(results, doc_title):
    """Export validation results to a timestamped CSV. Returns file path or None."""
    try:
        folder = os.path.join(CSV_BASE_DIR, SCRIPT_SUBFOLDER)
        if not os.path.exists(folder):
            os.makedirs(folder)
        safe_title = ''.join(c for c in doc_title
                             if c.isalnum() or c in (' ', '-', '_')).strip()
        ts       = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = 'CheckColumnDimensions_{}_{}.csv'.format(safe_title, ts)
        path     = os.path.join(folder, filename)

        with io.open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow([
                'Host Column ID', 'Linked Column ID',
                'Host Type', 'Linked Type',
                'Host Dims (mm)', 'Linked Dims (mm)',
                'Status', 'Note'
            ])
            for r in results:
                w.writerow([
                    r.get('host_column_id'),
                    r.get('linked_column_id'),
                    r.get('host_type_name'),
                    r.get('linked_type_name'),
                    r.get('host_dimensions'),
                    r.get('linked_dimensions'),
                    r.get('status'),
                    r.get('note'),
                ])
        return path
    except Exception as e:
        logger.error('CSV export failed: {}'.format(e))
        return None


# ─── 3D issues view ────────────────────────────────────────────────────────────

def _find_3d_view_type():
    for vft in FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements():
        if vft.ViewFamily == ViewFamily.ThreeDimensional:
            return vft
    return None


def create_issues_view(results):
    """Create a 3D view highlighting problematic columns (red = Unmatched, orange = Mismatch)."""
    try:
        vft = _find_3d_view_type()
        if not vft:
            logger.warning('No 3D view type found — issues view skipped.')
            return None

        ts        = datetime.now().strftime('%Y%m%d_%H%M%S')
        view_name = 'COLUMN CHECK - Issues Only {}'.format(ts)

        t = Transaction(doc, 'Create Column Check Issues View')
        t.Start()
        try:
            new_view      = View3D.CreateIsometric(doc, vft.Id)
            new_view.Name = view_name

            solid_pat    = get_solid_fill_pattern(doc) if get_solid_fill_pattern else None
            approved_ids = List[ElementId]()

            for row in results:
                status = row.get('status', '')
                id_str = row.get('host_column_id', '')
                if not id_str:
                    continue
                try:
                    eid = ElementId(Int64.Parse(str(id_str)))
                    col = doc.GetElement(eid)
                    if not col:
                        continue

                    if status == STATUS_APPROVED:
                        approved_ids.Add(eid)
                    elif status in COLOR_MAP:
                        clr      = COLOR_MAP[status]
                        override = OverrideGraphicSettings()
                        override.SetProjectionLineColor(clr)
                        override.SetCutLineColor(clr)
                        override.SetSurfaceForegroundPatternColor(clr)
                        override.SetSurfaceBackgroundPatternColor(clr)
                        if solid_pat:
                            override.SetSurfaceForegroundPatternId(solid_pat)
                            override.SetSurfaceBackgroundPatternId(solid_pat)
                            override.SetCutForegroundPatternId(solid_pat)
                        new_view.SetElementOverrides(eid, override)
                except Exception:
                    continue

            if approved_ids.Count > 0:
                try:
                    new_view.HideElements(approved_ids)
                except Exception:
                    pass

            # Keep linked model instances visible
            link_ids = List[ElementId]()
            for lnk in FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements():
                link_ids.Add(lnk.Id)
            if link_ids.Count > 0:
                try:
                    new_view.UnhideElements(link_ids)
                except Exception:
                    pass

            t.Commit()
            return new_view

        except Exception as e:
            logger.error('Issues view creation failed: {}'.format(e))
            # FIX 3: RollbackIfPending() called unconditionally — t.HasStarted()/HasEnded() don't exist
            t.RollbackIfPending()
            return None

    except Exception as e:
        logger.error('Outer issues view error: {}'.format(e))
        return None


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    # FIX 5: top-level try/finally — linked_dict.clear() + gc.collect() always runs
    # regardless of cancellation, exception, or normal completion
    linked_dict = {}
    try:
        # Step 1 — select linked model
        link_doc, selected_link = select_linked_model(doc)

        # Step 2 — collect elements
        host_columns   = collect_host_columns()
        linked_columns = collect_linked_columns(link_doc)

        if not linked_columns:
            forms.alert("No structural column elements found in the linked model.",
                        exitscript=True)

        # Step 3 — cache linked column solids (read-only, no transaction)
        with ProgressBar(title='Processing Linked Geometry ({value}/{max_value})',
                         cancellable=True) as pb:
            for i, col in enumerate(linked_columns):
                if pb.cancelled:
                    forms.alert("Cancelled.", exitscript=True)
                solid = get_solid(col, geo_opts)
                if solid:
                    linked_dict[get_element_id_value(col.Id)] = {'element': col, 'solid': solid}
                pb.update_progress(i + 1, len(linked_columns))

        logger.info('Linked column cache: {}/{} with valid geometry'.format(
            len(linked_dict), len(linked_columns)))

        # Step 4 — validate (read-only, no transaction)
        counts = {
            STATUS_APPROVED       : 0,
            STATUS_DIM_MISMATCH   : 0,
            STATUS_FAMILY_MISMATCH: 0,
            STATUS_UNMATCHED      : 0,
        }
        results = []

        with ProgressBar(title='Validating Columns ({value}/{max_value})',
                         cancellable=True) as pb:
            for i, host_col in enumerate(host_columns):
                if pb.cancelled:
                    forms.alert("Cancelled.", exitscript=True)
                status, row = validate_column(host_col, linked_dict)
                results.append(row)
                counts[status] = counts.get(status, 0) + 1
                pb.update_progress(i + 1, len(host_columns))

        # Step 5 — write Comments (short transaction, no output calls inside)
        t = Transaction(doc, 'Write Column Validation Results')
        t.Start()
        try:
            for row in results:
                # FIX 2: use _elem ref — no Int64.Parse risk on None/empty id_str
                col = row.get('_elem')
                if col:
                    set_comment(col, row.get('status', ''))
            if t.Commit() != TransactionStatus.Committed:
                forms.alert("Failed to commit transaction.", exitscript=True)
        except Exception as e:
            # FIX 3: RollbackIfPending() unconditional — t.HasStarted()/HasEnded() don't exist
            t.RollbackIfPending()
            forms.alert("Error writing results: {}".format(e), exitscript=True)

        # FIX 4: create_issues_view() called BEFORE output.print_md()
        # — issues view opens its own Transaction; all DB writes must complete
        #   before any output.print_md() call to prevent console splitting
        issues_view = None
        if CREATE_ISSUES_VIEW:
            issues_view = create_issues_view(results)

        # Step 6 — export CSV (no DB writes, safe before or after output)
        csv_path = export_csv(results, doc.Title)

        # Step 7 — all DB writes done, output panel is now safe to use
        output.print_md('## Check Column Dimensions — Results')
        output.print_md('- **Total processed**: {}'.format(len(host_columns)))
        output.print_md('- **Approved**: {}'.format(counts[STATUS_APPROVED]))
        output.print_md('- **Dimension Mismatch**: {}'.format(counts[STATUS_DIM_MISMATCH]))
        output.print_md('- **Unmatched**: {}'.format(counts[STATUS_UNMATCHED]))
        if csv_path:
            output.print_md('- **CSV**: {}'.format(csv_path))
        if issues_view:
            output.print_md('- **3D View**: `{}`'.format(issues_view.Name))
            output.print_md('*Red*: Unmatched | *Orange*: Dimension Mismatch')
            try:
                uidoc.RequestViewChange(issues_view)
            except Exception:
                pass

        # Step 8 — TaskDialog summary (after output, no console impact)
        from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons
        TaskDialog.Show(
            'Check Column Dimensions Complete',
            'Approved          : {}\n'
            'Dimension Mismatch: {}\n'
            'Unmatched         : {}'.format(
                counts[STATUS_APPROVED],
                counts[STATUS_DIM_MISMATCH],
                counts[STATUS_UNMATCHED],
            ),
            TaskDialogCommonButtons.Ok
        )

    finally:
        # FIX 5: always runs — cancel, error, or normal completion
        linked_dict.clear()
        gc.collect()


if __name__ == '__main__':
    main()