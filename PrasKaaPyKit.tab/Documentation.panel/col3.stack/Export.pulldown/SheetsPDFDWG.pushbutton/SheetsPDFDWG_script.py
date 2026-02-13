"""
Exports selected sheets to both PDF and DWG simultaneously.

CONTEXT: PyRevit UI tool - only run from Revit interface

This script uses the same configuration functions as individual PDF and DWG exports:
- expUtils_pdfOpts() - PDF export options (shared with SheetsPDF)
- expUtils_dwgOpts() - DWG export options (shared with SheetsDWG)
- expUtils_getNamingFormat() - naming format (shared with both)

Any changes to these functions will automatically apply to this script as well.
"""

# pyRevit imports
from pyrevit import forms, revit, DB, script

# Local lib imports - explicit imports as per project standards
from expUtils import (
    expUtils_canPrint,
    expUtils_getDir,
    expUtils_getFolder,
    expUtils_ensureDir,
    expUtils_openDir,
    expUtils_getNamingFormat,
    expUtils_pdfOpts,
    expUtils_dwgOpts,
    expUtils_exportSheetPdf,
    expUtils_exportSheetDwg
)

# Check for shift+click to open naming format editor
if __shiftclick__:
    # Add parent directory to path for importing EditNamingFormats
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    import EditNamingFormats
    xaml_path = os.path.join(os.path.dirname(__file__), '..', 'EditNamingFormats.xaml')
    EditNamingFormats.EditNamingFormatsWindow(xaml_path, caller_script='PDFDWG').show_dialog()
    script.exit()

# Make sure you can print, construct print path and make directory
expUtils_canPrint()

# Get document
doc = revit.doc
uidoc = revit.uidoc

# Get naming format (shared with PDF and DWG scripts)
naming_template = expUtils_getNamingFormat("{number} {name}")

# Ask user for sheets
sheets = forms.select_sheets(title='Select Sheets', include_placeholder=False, use_selection=True)

# Display primary UI if sheets found
if sheets:
    # Show export choice to user
    export_choice = forms.CommandSwitchWindow.show(
        ['Individual PDFs + DWGs (default)', 'Combined Multi-Sheet PDF + Individual DWGs'],
        message='Select export method:',
        title='PDF + DWG Export Options'
    )
    
    # Handle user cancellation
    if not export_choice:
        script.exit()
    
    # Determine export mode
    multi_sheet_mode = export_choice == 'Combined Multi-Sheet PDF + Individual DWGs'
    
    # Create export options (shared with individual scripts)
    pdf_opts = expUtils_pdfOpts()
    dwg_opts = expUtils_dwgOpts()
    
    if multi_sheet_mode:
        # Combined multi-sheet PDF + Individual DWGs export
        # Ask for PDF filename
        pdf_filename = forms.ask_for_string(
            default="Combined_Export",
            prompt="Enter a name for the combined PDF file",
            title="Combined PDF Filename"
        )
        
        if not pdf_filename:
            script.exit()
        
        # Get directory path for PDF
        pdf_dir = expUtils_getDir() + "\\" + expUtils_getFolder("_PDF")
        dwg_dir = expUtils_getDir() + "\\" + expUtils_getFolder("_DWG")
        
        expUtils_ensureDir(pdf_dir)
        expUtils_ensureDir(dwg_dir)
        
        # Open directories
        expUtils_openDir(pdf_dir)
        expUtils_openDir(dwg_dir)
        
        with forms.ProgressBar(title='Exporting combined PDF and DWGs...', cancellable=True) as pb:
            # Prepare ElementId collection for PDF
            from System.Collections.Generic import List
            export_sheets = List[DB.ElementId]()
            
            # Sort sheets by sheet number
            sorted_sheets = sorted(sheets, key=lambda s: s.SheetNumber)
            
            # Add all sheet IDs to collection
            for s in sorted_sheets:
                export_sheets.Add(s.Id)
            
            # Export combined PDF
            pdf_opts.FileName = pdf_filename
            doc.Export(pdf_dir, export_sheets, pdf_opts)
            
            # Export each sheet to DWG individually
            dwg_count = 0
            for s in sorted_sheets:
                if pb.cancelled:
                    break
                expUtils_exportSheetDwg(dwg_dir, s, dwg_opts, doc, uidoc, naming_template)
                dwg_count += 1
            
        if pb.cancelled:
            forms.alert("Export process cancelled.", title="Script cancelled")
        else:
            forms.alert("Export complete.\n\nPDF: {}\nDWGs: {}".format(pdf_filename, dwg_count), 
                       title="Script finished", warn_icon=False)
    
    else:
        # Individual PDF + DWG export for each sheet
        # Create subfolders for PDF and DWG
        pdf_dir = expUtils_getDir() + "\\" + expUtils_getFolder("_PDF")
        dwg_dir = expUtils_getDir() + "\\" + expUtils_getFolder("_DWG")
        
        expUtils_ensureDir(pdf_dir)
        expUtils_ensureDir(dwg_dir)
        
        # Open directories
        expUtils_openDir(pdf_dir)
        expUtils_openDir(dwg_dir)
        
        # Export sheets
        with forms.ProgressBar(step=1, title='Exporting sheets... ' + '{value} of {max_value}', cancellable=True) as pb:
            pb_total = len(sheets)
            pb_count = 1
            
            for s in sheets:
                if pb.cancelled:
                    break
                else:
                    # Export to PDF (using same function as SheetsPDF)
                    expUtils_exportSheetPdf(pdf_dir, s, pdf_opts, doc, uidoc, naming_template)
                    # Export to DWG (using same function as SheetsDWG)
                    expUtils_exportSheetDwg(dwg_dir, s, dwg_opts, doc, uidoc, naming_template)
                    # Update progress bar
                    pb.update_progress(pb_count, pb_total)
                    pb_count += 1
        
        if pb.cancelled:
            forms.alert("Export process cancelled.", title="Script cancelled")
        else:
            forms.alert("Export process complete.\n\nPDF folder: {}\nDWG folder: {}".format(pdf_dir, dwg_dir), 
                       title="Script finished", warn_icon=False)
