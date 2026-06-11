# -*- coding: utf-8 -*-
__title__ = 'Matching Dimension from EXR Geometry'
__author__ = 'PrasKaa'
__version__ = 'Version: 2.0'
__doc__ = """Version: 2.0
Date    = 21.03.2026
_____________________________________________________________________
Description:
Matches structural beam dimensions from a linked EXR (ETABS export)
model to the host Revit model using 3-pass geometry intersection.
Transfers the family type from the linked model to the host element
when dimensions differ. If dimensions already match, the element is
stamped Approved without modification.

Status values written to Comments parameter:
  Approved          — match found, dimensions already match, no change made
  Dimension Changed — match found, type successfully updated from linked model
  Family Mismatch   — match found but geometry types differ (e.g. circular vs rectangular)
  Type Not Found    — match found but linked type does not exist in host document
  Unmatched         — no geometric match found across all passes
_____________________________________________________________________
How-to:
1. Ensure the EXR model is linked to your Revit project
2. Optionally pre-select specific structural framing elements
3. Run the script and select the linked EXR model
4. Review the Comments parameter on each beam and the CSV output
5. A 3D issues view is automatically created for problematic beams
6. For "Type Not Found" beams: load the required family type into the
   host document, then re-run the script
_____________________________________________________________________
Last update:
- 02.03.2026 - 1.0  Initial Release
- 21.03.2026 - 2.0  Full refactor:
                     · get_solid() with GeometryInstance handling
                     · find_best_match() 3-pass geometric matching
                     · Dimension check moved to main() — determines
                       Approved vs transfer flow
                     · get_beam_dimensions() + compare_dimensions()
                       + get_geometry_type() adopted from CheckFraming
                     · Status values consistent: Approved, Dimension Changed,
                       Family Mismatch, Type Not Found, Unmatched
                     · Category.Id cross-version fix (name-based check)
                     · Transaction pattern: try/except RollBack + finally gc.collect()
                     · Console output trimmed — full detail in CSV
                     · 3D issues view with color-coded status

                     
_____________________________________________________________________
Author: PrasKaa
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
    FamilySymbol,
    JoinGeometryUtils,
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

SCRIPT_SUBFOLDER   = "Matching Framing"
CSV_BASE_DIR       = os.path.join(os.path.expanduser("~"), "Documents", "PrasKaaPyKit")
CREATE_ISSUES_VIEW = True
BATCH_SIZE         = 50

# Solid expansion tolerance ~6 cm
INTERSECTION_TOLERANCE = 0.2

# Status values — consistent across CheckFraming, MatchingFraming, TransferMark
STATUS_APPROVED          = "Approved"
STATUS_DIM_CHANGED       = "Dimension Changed"
STATUS_FAMILY_MISMATCH   = "Family Mismatch"
STATUS_TYPE_NOT_FOUND    = "Type Not Found"
STATUS_UNMATCHED         = "Unmatched"

# 3D issues view color map
COLOR_MAP = {
    STATUS_UNMATCHED      : Color(255, 0,   0),    # red
    STATUS_FAMILY_MISMATCH: Color(255, 165, 0),    # orange
    STATUS_TYPE_NOT_FOUND : Color(148, 103, 189),  # purple
    STATUS_DIM_CHANGED    : Color(55,  138, 221),  # blue
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


# ─── Dimension helpers ─────────────────────────────────────────────────────────

def get_beam_dimensions(beam):
    """
    Extract b / h dimension parameters from a beam (Revit internal feet).
    Checks instance level first, then type level.
    Returns {'b': float, 'h': float, 'type': 'rectangular'|'square'} or None.
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


# ─── Safe name helpers ─────────────────────────────────────────────────────────

def _safe_name(elem):
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
    """Returns {'type_name', 'family_name'} atau None. Aman untuk host dan linked beam."""
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


def find_family_symbol(host_doc, family_name, type_name):
    """
    Cari FamilySymbol di host doc.
    Pass 1: exact family + type name.
    Pass 2: type name saja (handle perbedaan nama family).
    """
    symbols = FilteredElementCollector(host_doc).OfClass(FamilySymbol).ToElements()
    for sym in symbols:
        try:
            sym_type   = _safe_name(sym)
            sym_family = sym.Family.Name if (hasattr(sym, 'Family') and sym.Family) else None
            if sym_family == family_name and sym_type == type_name:
                return sym
        except Exception:
            pass
    for sym in symbols:
        try:
            if _safe_name(sym) == type_name:
                return sym
        except Exception:
            pass
    return None


