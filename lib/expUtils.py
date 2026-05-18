# -*- coding: utf-8 -*-
# Prepare for utilities
from pyrevit import revit,DB,forms,script
from System.Collections.Generic import List
from System.Drawing.Printing import PrinterSettings
import System
import subprocess
import os, datetime, re
from strUtils import *

# Debug toggle - set to True for verbose debug output during development/troubleshooting
# When True, detailed debug information will be printed to console during export operations
DEBUG_MODE = False

# ──────────────────────────────────────────────
# PRINTER CONFIGURATION UTILITIES
# ──────────────────────────────────────────────
from System.Drawing.Printing import PrinterSettings
import subprocess

def expUtils_getAvailablePrinters():
    """Return list of printer names available on this system"""
    try:
        return [p for p in PrinterSettings.InstalledPrinters]
    except Exception as e:
        debug_print("Error getting printers:", str(e))
        return []

def expUtils_getSavedPrinter(default=None):
    """Get the saved printer name from shared config"""
    try:
        config = script.get_config(section='shared_naming')
        saved = config.get_option('selected_printer', None)
        debug_print("Saved printer:", saved)
        return saved if saved else default
    except Exception as e:
        debug_print("Error getting saved printer:", str(e))
        return default

def expUtils_savePrinter(printer_name):
    """Save selected printer name to shared config"""
    try:
        config = script.get_config(section='shared_naming')
        config.set_option('selected_printer', printer_name)
        script.save_config()
        return True
    except Exception as e:
        debug_print("Error saving printer:", str(e))
        return False

def expUtils_applyPrinter(doc):
    printer_name = expUtils_getSavedPrinter()

    if not printer_name:
        print(">>> No saved printer found!")
        return None
    try:
        print_mgr = doc.PrintManager
        original_printer = print_mgr.PrinterName
        print_mgr.SelectNewPrintDriver(printer_name)
        return original_printer
    except Exception as e:
        print(">>> ERROR applying printer: {}".format(str(e)))
        return None

def expUtils_restorePrinter(doc, original_printer_name):
    """Restore PrintManager ke printer semula setelah export"""
    if not original_printer_name:
        return
    try:
        print_mgr = doc.PrintManager
        print_mgr.SelectNewPrintDriver(original_printer_name)
        debug_print("Restored printer to:", original_printer_name)
    except Exception as e:
        debug_print("Error restoring printer:", str(e))

def debug_print(*args):
    """Print debug information if DEBUG_MODE is enabled"""
    if DEBUG_MODE:
        # IronPython compatible debug print
        msg = "DEBUG: " + " ".join(str(arg) for arg in args)
        print(msg)

# Get export naming format from config
def expUtils_getNamingFormat(default_template="{number} {name}"):
	"""Get the selected naming format from shared config"""
	try:
		config = script.get_config(section='shared_naming')
		naming_formats = config.get_option('namingformats', {})
		try:
			selected_format = config.get_option('selected_export_format', None)
		except:
			selected_format = None

		debug_print("Available formats:", list(naming_formats.keys()) if naming_formats else "None")
		debug_print("Selected format:", selected_format)

		if selected_format and selected_format in naming_formats:
			template = naming_formats[selected_format]
			# Strip any extensions that might have been saved in the template
			if template.lower().endswith('.pdf'):
				template = template[:-4]
			elif template.lower().endswith('.dwg'):
				template = template[:-4]
			debug_print("Using custom template (cleaned):", template)
			return template
		else:
			# Return default format
			debug_print("Using default template:", default_template)
			return default_template
	except Exception as e:
		debug_print("Error getting naming format:", str(e))
		return default_template

# get print directory
def expUtils_getDir():
	dp = os.path.join(os.path.expanduser("~"), "Documents", "PrasKaa Exports")
	return dp

# make subfolder extension
def expUtils_getFolder(task = "_PDF"):
	dateStamp = datetime.datetime.today().strftime("%y%m%d")
	timeStamp = datetime.datetime.today().strftime("%H%M%S")
	return dateStamp + "_" + timeStamp + task

