# -*- coding: utf-8 -*-
"""
Transfer Type Mark and Mark v2 - Transfer Mark values from Linked Model Type Names to Host Columns
Migrated to use ParameterSetting framework and modern WPF UI
"""

import re
import csv
import os
import io
import clr
import sys
from datetime import datetime

# Add extension root to Python path for library imports
# This is the standard pattern for accessing the 'lib' folder
extension_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if extension_root not in sys.path:
    sys.path.insert(0, extension_root)

# Import Windows Forms at module level
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')
import System.Windows.Forms as WinForms

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    RevitLinkInstance,
    ElementId,
    Solid,
    BooleanOperationsUtils,
    BooleanOperationsType,
    Transaction,
    TransactionStatus,
    View,
    ViewType,
    Element,
    BuiltInParameter,
    GeometryInstance
)

from pyrevit import revit, forms, script

# Import local library using imp for robustness in IronPython
import imp
lib_path = os.path.join(os.path.dirname(__file__), 'lib.py')
lib = imp.load_source('lib', lib_path)
TransferMarkConfig = lib.TransferMarkConfig
show_configuration_dialog = lib.show_configuration_dialog
FRAMEWORK_AVAILABLE = lib.FRAMEWORK_AVAILABLE

# Setup
doc = revit.doc
uidoc = revit.uidoc
logger = script.get_logger()
output = script.get_output()

# Debug: Check file locations
SCRIPT_DIR = os.path.dirname(__file__)
# These prints will be moved into the main execution logic to avoid split consoles

# Revit API Options for geometry extraction
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

# Script configuration
SCRIPT_SUBFOLDER = "Transfer Column Marks v2"

# Debug configuration - Set to True for troubleshooting, False for production
DEBUG_MODE = False  # Options: False, 'MINIMAL', 'NORMAL', 'VERBOSE', 'DIAGNOSTIC'

# Debug levels for granular control
DEBUG_LEVELS = {
    False: -1,        # No debug output
    'MINIMAL': 0,     # Only essential progress info
    'NORMAL': 1,      # Standard operation logs
    'VERBOSE': 2,     # Detailed operation logs
    'DIAGNOSTIC': 3   # Full diagnostic logs
}


def debug_log(message, level='NORMAL', force=False):
    """
    Smart logging function with debug toggle support.

    Args:
        message (str): Log message
        level (str): Debug level ('MINIMAL', 'NORMAL', 'VERBOSE', 'DIAGNOSTIC')
        force (bool): Force logging regardless of debug mode
    """
    if not force and not DEBUG_MODE:
        return

    # Determine current debug level
    if DEBUG_MODE is False:
        current_level = -1
    elif DEBUG_MODE is True:
        current_level = DEBUG_LEVELS['DIAGNOSTIC']  # True means full debug
    else:
        current_level = DEBUG_LEVELS.get(DEBUG_MODE, DEBUG_LEVELS['NORMAL'])

    required_level = DEBUG_LEVELS.get(level, DEBUG_LEVELS['NORMAL'])

    if current_level >= required_level or force:
        if level == 'MINIMAL' or force:
            logger.info(message)
        elif level == 'NORMAL':
            logger.info(message)
        elif level == 'VERBOSE':
            logger.debug(message)
        elif level == 'DIAGNOSTIC':
            logger.debug(message)


def feet3_to_mm3(volume_cu_ft):
    """Convert cubic feet to cubic millimeters for better readability."""
    # 1 cubic foot = 28,316,846.592 mm³
    return volume_cu_ft * 28316846.592


