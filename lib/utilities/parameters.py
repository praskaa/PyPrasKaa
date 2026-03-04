"""
Parameter handling utilities for Revit elements.

Migrated from pyChilizer database.py module.
Provides functions for extracting and working with parameter values.
"""

from pyrevit import revit, DB


def get_param_value_as_string(p):
    """
    Get the value of the element parameter as a string, regardless of the storage type.

    Args:
        p: Revit Parameter object

    Returns:
        str: Parameter value as string, or None if no value
    """
    if p.HasValue:
        if p_storage_type(p) == "ElementId":
            if p.Definition.Name == "Category":
                return p.AsValueString()
            else:
                return p.AsElementId().IntegerValue
        elif p_storage_type(p) == "Integer":
            return p.AsInteger()
        elif p_storage_type(p) == "Double":
            return p.AsValueString()
        elif p_storage_type(p) == "String":
            return p.AsString()
    else:
        return


def get_param_value_by_storage_type(p):
    """
    Get the value of the element parameter by storage type.

    Args:
        p: Revit Parameter object

    Returns:
        Value in appropriate type, or None if no value
    """
    if p.HasValue:
        if p_storage_type(p) == "ElementId":
            return p.AsElementId()
        elif p_storage_type(p) == "Integer":
            return p.AsInteger()
        elif p_storage_type(p) == "Double":
            return p.AsDouble()
        elif p_storage_type(p) == "String":
            return p.AsString()
    else:
        return


def p_storage_type(param):
    """
    Get the storage type of a parameter as string.

    Args:
        param: Revit Parameter object

    Returns:
        str: Storage type ("ElementId", "Integer", "Double", "String")
    """
    return param.StorageType.ToString()


def get_parameter_from_name(el, param_name):
    """
    Get parameter object from element by parameter name.

    Args:
        el: Revit Element
        param_name: str, parameter definition name

    Returns:
        Parameter object or None
    """
    params = el.Parameters
    for p in params:
        if p.Definition.Name == param_name:
            return p