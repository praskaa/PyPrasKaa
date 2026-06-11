# -*- coding: utf-8 -*-
__title__ = 'Matching Dimension from EXR Geometry'
__author__ = 'PrasKaa'
__version__ = 'Version: 1.0'
__doc__ ="""Version: 1.0
Date    = 02.03.2026
_____________________________________________________________________
Description:
Matches structural column dimensions from a linked EXR (ETABS export) model to the
host Revit model using geometry-based matching. The tool analyzes the physical
geometry of columns in both models to find corresponding elements, then transfers
the type information (family name and type name) from the linked model to the
host elements.

This tool is useful for structural projects where column dimensions need to be
synchronized between ETABS analysis models and Revit construction models.
Specifically designed for column elements with improved matching algorithm.
_____________________________________________________________________
How-to:
1. Ensure the EXR (ETABS export) model is linked to your Revit project
2. Run this tool from the PrasKaaPyKit tab in the EXR panel under Column category
3. Select the linked EXR model from the dialog
4. Choose how to select host columns:
   - Leave empty to process all structural columns in the model
   - Or pre-select specific columns in the view before running
5. The tool will:
   - Extract geometry from all columns in the linked model
   - Match each host column to a linked column using intersection analysis
   - Transfer the type information (dimension/type name)
   - Mark unmatched elements with a comment
6. Review the results in the output panel
7. CSV report is automatically saved to Documents/PrasKaaPyKit/Matching Framing/

Note: Required family types must exist in the host model before matching.
Run "Pre-run Matching Dimension" first to check type availability.

_____________________________________________________
Last update:
- 02.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa
"""

import gc
import csv
import os
import io
from datetime import datetime

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, RevitLinkInstance, ElementId,
    Solid, BooleanOperationsUtils, BooleanOperationsType, Transaction,
    TransactionStatus, ViewType, View, GeometryInstance, FamilySymbol,
    BuiltInParameter, JoinGeometryUtils, SolidUtils, XYZ
)
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons
from pyrevit import revit, forms, script
from pyrevit.forms import ProgressBar

# --- Config ---
SCRIPT_SUBFOLDER = "Matching Framing"
BATCH_SIZE = 50
EXPORT_CSV = True

# CSV output: ~/Documents/PrasKaaPyKit/Matching Framing/
CSV_BASE_DIR = os.path.join(os.path.expanduser("~"), "Documents", "PrasKaaPyKit")

doc = revit.doc
uidoc = revit.uidoc
output = script.get_output()

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


# Tolerance in feet — tweak jika masih ada unmatched
# 0.05 ~ 1.5cm | 0.1 ~ 3cm | 0.2 ~ 6cm
INTERSECTION_TOLERANCE = 0.2


def _expand_solid(solid, tolerance):
    """Expand solid by moving each face outward by tolerance amount.
    Used as fallback when direct intersection returns no volume.
    """
    try:
        # SolidUtils.CreateTransformed with scale — simple approximation via BoundingBox inflation
        # Revit does not have native inflate, so we use the solid as-is with a small offset check
        # Instead: try Boolean with a slightly scaled copy via transform
        from Autodesk.Revit.DB import Transform
        center = solid.ComputeCentroid()
        # Scale transform slightly outward from centroid
        scale = 1.0 + tolerance  # e.g. 1.05 = 5% larger
        t = Transform.Identity
        t.Origin = center.Multiply(1 - scale)
        t.BasisX = XYZ(scale, 0, 0)
        t.BasisY = XYZ(0, scale, 0)
        t.BasisZ = XYZ(0, 0, scale)
        return SolidUtils.CreateTransformed(solid, t)
    except Exception:
        return solid


