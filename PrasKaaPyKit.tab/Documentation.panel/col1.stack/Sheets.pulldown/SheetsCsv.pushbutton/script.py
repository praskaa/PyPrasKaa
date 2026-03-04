# -*- coding: utf-8 -*-
'''
Version: 1.0
Date    = 04.03.2026
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
- Skips sheets if number already exists in project
- Uses progress bar with cancel option

_____________________________________________________
Last update:
- 04.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa
'''

# Import libraries
import os
from pyrevit import revit, DB, script, forms

# Store current document into variable
doc = revit.doc

# Function to create sheets
def createSheet(number, name, titleBlockId):
	sheet = DB.ViewSheet.Create(doc, titleBlockId)
	sheet.SheetNumber = number
	sheet.Name = name
	return 1

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

csv_reader = csvUtils([],pathFile)
dat = csv_reader.csvUtils_import("Sheet1",2,0)

# Try to get column data
if dat[1]:
	sheetNumbers, sheetNames, sheetSeries, sheetSets = [],[],[],[]
	for row in dat[0][1:]:
		sheetNumbers.append(row[0])
		sheetNames.append(row[1])
else:
	forms.alert("Data not found. Make sure CSV file is valid and accessible.", title= "Script cancelled")
	script.exit()

# get all sheets in document
sheets = DB.FilteredElementCollector(revit.doc).OfCategory(DB.BuiltInCategory.OST_Sheets).WhereElementIsNotElementType().ToElements()
sheetnums = [n.SheetNumber for n in sheets]

# Create sheets
with forms.ProgressBar(step=1, title="Creating sheets", cancellable=True) as pb:
	# Create progress bar
	pbCount = 1
	pbTotal = len(sheetNumbers)
	passCount = 0
	# Start transaction
	with revit.Transaction('guRoo: Create sheets'):
		# Make sheets
		for sNumb, sNam in zip(sheetNumbers, sheetNames):
			if pb.cancelled:
				break
			if sNumb not in sheetnums:
				passCount += createSheet(sNumb, sNam, titleBlock)
			# Update progress bar
			pb.update_progress(pbCount, pbTotal)
			pbCount += 1

# Process the outcome
if pb.cancelled:
	extraMsg = "\n\n" + "Script cancelled partway through run."
	warnIcon = False
elif passCount != pbTotal:
	extraMsg = "\n\n" + "Skipped sheets typically are caused by sheet numbers already existing in the model."
	warnIcon = True
else:
	extraMsg = ""
	warnIcon = False

# Display the outcome
form_message = str(passCount) + "/" + str(pbTotal) + " sheets created." + extraMsg
forms.alert(form_message, title= "Script complete", warn_icon=warnIcon)