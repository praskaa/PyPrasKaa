# -*- coding: utf-8 -*-
# pyRevit | IronPython 2.7
# Tulis "nomor urut di Print Order" -> ke parameter sheet bernama "Number"

from __future__ import print_function
from pyrevit import forms
from Autodesk.Revit.DB import (
    FilteredElementCollector, ViewSheetSet, ViewSheet,
    Transaction, StorageType, ElementId
)

doc = __revit__.ActiveUIDocument.Document

def _get_attr(obj, names, default=None):
    for n in names:
        if hasattr(obj, n):
            return getattr(obj, n)
    return default

# --- Ambil & pilih Print Set
sets = list(FilteredElementCollector(doc).OfClass(ViewSheetSet))
if not sets:
    forms.alert("Tidak ada Print Set pada dokumen ini.", exitscript=True)

set_name = forms.SelectFromList.show([s.Name for s in sets],
                                     title='Pilih Print Set',
                                     multiselect=False)
if not set_name:
    forms.alert("Dibatalkan.", exitscript=True)

vss = next(s for s in sets if s.Name == set_name)

# --- Ambil daftar ID berurutan
ordered_ids = _get_attr(vss, [
    'OrderedViewList',    # Revit 2025
    'OrderedViewIds',     # Revit 2026+
    'OrderedViews',
    'OrderedViewIdList'
], None)

if ordered_ids is None:
    forms.alert("Build API ini tidak expose 'OrderedView*'. "
                "Tidak bisa melanjutkan.", exitscript=True)

# --- Opsi: mulai dari angka berapa?
start_at = forms.ask_for_string(default="1",
                                prompt="Mulai penomoran dari angka:",
                                title="Start Number")
try:
    start_at = int(start_at)
except:
    start_at = 1

# --- Tulis ke parameter "Number"
updated, skipped_no_param, skipped_ro = 0, 0, 0
idx = start_at - 1  # akan di-increment hanya saat ketemu Sheet

t = Transaction(doc, "Set Sheet.Parameter 'Number' from Print Order")
t.Start()

try:
    for raw in ordered_ids:
        eid = raw if isinstance(raw, ElementId) else raw.Id
        el = doc.GetElement(eid)
        if not isinstance(el, ViewSheet):
            continue  # hanya proses Sheet

        idx += 1  # nomor urut print untuk sheet ini
        p = el.LookupParameter("Number")
        if p is None:
            skipped_no_param += 1
            continue
        if p.IsReadOnly:
            skipped_ro += 1
            continue

        # Set sesuai tipe parameter
        if p.StorageType == StorageType.Integer:
            p.Set(idx)
        else:
            # Text/None/… -> set string
            p.Set(str(idx))
        updated += 1

    t.Commit()
except Exception as ex:
    t.RollBack()
    forms.alert("Gagal melakukan penulisan.\n{}".format(ex), warn_icon=True)
    raise

# --- Laporan ringkas
#msg = ("Print Set : {}\n"
#       "Mulai dari : {}\n"
#       "Updated    : {}\n"
#      "No Param   : {}\n"
#      "Read-Only  : {}"
#      ).format(vss.Name, start_at, updated, skipped_no_param, skipped_ro)
#forms.alert(msg)
#print(msg)
