# -*- coding: utf-8 -*-
"""
Structural Utilities Library - Shared utilities for structural elements

This module provides shared functions for collecting and processing
structural framing (beams) and structural columns.

Usage:
    from lib.structural_utils import (
        collect_structural_framing,
        collect_structural_columns,
        get_type_info,
        extract_mark_from_type_name
    )

Dependencies:
    - pyRevit (revit, forms)
    - Autodesk.Revit.DB (FilteredElementCollector, BuiltInCategory, etc.)
"""

import re

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    BuiltInParameter,
    FamilySymbol,
    Family,
    ElementId
)
from pyrevit import revit, forms

# Import from geometry_matching if available
try:
    from geometry_matching import get_beam_dimensions, get_column_dimensions
except ImportError:
    # Fallback implementations when geometry_matching is not available
    def get_beam_dimensions(element):
        """Fallback implementation - returns None."""
        return None
    def get_column_dimensions(element):
        """Fallback implementation - returns None."""
        return None


def collect_structural_framing(document, selection_ids=None, uidoc=None):
    """
    Collects structural framing elements (beams) from a document.
    
    Args:
        document: Revit Document
        selection_ids: Optional list of ElementIds for pre-selection
        uidoc: UIDocument (optional, for checking current selection)
    
    Returns:
        list: List of structural framing elements
    """
    doc = document
    if uidoc is None:
        uidoc = revit.uidoc
    
    # Check for pre-selected elements
    if selection_ids is None:
        selection_ids = uidoc.Selection.GetElementIds()
    
    if selection_ids:
        beams = []
        cat_id = ElementId(BuiltInCategory.OST_StructuralFraming)
        for eid in selection_ids:
            elem = doc.GetElement(eid)
            if elem and elem.Category and elem.Category.Id == cat_id:
                beams.append(elem)
        
        if beams:
            return beams
    
    # Collect all structural framing
    return list(
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_StructuralFraming)
        .WhereElementIsNotElementType()
        .ToElements()
    )


def collect_structural_columns(document, selection_ids=None, uidoc=None):
    """
    Collects structural column elements from a document.
    
    Args:
        document: Revit Document
        selection_ids: Optional list of ElementIds for pre-selection
        uidoc: UIDocument (optional, for checking current selection)
    
    Returns:
        list: List of structural column elements
    """
    doc = document
    if uidoc is None:
        uidoc = revit.uidoc
    
    # Check for pre-selected elements
    if selection_ids is None:
        selection_ids = uidoc.Selection.GetElementIds()
    
    if selection_ids:
        columns = []
        cat_id = ElementId(BuiltInCategory.OST_StructuralColumns)
        for eid in selection_ids:
            elem = doc.GetElement(eid)
            if elem and elem.Category and elem.Category.Id == cat_id:
                columns.append(elem)
        
        if columns:
            return columns
    
    # Collect all structural columns
    return list(
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_StructuralColumns)
        .WhereElementIsNotElementType()
        .ToElements()
    )


def get_type_info(element):
    """
    Retrieves comprehensive type information from a structural element.
    
    Args:
        element: Structural framing or column element
    
    Returns:
        dict or None: Dictionary with 'type_name', 'family_name', and 'family_symbol' keys
    """
    try:
        # Get element's type
        type_id = element.GetTypeId()
        if not type_id:
            return None
        
        element_type = element.Document.GetElement(type_id)
        if not element_type:
            return None
        
        # Get family name
        family_name = None
        if hasattr(element_type, 'Family') and element_type.Family:
            family_name = element_type.Family.Name
        
        # Get type name using multiple methods
        type_name = None
        
        # Method 1: Direct Name property
        if hasattr(element_type, 'Name'):
            type_name = element_type.Name
        
        # Method 2: SYMBOL_NAME_PARAM
        if not type_name:
            name_param = element_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
            if name_param and name_param.HasValue:
                type_name = name_param.AsString()
        
        # Method 3: ALL_MODEL_TYPE_NAME
        if not type_name:
            name_param = element_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
            if name_param and name_param.HasValue:
                type_name = name_param.AsString()
        
        if type_name and family_name:
            return {
                'type_name': type_name,
                'family_name': family_name,
                'family_symbol': element_type if isinstance(element_type, FamilySymbol) else None
            }
        
        return None
        
    except Exception as e:
        return None


def get_family_symbol(element):
    """
    Retrieves the FamilySymbol from an element.
    
    Args:
        element: Revit element
    
    Returns:
        FamilySymbol or None
    """
    try:
        type_id = element.GetTypeId()
        if type_id:
            return element.Document.GetElement(type_id)
        return None
    except Exception:
        # Element may not have a type or access failed
        return None


def extract_mark_from_type_name(type_name):
    """
    Extracts the mark value from Type Name parameter.
    Pattern: Extract numbers after "." or "-" from type names like "G9-99" or "G5.99"
    
    Args:
        type_name (str): The Type Name parameter value
    
    Returns:
        str: The extracted mark value or None if pattern not found
    """
    if not type_name:
        return None
    
    # Pattern to match numbers after "." or "-"
    # Examples: "G9-99" -> "99", "G5.99" -> "99", "GA1-6-CJ" -> "6"
    # Also handles: "B4-4(fc 40)-CI" -> "4", "B4-40fc 35)" -> "40"
    pattern = r'[.-](\d+)(?:-C[IJ])?'
    match = re.search(pattern, type_name)
    
    if match:
        return match.group(1)
    
    return None


def check_family_type_exists(host_doc, family_name, type_name):
    """
    Checks if a specific family and type exist in the host Revit document.
    
    Args:
        host_doc: The host Revit document to search in
        family_name (str): The name of the family to look for
        type_name (str): The name of the type within the family
    
    Returns:
        FamilySymbol or None: The matching FamilySymbol if found, None otherwise.
    """
    if not family_name or not type_name:
        return None
    
    try:
        all_symbols = FilteredElementCollector(host_doc)\
            .OfClass(FamilySymbol)\
            .WhereElementIsElementType()\
            .ToElements()
        
        for symbol in all_symbols:
            try:
                if not (symbol and hasattr(symbol, 'Family') and symbol.Family):
                    continue
                
                family = symbol.Family
                if not hasattr(family, 'Name'):
                    continue
                
                current_family_name = family.Name
                
                # Check if this is the family we're looking for
                if current_family_name == family_name:
                    # Get symbol name
                    symbol_name = None
                    
                    if hasattr(symbol, 'Name'):
                        symbol_name = symbol.Name
                    
                    if not symbol_name:
                        name_param = symbol.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                        if name_param and name_param.HasValue:
                            symbol_name = name_param.AsString()
                    
                    if symbol_name == type_name:
                        return symbol
                        
            except Exception:
                # Skip symbols that fail to process
                continue
        
        return None
        
    except Exception:
        # Collection or document access failed
        return None
