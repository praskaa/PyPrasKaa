# -*- coding: utf-8 -*-
__title__ = 'Check Framing Dimensions by EXR Geometry'
__author__ = 'PrasKaa Team'
__version__ = 'Version: 2.1'
__doc__ = """Version: 2.1
Date    = 21.05.2026
_____________________________________________________________________
Description:
Validates structural beam dimensions by comparing host model beams
against a linked EXR (ETABS export) model using 3-pass geometry
intersection. Each host beam is stamped with a validation status
in the Comments parameter.

Status values written to Comments parameter:
  Approved           — match found, dimensions already match
  Dimension Mismatch — match found but dimensions differ
  Family Mismatch    — match found but geometry type differs
  Unmatched          — no geometric match found across all passes
_____________________________________________________________________
How-to:
1. Ensure the EXR model is linked to your Revit project
2. Optionally pre-select specific structural framing elements
3. Run the script and select the linked EXR model
4. Review the Comments parameter on each beam and the CSV output
5. A 3D issues view is automatically created for problematic beams
_____________________________________________________________________
Last update:
- 21.03.2026 - 2.0  Full refactor:
                     · get_solid() with GeometryInstance handling
                     · find_best_match() 3-pass geometric matching
                     · get_beam_dimensions() + compare_dimensions()
                     · Status: Approved, Dimension Mismatch, Unmatched
                     · Transaction: try/except RollbackIfPending + finally gc
                     · 3D issues view with color-coded status
- 21.05.2026 - 2.1  Bug fixes (aligned with CheckColumn 3.1):
                     · Shared logic migrated to lib/exr_*.py modules
                     · exr_matching.py: 2-stage match — spatial pass first,
                       validation once on best candidate.
                       Fixes: dimension mismatch was reported as Unmatched
                     · get_geometry_type imported at module level
                     · _elem ref carried in row dict — no Int64.Parse risk
                     · RollbackIfPending() unconditional (HasStarted/HasEnded removed)
                     · create_issues_view() moved before output.print_md()
                       — fixes multiple console split
                     · Top-level try/finally — gc always runs on cancel/error/exit
_____________________________________________________________________
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
# get_geometry_type imported at module level — same fix as CheckColumn 3.1
from exr_dimensions import get_dimensions, dims_to_mm_str, get_geometry_type
from exr_matching import find_best_match
from compat import get_element_id_value

# Graphic overrides utility (optional)
try:
    from graphicOverrides import get_solid_fill_pattern
except ImportError:
    get_solid_fill_pattern = None

# ─── Config ────────────────────────────────────────────────────────────────────

SCRIPT_SUBFOLDER   = "Check Framing Dimensions"
CSV_BASE_DIR       = os.path.join(os.path.expanduser("~"), "Documents", "PrasKaaPyKit")
CREATE_ISSUES_VIEW = True

# Status values — consistent across CheckColumn, CheckFraming, MatchingFraming, TransferMark
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

def set_comment(beam, text):
    """Set the Comments parameter via BuiltInParameter — cross-version safe."""
    p = beam.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    if p and not p.IsReadOnly:
        p.Set(text)


# ─── Collection helpers (category-specific) ────────────────────────────────────

def collect_host_beams():
    """
    Return pre-selected structural framing elements, or all framing if nothing selected.
    Category check via name string — cross-version safe.
    """
    sel_ids = uidoc.Selection.GetElementIds()
    if sel_ids:
        beams = []
        for eid in sel_ids:
            elem = doc.GetElement(eid)
            if elem and elem.Category:
                cat_name = elem.Category.Name or ''
                if 'Structural Framing' in cat_name or 'StructuralFraming' in cat_name:
                    beams.append(elem)
        if beams:
            return beams

    all_beams = list(
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_StructuralFraming)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    if not all_beams:
        forms.alert("No structural framing elements found in the host model.",
                    exitscript=True)
    return all_beams


def collect_linked_beams(link_doc):
    """Collect all structural framing elements from a linked document."""
    return list(
        FilteredElementCollector(link_doc)
        .OfCategory(BuiltInCategory.OST_StructuralFraming)
        .WhereElementIsNotElementType()
        .ToElements()
    )


# ─── Per-beam validation ───────────────────────────────────────────────────────

def validate_beam(host_beam, linked_dict):
    """
    Validate a single host beam against the linked beam cache.

    Flow:
      1. Extract host solid
      2. find_best_match() — 3-pass spatial match, then single validation:
         · (match, None)          → Approved
         · (None, FamilyMismatch) → Family Mismatch
         · (None, DimMismatch)    → Dimension Mismatch
         · (None, Unmatched)      → Unmatched
    Returns (status_str, row_dict).
    """
    row = {
        'host_beam_id'     : str(host_beam.Id),
        'linked_beam_id'   : None,
        'host_type_name'   : None,
        'linked_type_name' : None,
        'host_dimensions'  : None,
        'linked_dimensions': None,
        'status'           : None,
        'note'             : None,
        # Carry element ref — avoids Int64.Parse risk in write loop
        '_elem'            : host_beam,
    }

    try:
        host_type = doc.GetElement(host_beam.GetTypeId())
        row['host_type_name'] = _safe_name(host_type) if host_type else None
    except Exception:
        pass

    # Capture host dims for CSV regardless of match result
    host_dims = get_dimensions(host_beam)
    row['host_dimensions'] = dims_to_mm_str(host_dims)

    # Step 1: extract solid
    host_solid = get_solid(host_beam, geo_opts)
    if not host_solid:
        row['status'] = STATUS_UNMATCHED
        row['note']   = 'Failed to extract host solid geometry'
        return STATUS_UNMATCHED, row

    # Step 2: 3-pass spatial match + single validation on best candidate
    # get_geometry_type is a module-level import — no inline import needed
    host_geom_type = get_geometry_type(host_beam)

    best, fail_reason = find_best_match(
        host_beam, host_solid, linked_dict, host_dims, host_geom_type)

    if not best:
        status = fail_reason or STATUS_UNMATCHED
        row['status'] = status
        row['note']   = 'No valid match found across all passes'
        return status, row

    # Match found and all checks passed → Approved
    row['linked_beam_id'] = str(best.Id)

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
        filename = 'CheckFramingDimensions_{}_{}.csv'.format(safe_title, ts)
        path     = os.path.join(folder, filename)

        with io.open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow([
                'Host Beam ID', 'Linked Beam ID',
                'Host Type', 'Linked Type',
                'Host Dims (mm)', 'Linked Dims (mm)',
                'Status', 'Note'
            ])
            for r in results:
                w.writerow([
                    r.get('host_beam_id'),
                    r.get('linked_beam_id'),
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
    """
    Create a 3D view highlighting problematic beams:
      Red    — Unmatched
      Orange — Dimension Mismatch / Family Mismatch
    Approved beams are hidden.
    Returns the View3D or None.
    """
    try:
        vft = _find_3d_view_type()
        if not vft:
            logger.warning('No 3D view type found — issues view skipped.')
            return None

        ts        = datetime.now().strftime('%Y%m%d_%H%M%S')
        view_name = 'FRAMING CHECK - Issues Only {}'.format(ts)

        t = Transaction(doc, 'Create Framing Check Issues View')
        t.Start()
        try:
            new_view      = View3D.CreateIsometric(doc, vft.Id)
            new_view.Name = view_name

            solid_pat    = get_solid_fill_pattern(doc) if get_solid_fill_pattern else None
            approved_ids = List[ElementId]()

            for row in results:
                status = row.get('status', '')
                id_str = row.get('host_beam_id', '')
                if not id_str:
                    continue
                try:
                    eid  = ElementId(Int64.Parse(str(id_str)))
                    beam = doc.GetElement(eid)
                    if not beam:
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
            # RollbackIfPending unconditional — HasStarted()/HasEnded() don't exist
            t.RollbackIfPending()
            return None

    except Exception as e:
        logger.error('Outer issues view error: {}'.format(e))
        return None


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Top-level try/finally — linked_dict.clear() + gc.collect() always runs
    # regardless of cancellation, exception, or normal completion
    linked_dict = {}
    try:
        # Step 1 — select linked model
        link_doc, selected_link = select_linked_model(doc)

        # Step 2 — collect elements
        host_beams   = collect_host_beams()
        linked_beams = collect_linked_beams(link_doc)

        if not linked_beams:
            forms.alert("No structural framing elements found in the linked model.",
                        exitscript=True)

        # Step 3 — cache linked beam solids (read-only, no transaction)
        with ProgressBar(title='Processing Linked Geometry ({value}/{max_value})',
                         cancellable=True) as pb:
            for i, beam in enumerate(linked_beams):
                if pb.cancelled:
                    forms.alert("Cancelled.", exitscript=True)
                solid = get_solid(beam, geo_opts)
                if solid:
                    linked_dict[get_element_id_value(beam.Id)] = {'element': beam, 'solid': solid}
                pb.update_progress(i + 1, len(linked_beams))

        logger.info('Linked beam cache: {}/{} with valid geometry'.format(
            len(linked_dict), len(linked_beams)))

        # Step 4 — validate (read-only, no transaction)
        counts = {
            STATUS_APPROVED       : 0,
            STATUS_DIM_MISMATCH   : 0,
            STATUS_FAMILY_MISMATCH: 0,
            STATUS_UNMATCHED      : 0,
        }
        results = []

        with ProgressBar(title='Validating Beams ({value}/{max_value})',
                         cancellable=True) as pb:
            for i, host_beam in enumerate(host_beams):
                if pb.cancelled:
                    forms.alert("Cancelled.", exitscript=True)
                status, row = validate_beam(host_beam, linked_dict)
                results.append(row)
                counts[status] = counts.get(status, 0) + 1
                pb.update_progress(i + 1, len(host_beams))

        # Step 5 — write Comments (short transaction, no output calls inside)
        t = Transaction(doc, 'Write Framing Validation Results')
        t.Start()
        try:
            for row in results:
                # Use _elem ref — no Int64.Parse risk on None/empty id_str
                beam = row.get('_elem')
                if beam:
                    set_comment(beam, row.get('status', ''))
            if t.Commit() != TransactionStatus.Committed:
                forms.alert("Failed to commit transaction.", exitscript=True)
        except Exception as e:
            # RollbackIfPending unconditional — HasStarted()/HasEnded() don't exist
            t.RollbackIfPending()
            forms.alert("Error writing results: {}".format(e), exitscript=True)

        # Step 6 — create issues view BEFORE output.print_md()
        # Issues view opens its own Transaction; all DB writes must finish
        # before any output.print_md() call to prevent console splitting
        issues_view = None
        if CREATE_ISSUES_VIEW:
            issues_view = create_issues_view(results)

        # Step 7 — export CSV (no DB writes, safe before or after output)
        csv_path = export_csv(results, doc.Title)

        # Step 8 — all DB writes done, output panel is now safe to use
        output.print_md('## Check Framing Dimensions — Results')
        output.print_md('- **Total processed**: {}'.format(len(host_beams)))
        output.print_md('- **Approved**: {}'.format(counts[STATUS_APPROVED]))
        output.print_md('- **Dimension Mismatch**: {}'.format(counts[STATUS_DIM_MISMATCH]))
        output.print_md('- **Family Mismatch**: {}'.format(counts[STATUS_FAMILY_MISMATCH]))
        output.print_md('- **Unmatched**: {}'.format(counts[STATUS_UNMATCHED]))
        if csv_path:
            output.print_md('- **CSV**: {}'.format(csv_path))
        if issues_view:
            output.print_md('- **3D View**: `{}`'.format(issues_view.Name))
            output.print_md('*Red*: Unmatched | *Orange*: Dimension / Family Mismatch')
            try:
                uidoc.RequestViewChange(issues_view)
            except Exception:
                pass

        # Step 9 — TaskDialog summary (after output, no console impact)
        from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons
        TaskDialog.Show(
            'Check Framing Dimensions Complete',
            'Approved          : {}\n'
            'Dimension Mismatch: {}\n'
            'Family Mismatch   : {}\n'
            'Unmatched         : {}'.format(
                counts[STATUS_APPROVED],
                counts[STATUS_DIM_MISMATCH],
                counts[STATUS_FAMILY_MISMATCH],
                counts[STATUS_UNMATCHED],
            ),
            TaskDialogCommonButtons.Ok
        )

    finally:
        # Always runs — cancel, error, or normal completion
        linked_dict.clear()
        gc.collect()


if __name__ == '__main__':
    main()