def get_solid(element):
    """Extracts the solid geometry from a given element with conditional debug logging."""
    debug_log("=== GEOMETRY EXTRACTION DEBUG for Element {} ===".format(element.Id), level='DIAGNOSTIC')

    try:
        geom_element = element.get_Geometry(options)
        debug_log("Geometry element retrieved: {}".format(geom_element is not None), level='DIAGNOSTIC')

        if not geom_element:
            debug_log("❌ FAILED: No geometry found for element {} (get_Geometry returned None)".format(element.Id), level='VERBOSE')
            debug_log("  - Element Category: {}".format(element.Category.Name if element.Category else "None"), level='DIAGNOSTIC')
            debug_log("  - Element Type: {}".format(type(element).__name__), level='DIAGNOSTIC')
            debug_log("  - Geometry Options View: {}".format(options.View.Name if options.View else "None"), level='DIAGNOSTIC')
            return None

        solids = []
        geom_count = 0

        for geom_obj in geom_element:
            geom_count += 1
            debug_log("Processing geometry object {}: Type={}, Volume={}".format(
                geom_count, type(geom_obj).__name__,
                getattr(geom_obj, 'Volume', 'N/A')), level='DIAGNOSTIC')

            if isinstance(geom_obj, Solid) and geom_obj.Volume > 0:
                solids.append(geom_obj)
                debug_log("  ✅ Added solid with volume: {:.6f} cu ft".format(geom_obj.Volume), level='DIAGNOSTIC')
            elif isinstance(geom_obj, GeometryInstance):
                # Handle geometry instances (common for families)
                debug_log("  📦 Processing GeometryInstance...", level='DIAGNOSTIC')
                instance_geom = geom_obj.GetInstanceGeometry()
                if instance_geom:
                    inst_count = 0
                    for inst_obj in instance_geom:
                        inst_count += 1
                        debug_log("    Instance geom {}: Type={}, Volume={}".format(
                            inst_count, type(inst_obj).__name__,
                            getattr(inst_obj, 'Volume', 'N/A')), level='DIAGNOSTIC')

                        if isinstance(inst_obj, Solid) and inst_obj.Volume > 0:
                            solids.append(inst_obj)
                            debug_log("      ✅ Added instance solid with volume: {:.6f} cu ft".format(inst_obj.Volume), level='DIAGNOSTIC')
                else:
                    debug_log("    ❌ No instance geometry found", level='DIAGNOSTIC')

        debug_log("Geometry processing complete: {} geometry objects processed, {} solids found".format(
            geom_count, len(solids)), level='DIAGNOSTIC')

        if not solids:
            debug_log("❌ FAILED: No valid solids found for element {} after processing {} geometry objects".format(
                element.Id, geom_count), level='VERBOSE')
            return None

        # Calculate total volume before union
        total_volume_before = sum(s.Volume for s in solids)
        debug_log("Total volume before union: {:.6f} cu ft from {} solids".format(
            total_volume_before, len(solids)), level='DIAGNOSTIC')

        # If multiple solids exist, unite them into a single solid for accurate volume calculations
        if len(solids) > 1:
            debug_log("Uniting {} solids...".format(len(solids)), level='DIAGNOSTIC')
            main_solid = solids[0]
            for i, s in enumerate(solids[1:], 1):
                try:
                    debug_log("  Union operation {}/{}...".format(i, len(solids)-1), level='DIAGNOSTIC')
                    main_solid = BooleanOperationsUtils.ExecuteBooleanOperation(main_solid, s, BooleanOperationsType.Union)
                    debug_log("    ✅ Union successful, current volume: {:.6f}".format(main_solid.Volume), level='DIAGNOSTIC')
                except Exception as e:
                    debug_log("❌ Could not unite solids for element {}. Union {}/{} failed: {}".format(
                        element.Id, i, len(solids)-1, e), level='VERBOSE')
            final_solid = main_solid
        else:
            final_solid = solids[0]

        debug_log("✅ SUCCESS: Geometry extracted for element {} - Final volume: {:.6f} cu ft".format(
            element.Id, final_solid.Volume), level='NORMAL')
        debug_log("=" * 60, level='DIAGNOSTIC')

        return final_solid

    except Exception as e:
        debug_log("❌ CRITICAL ERROR in geometry extraction for element {}: {}".format(element.Id, e), level='NORMAL')
        debug_log("=" * 60, level='DIAGNOSTIC')
        return None


def select_linked_model():
    """Prompts the user to select a linked EXR model from available Revit links."""
    link_instances = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()
    if not link_instances:
        forms.alert("No Revit links found in the current project.", exitscript=True)

    link_dict = {link.Name: link for link in link_instances}

    selected_link_name = forms.SelectFromList.show(
        sorted(link_dict.keys()),
        title='Select Source Linked EXR Model (from ETABS)',
        button_name='Select Link',
        multiselect=False
    )

    selected_link = link_dict.get(selected_link_name) if selected_link_name else None

    if not selected_link:
        forms.alert("No link selected. Script will exit.", exitscript=True)

    link_doc = selected_link.GetLinkDocument()
    if not link_doc:
        forms.alert("Could not access the document of the selected link. Ensure it is loaded.",
                   exitscript=True)

    return link_doc, selected_link