def find_best_match(host_solid, linked_beams_dict):
    """Find linked beam with largest intersection volume.
    Falls back to tolerance-expanded solid if direct intersection fails.
    """
    best, max_vol = None, 0.0

    # Pass 1: direct intersection
    no_intersect = []
    for beam_id, data in linked_beams_dict.items():
        if not data['solid']:
            continue
        try:
            inter = BooleanOperationsUtils.ExecuteBooleanOperation(
                host_solid, data['solid'], BooleanOperationsType.Intersect)
            if inter and inter.Volume > max_vol:
                max_vol = inter.Volume
                best = data['element']
            elif not inter or inter.Volume == 0:
                no_intersect.append(data)
        except Exception:
            no_intersect.append(data)

    if best:
        return best

    # Pass 2: expand host solid and retry
    try:
        expanded_host = _expand_solid(host_solid, INTERSECTION_TOLERANCE)
        for data in no_intersect:
            try:
                inter = BooleanOperationsUtils.ExecuteBooleanOperation(
                    expanded_host, data['solid'], BooleanOperationsType.Intersect)
                if inter and inter.Volume > max_vol:
                    max_vol = inter.Volume
                    best = data['element']
            except Exception:
                pass
    except Exception:
        pass

    if best:
        return best

    # Pass 3: expand BOTH host and linked solids
    try:
        expanded_host = _expand_solid(host_solid, INTERSECTION_TOLERANCE)
        for data in no_intersect:
            try:
                expanded_linked = _expand_solid(data['solid'], INTERSECTION_TOLERANCE)
                inter = BooleanOperationsUtils.ExecuteBooleanOperation(
                    expanded_host, expanded_linked, BooleanOperationsType.Intersect)
                if inter and inter.Volume > max_vol:
                    max_vol = inter.Volume
                    best = data['element']
            except Exception:
                pass
    except Exception:
        pass

    return best


# ─── Type Info (cross-document safe) ───────────────────────────────────────────

def _safe_name(elem):
    """Get element name via parameters — avoids AttributeError on linked-doc FamilySymbol (Revit 2024+)."""
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
        btype = beam.Document.GetElement(type_id)
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
    """Returns matching FamilySymbol. Pass 1: exact family+type. Pass 2: type name only."""
    symbols = FilteredElementCollector(host_doc).OfClass(FamilySymbol).ToElements()
    # Pass 1: exact family name + type name
    for sym in symbols:
        try:
            sym_type = _safe_name(sym)
            sym_family = sym.Family.Name if (hasattr(sym, 'Family') and sym.Family) else None
            if sym_family == family_name and sym_type == type_name:
                return sym
        except Exception:
            pass
    # Pass 2: type name only (handles different family names between host and linked)
    for sym in symbols:
        try:
            sym_type = _safe_name(sym)
            if sym_type == type_name:
                return sym
        except Exception:
            pass
    return None


# ─── Collection ────────────────────────────────────────────────────────────────

def collect_host_beams():
    sel_ids = uidoc.Selection.GetElementIds()
    if sel_ids:
        beams = []
        for i in sel_ids:
            elem = doc.GetElement(i)
            if elem and elem.Category:
                beams.append(elem)
        if not beams:
            forms.alert("Pilih elemen Structural Framing terlebih dahulu.", exitscript=True)
        return beams
    return list(FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType().ToElements())


