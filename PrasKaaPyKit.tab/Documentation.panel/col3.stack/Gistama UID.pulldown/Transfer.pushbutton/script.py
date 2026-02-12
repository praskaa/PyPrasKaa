# -*- coding: utf-8 -*-
"""
Transfer GIS_Element_UID from Linked Revit Model based on Geometry Intersection.

This script finds matching elements between the host model and a selected linked
Revit model. The matching is done by finding the largest intersection volume
between elements, then validating Family name and Type name match.

Workflow:
1. Select a linked Revit model from available links
2. Collect host elements that have GIS_Element_UID
3. Collect linked elements from the selected model
4. Find best matches using intersection volume
5. Validate Family name + Type name match (required)
6. Copy GIS_Element_UID from linked to host
7. Export CSV log to Documents\PrasKaaPyKit\
8. Simple summary output

Features:
- Uses largest intersection volume for matching
- Validates Family and Type name match (required)
- Only processes host elements with existing GIS_Element_UID
- Exports detailed CSV log
- Simple text output summary
"""

__title__ = 'Transfer GIS UIDs'
__author__ = 'PrasKaa'
__doc__ = "Copies GIS_Element_UID from linked Revit model elements to host " \
          "elements by finding geometric matches (intersection volume) with " \
          "Family and Type name validation."


from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    RevitLinkInstance,
    Solid,
    BooleanOperationsUtils,
    BooleanOperationsType,
    Transaction,
    View,
    ViewType,
    GeometryInstance,
    Transform,
    XYZ,
    Element,
    ElementId
)

from pyrevit import revit, forms, script
import os
import datetime
import csv

# Import shared GIS categories configuration
from parameters.gis_categories import GIS_CATEGORIES, PARAM_NAME

# Import element name extraction utilities
from elements.element_names import get_family_name, get_type_name, get_family_and_type_name

# Setup
doc = revit.doc
uidoc = revit.uidoc
logger = script.get_logger()

# Log folder path
LOG_FOLDER = os.path.join(os.path.expanduser("~"), "Documents", "PrasKaaPyKit", "GIS_Transfer_Log")


def get_all_category_enums():
    """Get all BuiltInCategory enums from GIS_CATEGORIES."""
    return [cat_enum for cat_enum, _ in GIS_CATEGORIES.values()]


def ensure_log_folder():
    """Create log folder if it doesn't exist."""
    if not os.path.exists(LOG_FOLDER):
        os.makedirs(LOG_FOLDER)


def get_transformed_solid(element, transform=None):
    """
    Extracts the solid geometry from a given element with optional coordinate transformation.
    
    Args:
        element: The Revit element to extract geometry from.
        transform: Optional Transform to apply to the geometry (for linked elements).
    
    Returns:
        tuple: (Solid, Transform) - The extracted solid geometry and the transform,
               or (None, None) if extraction fails.
    """
    # Get geometry options
    app = doc.Application
    options = app.Create.NewGeometryOptions()
    active_view = doc.ActiveView
    if active_view:
        options.View = active_view
    else:
        view_collector = FilteredElementCollector(doc).OfClass(View)
        for v in view_collector:
            if not v.IsTemplate and v.ViewType == ViewType.ThreeD:
                options.View = v
                break
    
    geom_element = element.get_Geometry(options)
    if not geom_element:
        return None, transform
    
    solids = []
    for geom_obj in geom_element:
        if isinstance(geom_obj, Solid) and geom_obj.Volume > 0:
            solids.append(geom_obj)
        elif isinstance(geom_obj, GeometryInstance):
            instance_geom = geom_obj.GetInstanceGeometry()
            if instance_geom:
                for inst_obj in instance_geom:
                    if isinstance(inst_obj, Solid) and inst_obj.Volume > 0:
                        solids.append(inst_obj)
    
    if not solids:
        return None, transform
    
    # If multiple solids, unite them into one
    if len(solids) > 1:
        main_solid = solids[0]
        for s in solids[1:]:
            try:
                main_solid = BooleanOperationsUtils.ExecuteBooleanOperation(
                    main_solid, s, BooleanOperationsType.Union
                )
            except Exception as e:
                logger.warning("Could not unite solids for element {}. Error: {}".format(
                    element.Id, e))
        return main_solid, transform
    
    return solids[0], transform


