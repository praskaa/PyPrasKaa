# -*- coding: utf-8 -*-
__title__ = 'Create Filter\nSection/Detail/Elevation'
__author__ = 'PrasKaa'
__version__ = 'Version: 2.0'
__doc__ ="""Version: 2.0
Date    = 11.03.2026
_____________________________________________________________________
Description:
Creates a Revit parameter filter targeting sections, callouts, and
elevations based on user-selected filter type:
  - Sub Category  : Project/Shared parameter (text-based)
  - Category      : Project/Shared parameter (text-based)
  - View Name     : Built-in parameter VIEW_NAME (contains/not contains)
_____________________________________________________________________
How-to:
1. Click "Create Filter"
2. Select filter type (Sub Category / Category / View Name)
3. Follow the prompts for the selected type
4. Filter will be created and ready to apply in Visibility/Graphics

Notes:
- Sub Category & Category: requires matching project/shared parameter
- View Name: uses built-in VIEW_NAME parameter (no shared param needed)
- View Name filter supports "Contains" or "Does Not Contain" rule
- Supports Text, Number, Integer, and Yes/No parameter types
____________________________________________________________________
Last update:
- 11.03.2026 - 2.0 Added View Name filter option
- 04.03.2026 - 1.0 Initial release
_____________________________________________________________________
"""

from pyrevit import revit, DB, forms, script
from System.Collections.Generic import List
from Autodesk.Revit.UI import TaskDialog


# ─────────────────────────────────────────────
#  UTILITY FUNCTIONS
# ─────────────────────────────────────────────

def find_parameter_element(doc, parameter_name):
    """
    Find a ParameterElement by name from the document.

    Searches through all ParameterElement objects (shared & project params)
    to find one with the specified name.

    Args:
        doc (DB.Document): The Revit document to search in
        parameter_name (str): The name of the parameter to find

    Returns:
        DB.ParameterElement or None
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
        DB.Definition
    """
    return parameter_element.GetDefinition()


def get_parameter_type_info(parameter_element):
    """
    Get comprehensive type information for a parameter.

    Handles both pre-2022 and 2022+ Revit API versions.

    Args:
        parameter_element (DB.ParameterElement): The parameter element

    Returns:
        dict with keys: type_id, type_name, is_text, is_number,
                        is_integer, is_boolean
    """
    definition = get_parameter_definition(parameter_element)

    try:
        # Revit 2022+ using ForgeTypeId
        data_type = definition.GetDataType()
        type_id   = data_type
        type_name = data_type.TypeId if hasattr(data_type, 'TypeId') else str(data_type)

        return {
            'type_id'   : type_id,
            'type_name' : type_name,
            'is_text'   : data_type == DB.SpecTypeId.String.Text,
            'is_number' : data_type == DB.SpecTypeId.Number,
            'is_integer': data_type == DB.SpecTypeId.Int.Integer,
            'is_boolean': data_type == DB.SpecTypeId.Boolean.YesNo
        }
    except AttributeError:
        # Fallback for Revit < 2022
        param_type = definition.ParameterType

        return {
            'type_id'   : param_type,
            'type_name' : str(param_type),
            'is_text'   : param_type == DB.ParameterType.Text,
            'is_number' : param_type == DB.ParameterType.Number,
            'is_integer': param_type == DB.ParameterType.Integer,
            'is_boolean': param_type == DB.ParameterType.YesNo
        }


def build_filter_rule_for_text_param(param_id, value, rule_type="not_equals"):
    """
    Build a FilterRule for a text-based project/shared parameter.

    Args:
        param_id   : DB.ElementId of the parameter
        value      : string value to match
        rule_type  : "not_equals" | "equals" | "contains" | "not_contains"

    Returns:
        DB.FilterRule
    """
    if rule_type == "equals":
        return DB.ParameterFilterRuleFactory.CreateEqualsRule(param_id, value)
    elif rule_type == "contains":
        return DB.ParameterFilterRuleFactory.CreateContainsRule(param_id, value, False)
    elif rule_type == "not_contains":
        return DB.ParameterFilterRuleFactory.CreateNotContainsRule(param_id, value, False)
    else:  # default: not_equals
        return DB.ParameterFilterRuleFactory.CreateNotEqualsRule(param_id, value)


