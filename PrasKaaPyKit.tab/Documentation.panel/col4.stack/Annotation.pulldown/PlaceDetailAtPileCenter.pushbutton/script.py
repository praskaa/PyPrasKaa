# -*- coding: utf-8 -*-
"""
Place Detail Item at Pile Center
Places detail items at the center of all Foundation Pile instances visible in the active ViewPlan
"""

import clr
import sys
import math

# Revit API
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import StructuralType

# pyRevit
from pyrevit import revit, forms, script

# Setup
doc = revit.doc
uidoc = revit.uidoc
active_view = doc.ActiveView
output = script.get_output()

# Configuration
FOUNDATION_PILE_FAMILY_NAME = "Foundation Pile"
DEBUG_MODE = False  # Set to True to enable debug output


def debug_print(message):
    """Print debug message only if debug mode is enabled"""
    if DEBUG_MODE:
        print("DEBUG: {}".format(message))


def get_family_name(element):
    """Get family name from element"""
    try:
        # Method 1: Through Symbol.Family (for family instances)
        if hasattr(element, 'Symbol') and element.Symbol:
            family = element.Symbol.Family
            if family and hasattr(family, 'Name'):
                return family.Name
    except:
        pass

    try:
        # Method 2: Through GetTypeId() and Family property
        element_type = element.Document.GetElement(element.GetTypeId())
        if element_type and hasattr(element_type, 'Family') and element_type.Family:
            return element_type.Family.Name
    except:
        pass

    try:
        # Method 3: ELEM_FAMILY_PARAM parameter
        family_param = element.get_Parameter(BuiltInParameter.ELEM_FAMILY_PARAM)
        if family_param and family_param.HasValue:
            return family_param.AsString()
    except:
        pass

    return None


def get_pile_type_name(pile):
    """Get pile type name using proven SYMBOL_NAME_PARAM method"""
    try:
        foundation_type = doc.GetElement(pile.GetTypeId())
        if foundation_type:
            name_param = foundation_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
            if name_param and name_param.HasValue:
                type_name = name_param.AsString()
                debug_print("Pile ID {} type name: '{}'".format(pile.Id, type_name))
                return type_name
    except Exception as e:
        debug_print("Error getting type name for pile {}: {}".format(pile.Id, str(e)))
        pass
    return "Unknown Type"


def pile_appears_in_view(pile, view):
    """Check if pile appears in the given view"""
    try:
        # For plan views, check if pile's base level matches view's level
        # or if pile spans through the view's level
        view_level = view.GenLevel
        if not view_level:
            return False

        # Get pile's base and top levels
        base_level_param = pile.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)
        top_level_param = pile.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM)

        base_elevation = 0
        top_elevation = float('inf')

        if base_level_param and base_level_param.HasValue:
            base_level_id = base_level_param.AsElementId()
            if base_level_id and base_level_id != ElementId.InvalidElementId:
                base_level = doc.GetElement(base_level_id)
                if base_level:
                    base_elevation = base_level.Elevation

        if top_level_param and top_level_param.HasValue:
            top_level_id = top_level_param.AsElementId()
            if top_level_id and top_level_id != ElementId.InvalidElementId:
                top_level = doc.GetElement(top_level_id)
                if top_level:
                    top_elevation = top_level.Elevation

        view_elevation = view_level.Elevation

        # Pile appears if view level is between base and top
        return base_elevation <= view_elevation <= top_elevation

    except Exception as e:
        print("Error checking pile visibility: {}".format(e))
        return False


def analyze_pile_types_in_view(doc, view):
    """
    Analyze and group Foundation Pile instances by type
    Returns: dict {type_name: [pile_elements]}
    """
    pile_groups = {}

    # Get all structural foundations
    foundations = FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_StructuralFoundation)\
        .WhereElementIsNotElementType()\
        .ToElements()

    debug_print("Found {} total structural foundations".format(len(foundations)))

    for foundation in foundations:
        # Check family name
        family_name = get_family_name(foundation)
        debug_print("Foundation ID {} - Family name: '{}'".format(foundation.Id, family_name))

        # Check if it's a pile (contains "pile" or "foundation" in family name)
        is_pile = False
        if family_name and ('pile' in family_name.lower() or 'foundation' in family_name.lower()):
            is_pile = True

        if is_pile:
            # Get type name for grouping
            type_name = get_pile_type_name(foundation)

            # Group by type
            if type_name not in pile_groups:
                pile_groups[type_name] = []
            pile_groups[type_name].append(foundation)

            debug_print("Foundation ID {} added to group '{}'".format(foundation.Id, type_name))

    # Log summary
    total_piles = sum(len(piles) for piles in pile_groups.values())
    debug_print("Analysis complete: {} pile types, {} total piles".format(len(pile_groups), total_piles))

    return pile_groups


