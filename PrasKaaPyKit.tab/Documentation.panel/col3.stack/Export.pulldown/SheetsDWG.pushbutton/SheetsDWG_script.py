import sys
import os
# Add lib directory to path for imports
lib_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

# import pyrevit libraries
from pyrevit import forms,revit,DB,script
# print utility library
from expUtils import *

# Check for shift+click to open naming format editor
if __shiftclick__:  #pylint: disable=E0602
    # Add parent directory to path for importing EditNamingFormats
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    import EditNamingFormats
    xaml_path = os.path.join(os.path.dirname(__file__), '..', 'EditNamingFormats.xaml')
    EditNamingFormats.EditNamingFormatsWindow(xaml_path, caller_script='DWG').show_dialog()
    script.exit()

# make sure you can print, construct print path and make directory
expUtils_canPrint()
dirPath = expUtils_getDir() + "\\" + expUtils_getFolder("_DWG")
expUtils_ensureDir(dirPath)

# get document
doc = revit.doc
uidoc = revit.uidoc

# get naming format
naming_template = expUtils_getNamingFormat("{number} {name}")

# ask user for sheets
sheets = forms.select_sheets(title='Select Sheets', include_placeholder = False, use_selection = True)

# display primary UI if sheets found
if sheets:
	# open the directory
	expUtils_openDir(dirPath)
	# export sheets
	with forms.ProgressBar(step=1, title='Exporting sheets... ' + '{value} of {max_value}', cancellable=True) as pb1:
		pbTotal1 = len(sheets)
		pbCount1 = 1
		# Make print options
		opts = expUtils_dwgOpts()
		# Export each sheet selected by user
		for s in sheets:
			if pb1.cancelled:
				break
			else:
				# Export sheet to DWG
				expUtils_exportSheetDwg(dirPath,s,opts,doc,uidoc,naming_template)
				# Update progress bar
				pb1.update_progress(pbCount1, pbTotal1)
				pbCount1 += 1
	# Cancel check
	if pb1.cancelled:
		forms.alert("Export process cancelled.", title= "Script cancelled")
	else:
		forms.alert("Export process complete.", title= "Script finished", warn_icon=False)