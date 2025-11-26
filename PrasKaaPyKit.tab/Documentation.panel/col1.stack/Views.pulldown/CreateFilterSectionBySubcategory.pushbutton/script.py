# -*- coding: utf-8 -*-
"""
This script creates a Revit parameter filter based on a user-provided Sub Category parameter (shared/project parameter).
It mimics the workflow of the provided Dynamo graph, adapted for pyRevit.
"""
__title__ = 'Filter Section'
__author__ = 'Cline + PrasKaa'

from pyrevit import revit, DB, forms, script
from System.Collections.Generic import List
from Autodesk.Revit.UI import TaskDialog


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

doc = revit.doc
uidoc = revit.uidoc

# 1. Prompt user for Sub Category name
sub_category_input = forms.ask_for_string(
    default="xx.x_SubCategoryName",
    prompt="Enter Sub Category Name (Format:xx.x_TypeofSubCategory)",
    title="Create Filter"
)

if not sub_category_input:
    forms.toast("No sub-category name provided. Aborting.",
                title="Filter Creation Cancelled",
                appid="FilterSection")
    script.exit()

# 2. Process the input string
split_string = sub_category_input.split('_')
if len(split_string) > 1:
    filter_name_part = '_'.join(split_string[1:]).replace('_', ' ').title()
else:
    filter_name_part = sub_category_input.title()

# 3. Define the filter name
filter_name = "Selection - Potongan " + filter_name_part

# 4. Create the filter rule (pakai Shared Parameter "Sub Category")
try:
    target_param_name = "Sub Category"

    # Cari ParameterElement menggunakan utility function
    pe = find_parameter_element(doc, target_param_name)

    if pe is None:
        raise Exception("Project/Shared Parameter '{}' tidak ditemukan di dokumen.".format(target_param_name))

    # Gunakan ParameterElement.Id untuk provider
    param_id = pe.Id

    # Deteksi tipe parameter menggunakan utility function
    type_info = get_parameter_type_info(pe)
    
    # Gunakan type_info dari utility function untuk menentukan tipe parameter
    if type_info['is_text']:
        # Parameter Text - menggunakan Does Not Equal rule
        converted_value = sub_category_input
        filter_rule = DB.ParameterFilterRuleFactory.CreateNotEqualsRule(
            param_id,
            converted_value
        )
    elif type_info['is_number']:
        # Parameter Number - TIDAK DISARANKAN untuk filter berbasis teks
        forms.alert(
            "Parameter 'Sub Category' bertipe NUMERIK.\n\n" +
            "Filter ini dirancang untuk parameter TEXT.\n\n" +
            "Silakan:\n" +
            "1. Ubah parameter 'Sub Category' menjadi tipe TEXT, atau\n" +
            "2. Masukkan nilai numerik yang valid\n\n" +
            "Tipe parameter: {}".format(type_info['type_name']),
            title="Parameter Type Mismatch"
        )
        script.exit()
    elif type_info['is_integer']:
        # Parameter Integer - TIDAK DISARANKAN untuk filter berbasis teks
        forms.alert(
            "Parameter 'Sub Category' bertipe INTEGER.\n\n" +
            "Filter ini dirancang untuk parameter TEXT.\n\n" +
            "Silakan:\n" +
            "1. Ubah parameter 'Sub Category' menjadi tipe TEXT, atau\n" +
            "2. Masukkan nilai integer yang valid\n\n" +
            "Tipe parameter: {}".format(type_info['type_name']),
            title="Parameter Type Mismatch"
        )
        script.exit()
    elif type_info['is_boolean']:
        # Parameter Yes/No
        lower_input = sub_category_input.lower()
        if lower_input in ['yes', 'true', '1', 'ya', 'y']:
            converted_value = 1
        elif lower_input in ['no', 'false', '0', 'tidak', 'n']:
            converted_value = 0
        else:
            raise Exception("Input '{}' tidak valid untuk parameter Yes/No. Gunakan 'yes'/'no', 'true'/'false', atau '1'/'0'.".format(sub_category_input))

        filter_rule = DB.ParameterFilterRuleFactory.CreateNotEqualsRule(
            param_id,
            converted_value
        )
    else:
        # Default: coba sebagai text dengan Does Not Equal rule
        try:
            converted_value = sub_category_input
            filter_rule = DB.ParameterFilterRuleFactory.CreateNotEqualsRule(
                param_id,
                converted_value
            )
        except:
            # Jika gagal, informasikan user tentang tipe parameter
            forms.alert(
                "Tipe parameter 'Sub Category' tidak didukung untuk filter berbasis teks.\n\n" +
                "Tipe parameter: {}\n\n".format(type_info['type_name']) +
                "Script ini hanya mendukung parameter TEXT.",
                title="Unsupported Parameter Type"
            )
            script.exit()

    element_filter = DB.ElementParameterFilter(filter_rule)

except Exception as param_error:
    forms.alert("Tidak bisa men-setup filter berdasarkan parameter '{}'. Error: {}".format(target_param_name, param_error),
                title="Parameter Error")
    script.exit()

# 5. Identify target categories (Sections, Callouts, Elevations)
category_ids = List[DB.ElementId]()
category_ids.Add(DB.ElementId(DB.BuiltInCategory.OST_Sections))
category_ids.Add(DB.ElementId(DB.BuiltInCategory.OST_Callouts))
category_ids.Add(DB.ElementId(DB.BuiltInCategory.OST_Elev))

# 6. Create the ParameterFilterElement
t = DB.Transaction(doc, "Create Filter Section")
try:
    t.Start()
    existing_filters = DB.FilteredElementCollector(doc) \
                        .OfClass(DB.ParameterFilterElement) \
                        .ToElements()

    existing_filter = None
    for filter_elem in existing_filters:
        if filter_elem.Name == filter_name:
            existing_filter = filter_elem
            break

    if existing_filter:
        forms.alert(
            "A filter with the name:\n\n     {0}   \n\nalready exists.\nPlease choose a different name!".format(filter_name),
            title="Filter Exists"
        )
        t.RollBack()
    else:
        new_filter = DB.ParameterFilterElement.Create(
            doc,
            filter_name,
            category_ids,
            element_filter
        )
        t.Commit()
        forms.toast(
            "Filter '{}' berhasil dibuat!".format(filter_name),
            title="Filter Section Created",
            appid="PrasKaaPyKit"
        )
except Exception as e:
    t.RollBack()
    forms.alert("Error creating filter: {}".format(e), title="Error")