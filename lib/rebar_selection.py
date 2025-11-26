# -*- coding: utf-8 -*-
"""
Rebar Selection Utilities
Library untuk memfasilitasi selection RebarBarType dan elemen rebar lainnya
Berdasarkan pola dari EF-Tools _selection.py dengan adaptasi khusus untuk rebar
"""

import sys
import clr
import traceback

from Autodesk.Revit.UI.Selection import ObjectType
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import RebarBarType

# pyRevit IMPORTS
from pyrevit.forms import SelectFromList
from pyrevit import forms

#.NET
clr.AddReference('System')
from System.Collections.Generic import List

# CUSTOM IMPORTS
from GUI.forms import select_from_dict

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#==================================================
uidoc     = __revit__.ActiveUIDocument
doc       = __revit__.ActiveUIDocument.Document
selection = uidoc.Selection                          # type: Selection

# ╔═╗╔═╗╔╦╗  ╔═╗╔═╗╦  ╔═╗╔═╗╔╦╗╔═╗╔╦╗
# ║ ╦║╣  ║   ╚═╗║╣ ║  ║╣ ║   ║ ║╣  ║║
# ╚═╝╚═╝ ╩   ╚═╝╚═╝╩═╝╚═╝╚═╝ ╩ ╚═╝═╩╝
#==================================================

def select_rebar_bar_type(given_uidoc=uidoc, exitscript=True, title="Select Rebar Bar Type", label="Choose Rebar Bar Type"):
    """
    Function to let user select a rebar bar type from available types.
    Based on EF-Tools select_title_block pattern but adapted for RebarBarType.

    Args:
        given_uidoc: UIDocument to work with
        exitscript: Whether to exit if no selection made
        title: Dialog title
        label: Dialog label

    Returns:
        Selected RebarBarType element or None
    """
    doc = given_uidoc.Document

    try:
        # Get all RebarBarType elements
        all_rebar_types = FilteredElementCollector(doc).OfClass(RebarBarType).ToElements()

        if not all_rebar_types:
            forms.alert("No Rebar Bar Types found in the project.", exitscript=exitscript)
            return None

        # Create selection dictionary with rich information
        dict_rebar_types = {}
        for rbt in all_rebar_types:
            try:
                # Get name
                type_name_param = rbt.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                name = type_name_param.AsString() if type_name_param and type_name_param.AsString() else "Unnamed"

                # Get diameter for better identification
                diameter = "N/A"
                bar_diameter_param = rbt.get_Parameter(BuiltInParameter.REBAR_BAR_DIAMETER)
                if bar_diameter_param:
                    diameter_feet = bar_diameter_param.AsDouble()
                    diameter_mm = diameter_feet * 304.8  # Convert feet to mm
                    diameter = "{:.0f}mm".format(diameter_mm)

                # Get grade/material info if available
                grade = ""
                material_param = rbt.get_Parameter(BuiltInParameter.MATERIAL_NAME)
                if material_param and material_param.AsString():
                    grade = material_param.AsString()

                # Create display name with diameter and grade
                if grade:
                    display_name = "{} - {} ({})".format(name, diameter, grade)
                else:
                    display_name = "{} - {}".format(name, diameter)

                dict_rebar_types[display_name] = rbt

            except Exception as e:
                # Fallback for problematic types
                try:
                    fallback_name = getattr(rbt, 'Name', 'Unnamed')
                    dict_rebar_types[fallback_name] = rbt
                except:
                    continue

        if not dict_rebar_types:
            forms.alert("No valid Rebar Bar Types could be processed.", exitscript=exitscript)
            return None

        # Use select_from_dict (same pattern as EF-Tools)
        selected_rebar_type = select_from_dict(dict_rebar_types,
                                             title=title,
                                             label=label,
                                             button_name='Select',
                                             SelectMultiple=False)

        # VERIFY SOMETHING IS SELECTED
        if not selected_rebar_type and exitscript:
            forms.alert("No Rebar Bar Type was selected. Please try again.", exitscript=exitscript)

        return selected_rebar_type[0] if selected_rebar_type else None

    except Exception as e:
        forms.alert("Error selecting Rebar Bar Type: {}".format(str(e)), exitscript=exitscript)
        return None


