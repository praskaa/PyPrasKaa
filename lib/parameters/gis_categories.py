# -*- coding: utf-8 -*-
"""
Centralized GIS Categories Configuration.

This module provides shared categories and parameter names
for GIS-related scripts in PrasKaaPyKit.

Categories:
- Floors
- Walls
- Structural Framing
- Structural Columns
- Structural Foundation
- Stairs

Usage:
    from parameters.gis_categories import (
        GIS_CATEGORIES,
        PARAM_NAME
    )
"""

from Autodesk.Revit.DB import BuiltInCategory

# GIS Element UID parameter name
PARAM_NAME = "GIS_Element_UID"

# Categories for GIS operations
# Format: { Display Name: (BuiltInCategory enum, UID Prefix) }
GIS_CATEGORIES = {
    "Floors": (BuiltInCategory.OST_Floors, "FLOOR"),
    "Walls": (BuiltInCategory.OST_Walls, "WALL"),
    "Structural Framing": (BuiltInCategory.OST_StructuralFraming, "BEAM"),
    "Structural Columns": (BuiltInCategory.OST_StructuralColumns, "COL"),
    "Structural Foundation": (BuiltInCategory.OST_StructuralFoundation, "FOUND"),
    "Stairs": (BuiltInCategory.OST_Stairs, "STAIR")
}


def get_categories_dict():
    """
    Returns the GIS_CATEGORIES dictionary.
    
    Returns:
        dict: Category mapping with display names as keys
    """
    return GIS_CATEGORIES


def get_category_by_name(category_name):
    """
    Get category tuple by display name.
    
    Args:
        category_name (str): Display name of the category
        
    Returns:
        tuple: (BuiltInCategory, UID Prefix) or None if not found
    """
    return GIS_CATEGORIES.get(category_name)


def get_all_category_enums():
    """
    Get all BuiltInCategory enums from GIS_CATEGORIES.
    
    Returns:
        list: List of BuiltInCategory enums
    """
    return [cat_enum for cat_enum, _ in GIS_CATEGORIES.values()]


def get_uid_prefix(category_name):
    """
    Get the UID prefix for a category.
    
    Args:
        category_name (str): Display name of the category
        
    Returns:
        str: UID prefix (e.g., "FLOOR", "WALL", "BEAM")
    """
    result = GIS_CATEGORIES.get(category_name)
    if result:
        return result[1]
    return None