def collect_host_columns():
    """Collects structural column elements from the host Revit model."""
    selection_ids = uidoc.Selection.GetElementIds()
    host_columns = []

    if selection_ids:
        for elem_id in selection_ids:
            elem = doc.GetElement(elem_id)
            if (elem.Category and
                    elem.Category.Id.IntegerValue == int(BuiltInCategory.OST_StructuralColumns)):
                host_columns.append(elem)

        if not host_columns:
            forms.alert("No structural columns found in selection. Please select columns and try again.",
                       exitscript=True)
    else:
        host_columns = FilteredElementCollector(doc)\
            .OfCategory(BuiltInCategory.OST_StructuralColumns)\
            .WhereElementIsNotElementType()\
            .ToElements()

    return host_columns


def collect_linked_columns(link_doc):
    """Collects structural column elements from the linked EXR model."""
    linked_columns = FilteredElementCollector(link_doc)\
        .OfCategory(BuiltInCategory.OST_StructuralColumns)\
        .WhereElementIsNotElementType()\
        .ToElements()

    return linked_columns


def find_best_match(host_column, linked_columns_dict):
    """
    Finds the best matching linked column for a host column based on geometric intersection volume.

    This function calculates the solid geometry of the host column and compares it against
    all linked columns by computing Boolean intersection volumes. The linked column with the
    largest intersection volume is considered the best match.

    Args:
        host_column (Element): The structural column element in the host model to match.
        linked_columns_dict (dict): Dictionary mapping ElementId to {'element': Element, 'solid': Solid}
            for columns in the linked model.

    Returns:
        tuple: (best_match Element or None, max_intersection_volume float)
            - best_match: The best matching column from the linked model, or None if no valid
              intersection is found or if geometry extraction fails.
            - max_intersection_volume: The intersection volume in cubic feet.
    """
    host_solid = get_solid(host_column)
    if not host_solid:
        debug_log("Could not get solid for host column {}".format(host_column.Id), level='VERBOSE')
        return None, 0.0

    best_match = None
    max_intersection_volume = 0.0
    all_candidates = []  # For debugging

    debug_log("=== INTERSECTION ANALYSIS for Host Column {} ===".format(host_column.Id), level='VERBOSE')

    for linked_column_id, linked_column_data in linked_columns_dict.items():
        linked_solid = linked_column_data['solid']
        if not linked_solid:
            continue

        try:
            # Calculate intersection
            intersection_solid = BooleanOperationsUtils.ExecuteBooleanOperation(
                host_solid, linked_solid, BooleanOperationsType.Intersect
            )

            volume = intersection_solid.Volume if intersection_solid else 0.0
            all_candidates.append((linked_column_id, volume))

            # Log each candidate with both units
            volume_mm3 = feet3_to_mm3(volume)
            debug_log("Host {} vs Linked {}: {:.6f} cu ft ({:.0f} mm³)".format(
                host_column.Id, linked_column_id, volume, volume_mm3), level='VERBOSE')

            # Compare volume
            if volume > max_intersection_volume:
                max_intersection_volume = volume
                best_match = linked_column_data['element']

        except Exception as e:
            # This can fail if solids are disjoint or have geometric inaccuracies
            debug_log("Boolean operation failed between host {} and linked {}. Error: {}".format(
                host_column.Id, linked_column_id, e), level='DIAGNOSTIC')
            continue

    # Sort candidates by volume (descending) for better visibility
    sorted_candidates = sorted(all_candidates, key=lambda x: x[1], reverse=True)

    debug_log("--- TOP INTERSECTION CANDIDATES for Host {} ---".format(host_column.Id), level='VERBOSE')
    for i, (linked_id, vol) in enumerate(sorted_candidates[:5]):  # Show top 5
        marker = " *** BEST MATCH ***" if vol == max_intersection_volume else ""
        vol_mm3 = feet3_to_mm3(vol)
        debug_log("  #{}. Linked {}: {:.6f} cu ft ({:.0f} mm³){}".format(
            i+1, linked_id, vol, vol_mm3, marker), level='VERBOSE')

    max_vol_mm3 = feet3_to_mm3(max_intersection_volume)
    debug_log("SELECTED: Host {} -> Linked {} (volume: {:.6f} cu ft / {:.0f} mm³)".format(
        host_column.Id, best_match.Id if best_match else "None",
        max_intersection_volume, max_vol_mm3), level='NORMAL')
    debug_log("=" * 80, level='VERBOSE')

    return best_match, max_intersection_volume


