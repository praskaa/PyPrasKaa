# -*- coding: utf-8 -*-
"""
Join Foundations - Join structural foundations with nearby elements
"""

__title__ = "Join Foundations"
__author__ = "PrasKaa Team"

from Autodesk.Revit.DB import *

from pyrevit import revit

# Local lib imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'lib'))

from Snippets._selection import pick_by_category
from Snippets._context_manager import ef_Transaction
from join_utils import get_intersecting_elements, perform_join_if_needed, ensure_join_order

# Setup
doc = revit.doc
uidoc = revit.uidoc

# Define join priority: Floor > Foundation > Column > Framing > Wall
join_priority_categories = [
    BuiltInCategory.OST_Floors,
    BuiltInCategory.OST_StructuralFoundation,
    BuiltInCategory.OST_StructuralColumns,
    BuiltInCategory.OST_StructuralFraming,
    BuiltInCategory.OST_Walls
]

# Get foundations (exclude "Foundation Pile - Rectangular")
foundations_to_process = pick_by_category([BuiltInCategory.OST_StructuralFoundation], exit_if_none=True)

# Filter out "Foundation Pile - Rectangular"
valid_foundations = []
for foundation in foundations_to_process:
    foundation_type = doc.GetElement(foundation.GetTypeId())
    if not (foundation_type and hasattr(foundation_type, "Name") and
            foundation_type.Name == "Foundation Pile - Rectangular"):
        valid_foundations.append(foundation)

# Define foundation join logic
def join_foundation_with_priority(foundation):
    """Join foundation with intersecting elements and handle priority-based join order"""

    # Get intersecting elements
    intersecting_elements = get_intersecting_elements(foundation, doc, join_priority_categories)

    # Join with intersecting elements
    for intersecting_elem in intersecting_elements:
        perform_join_if_needed(doc, foundation, intersecting_elem)

    # Handle priority-based join order switching
    joined_elements_ids = JoinGeometryUtils.GetJoinedElements(doc, foundation)
    for joined_id in joined_elements_ids:
        joined_element = doc.GetElement(joined_id)
        if joined_element and joined_element.Category:
            joined_cat = joined_element.Category.BuiltInCategory

            foundation_priority_idx = join_priority_categories.index(BuiltInCategory.OST_StructuralFoundation)
            joined_priority_idx = join_priority_categories.index(joined_cat) if joined_cat in join_priority_categories else -1

            if joined_priority_idx != -1:
                if foundation_priority_idx < joined_priority_idx:
                    # Foundation should cut - ensure it's cutting
                    ensure_join_order(doc, foundation, joined_element)
                elif joined_priority_idx < foundation_priority_idx:
                    # Joined element should cut - ensure it's cutting
                    ensure_join_order(doc, joined_element, foundation)

# Process foundations silently
if valid_foundations:
    with ef_Transaction(doc, "Join Foundations", debug=False, exitscript=False):
        for foundation in valid_foundations:
            try:
                join_foundation_with_priority(foundation)
            except:
                continue
