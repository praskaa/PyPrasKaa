# -*- coding: utf-8 -*-
"""
Parameter Finder Utility Module

This module provides utility functions for finding and working with Revit parameters,
including shared parameters and project parameters.
"""

from pyrevit import DB


def find_parameter_element(doc, parameter_name):
    """
    Find a ParameterElement by name from the document.

    This function searches through all ParameterElement objects in the document
    to find one with the specified name. This works for both shared parameters
    and project parameters.

    Args:
        doc (DB.Document): The Revit document to search in
        parameter_name (str): The name of the parameter to find

    Returns:
        DB.ParameterElement or None: The found parameter element, or None if not found

    Example:
        >>> param_elem = find_parameter_element(doc, "Sub Category")
        >>> if param_elem:
        ...     param_id = param_elem.Id
        ...     # Use parameter ID for filter creation
    """
    for param_elem in DB.FilteredElementCollector(doc).OfClass(DB.ParameterElement):
        if param_elem.Name == parameter_name:
            return param_elem
    return None


def get_parameter_definition(parameter_element):
    """
    Get the parameter definition from a ParameterElement.

    Args:
        parameter_element (DB.ParameterElement): The parameter element

    Returns:
        DB.Definition: The parameter definition

    Raises:
        AttributeError: If the parameter element doesn't have a definition
    """
    return parameter_element.GetDefinition()


def get_parameter_type_info(parameter_element):
    """
    Get comprehensive type information for a parameter.

    This function handles both old (pre-2022) and new (2022+) Revit API versions
    to provide consistent parameter type information.

    Args:
        parameter_element (DB.ParameterElement): The parameter element

    Returns:
        dict: Dictionary containing type information with keys:
            - 'type_id': ForgeTypeId or ParameterType
            - 'type_name': String representation of the type
            - 'is_text': Boolean indicating if parameter is text type
            - 'is_number': Boolean indicating if parameter is numeric type
            - 'is_integer': Boolean indicating if parameter is integer type
            - 'is_boolean': Boolean indicating if parameter is yes/no type

    Example:
        >>> type_info = get_parameter_type_info(param_elem)
        >>> if type_info['is_text']:
        ...     print("Parameter is text type")
    """
    definition = get_parameter_definition(parameter_element)

    try:
        # Revit 2022+ using ForgeTypeId
        data_type = definition.GetDataType()
        type_id = data_type
        type_name = data_type.TypeId if hasattr(data_type, 'TypeId') else str(data_type)

        return {
            'type_id': type_id,
            'type_name': type_name,
            'is_text': data_type == DB.SpecTypeId.String.Text,
            'is_number': data_type == DB.SpecTypeId.Number,
            'is_integer': data_type == DB.SpecTypeId.Int.Integer,
            'is_boolean': data_type == DB.SpecTypeId.Boolean.YesNo
        }
    except AttributeError:
        # Fallback for older Revit versions (pre-2022)
        param_type = definition.ParameterType

        return {
            'type_id': param_type,
            'type_name': str(param_type),
            'is_text': param_type == DB.ParameterType.Text,
            'is_number': param_type == DB.ParameterType.Number,
            'is_integer': param_type == DB.ParameterType.Integer,
            'is_boolean': param_type == DB.ParameterType.YesNo
        }