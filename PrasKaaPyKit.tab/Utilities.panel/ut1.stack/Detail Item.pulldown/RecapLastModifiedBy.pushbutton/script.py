# -*- coding: utf-8 -*-
'''
Version: 1.0
Date    = 04.03.2026
_____________________________________________________________________
Description:
Recaps LastModifiedBy parameter values for structural and architectural elements.
Displays results in a table with Element ID and LastModifiedBy value.
_____________________________________________________________________
How-to:
1. Click "Recap LastModifiedBy"
2. Tool will analyze all structural and architectural elements
3. Results displayed in output window as table

Notes:
- Processes: Structural Framing, Columns, Foundations, Walls, Floors, Stairs
- Clickable Element IDs in the output table

_____________________________________________________
Last update:
- 04.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa
'''

__title__ = 'Recap LastModifiedBy'
__author__ = 'PrasKaa'
__version__ = '1.0'

from pyrevit import revit, DB
from Autodesk.Revit.DB import BuiltInCategory

# Categories to process
CATEGORIES = [
    BuiltInCategory.OST_StructuralFraming,
    BuiltInCategory.OST_StructuralColumns,
    BuiltInCategory.OST_StructuralFoundation,
    BuiltInCategory.OST_Walls,
    BuiltInCategory.OST_Floors,
    BuiltInCategory.OST_Stairs
]

doc = revit.doc
output = revit.output

def get_lastmodifiedby(element):
    """Get LastModifiedBy value from element parameter."""
    try:
        param = element.LookupParameter('LastModifiedBy')
        if param and param.HasValue:
            return param.AsString()
        return None
    except Exception as e:
        return None

def main():
    """Main function."""
    all_data = []
    
    for category in CATEGORIES:
        # Collect elements
        elements = DB.FilteredElementCollector(doc)\
            .OfCategory(category)\
            .WhereElementIsNotElementType()\
            .ToElements()
        
        for elem in elements:
            last_modified = get_lastmodifiedby(elem)
            if last_modified:
                all_data.append([
                    output.linkify(elem.Id),
                    last_modified
                ])
    
    # Print results
    if all_data:
        output.print_table(
            table_data=all_data,
            title="LastModifiedBy Summary ({} elements)".format(len(all_data)),
            columns=["Element ID", "LastModifiedBy"]
        )
    else:
        output.log_warning("No elements with LastModifiedBy found")

if __name__ == '__main__':
    main()
