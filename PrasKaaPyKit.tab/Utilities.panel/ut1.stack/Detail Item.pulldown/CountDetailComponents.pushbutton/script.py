# -*- coding: utf-8 -*-
'''
Version: 1.0
Date    = 04.03.2026
_____________________________________________________________________
Description:
Counts selected Detail Components (OST_DetailComponents) in the active view
and displays the count in the output window.
_____________________________________________________________________
How-to:
1. Click "Count Detail Components"
2. Select Detail Components in the view
3. Count will be displayed in output window

Notes:
- Counts only Detail Components (not other element types)
- Works with currently selected elements

_____________________________________________________
Last update:
- 04.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa
'''

__title__ = 'Count Detail Components'
__author__ = 'PrasKaa Team'
__version__ = '1.0'

from pyrevit import revit, DB, script
from Autodesk.Revit.DB import BuiltInCategory, Category

# Get output
output = script.get_output()

# Get Detail Components category
detail_cat = Category.GetCategory(revit.doc, BuiltInCategory.OST_DetailComponents)

# Get selection
uidoc = revit.uidoc
selection_ids = uidoc.Selection.GetElementIds()

# Check if anything is selected
if not selection_ids:
    output.log_warning('No elements selected :warning:')
else:
    # Filter for Detail Components
    detail_components = []
    for elem_id in selection_ids:
        elem = revit.doc.GetElement(elem_id)
        if elem.Category and elem.Category.Id == detail_cat.Id:
            detail_components.append(elem)
    
    # Display result
    count = len(detail_components)
    
    if count > 0:
        output.log_success('{} Detail Component(s) selected :white_check_mark:'.format(count))
    else:
        output.log_warning('No Detail Components in selection :warning:')
