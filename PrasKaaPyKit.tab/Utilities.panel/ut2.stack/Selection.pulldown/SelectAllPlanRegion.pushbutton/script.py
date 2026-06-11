# -*- coding: utf-8 -*-
'''
Version: 1.0
Date    = 04.03.2026
_____________________________________________________________________
Description:
Selects all Plan Region elements in the current model and highlights
them in the selection. Useful for batch operations on Plan Regions.
_____________________________________________________________________
How-to:
1. Click "Select All Plan Regions"
2. All Plan Regions in the model will be selected
3. Use Revit selection commands as needed

Notes:
- Works on all Plan Regions in the model (not just active view)
- Displays toast notification with count of selected elements

_____________________________________________________
Last update:
- 04.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa Team
'''

__title__ = "Select All Plan Regions"
__author__ = "PrasKaa Team"
__version__ = "1.0"

from pyrevit import revit, DB, forms
from System.Collections.Generic import List

doc = revit.doc
uidoc = revit.uidoc

# collect semua Plan Region
plan_regions = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlanRegion).WhereElementIsNotElementType().ToElements()

# bikin .NET List[ElementId]
plan_region_ids = List[ElementId]([pr.Id for pr in plan_regions])

# select semua Plan Region di Revit
uidoc.Selection.SetElementIds(plan_region_ids)

forms.toast(
    "Jumlah Plan Region terseleksi: {}".format(plan_region_ids.Count),
    title="Plan Region Info",
    appid="PrasKaaPyKit"
)
