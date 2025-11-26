# -*- coding: utf-8 -*-
"""
Auto Load Missing Types - Automatic Family and Type Loading from Linked Model

Overview:
    This script automatically loads missing families and creates missing types from a linked EXR model
    to prepare the host model for the "Matching Dimension" tools. It addresses the gaps identified
    by the "Pre-run Matching Dimension" checker script.

Process:
    1. Select a linked EXR model (from ETABS).
    2. Identify missing families and types by comparing linked model against host model.
    3. Load missing families from the linked model to the host model.
    4. Create missing types by duplicating existing types and copying parameters from linked model.
    5. Report results with detailed success/failure information.

Requirements:
    - Revit environment with pyRevit extension.
    - A linked EXR model from ETABS containing the required families and types.
    - Host model that needs the missing families/types loaded.

Notes:
    - This script complements the "Pre-run Matching Dimension" checker.
    - Family loading requires the linked model to have loadable family files.
    - Type duplication works within existing families in the host model.
    - All operations are performed within transactions for safety.
"""

__title__ = 'Auto Load Missing Types'
__author__ = 'PrasKaa Team'
__doc__ = "Automatically loads missing families and creates missing types from linked EXR model " \
          "to prepare for Matching Dimension tools."

import re
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    RevitLinkInstance,
    ElementId,
    FamilySymbol,
    Family,
    BuiltInParameter,
    Transaction,
    TransactionStatus,
    FamilyManager,
    FamilyType,
    Parameter,
    StorageType,
    UnitUtils,
    UnitTypeId
)

from pyrevit import revit, forms, script

# Configuration
DEBUG_MODE = False  # Set to True to enable detailed parameter copy debugging

# Setup
doc = revit.doc
uidoc = revit.uidoc
logger = script.get_logger()
output = script.get_output()


def select_linked_model():
    """
    Prompts the user to select a linked EXR model from available Revit links.

    Returns:
        tuple: (link_doc, selected_link)
            - link_doc: The Document object of the selected linked model.
            - selected_link: The RevitLinkInstance object of the selected link.

    Raises:
        SystemExit: If no links are found or no link is selected.
    """
    link_instances = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()
    if not link_instances:
        forms.alert("No Revit links found in the current project.", exitscript=True)

    # Create a dictionary of link instances for selection
    link_dict = {link.Name: link for link in link_instances}

    selected_link_name = forms.SelectFromList.show(
        sorted(link_dict.keys()),
        title='Select Source Linked EXR Model (from ETABS)',
        button_name='Select Link',
        multiselect=False
    )

    selected_link = link_dict.get(selected_link_name) if selected_link_name else None

    if not selected_link:
        forms.alert("No link selected. Script will exit.", exitscript=True)

    link_doc = selected_link.GetLinkDocument()
    if not link_doc:
        forms.alert("Could not access the document of the selected link. Ensure it is loaded.", exitscript=True)

    return link_doc, selected_link


def collect_linked_elements(link_doc):
    """
    Collects structural framing elements (beams) and structural columns from the linked EXR model.

    Args:
        link_doc (Document): The document object of the linked Revit model.

    Returns:
        dict: Dictionary with categories as keys and element lists as values.
            {
                'StructuralFraming': [element1, element2, ...],
                'StructuralColumns': [element1, element2, ...]
            }
    """
    categories = {
        'StructuralFraming': BuiltInCategory.OST_StructuralFraming,
        'StructuralColumns': BuiltInCategory.OST_StructuralColumns
    }

    elements = {}

    for category_name, category in categories.items():
        category_elements = FilteredElementCollector(link_doc)\
            .OfCategory(category)\
            .WhereElementIsNotElementType()\
            .ToElements()

        elements[category_name] = category_elements
        logger.debug("Found {} {} elements in linked model".format(len(category_elements), category_name))

    return elements


