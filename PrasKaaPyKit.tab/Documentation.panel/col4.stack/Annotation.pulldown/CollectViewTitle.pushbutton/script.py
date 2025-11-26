# -*- coding: UTF-8 -*-
import csv
import os
import codecs
from pyrevit import forms
from Autodesk.Revit.DB import (
    FilteredElementCollector, 
    ViewPlan, 
    ViewSection, 
    ViewSchedule, 
    BuiltInParameter
)

doc = __revit__.ActiveUIDocument.Document

def collect_views(viewtype, typename):
    views = FilteredElementCollector(doc).OfClass(viewtype).ToElements()
    data = []
    for v in views:
        # Title on Sheet
        title_param = v.get_Parameter(BuiltInParameter.VIEW_DESCRIPTION)
        title = title_param.AsString() if (title_param and title_param.HasValue) else ""

        # Sub Category (View Type detail)
        subcat_param = v.get_Parameter(BuiltInParameter.VIEW_TYPE)
        subcat = subcat_param.AsString() if (subcat_param and subcat_param.HasValue) else ""

        # Referencing Sheet
        ref_sheet_param = v.get_Parameter(BuiltInParameter.VIEW_REFERENCING_SHEET)
        ref_sheet = ref_sheet_param.AsString() if (ref_sheet_param and ref_sheet_param.HasValue) else ""

        data.append((typename, v.Name, title, subcat, ref_sheet))
    return data

# Kumpulkan semua view
plan_data     = collect_views(ViewPlan, "Plan")
section_data  = collect_views(ViewSection, "Section")
schedule_data = collect_views(ViewSchedule, "Schedule")

all_data = plan_data + section_data + schedule_data

# Path file CSV
csv_path = os.path.join(os.path.expanduser("~"), "Documents", "Revit_ViewTitles.csv")

# Tulis ke CSV (pakai codecs.open untuk IronPython)
with codecs.open(csv_path, "wb", "utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["View Type", "Name", "Title", "Sub Category", "Referencing Sheet"])
    for viewtype, name, title, subcat, ref_sheet in all_data:
        writer.writerow([viewtype, name, title, subcat, ref_sheet])

# bikin dict actions
actions = {
    "📂 Buka Lokasi": os.path.dirname(csv_path),
    "📄 Buka File": csv_path
}

forms.toast(
    "✅ CSV berhasil dibuat!",
    title="Export Done",
    appid="PrasKaaPyKit",
    actions=actions
)