def collect_linked_beams(link_doc):
    return list(FilteredElementCollector(link_doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType().ToElements())


def select_linked_model():
    links = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()
    if not links:
        forms.alert("Tidak ada Revit link.", exitscript=True)
    link_dict = {l.Name: l for l in links}
    name = forms.SelectFromList.show(sorted(link_dict), title='Pilih Linked EXR Model',
                                     button_name='Select', multiselect=False)
    link = link_dict.get(name) if name else None
    if not link:
        forms.alert("Tidak ada link yang dipilih.", exitscript=True)
    link_doc = link.GetLinkDocument()
    if not link_doc:
        forms.alert("Tidak dapat mengakses dokumen link.", exitscript=True)
    return link_doc


# ─── Transfer ──────────────────────────────────────────────────────────────────

def unjoin_beam(beam):
    for jid in JoinGeometryUtils.GetJoinedElements(doc, beam):
        try:
            j = doc.GetElement(jid)
            if j and JoinGeometryUtils.AreElementsJoined(doc, beam, j):
                JoinGeometryUtils.UnjoinGeometry(doc, beam, j)
        except Exception:
            pass


def set_comment(beam, text):
    p = beam.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    if p and not p.IsReadOnly:
        p.Set(text)


def transfer_type(host_beam, linked_info):
    """Returns (success, old_info, new_info, reason)."""
    if not linked_info:
        return False, None, None, "No type info from linked beam"

    old_info = get_type_info(host_beam)
    type_name = linked_info['type_name']

    # Already correct — no change needed
    if old_info and old_info['type_name'] == type_name:
        set_comment(host_beam, "Dimension Matched (Already Correct)")
        return True, old_info, linked_info, ""

    # Find target symbol in host doc (by host family first, then type name only)
    host_family = old_info['family_name'] if old_info else linked_info['family_name']
    sym = find_family_symbol(doc, host_family, type_name)

    if sym:
        unjoin_beam(host_beam)
        host_beam.ChangeTypeId(sym.Id)
        set_comment(host_beam, "Change Dimension Type")
        return True, old_info, linked_info, ""

    reason = "Type '{}' not found in family '{}'".format(type_name, host_family)
    return False, old_info, linked_info, reason


def process_batch(matches_batch):
    successful, failed = [], []
    for host_beam, linked_beam in matches_batch:
        try:
            linked_info = get_type_info(linked_beam)
            ok, old_info, new_info, reason = transfer_type(host_beam, linked_info)
            (successful if ok else failed).append((host_beam, linked_beam, old_info, new_info, reason))
        except Exception as e:
            failed.append((host_beam, linked_beam, None, None, str(e)))
    return successful, failed


# ─── CSV Export ────────────────────────────────────────────────────────────────

def export_csv(successful, failed, unmatched):
    try:
        folder = os.path.join(CSV_BASE_DIR, SCRIPT_SUBFOLDER)
        if not os.path.exists(folder):
            os.makedirs(folder)
        safe_title = "".join(c for c in doc.Title if c.isalnum() or c in (" ", "-", "_")).strip()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = "MatchingDimension_{}_{}_{}.csv".format(
            safe_title,
            ts[:8],   # date: 20260225
            ts[9:]    # time: 122226 (strip the underscore between date and time)
        )
        path = os.path.join(folder, filename)
        with io.open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['Category', 'Host ID', 'Old Type', 'New Type', 'Linked ID', 'Family', 'Status', 'Reason'])
            for hb, lb, oi, ni, reason in successful:
                w.writerow(['Successful', hb.Id,
                            oi['type_name'] if oi else 'N/A',
                            ni['type_name'] if ni else 'N/A',
                            lb.Id, ni['family_name'] if ni else 'N/A', 'SUCCESS', reason])
            for hb, lb, oi, ni, reason in failed:
                w.writerow(['Failed', hb.Id,
                            oi['type_name'] if oi else 'N/A',
                            ni['type_name'] if ni else 'N/A',
                            lb.Id if lb else 'N/A',
                            ni['family_name'] if ni else 'N/A', 'FAILED', reason])
            for b in unmatched:
                try:
                    bname = _safe_name(b) or str(b.Id)
                except Exception:
                    bname = str(b.Id)
                w.writerow(['Unmatched', b.Id, bname, 'N/A', 'N/A', 'N/A', 'UNMATCHED', 'No geometric match'])
        return path
    except Exception as e:
        print("CSV Export gagal: {}".format(e))
        return None


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    link_doc = select_linked_model()
    host_beams = collect_host_beams()
    linked_beams = collect_linked_beams(link_doc)

    if not host_beams or not linked_beams:
        forms.alert("Tidak ada elemen ditemukan.", exitscript=True)

    # Cache linked beam solids
    linked_dict = {}
    with ProgressBar(title='Processing Linked Geometry ({value}/{max_value})', cancellable=True) as pb:
        for i, beam in enumerate(linked_beams):
            if pb.cancelled:
                forms.alert("Dibatalkan.", exitscript=True)
            solid = get_solid(beam)
            if solid:
                linked_dict[beam.Id] = {'element': beam, 'solid': solid}
            pb.update_progress(i + 1, len(linked_beams))

    # Match host beams to linked beams by geometry intersection
    # linked beam dapat dipakai lebih dari satu host beam (kasus duplikat/overlap)
    matches, unmatched = [], []
    matched_linked = {}  # linked_beam.Id -> linked_beam, untuk reuse pada duplikat

    with ProgressBar(title='Finding Matches ({value}/{max_value})', cancellable=True) as pb:
        for i, beam in enumerate(host_beams):
            if pb.cancelled:
                forms.alert("Dibatalkan.", exitscript=True)
            host_solid = get_solid(beam)
            match = find_best_match(host_solid, linked_dict) if host_solid else None

            if not match and host_solid:
                # Fallback: cari linked beam yang paling banyak overlap dengan host beam ini
                # menggunakan linked beam yang sudah pernah dipakai (kasus duplikat host)
                best_reuse, max_vol = None, 0.0
                for linked_id, linked_beam in matched_linked.items():
                    linked_solid = linked_dict.get(linked_id, {}).get('solid')
                    if not linked_solid:
                        continue
                    try:
                        expanded_host = _expand_solid(host_solid, INTERSECTION_TOLERANCE)
                        expanded_linked = _expand_solid(linked_solid, INTERSECTION_TOLERANCE)
                        inter = BooleanOperationsUtils.ExecuteBooleanOperation(
                            expanded_host, expanded_linked, BooleanOperationsType.Intersect)
                        if inter and inter.Volume > max_vol:
                            max_vol = inter.Volume
                            best_reuse = linked_beam
                    except Exception:
                        pass
                if best_reuse:
                    match = best_reuse

            if match:
                matched_linked[match.Id] = match
                matches.append((beam, match))
            else:
                unmatched.append(beam)

            pb.update_progress(i + 1, len(host_beams))

    if not matches:
        forms.alert("Tidak ada beam yang cocok ditemukan.", exitscript=True)

    # Transfer types in a single transaction
    successful, failed = [], []
    num_batches = (len(matches) + BATCH_SIZE - 1) // BATCH_SIZE
    t = Transaction(doc, 'Transfer Beam Types')
    t.Start()

    try:
        for beam in unmatched:
            set_comment(beam, "Unmatched")

        with ProgressBar(title='Transferring Types ({value}/{max_value})', cancellable=True) as pb:
            processed = 0
            for i in range(num_batches):
                if pb.cancelled:
                    t.RollBack()
                    forms.alert("Dibatalkan. Semua perubahan di-rollback.", exitscript=True)
                batch = matches[i * BATCH_SIZE:(i + 1) * BATCH_SIZE]
                s, f = process_batch(batch)
                successful.extend(s)
                failed.extend(f)
                processed += len(batch)
                pb.update_progress(processed, len(matches))

        if t.Commit() != TransactionStatus.Committed:
            forms.alert("Gagal menyimpan perubahan.", exitscript=True)

    except Exception as e:
        t.RollBack()
        forms.alert("Error: {}. Semua perubahan di-rollback.".format(e), exitscript=True)
    finally:
        linked_dict.clear()
        gc.collect()

    csv_path = export_csv(successful, failed, unmatched) if EXPORT_CSV else None

    output.print_md("## Results Summary")
    output.print_md("- **Matched:** {}".format(len(matches)))
    output.print_md("- **Successful:** {}".format(len(successful)))
    output.print_md("- **Failed:** {}".format(len(failed)))
    output.print_md("- **Unmatched:** {}".format(len(unmatched)))
    if csv_path:
        output.print_md("- **CSV:** {}".format(csv_path))


    TaskDialog.Show("Selesai",
                    "Berhasil: {} | Gagal: {} | Unmatched: {}".format(
                        len(successful), len(failed), len(unmatched)),
                    TaskDialogCommonButtons.Ok)


if __name__ == '__main__':
    main()