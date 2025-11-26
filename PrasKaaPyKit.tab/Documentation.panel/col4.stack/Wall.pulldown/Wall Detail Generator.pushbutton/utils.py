# -*- coding: utf-8 -*-
"""
Utilities Module
Shared utility functions for Wall Plan Generator

Author: Generated from EF Element Sections Generator analysis
Version: 1.0.0
"""

from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType
from Autodesk.Revit.DB import *


class EF_SelectionFilter(ISelectionFilter):
    """
    Selection filter adapted from EF Element Sections Generator
    Filters elements based on type or category
    """

    def __init__(self, list_types_or_cats):
        """
        Initialize selection filter

        Args:
            list_types_or_cats: List of allowed types or categories
        """
        # Convert BuiltInCategories to ElementIds, keep Types as-is
        self.list_types_or_cats = [
            ElementId(i) if type(i) == BuiltInCategory else i
            for i in list_types_or_cats
        ]

    def AllowElement(self, element):
        """
        Determine if element should be selectable

        Args:
            element: Revit element to test

        Returns:
            bool: True if element should be selectable
        """
        # Exclude view-specific elements
        if element.ViewSpecific:
            return False

        # Check element type
        if type(element) in self.list_types_or_cats:
            return True

        # Check element category
        if hasattr(element, 'Category') and element.Category:
            if element.Category.Id in self.list_types_or_cats:
                return True

        return False


def flatten_list(lst):
    """
    Flatten nested lists (adapted from EF script)

    Args:
        lst: List that may contain nested lists

    Returns:
        list: Flattened list
    """
    new_lst = []
    for i in lst:
        if isinstance(i, list):
            new_lst += i
        else:
            new_lst.append(i)
    return new_lst


def ensure_unique_name(base_name, existing_names, max_attempts=100):
    """
    Ensure a name is unique by adding counter suffix if needed

    Args:
        base_name: Base name to make unique
        existing_names: Set of existing names
        max_attempts: Maximum attempts to find unique name

    Returns:
        str: Unique name
    """
    if base_name not in existing_names:
        return base_name

    counter = 1
    while counter < max_attempts:
        candidate = "{} ({})".format(base_name, counter)
        if candidate not in existing_names:
            return candidate
        counter += 1

    # Fallback with timestamp
    import time
    timestamp = str(int(time.time()))[-4:]  # Last 4 digits of timestamp
    return "{} {}".format(base_name, timestamp)


def get_parameter_value_safe(parameter):
    """
    Safely extract parameter value with error handling

    Args:
        parameter: Revit Parameter object

    Returns:
        Value in appropriate type or None if failed
    """
    if not parameter or not parameter.HasValue:
        return None

    try:
        storage_type = parameter.StorageType

        if storage_type == StorageType.Double:
            return parameter.AsDouble()
        elif storage_type == StorageType.Integer:
            return parameter.AsInteger()
        elif storage_type == StorageType.String:
            return parameter.AsString()
        elif storage_type == StorageType.ElementId:
            return parameter.AsElementId()
        else:
            return None
    except:
        return None


def calculate_distance(point1, point2):
    """
    Calculate distance between two XYZ points

    Args:
        point1, point2: XYZ points

    Returns:
        float: Distance between points
    """
    if not point1 or not point2:
        return 0.0

    vector = point2 - point1
    return vector.GetLength()


def format_length(length, unit_type="feet"):
    """
    Format length value for display

    Args:
        length: Length value in feet
        unit_type: Unit type for display

    Returns:
        str: Formatted length string
    """
    if unit_type == "feet":
        return "{:.2f}'".format(length)
    elif unit_type == "mm":
        return "{:.0f} mm".format(length * 304.8)
    else:
        return "{:.2f}".format(length)


def validate_document(doc):
    """
    Validate that document is valid for operations

    Args:
        doc: Revit Document

    Returns:
        tuple: (is_valid, error_message)
    """
    if not doc:
        return False, "Document is null"

    if doc.IsFamilyDocument:
        return False, "Script cannot run in family documents"

    if doc.IsReadOnly:
        return False, "Document is read-only"

    return True, ""


def get_wall_type_name(wall):
    """
    Get wall type name safely

    Args:
        wall: Wall element

    Returns:
        str: Wall type name or "Wall" if failed
    """
    try:
        wall_type = wall.Document.GetElement(wall.GetTypeId())
        return wall_type.Name if wall_type else "Wall"
    except:
        return "Wall"


def create_progress_title(current, total, classification="", level=""):
    """
    Create progress bar title

    Args:
        current: Current operation number
        total: Total operations
        classification: Current classification
        level: Current level

    Returns:
        str: Progress title
    """
    base = "Generating Wall Plans ({}/{})".format(current, total)

    if classification and level:
        return "{} - {} at {}".format(base, classification, level)
    elif classification:
        return "{} - {}".format(base, classification)
    else:
        return base


def log_operation(operation_name, success, details=""):
    """
    Log operation result for debugging

    Args:
        operation_name: Name of operation
        success: Boolean success status
        details: Additional details
    """
    status = "SUCCESS" if success else "FAILED"
    message = "[{}] {} - {}".format(status, operation_name, details)

    print(message)  # In production, could write to log file


def handle_transaction_error(operation_name, error):
    """
    Handle transaction errors consistently

    Args:
        operation_name: Name of failed operation
        error: Exception object

    Returns:
        str: Error message for user
    """
    error_msg = "Failed to {}: {}".format(operation_name, str(error))
    log_operation(operation_name, False, str(error))
    return error_msg