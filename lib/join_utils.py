# -*- coding: utf-8 -*-
"""
Join Utilities - Common join operations for structural elements

This module provides common utilities for joining structural elements,
extracted from various join tools to ensure consistency and maintainability.

Functions:
    - get_intersecting_elements(): Find elements intersecting with a given element
    - perform_join_if_needed(): Join two elements if not already joined
    - ensure_join_order(): Ensure correct cutting element in join order
    - process_elements_with_join_logic(): Process multiple elements with custom join logic
"""

import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

from System.Collections.Generic import List


def get_intersecting_elements(element, doc, categories, tolerance=0.001):
    """
    Find elements that intersect with the given element's bounding box.

    Args:
        element: The element to find intersections for
        doc: Current Revit document
        categories: List of BuiltInCategory to check for intersections
        tolerance: Tolerance for bounding box expansion (default: 1mm)

    Returns:
        list: List of intersecting elements
    """
    # Get element bounding box
    bb = element.get_BoundingBox(None)
    if not bb:
        return []

    # Expand bounding box slightly to catch touching elements
    expanded_min = XYZ(bb.Min.X - tolerance, bb.Min.Y - tolerance, bb.Min.Z - tolerance)
    expanded_max = XYZ(bb.Max.X + tolerance, bb.Max.Y + tolerance, bb.Max.Z + tolerance)
    outline = Outline(expanded_min, expanded_max)

    # Create filters
    bb_filter = BoundingBoxIntersectsFilter(outline)
    ids_to_exclude = List[ElementId]([element.Id])
    exclude_self_filter = ExclusionFilter(ids_to_exclude)
    not_element_type_filter = ElementIsElementTypeFilter(True)

    # Find intersecting elements
    intersecting_elements = []
    for category in categories:
        elements = FilteredElementCollector(doc)\
            .OfCategory(category)\
            .WherePasses(bb_filter)\
            .WherePasses(exclude_self_filter)\
            .WherePasses(not_element_type_filter)\
            .ToElements()
        intersecting_elements.extend(elements)

    return intersecting_elements


def perform_join_if_needed(doc, element1, element2):
    """
    Join two elements if they are not already joined.

    Args:
        doc: Current Revit document
        element1: First element to join
        element2: Second element to join

    Returns:
        bool: True if join was performed, False if already joined or failed
    """
    if not JoinGeometryUtils.AreElementsJoined(doc, element1, element2):
        try:
            JoinGeometryUtils.JoinGeometry(doc, element1, element2)
            return True
        except:
            return False
    return False


def ensure_join_order(doc, cutting_element, cut_element):
    """
    Ensure the cutting element is set correctly in the join order.
    Only switches if cutting_element is NOT already cutting.
    """
    if not JoinGeometryUtils.AreElementsJoined(doc, cutting_element, cut_element):
        return False
    try:
        is_cutting = JoinGeometryUtils.IsCuttingElementInJoin(doc, cutting_element, cut_element)
        if not is_cutting:
            JoinGeometryUtils.SwitchJoinOrder(doc, cutting_element, cut_element)
            return True
        return False
    except:
        return False


def process_elements_with_join_logic(doc, elements, join_func):
    """
    Process multiple elements with custom join logic.

    Args:
        doc: Current Revit document
        elements: List of elements to process
        join_func: Function that takes (element, doc) and performs join operations

    Returns:
        int: Number of elements processed
    """
    processed_count = 0
    for element in elements:
        try:
            join_func(element, doc)
            processed_count += 1
        except:
            # Continue processing other elements even if one fails
            continue
    return processed_count