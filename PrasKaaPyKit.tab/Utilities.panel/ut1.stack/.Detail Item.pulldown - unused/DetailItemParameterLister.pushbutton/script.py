# -*- coding: utf-8 -*-
"""
Detail Item Parameter Lister - Lists all parameters of selected detail item instances.
Displays parameters in a clean, organized format with type classification and values.
"""

__title__ = 'Detail Item Parameter Lister'
__author__ = 'PrasKaa Team'
__doc__ = "Lists all parameters of selected detail item instances with clean formatting."

import clr
import sys
import os

# Revit API imports
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *

# PyRevit imports
from pyrevit import revit, forms, script, output
from pyrevit.revit import doc, uidoc

# Setup
logger = script.get_logger()
output_window = output.get_output()

# Unit conversion constants (feet to mm)
FEET_TO_MM = 304.8
FEET_TO_CM = 30.48
FEET_TO_M = 0.3048

def convert_feet_to_mm(feet_value):
    """Convert feet to millimeters."""
    return feet_value * FEET_TO_MM

def convert_feet_to_cm(feet_value):
    """Convert feet to centimeters."""
    return feet_value * FEET_TO_CM

def convert_feet_to_m(feet_value):
    """Convert feet to meters."""
    return feet_value * FEET_TO_M

def format_length_value(feet_value, max_decimals=2):
    """
    Format length value with appropriate unit conversion.
    Returns value in mm for small dimensions, m for large dimensions.
    """
    if feet_value is None:
        return "None"

    try:
        # Convert to mm
        mm_value = convert_feet_to_mm(feet_value)

        # Use meters for large values (> 1000mm)
        if mm_value >= 1000:
            m_value = convert_feet_to_m(feet_value)
            return str(round(m_value, max_decimals)) + " m"
        else:
            return str(round(mm_value, max_decimals)) + " mm"
    except:
        return str(feet_value) + " ft"

def robust_get_parameter_value(param):
    """
    Extract parameter value with comprehensive error handling.
    Returns tuple: (value, storage_type_str, has_value, error_msg)
    """
    if not param:
        return None, "None", False, "Parameter is None"

    try:
        storage_type = param.StorageType
        storage_type_str = str(storage_type)
        has_value = param.HasValue

        if not has_value:
            return None, storage_type_str, False, None

        # Extract value based on storage type
        if storage_type == StorageType.Double:
            value = param.AsDouble()
        elif storage_type == StorageType.Integer:
            value = param.AsInteger()
        elif storage_type == StorageType.String:
            value = param.AsString()
        elif storage_type == StorageType.ElementId:
            elem_id = param.AsElementId()
            if elem_id and elem_id != ElementId.InvalidElementId:
                try:
                    elem = doc.GetElement(elem_id)
                    value = elem.Name if elem else "<Element Not Found>"
                except:
                    value = "<ElementId: " + str(elem_id.IntegerValue) + ">"
            else:
                value = "<None>"
        else:
            return None, storage_type_str, True, "Unsupported storage type: " + str(storage_type)

        return value, storage_type_str, True, None

    except Exception as e:
        return None, "Unknown", False, "Extraction failed: " + str(e)

def safe_get_parameter_name(param):
    """
    Safely extract parameter name with multiple fallback strategies.
    """
    if not param:
        return "Invalid Parameter"

    # Primary: Try Definition.Name
    try:
        if param.Definition:
            return param.Definition.Name
    except AttributeError:
        pass
    except Exception as e:
        logger.warning("Error accessing Definition.Name: " + str(e))

    # Fallback 1: Try parameter Id
    try:
        param_id = param.Id
        if param_id:
            return "Parameter_" + str(param_id.IntegerValue)
    except:
        pass

    # Fallback 2: Generic description
    try:
        storage_type = str(param.StorageType)
        return "Unnamed_" + str(storage_type) + "_Parameter"
    except:
        return "Unnamed_Parameter"

