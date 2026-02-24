"""
Count Detail Components
Counts selected Detail Components (OST_DetailComponents) in the active view.

Author: PrasKaa
Version: 1.0.0
Last Updated: 2026-02-20

Changelog:
    v1.0.0 (2026-02-20): Initial release
"""

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
