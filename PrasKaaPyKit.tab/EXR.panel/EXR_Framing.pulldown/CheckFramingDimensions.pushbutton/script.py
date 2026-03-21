# -*- coding: utf-8 -*-
__title__ = 'Check Framing Dimensions by EXR Geometry'
__author__ = 'PrasKaa Team'
__version__ = 'Version: 2.0'
__doc__ = """Version: 2.0
Date    = 21.03.2026
_____________________________________________________________________
Description:
Validates framing dimensions by geometry intersection and parameter comparison.
Compares structural beams in the host model against beams in a linked EXR
(ETABS export) model, then stamps each host beam's Comments parameter with
the validation status.

Status values:
  Approved               — family type & dimensions match
  Family unmatched       — geometry intersects but family geometry type differs
  Dimension to be checked — same family type but dimensions don't match /
                            parameters not found
  Unmatched              — no geometric intersection found at all
_____________________________________________________________________
How-to:
1. Ensure the EXR model is linked to your Revit project
2. Optionally pre-select specific structural framing elements
3. Run this tool
4. Select the linked EXR model from the dialog
5. Review the Comments parameter on each beam and the output panel
6. A CSV report is saved to ~/Documents/PrasKaaPyKit/Check Framing Dimensions/
   and a 3D issues view is created automatically (if CREATE_ISSUES_VIEW = True)
_____________________________________________________________________
Last update:
- 21.03.2026 - 2.0  Refactored geometry & matching system to match
                     MatchingFraming script patterns:
                     · get_solid()        — compact, no debug overhead
                     · find_best_match()  — 3-pass with solid expansion fallback
                     · _safe_name() / _safe_family_name() — crash-safe
                       cross-document name access via BuiltInParameter
                     · collect_host_beams() — simplified category check
                     · Single transaction with try/except RollBack pattern
                     · Consistent post-commit output flow
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
    Solid,
    BooleanOperationsUtils,
    BooleanOperationsType,
    Transaction,
    TransactionStatus,
    View,
    ViewType,
    View3D,
    ViewFamilyType,
    ViewFamily,
    OverrideGraphicSettings,
    Color,
    ElementId,
    Options,
    BuiltInParameter,
    StorageType,
    GeometryInstance,
    ParameterFilterElement,
    ParameterFilterRuleFactory,
    ElementParameterFilter,
    FamilySymbol,
    SolidUtils,
    XYZ
)
from System.Collections.Generic import List
from System import Int64

from pyrevit import revit, forms, script
from pyrevit.forms import ProgressBar

# Import graphic overrides utility from lib (optional)
try:
    from graphicOverrides import get_solid_fill_pattern
except ImportError:
    get_solid_fill_pattern = None

# Import CSV configuration (optional)
try:
    from matching_config import CSV_BASE_DIR, CSV_CREATE_FOLDERS
except ImportError:
    CSV_BASE_DIR = os.path.join(os.path.expanduser("~"), "Documents", "PrasKaaPyKit")
    CSV_CREATE_FOLDERS = True

# ─── Config ────────────────────────────────────────────────────────────────────

SCRIPT_SUBFOLDER = "Check Framing Dimensions"
CREATE_ISSUES_VIEW = True
ISSUES_VIEW_TRANSPARENCY = 50

# Tolerance in feet for solid expansion fallback (~6 cm)
INTERSECTION_TOLERANCE = 0.2

# ─── Setup ─────────────────────────────────────────────────────────────────────

doc   = revit.doc
uidoc = revit.uidoc
output = script.get_output()
logger = script.get_logger()

# Geometry options — prefer active view, fallback to any 3D view
app = doc.Application
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
    """Extract largest/united solid from an element. Compact, no debug overhead."""
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
    """Scale solid slightly outward from its centroid — used as intersection fallback."""
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


def find_best_match(host_solid, linked_beams_dict):
    """
    3-pass geometry matching (mirrors MatchingFraming logic):
      Pass 1 — direct intersection
      Pass 2 — expand host solid
      Pass 3 — expand both host and linked solid
    Returns the best-matching linked beam Element, or None.
    """
    best, max_vol = None, 0.0
    no_intersect = []

    # Pass 1: direct
    for beam_id, data in linked_beams_dict.items():
        if not data['solid']:
            continue
        try:
            inter = BooleanOperationsUtils.ExecuteBooleanOperation(
                host_solid, data['solid'], BooleanOperationsType.Intersect)
            vol = inter.Volume if inter else 0.0
            if vol > max_vol:
                max_vol = vol
                best = data['element']
            if vol == 0.0:
                no_intersect.append(data)
        except Exception:
            no_intersect.append(data)

    if best:
        return best

    # Pass 2: expand host
    try:
        exp_host = _expand_solid(host_solid, INTERSECTION_TOLERANCE)
        for data in no_intersect:
            try:
                inter = BooleanOperationsUtils.ExecuteBooleanOperation(
                    exp_host, data['solid'], BooleanOperationsType.Intersect)
                vol = inter.Volume if inter else 0.0
                if vol > max_vol:
                    max_vol = vol
                    best = data['element']
            except Exception:
                pass
    except Exception:
        pass

    if best:
        return best

    # Pass 3: expand both
    try:
        exp_host = _expand_solid(host_solid, INTERSECTION_TOLERANCE)
        for data in no_intersect:
            try:
                exp_linked = _expand_solid(data['solid'], INTERSECTION_TOLERANCE)
                inter = BooleanOperationsUtils.ExecuteBooleanOperation(
                    exp_host, exp_linked, BooleanOperationsType.Intersect)
                vol = inter.Volume if inter else 0.0
                if vol > max_vol:
                    max_vol = vol
                    best = data['element']
            except Exception:
                pass
    except Exception:
        pass

    return best


# ─── Safe name helpers (cross-document, mirrors MatchingFraming) ───────────────

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


def _safe_family_name(beam, btype):
    """Get family name via FamilySymbol.Family then instance parameters."""
    try:
        if hasattr(btype, 'Family') and btype.Family:
            return btype.Family.Name
    except Exception:
        pass
    for bip in [BuiltInParameter.ELEM_FAMILY_PARAM, BuiltInParameter.ALL_MODEL_FAMILY_NAME]:
        try:
            p = beam.get_Parameter(bip)
            if p and p.HasValue:
                val = p.AsString()
                if val:
                    return val
        except Exception:
            pass
    return "Unknown"


def get_type_info(beam):
    """Returns {'type_name', 'family_name'} or None. Works for both host and linked beams."""
    try:
        type_id = beam.GetTypeId()
        btype   = beam.Document.GetElement(type_id)
        if not btype:
            return None
        type_name = _safe_name(btype)
        if not type_name:
            return None
        family_name = _safe_family_name(beam, btype)
        return {'type_name': type_name, 'family_name': family_name}
    except Exception:
        return None


# ─── Dimension extraction ──────────────────────────────────────────────────────

def get_beam_dimensions(beam):
    """
    Extracts b / h parameters from a beam (in Revit internal feet).
    Returns {'b': float, 'h': float, 'type': 'rectangular'|'square'} or None.
    Checks both instance and type-level parameters.
    """
    try:
        def _lookup(elem, names):
            for name in names:
                p = elem.LookupParameter(name)
                if p and p.HasValue and p.StorageType == StorageType.Double:
                    return p.AsDouble()
            return None

        b_val = beam.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_WIDTH)
        b_val = b_val.AsDouble() if (b_val and b_val.HasValue) else None
        if b_val is None:
            b_val = _lookup(beam, ['b', 'B', 'Width'])
            if b_val is None and beam.Symbol:
                b_val = _lookup(beam.Symbol, ['b', 'B', 'Width'])

        h_val = beam.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_HEIGHT)
        h_val = h_val.AsDouble() if (h_val and h_val.HasValue) else None
        if h_val is None:
            h_val = _lookup(beam, ['h', 'H', 'Height'])
            if h_val is None and beam.Symbol:
                h_val = _lookup(beam.Symbol, ['h', 'H', 'Height'])

        if b_val is not None and h_val is not None:
            if abs(b_val - h_val) < 1e-6:
                return {'b': b_val, 'type': 'square'}
            return {'b': b_val, 'h': h_val, 'type': 'rectangular'}
        if b_val is not None:
            return {'b': b_val, 'type': 'square'}
        return None

    except Exception:
        return None


def get_geometry_type(beam):
    """
    Detects 'circular', 'square', 'rectangular', or 'unknown' from family/type name,
    falling back to parameter comparison.
    """
    info = get_type_info(beam)
    family_name = (info.get('family_name') or '').lower() if info else ''
    type_name   = (info.get('type_name')   or '').lower() if info else ''
    combined    = family_name + ' ' + type_name

    circular_kw    = ['round', 'circular', 'circle', 'pipe', 'tube', 'diameter', 'ø', 'bulat']
    square_kw      = ['square', 'box', 'kuadrat']
    rectangular_kw = ['rectangular', 'rectangle', 'rect', 'persegi']

    for kw in circular_kw:
        if kw in combined:
            return 'circular'
    for kw in square_kw:
        if kw in combined:
            return 'square'
    for kw in rectangular_kw:
        if kw in combined:
            return 'rectangular'

    # Fallback: compare b vs h from parameters
    dims = get_beam_dimensions(beam)
    if dims:
        return dims.get('type', 'unknown')
    return 'unknown'


# ─── Dimension comparison ──────────────────────────────────────────────────────

def compare_dimensions(host_dims, linked_dims):
    """
    Compares dimensions in mm (converts from internal feet first).
    Tolerance: 0.01 mm.
    Returns True if dimensions match within tolerance.
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

    tol = 0.01  # mm

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


