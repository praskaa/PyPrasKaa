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
    EditNamingFormats.EditNamingFormatsWindow(xaml_path, caller_script='PDF').show_dialog()
    script.exit()

# make sure you can print, construct print path and make directory
expUtils_canPrint()
dirPath = expUtils_getDir() + "\\" + expUtils_getFolder("_PDF")
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
    # Check if single sheet selected
    is_single_sheet = len(sheets) == 1
    
    if is_single_sheet:
        # Single sheet - auto export directly (Individual PDF mode)
        # Skip export choice dialog for single sheet
        
        # Get sheet info for feedback
        sheet_info = "Sheet: {} - {}".format(sheets[0].SheetNumber, sheets[0].Name)
        
        # open the directory
        expUtils_openDir(dirPath)

        _original_printer = expUtils_applyPrinter(doc)

        with forms.ProgressBar(title='Exporting sheet...', cancellable=True) as pb1:
            # Make print options
            opts = expUtils_pdfOpts()
            
            # Export the single sheet
            expUtils_exportSheetPdf(dirPath, sheets[0], opts, doc, uidoc, naming_template)
        
        expUtils_restorePrinter(doc, _original_printer)
        
        # Show completion message
        if pb1.cancelled:
            forms.alert("Export process cancelled.", title= "Script cancelled")
        else:
            forms.alert("Export complete.\n\n{}".format(sheet_info), title= "Script finished", warn_icon=False)
    
    else:
        # Multiple sheets - show export choice dialog (existing behavior)
        # Ask user for sheets
        export_choice = forms.CommandSwitchWindow.show(
            ['Individual PDFs (default)', 'Single Multi-Sheet PDF'],
            message='Select PDF export method:',
            title='PDF Export Options'
        )
        
        # Handle user cancellation
        if not export_choice:
            script.exit()
        
        # Determine if multi-sheet export requested
        multi_sheet = export_choice == 'Single Multi-Sheet PDF'
        
        if multi_sheet:
            # Multi-sheet export mode
            # ask for filename
            fileName = forms.ask_for_string(
                default="MultiSheet_Export",
                prompt="Enter a name for the combined PDF file",
                title="Combined PDF Filename"
            )

            if not fileName:
                script.exit()
            
            # open the directory
            expUtils_openDir(dirPath)

            with forms.ProgressBar(title='Exporting multi-sheet PDF...', cancellable=True) as pb1:
                # Make print options
                opts = expUtils_pdfOpts()
                opts.FileName = fileName
                
                # Prepare ElementId collection for all selected sheets
                from System.Collections.Generic import List
                exportSheets = List[DB.ElementId]()
                
                # Sort sheets by sheet number (ascending) before exporting
                sorted_sheets = sorted(sheets, key=lambda s: s.SheetNumber)
                
                # Add all sheet IDs to collection in sorted order
                for s in sorted_sheets:
                    exportSheets.Add(s.Id)
                
                # Export all sheets as single PDF
                doc.Export(dirPath, exportSheets, opts)
                
            # Cancel check
            if pb1.cancelled:
                forms.alert("Export process cancelled.", title= "Script cancelled")
            else:
                forms.alert("Multi-sheet PDF export complete.", title= "Script finished", warn_icon=False)
        
        else:
            # Individual PDF export mode (existing behavior)
            with forms.ProgressBar(step=1, title='Exporting sheets... ' + '{value} of {max_value}', cancellable=True) as pb1:
                pbTotal1 = len(sheets)
                pbCount1 = 1
                # Make print options
                _original_printer = expUtils_applyPrinter(doc)
                opts = expUtils_pdfOpts()
                # Export each sheet selected by user
                for s in sheets:
                    if pb1.cancelled:
                        break
                    else:
                        # Export sheet to PDF
                        expUtils_exportSheetPdf(dirPath,s,opts,doc,uidoc,naming_template)
                        # Update progress bar
                        pb1.update_progress(pbCount1, pbTotal1)
                        pbCount1 += 1
            expUtils_restorePrinter(doc, _original_printer)
            # Cancel check
            if pb1.cancelled:
                forms.alert("Export process cancelled.", title= "Script cancelled")
            else:
                forms.alert("Export process complete.", title= "Script finished", warn_icon=False)
