"""Select all Plan Region in the model"""

__title__ = "Select All Plan Regions"
__author__ = "PrasKaa Team"

from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ElementId
from Autodesk.Revit.UI import UIDocument
from System.Collections.Generic import List
from pyrevit import forms

# akses doc & uidoc
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

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