def extract_used_types(elements_dict):
    """
    Extracts unique family and type combinations from element instances.

    Args:
        elements_dict (dict): Dictionary from collect_linked_elements()

    Returns:
        dict: Dictionary with categories as keys and type info as values.
            {
                'StructuralFraming': [
                    {'family_name': 'Concrete-Rectangular Beam', 'type_name': '300x600', 'element_ids': [id1, id2]},
                    ...
                ],
                'StructuralColumns': [
                    {'family_name': 'Concrete-Rectangular Column', 'type_name': '400x400', 'element_ids': [id1, id2]},
                    ...
                ]
            }
    """
    used_types = {'StructuralFraming': [], 'StructuralColumns': []}

    for category_name, elements in elements_dict.items():
        type_tracker = {}  # Track unique types: (family_name, type_name) -> element_ids

        for element in elements:
            try:
                # Get the element's type
                element_type = element.Document.GetElement(element.GetTypeId())
                if not element_type:
                    continue

                # Get family name
                family_name = None
                if hasattr(element_type, 'Family') and element_type.Family:
                    family_name = element_type.Family.Name

                # Get type name using multiple fallback methods
                type_name = None

                # Method 1: Direct Name property
                if hasattr(element_type, 'Name'):
                    type_name = element_type.Name

                # Method 2: SYMBOL_NAME_PARAM for FamilySymbol
                if not type_name:
                    name_param = element_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                    if name_param and name_param.HasValue:
                        type_name = name_param.AsString()

                # Method 3: ALL_MODEL_TYPE_NAME
                if not type_name:
                    name_param = element_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
                    if name_param and name_param.HasValue:
                        type_name = name_param.AsString()

                if family_name and type_name:
                    key = (family_name, type_name)
                    if key not in type_tracker:
                        type_tracker[key] = []
                    type_tracker[key].append(element.Id)

            except Exception as e:
                logger.debug("Failed to extract type info from element {}. Error: {}".format(element.Id, e))
                continue

        # Convert tracker to list format
        for (family_name, type_name), element_ids in type_tracker.items():
            used_types[category_name].append({
                'family_name': family_name,
                'type_name': type_name,
                'element_count': len(element_ids),
                'element_ids': element_ids
            })

        logger.debug("Extracted {} unique types for {}".format(len(used_types[category_name]), category_name))

    return used_types


def collect_host_types():
    """
    Collects all available family and type combinations from the host model.

    Returns:
        dict: Dictionary with categories as keys and available types as values.
            {
                'StructuralFraming': {
                    'Concrete-Rectangular Beam': ['300x600', '400x800', ...],
                    ...
                },
                'StructuralColumns': {
                    'Concrete-Rectangular Column': ['400x400', '500x500', ...],
                    ...
                }
            }
    """
    categories = {
        'StructuralFraming': BuiltInCategory.OST_StructuralFraming,
        'StructuralColumns': BuiltInCategory.OST_StructuralColumns
    }

    host_types = {'StructuralFraming': {}, 'StructuralColumns': {}}

    # Get all FamilySymbol elements (which represent types)
    all_symbols = FilteredElementCollector(doc).OfClass(FamilySymbol).WhereElementIsElementType().ToElements()

    for symbol in all_symbols:
        try:
            # Get family info
            if not (symbol and hasattr(symbol, 'Family') and symbol.Family):
                continue

            family = symbol.Family
            if not hasattr(family, 'Name'):
                continue

            family_name = family.Name

            # Get symbol name using multiple methods
            symbol_name = None

            # Method 1: Direct Name property
            if hasattr(symbol, 'Name'):
                symbol_name = symbol.Name

            # Method 2: SYMBOL_NAME_PARAM
            if not symbol_name:
                name_param = symbol.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                if name_param and name_param.HasValue:
                    symbol_name = name_param.AsString()

            # Method 3: ALL_MODEL_TYPE_NAME
            if not symbol_name:
                name_param = symbol.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
                if name_param and name_param.HasValue:
                    symbol_name = name_param.AsString()

            if symbol_name:
                # Determine category based on family name patterns
                category = None
                if 'beam' in family_name.lower() or 'balok' in family_name.lower():
                    category = 'StructuralFraming'
                elif 'column' in family_name.lower() or 'kolom' in family_name.lower():
                    category = 'StructuralColumns'

                if category:
                    if family_name not in host_types[category]:
                        host_types[category][family_name] = []
                    if symbol_name not in host_types[category][family_name]:
                        host_types[category][family_name].append(symbol_name)

        except Exception as e:
            logger.debug("Failed to process symbol {}. Error: {}".format(symbol.Id, e))
            continue

    logger.debug("Collected host types: {}".format(host_types))
    return host_types


