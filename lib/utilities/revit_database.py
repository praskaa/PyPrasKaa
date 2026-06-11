"""
Revit database utilities for filtering, categories, and common operations.

Migrated from pyChilizer database.py module.
Provides filter creation, category management, and Revit database operations.
"""

from pyrevit import revit, DB, script, forms, HOST_APP, coreutils, PyRevitException
from pyrevit.framework import List
from collections import defaultdict
from pyrevit.revit.db import query
from Autodesk.Revit import Exceptions
import clr
import System

BIC = DB.BuiltInCategory


def get_solid_fill_pat(doc=revit.doc):
    """
    Get the Solid Fill pattern element.

    Args:
        doc: Revit Document

    Returns:
        FillPatternElement: Solid fill pattern
    """
    fill_pats = DB.FilteredElementCollector(doc).OfClass(DB.FillPatternElement)
    solid_pat = [pat for pat in fill_pats if pat.GetFillPattern().IsSolidFill]
    return solid_pat[0]


def create_filter_by_name_bics(filter_name, bics_list, doc=revit.doc):
    """
    Create a parameter filter from filter name and list of built-in categories.

    Args:
        filter_name: str, name of the filter
        bics_list: list of DB.BuiltInCategory
        doc: Revit Document

    Returns:
        ParameterFilterElement: Created filter
    """
    cat_list = List[DB.ElementId](DB.ElementId(cat) for cat in bics_list)
    filter = DB.ParameterFilterElement.Create(doc, filter_name, cat_list)
    return filter


def filter_from_rules(rules, or_rule=False):
    """
    Create element filter from list of filter rules.

    Args:
        rules: list of FilterRule objects
        or_rule: bool, use logical OR if True, AND if False

    Returns:
        ElementFilter: Combined filter
    """
    elem_filters = List[DB.ElementFilter]()
    for rule in rules:
        elem_parameter_filter = DB.ElementParameterFilter(rule)
        elem_filters.Add(elem_parameter_filter)
    if or_rule:
        elem_filter = DB.LogicalOrFilter(elem_filters)
    else:
        elem_filter = DB.LogicalAndFilter(elem_filters)
    return elem_filter


def check_filter_exists(filter_name, doc=revit.doc):
    """
    Check if a filter with given name exists.

    Args:
        filter_name: str
        doc: Revit Document

    Returns:
        FilterElement or None: Existing filter if found
    """
    all_view_filters = DB.FilteredElementCollector(doc).OfClass(DB.FilterElement).ToElements()

    for vf in all_view_filters:
        if filter_name == str(vf.Name):
            return vf


def shared_param_id_from_guid(categories_list, guid, doc=revit.doc):
    """
    Return the parameter ID from GUID for shared parameters.

    Args:
        categories_list: list of BuiltInCategory
        guid: str, GUID of shared parameter
        doc: Revit Document

    Returns:
        ElementId or None: Parameter ID if found
    """
    for bic in categories_list:
        # iterating through each category helps address cases where some selected categories are not present in the model
        any_element_of_cat = DB.FilteredElementCollector(doc).OfCategory(
            bic).WhereElementIsNotElementType().ToElements()
        for el in any_element_of_cat:
            element_i_params = el.Parameters
            for p in element_i_params:
                try:
                    if p.GUID == guid:
                        return p.Id
                except Exceptions.InvalidOperationException:
                    pass
            element_t_params = query.get_type(el).Parameters
            for p in element_t_params:
                try:
                    if p.GUID and p.GUID == guid:
                        return p.Id
                except Exceptions.InvalidOperationException:
                    pass
    return None


def get_builtin_label(bip_or_bic):
    """
    Return a language-specific label for the BIP or BIC.

    Args:
        bip_or_bic: BuiltInParameter or BuiltInCategory

    Returns:
        str: Localized label
    """
    return DB.LabelUtils.GetLabelFor(bip_or_bic)


def get_document_model_bics(doc=revit.doc):
    """
    Get all model built-in categories of the document.

    Args:
        doc: Revit Document

    Returns:
        list: List of BuiltInCategory for model categories
    """
    built_in_categories = []
    for category in doc.Settings.Categories:
        if HOST_APP.is_newer_than(2022):
            bic = category.BuiltInCategory
        else:
            bic = System.Enum.ToObject(BIC, category.Id.IntegerValue)
        if category.CategoryType == DB.CategoryType.Model and bic != DB.BuiltInCategory.INVALID and category.Id.IntegerValue < 0:
            built_in_categories.append(bic)
    return built_in_categories


# Structural engineering focused categories
FREQUENTLY_SELECTED_CATEGORIES = [
    BIC.OST_StructuralFraming,      # Beams
    BIC.OST_StructuralColumns,      # Columns
    BIC.OST_Floors,                 # Floors
    BIC.OST_Walls,                  # Walls
    BIC.OST_StructuralFoundation,   # Foundations
    BIC.OST_Rebar,                  # Rebar
    BIC.OST_StructuralConnections,  # Connections
    BIC.OST_DetailComponents,      # Detail Components
]


def frequent_category_labels():
    """
    Get localized labels for frequently selected structural categories.

    Returns:
        list: List of localized category names
    """
    return [get_builtin_label(bic) for bic in FREQUENTLY_SELECTED_CATEGORIES]


def model_categories_dict(doc):
    """
    Create a dictionary of common categories used for colorizers.
    Formatted as {Category name : BIC}

    Args:
        doc: Revit Document

    Returns:
        dict: {localized_name: BuiltInCategory}
    """
    category_opt_dict = {}
    for cat in get_document_model_bics(doc):
        category_opt_dict[get_builtin_label(cat)] = cat
    return category_opt_dict


def category_labels_to_bic(labels, doc):
    """
    Convert list of category labels to dictionary {label: BIC}

    Args:
        labels: list of str, category labels
        doc: Revit Document

    Returns:
        dict: {label: BuiltInCategory}
    """
    categories_dict = {}
    for label in labels:
        categories_dict[label] = model_categories_dict(doc)[label]
    return categories_dict


def delete_existing_view(view_name, doc=revit.doc):
    """
    Delete an existing view by name.

    Args:
        view_name: str, name of the view to delete
        doc: Revit Document

    Returns:
        bool: True if deleted successfully, False otherwise
    """
    for view in DB.FilteredElementCollector(doc).OfClass(DB.View).ToElements():
        if view.Name == view_name:
            try:
                doc.Delete(view.Id)
                return True
            except:
                forms.alert('Current view cannot be deleted. Close view and try again.')
                return False
    return True


def remove_viewtemplate(vt_id, doc=revit.doc):
    """
    Remove the default view template from a view type.

    Args:
        vt_id: ElementId of the view type
        doc: Revit Document
    """
    viewtype = doc.GetElement(vt_id)
    template_id = viewtype.DefaultTemplateId
    if template_id.IntegerValue != -1:
        if forms.alert(
                "You are about to remove the View Template"
                " associated with this View Type. Is that cool with ya?",
                ok=False, yes=True, no=True, exitscript=True):
            viewtype.DefaultTemplateId = DB.ElementId(-1)


def get_3Dviewtype_id(doc=revit.doc):
    """
    Get the ElementId of the 3D View Family Type.

    Args:
        doc: Revit Document

    Returns:
        ElementId: ID of the 3D view family type
    """
    view_fam_type = DB.FilteredElementCollector(doc).OfClass(DB.ViewFamilyType)
    return next(vt.Id for vt in view_fam_type if vt.ViewFamily == DB.ViewFamily.ThreeDimensional)