def select_rebar_bar_types_multiple(given_uidoc=uidoc, exitscript=True, title="Select Rebar Bar Types",
                                   label="Choose Rebar Bar Types (Multiple)"):
    """
    Function to let user select multiple rebar bar types from available types.

    Args:
        given_uidoc: UIDocument to work with
        exitscript: Whether to exit if no selection made
        title: Dialog title
        label: Dialog label

    Returns:
        List of selected RebarBarType elements or empty list
    """
    doc = given_uidoc.Document

    try:
        # Get all RebarBarType elements
        all_rebar_types = FilteredElementCollector(doc).OfClass(RebarBarType).ToElements()

        if not all_rebar_types:
            forms.alert("No Rebar Bar Types found in the project.", exitscript=exitscript)
            return []

        # Create selection dictionary
        dict_rebar_types = {}
        for rbt in all_rebar_types:
            try:
                # Get name
                type_name_param = rbt.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                name = type_name_param.AsString() if type_name_param and type_name_param.AsString() else "Unnamed"

                # Get diameter
                diameter = "N/A"
                bar_diameter_param = rbt.get_Parameter(BuiltInParameter.REBAR_BAR_DIAMETER)
                if bar_diameter_param:
                    diameter_feet = bar_diameter_param.AsDouble()
                    diameter_mm = diameter_feet * 304.8
                    diameter = "{:.0f}mm".format(diameter_mm)

                display_name = "{} - {}".format(name, diameter)
                dict_rebar_types[display_name] = rbt

            except Exception as e:
                try:
                    fallback_name = getattr(rbt, 'Name', 'Unnamed')
                    dict_rebar_types[fallback_name] = rbt
                except:
                    continue

        if not dict_rebar_types:
            forms.alert("No valid Rebar Bar Types could be processed.", exitscript=exitscript)
            return []

        # Allow multiple selection
        selected_rebar_types = select_from_dict(dict_rebar_types,
                                              title=title,
                                              label=label,
                                              button_name='Select Types',
                                              SelectMultiple=True)

        if not selected_rebar_types and exitscript:
            forms.alert("No Rebar Bar Types were selected. Please try again.", exitscript=exitscript)

        return selected_rebar_types if selected_rebar_types else []

    except Exception as e:
        forms.alert("Error selecting Rebar Bar Types: {}".format(str(e)), exitscript=exitscript)
        return []


def select_rebar_bar_type_by_diameter_range(given_uidoc=uidoc, min_diameter=None, max_diameter=None,
                                           exitscript=True):
    """
    Select rebar bar type filtered by diameter range.

    Args:
        given_uidoc: UIDocument to work with
        min_diameter: Minimum diameter in mm (optional)
        max_diameter: Maximum diameter in mm (optional)
        exitscript: Whether to exit if no selection made

    Returns:
        Selected RebarBarType element or None
    """
    doc = given_uidoc.Document

    try:
        all_rebar_types = FilteredElementCollector(doc).OfClass(RebarBarType).ToElements()

        if not all_rebar_types:
            forms.alert("No Rebar Bar Types found in the project.", exitscript=exitscript)
            return None

        # Filter by diameter range
        filtered_types = {}
        for rbt in all_rebar_types:
            try:
                bar_diameter_param = rbt.get_Parameter(BuiltInParameter.REBAR_BAR_DIAMETER)
                if bar_diameter_param:
                    diameter_feet = bar_diameter_param.AsDouble()
                    diameter_mm = diameter_feet * 304.8

                    # Check if within range
                    in_range = True
                    if min_diameter is not None and diameter_mm < min_diameter:
                        in_range = False
                    if max_diameter is not None and diameter_mm > max_diameter:
                        in_range = False

                    if in_range:
                        # Get name
                        type_name_param = rbt.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                        name = type_name_param.AsString() if type_name_param and type_name_param.AsString() else "Unnamed"

                        display_name = "{} - {:.0f}mm".format(name, diameter_mm)
                        filtered_types[display_name] = rbt

            except:
                continue

        if not filtered_types:
            range_text = ""
            if min_diameter is not None and max_diameter is not None:
                range_text = "between {:.0f}mm and {:.0f}mm".format(min_diameter, max_diameter)
            elif min_diameter is not None:
                range_text = "larger than {:.0f}mm".format(min_diameter)
            elif max_diameter is not None:
                range_text = "smaller than {:.0f}mm".format(max_diameter)

            forms.alert("No Rebar Bar Types found {}".format(range_text), exitscript=exitscript)
            return None

        # Select from filtered types
        title = "Select Rebar Bar Type"
        if min_diameter is not None or max_diameter is not None:
            title += " (Filtered)"

        selected_rebar_type = select_from_dict(filtered_types,
                                             title=title,
                                             label="Choose Rebar Bar Type",
                                             button_name='Select',
                                             SelectMultiple=False)

        if not selected_rebar_type and exitscript:
            forms.alert("No Rebar Bar Type was selected. Please try again.", exitscript=exitscript)

        return selected_rebar_type[0] if selected_rebar_type else None

    except Exception as e:
        forms.alert("Error selecting Rebar Bar Type: {}".format(str(e)), exitscript=exitscript)
        return None


