# -*- coding: utf-8 -*-
'''
Version: 1.0
Date    = 04.03.2026
_____________________________________________________________________
Description:
Selects all Filled Region elements (excluding Masking Regions) in the
active view. Useful for batch operations on filled regions.
_____________________________________________________________________
How-to:
1. Click "Select All Filled Regions"
2. All Filled Regions in the active view will be selected
3. Use Revit selection commands as needed

Notes:
- Only selects Filled Regions, not Masking Regions
- Works only in the active view
- Displays toast notification with count of selected elements

_____________________________________________________
Last update:
- 04.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa Team
'''

__title__ = "Select All Filled Regions"
__author__ = "PrasKaa Team"
__version__ = "1.0"

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