def find_missing_types(used_types, host_types):
    """
    Compares used types from linked model against available types in host model.

    Args:
        used_types (dict): From extract_used_types()
        host_types (dict): From collect_host_types()

    Returns:
        dict: Missing types with element counts.
            {
                'missing_families': [
                    {'family_name': 'Concrete-Rectangular Beam', 'category': 'StructuralFraming'},
                    ...
                ],
                'missing_types': [
                    {'family_name': 'Concrete-Rectangular Beam', 'type_name': '300x600', 'category': 'StructuralFraming'},
                    ...
                ]
            }
    """
    missing_families = []
    missing_types = []

    for category in ['StructuralFraming', 'StructuralColumns']:
        for type_info in used_types[category]:
            family_name = type_info['family_name']
            type_name = type_info['type_name']

            # Check if family exists in host
            if family_name not in host_types[category]:
                # Family is missing entirely
                if not any(f['family_name'] == family_name and f['category'] == category for f in missing_families):
                    missing_families.append({
                        'family_name': family_name,
                        'category': category
                    })
                logger.debug("Family '{}' not found in host for category {}".format(family_name, category))
            else:
                # Family exists, check if type exists
                if type_name not in host_types[category][family_name]:
                    missing_types.append({
                        'family_name': family_name,
                        'type_name': type_name,
                        'category': category,
                        'element_count': type_info['element_count']
                    })
                    logger.debug("Type '{}' not found in family '{}' for category {}".format(
                        type_name, family_name, category))

    return {
        'missing_families': missing_families,
        'missing_types': missing_types
    }


def load_family_from_linked_model(link_doc, family_name, category):
    """
    Loads a family from the linked model into the host model.

    Args:
        link_doc (Document): The linked document
        family_name (str): Name of the family to load
        category (str): Category ('StructuralFraming' or 'StructuralColumns')

    Returns:
        dict: Result with 'success', 'message', and optionally 'loaded_family'
    """
    try:
        # Find the family in the linked document
        linked_families = FilteredElementCollector(link_doc).OfClass(Family).ToElements()

        target_family = None
        for family in linked_families:
            if family.Name == family_name:
                target_family = family
                break

        if not target_family:
            return {
                'success': False,
                'message': "Family '{}' not found in linked model".format(family_name)
            }

        # Check if family is already loaded in host
        host_families = FilteredElementCollector(doc).OfClass(Family).ToElements()
        for host_family in host_families:
            if host_family.Name == family_name:
                return {
                    'success': False,
                    'message': "Family '{}' already exists in host model".format(family_name)
                }

        # Load the family
        with Transaction(doc, "Load Family: {}".format(family_name)) as t:
            t.Start()

            # Load family - this will load all types within the family
            success = doc.LoadFamily(target_family)

            if success:
                t.Commit()
                return {
                    'success': True,
                    'message': "Successfully loaded family '{}' with all types".format(family_name)
                }
            else:
                t.RollBack()
                return {
                    'success': False,
                    'message': "Failed to load family '{}'".format(family_name)
                }

    except Exception as e:
        logger.error("Error loading family '{}': {}".format(family_name, e))
        return {
            'success': False,
            'message': "Error loading family '{}': {}".format(family_name, str(e))
        }


