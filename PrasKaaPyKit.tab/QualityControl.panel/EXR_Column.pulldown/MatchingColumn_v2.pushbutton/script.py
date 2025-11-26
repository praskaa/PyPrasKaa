# -*- coding: utf-8 -*-
"""
Matching Dimension Column v2 - Transfer Column Type based on Geometry Intersection
"""

__title__ = 'Matching\nDimension\nColumn v2'
__author__ = 'Kilo Code'
__doc__ = "Matches columns by geometry and transfers family types from a linked model."

import gc
import csv
import os
import io
from datetime import datetime

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, RevitLinkInstance, ElementId,
    Solid, BooleanOperationsUtils, BooleanOperationsType, Transaction,
    TransactionStatus, View, ViewType, Element, Transform, GeometryInstance,
    FamilySymbol, Family, BuiltInParameter, JoinGeometryUtils, Options
)

from pyrevit import revit, forms, script
from pyrevit.forms import ProgressBar

# Import local library
from lib import MatchingConfig, ConfigDialog

# Setup
doc = revit.doc
uidoc = revit.uidoc
logger = script.get_logger()
output = script.get_output()
config = MatchingConfig()

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

def get_solid(element):
    """Extracts the solid geometry from a given element."""
    geom_element = element.get_Geometry(options)
    if not geom_element:
        return None

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
        return None

    if len(solids) > 1:
        main_solid = solids[0]
        for s in solids[1:]:
            try:
                main_solid = BooleanOperationsUtils.ExecuteBooleanOperation(main_solid, s, BooleanOperationsType.Union)
            except Exception as e:
                logger.warning("Could not unite solids for element {}. Error: {}".format(element.Id, e))
        return main_solid
    return solids[0]

def select_linked_model():
    """Prompts the user to select a linked model."""
    link_instances = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()
    if not link_instances:
        forms.alert("No Revit links found.", exitscript=True)

    link_dict = {link.Name: link for link in link_instances}
    selected_link_name = forms.SelectFromList.show(
        sorted(link_dict.keys()),
        title='Select Source Linked Model',
        button_name='Select Link'
    )
    if not selected_link_name:
        forms.alert("No link selected.", exitscript=True)

    selected_link = link_dict[selected_link_name]
    link_doc = selected_link.GetLinkDocument()
    if not link_doc:
        forms.alert("Could not access the linked document.", exitscript=True)

    return link_doc, selected_link

def collect_columns(document, is_host=True):
    """Collects structural columns from a document."""
    if is_host:
        selection_ids = uidoc.Selection.GetElementIds()
        if selection_ids:
            columns = [doc.GetElement(id) for id in selection_ids if doc.GetElement(id).Category and doc.GetElement(id).Category.Id.IntegerValue == int(BuiltInCategory.OST_StructuralColumns)]
            if columns:
                return columns

    return FilteredElementCollector(document).OfCategory(BuiltInCategory.OST_StructuralColumns).WhereElementIsNotElementType().ToElements()

def find_best_match(host_solid, linked_columns_dict):
    """Finds the best matching linked column for a host column solid."""
    if not host_solid:
        return None

    best_match = None
    max_intersection_volume = 0.0

    for linked_id, linked_data in linked_columns_dict.items():
        linked_solid = linked_data['solid']
        if not linked_solid:
            continue

        try:
            intersection_solid = BooleanOperationsUtils.ExecuteBooleanOperation(host_solid, linked_solid, BooleanOperationsType.Intersect)
            if intersection_solid and intersection_solid.Volume > max_intersection_volume:
                max_intersection_volume = intersection_solid.Volume
                best_match = linked_data['element']
        except Exception as e:
            logger.debug("Boolean op failed between host and linked {}: {}".format(linked_id, e))
            continue

    return best_match

def get_type_info(column):
    """Retrieves type information for a column."""
    try:
        type_id = column.GetTypeId()
        if type_id:
            col_type = column.Document.GetElement(type_id)
            if col_type and hasattr(col_type, 'Family'):
                return {
                    'type_name': col_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString(),
                    'family_name': col_type.Family.Name,
                    'family_symbol': col_type
                }
    except Exception as e:
        logger.debug("Failed to get type info for column {}: {}".format(column.Id, e))
    return None

def find_matching_type_in_host(host_doc, family_name, type_name):
    """Finds a matching family type in the host document."""
    all_symbols = FilteredElementCollector(host_doc).OfClass(FamilySymbol).WhereElementIsElementType().ToElements()
    for symbol in all_symbols:
        try:
            if symbol.Family.Name == family_name and symbol.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == type_name:
                return symbol
        except:
            continue
    return None

def disable_element_joins(doc, element):
    """Disables all joins for a given element."""
    joined_ids = JoinGeometryUtils.GetJoinedElements(doc, element)
    for joined_id in joined_ids:
        joined_element = doc.GetElement(joined_id)
        if JoinGeometryUtils.AreElementsJoined(doc, element, joined_element):
            JoinGeometryUtils.UnjoinGeometry(doc, element, joined_element)

def process_batch(matches_batch):
    """Processes a batch of type transfers (transaction handled externally)."""
    successful = []
    failed = []
    for host_column, linked_column in matches_batch:
        if config.get('disable_joins'):
            disable_element_joins(doc, host_column)

        linked_type_info = get_type_info(linked_column)
        host_type_info = get_type_info(host_column)

        if not linked_type_info:
            failed.append((host_column, linked_column, host_type_info, None))
            continue

        target_type = find_matching_type_in_host(doc, linked_type_info['family_name'], linked_type_info['type_name'])
        if target_type:
            try:
                host_column.ChangeTypeId(target_type.Id)
                successful.append((host_column, linked_column, host_type_info, linked_type_info))
            except Exception as e:
                logger.error("Failed to change type for {}: {}".format(host_column.Id, e))
                failed.append((host_column, linked_column, host_type_info, linked_type_info))
        else:
            failed.append((host_column, linked_column, host_type_info, linked_type_info))
    return successful, failed

