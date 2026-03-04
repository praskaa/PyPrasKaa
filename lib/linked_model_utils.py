# -*- coding: utf-8 -*-
"""
Linked Model Utilities Library - Shared utilities for linked Revit models

This module provides shared functions for working with linked Revit models,
particularly for EXR (ETABS export) workflows.

Usage:
    from lib.linked_model_utils import select_linked_model, get_linked_beams, get_linked_columns

Dependencies:
    - pyRevit (revit, forms)
    - Autodesk.Revit.DB (FilteredElementCollector, RevitLinkInstance, etc.)
"""

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    RevitLinkInstance,
    BuiltInCategory,
    ElementId
)
from pyrevit import revit, forms


def select_linked_model(document, title='Select Source Linked Model', button_name='Select Link'):
    """
    Prompts the user to select a linked model from available Revit links.
    
    Args:
        document: Revit Document
        title: Dialog title (default: 'Select Source Linked Model')
        button_name: Button label (default: 'Select Link')
    
    Returns:
        tuple: (link_doc, selected_link)
            - link_doc: The Document object of the selected linked model
            - selected_link: The RevitLinkInstance object of the selected link
    
    Raises:
        SystemExit: If no links are found or no link is selected
    """
    doc = document
    
    link_instances = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()
    
    if not link_instances:
        forms.alert("No Revit links found in the current project.", exitscript=True)
    
    # Create a dictionary of link instances for selection
    link_dict = {link.Name: link for link in link_instances}
    
    selected_link_name = forms.SelectFromList.show(
        sorted(link_dict.keys()),
        title=title,
        button_name=button_name,
        multiselect=False
    )
    
    if not selected_link_name:
        forms.alert("No link selected. Script will exit.", exitscript=True)
    
    selected_link = link_dict.get(selected_link_name)
    
    if not selected_link:
        forms.alert("No link selected. Script will exit.", exitscript=True)
    
    link_doc = selected_link.GetLinkDocument()
    
    if not link_doc:
        forms.alert("Could not access the document of the selected link. Ensure it is loaded.", exitscript=True)
    
    return link_doc, selected_link


def get_linked_beams(link_doc):
    """
    Collects structural framing elements from the linked model.
    
    Args:
        link_doc: The document object of the linked Revit model
    
    Returns:
        list: List of structural framing elements from the linked model
    """
    return list(
        FilteredElementCollector(link_doc)
        .OfCategory(BuiltInCategory.OST_StructuralFraming)
        .WhereElementIsNotElementType()
        .ToElements()
    )


def get_linked_columns(link_doc):
    """
    Collects structural column elements from the linked model.
    
    Args:
        link_doc: The document object of the linked Revit model
    
    Returns:
        list: List of structural column elements from the linked model
    """
    return list(
        FilteredElementCollector(link_doc)
        .OfCategory(BuiltInCategory.OST_StructuralColumns)
        .WhereElementIsNotElementType()
        .ToElements()
    )


def validate_linked_model(link_doc):
    """
    Validates that a linked model is accessible and contains structural elements.
    
    Args:
        link_doc: The document object of the linked Revit model
    
    Returns:
        tuple: (is_valid, message, stats)
            - is_valid: Boolean indicating if the link is valid
            - message: Status message
            - stats: Dictionary with element counts
    """
    if not link_doc:
        return False, "Linked document is None", {}
    
    stats = {}
    
    # Count structural framing
    framing_count = 0
    try:
        framing = FilteredElementCollector(link_doc)\
            .OfCategory(BuiltInCategory.OST_StructuralFraming)\
            .WhereElementIsNotElementType()\
            .ToElements()
        framing_count = len(framing)
        stats['framing'] = framing_count
    except Exception:
        # Linked model may be unloaded or inaccessible
        stats['framing'] = 0
    
    # Count structural columns
    columns_count = 0
    try:
        columns = FilteredElementCollector(link_doc)\
            .OfCategory(BuiltInCategory.OST_StructuralColumns)\
            .WhereElementIsNotElementType()\
            .ToElements()
        columns_count = len(columns)
        stats['columns'] = columns_count
    except Exception:
        # Linked model may be unloaded or inaccessible
        stats['columns'] = 0
    
    if framing_count == 0 and columns_count == 0:
        return False, "No structural framing or columns found in linked model", stats
    
    message = "Found {} framing elements, {} columns".format(framing_count, columns_count)
    return True, message, stats


def get_all_link_instances(document):
    """
    Gets all linked model instances in the document.
    
    Args:
        document: Revit Document
    
    Returns:
        list: List of RevitLinkInstance elements
    """
    return FilteredElementCollector(document).OfClass(RevitLinkInstance).ToElements()


def get_link_by_name(document, link_name):
    """
    Gets a specific linked model by name.
    
    Args:
        document: Revit Document
        link_name: Name of the linked model to find
    
    Returns:
        RevitLinkInstance or None
    """
    links = get_all_link_instances(document)
    for link in links:
        if link.Name == link_name:
            return link
    return None