def extract_type_mark_and_mark(type_name, config=None):
    """Extracts Type Mark and Mark values from column type name using configurable regex."""
    if not type_name or not config:
        return None

    pattern = config.get_type_mark_pattern()

    try:
        match = re.match(pattern, type_name.strip())
        if match and len(match.groups()) >= 2:
            return {
                'type_mark': match.group(1),
                'mark': match.group(2)
            }
        else:
            logger.warning("Could not parse type name '{}' with pattern '{}'".format(
                type_name, pattern))
            return None
    except Exception as e:
        logger.warning("Regex error parsing '{}': {}".format(type_name, e))
        return None


def get_current_type_mark(column):
    """Gets the current Type Mark value from a column's type."""
    try:
        column_type_id = column.GetTypeId()
        if column_type_id:
            column_type = doc.GetElement(column_type_id)
            if column_type:
                type_mark_param = column_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)
                if type_mark_param and type_mark_param.HasValue:
                    return type_mark_param.AsString()
    except Exception as e:
        logger.debug("Failed to get current Type Mark for column {}. Error: {}".format(
            column.Id, e))
    return None


def get_current_mark(column, mark_param_name):
    """Gets the current Mark value from a column instance."""
    try:
        mark_param = column.LookupParameter(mark_param_name)
        if mark_param and mark_param.HasValue:
            return mark_param.AsString()
    except Exception as e:
        logger.debug("Failed to get current Mark for column {}. Error: {}".format(
            column.Id, e))
    return None


def add_operations_to_batch(param_framework, column, type_mark, mark, mark_param_name):
    """Adds Type Mark and Mark setting operations to the framework's batch.
    This function will raise an exception if adding to batch fails.
    """
    column_type = doc.GetElement(column.GetTypeId())
    if not column_type:
        raise Exception("Could not access column type for column {}".format(column.Id))

    # Add Type Mark operation to batch
    param_framework.set_parameter(
        element=column_type,
        param_name="Type Mark",
        value=type_mark,
        optimization_level=lib.OptimizationLevel.BATCH
    )

    # Add Mark operation to batch
    param_framework.set_parameter(
        element=column,
        param_name=mark_param_name,
        value=mark,
        optimization_level=lib.OptimizationLevel.BATCH
    )


def set_type_mark_and_mark_legacy(column, type_mark, mark, mark_param_name):
    """Legacy method for setting Type Mark and Mark parameters."""
    errors = []

    # Set Type Mark
    try:
        column_type_id = column.GetTypeId()
        if column_type_id:
            column_type = doc.GetElement(column_type_id)
            if column_type:
                type_mark_param = column_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)
                if type_mark_param and not type_mark_param.IsReadOnly:
                    type_mark_param.Set(type_mark)
                else:
                    errors.append("Type Mark parameter not found or read-only")
            else:
                errors.append("Could not access column type")
        else:
            errors.append("Column has no type ID")
    except Exception as e:
        errors.append("Failed to set Type Mark: {}".format(str(e)))

    # Set Mark
    try:
        mark_param = column.LookupParameter(mark_param_name)
        if mark_param and not mark_param.IsReadOnly:
            mark_param.Set(mark)
        else:
            errors.append("Mark parameter '{}' not found or read-only".format(mark_param_name))
    except Exception as e:
        errors.append("Failed to set Mark: {}".format(str(e)))

    success = len(errors) == 0
    error_message = "; ".join(errors) if errors else None

    return success, error_message


# This function is now handled by the batch operation
# def set_type_mark_and_mark(...)


def get_csv_output_path():
    """Gets the organized output path for CSV files."""
    try:
        from matching_config import CSV_BASE_DIR, CSV_CREATE_FOLDERS
    except ImportError:
        CSV_BASE_DIR = os.path.expanduser("~/Desktop")
        CSV_CREATE_FOLDERS = True

    script_path = os.path.join(CSV_BASE_DIR, SCRIPT_SUBFOLDER)

    if CSV_CREATE_FOLDERS:
        if not os.path.exists(CSV_BASE_DIR):
            os.makedirs(CSV_BASE_DIR)
        if not os.path.exists(script_path):
            os.makedirs(script_path)

    return script_path


