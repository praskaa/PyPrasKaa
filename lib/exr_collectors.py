# -*- coding: utf-8 -*-
"""
EXR shared collectors and geometry option builders.
"""

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    RevitLinkInstance,
    View,
    ViewType,
)

from pyrevit import forms


def select_linked_model(doc):
    """Prompts user to select a linked model. Returns (link_doc, link_instance)."""
    links = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()
    if not links:
        forms.alert("No Revit links found in the current project.", exitscript=True)
    link_dict = {l.Name: l for l in links}
    name = forms.SelectFromList.show(
        sorted(link_dict.keys()),
        title='Select Source Linked EXR Model (from ETABS)',
        button_name='Select Link',
        multiselect=False
    )
    link = link_dict.get(name) if name else None
    if not link:
        forms.alert("No link selected.", exitscript=True)
    link_doc = link.GetLinkDocument()
    if not link_doc:
        forms.alert("Could not access the linked document. Ensure it is loaded.",
                    exitscript=True)
    return link_doc, link


def build_geometry_options(doc):
    """Centralizes NewGeometryOptions + View fallback (fixes module-level geo_opts bug)."""
    app = doc.Application
    geo_opts = app.Create.NewGeometryOptions()
    if doc.ActiveView:
        geo_opts.View = doc.ActiveView
    else:
        for v in FilteredElementCollector(doc).OfClass(View):
            if not v.IsTemplate and v.ViewType == ViewType.ThreeD:
                geo_opts.View = v
                break
    return geo_opts
