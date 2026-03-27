# -*- coding: utf-8 -*-
__title__ = 'Check Framing Dimensions by EXR Geometry'
__author__ = 'PrasKaa Team'
__version__ = 'Version: 2.0'
__doc__ = """Version: 2.0
Date    = 21.03.2026
_____________________________________________________________________
Description:
Validates structural beam dimensions by comparing host model beams
against a linked EXR (ETABS export) model using 3-pass geometry
intersection. Each host beam is stamped with a validation status
in the Comments parameter.

Status values written to Comments parameter:
  Approved           — match found, dimensions already match
  Dimension Mismatch — match found but dimensions differ, or
                       dimension parameters could not be read
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
                       consistent with MatchingFraming & TransferMark
                     · Status values: Approved, Dimension Mismatch,
                       Unmatched — no geometry type check (audit only)
                     · Category.Id cross-version fix (name-based check)
                     · Transaction pattern: try/except RollBack
                       + finally gc.collect()
                     · Console output trimmed — full detail in CSV
                     · 3D issues view with color-coded status
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
    Solid,
    BooleanOperationsUtils,
    BooleanOperationsType,
    Transaction,
    TransactionStatus,
    View,
    View3D,
    ViewFamilyType,
    ViewFamily,
    ViewType,
    GeometryInstance,
    OverrideGraphicSettings,
    Color,
    BuiltInParameter,
    StorageType,
    SolidUtils,
    XYZ,
)
from System.Collections.Generic import List
from System import Int64

from pyrevit import revit, forms, script
from pyrevit.forms import ProgressBar

# Graphic overrides utility (optional)
try:
    from graphicOverrides import get_solid_fill_pattern
except ImportError:
    get_solid_fill_pattern = None

# ─── Config ────────────────────────────────────────────────────────────────────

SCRIPT_SUBFOLDER   = "Check Framing Dimensions"
CSV_BASE_DIR       = os.path.join(os.path.expanduser("~"), "Documents", "PrasKaaPyKit")
CREATE_ISSUES_VIEW = True

# Solid expansion tolerance ~6 cm
INTERSECTION_TOLERANCE = 0.2

# Status values — consistent across CheckFraming, MatchingFraming, TransferMark
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

app      = doc.Application
geo_opts = app.Create.NewGeometryOptions()
if doc.ActiveView:
    geo_opts.View = doc.ActiveView
else:
    for v in FilteredElementCollector(doc).OfClass(View):
        if not v.IsTemplate and v.ViewType == ViewType.ThreeD:
            geo_opts.View = v
            break


# ─── Geometry ──────────────────────────────────────────────────────────────────

def get_solid(element):
    """Extract the largest united solid from an element. Handles GeometryInstance nesting."""
    geom = element.get_Geometry(geo_opts)
    if not geom:
        return None
    solids = []
    for obj in geom:
        if isinstance(obj, Solid) and obj.Volume > 0:
            solids.append(obj)
        elif isinstance(obj, GeometryInstance):
            for inst_obj in obj.GetInstanceGeometry() or []:
                if isinstance(inst_obj, Solid) and inst_obj.Volume > 0:
                    solids.append(inst_obj)
    if not solids:
        return None
    result = solids[0]
    for s in solids[1:]:
        try:
            result = BooleanOperationsUtils.ExecuteBooleanOperation(
                result, s, BooleanOperationsType.Union)
        except Exception:
            pass
    return result


def _expand_solid(solid, tolerance):
    """Uniformly scale a solid outward from its centroid. Used as intersection fallback."""
    try:
        from Autodesk.Revit.DB import Transform
        center = solid.ComputeCentroid()
        scale  = 1.0 + tolerance
        t = Transform.Identity
        t.Origin = center.Multiply(1 - scale)
        t.BasisX = XYZ(scale, 0, 0)
        t.BasisY = XYZ(0, scale, 0)
        t.BasisZ = XYZ(0, 0, scale)
        return SolidUtils.CreateTransformed(solid, t)
    except Exception:
        return solid


def find_best_match(host_beam, host_solid, linked_beams_dict):
    """
    3-pass matching with geometry type check and dimension check integrated
    per pass — mirrors TransferMark pattern.

    Each pass: intersection volume > 0 AND geometry type matches AND dimensions match.
    Beams failing a pass enter no_match and are retried in the next pass with
    expanded solids. A beam with intersection but wrong geometry type or dimensions
    also enters no_match so it can be retried — but since expansion does not change
    dimensions, it will ultimately remain unmatched if no correct beam exists.

    Pass 1 — direct intersection
    Pass 2 — expand host solid
    Pass 3 — expand host and linked solid

    Returns (best_match Element or None, fail_reason str or None).
    fail_reason is the last validation failure across all passes.
    """
    host_geom_type = get_geometry_type(host_beam)
    host_dims      = get_beam_dimensions(host_beam)

    def _try_match(candidates, exp_host, expand_linked=False):
        best        = None
        max_vol     = 0.0
        no_match    = []
        last_reason = None

        for data in candidates:
            linked_solid = data['solid']
            if not linked_solid:
                continue

            ls = _expand_solid(linked_solid, INTERSECTION_TOLERANCE) \
                 if expand_linked else linked_solid

            try:
                inter = BooleanOperationsUtils.ExecuteBooleanOperation(
                    exp_host, ls, BooleanOperationsType.Intersect)
                vol = inter.Volume if inter else 0.0
            except Exception:
                vol = 0.0

            if vol == 0.0:
                no_match.append(data)
                continue

            # Intersection found — check geometry type
            linked_beam      = data['element']
            linked_geom_type = get_geometry_type(linked_beam)
            if host_geom_type != linked_geom_type:
                last_reason = STATUS_FAMILY_MISMATCH
                no_match.append(data)
                continue

            # Geometry type ok — check dimensions
            linked_dims = get_beam_dimensions(linked_beam)
            if not compare_dimensions(host_dims, linked_dims):
                last_reason = STATUS_DIM_MISMATCH
                no_match.append(data)
                continue

            # All checks passed — valid candidate
            if vol > max_vol:
                max_vol = vol
                best    = linked_beam

        return best, no_match, last_reason

    all_candidates = list(linked_beams_dict.values())

    # Pass 1: direct
    best, no_match_1, reason = _try_match(all_candidates, host_solid)
    if best:
        return best, None

    # Pass 2: expand host
    try:
        exp_host = _expand_solid(host_solid, INTERSECTION_TOLERANCE)
    except Exception:
        exp_host = host_solid
    best, no_match_2, reason = _try_match(no_match_1, exp_host)
    if best:
        return best, None

    # Pass 3: expand both
    best, _, reason = _try_match(no_match_2, exp_host, expand_linked=True)
    if best:
        return best, None

    return None, reason or STATUS_UNMATCHED


# ─── Dimension helpers ─────────────────────────────────────────────────────────

def get_beam_dimensions(beam):
    """
    Extract b / h dimension parameters from a beam (Revit internal feet).
    Checks instance level first, then type level.
    Returns {'b': float, 'h': float, 'type': 'rectangular'|'square'} or None.
    
    Enhanced with more fallback parameter names to handle various family definitions.
    """
    try:
        def _lookup(elem, names):
            for name in names:
                try:
                    p = elem.LookupParameter(name)
                    if p and p.HasValue and p.StorageType == StorageType.Double:
                        return p.AsDouble()
                except:
                    continue
            return None

        # Extended parameter name lists for better compatibility
        # These cover common naming conventions across different families
        b_param_names = ['b', 'B', 'Width', 'width', 'w', 'W', 'd', 'Depth', 'depth', 'Section Width', 'web_width']
        h_param_names = ['h', 'H', 'Height', 'height', 'd', 'Depth', 'depth', 'Section Depth', 'flange_width', 'total_depth']

        # Try BuiltInParameter first (most reliable)
        b_val = beam.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_WIDTH)
        b_val = b_val.AsDouble() if (b_val and b_val.HasValue) else None
        if b_val is None:
            b_val = _lookup(beam, b_param_names)
            if b_val is None and beam.Symbol:
                b_val = _lookup(beam.Symbol, b_param_names)

        h_val = beam.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_HEIGHT)
        h_val = h_val.AsDouble() if (h_val and h_val.HasValue) else None
        if h_val is None:
            h_val = _lookup(beam, h_param_names)
            if h_val is None and beam.Symbol:
                h_val = _lookup(beam.Symbol, h_param_names)

        # If we have b but not h, assume it's a square beam (b = h)
        # This handles cases where only one dimension is defined
        if b_val is not None and h_val is None:
            h_val = b_val  # Assume square

        if b_val is not None and h_val is not None:
            if abs(b_val - h_val) < 1e-6:
                return {'b': b_val, 'h': b_val, 'type': 'square'}
            return {'b': b_val, 'h': h_val, 'type': 'rectangular'}
        if b_val is not None:
            return {'b': b_val, 'h': b_val, 'type': 'square'}
        return None

    except Exception:
        return None


def compare_dimensions(host_dims, linked_dims):
    """
    Compare beam dimensions in mm (converted from internal feet).
    Tolerance: 0.01 mm. Returns True if dimensions match within tolerance.
    """
    if not host_dims or not linked_dims:
        return False
    if host_dims.get('type') != linked_dims.get('type'):
        return False

    try:
        from Autodesk.Revit.DB import UnitUtils, UnitTypeId
        def to_mm(v):
            return UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.Millimeters)
    except ImportError:
        def to_mm(v):
            return v * 304.8

    tol = 0.01

    if host_dims['type'] == 'square':
        hb = host_dims.get('b')
        lb = linked_dims.get('b')
        if hb is None or lb is None:
            return False
        return abs(to_mm(hb) - to_mm(lb)) <= tol

    if host_dims['type'] == 'rectangular':
        hb, hh = host_dims.get('b'), host_dims.get('h')
        lb, lh = linked_dims.get('b'), linked_dims.get('h')
        if None in [hb, hh, lb, lh]:
            return False
        return (abs(to_mm(hb) - to_mm(lb)) <= tol and
                abs(to_mm(hh) - to_mm(lh)) <= tol)

    return False



def get_geometry_type(beam):
    """
    Detect geometry type: 'circular', 'square', 'rectangular', or 'unknown'
    from family/type name. Falls back to b vs h parameter comparison.
    """
    try:
        type_id = beam.GetTypeId()
        btype   = beam.Document.GetElement(type_id)
        family_name = ''
        type_name   = ''
        if btype:
            try:
                if hasattr(btype, 'Family') and btype.Family:
                    family_name = str(btype.Family.Name).lower()
            except Exception:
                pass
            try:
                p = btype.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                type_name = str(p.AsString()).lower() if (p and p.HasValue) else ''
            except Exception:
                pass
    except Exception:
        family_name = ''
        type_name   = ''

    combined = family_name + ' ' + type_name

    for kw in ['round', 'circular', 'circle', 'pipe', 'tube', 'diameter', 'ø', 'bulat']:
        if kw in combined:
            return 'circular'
    for kw in ['square', 'box', 'kuadrat']:
        if kw in combined:
            return 'square'
    for kw in ['rectangular', 'rectangle', 'rect', 'persegi']:
        if kw in combined:
            return 'rectangular'

    dims = get_beam_dimensions(beam)
    if dims:
        return dims.get('type', 'unknown')
    return 'unknown'


# ─── Dimension formatting ──────────────────────────────────────────────────────

def _dims_to_mm_str(dims):
    """
    Convert a dims dict (internal feet) to a human-readable mm string for CSV.
    Examples:
      square      → 'b=500mm x h=500mm'  (always shows both for consistency)
      rectangular → 'b=300mm x h=600mm'
    Returns '-' if dims is None.
    """
    if not dims:
        return '-'
    try:
        from Autodesk.Revit.DB import UnitUtils, UnitTypeId
        def to_mm(v):
            return UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.Millimeters)
    except ImportError:
        def to_mm(v):
            return v * 304.8

    b = to_mm(dims.get('b', 0))
    # For square, use b value for h; for rectangular, use actual h
    h = to_mm(dims.get('h', dims.get('b', 0)))
    
    # Always show both b and h for consistency and clarity
    return 'b={:.0f}mm x h={:.0f}mm'.format(b, h)


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


# ─── Collection helpers ────────────────────────────────────────────────────────

def select_linked_model():
    """Prompts user to select a linked model. Returns (link_doc, link_instance)."""
    links = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()
    if not links:
        forms.alert("No Revit links found in the current project.", exitscript=True)
    link_dict = {l.Name: l for l in links}
    name = forms.SelectFromList.show(
        sorted(link_dict.keys()),
        title='Select Source Linked EXR Model (from ETABS)',
        button_name='Select Link',
        multiselect=False
    )
    link = link_dict.get(name) if name else None
    if not link:
        forms.alert("No link selected.", exitscript=True)
    link_doc = link.GetLinkDocument()
    if not link_doc:
        forms.alert("Could not access the linked document. Ensure it is loaded.",
                    exitscript=True)
    return link_doc, link


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

def validate_beam(host_beam, linked_beams_dict):
    """
    Validate a single host beam against the linked beam cache.

    Flow:
      1. Extract host solid
      2. find_best_match() — 3-pass with geometry type + dimension check per pass
         · returns (match, None)             → Approved
         · returns (None, Family Mismatch)   → Family Mismatch
         · returns (None, Dimension Mismatch)→ Dimension Mismatch
         · returns (None, Unmatched)         → Unmatched

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
    }

    # Capture host type name for CSV
    try:
        host_type = doc.GetElement(host_beam.GetTypeId())
        row['host_type_name'] = _safe_name(host_type) if host_type else None
    except Exception:
        pass

    # Capture host dims for CSV (always, regardless of match result)
    host_dims = get_beam_dimensions(host_beam)
    row['host_dimensions'] = _dims_to_mm_str(host_dims)

    # Step 1: extract solid
    host_solid = get_solid(host_beam)
    if not host_solid:
        row['status'] = STATUS_UNMATCHED
        row['note']   = 'Failed to extract host solid geometry'
        return STATUS_UNMATCHED, row

    # Step 2: 3-pass match with geometry type + dimension check per pass
    best, fail_reason = find_best_match(host_beam, host_solid, linked_beams_dict)

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

    linked_dims = get_beam_dimensions(best)
    row['linked_dimensions'] = _dims_to_mm_str(linked_dims)

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

        with Transaction(doc, 'Create Framing Check Issues View') as t:
            t.Start()
            try:
                new_view      = View3D.CreateIsometric(doc, vft.Id)
                new_view.Name = view_name

                solid_pat = get_solid_fill_pattern(doc) if get_solid_fill_pattern else None

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

                # Ensure linked model instances remain visible
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
                t.RollBack()
                return None

    except Exception as e:
        logger.error('Outer issues view error: {}'.format(e))
        return None


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Step 1 — select linked model
    link_doc, selected_link = select_linked_model()

    # Step 2 — collect elements
    host_beams   = collect_host_beams()
    linked_beams = collect_linked_beams(link_doc)

    if not linked_beams:
        forms.alert("No structural framing elements found in the linked model.",
                    exitscript=True)

    # Step 3 — cache linked beam solids
    linked_dict = {}
    with ProgressBar(title='Processing Linked Geometry ({value}/{max_value})',
                     cancellable=True) as pb:
        for i, beam in enumerate(linked_beams):
            if pb.cancelled:
                forms.alert("Cancelled.", exitscript=True)
            solid = get_solid(beam)
            if solid:
                linked_dict[beam.Id] = {'element': beam, 'solid': solid}
            pb.update_progress(i + 1, len(linked_beams))

    logger.info('Linked beam cache: {}/{} with valid geometry'.format(
        len(linked_dict), len(linked_beams)))

    # Step 4 — validate in a single transaction
    counts = {
        STATUS_APPROVED       : 0,
        STATUS_DIM_MISMATCH   : 0,
        STATUS_FAMILY_MISMATCH: 0,
        STATUS_UNMATCHED      : 0,
    }
    results = []

    t = Transaction(doc, 'Check Framing Dimensions')
    t.Start()
    try:
        with ProgressBar(title='Validating Beams ({value}/{max_value})',
                         cancellable=True) as pb:
            for i, host_beam in enumerate(host_beams):
                if pb.cancelled:
                    t.RollBack()
                    forms.alert("Cancelled. All changes have been rolled back.",
                                exitscript=True)

                status, row = validate_beam(host_beam, linked_dict)
                results.append(row)
                counts[status] = counts.get(status, 0) + 1
                set_comment(host_beam, status)
                pb.update_progress(i + 1, len(host_beams))

        if t.Commit() != TransactionStatus.Committed:
            forms.alert("Failed to commit transaction.", exitscript=True)

    except Exception as e:
        t.RollBack()
        forms.alert("Error: {}. All changes have been rolled back.".format(e),
                    exitscript=True)
    finally:
        linked_dict.clear()
        gc.collect()

    # ─── Post-commit output ────────────────────────────────────────────────────

    csv_path = export_csv(results, doc.Title)

    output.print_md('## Check Framing Dimensions — Results')
    output.print_md('- **Total processed**: {}'.format(len(host_beams)))
    output.print_md('- **Approved**: {}'.format(counts[STATUS_APPROVED]))
    output.print_md('- **Dimension Mismatch**: {}'.format(counts[STATUS_DIM_MISMATCH]))
    output.print_md('- **Unmatched**: {}'.format(counts[STATUS_UNMATCHED]))
    if csv_path:
        output.print_md('- **CSV**: {}'.format(csv_path))

    issues_view = None
    if CREATE_ISSUES_VIEW:
        issues_view = create_issues_view(results)
        if issues_view:
            output.print_md('- **3D View**: `{}`'.format(issues_view.Name))
            output.print_md('*Red*: Unmatched | *Orange*: Dimension Mismatch')
            try:
                uidoc.RequestViewChange(issues_view)
            except Exception:
                pass

    from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons
    TaskDialog.Show(
        'Check Framing Dimensions Complete',
        'Approved          : {}\n'
        'Dimension Mismatch: {}\n'
        'Unmatched         : {}'.format(
            counts[STATUS_APPROVED],
            counts[STATUS_DIM_MISMATCH],
            counts[STATUS_UNMATCHED],
        ),
        TaskDialogCommonButtons.Ok
    )


if __name__ == '__main__':
    main()