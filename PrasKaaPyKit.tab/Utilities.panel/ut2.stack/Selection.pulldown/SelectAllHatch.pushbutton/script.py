# coding: utf8
"""Select all Filled Region (exclude Masking Region) in active view
Show result with pyRevit forms.toast
"""

__title__ = "Select All Filled Regions"
__author__ = "PrasKaa Team"

from pyrevit import revit, DB, forms
from System.Collections.Generic import List

doc = revit.doc
uidoc = revit.uidoc
active_view = doc.ActiveView

# Kumpulkan semua DetailComponents di view aktif
collector = (DB.FilteredElementCollector(doc, active_view.Id)
             .OfCategory(DB.BuiltInCategory.OST_DetailComponents)
             .WhereElementIsNotElementType())

# Buat List[ElementId] .NET (bukan list Python biasa)
filled_region_ids = List[DB.ElementId]()

# Hanya ambil FilledRegion (exclude MaskingRegion)
for el in collector:
    if isinstance(el, DB.FilledRegion):
        filled_region_ids.Add(el.Id)

# Update selection + toast info
if filled_region_ids.Count > 0:
    uidoc.Selection.SetElementIds(filled_region_ids)
    forms.toast(
        "Jumlah Filled Region terseleksi: {}".format(filled_region_ids.Count),
        title="Filled Region Info",
        appid="PrasKaaPyKit"
    )
else:
    forms.toast(
        "Tidak ada Filled Region di view ini.",
        title="Filled Region Info",
        appid="PrasKaaPyKit"
    )