def duplicate_type_and_copy_parameters(family_name, type_name, link_doc, category):
    """
    Creates a new type by duplicating an existing type in the host family and copying parameters
    from the corresponding type in the linked model.

    Args:
        family_name (str): Name of the family in host model
        type_name (str): Name of the type to create
        link_doc (Document): The linked document
        category (str): Category ('StructuralFraming' or 'StructuralColumns')

    Returns:
        dict: Result with 'success' and 'message'
    """
    try:
        # Find the family in host document
        host_families = FilteredElementCollector(doc).OfClass(Family).ToElements()
        target_family = None
        for family in host_families:
            if family.Name == family_name:
                target_family = family
                break

        if not target_family:
            return {
                'success': False,
                'message': "Family '{}' not found in host model".format(family_name)
            }

        # Get existing types in the family
        family_symbols = []
        all_symbols = FilteredElementCollector(doc).OfClass(FamilySymbol).WhereElementIsElementType().ToElements()
        for symbol in all_symbols:
            if (hasattr(symbol, 'Family') and symbol.Family and
                symbol.Family.Name == family_name):
                family_symbols.append(symbol)

        if not family_symbols:
            return {
                'success': False,
                'message': "No existing types found in family '{}' to use as template".format(family_name)
            }

        # Check if type already exists
        for symbol in family_symbols:
            symbol_name = None
            if hasattr(symbol, 'Name'):
                symbol_name = symbol.Name
            if not symbol_name:
                name_param = symbol.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                if name_param and name_param.HasValue:
                    symbol_name = name_param.AsString()
            
            if symbol_name == type_name:
                return {
                    'success': False,
                    'message': "Type '{}' already exists in family '{}'".format(type_name, family_name)
                }

        # Use the first existing type as template
        template_symbol = family_symbols[0]

        # Find the source type in linked model
        source_symbol = None
        linked_symbols = FilteredElementCollector(link_doc).OfClass(FamilySymbol).WhereElementIsElementType().ToElements()
        for symbol in linked_symbols:
            if (hasattr(symbol, 'Family') and symbol.Family and
                symbol.Family.Name == family_name):

                # Check type name
                symbol_name = None
                if hasattr(symbol, 'Name'):
                    symbol_name = symbol.Name
                if not symbol_name:
                    name_param = symbol.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                    if name_param and name_param.HasValue:
                        symbol_name = name_param.AsString()

                if symbol_name == type_name:
                    source_symbol = symbol
                    break

        if not source_symbol:
            return {
                'success': False,
                'message': "Source type '{}' not found in linked model family '{}'".format(type_name, family_name)
            }

        # MAIN FIX: Duplicate the template type and rename it
        with Transaction(doc, "Create Type: {}".format(type_name)) as t:
            t.Start()
            
            try:
                # Duplicate the template symbol
                new_symbol = template_symbol.Duplicate(type_name)
                
                if not new_symbol:
                    t.RollBack()
                    return {
                        'success': False,
                        'message': "Failed to duplicate type in family '{}'".format(family_name)
                    }
                
                # Copy parameters from source to new symbol
                param_results = copy_parameters_between_types(source_symbol, new_symbol)

                t.Commit()

                if param_results['success']:
                    return {
                        'success': True,
                        'message': "Successfully created type '{}' and copied {} parameters".format(
                            type_name, param_results['success_count']),
                        'param_details': param_results
                    }
                else:
                    return {
                        'success': True,
                        'message': "Created type '{}' but parameter copying failed ({} successful, {} failed)".format(
                            type_name, param_results['success_count'], param_results['fail_count']),
                        'param_details': param_results
                    }
                    
            except Exception as inner_e:
                t.RollBack()
                return {
                    'success': False,
                    'message': "Error during duplication: {}".format(str(inner_e))
                }

    except Exception as e:
        logger.error("Error in duplicate_type_and_copy_parameters: {}".format(e))
        return {
            'success': False,
            'message': "Unexpected error: {}".format(str(e))
        }

def format_parameter_value(value, storage_type, param_name=""):
    """
    Format parameter value for display, converting units where appropriate.

    Args:
        value: The parameter value (string representation of the actual value)
        storage_type: The StorageType of the parameter
        param_name: Parameter name for context (optional)

    Returns:
        str: Formatted value string
    """
    try:
        if storage_type == StorageType.Double:
            # Try to convert feet to mm for length parameters
            try:
                numeric_value = float(value)
                # Convert from internal units (feet) to mm
                mm_value = UnitUtils.ConvertFromInternalUnits(numeric_value, UnitTypeId.Millimeters)
                return "{:.0f}mm".format(mm_value)
            except (ValueError, Exception):
                # If conversion fails, return original value
                return value
        elif storage_type == StorageType.Integer:
            try:
                return str(int(float(value)))
            except (ValueError, Exception):
                return value
        else:
            # String, ElementId, etc. - return as-is
            return value
    except Exception:
        # Fallback to original value if anything goes wrong
        return value