def find_best_match(host_element, linked_elements_dict):
    """
    Finds the best matching linked element for a host element based on intersection volume.
    
    Args:
        host_element (Element): The element in the host model.
        linked_elements_dict (dict): Dictionary of {ElementId: {'element': Element, 'solid': Solid}}
                                    from the linked model.
    
    Returns:
        Element: The best matching element from the linked model, or None.
    """
    host_solid, _ = get_transformed_solid(host_element)
    if not host_solid:
        return None
    
    best_match = None
    max_intersection_volume = 0.0
    
    for linked_id, linked_data in linked_elements_dict.items():
        linked_solid = linked_data['solid']
        if not linked_solid:
            continue
        
        try:
            intersection_solid = BooleanOperationsUtils.ExecuteBooleanOperation(
                host_solid, linked_solid, BooleanOperationsType.Intersect
            )
            
            if intersection_solid and intersection_solid.Volume > max_intersection_volume:
                max_intersection_volume = intersection_solid.Volume
                best_match = linked_data['element']
        
        except Exception as e:
            logger.debug("Boolean operation failed between host {} and linked {}. Error: {}".format(
                host_element.Id, linked_id, e))
            continue
    
    return best_match


def validate_family_type_match(host_element, linked_element):
    """
    Validate that Family name and Type name match between host and linked elements.
    
    Args:
        host_element (Element): The host element.
        linked_element (Element): The linked element.
    
    Returns:
        tuple: (bool, str) - (True, "") if match, (False, reason) if mismatch.
    """
    host_family, host_type = get_family_and_type_name(host_element)
    linked_family, linked_type = get_family_and_type_name(linked_element)
    
    # Check Family name match
    if host_family != linked_family:
        return False, "Family Mismatch: '{}' != '{}'".format(host_family, linked_family)
    
    # Check Type name match
    if host_type != linked_type:
        return False, "Type Mismatch: '{}' != '{}'".format(host_type, linked_type)
    
    return True, ""


def export_csv_log(transfer_data, log_path):
    """
    Export transfer log to CSV file.
    
    Args:
        transfer_data (list): List of dictionaries with transfer results.
        log_path (str): Full path to the CSV file.
    """
    if not transfer_data:
        return
    
    fieldnames = [
        "Host Element ID",
        "Host Family Name",
        "Host Type Name",
        "Linked Element ID",
        "Linked Family Name",
        "Linked Type Name",
        "GIS_Element_UID",
        "Status",
        "Skip Reason"
    ]
    
    with open(log_path, 'wb') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transfer_data)