def get_preselected_rebar_bar_types(given_uidoc=uidoc):
    """
    Get RebarBarType elements that are currently selected in the UI.
    Useful for pre-selection support.

    Args:
        given_uidoc: UIDocument to work with

    Returns:
        List of selected RebarBarType elements
    """
    doc = given_uidoc.Document
    selection = given_uidoc.Selection

    try:
        selected_elements = [doc.GetElement(e_id) for e_id in selection.GetElementIds()]
        selected_rebar_types = [e for e in selected_elements if isinstance(e, RebarBarType)]
        return selected_rebar_types

    except Exception:
        return []


def pick_rebar_elements(given_uidoc=uidoc, exitscript=True):
    """
    Function to let user pick rebar elements (Rebar instances) from the model.
    Based on EF-Tools pick_by_class pattern.

    Args:
        given_uidoc: UIDocument to work with
        exitscript: Whether to exit if no selection made

    Returns:
        List of selected Rebar elements
    """
    from Autodesk.Revit.DB.Structure import Rebar

    try:
        selected_elems = []
        ISF = ISelectionFilter_Classes([Rebar])

        with forms.WarningBar(title='Select Rebar Elements and click "Finish"'):
            ref_selected_elems = selection.PickObjects(ObjectType.Element, ISF)
        selected_elems = [doc.GetElement(ref) for ref in ref_selected_elems]

    except:
        pass

    if not selected_elems and exitscript:
        error_msg = 'No Rebar elements were selected.\nPlease Try Again'
        forms.alert(error_msg, title='Rebar Selection has Failed.', exitscript=True)

    return selected_elems


# ╔═╗╔═╗╦  ╔═╗╔═╗╔╦╗
# ╚═╗║╣ ║  ║╣ ║   ║
# ╚═╝╚═╝╩═╝╚═╝╚═╝ ╩
#==================================================
# ISelectionFilter Classes (adapted from EF-Tools)
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> REBAR FILTER

class ISelectionFilter_RebarTypes(ISelectionFilter):
    """Filter user selection to RebarBarType elements."""
    def AllowElement(self, element):
        return isinstance(element, RebarBarType)


class ISelectionFilter_RebarElements(ISelectionFilter):
    """Filter user selection to Rebar elements (instances)."""
    def __init__(self, allowed_types=None):
        """Filter for Rebar elements with optional type filtering."""
        from Autodesk.Revit.DB.Structure import Rebar, RebarInSystem
        self.allowed_types = allowed_types or [Rebar, RebarInSystem]

    def AllowElement(self, element):
        return type(element) in self.allowed_types


# ╔═╗╦╔═╗╦╔═  ╔═╗╦  ╔═╗╔╦╗╔═╗╔╗╔╔╦╗╔═╗
# ╠═╝║║  ╠╩╗  ║╣ ║  ║╣ ║║║║╣ ║║║ ║ ╚═╗
# ╩  ╩╚═╝╩ ╩  ╚═╝╩═╝╚═╝╩ ╩╚═╝╝╚╝ ╩ ╚═╝
#==================================================

def pick_rebar_bar_type(given_uidoc=uidoc):
    """
    Function to prompt user to select a single RebarBarType element in Revit UI.
    Based on EF-Tools pick_wall pattern.

    Args:
        given_uidoc: UIDocument to work with

    Returns:
        Selected RebarBarType element
    """
    try:
        ref_rebar_type = given_uidoc.Selection.PickObject(ObjectType.Element,
                                                        ISelectionFilter_RebarTypes(),
                                                        "Select a Rebar Bar Type")
        rebar_type = given_uidoc.Document.GetElement(ref_rebar_type)
        return rebar_type
    except:
        return None


def pick_rebar_element(given_uidoc=uidoc):
    """
    Function to prompt user to select a single Rebar element in Revit UI.

    Args:
        given_uidoc: UIDocument to work with

    Returns:
        Selected Rebar element
    """
    try:
        ref_rebar = given_uidoc.Selection.PickObject(ObjectType.Element,
                                                   ISelectionFilter_RebarElements(),
                                                   "Select a Rebar Element")
        rebar = given_uidoc.Document.GetElement(ref_rebar)
        return rebar
    except:
        return None


# ╦  ╔═╗╔═╗╦  ╔═╗╔═╗╔╦╗╦╔═╗╔╗╔  ╔═╗╦╦ ╔╦╗╔═╗╦═╗
# ║  ╚═╗║╣ ║  ║╣ ║   ║ ║║ ║║║║  ╠╣ ║║  ║ ║╣ ╠╦╝
# ╩  ╚═╝╚═╝╩═╝╚═╝╚═╝ ╩ ╩╚═╝╝╚╝  ╚  ╩╩═╝╩ ╚═╝╩╚═
# Custom ISelectionFilter (adapted from EF-Tools)

class CustomISelectionFilter(ISelectionFilter):
    """Filter user selection to certain element types by category ID."""
    def __init__(self, category_id):
        self.category_id = str(category_id)

    def AllowElement(self, e):
        if str(e.Category.Id) == self.category_id:
            return True
        return False