# ─── Collection helpers ────────────────────────────────────────────────────────

def select_linked_model():
    """Prompts user to select a linked Revit model. Returns (link_doc, link_instance)."""
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
        forms.alert("Could not access the selected link document. Ensure it is loaded.", exitscript=True)
    return link_doc, link


def collect_host_beams():
    """
    Returns pre-selected structural framing elements, or ALL structural framing
    if nothing (or non-framing elements) is selected.
    Simplified — no category-ID integer comparison needed.
    """
    sel_ids = uidoc.Selection.GetElementIds()
    if sel_ids:
        beams = []
        for eid in sel_ids:
            elem = doc.GetElement(eid)
            if elem and elem.Category:
                cat_name = elem.Category.Name or ''
                # Accept anything whose category name contains "Structural Framing"
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
        forms.alert(
            "No structural framing elements found in the host model.",
            exitscript=True
        )
    return all_beams


def collect_linked_beams(link_doc):
    """Collects all structural framing elements from a linked document."""
    return list(
        FilteredElementCollector(link_doc)
        .OfCategory(BuiltInCategory.OST_StructuralFraming)
        .WhereElementIsNotElementType()
        .ToElements()
    )


# ─── Comment helper ────────────────────────────────────────────────────────────

def set_comment(beam, text):
    """Sets the ALL_MODEL_INSTANCE_COMMENTS parameter if writable."""
    p = beam.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    if p and not p.IsReadOnly:
        p.Set(text)


