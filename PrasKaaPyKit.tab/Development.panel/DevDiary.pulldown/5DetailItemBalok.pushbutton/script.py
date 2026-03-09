# -*- coding: utf-8 -*-
__title__ = "Select Beam Detail"
__author__ = "PyRevit Script"
__doc__ = """Mencari, menyeleksi, dan opsional mengganti tipe 3 element
Detail Item Balok (Left-I, Middle, Right-J)."""

import re
import System
from pyrevit import forms, revit, DB
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    FamilyInstance,
    BuiltInCategory,
    Transaction,
)

doc   = revit.doc
uidoc = revit.uidoc

# ── Helper ────────────────────────────────────────────────────────────────────
def safe_name(elem):
    try:
        return DB.Element.Name.GetValue(elem) or ""
    except Exception:
        return ""

def exact_beam_match(type_nm, beam_type):
    """
    Cocokkan beam_type secara exact di awal type_nm sebelum ' - '.
    Contoh: 'B1-1 - Left-I' → prefix = 'B1-1'
    Hindari 'B4-1' match ke 'B4-19'.
    """
    prefix = type_nm.split(" - ")[0].strip()
    return prefix.lower() == beam_type.strip().lower()

# ── Keyword suffix ────────────────────────────────────────────────────────────
KEYWORDS = {
    "left"   : [" - left-i"],
    "middle" : [" - middle"],
    "right"  : [" - right-j"],
}

# ── Input ─────────────────────────────────────────────────────────────────────
family_name = forms.ask_for_string(
    prompt="Masukkan nama Family Detail Item:",
    title="Select Beam Detail",
    default="Detail Penulangan Balok",
)
if not family_name:
    forms.alert("Nama Family tidak boleh kosong.", exitscript=True)

beam_type_from = forms.ask_for_string(
    prompt="Tipe ASAL (contoh: B1-1):",
    title="Select Beam Detail",
    default="B1-1",
)
if not beam_type_from:
    forms.alert("Tipe asal tidak boleh kosong.", exitscript=True)

beam_type_to = forms.ask_for_string(
    prompt="Tipe TUJUAN (kosongkan jika hanya ingin select):",
    title="Select Beam Detail",
    default="",
)

# ── Collect ───────────────────────────────────────────────────────────────────
collector = (
    FilteredElementCollector(doc)
    .OfCategory(BuiltInCategory.OST_DetailComponents)
    .OfClass(FamilyInstance)
    .ToElements()
)

# ── Filter element ASAL ───────────────────────────────────────────────────────
# group by OwnerViewId supaya bisa pilih kalau ada duplikat di multi-view
# view_groups: { view_id_int: [ (elem, role, type_nm), ... ] }
view_groups = {}

for elem in collector:
    try:
        sym = elem.Symbol
        fam = sym.Family if sym else None
        if sym is None or fam is None:
            continue
        fam_nm  = safe_name(fam)
        type_nm = safe_name(sym)
        if not fam_nm or not type_nm:
            continue
    except Exception:
        continue

    if family_name.lower() not in fam_nm.lower():
        continue

    # Exact match — prefix sebelum ' - ' harus sama persis
    if not exact_beam_match(type_nm, beam_type_from):
        continue

    type_nm_lower = type_nm.lower()
    for role, kws in KEYWORDS.items():
        if any(kw in type_nm_lower for kw in kws):
            vid = elem.OwnerViewId.IntegerValue
            if vid not in view_groups:
                view_groups[vid] = []
            view_groups[vid].append((elem, role, type_nm))
            break

if not view_groups:
    forms.alert(
        "Tidak ditemukan element '{}'.\n"
        "Pastikan nama Family dan Type sudah benar.".format(beam_type_from),
        exitscript=True,
    )

# ── Jika ada di lebih dari 1 view → minta user pilih ─────────────────────────
if len(view_groups) == 1:
    chosen_vid  = list(view_groups.keys())[0]
    matched     = view_groups[chosen_vid]
