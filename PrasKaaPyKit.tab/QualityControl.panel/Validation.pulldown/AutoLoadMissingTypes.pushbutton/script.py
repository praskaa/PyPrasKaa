# -*- coding: utf-8 -*-
__title__ = 'Auto Load Missing Types'
__author__ = 'PrasKaa'
__version__ = 'Version: 1.0'
__doc__ ="""Version: 1.0
Date    = 03.03.2026
_____________________________________________________________________
Description:
Automatically loads missing structural family types from a linked EXR (ETABS export)
model into the host Revit model. This tool handles two scenarios:

1. Missing families: Exports the family from the linked model and loads it into
   the host model using temporary .rfa files
2. Missing types: Creates new types in existing families by duplicating existing
   types and copying parameter values from the linked model

This tool works together with the Pre-run Matching Dimension tool to prepare
the host model for dimension matching from ETABS models.
_____________________________________________________________________
How-to:
1. Ensure the EXR (ETABS export) model is linked to your Revit project
2. Run this tool from the PrasKaaPyKit tab under Quality Control > Validation
3. Select the linked EXR model from the dialog
4. The tool will automatically:
   - Scan structural framing and column elements in the linked model
   - Compare used family types against available types in host model
   - Identify missing families and missing types within existing families
   - Load missing families from the linked model
   - Create missing types by duplicating existing types and copying parameters
5. Review the results in the output panel showing:
   - Families loaded successfully or failed
   - Types created or skipped (if already exist)
6. After completion, run the Matching Dimension tool to match element dimensions

Tip: Run "Pre-run Matching Dimension" first to preview which types are missing
before loading them.

_____________________________________________________
Last update:
- 02.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa
"""

import os
import tempfile
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, RevitLinkInstance,
    FamilySymbol, Family, BuiltInParameter, Transaction, TransactionStatus,
    StorageType
)
from pyrevit import revit, forms, script

doc = revit.doc
output = script.get_output()


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _safe_name(elem):
    """Get element name via parameters (cross-document safe, IronPython/Revit 2024+)."""
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


def _safe_family_name(elem):
    """Get family name from a FamilySymbol (cross-document safe)."""
    try:
        if hasattr(elem, 'Family') and elem.Family:
            return elem.Family.Name
    except Exception:
        pass
    return None


# ─── Selection ─────────────────────────────────────────────────────────────────

def select_linked_model():
    links = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()
    if not links:
        forms.alert("Tidak ada Revit link ditemukan.", exitscript=True)
    link_dict = {l.Name: l for l in links}
    name = forms.SelectFromList.show(sorted(link_dict), title='Pilih Linked EXR Model',
                                     button_name='Select', multiselect=False)
    link = link_dict.get(name) if name else None
    if not link:
        forms.alert("Tidak ada link dipilih.", exitscript=True)
    link_doc = link.GetLinkDocument()
    if not link_doc:
        forms.alert("Tidak dapat mengakses dokumen link.", exitscript=True)
    return link_doc, link


# ─── Type Collection ───────────────────────────────────────────────────────────

def get_used_types_from_linked(link_doc):
    """Returns set of (family_name, type_name) used in linked model's structural elements."""
    used = set()
    for cat in [BuiltInCategory.OST_StructuralFraming, BuiltInCategory.OST_StructuralColumns]:
        elems = FilteredElementCollector(link_doc).OfCategory(cat)\
            .WhereElementIsNotElementType().ToElements()
        for elem in elems:
            try:
                btype = link_doc.GetElement(elem.GetTypeId())
                if not btype:
                    continue
                type_name = _safe_name(btype)
                family_name = _safe_family_name(btype)
                if type_name and family_name:
                    used.add((family_name, type_name))
            except Exception:
                pass
    return used


def get_available_types_in_host():
    """Returns set of (family_name, type_name) available in host model."""
    available = set()
    symbols = FilteredElementCollector(doc).OfClass(FamilySymbol).ToElements()
    for sym in symbols:
        try:
            type_name = _safe_name(sym)
            family_name = _safe_family_name(sym)
            if type_name and family_name:
                available.add((family_name, type_name))
        except Exception:
            pass
    return available


def _normalize(name):
    """Normalize family name for fuzzy matching: lowercase, replace -/space with _."""
    return name.lower().replace("-", "_").replace(" ", "_")


def get_host_families():
    """Returns dict of family_name -> Family for all families in host."""
    result = {}
    for fam in FilteredElementCollector(doc).OfClass(Family).ToElements():
        try:
            result[fam.Name] = fam
        except Exception:
            pass
    return result


def find_host_family(host_families, linked_family_name):
    """Find matching host family using exact then normalized name matching."""
    # Exact match first
    if linked_family_name in host_families:
        return linked_family_name, host_families[linked_family_name]
    # Fuzzy match: normalize both sides
    norm_linked = _normalize(linked_family_name)
    for host_name, host_fam in host_families.items():
        if _normalize(host_name) == norm_linked:
            return host_name, host_fam
    return None, None