# ─── Per-beam validation ───────────────────────────────────────────────────────

def validate_beam(host_beam, linked_beams_dict):
    """
    Validates a single host beam against the linked beam cache.

    Returns:
        (status_str, validation_dict)
        status_str — one of: 'Approved', 'Family unmatched',
                              'Dimension to be checked', 'Unmatched'
    """
    row = {
        'host_beam_id'         : str(host_beam.Id),
        'linked_beam_id'       : None,
        'host_family_name'     : None,
        'host_type_name'       : None,
        'linked_family_name'   : None,
        'linked_type_name'     : None,
        'host_geometry_type'   : None,
        'linked_geometry_type' : None,
        'host_dimensions'      : None,
        'linked_dimensions'    : None,
        'status'               : None,
        'debug_info'           : None,
    }

    host_info = get_type_info(host_beam)
    if host_info:
        row['host_family_name'] = host_info.get('family_name')
        row['host_type_name']   = host_info.get('type_name')

    host_solid = get_solid(host_beam)
    if not host_solid:
        row['status']     = 'Unmatched'
        row['debug_info'] = 'Could not extract host solid geometry'
        return 'Unmatched', row

    best = find_best_match(host_solid, linked_beams_dict)
    if not best:
        row['status']     = 'Unmatched'
        row['debug_info'] = 'No geometric intersection found'
        return 'Unmatched', row

    row['linked_beam_id'] = str(best.Id)
    linked_info = get_type_info(best)
    if linked_info:
        row['linked_family_name'] = linked_info.get('family_name')
        row['linked_type_name']   = linked_info.get('type_name')

    # Family geometry type check
    host_geom_type   = get_geometry_type(host_beam)
    linked_geom_type = get_geometry_type(best)
    row['host_geometry_type']   = host_geom_type
    row['linked_geometry_type'] = linked_geom_type

    if host_geom_type != linked_geom_type:
        row['status']     = 'Family unmatched'
        row['debug_info'] = 'Geometry type mismatch: {} vs {}'.format(
            host_geom_type, linked_geom_type)
        return 'Family unmatched', row

    # Dimension check
    host_dims   = get_beam_dimensions(host_beam)
    linked_dims = get_beam_dimensions(best)
    row['host_dimensions']   = str(host_dims)   if host_dims   else None
    row['linked_dimensions'] = str(linked_dims) if linked_dims else None

    if not host_dims or not linked_dims:
        row['status']     = 'Dimension to be checked'
        row['debug_info'] = 'Missing dimension params — host:{} linked:{}'.format(
            'OK' if host_dims else 'FAIL',
            'OK' if linked_dims else 'FAIL')
        return 'Dimension to be checked', row

    if compare_dimensions(host_dims, linked_dims):
        row['status']     = 'Approved'
        row['debug_info'] = 'Dimensions match within tolerance'
        return 'Approved', row

    row['status']     = 'Dimension to be checked'
    row['debug_info'] = "Dimensions don't match"
    return 'Dimension to be checked', row


