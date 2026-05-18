# -*- coding: utf-8 -*-
"""Join and Switch Floor Connections with Structure.
Join floors with intersecting elements and ensure floors cut through walls."""
__title__ = 'Join Floors\nto Structure'
__author__ = 'PrasKaa'
__doc__ = 'Automatically joins selected floors with intersecting elements and ensures floors cut through walls.'
# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System')
clr.AddReference('System.Collections')
from Autodesk.Revit.DB import *
from System.Collections.Generic import List
from pyrevit import forms
from pyrevit import script
from pyrevit import revit
# Local lib imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'lib'))
from Snippets._selection import get_selected_elements, pick_by_category
from Snippets._context_manager import ef_Transaction
from join_utils import get_intersecting_elements, perform_join_if_needed, ensure_join_order
# Get current document and UI
doc = revit.doc
uidoc = revit.uidoc
# Helper function for cross-version ElementId value access
def id_val(eid):
    try:
        return eid.Value
    except AttributeError:
        return eid.IntegerValue
# Configuration
structural_categories = [
    BuiltInCategory.OST_StructuralFraming,
    BuiltInCategory.OST_StructuralColumns,
    BuiltInCategory.OST_StructuralFoundation,
    BuiltInCategory.OST_Floors,
    BuiltInCategory.OST_Walls,
    BuiltInCategory.OST_IOSModelGroups
]
# Get selected floors (if any)
selected_elements = get_selected_elements(uidoc, exitscript=False)
# Filter for floors
selected_floors = []
if selected_elements:
    for elem in selected_elements:
        if elem and isinstance(elem, Floor):
            selected_floors.append(elem)
# If no floors selected, prompt user to select
if not selected_floors:
    selected_floors = pick_by_category([BuiltInCategory.OST_Floors], exit_if_none=True)
# Define floor join logic
def join_floor_with_structure(floor):
    """Join floor with intersecting structural elements"""
    intersecting_elements = get_intersecting_elements(floor, doc, structural_categories)
    walls = []
    others = []
    for elem in intersecting_elements:
        if elem and elem.Category:
            if elem.Category.BuiltInCategory == BuiltInCategory.OST_Walls:
                walls.append(elem)
            else:
                others.append(elem)
    # Join non-wall elements — structure should cut floor
    for elem in others:
        perform_join_if_needed(doc, floor, elem)
        ensure_join_order(doc, elem, floor)  # elem cuts floor
    # Join walls — floor should cut wall
    for wall in walls:
        perform_join_if_needed(doc, floor, wall)
        ensure_join_order(doc, floor, wall)  # floor cuts wall
# Process floors silently
if selected_floors:
    with ef_Transaction(doc, "Join Floors to Structure", debug=False, exitscript=False):
        for floor in selected_floors:
            try:
                join_floor_with_structure(floor)
            except:
                continue