# -*- coding: utf-8 -*-
"""
Add 'Reference ETABS GUID' Parameter to Structural Framing Category.

This script creates a new shared parameter called 'Reference ETABS GUID'
and binds it to the Structural Framing category. This parameter is used
to store the ETABS GUID reference for beam matching operations.
"""

__title__ = 'Add Reference\nETABS GUID'
__author__ = 'PrasKaa+KiloCode'
__doc__ = "Creates 'Reference ETABS GUID' shared parameter for Structural Framing category."

import os
from Autodesk.Revit.DB import (
    Transaction,
    BuiltInCategory,
    ParameterType,
    StorageType,
    Category,
    CategorySet,
    InstanceBinding,
    SharedParameterElement,
    ExternalDefinitionCreationOptions,
    DefinitionFile,
    DefinitionGroups,
    Definitions,
    ElementId,
    FilteredElementCollector,
    BuiltInParameterGroup
)

from pyrevit import revit, forms, script

# Setup
doc = revit.doc
app = doc.Application
logger = script.get_logger()
output = script.get_output()


def create_shared_parameter_file():
    """
    Create a temporary shared parameter file if one doesn't exist.

    Returns:
        str: Path to the shared parameter file
    """
    # Try to get existing shared parameter file
    current_file = app.SharedParametersFilename
    if current_file and os.path.exists(current_file):
        logger.info("Using existing shared parameter file: {}".format(current_file))
        return current_file

    # Create temporary shared parameter file
    temp_dir = os.path.expanduser("~/AppData/Local/Temp")
    temp_file = os.path.join(temp_dir, "PrasKaaPyKit_SharedParameters.txt")

    try:
        # Create empty shared parameter file
        with open(temp_file, 'w') as f:
            f.write("# Temporary shared parameter file for PrasKaaPyKit\n")
            f.write("# This file was auto-generated\n\n")

        # Set it as the current shared parameter file
        app.SharedParametersFilename = temp_file
        logger.info("Created temporary shared parameter file: {}".format(temp_file))
        return temp_file

    except Exception as e:
        logger.error("Failed to create shared parameter file: {}".format(e))
        return None


def add_shared_parameter_to_file(param_name, param_type=ParameterType.Text):
    """
    Add a parameter definition to the shared parameter file.

    Args:
        param_name (str): Name of the parameter
        param_type: ParameterType enum value

    Returns:
        bool: Success status
    """
    try:
        # Get the shared parameter file
        definition_file = app.OpenSharedParameterFile()
        if not definition_file:
            logger.error("Could not open shared parameter file")
            return False

        # Get or create the group
        group_name = "PrasKaaPyKit Parameters"
        groups = definition_file.Groups
        group = None

        # Look for existing group
        for g in groups:
            if g.Name == group_name:
                group = g
                break

        # Create group if it doesn't exist
        if not group:
            group = groups.Create(group_name)
            logger.info("Created parameter group: {}".format(group_name))

        # Check if parameter already exists
        definitions = group.Definitions
        for def_item in definitions:
            if def_item.Name == param_name:
                logger.info("Parameter '{}' already exists in shared parameter file".format(param_name))
                return True

        # Create new parameter definition
        options = ExternalDefinitionCreationOptions(param_name, param_type)
        options.UserModifiable = True
        options.Description = "Reference ETABS GUID for beam matching operations"

        definition = group.Definitions.Create(options)
        logger.info("Created parameter definition: '{}'".format(param_name))

        return True

    except Exception as e:
        logger.error("Failed to add parameter to shared parameter file: {}".format(e))
        return False


def bind_parameter_to_category(param_name, category_id):
    """
    Bind the shared parameter to a specific category.

    Args:
        param_name (str): Name of the parameter
        category_id: BuiltInCategory enum value

    Returns:
        bool: Success status
    """
    try:
        # Find the parameter element
        param_elem = None
        collector = FilteredElementCollector(doc).OfClass(SharedParameterElement)
        for elem in collector:
            if elem.Name == param_name:
                param_elem = elem
                break

        if not param_elem:
            logger.error("Could not find shared parameter element: {}".format(param_name))
            return False

        # Create category set
        category_set = CategorySet()
        category = Category.GetCategory(doc, category_id)
        if category:
            category_set.Insert(category)
        else:
            logger.error("Could not get category: {}".format(category_id))
            return False

        # Create instance binding
        binding = InstanceBinding(category_set)

        # Bind the parameter
        success = doc.ParameterBindings.Insert(param_elem.GetDefinition(), binding, BuiltInParameterGroup.PG_DATA)

        if success:
            logger.info("Successfully bound parameter '{}' to category".format(param_name))
            return True
        else:
            logger.error("Failed to bind parameter '{}' to category".format(param_name))
            return False

    except Exception as e:
        logger.error("Failed to bind parameter to category: {}".format(e))
        return False


def main():
    """Main execution logic."""
    param_name = "Reference ETABS GUID"
    target_category = BuiltInCategory.OST_StructuralFraming

    logger.info("Starting parameter creation process for: {}".format(param_name))

    # Check if parameter already exists
    existing_param = None
    collector = FilteredElementCollector(doc).OfClass(SharedParameterElement)
    for elem in collector:
        if elem.Name == param_name:
            existing_param = elem
            break

    if existing_param:
        forms.alert("Parameter '{}' already exists in the project.".format(param_name), title="Parameter Exists")
        return

    # Create shared parameter file if needed
    shared_param_file = create_shared_parameter_file()
    if not shared_param_file:
        forms.alert("Failed to create or access shared parameter file.", exitscript=True)

    # Add parameter to shared parameter file
    if not add_shared_parameter_to_file(param_name, ParameterType.Text):
        forms.alert("Failed to add parameter to shared parameter file.", exitscript=True)

    # Bind parameter to category
    with Transaction(doc, "Add Reference ETABS GUID Parameter") as t:
        t.Start()

        try:
            if bind_parameter_to_category(param_name, target_category):
                t.Commit()
                forms.alert(
                    "Successfully created and bound parameter '{}' to Structural Framing category.".format(param_name),
                    title="Parameter Created"
                )
                logger.info("Parameter creation completed successfully")
            else:
                t.RollBack()
                forms.alert("Failed to bind parameter to category.", exitscript=True)

        except Exception as e:
            t.RollBack()
            logger.error("Transaction failed: {}".format(e))
            forms.alert("Failed to create parameter: {}".format(str(e)), exitscript=True)


if __name__ == '__main__':
    main()