# make directory if it doesn't exist
def expUtils_ensureDir(dp):
	if not os.path.exists(dp):
		os.makedirs(dp)
	return dp

# open the directory
def expUtils_openDir(dp):
	try:
		os.startfile(dp)
	except:
		pass
	return dp

# function for checking version
def expUtils_canPrint():
	app = __revit__.Application
	rvt_year = int(app.VersionNumber)
	# Check that version is 2022 or higher
	if rvt_year < 2022:
		forms.alert("Only available in Revit 2022 or later.", title= "Script cancelled")
		script.exit()
	else:
		return True

# Helper function to get parameter value from element
def expUtils_getParamValue(param):
	"""Get parameter value, handling different parameter types"""
	if not param:
		return ""
	try:
		if param.StorageType == DB.StorageType.String:
			return param.AsString() or ""
		elif param.StorageType == DB.StorageType.Integer:
			return str(param.AsInteger())
		elif param.StorageType == DB.StorageType.Double:
			return str(param.AsDouble())
		elif param.StorageType == DB.StorageType.ElementId:
			return str(param.AsElementId().IntegerValue)
		else:
			return param.AsValueString() or ""
	except:
		return ""

# Helper function to find titleblock on sheet
def expUtils_getTitleBlock(sheet, doc):
	"""Find the titleblock family instance on the given sheet"""
	try:
		# Get all titleblocks in the document
		titleblocks = DB.FilteredElementCollector(doc)\
			.OfCategory(DB.BuiltInCategory.OST_TitleBlocks)\
			.WhereElementIsNotElementType()\
			.ToElements()

		# Find titleblock on this sheet
		for tblock in titleblocks:
			if tblock.OwnerViewId == sheet.Id:
				return tblock
	except:
		pass
	return None

# Function to update filename template with custom parameters
def expUtils_updateFilenameTemplate(template, value_type, value_getter):
	"""Update template by replacing parameter patterns with actual values"""
	finder_pattern = r'{' + value_type + r':(.*?)}'
	for param_name in re.findall(finder_pattern, template):
		param_value = value_getter(param_name)
		repl_pattern = r'{' + value_type + ':' + param_name + r'}'
		if param_value:
			template = re.sub(repl_pattern, str(param_value), template)
		else:
			template = re.sub(repl_pattern, '', template)
	return template

# make sheet name for print
def expUtils_nameSheet(s, template=None, doc=None):
	# Get revision number
	try:
		curRevId = s.GetCurrentRevision()
		if doc and curRevId:
			curRev = doc.GetElement(curRevId)
			curNum = s.GetRevisionNumberOnSheet(curRevId)
		else:
			curRev = None
			curNum = "0"
	except:
		curRev = None
		curNum = "0"

	debug_print("Processing sheet:", s.SheetNumber, s.Name)
	debug_print("Template provided:", template)

	# If no template provided, use default format
	if template is None:
		preName = s.SheetNumber + " R" + curNum + " - " + s.Name
		shtName = strUtils_legalize(preName)
		debug_print("Using default format:", shtName)
		return shtName

	# If doc is provided, resolve custom parameters
	if doc:
		# Get titleblock for this sheet
		tblock = expUtils_getTitleBlock(s, doc)
		tblock_type = tblock.Document.GetElement(tblock.GetTypeId()) if tblock else None

		# Resolve sheet parameters
		template = expUtils_updateFilenameTemplate(
			template=template,
			value_type='sheet_param',
			value_getter=lambda x: expUtils_getParamValue(s.LookupParameter(x))
		)

		# Resolve titleblock parameters
		template = expUtils_updateFilenameTemplate(
			template=template,
			value_type='tblock_param',
			value_getter=lambda x: expUtils_getParamValue(tblock.LookupParameter(x) if tblock else None) or \
									expUtils_getParamValue(tblock_type.LookupParameter(x) if tblock_type else None)
		)

		# Resolve project parameters
		template = expUtils_updateFilenameTemplate(
			template=template,
			value_type='proj_param',
			value_getter=lambda x: expUtils_getParamValue(doc.ProjectInformation.LookupParameter(x))
		)

		# Resolve global parameters
		template = expUtils_updateFilenameTemplate(
			template=template,
			value_type='glob_param',
			value_getter=lambda x: expUtils_getParamValue(revit.query.get_global_parameter(x, doc=doc))
		)

	# Apply custom template
	try:
		# Get project info
		project_info = revit.query.get_project_info(doc=doc)
		shtName = template.format(
			number=s.SheetNumber,
			name=s.Name,
			name_dash=s.Name.replace(' ', '-'),
			name_underline=s.Name.replace(' ', '_'),
			rev_number=curNum,
			rev_desc=curRev.Description if curRev else '',
			rev_date=curRev.RevisionDate if curRev else '',
			current_date=datetime.datetime.today().strftime("%Y-%m-%d"),
			proj_name=project_info.name if project_info else '',
			proj_number=project_info.number if project_info else '',
		)
		shtName = strUtils_legalize(shtName)
		debug_print("Final filename:", shtName)
		return shtName
	except Exception as e:
		# Fallback to default format if template fails
		debug_print("Template error:", str(e), "- using default")
		preName = s.SheetNumber + " R" + curNum + " - " + s.Name
		shtName = strUtils_legalize(preName)
		debug_print("Default filename:", shtName)
		return shtName