# ─── 3-pass geometric matching ─────────────────────────────────────────────────

def find_best_match(host_solid, linked_beams_dict):
    """
    3-pass geometric matching dengan geometry type check di tiap pass.
    Dimension check TIDAK dilakukan di sini — dilakukan di main()
    setelah match ditemukan untuk menentukan Approved vs transfer.

    Pass 1: direct intersection + geometry type check
    Pass 2: expand host solid
    Pass 3: expand host dan linked solid

    Returns (best_match Element atau None, host_geom_type str)
    """
    best        = None
    max_vol     = 0.0
    no_match_1  = []

    # Pass 1: direct
    for data in linked_beams_dict.values():
        if not data['solid']:
            continue
        try:
            inter = BooleanOperationsUtils.ExecuteBooleanOperation(
                host_solid, data['solid'], BooleanOperationsType.Intersect)
            vol = inter.Volume if inter else 0.0
        except Exception:
            vol = 0.0

        if vol == 0.0:
            no_match_1.append(data)
            continue

        if vol > max_vol:
            max_vol = vol
            best    = data['element']

    if best:
        return best

    # Pass 2: expand host
    try:
        exp_host = _expand_solid(host_solid, INTERSECTION_TOLERANCE)
    except Exception:
        exp_host = host_solid

    no_match_2 = []
    for data in no_match_1:
        try:
            inter = BooleanOperationsUtils.ExecuteBooleanOperation(
                exp_host, data['solid'], BooleanOperationsType.Intersect)
            vol = inter.Volume if inter else 0.0
        except Exception:
            vol = 0.0

        if vol == 0.0:
            no_match_2.append(data)
            continue

        if vol > max_vol:
            max_vol = vol
            best    = data['element']

    if best:
        return best

    # Pass 3: expand keduanya
    for data in no_match_2:
        try:
            exp_linked = _expand_solid(data['solid'], INTERSECTION_TOLERANCE)
            inter = BooleanOperationsUtils.ExecuteBooleanOperation(
                exp_host, exp_linked, BooleanOperationsType.Intersect)
            vol = inter.Volume if inter else 0.0
        except Exception:
            vol = 0.0

        if vol > max_vol:
            max_vol = vol
            best    = data['element']

    return best


# ─── Type transfer helpers ─────────────────────────────────────────────────────

def unjoin_beam(beam):
    """Unjoin all joined elements before calling ChangeTypeId."""
    for jid in JoinGeometryUtils.GetJoinedElements(doc, beam):
        try:
            j = doc.GetElement(jid)
            if j and JoinGeometryUtils.AreElementsJoined(doc, beam, j):
                JoinGeometryUtils.UnjoinGeometry(doc, beam, j)
        except Exception:
            pass


def set_comment(beam, text):
    """Set the Comments parameter via BuiltInParameter — cross-version safe."""
    p = beam.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    if p and not p.IsReadOnly:
        p.Set(text)


# ─── Collection helpers ────────────────────────────────────────────────────────

def select_linked_model():
    links = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()
    if not links:
        forms.alert("No Revit links found in the current project.", exitscript=True)
    link_dict = {l.Name: l for l in links}
    name = forms.SelectFromList.show(
        sorted(link_dict.keys()),
        title='Select Source Linked EXR Model (from ETABS)',
        button_name='Select',
        multiselect=False
    )
    link = link_dict.get(name) if name else None
    if not link:
        forms.alert("No link selected.", exitscript=True)
    link_doc = link.GetLinkDocument()
    if not link_doc:
        forms.alert("Could not access the linked document. Ensure it is loaded.", exitscript=True)
    return link_doc


