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

from Snippets._selection import pick_by_category
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

# Get all structural elements
all_elements = []
for category in STRUCTURAL_CATEGORIES:
    elements = FilteredElementCollector(doc)\
        .OfCategory(category)\
        .WhereElementIsNotElementType()\
        .ToElements()
    all_elements.extend(elements)

# Define join logic function
def join_element_with_nearby(element):
    """Join element with all intersecting structural elements"""
    intersecting_elements = get_intersecting_elements(element, doc, STRUCTURAL_CATEGORIES)

    for intersecting_elem in intersecting_elements:
        perform_join_if_needed(doc, element, intersecting_elem)

# Process all elements silently
if all_elements:
    with ef_Transaction(doc, "Join All Elements", debug=False, exitscript=False):
        for element in all_elements:
            try:
                join_element_with_nearby(element)
            except:
                continue