# make view name for print
def expUtils_nameView(v):
	# make sheet name
	preName = str(v.ViewType) + '_' + v.Name
	viewName = strUtils_legalize(preName)
	return viewName

# open a view/sheet
def expUtils_viewFocus(v,myDoc,myUiDoc):
	try:
		myUiDoc.RequestViewChange(v)
		curView  = myDoc.ActiveView
		allViews = myUiDoc.GetOpenUIViews()
		for v in allViews:
			if v.ViewId != curView.Id:
				try:
					v.Close()
				except:
					pass
	except Exception as e:
		# Skip view change if not applicable (e.g., inactive document)
		pass

# make pdf options
def expUtils_pdfOpts(hcb=False,hsb=True,hrp=True,hvt=False,mcl=False,raster_processing=None):
	opts = DB.PDFExportOptions()
	# Settings default
	opts.HideCropBoundaries = hcb
	opts.HideScopeBoxes = hsb
	opts.HideReferencePlane = hrp
	opts.HideUnreferencedViewTags = hvt
	opts.MaskCoincidentLines = mcl
	opts.RasterQuality = DB.RasterQualityType.High
	opts.ColorDepth = DB.ColorDepthType.Color
	# Paper format
	opts.PaperFormat = DB.ExportPaperFormat.Default

	# Raster processing - load from config if not specified
	if raster_processing is None:
		settings = expUtils_getSavedPdfSettings()
		raster_processing = settings.get('raster_processing', False)

	opts.AlwaysUseRaster = raster_processing
	debug_print("PDF opts - AlwaysUseRaster (Raster Processing):", raster_processing)

	return opts

# make dwg options
def expUtils_dwgOpts(sc=False,mv=True):
	opts = DB.DWGExportOptions()
	# Settings default
	opts.SharedCoords = sc
	opts.MergedViews = mv
	return opts

# export a single sheet to pdf
def expUtils_exportSheetPdf(d,s,opt,myDoc,myUidoc,template=None):
	docName = expUtils_nameSheet(s, template, myDoc)
	expUtils_viewFocus(s,myDoc,myUidoc)
	# Strip any existing .pdf extension
	if docName.lower().endswith('.pdf'):
		docName = docName[:-4]
	# Do not append .pdf here; let the Export method handle it
	opt.FileName = docName
	# Prepare an Id list
	exportSheet = List[DB.ElementId]()
	exportSheet.Add(s.Id)
	# Export the sheet to PDF
	myDoc.Export(d, exportSheet, opt)
	return 1

