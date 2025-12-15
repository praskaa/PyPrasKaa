from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import UIDocument
default_uidoc = __revit__.ActiveUIDocument
default_doc = default_uidoc.Document




def get_views_on_sheet(sheet, uidoc=default_uidoc):
    """Function to return all views found on the given sheet."""
    doc = uidoc.Document
    viewports_ids   = sheet.GetAllViewports()
    viewports       = [doc.GetElement(viewport_id)  for viewport_id in viewports_ids]
    views_ids       = [viewport.ViewId              for viewport    in viewports]
    views           = [doc.GetElement(view_id)      for view_id     in views_ids]
    return views


def get_titleblock_on_sheet(sheet, uidoc=default_uidoc):
    """Function to get TitleBlock from given ViewSheet.
    It will not return any TitleBlocks if there are more than 1 on ViewSheet.
    :returns TitleBlock"""
    #TODO THIS FUNCTION IS OBSOLETE
    doc = uidoc.Document

    all_TitleBlocks = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsNotElementType().ToElements()
    title_blocks_on_sheet = []

    for title_block in all_TitleBlocks:
        if title_block.OwnerViewId == sheet.Id:
            title_blocks_on_sheet.append(title_block)

    if not title_blocks_on_sheet:
        print("***No TitleBlocks were found on given ViewSheet ({}***".format(sheet.SheetNumber))

    elif len(title_blocks_on_sheet) > 1:
        print("***There are more than 1 TitleBlock on given ViewSheet ({})****".format(sheet.SheetNumber))

    else:
        return title_blocks_on_sheet[0]


def get_titleblocks_from_sheet(sheet, uidoc):
    #type:(ViewSheet, UIDocument) -> list
    """Function to get TitleBlocks from the given ViewSheet.
    :param sheet: ViewSheet that has TitleBlock/
    :param uidoc: UIDocument of the Project
    :return:      list of TitleBlocks that are placed on the given Sheet."""
    # CREATE A RULE
    rule_value = sheet.SheetNumber
    param_sheet_number = ElementId(BuiltInParameter.SHEET_NUMBER)
    f_pvp = ParameterValueProvider(param_sheet_number)
    evaluator = FilterStringEquals()
    f_rule = FilterStringRule(f_pvp, evaluator, rule_value, True)

    # CREATE A FILTER
    tb_filter = ElementParameterFilter(f_rule)

    tb = FilteredElementCollector(uidoc.Document).OfCategory(BuiltInCategory.OST_TitleBlocks) \
        .WhereElementIsNotElementType().WherePasses(tb_filter).ToElements()

    return list(tb)

def get_views_on_sheets(doc=None):
    """Get all views that are placed on sheets."""
    if doc is None:
        doc = default_doc

    views_on_sheets = []

    # Get all sheets in the project
    all_sheets = FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_Sheets)\
        .WhereElementIsNotElementType()\
        .ToElements()

    # Collect all unique views from all sheets
    view_ids = set()
    for sheet in all_sheets:
        viewport_ids = sheet.GetAllViewports()
        for viewport_id in viewport_ids:
            view_id = doc.GetElement(viewport_id).ViewId
            view_ids.add(view_id)

    # Convert view IDs to view elements
    for view_id in view_ids:
        view = doc.GetElement(view_id)
        if view:
            views_on_sheets.append(view)

    return views_on_sheets

def get_sheets_with_view(view, doc=None):
    """Get all sheets that contain a specific view."""
    if doc is None:
        doc = default_doc

    sheets_with_view = []

    # Get all sheets
    sheets = FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_Sheets)\
        .WhereElementIsNotElementType()\
        .ToElements()

    for sheet in sheets:
        viewport_ids = sheet.GetAllViewports()
        for viewport_id in viewport_ids:
            viewport = doc.GetElement(viewport_id)
            if viewport and viewport.ViewId == view.Id:
                sheets_with_view.append(sheet)
                # Early exit if we only need one sheet (most common case)
                # break

    return sheets_with_view

def get_sheet_number_and_name(sheet):
    """Get formatted sheet number and name for display."""
    return "{} - {}".format(sheet.SheetNumber, sheet.Name)

