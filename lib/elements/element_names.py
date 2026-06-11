# -*- coding: utf-8 -*-
"""
Element Name Extraction Utilities.

Provides robust methods for extracting Family Name and Type Name from Revit elements.
Based on proven patterns from LOG-UTIL-ELEMENT-001-v1 documentation.

Usage:
    from elements.element_names import get_family_name, get_type_name
"""

from Autodesk.Revit.DB import (
    BuiltInParameter,
    FamilyInstance,
    ElementId,
    Element
)


def get_type_name(element):
    """
    Get type name from element with multiple fallback strategies.
    
    Most reliable method is to get Symbol's SYMBOL_NAME_PARAM.
    
    Args:
        element: Revit element
        
    Returns:
        str: Type name or "Unknown Type" if not found
    """
    try:
        # Method 1: Get from Symbol's SYMBOL_NAME_PARAM (most reliable for FamilyInstance)
        if isinstance(element, FamilyInstance):
            if hasattr(element, 'Symbol') and element.Symbol:
                try:
                    type_param = element.Symbol.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                    if type_param and type_param.HasValue:
                        type_name = type_param.AsString()
                        if type_name and type_name.strip():
                            return type_name.strip()
                except:
                    pass
                
                try:
                    if hasattr(element.Symbol, 'Name') and element.Symbol.Name:
                        return element.Symbol.Name
                except:
                    pass
        
        # Method 2: Get from element type via GetTypeId()
        try:
            type_id = element.GetTypeId()
            if type_id and type_id != ElementId.InvalidElementId:
                element_type = element.Document.GetElement(type_id)
                if element_type:
                    try:
                        type_param = element_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                        if type_param and type_param.HasValue:
                            type_name = type_param.AsString()
                            if type_name and type_name.strip():
                                return type_name.strip()
                    except:
                        pass
                    
                    try:
                        if hasattr(element_type, 'Name') and element_type.Name:
                            return element_type.Name
                    except:
                        pass
        except:
            pass
        
        # Method 3: Try element.Name directly
        try:
            if hasattr(element, 'Name') and element.Name:
                return element.Name
        except:
            pass
        
        return "Unknown Type"
        
    except Exception:
        return "Unknown Type"


def get_family_name(element):
    """
    Get family name from element.
    
    For FamilyInstance, get from Symbol.Family.Name.
    For other elements, try ElementType.FamilyName.
    
    Args:
        element: Revit element
        
    Returns:
        str: Family name or "Unknown Family" if not found
    """
    try:
        # Method 1: For FamilyInstance, get from Symbol.Family
        if isinstance(element, FamilyInstance):
            if hasattr(element, 'Symbol') and element.Symbol:
                try:
                    if (hasattr(element.Symbol, 'Family') and 
                        element.Symbol.Family and
                        hasattr(element.Symbol.Family, 'Name') and 
                        element.Symbol.Family.Name):
                        return element.Symbol.Family.Name
                except:
                    pass
        
        # Method 2: Get from ElementType via GetTypeId()
        try:
            type_id = element.GetTypeId()
            if type_id and type_id != ElementId.InvalidElementId:
                element_type = element.Document.GetElement(type_id)
                if element_type and hasattr(element_type, 'FamilyName'):
                    family_name = element_type.FamilyName
                    if family_name:
                        return family_name
        except:
            pass
        
        # Method 3: Try ELEM_FAMILY_PARAM
        try:
            family_param = element.get_Parameter(BuiltInParameter.ELEM_FAMILY_PARAM)
            if family_param and family_param.HasValue:
                family_elem = element.Document.GetElement(family_param.AsElementId())
                if family_elem and hasattr(family_elem, 'Name'):
                    return family_elem.Name
        except:
            pass
        
        return "Unknown Family"
        
    except Exception:
        return "Unknown Family"


def get_family_and_type_name(element):
    """
    Get both Family name and Type name from element.
    
    Args:
        element: Revit element
        
    Returns:
        tuple: (Family Name, Type Name)
    """
    return get_family_name(element), get_type_name(element)
