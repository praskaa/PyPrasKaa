# -*- coding: utf-8 -*-
"""
Join Columns Utility - Column-specific join operations for pyRevit

This module provides utilities for joining structural columns with nearby elements
(beams, floors, foundations, walls) and ensuring columns win in join order.

Functions:
    - join_column_with_nearby_elements(): Join a single column with intersecting elements
    - get_join_candidate_elements(): Find elements that can be joined with a column
    - ensure_column_wins_join_order(): Switch join order if column is not winning
"""

import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

# Categories that columns can be joined with
JOIN_CANDIDATE_CATEGORIES = [
    BuiltInCategory.OST_StructuralFraming,  # Beams
    BuiltInCategory.OST_Floors,             # Floors
    BuiltInCategory.OST_StructuralFoundation, # Foundations
    BuiltInCategory.OST_Walls,              # Walls
    BuiltInCategory.OST_StructuralColumns   # Other Columns
]


def get_join_candidate_elements(column, doc):
    """
    Find elements that can potentially be joined with the given column.

    Args:
        column: The structural column element
        doc: Current Revit document

    Returns:
        list: List of elements that intersect with the column's bounding box
    """
    # Get column bounding box
    bb = column.get_BoundingBox(None)
    if not bb:
        return []

    # Expand bounding box slightly to catch touching elements
    tolerance = 0.001  # 1mm tolerance
    expanded_min = XYZ(bb.Min.X - tolerance, bb.Min.Y - tolerance, bb.Min.Z - tolerance)
    expanded_max = XYZ(bb.Max.X + tolerance, bb.Max.Y + tolerance, bb.Max.Z + tolerance)
    outline = Outline(expanded_min, expanded_max)

    # Create bounding box filter
    bb_filter = BoundingBoxIntersectsFilter(outline)

    # Find intersecting elements of join candidate categories
    candidate_elements = []
    for category in JOIN_CANDIDATE_CATEGORIES:
        elements = FilteredElementCollector(doc)\
            .OfCategory(category)\
            .WherePasses(bb_filter)\
            .WhereElementIsNotElementType()\
            .ToElements()

        candidate_elements.extend(elements)

    # Remove self-reference if column is in the list
    return [elem for elem in candidate_elements if elem.Id != column.Id]


def ensure_column_wins_join_order(doc, column, other_element):
    """
    Ensure the column wins in the join order with another element.
    For column-to-column joins, the higher column ID wins.

    Args:
        doc: Current Revit document
        column: The structural column element
        other_element: The element to check join order with
    """
    if JoinGeometryUtils.AreElementsJoined(doc, column, other_element):
        # For column-to-column joins, let the higher column ID win
        if (other_element.Category and
            other_element.Category.Id.IntegerValue == int(BuiltInCategory.OST_StructuralColumns)):
            if column.Id.IntegerValue > other_element.Id.IntegerValue:
                if not JoinGeometryUtils.IsCuttingElementInJoin(doc, column, other_element):
                    JoinGeometryUtils.SwitchJoinOrder(doc, column, other_element)
        else:
            # For other elements, column should always win
            if not JoinGeometryUtils.IsCuttingElementInJoin(doc, column, other_element):
                JoinGeometryUtils.SwitchJoinOrder(doc, column, other_element)


def join_column_with_nearby_elements(column, doc):
    """
    Join a structural column with nearby elements and ensure column wins join order.

    This function:
    1. Finds elements intersecting with the column's bounding box
    2. Joins the column with intersecting elements if not already joined
    3. Ensures the column wins in join order

    Args:
        column: The structural column element to process
        doc: Current Revit document
    """
    # Find candidate elements to join with
    candidate_elements = get_join_candidate_elements(column, doc)

    # Process each candidate element
    for element in candidate_elements:
        try:
            # Join if not already joined
            if not JoinGeometryUtils.AreElementsJoined(doc, column, element):
                JoinGeometryUtils.JoinGeometry(doc, column, element)

            # Ensure column wins join order
            ensure_column_wins_join_order(doc, column, element)

        except:
            # Silently continue if join fails (elements might not be joinable)
            continue