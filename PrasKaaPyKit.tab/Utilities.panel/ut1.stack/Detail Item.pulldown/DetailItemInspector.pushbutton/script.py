# -*- coding: utf-8 -*-
"""
Detail Item Inspector - Inspects parameters of selected detail item instances or family types.
Allows reading parameters from selected instances in the model or types from the Project Browser.
"""

__title__ = 'Detail Item Inspector'
__author__ = 'PrasKaa Team'
__doc__ = "Inspects parameters of selected detail item instances or family types, and lists all available types."

import clr
import sys
import os

# Add extension root to Python path for library imports
# From: PrasKaaPyKit.tab/Utilities.panel/Detail Item.pulldown/DetailItemInspector.pushbutton/script.py
# To: extension_root/lib/parameters/
extension_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if extension_root not in sys.path:
    sys.path.insert(0, extension_root)

# Revit API imports
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *

# PyRevit imports
from pyrevit import revit, forms, script, output
from pyrevit.revit import doc, uidoc

# Parameter Setting Framework import
from lib.parameters import ParameterSettingFramework

# Direct implementation of type name extraction (no external imports)
def get_type_name_from_instance(instance):
    """
    Extract type name from instance element with multiple fallback strategies.
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

# Setup
logger = script.get_logger()
output_window = output.get_output()

# Initialize Parameter Setting Framework
param_framework = ParameterSettingFramework(doc, logger)

def get_parameter_value(param):
    """
    Extract parameter value based on its storage type with robust error handling.
    Based on LOG-UTIL-PARAM-005-v1-robust-parameter-extraction patterns.
    """
    if not param:
        return None

    try:
        storage_type = param.StorageType
    except Exception as e:
        logger.warning("Error accessing parameter storage type: {}".format(str(e)))
        return None

    try:
        has_value = param.HasValue
        if not has_value:
            return None
    except Exception as e:
        logger.warning("Error checking parameter HasValue: {}".format(str(e)))
        return None

    try:
        if storage_type == StorageType.Double:
            return param.AsDouble()
        elif storage_type == StorageType.Integer:
            return param.AsInteger()
        elif storage_type == StorageType.String:
            value = param.AsString()
            return value if value else None
        elif storage_type == StorageType.ElementId:
            elem_id = param.AsElementId()
            if elem_id and elem_id != ElementId.InvalidElementId:
                try:
                    elem = doc.GetElement(elem_id)
                    return elem.Name if elem else "<Element Not Found>"
                except:
                    return "<Element Access Error>"
            return "<None>"
        else:
            return None
    except Exception as e:
        logger.warning("Error extracting parameter value: {}".format(str(e)))
        return None

def set_parameter_value(element, param_name, new_value):
    """
    Sets the value of a parameter on a given Revit element using the standardized framework.
    This function now uses the ParameterSettingFramework for robust parameter setting.
    """
    try:
        # Use the framework for parameter setting
        success = param_framework.set_parameter(
            element=element,
            param_name=param_name,
            value=new_value,
            validate=True  # Enable validation for safety
        )
        return success
    except Exception as e:
        logger.error("Framework error setting parameter '{}' to '{}': {}".format(param_name, new_value, str(e)))
        return False

def change_instance_type(instance, new_type_symbol):
    """
    Changes the FamilySymbol (type) of a FamilyInstance.
    """
    if not isinstance(instance, FamilyInstance):
        logger.warning("Element is not a FamilyInstance. Cannot change type.")
        return False
    
    if instance.Symbol.Id == new_type_symbol.Id:
        logger.info("Instance '{}' is already of type '{}'. No change needed.".format(instance.Name, new_type_symbol.Name))
        return True

    t = Transaction(doc, "Change Instance Type")
    try:
        t.Start()
        instance.ChangeTypeId(new_type_symbol.Id)
        t.Commit()
        logger.info("Instance '{}' type changed to '{}' successfully.".format(instance.Name, new_type_symbol.Name))
        return True
    except Exception as e:
        logger.error("Error changing type for instance '{}' to '{}': {}".format(instance.Name, new_type_symbol.Name, str(e)))
        if t.HasStarted() and t.GetStatus() == TransactionStatus.Started:
            t.RollBack()
        return False

def get_element_parameters(element):
    """
    Extracts all parameters from a given Revit element (instance or type) with robust error handling.
    Based on LOG-UTIL-PARAM-005-v1-robust-parameter-extraction patterns.
    Returns a dictionary of parameter name to its value and storage type.
    """
    parameters_info = {}
    extraction_stats = {
        'total_attempted': 0,
        'successful': 0,
        'failed': 0,
        'no_value': 0,
        'errors': []
    }

    try:
        # Get instance parameters
        if hasattr(element, 'Parameters'):
            for param in element.Parameters:
                extraction_stats['total_attempted'] += 1

                try:
                    # Safe parameter name extraction
                    param_name = safe_get_parameter_name(param)
                    param_value = get_parameter_value(param)

                    if param_value is not None:
                        extraction_stats['successful'] += 1
                    else:
                        extraction_stats['no_value'] += 1

                    parameters_info[param_name] = {
                        'value': param_value,
                        'storage_type': str(param.StorageType),
                        'is_type_param': False
                    }
                except Exception as e:
                    extraction_stats['failed'] += 1
                    extraction_stats['errors'].append("Instance param error: {}".format(str(e)))
                    logger.warning("Error reading parameter: {}".format(str(e)))
                    continue

        # If it's an instance, also get its type parameters
        if isinstance(element, FamilyInstance):
            try:
                elem_type = doc.GetElement(element.GetTypeId())
                if elem_type and hasattr(elem_type, 'Parameters'):
                    for param in elem_type.Parameters:
                        extraction_stats['total_attempted'] += 1

                        try:
                            param_name = safe_get_parameter_name(param)

                            # Skip if already extracted as instance parameter
                            if param_name in parameters_info:
                                continue

                            param_value = get_parameter_value(param)

                            if param_value is not None:
                                extraction_stats['successful'] += 1
                            else:
                                extraction_stats['no_value'] += 1

                            parameters_info[param_name] = {
                                'value': param_value,
                                'storage_type': str(param.StorageType),
                                'is_type_param': True
                            }
                        except Exception as e:
                            extraction_stats['failed'] += 1
                            extraction_stats['errors'].append("Type param error: {}".format(str(e)))
                            logger.warning("Error reading type parameter: {}".format(str(e)))
                            continue
            except Exception as e:
                logger.error("Error accessing type parameters: {}".format(str(e)))

        elif isinstance(element, FamilySymbol):
            if hasattr(element, 'Parameters'):
                for param in element.Parameters:
                    extraction_stats['total_attempted'] += 1

                    try:
                        param_name = safe_get_parameter_name(param)
                        param_value = get_parameter_value(param)

                        if param_value is not None:
                            extraction_stats['successful'] += 1
                        else:
                            extraction_stats['no_value'] += 1

                        parameters_info[param_name] = {
                            'value': param_value,
                            'storage_type': str(param.StorageType),
                            'is_type_param': True
                        }
                    except Exception as e:
                        extraction_stats['failed'] += 1
                        extraction_stats['errors'].append("Family symbol param error: {}".format(str(e)))
                        logger.warning("Error reading family symbol parameter: {}".format(str(e)))
                        continue

    except Exception as e:
        logger.error("Critical error in parameter extraction: {}".format(str(e)))
        extraction_stats['errors'].append("Critical error: {}".format(str(e)))

    # Add extraction statistics
    parameters_info['_extraction_stats'] = extraction_stats

    return parameters_info

def safe_get_parameter_name(param):
    """
    Safely extract parameter name with multiple fallback strategies.
    Based on LOG-UTIL-PARAM-005-v1-robust-parameter-extraction patterns.
    """
    if not param:
        return "Invalid Parameter"

    # Primary: Try Definition.Name
    try:
        if param.Definition:
            name = param.Definition.Name
            if name:
                return name
    except:
        pass

    # Fallback 1: Try parameter Id
    try:
        param_id = param.Id
        if param_id:
            return "Parameter_{}".format(param_id.IntegerValue)
    except:
        pass

    # Fallback 2: Generic description
    try:
        storage_type = str(param.StorageType)
        return "Unnamed_{}_Parameter".format(storage_type.replace('StorageType.', ''))
    except:
        return "Unnamed_Parameter"

def get_family_types(element):
    """
    Retrieves all FamilySymbol (types) belonging to the family of the given element.
    """
    family = None
    if isinstance(element, FamilyInstance):
        family = element.Symbol.Family
    elif isinstance(element, FamilySymbol):
        family = element.Family
    
    if family:
        collector = FilteredElementCollector(doc).OfClass(FamilySymbol)
        family_types = [fs for fs in collector if fs.Family.Id == family.Id]
        # Safe sorting with error handling
        try:
            return sorted(family_types, key=lambda x: x.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString())
        except:
            # Fallback if sorting fails
            return family_types
    return []

def display_element_info(element):
    """Displays information about the selected element in the pyRevit output."""
    output_window.print_md("# Detail Item Inspector")
    output_window.print_md("---")

    if isinstance(element, FamilyInstance):
        output_window.print_md("## Selected Instance:")
        try:
            output_window.print_md("**Name:** {}".format(element.Name))
        except AttributeError:
            output_window.print_md("**Name:** <No Name>")
        try:
            output_window.print_md("**Category:** {}".format(element.Category.Name if element.Category else "N/A"))
        except AttributeError:
            output_window.print_md("**Category:** <No Category>")
        try:
            output_window.print_md("**Family:** {}".format(element.Symbol.Family.Name))
        except AttributeError:
            output_window.print_md("**Family:** <No Family>")
        # Use the robust type name extraction utility
        type_name = get_type_name_from_instance(element)
        output_window.print_md("**Type:** {}".format(type_name))
        output_window.print_md("**Element ID:** {}".format(output_window.linkify(element.Id)))
    elif isinstance(element, FamilySymbol):
        output_window.print_md("## Selected Family Type:")
        try:
            output_window.print_md("**Family:** {}".format(element.Family.Name))
        except AttributeError:
            output_window.print_md("**Family:** <No Family>")
        try:
            output_window.print_md("**Type Name:** {}".format(element.Name))
        except AttributeError:
            output_window.print_md("**Type Name:** <No Name>")
        output_window.print_md("**Element ID:** {}".format(output_window.linkify(element.Id)))
    else:
        output_window.print_md("## Selected Element:")
        try:
            output_window.print_md("**Name:** {}".format(element.Name))
        except AttributeError:
            output_window.print_md("**Name:** <No Name>")
        try:
            output_window.print_md("**Category:** {}".format(element.Category.Name if element.Category else 'N/A'))
        except AttributeError:
            output_window.print_md("**Category:** <No Category>")
        output_window.print_md("**Element ID:** {}".format(output_window.linkify(element.Id)))

    output_window.print_md("---")
    output_window.print_md("### Parameters:")

    parameters = get_element_parameters(element)
    stats = parameters.get('_extraction_stats', {})

    if parameters and len(parameters) > 1:  # More than just stats
        # Display extraction summary
        total_attempted = stats.get('total_attempted', 0)
        successful = stats.get('successful', 0)
        failed = stats.get('failed', 0)
        no_value = stats.get('no_value', 0)

        if total_attempted > 0:
            success_rate = (successful / float(total_attempted) * 100) if total_attempted > 0 else 0
            output_window.print_md("**Extraction Summary:** {} attempted, {} successful, {} failed, {} no value ({:.1f}% success rate)".format(
                total_attempted, successful, failed, no_value, success_rate))

        # Display parameters
        param_count = 0
        for param_name in sorted(parameters.keys()):
            if param_name.startswith('_'):  # Skip metadata
                continue

            param_info = parameters[param_name]
            param_value = param_info['value']
            param_type_label = "Type Parameter" if param_info['is_type_param'] else "Instance Parameter"

            # Format value display
            if param_value is None:
                display_value = "⚠️"
            elif isinstance(param_value, float):
                # Check if it's a length parameter (feet values)
                if 'Location' in param_name or 'Width' in param_name or 'Height' in param_name or 'Length' in param_name:
                    # Convert feet to mm for display
                    if param_value >= 1.0:  # Likely a real dimension
                        mm_value = param_value * 304.8  # feet to mm
                        if mm_value >= 1000:
                            display_value = "{:.1f} m".format(param_value * 0.3048)  # feet to meters
                        else:
                            display_value = "{:.0f} mm".format(mm_value)
                    else:
                        display_value = "{:.4f}".format(param_value)
                else:
                    display_value = "{:.4f}".format(param_value)
            elif isinstance(param_value, str) and len(param_value) > 50:
                display_value = param_value[:47] + "..."
            else:
                display_value = str(param_value) if param_value is not None else "⚠️"

            output_window.print_md("- **{}** ({}): `{}` (Storage: {})".format(
                param_name, param_type_label, display_value, param_info['storage_type']))

            param_count += 1
            if param_count >= 50:  # Limit display to first 50 parameters
                remaining = len(parameters) - param_count - 1  # -1 for stats
                if remaining > 0:
                    output_window.print_md("- ... and {} more parameters".format(remaining))
                break

        # Show errors if any
        if stats.get('errors'):
            output_window.print_md("**Warnings/Errors:** {} issues found (check console for details)".format(len(stats['errors'])))
    else:
        output_window.print_md("No parameters found for this element.")

    output_window.print_md("---")
    output_window.print_md("### Available Family Types:")
    family_types = get_family_types(element)
    if family_types:
        for f_type in family_types:
            try:
                type_name = f_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
                output_window.print_md("- {} {}".format(type_name, output_window.linkify(f_type.Id)))
            except:
                output_window.print_md("- <No Name> {}".format(output_window.linkify(f_type.Id)))
    else:
        output_window.print_md("No other types found in this family.")

def interact_with_element(element):
    """Displays element info and provides options for interaction."""
    display_element_info(element)

    options = ["Override Parameter"]
    if isinstance(element, FamilyInstance):
        options.append("Change Instance Type")
    options.append("Done")

    while True:
        choice = forms.alert(
            "What would you like to do?",
            options=options,
            title="Detail Item Inspector Actions"
        )

        if choice == "Override Parameter":
            parameters = get_element_parameters(element)
            if not parameters or len(parameters) <= 1:  # Only stats
                forms.alert("No parameters available to override.", title="No Parameters")
                continue

            # Filter to modifiable parameters only
            modifiable_params = {}
            for param_name, param_info in parameters.items():
                if param_name.startswith('_'):  # Skip metadata
                    continue

                # Check if parameter can be modified
                try:
                    if param_info['is_type_param']:
                        # Type parameter - check if element is FamilyInstance
                        if isinstance(element, FamilyInstance):
                            # Check if type parameter is not read-only
                            elem_type = doc.GetElement(element.GetTypeId())
                            if elem_type:
                                type_param = elem_type.LookupParameter(param_name)
                                if type_param and not type_param.IsReadOnly:
                                    modifiable_params[param_name] = param_info
                        elif isinstance(element, FamilySymbol):
                            # FamilySymbol parameters
                            symbol_param = element.LookupParameter(param_name)
                            if symbol_param and not symbol_param.IsReadOnly:
                                modifiable_params[param_name] = param_info
                    else:
                        # Instance parameter
                        instance_param = element.LookupParameter(param_name)
                        if instance_param and not instance_param.IsReadOnly:
                            modifiable_params[param_name] = param_info
                except:
                    continue

            if not modifiable_params:
                forms.alert("No modifiable parameters found.", title="No Modifiable Parameters")
                continue

            param_names = sorted(modifiable_params.keys())
            selected_param_name = forms.SelectFromList.show(
                param_names,
                title="Select Parameter to Override",
                button_name="Select"
            )

            if selected_param_name:
                current_value = modifiable_params[selected_param_name]['value']
                param_type = modifiable_params[selected_param_name]['storage_type']

                # Format default value based on storage type
                if current_value is not None:
                    try:
                        if param_type == "StorageType.Double":
                            default_value = "{:.4f}".format(float(current_value))
                        elif param_type == "StorageType.Integer":
                            default_value = str(int(float(current_value)))
                        else:
                            default_value = str(current_value)
                    except (ValueError, TypeError):
                        default_value = str(current_value)
                else:
                    default_value = ""

                new_value = forms.ask_for_string(
                    default=default_value,
                    prompt="Enter new value for '{}' ({}):".format(selected_param_name, param_type.replace("StorageType.", "")),
                    title="Override Parameter Value"
                )
                if new_value is not None and new_value.strip():
                    if set_parameter_value(element, selected_param_name, new_value.strip()):
                        forms.alert("Parameter '{}' updated successfully.".format(selected_param_name), title="Success")
                        # Refresh display instead of clear
                        output_window.print_md("---")
                        output_window.print_md("*Parameter updated - refreshing display...*")
                        output_window.print_md("---")
                        display_element_info(element)
                    else:
                        forms.alert("Failed to update parameter '{}'. Check console for details.".format(selected_param_name), title="Error")
            else:
                forms.alert("No parameter selected.", title="Cancelled")

        elif choice == "Change Instance Type" and isinstance(element, FamilyInstance):
            family_types = get_family_types(element)
            if not family_types:
                forms.alert("No other family types available to change to.", title="No Types")
                continue
            
            available_types = [f_type for f_type in family_types if f_type.Id != element.Symbol.Id]
            if not available_types:
                forms.alert("No other family types available to change to.", title="No Types")
                continue

            selected_type_symbol = forms.select_one_object(
                available_types,
                title="Select New Family Type",
                prompt="Choose a new type for the instance:",
                key_param=lambda x: x.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() if x.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM) else "No Name"
            )

            if selected_type_symbol:
                type_name = selected_type_symbol.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() if selected_type_symbol.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM) else "Unknown"
                if change_instance_type(element, selected_type_symbol):
                    forms.alert("Instance type changed to '{}' successfully.".format(type_name), title="Success")
                    output_window.clear()
                    display_element_info(element)
                else:
                    forms.alert("Failed to change instance type. Check console for details.", title="Error")
            else:
                forms.alert("No new type selected.", title="Cancelled")

        elif choice == "Done":
            break
        else:
            break

def main():
    """Main execution function for the Detail Item Inspector."""
    output_window.set_title("Detail Item Inspector")
    output_window.freeze()

    selected_elements = revit.get_selection().elements
    
    target_element = None

    if not selected_elements:
        forms.alert("Please select a Family Instance in the model or a Family Type in the Project Browser.", exitscript=True)
        return
    elif len(selected_elements) > 1:
        target_element = forms.select_one_object(
            selected_elements,
            title="Select Element to Inspect",
            prompt="Multiple elements selected. Please choose one:",
            key_param=lambda x: x.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString() if x.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME) else "Unknown Element"
        )
        if not target_element:
            forms.alert("No element selected. Exiting script.", exitscript=True)
            return
    else:
        target_element = selected_elements[0]

    if not isinstance(target_element, (FamilyInstance, FamilySymbol)):
        forms.alert(
            "Selected element is not a Family Instance or Family Type. "
            "Please select a valid element to inspect.",
            exitscript=True
        )
        return

    interact_with_element(target_element)
    output_window.unfreeze()

if __name__ == '__main__':
    main()