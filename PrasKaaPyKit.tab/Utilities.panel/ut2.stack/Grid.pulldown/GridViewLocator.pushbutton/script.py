# -*- coding: utf-8 -*-
__title__ = "Grid View Hider"
__author__ = "Prasetyo"
__doc__ = """Tool to find all views on sheets that contain specific grids and hide selected grids from chosen views"""

# Imports
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from pyrevit import revit, DB, UI, forms, script
from System.Collections.Generic import List

# pyRevit environment
doc = revit.doc
uidoc = revit.uidoc

# Import from lib following architecture guidelines
from Snippets._sheets import get_views_on_sheets, get_sheets_with_view, get_sheet_number_and_name
from Snippets._selection import get_selected_elements

def get_all_grids(doc=None):
    """Get all grids in the document."""
    if doc is None:
        doc = revit.doc

    collector = FilteredElementCollector(doc)\
        .OfClass(DB.Grid)\
        .WhereElementIsNotElementType()

    return list(collector)

def get_grid_display_name(grid):
    """Get display name for grid (name + id)."""
    return "{} (ID: {})".format(grid.Name, grid.Id.IntegerValue)


def find_views_containing_grids(selected_grids, doc=None):
    """Find all views that contain the selected grids."""
    if doc is None:
        doc = revit.doc

    # Get all views on sheets once
    views_on_sheets = get_views_on_sheets(doc)

    # Cache sheets for each view to avoid redundant calls
    view_to_sheets_cache = {}
    total_grids = len(selected_grids)
    grid_view_info = {}

    # Removed progress messages for cleaner output
    for i, grid in enumerate(selected_grids):
        grid_name = get_grid_display_name(grid)
        grid_view_info[grid_name] = []

        for view in views_on_sheets:
            # Check if grid is visible in this view
            try:
                if not grid.IsHidden(view):
                    # Use cached sheets or get them once
                    if view.Id not in view_to_sheets_cache:
                        view_to_sheets_cache[view.Id] = get_sheets_with_view(view, doc)

                    sheets = view_to_sheets_cache[view.Id]
                    for sheet in sheets:
                        sheet_info = get_sheet_number_and_name(sheet)
                        view_info = {
                            'view': view,
                            'sheet': sheet,
                            'sheet_info': sheet_info,
                            'view_name': view.Name,
                            'view_type': str(view.ViewType).replace('ViewType.', '')
                        }
                        grid_view_info[grid_name].append(view_info)
            except Exception as e:
                # Skip problematic views/grids and continue
                continue

    # Removed "Grid analysis complete!" message for cleaner output
    return grid_view_info

def show_grid_selection_dialog(grids):
    """Show dialog for selecting grids."""
    if not grids:
        print("No grids found in the document.")
        return None

    # Create display names for grids
    grid_options = [get_grid_display_name(grid) for grid in grids]

    # Show multi-selection dialog
    selected_names = forms.SelectFromList.show(
        grid_options,
        title='Select Grids to Hide',
        button_name='Find Views with Grids',
        multiselect=True
    )

    if not selected_names:
        print("User cancelled grid selection.")
        return None

    # Map back to grid objects
    selected_grids = []
    for grid in grids:
        if get_grid_display_name(grid) in selected_names:
            selected_grids.append(grid)

    # Removed selection confirmation for cleaner output
    return selected_grids

def show_view_selection_dialog(grid_view_info):
    """Show dialog for selecting views to modify."""
    if not grid_view_info:
        print("No views found containing the selected grids.")
        return None

    # Collect all unique views from the results
    all_views = []
    view_display_info = {}  # Map display name to view_info

    for grid_name, view_infos in grid_view_info.items():
        for view_info in view_infos:
            view = view_info['view']
            display_name = view_info['view_name'] + " (" + view_info['view_type'] + ") on " + view_info['sheet_info']
            if display_name not in view_display_info:
                view_display_info[display_name] = view_info
                all_views.append(display_name)

    if not all_views:
        print("No views available for selection.")
        return None

    # Show view selection dialog
    selected_view_names = forms.SelectFromList.show(
        all_views,
        title='Select Views to Modify',
        button_name='Hide Grids in Selected Views',
        multiselect=True
    )

    if not selected_view_names:
        print("User cancelled view selection.")
        return None

    # Map back to view objects
    selected_views = []
    for view_name in selected_view_names:
        if view_name in view_display_info:
            selected_views.append(view_display_info[view_name])

    # Removed view selection confirmation for cleaner output
    return selected_views

