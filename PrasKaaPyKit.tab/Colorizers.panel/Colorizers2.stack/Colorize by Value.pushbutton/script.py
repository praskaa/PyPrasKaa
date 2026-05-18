# -*- coding: utf-8 -*-
"""
Colorize by Value
Description: Override element colors based on parameter values.
             Shift+Click: apply overrides to multiple selected views.
Author: PrasKaa
Version: 1.1.0
Last Updated: 2026-03-18

Changelog:
    v1.1.0 (2026-03-18): Shift+Click mode - apply overrides to multiple views
                         (regular views only, View Templates excluded)
    v1.0.0            : Initial release
"""

from pyrevit import revit, DB, forms, script
from pyrevit.revit.db import query
from collections import defaultdict

# Explicit imports from lib
from database import get_param_value_as_string
from colorize import (
    get_colorize_only_categories_config,
    get_colours,
    set_colour_overrides_by_option,
    get_config,
    OVERRIDES_CONFIG_OPTION_NAME,
    default_override_options
)

logger = script.get_logger()
BIC = DB.BuiltInCategory
doc = revit.doc
view = revit.active_view

# Detect Shift+Click using pyRevit's recommended EXEC_PARAMS.config_mode.
# This is the preferred method over the older __shiftclick__ builtin.
# Requires NO config script inside the bundle — otherwise pyRevit runs
# the config script directly and this code is never reached.
from pyrevit import EXEC_PARAMS
_is_shiftclick = EXEC_PARAMS.config_mode

# Get colorizebyvalue config - to store override options
overrides_config = script.get_config()


def get_overrides_config():
    return get_config(overrides_config, OVERRIDES_CONFIG_OPTION_NAME, default_override_options)