# export a single sheet to dwg
def expUtils_exportSheetDwg(d, s, opt, myDoc, myUidoc, template=None):
    docName = expUtils_nameSheet(s, template, myDoc)
    expUtils_viewFocus(s, myDoc, myUidoc)
    if not docName.lower().endswith('.dwg'):
        docName += '.dwg'
    # Apply export setup dari config — HARUS di sini karena butuh doc
    opt = expUtils_applyDwgExportSetup(myDoc, opt)
    debug_print("DWG export - file:{} mergedviews:{} version:{}".format(
        docName, opt.MergedViews, opt.FileVersion))
    exportSheet = List[DB.ElementId]()
    exportSheet.Add(s.Id)
    myDoc.Export(d, docName, exportSheet, opt)
    return 1

# export a single view to dwg
def expUtils_exportViewDwg(d,v,opt,myDoc,myUidoc):
	docName = expUtils_nameView(v)
	expUtils_viewFocus(v,myDoc,myUidoc)
	# Prepare an Id list
	exportView = List[DB.ElementId]()
	exportView.Add(v.Id)
	# Export the sheet to DWG
	myDoc.Export(d, docName, exportView, opt)
	return 1

# export a single sheet to pdf and dwg
def expUtils_exportSheetPdfDwg(d,s,optPdf,optDwg,myDoc,myUidoc):
	docName = expUtils_nameSheet(s)
	expUtils_viewFocus(s,myDoc,myUidoc)
	optPdf.FileName = docName
	# Prepare an Id list
	exportSheet = List[DB.ElementId]()
	exportSheet.Add(s.Id)
	# Export the sheet to PDF
	myDoc.Export(d, exportSheet, optPdf)
	# Export the sheet to DWG
	myDoc.Export(d, docName, exportSheet, optDwg)
	return 1

# update Sheet Issue Date parameter for a sheet
def expUtils_updateSheetIssueDate(sheet, doc):
	"""
	Update the Sheet Issue Date parameter for a given sheet with today's date.
	
	Args:
		sheet: The sheet element to update
		doc: The Revit document
	
	Returns:
		bool: True if update successful, False otherwise
	"""
	try:
		# Get today's date in dd/mm/yy format
		today_str = datetime.datetime.today().strftime("%d/%m/%y")
		
		# Get the parameter
		param = sheet.LookupParameter("Sheet Issue Date")
		
		if param and param.StorageType == DB.StorageType.String:
			# Update the parameter value
			param.Set(today_str)
			return True
		else:
			# Parameter not found or not a string parameter
			return False
			
	except Exception as e:
		# Log error or handle exception
		print("Error updating Sheet Issue Date: {}".format(str(e)))
		return False

# update Sheet Issue Date for multiple sheets
def expUtils_updateSheetsIssueDate(sheets, doc):
	"""
	Update the Sheet Issue Date parameter for multiple sheets with today's date.
	
	Args:
		sheets: List of sheet elements to update
		doc: The Revit document
	
	Returns:
		int: Number of sheets successfully updated
	"""
	updated_count = 0
	
	# Start transaction
	with revit.Transaction("Update Sheet Issue Date"):
		for sheet in sheets:
			if expUtils_updateSheetIssueDate(sheet, doc):
				updated_count += 1
	
	return updated_count

# ──────────────────────────────────────────────
# DWG CONFIGURATION UTILITIES
# ──────────────────────────────────────────────

def expUtils_getDwgExportSetups(doc):
    """Return list of saved DWG Export Setup names dari dokumen"""
    try:
        names = list(DB.DWGExportOptions.GetPredefinedSetupNames(doc))
        debug_print("DWG export setups:", names)
        return sorted(names)
    except Exception as e:
        debug_print("Error getting DWG export setups:", str(e))
        return []

