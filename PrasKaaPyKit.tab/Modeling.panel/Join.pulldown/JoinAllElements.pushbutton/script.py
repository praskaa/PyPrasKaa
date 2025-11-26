# -*- coding: utf-8 -*-
"""
Manual Join Elements - Post-Processing Join Tool

Overview:
    This script provides manual join functionality for structural elements that were
    not automatically joined during the Matching Dimension process. It allows users
    to selectively join elements to complete their model after disabling auto-joins
    for crash prevention.

Features:
    - Join selected elements (with interactive selection if none selected)
    - Join elements by category (beams, columns, floors, foundations, walls)
    - Batch processing to prevent crashes
    - Progress reporting
    - Selection filter for structural categories only

Requirements:
    - Revit environment with pyRevit extension
    - Elements that need to be joined (typically after running Matching Dimension)

Configuration:
    - ENABLE_PROGRESS_DETAIL: Show detailed progress (default: True)
"""

__title__ = 'Manual\nJoin\nElements'
__author__ = 'Cline'
__doc__ = "Manually join structural elements that were not auto-joined during Matching Dimension process."

import gc
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    RevitLinkInstance,
    ElementId,
    JoinGeometryUtils,
    Transaction,
    TransactionStatus,
    BoundingBoxIntersectsFilter,
    Outline,
    XYZ,
    ExclusionFilter,
    ElementIsElementTypeFilter
)
from Autodesk.Revit.UI.Selection import ISelectionFilter
from System.Collections.Generic import List

from pyrevit import revit, forms, script

# Configuration
ENABLE_PROGRESS_DETAIL = True  # Show detailed progress

# Structural categories that can be joined
STRUCTURAL_CATEGORIES = [
    BuiltInCategory.OST_StructuralFraming,
    BuiltInCategory.OST_StructuralColumns,
    BuiltInCategory.OST_Floors,
    BuiltInCategory.OST_StructuralFoundation,
    BuiltInCategory.OST_Walls
]

# Setup
doc = revit.doc
uidoc = revit.uidoc
logger = script.get_logger()
output = script.get_output()


class StructuralElementFilter(ISelectionFilter):
    """Selection filter to allow only structural elements."""

    def AllowElement(self, element):
        if element and element.Category:
            return element.Category.BuiltInCategory in STRUCTURAL_CATEGORIES
        return False

    def AllowReference(self, reference, position):
        # Not used for element selection
        return False


def get_selected_elements():
    """
    Get elements currently selected by the user.

    Returns:
        list: List of selected elements
    """
    selection_ids = uidoc.Selection.GetElementIds()
    selected_elements = []

    for elem_id in selection_ids:
        elem = doc.GetElement(elem_id)
        if elem and elem.Category and elem.Category.BuiltInCategory in STRUCTURAL_CATEGORIES:
            selected_elements.append(elem)

    return selected_elements


def prompt_for_element_selection():
    """
    Prompt user to select structural elements interactively.

    Returns:
        list: List of selected elements, or empty list if cancelled
    """
    try:
        # Use PickElements with filter for structural categories only
        selected_refs = uidoc.Selection.PickElements(StructuralElementFilter(),
                                                   "Select structural elements to join",
                                                   "Finish selection to proceed with joining")
        selected_elements = [doc.GetElement(ref.ElementId) for ref in selected_refs]
        return selected_elements
    except:
        # User cancelled selection
        return []


def get_elements_by_category(category):
    """
    Get all elements of a specific category.

    Args:
        category (BuiltInCategory): The category to collect

    Returns:
        list: List of elements in the category
    """
    return FilteredElementCollector(doc)\
        .OfCategory(category)\
        .WhereElementIsNotElementType()\
        .ToElements()


