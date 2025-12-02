# -*- coding: utf-8 -*-
# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#==================================================
import sys, clr

from Autodesk.Revit.DB import Transaction, BuiltInParameter
from pyrevit import forms

# CUSTOM IMPORTS (following ARCHITECTURE_GUIDE.md)
from Snippets._selection import get_selected_views

# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#==================================================
uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

# Get selected views using the library function
selected_views = get_selected_views(exit_if_none=False)

if not selected_views:
    forms.alert("No views were selected. Please select views first.", exitscript=True)

# Process views in transaction
with Transaction(doc, "Set View Title on Sheet") as t:
    t.Start()

    for view in selected_views:
        # Get the VIEW_DESCRIPTION parameter (Title on Sheet)
        title_param = view.get_Parameter(BuiltInParameter.VIEW_DESCRIPTION)

        if title_param and title_param.IsReadOnly == False:
            # Set the parameter value to the view name
            title_param.Set(view.Name)

    t.Commit()

# Success message
forms.toast(
    "Successfully updated 'Title on Sheet' for {} view(s)".format(len(selected_views)),
    title="Set View Title on Sheet",
    appid="PrasKaaPyKit"
)