def export_to_csv(successful, failed, unmatched, doc_title):
    """Exports the results to a CSV file."""
    if not config.get('export_results_to_csv'):
        return None

    output_dir = config.get('csv_base_dir')
    if config.get('csv_create_folders') and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = "MatchingColumn_v2_{}_{}.csv".format(doc_title, timestamp)
    filepath = os.path.join(output_dir, filename)

    try:
        with io.open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Status', 'Host Column ID', 'Old Type', 'Linked Column ID', 'New Type', 'Family Name'])

            for hc, lc, old_info, new_info in successful:
                writer.writerow(['SUCCESS', hc.Id, old_info['type_name'] if old_info else 'N/A', lc.Id, new_info['type_name'], new_info['family_name']])
            for hc, lc, old_info, new_info in failed:
                writer.writerow(['FAIL', hc.Id, old_info['type_name'] if old_info else 'N/A', lc.Id if lc else 'N/A', new_info['type_name'] if new_info else 'N/A', new_info['family_name'] if new_info else 'N/A'])
            for hc in unmatched:
                writer.writerow(['UNMATCHED', hc.Id, get_type_info(hc)['type_name'] if get_type_info(hc) else 'N/A', '', '', ''])
        return filepath
    except Exception as e:
        logger.error("Failed to export CSV: {}".format(e))
        return None

def main():
    """Main script execution."""
    output_lines = []

    # Show config dialog if shift is pressed
    try:
        if script.get_shift_key_state():
            dialog = ConfigDialog(config)
            dialog.ShowDialog()
    except AttributeError:
        # Fallback for older pyRevit versions that don't have get_shift_key_state
        pass

    output_lines.append("# Matching Dimension Column v2")
    output_lines.append("---")

    link_doc, selected_link = select_linked_model()
    output_lines.append("Linked Model: **{}**".format(link_doc.Title))

    host_columns = collect_columns(doc, is_host=True)
    linked_columns = collect_columns(link_doc, is_host=False)

    if not host_columns or not linked_columns:
        forms.alert("No columns found in host or linked model.", exitscript=True)

    output_lines.append("Host Columns: **{}** | Linked Columns: **{}**".format(len(host_columns), len(linked_columns)))
    output_lines.append("---")

    output_lines.append("## Processing Geometry...")
    linked_columns_dict = {c.Id: {'element': c, 'solid': get_solid(c)} for c in linked_columns}
    output_lines.append("✓ Linked column geometry cached.")

    output_lines.append("## Finding Matches...")
    matches = []
    unmatched = []

    for hc in host_columns:
        host_solid = get_solid(hc)
        best_match = find_best_match(host_solid, linked_columns_dict)
        if best_match:
            matches.append((hc, best_match))
        else:
            unmatched.append(hc)
    output_lines.append("✓ Matching complete. Found **{}** matches.".format(len(matches)))
    output_lines.append("---")

    output_lines.append("## Transferring Column Types...")
    batch_size = config.get('batch_size')
    num_batches = (len(matches) + batch_size - 1) // batch_size
    successful_transfers = []
    failed_transfers = []

    # Process transfers with progress bar inside transaction (like ClearColumnComments)
    with Transaction(doc, 'Transfer Column Type Marks and Marks v2') as t:
        t.Start()

        with ProgressBar(title='Transferring Types (Batch {value} of {max_value})',
                        cancellable=False) as pb:

            for i in range(num_batches):
                start = i * batch_size
                end = start + batch_size
                batch = matches[start:end]
                if config.get('enable_progress_detail'):
                    output_lines.append("Processing Batch {}/{} ({} elements)".format(i + 1, num_batches, len(batch)))

                successful, failed = process_batch(batch)
                successful_transfers.extend(successful)
                failed_transfers.extend(failed)
                pb.update_progress(i + 1, num_batches)

        # Print results BEFORE commit
        output_lines.append("---")
        output_lines.append("## Results Summary")
        output_lines.append("- Successful Transfers: **{}**".format(len(successful_transfers)))
        output_lines.append("- Failed Transfers: **{}**".format(len(failed_transfers)))
        output_lines.append("- Unmatched Columns: **{}**".format(len(unmatched)))

        csv_path = export_to_csv(successful_transfers, failed_transfers, unmatched, doc.Title)
        if csv_path:
            output_lines.append("Full results exported to: `{}`".format(csv_path))

        output_lines.append("---")
        output_lines.append("\\n💾 **Saving changes...**")

        status = t.Commit()

        if status != TransactionStatus.Committed:
            logger.warning("Transaction was not committed successfully")
            forms.alert("Failed to update column marks. Please try again.", exitscript=True)

    # Final output - only print once after transaction is complete
    for line in output_lines:
        output.print_md(line)

    if config.get('cleanup_geometry_cache'):
        del linked_columns_dict
        gc.collect()
        output.print_md("✓ Geometry cache cleared.")

    alert_message = "Column Type Transfer Complete!\n\n"
    alert_message += "Successful: {} columns\n".format(len(successful_transfers))
    alert_message += "Failed: {} columns\n".format(len(failed_transfers))
    alert_message += "Unmatched: {} columns\n".format(len(unmatched))

    if csv_path:
        alert_message += "\n\nDetailed results: {}".format(os.path.basename(csv_path))

    forms.alert(alert_message, title="Transfer Complete")

if __name__ == '__main__':
    main()