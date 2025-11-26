# -*- coding: utf-8 -*-
"""
Join Columns - Join structural columns with nearby elements

This script joins selected structural columns with nearby beams, floors,
foundations, and walls, ensuring columns win in join order.

Usage:
- Select structural columns first, then run the tool
- If no columns selected, you'll be prompted to select them
- No output or feedback is provided - processing is silent
"""

__title__ = 'Join Columns'
__author__ = 'PrasKaa Team'

import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

# pyRevit imports
from pyrevit import revit

# Local lib imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'lib'))

from Snippets._selection import get_selected_elements, pick_by_category
from Snippets._context_manager import ef_Transaction
from join_utils import process_elements_with_join_logic
from join_columns import join_column_with_nearby_elements

# Setup
doc = revit.doc
uidoc = revit.uidoc

# Get selected elements (if any)
selected_elements = get_selected_elements(uidoc, exitscript=False)

# Filter for structural columns
selected_columns = []
if selected_elements:
    for elem in selected_elements:
        if (elem and elem.Category and
            elem.Category.Id.IntegerValue == int(BuiltInCategory.OST_StructuralColumns)):
            selected_columns.append(elem)

# If no columns selected, prompt user to select
if not selected_columns:
    selected_columns = pick_by_category([BuiltInCategory.OST_StructuralColumns], exit_if_none=False)

# Process columns if any were selected/provided
if selected_columns:
    # Process with standardized silent transaction
    with ef_Transaction(doc, "Join Columns", debug=False, exitscript=False):
        process_elements_with_join_logic(doc, selected_columns, join_column_with_nearby_elements)