def get_pile_center_for_2d_placement(pile):
    """
    Get pile center point for 2D detail item placement
    Returns XYZ with Z=0 for plan view placement
    """
    location = pile.Location

    if isinstance(location, LocationPoint):
        point = location.Point
        # Return 2D point (X, Y, 0) for plan placement
        return XYZ(point.X, point.Y, 0.0)

    return None


def get_available_detail_items(doc):
    """Get all available detail item types"""
    detail_items = FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_DetailComponents)\
        .WhereElementIsElementType()\
        .ToElements()

    return list(detail_items)


def get_detail_item_display_name(detail_type):
    """Get display name for detail item type"""
    try:
        name_param = detail_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
        if name_param and name_param.HasValue:
            return name_param.AsString()
    except:
        pass

    try:
        if hasattr(detail_type, 'Name') and detail_type.Name:
            return detail_type.Name
    except:
        pass

    return str(detail_type.Id)


def select_detail_item_for_type(pile_type, pile_count, available_types):
    """Show selection dialog for a specific pile type"""
    if not available_types:
        return None

    # Create options list with "(none - skip)" option
    type_options = ["(none - skip this type)"]
    for detail_type in available_types:
        display_name = get_detail_item_display_name(detail_type)
        type_options.append(display_name)

    # Show selection dialog
    selected_name = forms.SelectFromList.show(
        type_options,
        title="Select Detail Item for: {} ({} piles)".format(pile_type, pile_count),
        button_name="Select",
        multiselect=False
    )

    if not selected_name or selected_name == "(none - skip this type)":
        return None  # User chose to skip this type

    # Find the corresponding type object
    for detail_type in available_types:
        display_name = get_detail_item_display_name(detail_type)
        if display_name == selected_name:
            return detail_type

    return None


def create_pile_type_mapping_ui(pile_groups, available_detail_items):
    """
    Create mapping UI for pile types to detail items
    Returns: dict {pile_type: detail_item} only for mapped types
    """
    mapping = {}

    # Sort pile types by pile count (most common first)
    sorted_types = sorted(pile_groups.items(), key=lambda x: len(x[1]), reverse=True)

    for pile_type, piles in sorted_types:
        pile_count = len(piles)
        debug_print("Creating mapping for type: {} ({} piles)".format(pile_type, pile_count))

        # Let user select detail item for this type
        selected_detail_item = select_detail_item_for_type(pile_type, pile_count, available_detail_items)

        if selected_detail_item:
            mapping[pile_type] = selected_detail_item
            debug_print("Mapped {} -> {}".format(pile_type, get_detail_item_display_name(selected_detail_item)))
        else:
            debug_print("Skipped mapping for {}".format(pile_type))

    return mapping


def place_detail_item_at_pile_center(doc, view, detail_item_type, pile_center):
    """
    Place detail item with its origin at the pile center point
    For 2D placement in plan views
    """
    try:
        # Create detail item instance at pile center
        detail_item = doc.Create.NewFamilyInstance(
            pile_center,       # XYZ point (origin placement)
            detail_item_type,  # FamilySymbol
            view               # ViewPlan
        )
        return detail_item
    except Exception as e:
        debug_print("Failed to place detail item at {}: {}".format(pile_center, e))
        return None


def place_detail_items_with_mapping(doc, view, pile_groups, type_mapping):
    """
    Place detail items only for mapped pile types
    Returns: (successful, failed, skipped_types)
    """
    successful = []
    failed = []
    skipped_types = []

    debug_print("Starting placement for {} mapped types".format(len(type_mapping)))

    with Transaction(doc, "Place Detail Items at Pile Centers") as t:
        t.Start()

        for pile_type, piles in pile_groups.items():
            if pile_type in type_mapping:
                # This type is mapped - place detail items
                detail_item = type_mapping[pile_type]
                debug_print("Placing {} items for type: {}".format(len(piles), pile_type))

                for pile in piles:
                    center = get_pile_center_for_2d_placement(pile)
                    debug_print("Pile {} center: {}".format(pile.Id, center))

                    if center:
                        result = place_detail_item_at_pile_center(doc, view, detail_item, center)
                        if result:
                            successful.append((pile, result))
                        else:
                            failed.append((pile, "Placement failed"))
                    else:
                        failed.append((pile, "No valid center point"))
            else:
                # This type is not mapped - skip
                skipped_types.append(pile_type)
                skipped_count = len(piles)
                debug_print("Skipped unmapped type: {} ({} piles)".format(pile_type, skipped_count))

        t.Commit()

    debug_print("Placement complete - {} successful, {} failed, {} types skipped".format(
        len(successful), len(failed), len(skipped_types)))

    return successful, failed, skipped_types


