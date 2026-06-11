# -*- coding: utf-8 -*-
__title__ = "Create Sheet from CSV Template"
__author__ = "PrasKaa"
__version__ = 'Version: 1.1'
__doc__ =""" Version: 1.1
Date    = 09.03.2026
_____________________________________________________________________
Description:
Creates sheets in the project from a CSV file. The CSV should contain
sheet numbers and names in the first two columns.
_____________________________________________________________________
How-to:
1. Click "Sheets from CSV"
2. Select the CSV file containing sheet data
3. Select a titleblock for the new sheets
4. Sheets will be created based on CSV data

Notes:
- If sheet number already exists, sheet is still created but with
  "*" appended as suffix to the sheet number
- If sheet number with "*" already exists, adds another "*" (e.g. "**")
- Uses progress bar with cancel option

_____________________________________________________
Last update:
- 09.03.2026 - 1.1 Duplicate sheet number handling with suffix "*"
- 04.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa
"""
# Import libraries
import os
from pyrevit import revit, DB, script, forms

# Store current document into variable
doc = revit.doc


def get_unique_sheet_number(base_number, existing_numbers):
    """
    Returns a unique sheet number by appending '*' suffixes
    until a non-existing number is found.
    
    Example:
        "A101"     exists → try "A101*"
        "A101*"    exists → try "A101**"
        "A101**" doesn't exist → return "A101**"
    """
    candidate = base_number
    while candidate in existing_numbers:
        candidate = candidate + "*"
    return candidate


def createSheet(number, name, titleBlockId, existing_numbers):
    """
    Creates a sheet. If the sheet number already exists,
    appends '*' suffixes until the number is unique.
    Returns a tuple: (sheets_created, was_renamed)
    """
    final_number = get_unique_sheet_number(number, existing_numbers)
    was_renamed = (final_number != number)

    sheet = DB.ViewSheet.Create(doc, titleBlockId)
    sheet.SheetNumber = final_number
    sheet.Name = name

    # Add newly created number to existing set to prevent
    # collisions within the same CSV batch
    existing_numbers.add(final_number)

    return final_number, was_renamed


# Prompt user to specify file path
pathFile = forms.pick_file(files_filter='CSV Files (*.csv)|*.csv')

# Catch if no file selected
if not pathFile:
    script.exit()

# Prompt user to select titleblock
titleBlock = forms.select_titleblocks(doc=doc)

# Catch if no titleblock selected
if not titleBlock:
    script.exit()

# Import CSV utilities
from csv_utils import csvUtils
csv_reader = csvUtils([], pathFile)
dat = csv_reader.csvUtils_import("Sheet1", 2, 0)

# Try to get column data
if dat[1]:
    sheetNumbers, sheetNames = [], []
    for row in dat[0][1:]:
        sheetNumbers.append(row[0])
        sheetNames.append(row[1])
else:
    forms.alert(
        "Data not found. Make sure CSV file is valid and accessible.",
        title="Script cancelled"
    )
    script.exit()

# Get all existing sheet numbers in document (use a set for fast lookup)
sheets = (
    DB.FilteredElementCollector(revit.doc)
    .OfCategory(DB.BuiltInCategory.OST_Sheets)
    .WhereElementIsNotElementType()
    .ToElements()
)
existingSheetNums = set(n.SheetNumber for n in sheets)

# Tracking
renamedSheets = []   # list of (original_number, final_number, name)
createdCount  = 0

# Create sheets
with forms.ProgressBar(step=1, title="Creating sheets", cancellable=True) as pb:
    pbCount = 1
    pbTotal = len(sheetNumbers)

    with revit.Transaction('guRoo: Create sheets'):
        for sNumb, sNam in zip(sheetNumbers, sheetNames):
            if pb.cancelled:
                break

            final_number, was_renamed = createSheet(
                sNumb, sNam, titleBlock, existingSheetNums
            )

            createdCount += 1
            if was_renamed:
                renamedSheets.append((sNumb, final_number, sNam))

            pb.update_progress(pbCount, pbTotal)
            pbCount += 1

# Build result message
if pb.cancelled:
    extra_msg = "\n\nScript cancelled partway through run."
    warn_icon  = False
else:
    extra_msg = ""
    warn_icon  = False

# Append renamed sheet info if any
if renamedSheets:
    warn_icon = True
    extra_msg += "\n\n{} sheet(s) had duplicate numbers and were renamed:\n".format(len(renamedSheets))
    for orig, final, name in renamedSheets:
        extra_msg += "  - '{}' -> '{}'\n     {}\n".format(orig, final, name)

form_message = "{}/{} sheets created.{}".format(createdCount, pbTotal, extra_msg)
forms.alert(form_message, title="Script complete", warn_icon=warn_icon)