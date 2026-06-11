# -*- coding: utf-8 -*-
__title__ = 'Print Set by Revision'
__author__ = 'PrasKaa Team'
__version__ = '1.0'
__doc__ = """Version: 1.0
Date    = 07.04.2026
_____________________________________________________________________
Description:
Creates a print sheet set from multiple selected revisions.

Allows selecting multiple revisions and creates a single sheet set
containing all sheets that have any of the selected revisions.
Sheets are deduplicated if they appear in multiple revisions.

How-to:
1. Click the tool button
2. Select one or more revisions from the list
3. The tool will create a sheet set with all sheets containing selected revisions
4. Sheet set is named "Multiple Revisions - [combined descriptions]"

Notes:
- Supports single or multiple revision selection
- Automatically deduplicates sheets across revisions
- Handles sheet set overwrite confirmation

_____________________________________________________
Last update:
- 07.04.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa Team
"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#==================================================
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSheet,
    ViewSheetSet,
    ViewSet,
    PrintRange
)

from pyrevit import revit, forms, script

# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#==================================================
doc = revit.doc

# ╔╦╗╔═╗╦╔╗╔
# ║║║║╣ ║║║║
# ╩ ╩╚═╝╩╝╚╝
#==================================================
def main():
    """Main function for creating print set from multiple revisions."""

    # Select multiple revisions
    selected_revisions = forms.select_revisions(
        title='Select Revisions',
        button_name='Create Print Set',
        width=500,
        multiple=True
    )

    # No revisions selected
    if not selected_revisions:
        forms.alert("No revisions selected.", title="Script cancelled")
        return

    # Get revision IDs for faster lookup
    selected_rev_ids = {rev.Id for rev in selected_revisions}

    # Get all sheets
    all_sheets = FilteredElementCollector(doc).OfClass(ViewSheet).WhereElementIsNotElementType().ToElements()

    # Find sheets that have any of the selected revisions
    rev_sheets = set()  # Use set to deduplicate

    for sheet in all_sheets:
        sheet_rev_ids = set(sheet.GetAllRevisionIds())
        if selected_rev_ids & sheet_rev_ids:  # Intersection check
            rev_sheets.add(sheet)

    # Convert back to list for ViewSet insertion
    rev_sheets = list(rev_sheets)

    # No sheets found
    if len(rev_sheets) == 0:
        forms.alert("No sheets found with selected revisions.", title="Script cancelled")
        return

    # Create combined description for naming
    descriptions = [rev.Description for rev in selected_revisions if rev.Description]
    if descriptions:
        combined_desc = ", ".join(descriptions)
        proposed_name = "Multiple Revisions - {}".format(combined_desc)
    else:
        # Fallback if no descriptions
        proposed_name = "Multiple Revisions ({} selected)".format(len(selected_revisions))

    # Get all sheet set names
    all_sheet_sets = FilteredElementCollector(doc).OfClass(ViewSheetSet).WhereElementIsNotElementType().ToElements()
    all_sheet_set_names = [s.Name for s in all_sheet_sets]

    # Check if exists, allow overwrite if so
    if proposed_name in all_sheet_set_names:
        check_delete = forms.alert(
            "Sheet set '{}' exists, overwrite?".format(proposed_name),
            title="Set exists",
            ok=False,
            cancel=False,
            yes=True,
            no=True
        )
        if check_delete:
            ind = all_sheet_set_names.index(proposed_name)
            del_sheet_set = all_sheet_sets[ind]
            try:
                with revit.Transaction('Delete sheet set for overwrite'):
                    doc.Delete(del_sheet_set.Id)
            except:
                forms.alert("Sheet set could not be overwritten.", title="Script cancelled")
                return
        else:
            return

    # Create new sheet set
    new_set = ViewSet()

    # Add sheets to sheet set
    for sheet in rev_sheets:
        new_set.Insert(sheet)

    # Configure print manager and sheet settings
    print_man = doc.PrintManager
    print_man.PrintRange = PrintRange.Select
    view_ss = print_man.ViewSheetSetting

    # Create the new sheet set
    with revit.Transaction('PrasKaa: Create Multi-Revision Print Set'):
        view_ss.CurrentViewSheetSet.Views = new_set
        view_ss.SaveAs(proposed_name)

    forms.alert(
        "New sheet set created: '{}'\nIncludes {} sheets from {} revisions.".format(
            proposed_name, len(rev_sheets), len(selected_revisions)
        ),
        title="Script completed",
        warn_icon=False
    )

if __name__ == '__main__':
    main()