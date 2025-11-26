# -*- coding: utf-8 -*-
"""
This script allows users to Disallow or Allow joins at the ends of
Structural Framing (Beams) in Revit.
"""
__title__ = "Disallow/Allow Joins"
__author__ = "Prasetyo"
__version__ = "1.2.0"

import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System')
clr.AddReference('System.Collections')

import Autodesk.Revit.DB
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ISelectionFilter, Selection, ObjectType
from System.Collections.Generic import List

from pyrevit import forms
from pyrevit import script
from pyrevit import revit

doc = revit.doc
uidoc = revit.uidoc

# --- Cross-Version ElementId Helper ---
def id_val(eid):
    """
    Cross-version compatible ElementId value accessor.
    Returns the integer value of the ElementId, using Value (int64) for Revit 2026+
    and IntegerValue (int32) for earlier versions.
    """
    try:
        return eid.Value
    except AttributeError:
        return eid.IntegerValue

# --- Selection Filter for Structural Framing ---
class CategoryFilterStructuralFraming(ISelectionFilter):
    def AllowElement(self, elem):
        if elem.Category.Id == ElementId(BuiltInCategory.OST_StructuralFraming):
            return True
        return False

    def AllowReference(self, refer, point):
        return False

# --- Input from PyRevit Forms ---
# Check existing selection first, then filter for valid categories
elements_to_process = []

# Get currently selected elements
selected_ids = uidoc.Selection.GetElementIds()

# Filter selected elements for valid categories
for eid in selected_ids:
    elem = doc.GetElement(eid)
    if elem and elem.Category.Id == ElementId(BuiltInCategory.OST_StructuralFraming):
        elements_to_process.append(elem)

# If no valid elements from existing selection, prompt for manual selection
if not elements_to_process:
    try:
        ref_elems = uidoc.Selection.PickObjects(ObjectType.Element, CategoryFilterStructuralFraming(), "Select Structural Framing")
        elements_to_process = [doc.GetElement(ref) for ref in ref_elems]
    except Exception as e:
        forms.alert("Selection cancelled or an error occurred during selection: {}".format(str(e)), title="Selection Cancelled")
        script.exit()

if not elements_to_process:
    forms.alert("No structural framing elements were selected. Please select valid elements.", title="No Elements Selected")
    script.exit()

# Choose join function: Disallow or Allow
join_function_option = forms.CommandSwitchWindow.show(
    ["Disallow Join", "Allow Join"],
    default="Disallow Join",
    title="Choose Join Function",
    message="Do you want to Disallow or Allow joins?"
)

if not join_function_option:
    script.exit()

# --- Initialize Counters ---
num_elements_processed = 0
success_count = 0
error_messages = []

# Use pyRevit's transaction context manager
with revit.Transaction("Disallow/Allow Joins") as t:
    for element in elements_to_process:
        num_elements_processed += 1
        try:
            if id_val(element.Category.Id) == int(BuiltInCategory.OST_StructuralFraming):
                if join_function_option == "Disallow Join":
                    Autodesk.Revit.DB.Structure.StructuralFramingUtils.DisallowJoinAtEnd(element, 0)
                    Autodesk.Revit.DB.Structure.StructuralFramingUtils.DisallowJoinAtEnd(element, 1)
                elif join_function_option == "Allow Join":
                    Autodesk.Revit.DB.Structure.StructuralFramingUtils.AllowJoinAtEnd(element, 0)
                    Autodesk.Revit.DB.Structure.StructuralFramingUtils.AllowJoinAtEnd(element, 1)
                success_count += 1
            else:
                error_messages.append("Skipped non-structural framing element. Element ID: {}".format(element.Id.ToString()))

        except Exception as e:
            error_messages.append("Error processing element {}: {}".format(element.Id.ToString(), str(e)))

# --- Final Summary Output ---
# Toast singkat
summary = "Processed: {} | Success: {} | Errors: {}".format(
    num_elements_processed,
    success_count,
    len(error_messages)
)
forms.toast(summary, title="Disallow/Allow Joins", appid="PrasKaaPyKit")

#Console detail
#output = script.get_output()
#output.print_md("## 📊 Disallow/Allow Joins Results\n")
#output.print_md("- 🏗️ **Total Elements Processed:** `{}`".format(num_elements_processed))
#output.print_md("- ✅ **Successful Operations:** `{}`".format(success_count))
#if error_messages:
#    output.print_md("\n### ⚠️ Error/Warning Messages:\n")
#    for error in error_messages:
#        output.print_md("- ❌ {}".format(error))
#else:
#    output.print_md("\n✨ No errors or warnings found.")