def show_results(successful, failed, total_piles):
    """Show results summary"""
    success_count = len(successful)
    failed_count = len(failed)

    message = "Place Detail Item at Pile Centers - Results\n\n"
    message += "Total piles found: {}\n".format(total_piles)
    message += "Detail items placed: {}\n".format(success_count)
    message += "Failed placements: {}\n".format(failed_count)

    if failed_count > 0:
        message += "\nFailed placements:\n"
        for pile, error in failed[:5]:  # Show first 5 failures
            message += "- Pile ID {}: {}\n".format(pile.Id, error)
        if failed_count > 5:
            message += "... and {} more failures\n".format(failed_count - 5)

    forms.alert(message, title="Placement Complete")


def main():
    """Main execution function"""
    output.print_md("# Place Detail Item at Pile Centers")
    output.print_md("---")

    # Step 1: Validate active view
    if not isinstance(active_view, ViewPlan):
        forms.alert(
            "Active view '{}' is not a plan view.\n"
            "Please switch to a floor plan or structural plan.".format(
                active_view.Name
            ),
            title="Invalid View Type",
            exitscript=True
        )

    output.print_md("Active View: **{}**".format(active_view.Name))

    # Step 2: Analyze pile types in view
    output.print_md("## Step 1: Analyzing Pile Types")
    pile_groups = analyze_pile_types_in_view(doc, active_view)

    if not pile_groups:
        forms.alert(
            "No 'Foundation Pile' instances found in the current view.",
            title="No Piles Found",
            exitscript=True
        )

    # Show analysis results
    total_piles = sum(len(piles) for piles in pile_groups.values())
    output.print_md("Found **{}** pile types with **{}** total piles:".format(len(pile_groups), total_piles))

    for pile_type, piles in sorted(pile_groups.items(), key=lambda x: len(x[1]), reverse=True):
        output.print_md("- **{}**: {} piles".format(pile_type, len(piles)))

    # Step 3: Get available detail items
    output.print_md("## Step 2: Mapping Pile Types to Detail Items")
    available_detail_types = get_available_detail_items(doc)

    debug_print("Found {} detail item types".format(len(available_detail_types)))

    if not available_detail_types:
        forms.alert(
            "No detail item types found in the project.\n"
            "Please load detail item families first.",
            title="No Detail Items",
            exitscript=True
        )

    # Step 4: Create type-to-detail item mapping
    type_mapping = create_pile_type_mapping_ui(pile_groups, available_detail_types)

    if not type_mapping:
        forms.alert(
            "No pile types were mapped to detail items.\n"
            "At least one mapping is required.",
            title="No Mappings Created",
            exitscript=True
        )

    mapped_piles = sum(len(pile_groups[pile_type]) for pile_type in type_mapping.keys())
    output.print_md("Created mappings for **{}** pile types (**{}** piles will get detail items)".format(
        len(type_mapping), mapped_piles))

    # Step 5: Place detail items with mapping
    output.print_md("## Step 3: Placing Detail Items")

    successful, failed, skipped_types = place_detail_items_with_mapping(
        doc, active_view, pile_groups, type_mapping
    )

    # Step 6: Show results
    output.print_md("## Results")
    output.print_md("---")
    output.print_md("**Total piles analyzed:** {}".format(total_piles))
    output.print_md("**Pile types mapped:** {}".format(len(type_mapping)))
    output.print_md("**Detail items placed:** {}".format(len(successful)))
    output.print_md("**Failed placements:** {}".format(len(failed)))

    if skipped_types:
        output.print_md("**Skipped types:** {}".format(len(skipped_types)))
        for skipped_type in skipped_types:
            pile_count = len(pile_groups[skipped_type])
            output.print_md("- {} ({} piles)".format(skipped_type, pile_count))

    show_results(successful, failed, total_piles)

    output.print_md("### ✅ Process Complete")
    output.print_md("Detail items have been placed at pile centers according to type mappings.")


if __name__ == "__main__":
    main()