def export_results_to_csv(failed_transfers, type_mark_conflicts, doc_title):
    """Exports transfer results to a CSV file."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_doc_title = "".join(c for c in doc_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = "TransferColumnMarks_v2_{}_{}.csv".format(safe_doc_title, timestamp)

        output_dir = get_csv_output_path()
        filepath = os.path.join(output_dir, filename)

        with io.open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            writer.writerow([
                'Category', 'Host Column ID', 'Current Type Mark', 'Target Type Mark',
                'Current Mark', 'Target Mark', 'Linked Type Name', 'Status', 'Error Message'
            ])

            for (host_column, linked_column, current_type_mark, target_type_mark,
                 current_mark, target_mark, linked_type_name, error_msg) in failed_transfers:
                writer.writerow([
                    'Failed Transfer',
                    str(host_column.Id),
                    current_type_mark or 'N/A',
                    target_type_mark or 'N/A',
                    current_mark or 'N/A',
                    target_mark or 'N/A',
                    linked_type_name or 'N/A',
                    'TRANSFER_FAILED',
                    error_msg or 'N/A'
                ])

            for (host_column, linked_column, current_type_mark, target_type_mark,
                 current_mark, target_mark, linked_type_name) in type_mark_conflicts:
                writer.writerow([
                    'Type Mark Conflict',
                    str(host_column.Id),
                    current_type_mark or 'N/A',
                    target_type_mark or 'N/A',
                    current_mark or 'N/A',
                    target_mark or 'N/A',
                    linked_type_name or 'N/A',
                    'TYPE_MARK_CONFLICT',
                    'Existing Type Mark does not match target'
                ])

        logger.info("Results exported to: {}".format(filepath))
        return filepath

    except Exception as e:
        logger.error("Failed to export results to CSV: {}".format(e))
        return None


def execute_transfer():
    """Execute the main transfer functionality"""
    output_lines = []
    output_lines.append("="*60)
    output_lines.append("SCRIPT DIRECTORY: {}".format(SCRIPT_DIR))
    output_lines.append("="*60)
    output_lines.append("FRAMEWORK_AVAILABLE: {}".format(FRAMEWORK_AVAILABLE))
    output_lines.append("="*60)
    output_lines.append("\n" + "="*60)
    output_lines.append("EXECUTING TRANSFER v2")
    output_lines.append("="*60)

    config_manager = TransferMarkConfig()
    param_framework = lib.ParameterSettingFramework(doc, logger) if FRAMEWORK_AVAILABLE else None

    output_lines.append("# Transfer Type Mark and Mark v2 - Column Mark Transfer")
    output_lines.append("---")

    # Step 1: Select linked model
    output_lines.append("## Step 1: Setup Linked EXR Model")
    link_doc, selected_link = select_linked_model()
    output_lines.append("Linked EXR model: **{}**".format(link_doc.Title))
    output_lines.append("---")

    mark_param_name = config_manager.get_mark_parameter_name()
    output_lines.append("Target Mark parameter: **{}**".format(mark_param_name))
    output_lines.append("Type Mark pattern: **{}**".format(config_manager.get_type_mark_pattern()))
    output_lines.append("Framework available: **{}**".format(FRAMEWORK_AVAILABLE))
    output_lines.append("---")

    # Step 2: Collect columns
    output_lines.append("## Step 2: Collecting Columns")
    host_columns = collect_host_columns()
    linked_columns = collect_linked_columns(link_doc)

    if not host_columns or not linked_columns:
        forms.alert("No structural column elements found in the host or linked model.", exitscript=True)

    output_lines.append("Host columns found: **{}**".format(len(host_columns)))
    output_lines.append("Linked columns found: **{}**".format(len(linked_columns)))
    output_lines.append("---")

    # Step 3: Process geometry
    output_lines.append("## Step 3: Processing Linked Column Geometry")
    output_lines.append("Processing {} linked columns...".format(len(linked_columns)))
    linked_columns_dict = {}
    for column in linked_columns:
        solid = get_solid(column)
        if solid:
            linked_columns_dict[column.Id] = {'element': column, 'solid': solid}
    output_lines.append("✓ Geometry processing complete: {} columns cached".format(len(linked_columns_dict)))

    # Step 4: Transfer marks
    output_lines.append("## Step 4: Processing Mark Transfers")
    output_lines.append("Finding matches and transferring marks...")

    successful_transfers = 0
    failed_transfers = []
    type_mark_conflicts = []
    unmatched_columns = []
    batch_operations_to_commit = []

    for host_column in host_columns:
        best_match, intersection_volume = find_best_match(host_column, linked_columns_dict)

        if not best_match:
            unmatched_columns.append(host_column)
            continue

        linked_type = best_match.Document.GetElement(best_match.GetTypeId())
        if not linked_type:
            failed_transfers.append((host_column, best_match, None, None, None, None, None, "Could not access linked column type"))
            continue

        type_name_param = linked_type.LookupParameter('Type Name')
        if not type_name_param or not type_name_param.HasValue:
            failed_transfers.append((host_column, best_match, None, None, None, None, None, "Linked column has no Type Name parameter"))
            continue

        linked_type_name = type_name_param.AsString()
        extracted_values = extract_type_mark_and_mark(linked_type_name, config_manager)
        if not extracted_values:
            failed_transfers.append((host_column, best_match, None, None, None, None, linked_type_name, "Could not parse type name format"))
            continue

        target_type_mark = extracted_values['type_mark']
        target_mark = extracted_values['mark']
        current_type_mark = get_current_type_mark(host_column)
        current_mark = get_current_mark(host_column, mark_param_name)

        if current_type_mark and current_type_mark != target_type_mark:
            type_mark_conflicts.append((host_column, best_match, current_type_mark, target_type_mark, current_mark, target_mark, linked_type_name))
            continue

        operation_data = (host_column, best_match, current_type_mark, target_type_mark, current_mark, target_mark, linked_type_name)

        try:
            if FRAMEWORK_AVAILABLE:
                add_operations_to_batch(param_framework, host_column, target_type_mark, target_mark, mark_param_name)
                batch_operations_to_commit.append(operation_data)
            else:
                with Transaction(doc, "Set Mark Legacy") as t:
                    t.Start()
                    success, error_msg = set_type_mark_and_mark_legacy(host_column, target_type_mark, target_mark, mark_param_name)
                    t.Commit()
                if success:
                    successful_transfers += 1
                else:
                    raise Exception(error_msg)
        except Exception as e:
            logger.error("Error during operation for host column {}: {}".format(host_column.Id, str(e)))
            failed_transfers.append(operation_data + (str(e),))

    # Execute batch if framework was used
    if FRAMEWORK_AVAILABLE and batch_operations_to_commit:
        try:
            param_framework.execute_batch_operations("Batch Transfer Column Marks")
            successful_transfers += len(batch_operations_to_commit)
        except Exception as e:
            logger.error("Batch execution failed: {}".format(str(e)))
            # Move all pending batch operations to failed_transfers
            for op_data in batch_operations_to_commit:
                failed_transfers.append(op_data + ("Batch execution failed: {}".format(str(e)),))
            forms.alert("A critical error occurred during batch parameter update. No changes were saved.", title="Batch Error")

    # === CRITICAL: Print ALL Results AFTER operations ===
    output_lines.append("## Results Summary")
    output_lines.append("---")
    output_lines.append("**Total columns processed:** {}".format(len(host_columns)))
    output_lines.append("**Successful transfers:** {}".format(successful_transfers))
    output_lines.append("**Type Mark conflicts:** {}".format(len(type_mark_conflicts)))
    output_lines.append("**Failed transfers:** {}".format(len(failed_transfers)))
    output_lines.append("**Unmatched columns:** {}".format(len(unmatched_columns)))

    # Export CSV
    csv_path = None
    if failed_transfers or type_mark_conflicts:
        output_lines.append("**Exporting detailed results to CSV file...**")
        csv_path = export_results_to_csv(failed_transfers, type_mark_conflicts, doc.Title)
        if csv_path:
            output_lines.append("* **Full results exported to:** `{}`".format(csv_path))

    output_lines.append("---")

    # Print all collected output at once
    for line in output_lines:
        output.print_md(line)

    alert_message = "Mark transfer v2 complete!\n\n"
    alert_message += "Successful: {} columns\n".format(successful_transfers)
    alert_message += "Conflicts: {} columns\n".format(len(type_mark_conflicts))
    alert_message += "Failed: {} columns\n".format(len(failed_transfers))
    alert_message += "Unmatched: {} columns\n".format(len(unmatched_columns))

    if csv_path:
        alert_message += "\n\nDetailed results: Desktop\\{}".format(os.path.basename(csv_path))

    forms.alert(alert_message, title="Transfer Complete v2")


def main():
    """Main execution - Transfer Type Mark and Mark v2"""
    execute_transfer()


if __name__ == '__main__':
    main()