def classify_parameter_type(element, param):
    """
    Classify parameter as instance or type parameter.
    Returns dict with classification info.
    """
    classification = {
        'is_instance_param': False,
        'is_type_param': False,
        'param_level': 'unknown'
    }

    if not param or not element:
        return classification

    try:
        # Check if parameter exists on instance level
        instance_param = element.LookupParameter(param.Definition.Name)
        if instance_param and instance_param.Id == param.Id:
            classification['is_instance_param'] = True
            classification['param_level'] = 'instance'
            return classification

        # Check if parameter exists on type level
        if isinstance(element, FamilyInstance):
            type_param = element.Symbol.LookupParameter(param.Definition.Name)
            if type_param and type_param.Id == param.Id:
                classification['is_type_param'] = True
                classification['param_level'] = 'type'
                return classification

        elif isinstance(element, FamilySymbol):
            classification['is_type_param'] = True
            classification['param_level'] = 'type'
            return classification

    except Exception as e:
        classification['param_level'] = 'error'

    return classification

def extract_detail_item_parameters(element):
    """
    Extract all parameters from a detail item element with robust error handling.
    Returns organized parameter information.
    """
    parameters_info = {
        'instance_parameters': {},
        'type_parameters': {},
        'extraction_stats': {
            'total_attempted': 0,
            'successful': 0,
            'failed': 0,
            'no_value': 0,
            'errors': []
        }
    }

    try:
        # Extract instance parameters
        if hasattr(element, 'Parameters'):
            for param in element.Parameters:
                parameters_info['extraction_stats']['total_attempted'] += 1

                param_name = safe_get_parameter_name(param)
                value, storage_type, has_value, error_msg = robust_get_parameter_value(param)

                if error_msg:
                    parameters_info['extraction_stats']['failed'] += 1
                    parameters_info['extraction_stats']['errors'].append(param_name + ": " + error_msg)
                elif not has_value:
                    parameters_info['extraction_stats']['no_value'] += 1
                else:
                    parameters_info['extraction_stats']['successful'] += 1

                # Classify parameter
                classification = classify_parameter_type(element, param)

                param_info = {
                    'value': value,
                    'storage_type': storage_type,
                    'has_value': has_value,
                    'classification': classification,
                    'extraction_error': error_msg
                }

                if classification['is_instance_param']:
                    parameters_info['instance_parameters'][param_name] = param_info
                elif classification['is_type_param']:
                    parameters_info['type_parameters'][param_name] = param_info
                else:
                    # Default to instance if classification fails
                    parameters_info['instance_parameters'][param_name] = param_info

        # Extract type parameters for FamilyInstance
        if isinstance(element, FamilyInstance) and element.Symbol:
            try:
                for param in element.Symbol.Parameters:
                    param_name = safe_get_parameter_name(param)

                    # Skip if already processed as instance parameter
                    if param_name in parameters_info['instance_parameters']:
                        continue

                    parameters_info['extraction_stats']['total_attempted'] += 1

                    value, storage_type, has_value, error_msg = robust_get_parameter_value(param)

                    if error_msg:
                        parameters_info['extraction_stats']['failed'] += 1
                        parameters_info['extraction_stats']['errors'].append("Type param " + param_name + ": " + error_msg)
                    elif not has_value:
                        parameters_info['extraction_stats']['no_value'] += 1
                    else:
                        parameters_info['extraction_stats']['successful'] += 1

                    param_info = {
                        'value': value,
                        'storage_type': storage_type,
                        'has_value': has_value,
                        'classification': {'is_type_param': True, 'param_level': 'type'},
                        'extraction_error': error_msg
                    }

                    parameters_info['type_parameters'][param_name] = param_info

            except Exception as e:
                error_msg = "Type parameter extraction failed: " + str(e)
                parameters_info['extraction_stats']['errors'].append(error_msg)
                logger.error(error_msg)

    except Exception as e:
        error_msg = "Critical error in parameter extraction: " + str(e)
        parameters_info['extraction_stats']['errors'].append(error_msg)
        logger.error(error_msg)

    return parameters_info