def get_symbols_by_family(doc_to_search, family_name):
    """Returns list of FamilySymbol in a given family."""
    symbols = FilteredElementCollector(doc_to_search).OfClass(FamilySymbol).ToElements()
    return [s for s in symbols if _safe_family_name(s) == family_name]


# ─── Load Family ───────────────────────────────────────────────────────────────

def load_family_from_linked(link_doc, family_name, debug_log):
    """
    Exports family from linked doc to temp .rfa then loads into host.
    Returns (success, message). Appends debug info to debug_log list.
    """
    # Find family in linked doc
    target = None
    for fam in FilteredElementCollector(link_doc).OfClass(Family).ToElements():
        try:
            if fam.Name == family_name:
                target = fam
                break
        except Exception:
            pass

    if not target:
        return False, "Family '{}' tidak ditemukan di linked model".format(family_name)

    # Check already loaded
    for fam in FilteredElementCollector(doc).OfClass(Family).ToElements():
        try:
            if fam.Name == family_name:
                return False, "Family '{}' sudah ada di host".format(family_name)
        except Exception:
            pass

    temp_path = None
    try:
        temp_path = os.path.join(
            tempfile.gettempdir(),
            "{}.rfa".format(family_name.replace(' ', '_').replace('-', '_'))
        )
        family_doc = doc.EditFamily(target)
        if not family_doc:
            return False, "Gagal membuka family editor untuk '{}'".format(family_name)

        debug_log.append("[{}] family_doc.Title: {}".format(family_name, family_doc.Title))
        debug_log.append("[{}] temp_path: {}".format(family_name, temp_path))

        family_doc.SaveAs(temp_path)
        family_doc.Close(False)

        file_exists = os.path.exists(temp_path)
        file_size = os.path.getsize(temp_path) if file_exists else 0
        debug_log.append("[{}] file exists={} size={} bytes".format(family_name, file_exists, file_size))

        with Transaction(doc, "Load Family: {}".format(family_name)) as t:
            t.Start()
            ok = doc.LoadFamily(temp_path)
            debug_log.append("[{}] LoadFamily result: {}".format(family_name, ok))
            if ok:
                t.Commit()
                return True, "Berhasil load family '{}'".format(family_name)
            else:
                t.RollBack()
                # LoadFamily returns False jika family sudah ada di host
                # Gunakan overload dengan IFamilyLoadOptions untuk force reload
                pass

        # Retry dengan IFamilyLoadOptions untuk override existing family
        class FamilyLoadOptions(object):
            def OnFamilyFound(self, familyInUse, overwriteParameterValues):
                overwriteParameterValues = True
                return True  # overwrite
            def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
                overwriteParameterValues = True
                return True

        with Transaction(doc, "Load Family (override): {}".format(family_name)) as t2:
            t2.Start()
            try:
                ok2 = doc.LoadFamily(temp_path, FamilyLoadOptions())
                debug_log.append("[{}] LoadFamily (override) result: {}".format(family_name, ok2))
                if ok2:
                    t2.Commit()
                    return True, "Berhasil load family '{}' (override)".format(family_name)
                else:
                    # Cek apakah sudah ada di host
                    for fam in FilteredElementCollector(doc).OfClass(Family).ToElements():
                        try:
                            if fam.Name == family_name:
                                t2.Commit()
                                debug_log.append("[{}] sudah ada di host".format(family_name))
                                return False, "Family '{}' sudah ada di host model".format(family_name)
                        except Exception:
                            pass
                    t2.RollBack()
                    return False, "LoadFamily() return False untuk '{}'".format(family_name)
            except Exception as e2:
                t2.RollBack()
                return False, "Error override load: {}".format(str(e2))

    except Exception as e:
        return False, "Error: {}".format(str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


# ─── Create Type ───────────────────────────────────────────────────────────────

def copy_parameters(source_sym, target_sym):
    """Copies writable parameter values from source to target FamilySymbol."""
    success, fail = 0, 0
    target_params = {p.Definition.Name: p for p in target_sym.Parameters}

    for sp in source_sym.Parameters:
        try:
            if sp.IsReadOnly or not sp.HasValue:
                continue
            tp = target_params.get(sp.Definition.Name)
            if not tp or tp.IsReadOnly:
                continue
            st = sp.StorageType
            if st == StorageType.Double:
                tp.Set(sp.AsDouble())
            elif st == StorageType.Integer:
                tp.Set(sp.AsInteger())
            elif st == StorageType.String:
                tp.Set(sp.AsString())
            elif st == StorageType.ElementId:
                tp.Set(sp.AsElementId())
            success += 1
        except Exception:
            fail += 1

    return success, fail


def create_missing_type(family_name, type_name, link_doc, linked_family_name=None):
    """
    Duplicates an existing host type and copies parameters from linked model.
    Returns (ok, skipped, message).
      ok=True, skipped=False → berhasil dibuat
      ok=True, skipped=True  → sudah ada, tidak perlu dibuat
      ok=False, skipped=False → gagal
    """
    host_symbols = get_symbols_by_family(doc, family_name)
    if not host_symbols:
        return False, False, "Tidak ada type template di family '{}' untuk diduplikat".format(family_name)

    # Type already exists → skip, not a failure
    for sym in host_symbols:
        if _safe_name(sym) == type_name:
            return True, True, "Type '{}' sudah ada, dilewati".format(type_name)

    # Find source symbol in linked doc
    source_sym = None
    for search_name in [n for n in [linked_family_name, family_name] if n]:
        linked_symbols = get_symbols_by_family(link_doc, search_name)
        source_sym = next((s for s in linked_symbols if _safe_name(s) == type_name), None)
        if source_sym:
            break

    if not source_sym:
        return False, False, "Type '{}' tidak ditemukan di linked model".format(type_name)

    try:
        with Transaction(doc, "Create Type: {}".format(type_name)) as t:
            t.Start()
            new_sym = host_symbols[0].Duplicate(type_name)
            if not new_sym:
                t.RollBack()
                return False, False, "Gagal menduplikat type di family '{}'".format(family_name)
            success_count, fail_count = copy_parameters(source_sym, new_sym)
            t.Commit()
        return True, False, "Berhasil buat type '{}' ({} param copied, {} failed)".format(
            type_name, success_count, fail_count)
    except Exception as e:
        return False, False, "Error: {}".format(str(e))


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    link_doc, selected_link = select_linked_model()

    # Step 1: Find what's missing
    used = get_used_types_from_linked(link_doc)
    available = get_available_types_in_host()
    host_families = get_host_families()

    missing = used - available  # set of (family_name, type_name) not in host

    if not missing:
        forms.alert("Semua type sudah tersedia di host model. Tidak ada yang perlu diload.",
                    title="Up to Date")
        return

    # Categorize: missing family vs missing type only
    # Use fuzzy matching to handle name differences (- vs _, spaces, etc.)
    missing_families = set()
    missing_types = []  # (host_family_name, type_name, linked_family_name)

    for family_name, type_name in sorted(missing):
        host_name, _ = find_host_family(host_families, family_name)
        if host_name is None:
            # Family truly missing — needs to be loaded
            missing_families.add(family_name)
        else:
            # Family exists under different name — just create the type
            missing_types.append((host_name, type_name, family_name))

    output.print_md("## Auto Load Missing Types")
    output.print_md("**Linked model:** {}".format(selected_link.Name))
    output.print_md("**Missing families (truly missing):** {}".format(len(missing_families)))
    output.print_md("**Missing types (family exists):** {}".format(len(missing_types)))
    output.print_md("---")

    # Step 2: Load truly missing families
    debug_log = []
    family_results = []
    for family_name in sorted(missing_families):
        ok, msg = load_family_from_linked(link_doc, family_name, debug_log)
        family_results.append((family_name, ok, msg))

    # Step 3: Create missing types (using correct host family name)
    type_results = []
    for host_family_name, type_name, linked_family_name in missing_types:
        ok, skipped, msg = create_missing_type(host_family_name, type_name, link_doc, linked_family_name)
        type_results.append((host_family_name, type_name, ok, skipped, msg))

    # Report — semua output SETELAH semua transaksi selesai
    if family_results:
        output.print_md("## Family Loading")
        output.print_table(
            [[n, "✅ OK" if ok else "⏭ SKIP" if "sudah ada" in msg else "❌ FAIL", msg]
             for n, ok, msg in family_results],
            title="Families",
            columns=["Family Name", "Status", "Message"]
        )

    if type_results:
        output.print_md("## Type Creation")
        output.print_table(
            [[fn, tn,
              "⏭ SKIP" if skipped else "✅ OK" if ok else "❌ FAIL",
              msg]
             for fn, tn, ok, skipped, msg in type_results],
            title="Types",
            columns=["Family", "Type", "Status", "Message"]
        )

    if debug_log:
        output.print_md("## Debug Log")
        for line in debug_log:
            print(line)

    # Count only real failures (not skipped)
    family_fail = sum(1 for _, ok, msg in family_results if not ok and "sudah ada" not in msg)
    type_fail   = sum(1 for _, _, ok, skipped, _ in type_results if not ok and not skipped)
    type_new    = sum(1 for _, _, ok, skipped, _ in type_results if ok and not skipped)
    total_fail  = family_fail + type_fail

    output.print_md("---")
    output.print_md("**Type baru dibuat: {}  |  Gagal: {}**".format(type_new, total_fail))

    if total_fail == 0:
        forms.alert("Selesai! {} type baru berhasil dibuat.\n\nSilakan jalankan Matching Dimension.".format(type_new),
                    title="Sukses")
    else:
        forms.alert("{} type baru dibuat.\n{} operasi gagal.\n\nCek output untuk detail.".format(
            type_new, total_fail), title="Partial Success")


if __name__ == '__main__':
    main()