def process_join_elements(elements):
    """
    Process all elements and join them with intersecting structural elements.
    Follows the pattern from "Join Walls to Structure" script.

    Args:
        elements (list): List of elements to process

    Returns:
        tuple: (total_processed, successful_joins, failed_joins, error_messages)
    """
    total_processed = 0
    successful_joins = 0
    failed_joins = 0
    error_messages = []

    for main_elem in elements:
        total_processed += 1

        # Phase 1: Find intersecting elements and join
        try:
            bb = main_elem.get_BoundingBox(None)
            if bb:
                # Expand bounding box slightly to catch touching elements
                tolerance = 0.001  # 1mm tolerance
                expanded_min = XYZ(bb.Min.X - tolerance, bb.Min.Y - tolerance, bb.Min.Z - tolerance)
                expanded_max = XYZ(bb.Max.X + tolerance, bb.Max.Y + tolerance, bb.Max.Z + tolerance)
                outline = Outline(expanded_min, expanded_max)

                # Create filters
                bb_filter = BoundingBoxIntersectsFilter(outline)
                ids_to_exclude = List[ElementId]([main_elem.Id])
                exclude_self_filter = ExclusionFilter(ids_to_exclude)
                not_element_type_filter = ElementIsElementTypeFilter(True)

                # Find intersecting elements
                intersect_candidates = FilteredElementCollector(doc)\
                    .WherePasses(bb_filter)\
                    .WherePasses(exclude_self_filter)\
                    .WherePasses(not_element_type_filter)\
                    .ToElements()

                # Try to join with found elements
                for intersecting_elem in intersect_candidates:
                    # Skip if not a structural element
                    if (not intersecting_elem.Category or
                        intersecting_elem.Category.BuiltInCategory not in STRUCTURAL_CATEGORIES):
                        continue

                    # Only try to join if not already joined
                    if not JoinGeometryUtils.AreElementsJoined(doc, main_elem, intersecting_elem):
                        try:
                            JoinGeometryUtils.JoinGeometry(doc, main_elem, intersecting_elem)
                            successful_joins += 1

                            if ENABLE_PROGRESS_DETAIL:
                                logger.debug("Joined {} with {}".format(main_elem.Id, intersecting_elem.Id))

                        except Exception as join_err:
                            if "cannot be joined" in str(join_err):
                                failed_joins += 1  # Expected failure
                            else:
                                error_messages.append("Join Error ({} - {}): {}".format(
                                    main_elem.Id, intersecting_elem.Id, str(join_err)))
                                failed_joins += 1

        except Exception as e:
            error_messages.append("Intersection Check Error ({}): {}".format(main_elem.Id, str(e)))

    return total_processed, successful_joins, failed_joins, error_messages


def select_join_mode():
    """
    Let user select the join mode.

    Returns:
        str: Selected mode ('selection' or 'all_structural')
    """
    join_modes = [
        {'name': 'Selected Element', 'value': 'selection'},
        {'name': 'All Element', 'value': 'all_structural'}
    ]

    selected_mode_name = forms.SelectFromList.show(
        [mode['name'] for mode in join_modes],
        title='Select Join Mode',
        button_name='Select Mode',
        multiselect=False
    )

    if not selected_mode_name:
        return None

    selected_mode = next(mode['value'] for mode in join_modes if mode['name'] == selected_mode_name)
    return selected_mode


def main():
    """
    Main execution function.
    """
    # Select join mode
    mode = select_join_mode()
    if not mode:
        forms.alert("No join mode selected. Script will exit.", exitscript=True)



    # Get elements based on mode
    elements = []

    if mode == 'selection':
        elements = get_selected_elements()
        if not elements:
            # No pre-selection, prompt user to select
            elements = prompt_for_element_selection()
            if not elements:
                forms.alert("No elements selected. Script will exit.", exitscript=True)


    elif mode == 'all_structural':
        elements = list(get_elements_by_category(BuiltInCategory.OST_StructuralFraming))
        elements.extend(list(get_elements_by_category(BuiltInCategory.OST_StructuralColumns)))
        elements.extend(list(get_elements_by_category(BuiltInCategory.OST_StructuralFoundation)))
        elements.extend(list(get_elements_by_category(BuiltInCategory.OST_Floors)))
        elements.extend(list(get_elements_by_category(BuiltInCategory.OST_Walls)))

    if not elements:
        forms.alert("No elements found for the selected mode.", exitscript=True)



    # Initialize counters
    total_processed = 0
    successful_joins = 0
    failed_joins = 0
    error_messages = []

    # Start transaction
    t = Transaction(doc, "Manual Join Elements")
    t.Start()

    try:
        with forms.ProgressBar(title='Joining elements...') as pb:
            # Process all elements
            total_processed, successful_joins, failed_joins, error_messages = process_join_elements(elements)

        # Commit the transaction
        t.Commit()

    except Exception as e:
        # Roll back on error
        t.RollBack()
        error_messages.append("Transaction Error: {}".format(str(e)))
        forms.alert("Critical error during join process: {}".format(str(e)), title="Error")

    # Force garbage collection
    gc.collect()

    # Show toast notification
    summary = "Processed: {} | Success: {} | Errors: {}".format(
        total_processed, successful_joins, len(error_messages)
    )
    forms.toast(summary, title="Manual Join Elements", appid="PrasKaaPyKit")


if __name__ == '__main__':
    main()