def get_type_name_from_instance(instance):
    """
    Get type name from instance element with multiple fallback strategies.
    Based on proven patterns from TypeMarkChecker script.
    """
    try:
        # Method 1: Direct access for FamilyInstance
        if isinstance(instance, FamilyInstance):
            if hasattr(instance, 'Symbol') and instance.Symbol:
                # Try SYMBOL_NAME_PARAM first (most reliable)
                try:
                    type_param = instance.Symbol.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                    if type_param and type_param.HasValue:
                        type_name = type_param.AsString()
                        if type_name and type_name.strip():
                            return type_name.strip()
                except:
                    pass

                # Fallback to Symbol.Name
                try:
                    if hasattr(instance.Symbol, 'Name') and instance.Symbol.Name:
                        return instance.Symbol.Name
                except:
                    pass

        # Method 2: Get element type and extract name
        try:
            type_id = instance.GetTypeId()
            if type_id and type_id != ElementId.InvalidElementId:
                element_type = doc.GetElement(type_id)
                if element_type:
                    # Try SYMBOL_NAME_PARAM on the type
                    try:
                        type_param = element_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                        if type_param and type_param.HasValue:
                            type_name = type_param.AsString()
                            if type_name and type_name.strip():
                                return type_name.strip()
                    except:
                        pass

                    # Fallback to element type Name
                    try:
                        if hasattr(element_type, 'Name') and element_type.Name:
                            return element_type.Name
                    except:
                        pass
        except:
            pass

        # Method 3: Try Type Mark (for elements that have it)
        try:
            type_mark_param = instance.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)
            if type_mark_param and type_mark_param.HasValue:
                type_mark = type_mark_param.AsString()
                if type_mark and type_mark.strip():
                    return type_mark.strip()
        except:
            pass

        # Final fallback
        return "Unknown Type"

    except Exception as e:
        return "Error: " + str(e)

def display_element_info(element):
    """Display basic element information."""
    output_window.print_md("# Detail Item Parameter Lister")
    output_window.print_md("---")

    if isinstance(element, FamilyInstance):
        output_window.print_md("## Selected Detail Item Instance:")
        try:
            name = element.Name if element.Name else "Unnamed"
            output_window.print_md("**Name:** " + name)
        except:
            output_window.print_md("**Name:** <Error reading name>")

        try:
            category = element.Category.Name if element.Category else "N/A"
            output_window.print_md("**Category:** " + category)
        except:
            output_window.print_md("**Category:** <Error reading category>")

        try:
            family_name = element.Symbol.Family.Name if element.Symbol and element.Symbol.Family else "N/A"
            output_window.print_md("**Family:** " + family_name)
        except:
            output_window.print_md("**Family:** <Error reading family>")

        # Use the new type name extraction function
        type_name = get_type_name_from_instance(element)
        output_window.print_md("**Type:** " + type_name)

        output_window.print_md("**Element ID:** " + str(output_window.linkify(element.Id)))

    elif isinstance(element, FamilySymbol):
        output_window.print_md("## Selected Detail Item Type:")
        try:
            family_name = element.Family.Name if element.Family else "N/A"
            output_window.print_md("**Family:** " + family_name)
        except:
            output_window.print_md("**Family:** <Error reading family>")

        try:
            type_name = element.Name if element.Name else "Unnamed"
            output_window.print_md("**Type Name:** " + type_name)
        except:
            output_window.print_md("**Type Name:** <Error reading type name>")

        output_window.print_md("**Element ID:** " + str(output_window.linkify(element.Id)))

    else:
        output_window.print_md("## Selected Element:")
        try:
            name = element.Name if element.Name else "Unnamed"
            output_window.print_md("**Name:** " + name)
        except:
            output_window.print_md("**Name:** <Error reading name>")

        try:
            category = element.Category.Name if element.Category else "N/A"
            output_window.print_md("**Category:** " + category)
        except:
            output_window.print_md("**Category:** <Error reading category>")

        output_window.print_md("**Element ID:** " + str(output_window.linkify(element.Id)))

    output_window.print_md("---")

def display_parameters(parameters_info):
    """Display parameters in organized format."""
    output_window.print_md("### Parameters:")

    # Display instance parameters first
    instance_params = parameters_info.get('instance_parameters', {})
    if instance_params:
        output_window.print_md("**Instance Parameters:**")
        for param_name in sorted(instance_params.keys()):
            param_info = instance_params[param_name]
            display_single_parameter(param_name, param_info, "Instance")

    # Display type parameters
    type_params = parameters_info.get('type_parameters', {})
    if type_params:
        if instance_params:  # Add spacing if there were instance params
            output_window.print_md("")
        output_window.print_md("**Type Parameters:**")
        for param_name in sorted(type_params.keys()):
            param_info = type_params[param_name]
            display_single_parameter(param_name, param_info, "Type")

    # Display extraction statistics
    stats = parameters_info.get('extraction_stats', {})
    if stats:
        output_window.print_md("---")
        output_window.print_md("### Extraction Summary:")
        total_attempted = stats.get('total_attempted', 0)
        successful = stats.get('successful', 0)
        failed = stats.get('failed', 0)
        no_value = stats.get('no_value', 0)

        success_rate = (successful / total_attempted * 100) if total_attempted > 0 else 0

        output_window.print_md("- **Total Parameters:** " + str(total_attempted))
        output_window.print_md("- **Successfully Extracted:** " + str(successful))
        output_window.print_md("- **No Value:** " + str(no_value))
        output_window.print_md("- **Failed:** " + str(failed))
        output_window.print_md("- **Success Rate:** " + str(round(success_rate, 1)) + "%")
        # Show errors if any
        errors = stats.get('errors', [])
        if errors and len(errors) <= 5:  # Show up to 5 errors
            output_window.print_md("- **Errors:**")
            for error in errors[:5]:
                output_window.print_md("  - " + error)
            if len(errors) > 5:
                output_window.print_md("  - ... and " + str(len(errors) - 5) + " more errors")