def hide_grids_in_views(selected_grids, selected_views):
    """Hide selected grids in the chosen views using transactions."""
    if not selected_grids or not selected_views:
        print("No grids or views selected for hiding.")
        return 0

    # Show summary BEFORE transaction
    print("About to hide " + str(len(selected_grids)) + " grid(s) from " + str(len(selected_views)) + " view(s)")

    # Start transaction
    transaction = Transaction(doc, "Hide Grids in Views")
    transaction.Start()

    grids_hidden_count = 0

    try:
        for view_info in selected_views:
            view = view_info['view']

            for grid in selected_grids:
                try:
                    # Check if grid is currently visible in this view
                    if not grid.IsHidden(view):
                        # Hide the grid in this view using the correct Revit API
                        # The correct method is to use the view's HideElements method
                        try:
                            # Create a list of element IDs to hide
                            element_ids = List[ElementId]()
                            element_ids.Add(grid.Id)

                            # Hide the elements in this specific view
                            view.HideElements(element_ids)

                            grids_hidden_count += 1
                            # Removed individual grid hiding messages for cleaner output
                        except Exception as hide_error:
                            # Removed individual error messages for cleaner output
                            # Try alternative approach if available
                            try:
                                # Some view types might need different handling
                                if hasattr(view, 'HideElement'):
                                    view.HideElement(grid.Id)
                                    grids_hidden_count += 1
                                    # Removed alternative method messages for cleaner output
                            except:
                                continue
                    else:
                        # Removed "already hidden" messages for cleaner output
                        pass
                except Exception as e:
                    # Removed individual error messages for cleaner output
                    continue

        # Commit transaction
        transaction.Commit()
        return grids_hidden_count

    except Exception as e:
        # Rollback transaction on error
        transaction.RollBack()
        return 0

def show_success_message(grids_hidden_count, views_modified_count):
    """Show success message after hiding grids."""
    if grids_hidden_count > 0:
        success_message = "SUCCESS: Grid Hiding Complete\n" + \
                         "=" * 50 + "\n" + \
                         "Grids hidden: " + str(grids_hidden_count) + "\n" + \
                         "Views modified: " + str(views_modified_count) + "\n" + \
                         "Changes can be undone using Revit's Undo feature\n" + \
                         "=" * 50
        forms.alert(success_message, title="Grid Hiding Complete", exitscript=False)
    else:
        forms.alert("No grids were hidden (they may already be hidden)", title="Grid Hiding", exitscript=False)

# Main execution
def run_grid_view_locator():
    """Main function to run the grid view locator tool."""

    # Get all grids in the document
    all_grids = get_all_grids(doc)
    print("Found " + str(len(all_grids)) + " grids in the document")

    # Show grid selection dialog
    selected_grids = show_grid_selection_dialog(all_grids)

    # Check if user cancelled or no grids found
    if not selected_grids:
        print("Operation cancelled or no grids available.")
        return

    # Find views containing selected grids
    grid_view_info = find_views_containing_grids(selected_grids, doc)

    # Check if any views were found
    if not grid_view_info:
        print("No views found containing the selected grids.")
        return

    # Show view selection dialog
    selected_views = show_view_selection_dialog(grid_view_info)

    # Check if user cancelled view selection
    if not selected_views:
        print("View selection cancelled.")
        return

    # Hide grids in selected views
    grids_hidden_count = hide_grids_in_views(selected_grids, selected_views)

    # Show success message
    show_success_message(grids_hidden_count, len(selected_views))

# Execute the tool
run_grid_view_locator()