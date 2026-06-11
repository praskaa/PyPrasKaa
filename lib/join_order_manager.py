# -*- coding: utf-8 -*-
"""
join_order_manager.py
Manages join and unjoin operations with configurable priority-based join order.
Priority: lower number = cuts through higher number elements.
"""
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
from System.Collections.Generic import List

# Join order priority configuration
# Lower number = higher priority = cuts through lower priority elements
JOIN_PRIORITY = {
    BuiltInCategory.OST_StructuralColumns:    1,
    BuiltInCategory.OST_StructuralFraming:    2,
    BuiltInCategory.OST_StructuralFoundation: 3,
    BuiltInCategory.OST_Floors:               4,
    BuiltInCategory.OST_Walls:                5,
    BuiltInCategory.OST_IOSModelGroups:       6,
}

ALL_CATEGORIES = list(JOIN_PRIORITY.keys())


def get_priority(element):
    """Get join priority for an element. Returns 99 if category not in config."""
    if not element or not element.Category:
        return 99
    cat = element.Category.BuiltInCategory
    return JOIN_PRIORITY.get(cat, 99)


def get_cutting_element(elem_a, elem_b):
    """
    Determine which element should be the cutting element based on priority.
    Returns (cutting, cut) tuple.
    """
    if get_priority(elem_a) <= get_priority(elem_b):
        return elem_a, elem_b
    return elem_b, elem_a


def join_with_order(doc, elem_a, elem_b):
    """
    Join two elements and apply correct join order based on priority config.
    Performs join if not already joined, then ensures correct cutting element.

    Returns:
        str: 'joined_and_ordered', 'ordered_only', 'already_correct', 'failed'
    """
    try:
        cutting, cut = get_cutting_element(elem_a, elem_b)

        # Join if not already joined
        if not JoinGeometryUtils.AreElementsJoined(doc, cutting, cut):
            try:
                JoinGeometryUtils.JoinGeometry(doc, cutting, cut)
            except:
                return 'failed'
            joined_new = True
        else:
            joined_new = False

        # Apply correct join order
        try:
            is_cutting = JoinGeometryUtils.IsCuttingElementInJoin(doc, cutting, cut)
            if not is_cutting:
                JoinGeometryUtils.SwitchJoinOrder(doc, cutting, cut)
                return 'joined_and_ordered' if joined_new else 'ordered_only'
            return 'already_correct'
        except:
            # IsCuttingElementInJoin unsupported — force switch
            try:
                JoinGeometryUtils.SwitchJoinOrder(doc, cutting, cut)
                return 'joined_and_ordered' if joined_new else 'ordered_only'
            except:
                return 'already_correct'

    except:
        return 'failed'


def unjoin_elements(doc, elem_a, elem_b):
    """
    Unjoin two elements if they are currently joined.

    Returns:
        bool: True if unjoined, False if not joined or failed
    """
    if JoinGeometryUtils.AreElementsJoined(doc, elem_a, elem_b):
        try:
            JoinGeometryUtils.UnjoinGeometry(doc, elem_a, elem_b)
            return True
        except:
            return False
    return False


def get_intersecting_structural(element, doc, tolerance=0.001):
    """
    Find all structural elements intersecting with the given element,
    using ALL_CATEGORIES from priority config.
    """
    bb = element.get_BoundingBox(None)
    if not bb:
        return []

    expanded_min = XYZ(bb.Min.X - tolerance, bb.Min.Y - tolerance, bb.Min.Z - tolerance)
    expanded_max = XYZ(bb.Max.X + tolerance, bb.Max.Y + tolerance, bb.Max.Z + tolerance)
    outline = Outline(expanded_min, expanded_max)

    bb_filter = BoundingBoxIntersectsFilter(outline)
    ids_to_exclude = List[ElementId]([element.Id])
    exclude_self_filter = ExclusionFilter(ids_to_exclude)
    not_type_filter = ElementIsElementTypeFilter(True)

    results = []
    for category in ALL_CATEGORIES:
        elements = FilteredElementCollector(doc)\
            .OfCategory(category)\
            .WherePasses(bb_filter)\
            .WherePasses(exclude_self_filter)\
            .WherePasses(not_type_filter)\
            .ToElements()
        results.extend(elements)
    return results


def process_element_joins(doc, element):
    """
    Find all intersecting structural elements for a given element
    and apply join + correct order for each pair.

    Returns:
        dict: {'joined_and_ordered': n, 'ordered_only': n, 'already_correct': n, 'failed': n}
    """
    results = {'joined_and_ordered': 0, 'ordered_only': 0, 'already_correct': 0, 'failed': 0}
    intersecting = get_intersecting_structural(element, doc)
    for other in intersecting:
        result = join_with_order(doc, element, other)
        results[result] += 1
    return results