overrides_option = get_overrides_config()
categories_for_selection = get_colorize_only_categories_config(doc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class ParameterOption(forms.TemplateListItem):
    """Wrapper for selecting parameters from a list"""

    def __init__(self, param, param_dict, param_type):
        self.param = param
        self.param_dict = param_dict
        self.param_type = param_type
        super(ParameterOption, self).__init__((param, param_type))

    @property
    def name(self):
        return str(self.param_dict[self.param])


class ViewOption(forms.TemplateListItem):
    """Wrapper for displaying regular views in SelectFromList.
    Shows 'ViewType | View Name' so the user can distinguish views easily.
    """

    def __init__(self, v):
        super(ViewOption, self).__init__(v)

    @property
    def name(self):
        return "{} | {}".format(self.item.ViewType, self.item.Name)


# View types that make sense to colorize elements in.
# Sheets and Schedules are excluded — SetElementOverrides does not apply there.
_VALID_VIEW_TYPES = {
    DB.ViewType.FloorPlan,
    DB.ViewType.CeilingPlan,
    DB.ViewType.Elevation,
    DB.ViewType.Section,
    DB.ViewType.ThreeD,
    DB.ViewType.Detail,
    DB.ViewType.DraftingView,
    DB.ViewType.AreaPlan,
    DB.ViewType.EngineeringPlan,
}


def get_regular_views():
    """Return all non-template, non-sheet views that support element overrides,
    sorted by ViewType then Name.
    """
    all_views = DB.FilteredElementCollector(doc) \
        .OfClass(DB.View) \
        .ToElements()
    regular = [
        v for v in all_views
        if not v.IsTemplate
        and v.ViewType in _VALID_VIEW_TYPES
        and not v.IsCallout  # skip callout views that are sub-views of sheets
    ]
    return sorted(regular, key=lambda v: (str(v.ViewType), v.Name))


def param_is_bip(param):
    return param.Definition.BuiltInParameter != DB.BuiltInParameter.INVALID


# ---------------------------------------------------------------------------
# Step 1 – Category selection
# ---------------------------------------------------------------------------

sorted_cats = sorted(categories_for_selection.keys(), key=lambda x: x)

if forms.check_modelview(revit.active_view):
    selected_cat = forms.CommandSwitchWindow.show(
        sorted_cats,
        message="Select Category to Colorize",
        width=400
    )
else:
    selected_cat = None

if selected_cat is None:
    script.exit()

chosen_bic = categories_for_selection[selected_cat]

all_cats = doc.Settings.Categories
chosen_category = all_cats.get_Item(chosen_bic)
hide_categories_except = [c for c in all_cats if c.Id != chosen_category.Id]

get_view_elements = DB.FilteredElementCollector(doc) \
    .OfCategory(chosen_bic) \
    .WhereElementIsNotElementType() \
    .ToElements()

# ---------------------------------------------------------------------------
# Step 2 – Build parameter dictionaries
# ---------------------------------------------------------------------------

inst_param_dict = {}
type_param_dict = {}

for e in get_view_elements:
    element_parameter_set = e.Parameters
    for ip in element_parameter_set:
        if ip.IsShared and ip.Definition.Id not in inst_param_dict:
            pretty_param_name = "".join([str(ip.Definition.Name), " [Shared Parameter]"])
            inst_param_dict[ip.Definition.Id] = pretty_param_name
        elif param_is_bip(ip) and ip.Definition.Name not in inst_param_dict:
            inst_param_dict[ip.Definition.BuiltInParameter] = str(ip.Definition.Name)
        elif not ip.IsShared and not param_is_bip(ip) and ip.Definition.Name not in inst_param_dict:
            pretty_param_name = "".join([str(ip.Definition.Name), " [Family Parameter]"])
            inst_param_dict[ip.Definition.Name] = pretty_param_name

    type_parameter_set = doc.GetElement(e.GetTypeId()).Parameters
    for tp in type_parameter_set:
        if tp.IsShared and tp.Definition.Id not in type_param_dict:
            pretty_param_name = "".join([str(tp.Definition.Name), " [Shared Parameter]"])
            type_param_dict[tp.Definition.Id] = pretty_param_name
        elif param_is_bip(tp) and tp.Definition.Name not in type_param_dict:
            type_param_dict[tp.Definition.BuiltInParameter] = str(tp.Definition.Name)
        elif not tp.IsShared and not param_is_bip(tp) and tp.Definition.Name not in type_param_dict:
            pretty_param_name = "".join([str(tp.Definition.Name), " [Family Parameter]"])
            type_param_dict[tp.Definition.Name] = pretty_param_name

# ---------------------------------------------------------------------------
# Step 3 – Parameter selection
# ---------------------------------------------------------------------------

instance_p_class = [ParameterOption(x, inst_param_dict, 'instance') for x in inst_param_dict.keys()]
type_p_class = [ParameterOption(x, type_param_dict, 'type') for x in type_param_dict.keys()]
i_p_ops = sorted(instance_p_class, key=lambda x: x.name)
t_p_ops = sorted(type_p_class, key=lambda x: x.name)
ops = {"Type Parameters": t_p_ops, "Instance Parameters": i_p_ops}

selected_parameter = forms.SelectFromList.show(
    ops,
    button_name="Select Parameters",
    multiselect=False
)

forms.alert_ifnot(selected_parameter, "No Parameters Selected", exitscript=True)

# Unpack selected parameter
selected_param, selected_param_type = selected_parameter

# ---------------------------------------------------------------------------
# Step 4 – Override style selection
# ---------------------------------------------------------------------------

override_style_options = [
    "Pattern Only",
    "Lines Only",
    "Lines & Pattern"
]

selected_override_style = forms.CommandSwitchWindow.show(
    override_style_options,
    message="Select Override Style",
    width=400
)

if selected_override_style is None:
    script.exit()

if selected_override_style == "Pattern Only":
    override_option = ["Projection Surface Colour", "Cut Pattern Colour"]
elif selected_override_style == "Lines Only":
    override_option = ["Projection Line Colour", "Cut Line Colour"]
else:  # Lines & Pattern
    override_option = ["Projection Line Colour", "Projection Surface Colour",
                       "Cut Line Colour", "Cut Pattern Colour"]

# ---------------------------------------------------------------------------
# Step 5 – Collect element → param value mapping
# ---------------------------------------------------------------------------

values_dict = defaultdict(list)  # {param_value_string : [ElementId, ...]}

for el in get_view_elements:
    if selected_param_type == 'instance':
        if isinstance(selected_param, DB.BuiltInParameter):
            el_parameter = el.get_Parameter(selected_param)
        elif isinstance(selected_param, str):
            el_parameter = el.LookupParameter(selected_param)
        else:  # ElementId shared
            el_parameter = el.get_Parameter(selected_param)
    else:  # type
        el_type = query.get_type(el)
        if isinstance(selected_param, DB.BuiltInParameter):
            el_parameter = el_type.get_Parameter(selected_param)
        elif isinstance(selected_param, str):
            el_parameter = el_type.LookupParameter(selected_param)
        else:  # ElementId shared
            el_parameter = el_type.get_Parameter(selected_param)

    if el_parameter:
        param_value = get_param_value_as_string(el_parameter)
        if param_value is not None:
            values_dict[param_value].append(el.Id)

n = len(values_dict.keys())
forms.alert_ifnot(n > 0, "No values found for the selected parameter.", exitscript=True)

# ---------------------------------------------------------------------------
# Step 6 – (Shift+Click only) Select target views
# ---------------------------------------------------------------------------

if _is_shiftclick:
    regular_views = get_regular_views()
    if not regular_views:
        forms.alert("No regular views found in this document.", exitscript=True)

    view_options = [ViewOption(v) for v in regular_views]

    selected_view_options = forms.SelectFromList.show(
        view_options,
        message="Select Views to Apply Overrides To",
        button_name="Apply to Selected Views",
        multiselect=True,
        width=550
    )

    if not selected_view_options:
        forms.alert("No views selected.", exitscript=True)

    # Unwrap to DB.View objects
    target_views = [
        opt if isinstance(opt, DB.View) else opt.item
        for opt in selected_view_options
    ]
else:
    # Normal click — active view only
    target_views = [view]

# ---------------------------------------------------------------------------
# Step 7 – Build colour map and apply overrides
# ---------------------------------------------------------------------------

revit_colours = get_colours(n)

# Pre-build the (override, [element_ids]) pairs — computed once, applied to all targets
colour_map = []  # [(OverrideGraphicSettings, [ElementId, ...])]

with revit.Transaction("Colorize by Value", doc):
    for param_value, colour in zip(values_dict.keys(), revit_colours):
        override = set_colour_overrides_by_option(override_option, colour, doc)
        colour_map.append((override, values_dict[param_value]))

    for target in target_views:
        for override, el_ids in colour_map:
            for el_id in el_ids:
                target.SetElementOverrides(el_id, override)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

target_names = ", ".join(t.Name for t in target_views)
forms.alert(
    "{} colour group(s) applied across {} view(s):\n{}".format(
        len(colour_map), len(target_views), target_names
    ),
    title="Colorize by Value"
)