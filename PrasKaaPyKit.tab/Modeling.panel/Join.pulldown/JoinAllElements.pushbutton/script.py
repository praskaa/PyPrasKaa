# -*- coding: utf-8 -*-
"""
Join All Elements - Join all structural elements with nearby elements
"""

__title__ = 'Join All\nElements'
__author__ = 'PrasKaa Team'

from Autodesk.Revit.DB import *

from pyrevit import forms
from pyrevit import revit

# Local lib imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'lib'))

from Snippets._selection import pick_by_category, get_selected_elements
from Snippets._context_manager import ef_Transaction
from join_utils import get_intersecting_elements, perform_join_if_needed

# Setup
doc = revit.doc
uidoc = revit.uidoc

# Structural categories that can be joined
STRUCTURAL_CATEGORIES = [
    BuiltInCategory.OST_StructuralFraming,
    BuiltInCategory.OST_StructuralColumns,
    BuiltInCategory.OST_Floors,
    BuiltInCategory.OST_StructuralFoundation,
    BuiltInCategory.OST_Walls
]

# Check for preselected elements
selected_elements = get_selected_elements(uidoc, exitscript=False)

if selected_elements:
    # Filter selected elements to only structural categories
    elements_to_process = [elem for elem in selected_elements if elem.Category and elem.Category.Id.IntegerValue in [int(cat) for cat in STRUCTURAL_CATEGORIES]]
else:
    # Get all structural elements
    all_elements = []
    for category in STRUCTURAL_CATEGORIES:
        elements = FilteredElementCollector(doc)\
            .OfCategory(category)\
            .WhereElementIsNotElementType()\
            .ToElements()
        all_elements.extend(elements)
    elements_to_process = all_elements

# Define join logic function
def join_element_with_nearby(element):
    """Join element with all intersecting structural elements"""
    intersecting_elements = get_intersecting_elements(element, doc, STRUCTURAL_CATEGORIES)

    for intersecting_elem in intersecting_elements:
        perform_join_if_needed(doc, element, intersecting_elem)

# Process elements silently
if elements_to_process:
    with ef_Transaction(doc, "Join All Elements", debug=False, exitscript=False):
        for element in elements_to_process:
            try:
                join_element_with_nearby(element)
            except:
                continue