else:
    # Bangun pilihan: "NamaView  (3 element)"
    choices = {}
    for vid, elems in view_groups.items():
        vw   = doc.GetElement(DB.ElementId(vid))
        vwnm = safe_name(vw)
        label = "{} ({} element)".format(vwnm, len(elems))
        choices[label] = vid

    picked = forms.ask_for_one_item(
        list(choices.keys()),
        prompt="Ditemukan di {} view. Pilih view:".format(len(view_groups)),
        title="Select Beam Detail",
    )
    if not picked:
        import sys; sys.exit()

    chosen_vid = choices[picked]
    matched    = view_groups[chosen_vid]

# ── Validasi 3 role ───────────────────────────────────────────────────────────
found_roles   = {role for _, role, _ in matched}
missing_roles = [r for r in KEYWORDS.keys() if r not in found_roles]
if missing_roles:
    msg  = "Role berikut TIDAK ditemukan:\n"
    msg += "\n".join("  - " + r.upper() for r in missing_roles)
    msg += "\n\nLanjutkan?"
    if not forms.alert(msg, yes=True, no=True):
        import sys; sys.exit()

# ── Set selection ─────────────────────────────────────────────────────────────
id_list = System.Collections.Generic.List[DB.ElementId](
    [elem.Id for elem, _, _ in matched]
)
uidoc.Selection.SetElementIds(id_list)

# ── Ganti tipe jika ada input tipe tujuan ─────────────────────────────────────
if beam_type_to and beam_type_to.strip():
    beam_type_to = beam_type_to.strip()

    all_symbols = (
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_DetailComponents)
        .OfClass(DB.FamilySymbol)
        .ToElements()
    )

    role_to_symbol = {}
    for sym in all_symbols:
        try:
            fam    = sym.Family
            fam_nm = safe_name(fam)
            sym_nm = safe_name(sym)
            if not fam_nm or not sym_nm:
                continue
        except Exception:
            continue

        if family_name.lower() not in fam_nm.lower():
            continue

        # Exact match untuk tipe tujuan juga
        if not exact_beam_match(sym_nm, beam_type_to):
            continue

        sym_nm_lower = sym_nm.lower()
        for role, kws in KEYWORDS.items():
            if any(kw in sym_nm_lower for kw in kws):
                role_to_symbol[role] = sym
                break

    missing_target = [r for r in found_roles if r not in role_to_symbol]
    if missing_target:
        forms.alert(
            "Symbol tujuan untuk role berikut TIDAK ditemukan di tipe '{}':\n".format(beam_type_to) +
            "\n".join("  - " + r.upper() for r in missing_target) +
            "\n\nPastikan tipe '{}' sudah ada di project.".format(beam_type_to),
            exitscript=True,
        )

    with Transaction(doc, "Ganti Tipe Balok: {} -> {}".format(beam_type_from, beam_type_to)) as t:
        t.Start()
        for elem, role, _ in matched:
            if role in role_to_symbol:
                elem.ChangeTypeId(role_to_symbol[role].Id)
        t.Commit()

    lines   = ["  [{}]  {} -> {}  (ID: {})".format(
                   role, tnm, safe_name(role_to_symbol.get(role)), elem.Id.IntegerValue)
               for elem, role, tnm in matched]
    summary = "Berhasil mengganti tipe {} element:\n\n".format(len(matched))
    summary += "\n".join(lines)

else:
    lines   = ["  [{}]  {}  (ID: {})".format(role, tnm, elem.Id.IntegerValue)
               for elem, role, tnm in matched]
    summary = "Berhasil menyeleksi {} element:\n\n".format(len(matched))
    summary += "\n".join(lines)

# ── Buka owner view ───────────────────────────────────────────────────────────
owner_view      = doc.GetElement(DB.ElementId(chosen_vid))
owner_view_name = safe_name(owner_view)
summary += "\n\nMembuka view:\n  {}".format(owner_view_name)

forms.alert(summary, title="Select Beam Detail – Selesai")

uidoc.RequestViewChange(owner_view)