"""Ensures Adaptive Points are hidden in all views placed on sheets"""

__title__ = "Hide Adaptive Points"
__author__ = "PrasKaa Team"

from pyrevit import framework
from pyrevit import revit, DB


def get_views_on_sheets():
    """Get all views that are placed on sheets."""
    views_on_sheets = []

    # Get all sheets in the project
    all_sheets = DB.FilteredElementCollector(revit.doc)\
                   .OfCategory(DB.BuiltInCategory.OST_Sheets)\
                   .WhereElementIsNotElementType()\
                   .ToElements()

    # Collect all unique views from all sheets
    view_ids = set()
    for sheet in all_sheets:
        viewport_ids = sheet.GetAllViewports()
        for viewport_id in viewport_ids:
            viewport = revit.doc.GetElement(viewport_id)
            if viewport:
                view_ids.add(viewport.ViewId)

    # Convert view IDs to view objects
    for view_id in view_ids:
        view = revit.doc.GetElement(view_id)
        if view:
            views_on_sheets.append(view)

    return views_on_sheets


@revit.carryout('Hide Adaptive Points on Sheets')
def hide_adaptive_points_on_sheets():
    # Get all adaptive points in the project
    all_adaptive_points = DB.FilteredElementCollector(revit.doc)\
                            .OfCategory(DB.BuiltInCategory.OST_AdaptivePoints)\
                            .WhereElementIsNotElementType()\
                            .ToElements()

    # Get all views that are placed on sheets
    sheet_views = get_views_on_sheets()

    # Process each sheet view
    for view in sheet_views:
        # Collect points that are visible in this view and can be hidden
        visible_points_in_view = []

        for point in all_adaptive_points:
            # Check if the element can be hidden in this view
            if point.CanBeHidden(view) and not point.IsHidden(view):
                visible_points_in_view.append(point.Id)

        # Hide visible points in this view
        if visible_points_in_view:
            view.HideElements(framework.List[DB.ElementId](visible_points_in_view))


hide_adaptive_points_on_sheets()