def copy_parameters_between_types(source_symbol, target_symbol):
    """
    Copies parameter values from source symbol to target symbol with detailed logging.

    Args:
        source_symbol (FamilySymbol): Source type to copy from
        target_symbol (FamilySymbol): Target type to copy to

    Returns:
        dict: Detailed results with 'success', 'copied_params', 'failed_params', 'debug_output'
    """
    debug_output = ""

    try:
        debug_output += "\n=== DEBUG PARAMETER COPY ===\n"
        debug_output += "Source symbol: {}\n".format(source_symbol.Name if hasattr(source_symbol, 'Name') else 'Unknown')
        debug_output += "Target symbol: {}\n".format(target_symbol.Name if hasattr(target_symbol, 'Name') else 'Unknown')

        # Get all parameters from source
        source_params = source_symbol.Parameters
        debug_output += "Source parameters count: {}\n".format(source_params.Size)

        # Get all parameters from target
        target_params = target_symbol.Parameters
        debug_output += "Target parameters count: {}\n".format(target_params.Size)

        # Create lookup dict for target parameters
        target_param_dict = {}
        for target_param in target_params:
            param_name = target_param.Definition.Name
            target_param_dict[param_name] = target_param
            debug_output += "Target param: {} (Type: {}, ReadOnly: {})\n".format(
                param_name, target_param.StorageType, target_param.IsReadOnly)

        success_count = 0
        fail_count = 0
        copied_params = []
        failed_params = []

        for source_param in source_params:
            try:
                param_name = source_param.Definition.Name
                debug_output += "\nProcessing source param: {} (Type: {}, ReadOnly: {}, HasValue: {})\n".format(
                    param_name, source_param.StorageType, source_param.IsReadOnly, source_param.HasValue)

                # Skip read-only parameters
                if source_param.IsReadOnly:
                    debug_output += "  Skipping read-only parameter\n"
                    continue

                # Skip if no value
                if not source_param.HasValue:
                    debug_output += "  Skipping parameter with no value\n"
                    continue

                # Find corresponding parameter in target
                target_param = target_param_dict.get(param_name)

                if not target_param:
                    debug_output += "  FAILED: Parameter '{}' not found in target\n".format(param_name)
                    failed_params.append({
                        'name': param_name,
                        'reason': 'Parameter not found in target',
                        'source_value': source_param.AsValueString() if hasattr(source_param, 'AsValueString') else 'Unknown'
                    })
                    fail_count += 1
                    continue

                if target_param.IsReadOnly:
                    debug_output += "  FAILED: Target parameter '{}' is read-only\n".format(param_name)
                    failed_params.append({
                        'name': param_name,
                        'reason': 'Target parameter is read-only',
                        'source_value': source_param.AsValueString() if hasattr(source_param, 'AsValueString') else 'Unknown'
                    })
                    fail_count += 1
                    continue

                # Get source value
                source_value = None
                if source_param.StorageType == StorageType.Double:
                    source_value = source_param.AsDouble()
                    debug_output += "  Source value (Double): {}\n".format(source_value)
                elif source_param.StorageType == StorageType.Integer:
                    source_value = source_param.AsInteger()
                    debug_output += "  Source value (Integer): {}\n".format(source_value)
                elif source_param.StorageType == StorageType.String:
                    source_value = source_param.AsString()
                    debug_output += "  Source value (String): {}\n".format(source_value)
                elif source_param.StorageType == StorageType.ElementId:
                    source_value = source_param.AsElementId()
                    debug_output += "  Source value (ElementId): {}\n".format(source_value)

                # Set value on target
                debug_output += "  Attempting to set value on target...\n"
                if source_param.StorageType == StorageType.Double:
                    target_param.Set(source_value)
                    debug_output += "  SUCCESS: Set Double value\n"
                elif source_param.StorageType == StorageType.Integer:
                    target_param.Set(source_value)
                    debug_output += "  SUCCESS: Set Integer value\n"
                elif source_param.StorageType == StorageType.String:
                    target_param.Set(source_value)
                    debug_output += "  SUCCESS: Set String value\n"
                elif source_param.StorageType == StorageType.ElementId:
                    target_param.Set(source_value)
                    debug_output += "  SUCCESS: Set ElementId value\n"

                # Verify the value was set
                if target_param.HasValue:
                    if source_param.StorageType == StorageType.Double:
                        set_value = target_param.AsDouble()
                        debug_output += "  Verification: Target now has value {}\n".format(set_value)
                    elif source_param.StorageType == StorageType.Integer:
                        set_value = target_param.AsInteger()
                        debug_output += "  Verification: Target now has value {}\n".format(set_value)
                    elif source_param.StorageType == StorageType.String:
                        set_value = target_param.AsString()
                        debug_output += "  Verification: Target now has value {}\n".format(set_value)

                copied_params.append({
                    'name': param_name,
                    'source_value': str(source_value),
                    'storage_type': source_param.StorageType
                })
                success_count += 1

            except Exception as e:
                param_name = source_param.Definition.Name if source_param else 'Unknown'
                debug_output += "  ERROR: Failed to copy parameter '{}': {}\n".format(param_name, e)
                failed_params.append({
                    'name': param_name,
                    'reason': 'Exception: {}'.format(str(e)),
                    'source_value': 'Unknown'
                })
                fail_count += 1
                continue

        debug_output += "\n=== PARAMETER COPY SUMMARY ===\n"
        debug_output += "Successful: {}, Failed: {}\n".format(success_count, fail_count)

        return {
            'success': success_count > 0,
            'success_count': success_count,
            'fail_count': fail_count,
            'copied_params': copied_params,
            'failed_params': failed_params,
            'debug_output': debug_output
        }

    except Exception as e:
        debug_output += "CRITICAL ERROR in copy_parameters_between_types: {}\n".format(e)
        return {
            'success': False,
            'success_count': 0,
            'fail_count': 0,
            'copied_params': [],
            'failed_params': [{'name': 'Unknown', 'reason': 'Critical error: {}'.format(str(e)), 'source_value': 'Unknown'}],
            'debug_output': debug_output
        }




