"""
Smart Selection Utility for Intelligent Element Selection

Version: 1.0.0
Date: 2025-10-16
Author: Prasetyo

Utility for intelligent element selection that prioritizes user's existing selection
while maintaining category filtering capabilities. Supports both pre-selected elements
and fallback to manual selection.
"""

# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType
from pyrevit import forms
from pyrevit import script


def get_filtered_selection(doc, uidoc, category_filter_func, prompt_message="Select Elements",
                          no_selection_message="No valid elements were selected. Please select valid elements.",
                          filter_name="Element Filter"):
    """
    Intelligent element selection with smart filtering logic.

    Selection Logic Flow:
    1. Get existing selection from UI
    2. Filter existing selection using category_filter_func
    3. Fallback to manual selection if no valid elements found
    4. Return filtered list or exit script if cancelled

    Args:
        doc: Revit Document
        uidoc: Revit UIDocument
        category_filter_func: Function that takes an element and returns True if valid
        prompt_message: Message shown when prompting for manual selection
        no_selection_message: Message shown when no valid elements found
        filter_name: Name of the filter for logging purposes

    Returns:
        List of valid elements or exits script if cancelled
    """
    try:
        # Step 1: Get existing selection
        existing_selection_ids = uidoc.Selection.GetElementIds()
        existing_elements = [doc.GetElement(elId) for elId in existing_selection_ids]

        # Step 2: Filter existing selection
        valid_elements = [elem for elem in existing_elements if category_filter_func(elem)]

        # Step 3: If valid elements found, return them
        if valid_elements:
            script.get_logger().info("{}: Found {} valid elements in existing selection".format(
                filter_name, len(valid_elements)))
            return valid_elements

        # Step 4: Fallback to manual selection
        script.get_logger().info("{}: No valid elements in existing selection, prompting for manual selection".format(filter_name))

        try:
            # Prompt user to select elements
            selected_refs = uidoc.Selection.PickObjects(
                ObjectType.Element,
                prompt_message
            )

            # Convert to elements and filter
            selected_elements = [doc.GetElement(ref.ElementId) for ref in selected_refs]
            valid_elements = [elem for elem in selected_elements if category_filter_func(elem)]

            if valid_elements:
                script.get_logger().info("{}: User selected {} valid elements".format(
                    filter_name, len(valid_elements)))
                return valid_elements
            else:
                forms.alert(no_selection_message, title="Selection Required")
                script.exit()

        except Exception as selection_err:
            # User cancelled selection
            if "cancelled" in str(selection_err).lower() or "escape" in str(selection_err).lower():
                forms.alert("Selection cancelled by user.", title="Cancelled")
                script.exit()
            else:
                # Other selection error
                forms.alert("Selection error: {}".format(str(selection_err)), title="Error")
                script.exit()

    except Exception as e:
        forms.alert("Error during element selection: {}".format(str(e)), title="Error")
        script.exit()


def create_single_category_filter(category):
    """
    Create a filter function for a single BuiltInCategory.

    Args:
        category: BuiltInCategory enum value

    Returns:
        Filter function that checks if element belongs to the specified category
    """
    def filter_func(elem):
        if not elem or not elem.Category:
            return False
        return elem.Category.BuiltInCategory == category

    return filter_func


def create_category_filter(categories):
    """
    Create a filter function for multiple BuiltInCategories.

    Args:
        categories: List of BuiltInCategory enum values

    Returns:
        Filter function that checks if element belongs to any of the specified categories
    """
    def filter_func(elem):
        if not elem or not elem.Category:
            return False
        return elem.Category.BuiltInCategory in categories

    return filter_func


def create_wall_filter():
    """
    Convenience function to create a wall filter.

    Returns:
        Filter function for wall elements
    """
    return create_single_category_filter(BuiltInCategory.OST_Walls)


def create_structural_filter():
    """
    Convenience function to create a structural elements filter.

    Returns:
        Filter function for structural elements (framing, columns, floors, foundations)
    """
    structural_categories = [
        BuiltInCategory.OST_StructuralFraming,
        BuiltInCategory.OST_StructuralColumns,
        BuiltInCategory.OST_Floors,
        BuiltInCategory.OST_StructuralFoundation
    ]
    return create_category_filter(structural_categories)