# -*- coding: utf-8 -*-
"""
Pre-run Matching Dimension - Pre-check Tool for Matching Dimension.

Overview:
    This script checks if beam and column types from linked EXR model exist in the host model.
    It serves as a pre-check tool before running the "Matching Dimension" script to ensure
    all required family types are available in the host document.

Process:
    1. Select a linked EXR model (from ETABS).
    2. Collect structural framing elements (beams) and structural columns from linked model.
    3. Extract unique family and type combinations used by these elements.
    4. Check which of these types exist in the host model.
    5. Report missing types with element counts and recommendations.

Requirements:
    - Revit environment with pyRevit extension.
    - A linked EXR model from ETABS containing beam and column elements.
    - Host model to check against.

Notes:
    - This is a pre-check tool for the "Matching Dimension" script.
    - Missing types will cause failures in the type transfer process.
    - Use this tool to identify what families need to be loaded before running Matching Dimension.
"""

__title__ = 'Pre-run\nMatching Dimension'
__author__ = 'Cline'
__doc__ = "Pre-check tool that verifies beam and column types from linked EXR model exist in host model " \
          "before running Matching Dimension tool."

import re
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    RevitLinkInstance,
    ElementId,
    FamilySymbol,
    Family,
    BuiltInParameter
)

from pyrevit import revit, forms, script

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
                'StructuralFraming': [
                    {'family_name': 'Concrete-Rectangular Beam', 'type_name': '300x600', 'element_count': 5},
                    ...
                ],
                'StructuralColumns': [
                    {'family_name': 'Concrete-Rectangular Column', 'type_name': '400x400', 'element_count': 3},
                    ...
                ]
            }
    """
    missing_types = {'StructuralFraming': [], 'StructuralColumns': []}

    for category in ['StructuralFraming', 'StructuralColumns']:
        for type_info in used_types[category]:
            family_name = type_info['family_name']
            type_name = type_info['type_name']

            # Check if family exists in host
            if family_name not in host_types[category]:
                missing_types[category].append(type_info)
                logger.debug("Family '{}' not found in host for category {}".format(family_name, category))
                continue

            # Check if type exists in the family
            if type_name not in host_types[category][family_name]:
                missing_types[category].append(type_info)
                logger.debug("Type '{}' not found in family '{}' for category {}".format(
                    type_name, family_name, category))

    return missing_types


def generate_report(missing_types, linked_model_name):
    """
    Generates a formatted report with tables showing missing types.

    Args:
        missing_types (dict): From find_missing_types()
        linked_model_name (str): Name of the linked model
    """
    output.print_md("# Type Availability Check Report")
    output.print_md("---")

    # Summary
    total_missing = sum(len(types) for types in missing_types.values())
    beams_missing = len(missing_types['StructuralFraming'])
    columns_missing = len(missing_types['StructuralColumns'])

    output.print_md("## Summary")
    output.print_md("- **Linked Model**: {}".format(linked_model_name))
    output.print_md("- **Categories Checked**: Structural Framing (Beams), Structural Columns")
    output.print_md("- **Total Missing Types**: {}".format(total_missing))
    output.print_md("  - Beams: {}".format(beams_missing))
    output.print_md("  - Columns: {}".format(columns_missing))
    output.print_md("---")

    # Missing Beam Types
    if missing_types['StructuralFraming']:
        output.print_md("## Missing Beam Types (Structural Framing)")
        beam_data = []
        for type_info in missing_types['StructuralFraming']:
            beam_data.append([
                type_info['family_name'],
                type_info['type_name'],
                str(type_info['element_count'])
            ])

        output.print_table(
            table_data=beam_data,
            title="Missing Beam Types",
            columns=["Family Name", "Type Name", "Element Count"]
        )
        output.print_md("---")

    # Missing Column Types
    if missing_types['StructuralColumns']:
        output.print_md("## Missing Column Types (Structural Columns)")
        column_data = []
        for type_info in missing_types['StructuralColumns']:
            column_data.append([
                type_info['family_name'],
                type_info['type_name'],
                str(type_info['element_count'])
            ])

        output.print_table(
            table_data=column_data,
            title="Missing Column Types",
            columns=["Family Name", "Type Name", "Element Count"]
        )
        output.print_md("---")

    # Recommendations
    output.print_md("## Recommendations")

    if total_missing > 0:
        output.print_md("⚠️ **Action Required**: Load the missing family types into the host model before running \"Matching Dimension\"")
        output.print_md("")
        output.print_md("📝 **Note**: Elements with missing types will fail during the type transfer process.")
        output.print_md("")
        output.print_md("**Steps to resolve:**")
        output.print_md("1. Load the required families into your host Revit model")
        output.print_md("2. Ensure the exact type names match those in the linked EXR model")
        output.print_md("3. Re-run this check to verify all types are available")
        output.print_md("4. Then proceed with the \"Matching Dimension\" tool")
    else:
        output.print_md("✅ **All types are available!** You can safely run the \"Matching Dimension\" tool.")


def main():
    """
    Main execution function that orchestrates the type availability check process.
    """
    output.print_md("# Pre-run Matching Dimension - Pre-check Tool")
    output.print_md("---")

    # Step 1: Select the linked EXR model
    output.print_md("## Step 1: Setup Linked EXR Model")
    link_doc, selected_link = select_linked_model()
    linked_model_name = selected_link.Name
    output.print_md("Linked EXR model: **{}**".format(linked_model_name))
    output.print_md("---")

    # Step 2: Collect structural elements from linked model
    output.print_md("## Step 2: Collecting Elements from Linked Model")
    linked_elements = collect_linked_elements(link_doc)

    total_elements = sum(len(elements) for elements in linked_elements.values())
    output.print_md("Total elements found: **{}**".format(total_elements))
    output.print_md("- Beams: **{}**".format(len(linked_elements['StructuralFraming'])))
    output.print_md("- Columns: **{}**".format(len(linked_elements['StructuralColumns'])))
    output.print_md("---")

    # Step 3: Extract unique types used by elements
    output.print_md("## Step 3: Extracting Used Types")
    used_types = extract_used_types(linked_elements)

    total_types = sum(len(types) for types in used_types.values())
    output.print_md("Unique types found: **{}**".format(total_types))
    output.print_md("- Beam types: **{}**".format(len(used_types['StructuralFraming'])))
    output.print_md("- Column types: **{}**".format(len(used_types['StructuralColumns'])))
    output.print_md("---")

    # Step 4: Collect available types from host model
    output.print_md("## Step 4: Checking Host Model Types")
    host_types = collect_host_types()

    host_total_types = sum(len(types) for family_types in host_types.values() for types in family_types.values())
    output.print_md("Available types in host: **{}**".format(host_total_types))
    output.print_md("- Beam families: **{}**".format(len(host_types['StructuralFraming'])))
    output.print_md("- Column families: **{}**".format(len(host_types['StructuralColumns'])))
    output.print_md("---")

    # Step 5: Find missing types
    output.print_md("## Step 5: Comparing Types")
    missing_types = find_missing_types(used_types, host_types)

    # Step 6: Generate report
    generate_report(missing_types, linked_model_name)

    # Final message
    total_missing = sum(len(types) for types in missing_types.values())
    if total_missing > 0:
        forms.alert(
            "Type availability check complete.\n\nFound {} missing types that need to be loaded before running Matching Dimension.".format(total_missing),
            title="Action Required"
        )
    else:
        forms.alert(
            "Type availability check complete.\n\nAll required types are available in the host model. You can safely run Matching Dimension.",
            title="Ready to Proceed"
        )


if __name__ == '__main__':
    main()