# -*- coding: utf-8 -*-
"""
Reset Overrides
Description: Reset all element overrides in the active view.
Shift-Click: Reset element overrides in multiple selected views.
Author: PrasKaa
Version: 1.0.0
Last Updated: 2026-03-18

Changelog:
    v1.0.0 (2026-03-18): Initial release with Shift+Click multi-view support
"""

from pyrevit import revit, DB, forms, script, EXEC_PARAMS

doc = revit.doc
view = revit.active_view

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


class ViewOption(forms.TemplateListItem):
    """Displays 'ViewType | View Name' in SelectFromList."""

    def __init__(self, v):
        super(ViewOption, self).__init__(v)

    @property
    def name(self):
        return "{} | {}".format(self.item.ViewType, self.item.Name)


def get_regular_views():
    """Return all non-template views that support element overrides, sorted by type then name."""
    all_views = DB.FilteredElementCollector(doc).OfClass(DB.View).ToElements()
    regular = [
        v for v in all_views
        if not v.IsTemplate
        and v.ViewType in _VALID_VIEW_TYPES
    ]
    return sorted(regular, key=lambda v: (str(v.ViewType), v.Name))


def reset_overrides_in_view(target_view):
    """Reset all element overrides in a single view."""
    el_ids = DB.FilteredElementCollector(doc, target_view.Id) \
        .WhereElementIsNotElementType() \
        .ToElementIds()
    blank = DB.OverrideGraphicSettings()
    for el_id in el_ids:
        target_view.SetElementOverrides(el_id, blank)
    return len(list(el_ids))


# ---------------------------------------------------------------------------
# Normal click — reset active view only
# ---------------------------------------------------------------------------

if not EXEC_PARAMS.config_mode:
    with revit.Transaction("Reset Overrides", doc):
        count = reset_overrides_in_view(view)
    forms.alert(
        "Reset overrides on {} element(s) in: {}".format(count, view.Name),
        title="Reset Overrides"
    )

# ---------------------------------------------------------------------------
# Shift+Click — pick views from a list, reset all selected
# ---------------------------------------------------------------------------

else:
    regular_views = get_regular_views()
    if not regular_views:
        forms.alert("No regular views found in this document.", exitscript=True)

    view_options = [ViewOption(v) for v in regular_views]

    selected_view_options = forms.SelectFromList.show(
        view_options,
        message="Select Views to Reset Overrides",
        button_name="Reset Selected Views",
        multiselect=True,
        width=550
    )

    if not selected_view_options:
        script.exit()

    target_views = [
        opt if isinstance(opt, DB.View) else opt.item
        for opt in selected_view_options
    ]

    with revit.Transaction("Reset Overrides", doc):
        total = 0
        for target in target_views:
            total += reset_overrides_in_view(target)

    target_names = "\n".join("- " + t.Name for t in target_views)
    forms.alert(
        "Reset overrides on {} element(s) across {} view(s):\n{}".format(
            total, len(target_views), target_names
        ),
        title="Reset Overrides"
    )