def collect_host_beams():
    """
    Pakai pre-selected elements kalau ada, fallback ke semua structural framing.
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
        forms.alert("No structural framing elements found in the host model.", exitscript=True)
    return all_beams


def collect_linked_beams(link_doc):
    return list(
        FilteredElementCollector(link_doc)
        .OfCategory(BuiltInCategory.OST_StructuralFraming)
        .WhereElementIsNotElementType()
        .ToElements()
    )


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
        filename = 'MatchingFraming_{}_{}.csv'.format(safe_title, ts)
        path     = os.path.join(folder, filename)

        with io.open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow([
                'Host Beam ID', 'Linked Beam ID',
                'Host Family', 'Host Type',
                'Linked Family', 'Linked Type',
                'Old Type', 'New Type',
                'Status', 'Note'
            ])
            for r in results:
                w.writerow([
                    r.get('host_id'),
                    r.get('linked_id'),
                    r.get('host_family'),
                    r.get('host_type'),
                    r.get('linked_family'),
                    r.get('linked_type'),
                    r.get('old_type'),
                    r.get('new_type'),
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
    Buat 3D view dengan warna per status:
      Merah  — Unmatched
      Oranye — Family Mismatch
      Ungu   — Type Not Found
      Biru   — Dimension Changed (informasi)
    Approved disembunyikan.
    """
    try:
        vft = _find_3d_view_type()
        if not vft:
            logger.warning('No 3D view type found — issues view skipped.')
            return None

        ts        = datetime.now().strftime('%Y%m%d_%H%M%S')
        view_name = 'MATCHING FRAMING - Issues Only {}'.format(ts)

        with Transaction(doc, 'Create Matching Framing Issues View') as t:
            t.Start()
            try:
                new_view      = View3D.CreateIsometric(doc, vft.Id)
                new_view.Name = view_name

                solid_pat = get_solid_fill_pattern(doc) if get_solid_fill_pattern else None

                approved_ids = List[ElementId]()

                for row in results:
                    status = row.get('status', '')
                    id_str = row.get('host_id', '')
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
    link_doc = select_linked_model()

    # Step 2 — collect elements
    host_beams   = collect_host_beams()
    linked_beams = collect_linked_beams(link_doc)

    if not linked_beams:
        forms.alert("No structural framing elements found in the linked model.", exitscript=True)

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

    logger.info('Linked beam cache: {}/{} with valid geometry'.format(len(linked_dict), len(linked_beams)))

    # Step 4 — match and transfer in a single transaction
    counts = {
        STATUS_APPROVED       : 0,
        STATUS_DIM_CHANGED    : 0,
        STATUS_FAMILY_MISMATCH: 0,
        STATUS_TYPE_NOT_FOUND : 0,
        STATUS_UNMATCHED      : 0,
    }
    results = []

    t = Transaction(doc, 'Match Beam Dimensions from EXR')
    t.Start()
    try:
        with ProgressBar(title='Matching Beams ({value}/{max_value})',
                         cancellable=True) as pb:
            for i, host_beam in enumerate(host_beams):
                if pb.cancelled:
                    t.RollBack()
                    forms.alert("Cancelled. All changes have been rolled back.", exitscript=True)

                host_info = get_type_info(host_beam)
                row = {
                    'host_id'      : str(host_beam.Id),
                    'linked_id'    : None,
                    'host_family'  : host_info.get('family_name') if host_info else None,
                    'host_type'    : host_info.get('type_name')   if host_info else None,
                    'linked_family': None,
                    'linked_type'  : None,
                    'old_type'     : host_info.get('type_name')   if host_info else None,
                    'new_type'     : None,
                    'status'       : None,
                    'note'         : None,
                }

                host_solid = get_solid(host_beam)
                if not host_solid:
                    row['status'] = STATUS_UNMATCHED
                    row['note']   = 'Failed to extract host solid geometry'
                    set_comment(host_beam, STATUS_UNMATCHED)
                    counts[STATUS_UNMATCHED] += 1
                    results.append(row)
                    pb.update_progress(i + 1, len(host_beams))
                    continue

                best = find_best_match(host_solid, linked_dict)

                if not best:
                    row['status'] = STATUS_UNMATCHED
                    row['note']   = 'No geometric match found'
                    set_comment(host_beam, STATUS_UNMATCHED)
                    counts[STATUS_UNMATCHED] += 1
                    results.append(row)
                    pb.update_progress(i + 1, len(host_beams))
                    continue

                row['linked_id'] = str(best.Id)
                linked_info      = get_type_info(best)
                if linked_info:
                    row['linked_family'] = linked_info.get('family_name')
                    row['linked_type']   = linked_info.get('type_name')

                # Check geometry type consistency
                host_geom_type   = get_geometry_type(host_beam)
                linked_geom_type = get_geometry_type(best)
                if host_geom_type != linked_geom_type:
                    row['status'] = STATUS_FAMILY_MISMATCH
                    row['note']   = 'Geometry type: {} vs {}'.format(
                        host_geom_type, linked_geom_type)
                    set_comment(host_beam, STATUS_FAMILY_MISMATCH)
                    counts[STATUS_FAMILY_MISMATCH] += 1
                    results.append(row)
                    pb.update_progress(i + 1, len(host_beams))
                    continue

                # Check dimensions — determines Approved vs transfer
                host_dims   = get_beam_dimensions(host_beam)
                linked_dims = get_beam_dimensions(best)

                if compare_dimensions(host_dims, linked_dims):
                    # Dimensions already match — no transfer needed
                    row['status']   = STATUS_APPROVED
                    row['new_type'] = row['old_type']
                    row['note']     = 'Dimensi sudah sama'
                    set_comment(host_beam, STATUS_APPROVED)
                    counts[STATUS_APPROVED] += 1
                    results.append(row)
                    pb.update_progress(i + 1, len(host_beams))
                    continue

                # Dimensions differ — find type in host doc and transfer
                if not linked_info:
                    row['status'] = STATUS_TYPE_NOT_FOUND
                    row['note']   = 'Type info not available from linked beam'
                    set_comment(host_beam, STATUS_TYPE_NOT_FOUND)
                    counts[STATUS_TYPE_NOT_FOUND] += 1
                    results.append(row)
                    pb.update_progress(i + 1, len(host_beams))
                    continue

                host_family_name  = row['host_family'] or linked_info['family_name']
                linked_type_name  = linked_info['type_name']
                sym = find_family_symbol(doc, host_family_name, linked_type_name)

                if not sym:
                    row['status'] = STATUS_TYPE_NOT_FOUND
                    row['note']   = 'Type "{}" not found in host document'.format(linked_type_name)
                    set_comment(host_beam, STATUS_TYPE_NOT_FOUND)
                    counts[STATUS_TYPE_NOT_FOUND] += 1
                    results.append(row)
                    pb.update_progress(i + 1, len(host_beams))
                    continue

                # Perform type transfer
                try:
                    unjoin_beam(host_beam)
                    host_beam.ChangeTypeId(sym.Id)
                    row['status']   = STATUS_DIM_CHANGED
                    row['new_type'] = linked_type_name
                    row['note']     = 'Type diupdate'
                    set_comment(host_beam, STATUS_DIM_CHANGED)
                    counts[STATUS_DIM_CHANGED] += 1
                except Exception as e:
                    row['status'] = STATUS_TYPE_NOT_FOUND
                    row['note']   = 'ChangeTypeId failed: {}'.format(str(e))
                    set_comment(host_beam, STATUS_TYPE_NOT_FOUND)
                    counts[STATUS_TYPE_NOT_FOUND] += 1

                results.append(row)
                pb.update_progress(i + 1, len(host_beams))

        if t.Commit() != TransactionStatus.Committed:
            forms.alert("Failed to commit transaction.", exitscript=True)

    except Exception as e:
        t.RollBack()
        forms.alert("Error: {}. All changes have been rolled back.".format(e), exitscript=True)
    finally:
        linked_dict.clear()
        gc.collect()

    # ─── Post-commit output ────────────────────────────────────────────────────────

    csv_path = export_csv(results, doc.Title)

    output.print_md('## Matching Framing — Results')
    output.print_md('- **Total processed**: {}'.format(len(host_beams)))
    output.print_md('- **Approved**: {}'.format(counts[STATUS_APPROVED]))
    output.print_md('- **Dimension Changed**: {}'.format(counts[STATUS_DIM_CHANGED]))
    output.print_md('- **Family Mismatch**: {}'.format(counts[STATUS_FAMILY_MISMATCH]))
    output.print_md('- **Type Not Found**: {}'.format(counts[STATUS_TYPE_NOT_FOUND]))
    output.print_md('- **Unmatched**: {}'.format(counts[STATUS_UNMATCHED]))
    if csv_path:
        output.print_md('- **CSV**: {}'.format(csv_path))

    issues_view = None
    if CREATE_ISSUES_VIEW:
        issues_view = create_issues_view(results)
        if issues_view:
            output.print_md('- **3D View**: `{}`'.format(issues_view.Name))
            try:
                uidoc.RequestViewChange(issues_view)
            except Exception:
                pass

    from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons
    TaskDialog.Show(
        'Matching Framing Complete',
        'Approved        : {}\n'
        'Dim Changed     : {}\n'
        'Family Mismatch : {}\n'
        'Type Not Found  : {}\n'
        'Unmatched       : {}'.format(
            counts[STATUS_APPROVED],
            counts[STATUS_DIM_CHANGED],
            counts[STATUS_FAMILY_MISMATCH],
            counts[STATUS_TYPE_NOT_FOUND],
            counts[STATUS_UNMATCHED],
        ),
        TaskDialogCommonButtons.Ok
    )


if __name__ == '__main__':
    main()