def main():
    """
    Main execution function that orchestrates the automatic type loading process.
    """
    # Collect ALL output in a single string to prevent multiple console windows
    full_report = ""

    full_report += "# Auto Load Missing Types - Automatic Type Loading\n"
    full_report += "---\n"

    # Step 1: Select the linked EXR model
    full_report += "## Step 1: Setup Linked EXR Model\n"
    link_doc, selected_link = select_linked_model()
    linked_model_name = selected_link.Name
    full_report += "Linked EXR model: **{}**\n".format(linked_model_name)
    full_report += "---\n"

    # Step 2: Collect elements and extract types from linked model
    full_report += "## Step 2: Analyzing Linked Model\n"
    linked_elements = collect_linked_elements(link_doc)
    used_types = extract_used_types(linked_elements)

    total_linked_types = sum(len(types) for types in used_types.values())
    full_report += "Found **{}** unique types in linked model\n".format(total_linked_types)
    full_report += "---\n"

    # Step 3: Check host model for available types
    full_report += "## Step 3: Checking Host Model\n"
    host_types = collect_host_types()

    host_total_types = sum(len(types) for family_types in host_types.values() for types in family_types.values())
    full_report += "Found **{}** types in host model\n".format(host_total_types)
    full_report += "---\n"

    # Step 4: Find missing families and types
    full_report += "## Step 4: Identifying Missing Items\n"
    missing_data = find_missing_types(used_types, host_types)

    total_missing = len(missing_data['missing_families']) + len(missing_data['missing_types'])
    full_report += "Found **{}** missing items:\n".format(total_missing)
    full_report += "- **{}** families to load\n".format(len(missing_data['missing_families']))
    full_report += "- **{}** types to create\n".format(len(missing_data['missing_types']))
    full_report += "---\n"

    if total_missing == 0:
        forms.alert("No missing families or types found. All required types are already available in the host model.",
                   title="Nothing to Load")
        return

    # Step 5: Load missing families
    full_report += "## Step 5: Loading Missing Families\n"
    family_load_results = []

    for family_info in missing_data['missing_families']:
        result = load_family_from_linked_model(link_doc, family_info['family_name'], family_info['category'])
        family_load_results.append({
            'family_name': family_info['family_name'],
            'category': family_info['category'],
            'success': result['success'],
            'message': result['message']
        })

    full_report += "Processed {} families\n".format(len(family_load_results))
    full_report += "---\n"

    # Step 6: Create missing types
    full_report += "## Step 6: Creating Missing Types\n"
    type_create_results = []

    for type_info in missing_data['missing_types']:
        result = duplicate_type_and_copy_parameters(
            type_info['family_name'], type_info['type_name'], link_doc, type_info['category'])
        type_create_results.append({
            'family_name': type_info['family_name'],
            'type_name': type_info['type_name'],
            'category': type_info['category'],
            'success': result['success'],
            'message': result['message'],
            'param_details': result.get('param_details', {})
        })

    full_report += "Processed {} types\n".format(len(type_create_results))
    full_report += "---\n"

    # Generate final report content
    results = {
        'family_load_results': family_load_results,
        'type_create_results': type_create_results
    }

    # Add basic report content to full_report
    full_report += "# Auto Load Missing Types Report\n"
    full_report += "---\n"

    # Summary
    total_missing_families = len(missing_data['missing_families'])
    total_missing_types = len(missing_data['missing_types'])
    successful_family_loads = sum(1 for r in results['family_load_results'] if r['success'])
    successful_type_creates = sum(1 for r in results['type_create_results'] if r['success'])

    full_report += "## Summary\n"
    full_report += "- **Linked Model**: {}\n".format(linked_model_name)
    full_report += "- **Missing Families**: {}\n".format(total_missing_families)
    full_report += "- **Missing Types**: {}\n".format(total_missing_types)
    full_report += "- **Families Loaded**: {} successful\n".format(successful_family_loads)
    full_report += "- **Types Created**: {} successful\n".format(successful_type_creates)
    full_report += "---\n"

    # Print main content first
    output.print_md(full_report)

    # Now print detailed tables (these will appear in the same console window)
    if results['family_load_results']:
        output.print_md("## Family Loading Results")
        family_data = []
        for result in results['family_load_results']:
            status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
            family_data.append([
                result['family_name'],
                result['category'],
                status,
                result['message']
            ])

        output.print_table(
            table_data=family_data,
            title="Family Loading Results",
            columns=["Family Name", "Category", "Status", "Message"]
        )
        output.print_md("---")

    if results['type_create_results']:
        output.print_md("## Type Creation Results")
        type_data = []
        for result in results['type_create_results']:
            status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
            type_data.append([
                result['family_name'],
                result['type_name'],
                result['category'],
                status,
                result['message']
            ])

        output.print_table(
            table_data=type_data,
            title="Type Creation Results",
            columns=["Family Name", "Type Name", "Category", "Status", "Message"]
        )
        output.print_md("---")

    # Parameter Details Section
    if successful_type_creates > 0:
        output.print_md("## Parameter Copy Details")

        for result in type_create_results:
            if result['success'] and 'param_details' in result:
                param_details = result['param_details']
                output.print_md("**Type: {} ({})**".format(result['type_name'], result['family_name']))

                if param_details.get('copied_params'):
                    output.print_md("**Successfully Copied ({}):**".format(len(param_details['copied_params'])))
                    for param in param_details['copied_params']:
                        formatted_value = format_parameter_value(param['source_value'], param['storage_type'], param['name'])
                        output.print_md("- {}: {} ✓".format(param['name'], formatted_value))

                if param_details.get('failed_params'):
                    output.print_md("**Failed to Copy ({}):**".format(len(param_details['failed_params'])))
                    for param in param_details['failed_params']:
                        output.print_md("- {}: {} ✗ ({})".format(param['name'], param['source_value'], param['reason']))

                output.print_md("")

    # Debug Information (only if DEBUG_MODE is enabled)
    if DEBUG_MODE and successful_type_creates > 0:
        output.print_md("## Debug Information")
        output.print_md("**Note:** Debug mode is enabled. Detailed parameter copy logs are shown below.")

        all_debug_output = ""
        for result in type_create_results:
            if result['success'] and 'param_details' in result and 'debug_output' in result['param_details']:
                all_debug_output += result['param_details']['debug_output']

        if all_debug_output:
            output.print_md("```\n{}\n```".format(all_debug_output))

    # Next steps
    output.print_md("## Next Steps")

    if successful_family_loads > 0:
        output.print_md("✅ **Families Successfully Loaded**: {} families were automatically loaded from the linked model.".format(successful_family_loads))

    if successful_type_creates > 0:
        output.print_md("✅ **Types Successfully Created**: {} types were automatically created and parameters copied.".format(successful_type_creates))

    output.print_md("**To verify completion:**")
    output.print_md("1. Run 'Pre-run Matching Dimension' again to check remaining missing types")
    output.print_md("2. If all types are now available, proceed with 'Matching Dimension' tools")
    output.print_md("3. All required families and types should now be available in your host model")

    # Final alert
    successful_ops = sum(r['success'] for r in family_load_results + type_create_results)
    total_ops = len(family_load_results) + len(type_create_results)

    if successful_ops == total_ops:
        forms.alert(
            "Auto loading completed successfully!\n\nAll missing families and types have been loaded/created.",
            title="Success"
        )
    else:
        forms.alert(
            "Auto loading completed with some issues.\n\nSuccessful: {}/{}\n\nCheck the report for details.".format(successful_ops, total_ops),
            title="Partial Success"
        )


if __name__ == '__main__':
    main()