# ─── CSV export ────────────────────────────────────────────────────────────────

def export_csv(validation_results, doc_title):
    """Exports validation results to a timestamped CSV. Returns path or None."""
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
                'Host Family', 'Host Type',
                'Linked Family', 'Linked Type',
                'Host Geom Type', 'Linked Geom Type',
                'Host Dims', 'Linked Dims',
                'Status', 'Debug Info'
            ])
            for r in validation_results:
                w.writerow([
                    r.get('host_beam_id'),
                    r.get('linked_beam_id'),
                    r.get('host_family_name'),
                    r.get('host_type_name'),
                    r.get('linked_family_name'),
                    r.get('linked_type_name'),
                    r.get('host_geometry_type'),
                    r.get('linked_geometry_type'),
                    r.get('host_dimensions'),
                    r.get('linked_dimensions'),
                    r.get('status'),
                    r.get('debug_info'),
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


def create_issues_view(validation_results, selected_link):
    """
    Creates a 3D view highlighting problematic beams:
      Red    — Unmatched
      Orange — Family unmatched
      Yellow — Dimension to be checked
    Hides Approved beams for clarity.
    Returns the View3D or None.
    """
    try:
        vft = _find_3d_view_type()
        if not vft:
            logger.warning('No 3D view type found; skipping issues view creation.')
            return None

        ts        = datetime.now().strftime('%Y%m%d_%H%M%S')
        view_name = 'FRAMING CHECK - Issues Only {}'.format(ts)

        with Transaction(doc, 'Create Framing Issues View') as t:
            t.Start()
            try:
                new_view      = View3D.CreateIsometric(doc, vft.Id)
                new_view.Name = view_name

                # Solid fill pattern (optional — from lib)
                solid_pat = get_solid_fill_pattern(doc) if get_solid_fill_pattern else None

                # Status → color map
                status_colors = {
                    'Unmatched'              : Color(255, 0,   0),
                    'Family unmatched'       : Color(255, 165, 0),
                    'Dimension to be checked': Color(255, 255, 0),
                }

                approved_ids    = List[ElementId]()
                problematic_ids = List[ElementId]()

                for row in validation_results:
                    status   = row.get('status', '')
                    id_str   = row.get('host_beam_id', '')
                    if not id_str:
                        continue
                    try:
                        eid  = ElementId(Int64.Parse(id_str))
                        beam = doc.GetElement(eid)
                        if not beam:
                            continue

                        if status == 'Approved':
                            approved_ids.Add(eid)
                        elif status in status_colors:
                            clr      = status_colors[status]
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
                            problematic_ids.Add(eid)
                    except Exception:
                        continue

                # Hide approved beams
                if approved_ids.Count > 0:
                    try:
                        new_view.HideElements(approved_ids)
                    except Exception as e:
                        logger.warning('Could not hide approved beams: {}'.format(e))

                # Ensure linked model instances are visible
                link_ids = List[ElementId]()
                for lnk in FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements():
                    link_ids.Add(lnk.Id)
                if link_ids.Count > 0:
                    try:
                        new_view.UnhideElements(link_ids)
                    except Exception as e:
                        logger.warning('Could not unhide linked models: {}'.format(e))

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

    # Step 2 — collect beams
    host_beams   = collect_host_beams()
    linked_beams = collect_linked_beams(link_doc)

    if not linked_beams:
        forms.alert(
            'No structural framing found in the linked EXR model.',
            exitscript=True
        )

    # Step 3 — cache linked beam solids (mirrors MatchingFraming)
    linked_dict = {}
    with ProgressBar(title='Processing Linked Geometry ({value}/{max_value})',
                     cancellable=True) as pb:
        for i, beam in enumerate(linked_beams):
            if pb.cancelled:
                forms.alert('Cancelled.', exitscript=True)
            solid = get_solid(beam)
            if solid:
                linked_dict[beam.Id] = {'element': beam, 'solid': solid}
            pb.update_progress(i + 1, len(linked_beams))

    logger.info('Linked beam cache: {}/{} with valid geometry'.format(
        len(linked_dict), len(linked_beams)))

    # Step 4 — validate in a single transaction (mirrors MatchingFraming pattern)
    counts = {'Approved': 0, 'Family unmatched': 0,
              'Dimension to be checked': 0, 'Unmatched': 0}
    validation_results = []

    t = Transaction(doc, 'Validate Beam Dimensions')
    t.Start()
    try:
        with ProgressBar(title='Validating Beams ({value}/{max_value})',
                         cancellable=True) as pb:
            for i, host_beam in enumerate(host_beams):
                if pb.cancelled:
                    t.RollBack()
                    forms.alert('Cancelled. All changes rolled back.', exitscript=True)

                status, row = validate_beam(host_beam, linked_dict)
                validation_results.append(row)
                counts[status] = counts.get(status, 0) + 1
                set_comment(host_beam, status)
                pb.update_progress(i + 1, len(host_beams))

        if t.Commit() != TransactionStatus.Committed:
            forms.alert('Failed to commit changes.', exitscript=True)

    except Exception as e:
        t.RollBack()
        forms.alert('Error: {}. All changes rolled back.'.format(e), exitscript=True)
    finally:
        linked_dict.clear()
        gc.collect()

    # ─── Post-commit: output, CSV, 3D view ─────────────────────────────────────

    output.print_md('## Results Summary')
    output.print_md('- **Total processed**: {}'.format(len(host_beams)))
    output.print_md('- **Approved**: {}'.format(counts['Approved']))
    output.print_md('- **Family unmatched**: {}'.format(counts['Family unmatched']))
    output.print_md('- **Dimension to be checked**: {}'.format(counts['Dimension to be checked']))
    output.print_md('- **Unmatched**: {}'.format(counts['Unmatched']))

    csv_path = export_csv(validation_results, doc.Title)
    if csv_path:
        output.print_md('- **CSV**: {}'.format(csv_path))

    issues_view = None
    if CREATE_ISSUES_VIEW:
        issues_view = create_issues_view(validation_results, selected_link)
        if issues_view:
            output.print_md('')
            output.print_md('**3D Issues View**: `{}`'.format(issues_view.Name))
            output.print_md('*Red*: Unmatched | *Orange*: Family unmatched | *Yellow*: Dimension check needed')
            try:
                uidoc.RequestViewChange(issues_view)
            except Exception:
                pass

    from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons
    TaskDialog.Show(
        'Validation Complete',
        'Approved: {}\nFamily unmatched: {}\nDimension to be checked: {}\nUnmatched: {}'.format(
            counts['Approved'], counts['Family unmatched'],
            counts['Dimension to be checked'], counts['Unmatched']
        ),
        TaskDialogCommonButtons.Ok
    )


if __name__ == '__main__':
    main()