def build_filter_rule_for_builtin_param(builtin_param, value, rule_type="not_equals"):
    """
    Build a FilterRule using a BuiltInParameter (e.g. VIEW_NAME).

    Args:
        builtin_param : DB.BuiltInParameter enum value
        value         : string to match
        rule_type     : "not_equals" | "equals" | "contains" | "not_contains"

    Returns:
        DB.FilterRule
    """
    param_id = DB.ElementId(builtin_param)

    if rule_type == "equals":
        return DB.ParameterFilterRuleFactory.CreateEqualsRule(param_id, value)
    elif rule_type == "contains":
        return DB.ParameterFilterRuleFactory.CreateContainsRule(param_id, value, False)
    elif rule_type == "not_contains":
        return DB.ParameterFilterRuleFactory.CreateNotContainsRule(param_id, value, False)
    else:
        return DB.ParameterFilterRuleFactory.CreateNotEqualsRule(param_id, value)


# ─────────────────────────────────────────────
#  MAIN SCRIPT
# ─────────────────────────────────────────────

doc   = revit.doc
uidoc = revit.uidoc

# ── Step 1: Choose filter type ────────────────
param_options = ["Sub Category", "Category", "View Name"]
selected_param = forms.SelectFromList.show(
    param_options,
    title="Select Filter Type",
    button_name="Select"
)

if not selected_param:
    forms.toast("No filter type selected. Aborting.",
                title="Filter Creation Cancelled",
                appid="FilterSection")
    script.exit()


# ─────────────────────────────────────────────
#  BRANCH A: Sub Category / Category
#  (uses project/shared parameter)
# ─────────────────────────────────────────────

if selected_param in ("Sub Category", "Category"):

    param_abbrev = "SubCat" if selected_param == "Sub Category" else "Cat"

    # Prompt for value
    sub_category_input = forms.ask_for_string(
        default="xx.x_SubCategoryName",
        prompt="Enter Sub Category Name (Format: xx.x_TypeofSubCategory)",
        title="Create Filter – {}".format(selected_param)
    )

    if not sub_category_input:
        forms.toast("No sub-category name provided. Aborting.",
                    title="Filter Creation Cancelled",
                    appid="FilterSection")
        script.exit()

    # Derive a readable filter name from the input
    split_string = sub_category_input.split('_')
    filter_name_part = '_'.join(split_string[1:]).replace('_', ' ').title() \
                       if len(split_string) > 1 else sub_category_input.title()

    filter_name = "Section Filter - {} {}".format(param_abbrev, filter_name_part)

    # Build filter rule
    try:
        pe = find_parameter_element(doc, selected_param)

        if pe is None:
            raise Exception(
                "Project/Shared Parameter '{}' not found in document.".format(selected_param)
            )

        param_id  = pe.Id
        type_info = get_parameter_type_info(pe)

        if type_info['is_text']:
            filter_rule = build_filter_rule_for_text_param(
                param_id, sub_category_input, "not_equals"
            )

        elif type_info['is_number']:
            forms.alert(
                "Parameter '{}' is NUMERIC type.\n\n".format(selected_param) +
                "This filter is designed for TEXT parameters.\n\n" +
                "Please change the parameter type to TEXT, or enter a valid numeric value.\n\n" +
                "Parameter type: {}".format(type_info['type_name']),
                title="Parameter Type Mismatch"
            )
            script.exit()

        elif type_info['is_integer']:
            forms.alert(
                "Parameter '{}' is INTEGER type.\n\n".format(selected_param) +
                "This filter is designed for TEXT parameters.\n\n" +
                "Please change the parameter type to TEXT.\n\n" +
                "Parameter type: {}".format(type_info['type_name']),
                title="Parameter Type Mismatch"
            )
            script.exit()

        elif type_info['is_boolean']:
            lower_input = sub_category_input.lower()
            if lower_input in ('yes', 'true', '1', 'ya', 'y'):
                converted_value = 1
            elif lower_input in ('no', 'false', '0', 'tidak', 'n'):
                converted_value = 0
            else:
                raise Exception(
                    "Input '{}' is not valid for a Yes/No parameter. "
                    "Use 'yes'/'no', 'true'/'false', or '1'/'0'.".format(sub_category_input)
                )
            filter_rule = DB.ParameterFilterRuleFactory.CreateNotEqualsRule(
                param_id, converted_value
            )

        else:
            # Fallback: try as text
            try:
                filter_rule = build_filter_rule_for_text_param(
                    param_id, sub_category_input, "not_equals"
                )
            except Exception:
                forms.alert(
                    "Unsupported parameter type for text-based filter.\n\n" +
                    "Parameter type: {}".format(type_info['type_name']),
                    title="Unsupported Parameter Type"
                )
                script.exit()

        element_filter = DB.ElementParameterFilter(filter_rule)

    except Exception as param_error:
        forms.alert(
            "Cannot setup filter for parameter '{}'.\nError: {}".format(
                selected_param, param_error),
            title="Parameter Error"
        )
        script.exit()


