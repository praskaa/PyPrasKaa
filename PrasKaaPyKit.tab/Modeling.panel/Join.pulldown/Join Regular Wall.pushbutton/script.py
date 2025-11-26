"""Join and Switch Wall Connections with Structure.
Join walls with intersecting elements and ensure structural elements cut through walls."""

__title__ = 'Join Walls\nto Structure'
__author__ = 'PyRevit'
__doc__ = 'Automatically joins selected walls with intersecting elements and ensures structural elements cut through the walls.'

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
    """Extract numeric value from ElementId, compatible with Revit 2020-2025 (IntegerValue) and 2026+ (Value).

    Args:
        eid (ElementId): The ElementId to extract value from.

    Returns:
        int: The numeric ID value.
    """
    try:
        return eid.Value
    except AttributeError:
        return eid.IntegerValue


# Configuration
structural_categories = [
    BuiltInCategory.OST_StructuralFraming,
    BuiltInCategory.OST_StructuralColumns,
    BuiltInCategory.OST_Floors,
    BuiltInCategory.OST_StructuralFoundation,  # Main foundation category
    BuiltInCategory.OST_Walls,  # Include walls since they can also be structural
    BuiltInCategory.OST_IOSModelGroups  # Added support for Model Groups
]

# Get selected walls (if any)
selected_elements = get_selected_elements(uidoc, exitscript=False)

# Filter for walls
selected_walls = []
if selected_elements:
    for elem in selected_elements:
        if elem and isinstance(elem, Wall):
            selected_walls.append(elem)

# If no walls selected, prompt user to select
if not selected_walls:
    selected_walls = pick_by_category([BuiltInCategory.OST_Walls], exit_if_none=True)

# Define wall join logic
def join_wall_with_structure(wall):
    """Join wall with intersecting structural elements and ensure structure cuts wall"""

    # Get intersecting structural elements
    intersecting_elements = get_intersecting_elements(wall, doc, structural_categories)

    # Join with intersecting elements
    for intersecting_elem in intersecting_elements:
        perform_join_if_needed(doc, wall, intersecting_elem)

    # Ensure structural elements cut through walls
    joined_elements_ids = JoinGeometryUtils.GetJoinedElements(doc, wall)
    for joined_id in joined_elements_ids:
        joined_element = doc.GetElement(joined_id)
        if (joined_element and joined_element.Category and
            joined_element.Category.BuiltInCategory in structural_categories):
            # Structure should cut wall
            ensure_join_order(doc, joined_element, wall)

# Process walls silently
if selected_walls:
    with ef_Transaction(doc, "Join Walls to Structure", debug=False, exitscript=False):
        for wall in selected_walls:
            try:
                join_wall_with_structure(wall)
            except:
                continue