def display_single_parameter(param_name, param_info, param_type_label):
    """Display a single parameter with proper formatting and unit conversion."""
    value = param_info.get('value')
    storage_type = param_info.get('storage_type', 'Unknown')
    has_value = param_info.get('has_value', False)
    error = param_info.get('extraction_error')

    if error:
        # Parameter with extraction error
        output_window.print_md("- **" + param_name + "** (" + param_type_label + " Parameter): ❌ Error - " + error)
    elif not has_value:
        # Parameter without value
        output_window.print_md("- **" + param_name + "** (" + param_type_label + " Parameter): ⚠️ <No Value> (Storage: " + storage_type + ")")
    else:
        # Parameter with value - apply unit conversion for length parameters
        display_value = format_parameter_value(value, storage_type, param_name)

        output_window.print_md("- **" + param_name + "** (" + param_type_label + " Parameter): `" + display_value + "` (Storage: " + storage_type + ")")

def format_parameter_value(value, storage_type, param_name):
    """Format parameter value with appropriate unit conversion."""
    if value is None:
        return "None"

    try:
        # Convert length/distance parameters from feet to mm/m
        if storage_type == "Double":
            # Check if this is likely a length parameter by name
            length_keywords = ['length', 'width', 'height', 'depth', 'diameter', 'radius',
                             'spacing', 'clear', 'cover', 'offset', 'distance', 'size',
                             'location', 'position', 'coordinate', 'dimension']

            param_lower = param_name.lower()
            is_length_param = any(keyword in param_lower for keyword in length_keywords)

            if is_length_param and isinstance(value, (int, float)):
                return format_length_value(value)
            else:
                # Regular float formatting
                return str(round(value, 6)).rstrip('0').rstrip('.')
        else:
            # Non-length parameters (Integer, String, ElementId)
            return str(value)

    except Exception as e:
        # Fallback to basic string conversion
        return str(value)

def main():
    """Main execution function for the Detail Item Parameter Lister."""
    output_window.set_title("Detail Item Parameter Lister")
    output_window.freeze()

    try:
        selected_elements = revit.get_selection().elements

        target_element = None

        if not selected_elements:
            forms.alert("Please select a Detail Item in the model.", exitscript=True)
            return
        elif len(selected_elements) > 1:
            target_element = forms.select_one_object(
                selected_elements,
                title="Select Detail Item to List Parameters",
                prompt="Multiple elements selected. Please choose one:",
                key_param=lambda x: getattr(x, 'Name', 'Unnamed Element')
            )
            if not target_element:
                forms.alert("No element selected. Exiting script.", exitscript=True)
                return
        else:
            target_element = selected_elements[0]

        # Validate that it's a detail item or similar element
        if not isinstance(target_element, (FamilyInstance, FamilySymbol)):
            forms.alert(
                "Selected element is not a Family Instance or Family Type. "
                "Please select a Detail Item or similar family-based element.",
                exitscript=True
            )
            return

        # Display element information
        display_element_info(target_element)

        # Extract and display parameters
        parameters_info = extract_detail_item_parameters(target_element)
        display_parameters(parameters_info)

        # Log completion
        stats = parameters_info.get('extraction_stats', {})
        successful = stats.get('successful', 0)
        total = stats.get('total_attempted', 0)
        logger.info("Parameter listing completed: " + str(successful) + "/" + str(total) + " parameters extracted successfully")

    except Exception as e:
        logger.error("Critical error in Detail Item Parameter Lister: " + str(e))
        forms.alert("An error occurred: " + str(e), title="Error")
    finally:
        output_window.unfreeze()

if __name__ == '__main__':
    main()