# ─────────────────────────────────────────────
#  BRANCH B: View Name
#  (uses built-in VIEW_NAME parameter)
# ─────────────────────────────────────────────

elif selected_param == "View Name":

    # Ask for rule direction: Contains vs Does Not Contain
    rule_options = ["Contains", "Does Not Contain", "Equals", "Does Not Equal"]
    selected_rule = forms.SelectFromList.show(
        rule_options,
        title="Select View Name Rule",
        button_name="Select"
    )

    if not selected_rule:
        forms.toast("No rule selected. Aborting.",
                    title="Filter Creation Cancelled",
                    appid="FilterSection")
        script.exit()

    # Map display name to internal key
    rule_map = {
        "Contains"         : "contains",
        "Does Not Contain" : "not_contains",
        "Equals"           : "equals",
        "Does Not Equal"   : "not_equals"
    }
    rule_type = rule_map[selected_rule]

    # Ask for the view name keyword
    view_name_input = forms.ask_for_string(
        default="",
        prompt="Enter View Name keyword (e.g. 'Section', 'Level 1', 'A-')",
        title="Create Filter – View Name"
    )

    if not view_name_input:
        forms.toast("No view name keyword provided. Aborting.",
                    title="Filter Creation Cancelled",
                    appid="FilterSection")
        script.exit()

    # Build a clean filter name
    safe_keyword   = view_name_input.replace(' ', '_').title()
    rule_label_map = {
        "contains"     : "Contains",
        "not_contains" : "NotContains",
        "equals"       : "Equals",
        "not_equals"   : "NotEquals"
    }
    filter_name = "Section Filter - ViewName {} {}".format(
        rule_label_map[rule_type], safe_keyword
    )

    # Build filter rule using VIEW_NAME built-in parameter
    try:
        filter_rule = build_filter_rule_for_builtin_param(
            DB.BuiltInParameter.VIEW_NAME,
            view_name_input,
            rule_type
        )
        element_filter = DB.ElementParameterFilter(filter_rule)

    except Exception as vn_error:
        forms.alert(
            "Cannot create View Name filter.\nError: {}".format(vn_error),
            title="View Name Filter Error"
        )
        script.exit()


# ─────────────────────────────────────────────
#  STEP: Define target categories
#        (Sections, Callouts, Elevations)
# ─────────────────────────────────────────────

category_ids = List[DB.ElementId]()
category_ids.Add(DB.ElementId(DB.BuiltInCategory.OST_Sections))
category_ids.Add(DB.ElementId(DB.BuiltInCategory.OST_Callouts))
category_ids.Add(DB.ElementId(DB.BuiltInCategory.OST_Elev))


# ─────────────────────────────────────────────
#  STEP: Create ParameterFilterElement in doc
# ─────────────────────────────────────────────

t = DB.Transaction(doc, "Create Filter Section")
try:
    t.Start()

    # Check for duplicate filter name
    existing_filters = (
        DB.FilteredElementCollector(doc)
        .OfClass(DB.ParameterFilterElement)
        .ToElements()
    )
    existing_filter = next(
        (f for f in existing_filters if f.Name == filter_name), None
    )

    if existing_filter:
        forms.alert(
            "A filter with the name:\n\n     {}\n\nalready exists.\n"
            "Please choose a different name!".format(filter_name),
            title="Filter Already Exists"
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
            "Filter '{}' created successfully!".format(filter_name),
            title="Filter Section Created",
            appid="PrasKaaPyKit"
        )

except Exception as e:
    t.RollBack()
    forms.alert("Error creating filter: {}".format(e), title="Error")