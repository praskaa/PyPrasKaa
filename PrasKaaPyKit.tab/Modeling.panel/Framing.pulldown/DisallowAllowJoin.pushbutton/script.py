# -*- coding: utf-8 -*-
"""
Disallow/Allow Joins - Toggle join functionality for structural framing
"""

__title__ = "Disallow/Allow Joins"
__author__ = "PrasKaa Team"

import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

from pyrevit import forms
from pyrevit import revit

# Local lib imports
from Snippets._selection import get_selected_elements, pick_by_category
from Snippets._context_manager import ef_Transaction

# Helper function for Revit API compatibility
def get_element_id_value(element_id):
    """Get the integer value from ElementId, compatible with different Revit versions."""
    try:
        return element_id.Value
    except AttributeError:
        # Fallback for older Revit versions
        return element_id.IntegerValue

# Setup
doc = revit.doc
uidoc = revit.uidoc

# Get selected elements (if any)
selected_elements = get_selected_elements(uidoc, exitscript=False)

# Filter for structural framing
selected_framing = []
if selected_elements:
    for elem in selected_elements:
        if (elem and elem.Category and
            get_element_id_value(elem.Category.Id) == int(BuiltInCategory.OST_StructuralFraming)):
            selected_framing.append(elem)

# If no framing selected, prompt user to select
if not selected_framing:
    selected_framing = pick_by_category([BuiltInCategory.OST_StructuralFraming], exit_if_none=True)

# Choose join function
join_function_option = forms.CommandSwitchWindow.show(
    ["Disallow Join", "Allow Join"],
    default="Disallow Join",
    title="Choose Join Function",
    message="Do you want to Disallow or Allow joins?"
)

if not join_function_option or not selected_framing:
    # Silent exit - no output
    pass
else:
    # Define join logic function
    def disallow_allow_join(element):
        if join_function_option == "Disallow Join":
            Structure.StructuralFramingUtils.DisallowJoinAtEnd(element, 0)
            Structure.StructuralFramingUtils.DisallowJoinAtEnd(element, 1)
        elif join_function_option == "Allow Join":
            Structure.StructuralFramingUtils.AllowJoinAtEnd(element, 0)
            Structure.StructuralFramingUtils.AllowJoinAtEnd(element, 1)

    # Process silently with standardized transaction
    with ef_Transaction(doc, "Disallow/Allow Joins", debug=False, exitscript=False):
        for element in selected_framing:
            try:
                disallow_allow_join(element)
            except:
                continue