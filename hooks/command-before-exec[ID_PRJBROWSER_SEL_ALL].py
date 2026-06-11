# -*- coding: utf-8 -*-
"""
command-before-exec[ID_PRJBROWSER_SEL_ALL].py
"""
from pyrevit import forms

forms.alert(
    "Selecting ALL instances of this type in the Entire Project.",
    title="Select All Instances - Entire Project",
    warn_icon=True,
)