def expUtils_getSavedDwgSettings():
    """Get saved DWG export settings from shared config"""
    try:
        config = script.get_config(section='shared_naming')
        settings = {
            'export_setup': config.get_option('dwg_export_setup', None),
            'merged_views': config.get_option('dwg_merged_views', True),
            'file_format':  config.get_option('dwg_file_format', 'R2018'),
        }
        debug_print("Loaded DWG settings:", settings)
        return settings
    except Exception as e:
        debug_print("Error getting DWG settings:", str(e))
        return {'export_setup': None, 'merged_views': True, 'file_format': 'R2018'}

def expUtils_saveDwgSettings(settings):
    """Save DWG export settings to shared config"""
    try:
        config = script.get_config(section='shared_naming')
        config.set_option('dwg_export_setup', settings.get('export_setup', None))
        config.set_option('dwg_merged_views', settings.get('merged_views', True))
        config.set_option('dwg_file_format',  settings.get('file_format', 'R2018'))
        script.save_config()
        debug_print("DWG settings saved:", settings)
        return True
    except Exception as e:
        debug_print("Error saving DWG settings:", str(e))
        return False

def expUtils_dwgOpts(sc=False, mv=None):
    """
    Build DWGExportOptions dari saved config.
    sc = SharedCoords override (default False)
    mv = MergedViews override (None = baca dari config)
    """
    from pyrevit import DB

    settings = expUtils_getSavedDwgSettings()

    opts = DB.DWGExportOptions()
    opts.SharedCoords = sc

    # Merged Views — dari config kecuali di-override
    if mv is None:
        mv = settings.get('merged_views', True)
    opts.MergedViews = mv

    # File Format Version
    fmt_str = settings.get('file_format', 'R2018')
    fmt_map = {
        'R2018': DB.ACADVersion.R2018,
        'R2013': DB.ACADVersion.R2013,
        'R2010': DB.ACADVersion.R2010,
        'R2007': DB.ACADVersion.R2007,
    }
    opts.FileVersion = fmt_map.get(fmt_str, DB.ACADVersion.R2018)
    debug_print("DWG opts - MergedViews:{} FileVersion:{}".format(opts.MergedViews, fmt_str))

    return opts

def expUtils_applyDwgExportSetup(doc, opts):
    try:
        settings = expUtils_getSavedDwgSettings()
        setup_name = settings.get('export_setup', None)

        # Get predefined options - may return None in Revit 2026+ if setup not found
        predefined_opts = DB.DWGExportOptions.GetPredefinedOptions(doc, setup_name)

        if predefined_opts is not None:
            # Revit 2024+ way - use the predefined options
            opts = predefined_opts
        else:
            # Fallback: keep original opts but apply settings manually
            debug_print("DWG export setup '{}' not found, using manual settings".format(setup_name))

        fmt_map = {
            'R2018': DB.ACADVersion.R2018, 'R2013': DB.ACADVersion.R2013,
            'R2010': DB.ACADVersion.R2010, 'R2007': DB.ACADVersion.R2007,
        }
        opts.MergedViews = settings.get('merged_views', True)
        opts.FileVersion = fmt_map.get(settings.get('file_format', 'R2018'), DB.ACADVersion.R2018)
        return opts

    except Exception as e:
        debug_print("Error applying DWG export setup:", str(e))
        return opts

# ──────────────────────────────────────────────
# PDF CONFIGURATION UTILITIES
# ──────────────────────────────────────────────

def expUtils_getSavedPdfSettings():
    """Get saved PDF export settings from shared config"""
    try:
        config = script.get_config(section='shared_naming')
        settings = {
            'raster_processing': config.get_option('pdf_raster_processing', False),  # False = Vector (default)
        }
        debug_print("Loaded PDF settings:", settings)
        return settings
    except Exception as e:
        debug_print("Error getting PDF settings:", str(e))
        return {'raster_processing': False}

def expUtils_savePdfSettings(settings):
    """Save PDF export settings to shared config"""
    try:
        config = script.get_config(section='shared_naming')
        config.set_option('pdf_raster_processing', settings.get('raster_processing', False))
        script.save_config()
        debug_print("PDF settings saved:", settings)
        return True
    except Exception as e:
        debug_print("Error saving PDF settings:", str(e))
        return False