def main():
    """
    Main execution logic for transferring GIS_Element_UID.
    """
    # =========================================================================
    # STEP 1: Select the Linked Model
    # =========================================================================
    link_instances = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()
    
    if not link_instances:
        forms.alert("No Revit links found in the current project.", exitscript=True)
    
    link_dict = {link.Name: link for link in link_instances}
    
    selected_link_name = forms.SelectFromList.show(
        sorted(link_dict.keys()),
        title='Select Source Linked Revit Model',
        button_name='Select Link',
        multiselect=False
    )
    
    selected_link = link_dict.get(selected_link_name) if selected_link_name else None
    
    if not selected_link:
        forms.alert("No link selected. Script will exit.", exitscript=True)
    
    link_doc = selected_link.GetLinkDocument()
    if not link_doc:
        forms.alert("Could not access the document of the selected link. Ensure it is loaded.", exitscript=True)
    
    # =========================================================================
    # STEP 2: Get the transformation matrix for the linked model
    # =========================================================================
    link_transform = selected_link.GetTotalTransform()
    if not link_transform:
        link_transform = Transform.Identity
    
    # =========================================================================
    # STEP 2b: Select Transfer Mode
    # =========================================================================
    transfer_mode = forms.alert(
        "Select transfer mode:",
        options=["Transfer Missing", "Overwrite All"],
        title="Transfer Mode"
    )
    
    if not transfer_mode:
        forms.alert("No mode selected. Script will exit.", exitscript=True)
    
    overwrite = (transfer_mode == "Overwrite All")
    
    # =========================================================================
    # STEP 3: Collect Host Elements by Categories
    # =========================================================================
    host_elements = []
    
    for cat_enum in get_all_category_enums():
        for el in FilteredElementCollector(doc).OfCategory(cat_enum).WhereElementIsNotElementType():
            # Check if we should include this element based on mode
            param = el.LookupParameter(PARAM_NAME)
            has_uid = param and param.AsString()
            
            if not overwrite and has_uid:
                # Transfer Missing mode: skip elements that already have UID
                continue
            
            host_elements.append(el)
    
    if not host_elements:
        if overwrite:
            forms.alert("No elements found in the host model.", exitscript=True)
        else:
            forms.alert("No elements without GIS_Element_UID found in the host model.", exitscript=True)
    
    logger.info("Found {} host elements to process (mode: {})".format(
        len(host_elements), transfer_mode))
    
    # =========================================================================
    # STEP 4: Collect Linked Elements by Categories
    # =========================================================================
    linked_elements = []
    
    for cat_enum in get_all_category_enums():
        elements = FilteredElementCollector(link_doc).OfCategory(cat_enum).WhereElementIsNotElementType().ToElements()
        linked_elements.extend(elements)
    
    if not linked_elements:
        forms.alert("No elements found in the linked model.", exitscript=True)
    
    # =========================================================================
    # STEP 5: Pre-calculate solids for linked elements
    # =========================================================================
    linked_elements_dict = {}
    
    with forms.ProgressBar(title='Processing linked elements... ({value} of {max_value})', cancellable=True) as pb:
        for i, el in enumerate(linked_elements):
            if pb.cancelled:
                forms.alert("Operation cancelled by user.", exitscript=True)
            pb.update_progress(i, len(linked_elements))
            
            solid, _ = get_transformed_solid(el, link_transform)
            if solid:
                linked_elements_dict[el.Id] = {'element': el, 'solid': solid}
    
    if not linked_elements_dict:
        forms.alert("Could not extract geometry from any linked element.", exitscript=True)
    
    # =========================================================================
    # STEP 6: Find best matches and validate
    # =========================================================================
    transfer_data = []
    updated_count = 0
    skipped_family_mismatch = 0
    skipped_type_mismatch = 0
    no_match_count = 0
    skipped_no_uid = 0
    
    with forms.ProgressBar(title='Finding matches... ({value} of {max_value})', cancellable=True) as pb:
        for i, host_el in enumerate(host_elements):
            if pb.cancelled:
                forms.alert("Operation cancelled by user.", exitscript=True)
            pb.update_progress(i, len(host_elements))
            
            # Find best match by volume
            best_match = find_best_match(host_el, linked_elements_dict)
            
            if not best_match:
                family_name, type_name = get_family_and_type_name(host_el)
                transfer_data.append({
                    "Host Element ID": host_el.Id.IntegerValue,
                    "Host Family Name": family_name,
                    "Host Type Name": type_name,
                    "Linked Element ID": "",
                    "Linked Family Name": "",
                    "Linked Type Name": "",
                    "GIS_Element_UID": "",
                    "Status": "SKIPPED",
                    "Skip Reason": "No geometric match found"
                })
                no_match_count += 1
                continue
            
            # Validate Family + Type match
            is_valid, reason = validate_family_type_match(host_el, best_match)
            
            if not is_valid:
                host_family, host_type = get_family_and_type_name(host_el)
                linked_family, linked_type = get_family_and_type_name(best_match)
                
                transfer_data.append({
                    "Host Element ID": host_el.Id.IntegerValue,
                    "Host Family Name": host_family,
                    "Host Type Name": host_type,
                    "Linked Element ID": best_match.Id.IntegerValue,
                    "Linked Family Name": linked_family,
                    "Linked Type Name": linked_type,
                    "GIS_Element_UID": "",
                    "Status": "SKIPPED",
                    "Skip Reason": reason
                })
                
                if "Family" in reason:
                    skipped_family_mismatch += 1
                else:
                    skipped_type_mismatch += 1
                continue
            
            # Check if linked element has GIS_Element_UID
            linked_uid_param = best_match.LookupParameter(PARAM_NAME)
            if not linked_uid_param or not linked_uid_param.HasValue:
                family_name, type_name = get_family_and_type_name(host_el)
                transfer_data.append({
                    "Host Element ID": host_el.Id.IntegerValue,
                    "Host Family Name": family_name,
                    "Host Type Name": type_name,
                    "Linked Element ID": best_match.Id.IntegerValue,
                    "Linked Family Name": get_family_and_type_name(best_match)[0],
                    "Linked Type Name": get_family_and_type_name(best_match)[1],
                    "GIS_Element_UID": "",
                    "Status": "SKIPPED",
                    "Skip Reason": "Linked element has no GIS_Element_UID"
                })
                skipped_no_uid += 1
                continue
            
            # Ready to copy
            linked_uid = linked_uid_param.AsString()
            
            # Add to transfer list (will process in transaction)
            transfer_data.append({
                "Host Element ID": host_el.Id.IntegerValue,
                "Host Family Name": get_family_and_type_name(host_el)[0],
                "Host Type Name": get_family_and_type_name(host_el)[1],
                "Linked Element ID": best_match.Id.IntegerValue,
                "Linked Family Name": get_family_and_type_name(best_match)[0],
                "Linked Type Name": get_family_and_type_name(best_match)[1],
                "GIS_Element_UID": linked_uid,
                "Status": "PENDING",
                "Skip Reason": ""
            })
    
    # =========================================================================
    # STEP 7: Execute the transfers in a transaction
    # =========================================================================
    pending_transfers = [row for row in transfer_data if row["Status"] == "PENDING"]
    
    if pending_transfers:
        transaction_name = "Transfer GIS_Element_UID from Linked Model"
        
        with Transaction(doc, transaction_name) as t:
            t.Start()
            
            for row in pending_transfers:
                host_el = doc.GetElement(ElementId(row["Host Element ID"]))
                if host_el:
                    param = host_el.LookupParameter(PARAM_NAME)
                    if param and not param.IsReadOnly:
                        param.Set(row["GIS_Element_UID"])
                        updated_count += 1
                        row["Status"] = "SUCCESS"
            
            t.Commit()
    
    # =========================================================================
    # STEP 8: Export CSV Log
    # =========================================================================
    ensure_log_folder()
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = "GIS_Transfer_{}.csv".format(timestamp)
    log_path = os.path.join(LOG_FOLDER, log_filename)
    
    export_csv_log(transfer_data, log_path)
    
    # =========================================================================
    # STEP 9: Simple Summary Output
    # =========================================================================
    print("=" * 60)
    print("GIS_Element_UID Transfer Complete")
    print("=" * 60)
    print("Source Linked Model: {}".format(selected_link_name))
    print("Transfer Mode: {}".format(transfer_mode))
    print("Log File: {}".format(log_path))
    print("-" * 60)
    print("Summary:")
    print("  Total host elements processed: {}".format(len(host_elements)))
    print("  Successfully updated: {}".format(updated_count))
    print("  Skipped (Family mismatch): {}".format(skipped_family_mismatch))
    print("  Skipped (Type mismatch): {}".format(skipped_type_mismatch))
    print("  Skipped (No GIS_Element_UID in linked): {}".format(skipped_no_uid))
    print("  Skipped (No geometric match): {}".format(no_match_count))
    print("=" * 60)
    
    # Final alert
    forms.alert(
        "Successfully updated {} of {} elements ({} mode).\n\nLog saved to:\n{}".format(
            updated_count, len(host_elements), transfer_mode, log_path),
        title="Transfer Complete"
    )


if __name__ == '__main__':
    main()
