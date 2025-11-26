# -*- coding: utf-8 -*-
__title__ = 'Matching Dimension from EXR Geometry'
__author__ = 'PrasKaa'
__doc__ = "Matches beams by geometry intersection and transfers family types from linked EXR model " \
          "to synchronize beam dimensions between analytical and documentation models."

import re
import gc
import csv
import os
import io
import logging
from datetime import datetime
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
    Transform,
    GeometryInstance,
    FamilySymbol,
    Family,
    BuiltInParameter,
    JoinGeometryUtils,
    Options,
    SubTransaction
)
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons

from pyrevit import revit, forms, script
from pyrevit.forms import ProgressBar
from matching_config import *

# Script-specific configuration
SCRIPT_SUBFOLDER = "Matching Framing"  # Subfolder for CSV outputs

# Setup
doc = revit.doc
uidoc = revit.uidoc
logger = script.get_logger()
# Reduce logging verbosity for cleaner output
logger.setLevel(logging.WARNING)  # Only show warnings and errors
output = script.get_output()

# Revit API Options for geometry extraction
app = doc.Application
options = app.Create.NewGeometryOptions()
active_view = doc.ActiveView
if active_view:
    options.View = active_view
else:
    # If no active view, find any 3D view to get geometry
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
            # Handle geometry instances (common for families)
            instance_geom = geom_obj.GetInstanceGeometry()
            if instance_geom:
                for inst_obj in instance_geom:
                    if isinstance(inst_obj, Solid) and inst_obj.Volume > 0:
                        solids.append(inst_obj)

    if not solids:
        return None

    # If multiple solids exist, unite them into a single solid for accurate volume calculations
    if len(solids) > 1:
        main_solid = solids[0]
        for s in solids[1:]:
            try:
                # Perform Boolean union to combine solids
                main_solid = BooleanOperationsUtils.ExecuteBooleanOperation(main_solid, s, BooleanOperationsType.Union)
            except Exception as e:
                logger.warning("Could not unite solids for element {}. Error: {}".format(element.Id, e))
        return main_solid
    return solids[0]


def select_linked_model():
    """
    Prompts the user to select a linked EXR model from available Revit links.

    Returns:
        tuple: (link_doc, selected_link)
            - link_doc: The Document object of the selected linked model.
            - selected_link: The RevitLinkInstance object of the selected link.

    Raises:
        SystemExit: If no links are found or no link is selected.
    """
    link_instances = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()
    if not link_instances:
        forms.alert("No Revit links found in the current project.", exitscript=True)

    # Create a dictionary of link instances for selection
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
        forms.alert("Could not access the document of the selected link. Ensure it is loaded.", exitscript=True)

    return link_doc, selected_link


def collect_host_beams():
    """
    Collects structural framing elements (beams) from the host Revit model.

    If elements are pre-selected by the user, uses those; otherwise, collects all
    structural framing elements in the project.

    Returns:
        list: List of Element objects representing beams in the host model.

    Raises:
        SystemExit: If no beams are found in the selection or project.
    """
    selection_ids = uidoc.Selection.GetElementIds()
    host_beams = []

    if selection_ids:
        # If user has pre-selected elements, use them
        for elem_id in selection_ids:
            elem = doc.GetElement(elem_id)
            # Make sure the selected element is a Structural Framing element
            if elem.Category and elem.Category.Id == BuiltInCategory.OST_StructuralFraming:
                host_beams.append(elem)

        if not host_beams:
            forms.alert("Tidak ada elemen balok (Structural Framing) yang ditemukan dalam seleksi Anda. "
                        "Silakan pilih beberapa balok dan coba lagi.", exitscript=True)
    else:
        # If nothing is selected, get all structural framing in the project
        host_beams = FilteredElementCollector(doc)\
            .OfCategory(BuiltInCategory.OST_StructuralFraming)\
            .WhereElementIsNotElementType()\
            .ToElements()

    return host_beams


def collect_linked_beams(link_doc):
    """
    Collects structural framing elements (beams) from the linked EXR model.

    Args:
        link_doc (Document): The document object of the linked Revit model.

    Returns:
        list: List of Element objects representing beams in the linked model.
    """
    linked_beams = FilteredElementCollector(link_doc)\
        .OfCategory(BuiltInCategory.OST_StructuralFraming)\
        .WhereElementIsNotElementType()\
        .ToElements()

    return linked_beams


def find_best_match(host_beam, linked_beams_dict):
    """
    Finds the best matching linked beam for a host beam based on geometric intersection volume.

    This function calculates the solid geometry of the host beam and compares it against
    all linked beams by computing Boolean intersection volumes. The linked beam with the
    largest intersection volume is considered the best match.

    Args:
        host_beam (Element): The structural framing element in the host model to match.
        linked_beams_dict (dict): Dictionary mapping ElementId to {'element': Element, 'solid': Solid}
            for beams in the linked model.

    Returns:
        Element or None: The best matching beam from the linked model, or None if no valid
            intersection is found or if geometry extraction fails.
    """
    host_solid = get_solid(host_beam)
    if not host_solid:
        logger.debug("Could not get solid for host beam {}".format(host_beam.Id))
        return None

    best_match = None
    max_intersection_volume = 0.0

    for linked_beam_id, linked_beam_data in linked_beams_dict.items():
        linked_solid = linked_beam_data['solid']
        if not linked_solid:
            continue

        try:
            # Calculate intersection
            intersection_solid = BooleanOperationsUtils.ExecuteBooleanOperation(
                host_solid, linked_solid, BooleanOperationsType.Intersect
            )

            # Compare volume
            if intersection_solid and intersection_solid.Volume > max_intersection_volume:
                max_intersection_volume = intersection_solid.Volume
                best_match = linked_beam_data['element']

        except Exception as e:
            # This can fail if solids are disjoint or have issues
            logger.debug("Boolean operation failed between host {} and linked {}. Error: {}".format(
                host_beam.Id, linked_beam_id, e))
            continue

    return best_match


def get_family_type(beam):
    """
    Retrieves the FamilySymbol (family type) of a given beam element.

    Args:
        beam (Element): The structural framing element to get the type for.

    Returns:
        FamilySymbol or None: The family symbol of the beam, or None if not found.
    """
    try:
        beam_type_id = beam.GetTypeId()
        if beam_type_id:
            beam_type = beam.Document.GetElement(beam_type_id)
            if beam_type and hasattr(beam_type, 'Family') and beam_type.Family and hasattr(beam_type.Family, 'Name'):
                return beam_type
    except Exception as e:
        logger.debug("Failed to get family type for beam {}. Error: {}".format(beam.Id, e))
    return None


def get_type_info_from_parameters(beam):
    """
    Extracts type information from beam parameters as a fallback method.

    Attempts to retrieve type and family names using built-in parameters when
    direct FamilySymbol access fails.

    Args:
        beam (Element): The beam element to extract type info from.

    Returns:
        dict or None: Dictionary with 'type_name' and 'family_name' keys, or None
            if parameters are not available or invalid.
    """
    try:
        type_param = beam.get_Parameter(BuiltInParameter.ELEM_TYPE_PARAM)
        logger.debug("Beam {} ELEM_TYPE_PARAM: {} (has value: {})".format(
            beam.Id, type_param, type_param and type_param.AsString()))

        if type_param and type_param.AsString():
            type_name = type_param.AsString()
            logger.debug("Type name from parameter: '{}'".format(type_name))

            # Try to get family name from other parameters or parse from type name
            family_param = beam.get_Parameter(BuiltInParameter.ELEM_FAMILY_PARAM)
            logger.debug("Beam {} ELEM_FAMILY_PARAM: {} (has value: {})".format(
                beam.Id, family_param, family_param and family_param.AsString()))

            if family_param and family_param.AsString():
                family_name = family_param.AsString()
                logger.debug("Family name from parameter: '{}'".format(family_name))
            else:
                # For structural framing, family name might be embedded in type name
                # or we can assume it's a standard family
                family_name = "Concrete-Rectangular Beam"  # Default assumption
                logger.debug("Using default family name: '{}'".format(family_name))

            return {
                'type_name': type_name,
                'family_name': family_name
            }
        else:
            logger.debug("No valid type parameter found for beam {}".format(beam.Id))
    except Exception as e:
        logger.debug("Failed to get type info from parameters for beam {}. Error: {}".format(beam.Id, e))
    return None


def get_linked_beam_type_info(beam):
    """
    Retrieves comprehensive type information from a linked beam using multiple fallback approaches.

    Attempts to get type info through FamilySymbol access first, then parameter-based methods,
    and finally uses the beam's Name property as a last resort.

    Args:
        beam (Element): The beam element from the linked model.

    Returns:
        dict or None: Dictionary with 'type_name', 'family_name', and 'family_symbol' keys,
            or None if no type information can be extracted.
    """
    logger.debug("Getting type info for linked beam {}".format(beam.Id))

    # First try the standard approach
    family_symbol = get_family_type(beam)
    logger.debug("Family symbol result: {}".format(family_symbol))

    if family_symbol and hasattr(family_symbol, 'Name') and hasattr(family_symbol, 'Family') and family_symbol.Family and hasattr(family_symbol.Family, 'Name'):
        logger.debug("Using FamilySymbol approach for beam {}".format(beam.Id))
        return {
            'type_name': family_symbol.Name,
            'family_name': family_symbol.Family.Name,
            'family_symbol': family_symbol
        }

    # Fallback to parameter-based approach
    logger.debug("Trying parameter-based approach for beam {}".format(beam.Id))
    param_info = get_type_info_from_parameters(beam)
    logger.debug("Parameter info result: {}".format(param_info))

    if param_info:
        logger.debug("Using parameter-based approach for beam {}".format(beam.Id))
        return {
            'type_name': param_info['type_name'],
            'family_name': param_info['family_name'],
            'family_symbol': None  # No actual FamilySymbol object
        }

    # Last resort: try to use beam.Name as type name
    logger.debug("Trying beam.Name approach for beam {}".format(beam.Id))
    if hasattr(beam, 'Name') and beam.Name:
        logger.debug("Using beam.Name '{}' as type name for beam {}".format(beam.Name, beam.Id))
        return {
            'type_name': beam.Name,
            'family_name': "Concrete-Rectangular Beam",  # Default assumption
            'family_symbol': None
        }

    logger.debug("No type info found for linked beam {}".format(beam.Id))
    return None


def get_host_beam_type_info(beam):
    """
    Retrieves comprehensive type information from a host beam using multiple fallback approaches.

    Similar to get_linked_beam_type_info but for beams in the host document.

    Args:
        beam (Element): The beam element from the host model.

    Returns:
        dict or None: Dictionary with 'type_name', 'family_name', and 'family_symbol' keys,
            or None if no type information can be extracted.
    """
    logger.debug("Getting type info for host beam {}".format(beam.Id))

    # First try the standard approach
    family_symbol = get_family_type(beam)
    logger.debug("Host beam family symbol result: {}".format(family_symbol))

    if family_symbol and hasattr(family_symbol, 'Name') and hasattr(family_symbol, 'Family') and family_symbol.Family and hasattr(family_symbol.Family, 'Name'):
        logger.debug("Using FamilySymbol approach for host beam {}".format(beam.Id))
        return {
            'type_name': family_symbol.Name,
            'family_name': family_symbol.Family.Name,
            'family_symbol': family_symbol
        }

    # Fallback to parameter-based approach
    logger.debug("Trying parameter-based approach for host beam {}".format(beam.Id))
    param_info = get_type_info_from_parameters(beam)
    logger.debug("Host beam parameter info result: {}".format(param_info))

    if param_info:
        logger.debug("Using parameter-based approach for host beam {}".format(beam.Id))
        return {
            'type_name': param_info['type_name'],
            'family_name': param_info['family_name'],
            'family_symbol': None  # No actual FamilySymbol object
        }

    # Last resort: try to use beam.Name as type name
    logger.debug("Trying beam.Name approach for host beam {}".format(beam.Id))
    if hasattr(beam, 'Name') and beam.Name:
        logger.debug("Using beam.Name '{}' as type name for host beam {}".format(beam.Name, beam.Id))
        return {
            'type_name': beam.Name,
            'family_name': "Concrete-Rectangular Beam",  # Default assumption
            'family_symbol': None
        }

    logger.debug("No type info found for host beam {}".format(beam.Id))
    return None


def check_family_type_exists(host_doc, family_name, type_name):
    """
    Checks if a specific family and type exist in the host Revit document.

    Searches through all FamilySymbol elements to find a match for the given
    family name and type name combination.

    Args:
        host_doc (Document): The host Revit document to search in.
        family_name (str): The name of the family to look for.
        type_name (str): The name of the type within the family.

    Returns:
        FamilySymbol or None: The matching FamilySymbol if found, None otherwise.
    """
    if not family_name or not type_name:
        return None

    # Method 1: Direct approach using FilteredElementCollector for FamilySymbol
    all_symbols = FilteredElementCollector(host_doc).OfClass(FamilySymbol).WhereElementIsElementType().ToElements()

    found_families = set()
    found_types = []

    for symbol in all_symbols:
        try:
            # Get family info
            if not (symbol and hasattr(symbol, 'Family') and symbol.Family):
                continue
            
            family = symbol.Family
            if not hasattr(family, 'Name'):
                continue
                
            current_family_name = family.Name
            found_families.add(current_family_name)
            
            # Check if this is the family we're looking for
            if current_family_name == family_name:
                # Attempt to retrieve the symbol name using multiple methods due to API inconsistencies
                symbol_name = None

                # First attempt: Direct property access (most reliable)
                if hasattr(symbol, 'Name'):
                    try:
                        symbol_name = symbol.Name
                    except:
                        pass

                # Second attempt: Use SYMBOL_NAME_PARAM built-in parameter
                if not symbol_name:
                    try:
                        name_param = symbol.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
                        if name_param and name_param.HasValue:
                            symbol_name = name_param.AsString()
                    except:
                        pass

                # Third attempt: Use ALL_MODEL_TYPE_NAME parameter as final fallback
                if not symbol_name:
                    try:
                        name_param = symbol.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
                        if name_param and name_param.HasValue:
                            symbol_name = name_param.AsString()
                    except:
                        pass
                
                if symbol_name:
                    found_types.append(symbol_name)
                    
                    # Check if this matches our target type
                    if symbol_name == type_name:
                        return symbol
        
        except Exception as e:
            continue

    # Only log if type not found (for debugging failed transfers)
    if family_name in found_families and found_types:
        logger.debug("Type '{}' not found in family '{}'. Available: {}".format(
            type_name, family_name, found_types[:10]))
    elif family_name not in found_families:
        logger.debug("Family '{}' not found in host document.".format(family_name))

    return None

def transfer_family_type(host_beam, linked_type_info, host_doc):
    """
    Transfers the family type from a linked beam to a host beam.

    Changes the type of the host beam to match the linked beam's type, provided
    the target type exists in the host document. Also sets a comments parameter
    to track the change.

    Args:
        host_beam (Element): The beam element in the host model to modify.
        linked_type_info (dict): Type information from the linked beam containing
            'type_name', 'family_name', and optionally 'family_symbol'.
        host_doc (Document): The host Revit document.

    Returns:
        tuple: (success, old_type_info, new_type_info)
            - success (bool): True if the type transfer succeeded.
            - old_type_info (dict): Type information before the change.
            - new_type_info (dict): Type information after the change (or target info if failed).
    """
    try:
        if not linked_type_info:
            logger.warning("No type info available for beam {}".format(host_beam.Id))
            return False, None, None

        type_name = linked_type_info.get('type_name')
        family_name = linked_type_info.get('family_name')
        family_symbol = linked_type_info.get('family_symbol')

        if not type_name or not family_name:
            logger.warning("Missing type name or family name for beam {}".format(host_beam.Id))
            return False, None, None

        # CAPTURE OLD TYPE INFO BEFORE ANY CHANGES
        old_type_info = get_host_beam_type_info(host_beam)
        if old_type_info:
            logger.debug("Old type for host beam {}: '{}' from family '{}'".format(
                host_beam.Id, old_type_info.get('type_name', 'Unknown'), old_type_info.get('family_name', 'Unknown')))
        else:
            logger.warning("Could not capture old type info for host beam {}".format(host_beam.Id))

        # Check if the family and type exist in host document
        existing_type = check_family_type_exists(host_doc, family_name, type_name)

        if existing_type:
            # Check if type actually needs to change
            type_changed = False
            if old_type_info and old_type_info.get('type_name') != type_name:
                # Type exists and is different, change the beam type
                host_beam.ChangeTypeId(existing_type.Id)
                type_changed = True
                logger.debug("Successfully changed type for host beam {} from '{}' to '{}'".format(
                    host_beam.Id,
                    old_type_info.get('type_name', 'Unknown') if old_type_info else 'Unknown',
                    type_name))
            elif not old_type_info:
                # No old type info available, assume change is needed
                host_beam.ChangeTypeId(existing_type.Id)
                type_changed = True
                logger.debug("Changed type for host beam {} to '{}' (no old type info available)".format(
                    host_beam.Id, type_name))
            else:
                logger.debug("Beam {} already has correct type '{}', no change needed".format(
                    host_beam.Id, type_name))

            # SET COMMENTS PARAMETER ONLY IF TYPE ACTUALLY CHANGED
            if type_changed:
                try:
                    comments_param = host_beam.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
                    if comments_param and not comments_param.IsReadOnly:
                        comments_param.Set("Change Dimension Type")
                        logger.debug("Set Comments parameter to 'Change Dimension Type' for beam {}".format(host_beam.Id))
                    else:
                        logger.warning("Could not set Comments parameter for beam {} (parameter not found or read-only)".format(host_beam.Id))
                except Exception as e:
                    logger.warning("Failed to set Comments parameter for beam {}. Error: {}".format(host_beam.Id, e))

            return True, old_type_info, linked_type_info
        else:
            # Type doesn't exist - for now, we'll skip (could add family loading later)
            return False, old_type_info, linked_type_info

    except Exception as e:
        logger.error("Failed to transfer type to beam {}. Error: {}".format(host_beam.Id, e))
        return False, None, None


def disable_all_joins_in_elements(elements, doc):
    """
    Disables all automatic joins for the given elements to prevent cascading join/unjoin operations.
    
    Args:
        elements (list): List of elements to disable joins for
        doc (Document): The Revit document
        
    Returns:
        int: Number of joins disabled
    """
    joins_disabled = 0
    for elem in elements:
        try:
            # Get all elements joined to this element
            joined_elements = JoinGeometryUtils.GetJoinedElements(doc, elem)
            for joined_elem_id in joined_elements:
                try:
                    joined_elem = doc.GetElement(joined_elem_id)
                    if joined_elem and JoinGeometryUtils.AreElementsJoined(doc, elem, joined_elem):
                        JoinGeometryUtils.UnjoinGeometry(doc, elem, joined_elem)
                        joins_disabled += 1
                except Exception as e:
                    logger.debug("Could not unjoin element {} from {}. Error: {}".format(
                        elem.Id, joined_elem_id, e))
        except Exception as e:
            logger.debug("Could not process joins for element {}. Error: {}".format(elem.Id, e))
    
    return joins_disabled


def cleanup_geometry_cache(linked_beams_dict):
    """
    Cleans up cached geometry data to free memory.
    
    Args:
        linked_beams_dict (dict): Dictionary containing cached solid geometries
    """
    if CLEANUP_GEOMETRY_CACHE:
        # Clear solid references
        for beam_data in linked_beams_dict.values():
            beam_data['solid'] = None
        
        # Clear the dictionary
        linked_beams_dict.clear()
        
        # Force garbage collection
        gc.collect()
        logger.info("Geometry cache cleared, memory freed")


def get_csv_output_path():
    """
    Gets the organized output path for CSV files.
    Now uses the same Documents path detection as hooks for consistency.

    Returns:
        str: Path to the script-specific output directory
    """
    # CSV_BASE_DIR now contains full path from config
    base_path = CSV_BASE_DIR
    script_path = os.path.join(base_path, SCRIPT_SUBFOLDER)

    # Auto-create folders if they don't exist
    if CSV_CREATE_FOLDERS:
        if not os.path.exists(base_path):
            os.makedirs(base_path)
        if not os.path.exists(script_path):
            os.makedirs(script_path)

    return script_path


def export_results_to_csv(successful_transfers, failed_transfers, unmatched, doc_title):
    """
    Exports transfer results to a CSV file to avoid overloading output window.

    Args:
        successful_transfers (list): List of successful transfer tuples
        failed_transfers (list): List of failed transfer tuples
        unmatched (list): List of unmatched beams
        doc_title (str): Document title for filename

    Returns:
        str: Path to the exported CSV file, or None if export failed
    """
    try:
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_doc_title = "".join(c for c in doc_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = "MatchingDimension_{}_{}.csv".format(safe_doc_title, timestamp)

        # Get organized output path
        output_dir = get_csv_output_path()
        filepath = os.path.join(output_dir, filename)
        
        # Write CSV
        with io.open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['Category', 'Host Beam ID', 'Old Type', 'New Type', 'Linked Beam ID', 'Family Name', 'Status'])
            
            # Write successful transfers
            for host_beam, linked_beam, old_type_info, new_type_info in successful_transfers:
                old_type_name = old_type_info.get('type_name', 'N/A') if old_type_info else 'N/A'
                new_type_name = new_type_info.get('type_name', 'N/A') if new_type_info else 'N/A'
                family_name = new_type_info.get('family_name', 'N/A') if new_type_info else 'N/A'

                writer.writerow([
                    'Successful',
                    str(host_beam.Id),
                    old_type_name,
                    new_type_name,
                    str(linked_beam.Id),
                    family_name,
                    'SUCCESS'
                ])
            
            # Write failed transfers
            for host_beam, linked_beam, old_type_info, new_type_info in failed_transfers:
                old_type_name = old_type_info.get('type_name', 'N/A') if old_type_info else 'N/A'
                target_type_name = new_type_info.get('type_name', 'No Type') if new_type_info else 'No Type'
                family_name = new_type_info.get('family_name', 'N/A') if new_type_info else 'N/A'

                writer.writerow([
                    'Failed',
                    str(host_beam.Id),
                    old_type_name,
                    target_type_name,
                    str(linked_beam.Id) if linked_beam else 'N/A',
                    family_name,
                    'FAILED'
                ])
            
            # Write unmatched beams
            for beam in unmatched:
                writer.writerow([
                    'Unmatched',
                    str(beam.Id),
                    beam.Name,
                    'N/A',
                    'N/A',
                    'N/A',
                    'UNMATCHED'
                ])
        
        logger.info("Results exported to: {}".format(filepath))
        return filepath
        
    except Exception as e:
        logger.error("Failed to export results to CSV: {}".format(e))
        return None


def process_batch_transfers(doc, matches_batch, batch_number, total_batches):
    """
    Processes a batch of beam type transfers within a single transaction.

    Args:
        doc (Document): The host Revit document
        matches_batch (list): List of (host_beam, linked_beam) tuples for this batch
        batch_number (int): Current batch number
        total_batches (int): Total number of batches

    Returns:
        tuple: (successful_transfers, failed_transfers) lists
    """
    successful = []
    failed = []

    transaction_name = 'Transfer Beam Types - Batch {}/{}'.format(batch_number, total_batches)

    try:
        with Transaction(doc, transaction_name) as t:
            t.Start()

            # Disable joins for all elements in this batch first (CRITICAL OPTIMIZATION)
            host_beams_in_batch = [host_beam for host_beam, _ in matches_batch]
            if DISABLE_JOINS:
                joins_disabled = disable_all_joins_in_elements(host_beams_in_batch, doc)

            # Process each match in the batch
            for i, (host_beam, linked_beam) in enumerate(matches_batch):
                try:
                    linked_type_info = get_linked_beam_type_info(linked_beam)

                    if linked_type_info:
                        success, old_type_info, new_type_info = transfer_family_type(
                            host_beam, linked_type_info, doc
                        )

                        if success:
                            successful.append((host_beam, linked_beam, old_type_info, new_type_info))
                        else:
                            failed.append((host_beam, linked_beam, old_type_info, new_type_info))
                    else:
                        failed.append((host_beam, linked_beam, None, None))

                except Exception as e:
                    failed.append((host_beam, linked_beam, None, None))

            # Commit the transaction
            status = t.Commit()

            if status != TransactionStatus.Committed:
                logger.warning("Batch {} transaction was not committed successfully".format(batch_number))
                # Move all successful to failed
                failed.extend(successful)
                successful = []

    except Exception as e:
        logger.error("Critical error in batch {}: {}".format(batch_number, e))
        # All items in this batch failed
        failed.extend([(hb, lb, None, None) for hb, lb in matches_batch])
        successful = []

    # Force garbage collection after each batch
    gc.collect()

    return successful, failed


def process_batch_transfers_no_transaction(doc, matches_batch, batch_number, total_batches):
    """
    Processes a batch of beam type transfers WITHOUT creating its own transaction.
    Used when all batches are processed within a single master transaction.

    Args:
        doc (Document): The host Revit document
        matches_batch (list): List of (host_beam, linked_beam) tuples for this batch
        batch_number (int): Current batch number
        total_batches (int): Total number of batches

    Returns:
        tuple: (successful_transfers, failed_transfers) lists
    """
    successful = []
    failed = []

    try:
        # Disable joins for all elements in this batch first (CRITICAL OPTIMIZATION)
        host_beams_in_batch = [host_beam for host_beam, _ in matches_batch]
        if DISABLE_JOINS:
            joins_disabled = disable_all_joins_in_elements(host_beams_in_batch, doc)

        # Process each match in the batch
        for i, (host_beam, linked_beam) in enumerate(matches_batch):
            try:
                linked_type_info = get_linked_beam_type_info(linked_beam)

                if linked_type_info:
                    success, old_type_info, new_type_info = transfer_family_type(
                        host_beam, linked_type_info, doc
                    )

                    if success:
                        successful.append((host_beam, linked_beam, old_type_info, new_type_info))
                    else:
                        failed.append((host_beam, linked_beam, old_type_info, new_type_info))
                else:
                    failed.append((host_beam, linked_beam, None, None))

            except Exception as e:
                failed.append((host_beam, linked_beam, None, None))

    except Exception as e:
        logger.error("Critical error in batch {}: {}".format(batch_number, e))
        # All items in this batch failed
        failed.extend([(hb, lb, None, None) for hb, lb in matches_batch])
        successful = []

    # Force garbage collection after each batch
    gc.collect()

    return successful, failed


def main():
    """
    Main execution function that orchestrates the beam type transfer process.

    Handles the complete workflow from model selection through results reporting,
    including error handling and user feedback.
    """
    # Step 1: Select the linked EXR model from available Revit links
    link_doc, selected_link = select_linked_model()

    # For now, coordinate transformation is disabled (can be enabled in future versions)
    use_transform = False
    link_transform = None

    # Step 2: Gather structural framing elements from both host and linked models
    host_beams = collect_host_beams()
    linked_beams = collect_linked_beams(link_doc)

    if not host_beams or not linked_beams:
        forms.alert("No structural framing elements found in the host or linked model.", exitscript=True)

    # Step 3: Extract and cache solid geometries for linked beams to optimize matching performance
    with ProgressBar(title='Processing Beam Geometry ({value} of {max_value})',
                     cancellable=True) as pb:

        linked_beams_dict = {}
        for i, beam in enumerate(linked_beams):
            if pb.cancelled:
                forms.alert("Geometry processing was cancelled. Script will exit.", exitscript=True)

            solid = get_solid(beam)
            if solid:
                linked_beams_dict[beam.Id] = {'element': beam, 'solid': solid}

            # Update progress
            pb.update_progress(i + 1, len(linked_beams))

    # Step 4: Match host beams to linked beams by calculating geometric intersections
    matches = []
    unmatched = []

    with ProgressBar(title='Finding Geometry Matches ({value} of {max_value})',
                     cancellable=True) as pb:

        for i, host_beam in enumerate(host_beams):
            if pb.cancelled:
                forms.alert("Matching process was cancelled. Script will exit.", exitscript=True)

            best_match = find_best_match(host_beam, linked_beams_dict)

            if best_match:
                matches.append((host_beam, best_match))
            else:
                unmatched.append(host_beam)

            # Update progress
            pb.update_progress(i + 1, len(host_beams))

    if not matches:
        forms.alert("No matching beams found between the host and linked model.", exitscript=True)

    # Step 5: Apply type changes to matched host beams using batch processing (OPTIMIZED)
    successful_transfers = []
    failed_transfers = []

    # Calculate number of batches
    total_matches = len(matches)
    num_batches = (total_matches + BATCH_SIZE - 1) // BATCH_SIZE  # Ceiling division

    # Initialize progress tracking
    beams_processed = 0

    # Process ALL matches in a single transaction with per-beam progress
    # Manual transaction management for full control over commit timing
    master_transaction = Transaction(doc, 'Transfer All Beam Types')
    master_transaction.Start()

    try:
        # Progress bar only for batch processing (not including commit)
        with ProgressBar(title='Transferring Beam Types ({value} of {max_value})',
                         cancellable=True) as pb:

            # Process matches in batches (but within single transaction)
            for batch_num in range(num_batches):
                # Calculate batch range
                start_idx = batch_num * BATCH_SIZE
                end_idx = min(start_idx + BATCH_SIZE, total_matches)
                matches_batch = matches[start_idx:end_idx]

                # Process this batch WITHOUT creating sub-transactions
                batch_successful, batch_failed = process_batch_transfers_no_transaction(
                    doc, matches_batch, batch_num + 1, num_batches
                )

                # Accumulate results
                successful_transfers.extend(batch_successful)
                failed_transfers.extend(batch_failed)

                # Update progress per beam
                beams_processed += len(matches_batch)
                pb.update_progress(beams_processed, total_matches)

                # Check for cancellation
                if pb.cancelled:
                    master_transaction.RollBack()
                    forms.alert("Transfer process was cancelled. All changes have been rolled back.", exitscript=True)

        # DO NOT COMMIT HERE - will commit after all output is complete

    except Exception as e:
        master_transaction.RollBack()
        logger.error("Critical error during batch processing: {}".format(e))
        forms.alert("An error occurred during processing. All changes have been rolled back.", exitscript=True)

    # Clean up geometry cache to free memory
    if CLEANUP_GEOMETRY_CACHE:
        cleanup_geometry_cache(linked_beams_dict)

    # Export full results to CSV if enabled
    csv_path = None
    if EXPORT_RESULTS_TO_CSV:
        csv_path = export_results_to_csv(successful_transfers, failed_transfers, unmatched, doc.Title)

    # Results Summary
    output.print_md("##Results Summary")
    output.print_md("")
    output.print_md("**Total matches found:** {}".format(len(matches)))
    output.print_md("**Successful transfers:** {}".format(len(successful_transfers)))
    output.print_md("**Failed transfers:** {}".format(len(failed_transfers)))
    output.print_md("**Unmatched beams:** {}".format(len(unmatched)))

    # Add CSV path to console if available
    if csv_path:
        output.print_md("")
        output.print_md("**CSV Results:** {}".format(csv_path))

    # EXTRACT SUMMARY DATA BEFORE COMMIT to avoid "managed object is not valid" error
    summary_data = {
        'successful_count': len(successful_transfers),
        'failed_count': len(failed_transfers),
        'unmatched_count': len(unmatched),
        'csv_path': csv_path
    }

    # Commit the transaction AFTER all output is complete to prevent console splitting
    # Transaction is still active (not rolled back) if we reach this point
    status = master_transaction.Commit()
    if status == TransactionStatus.Committed:
        summary_data['commit_success'] = True
    else:
        logger.error("Master transaction failed to commit")
        summary_data['commit_success'] = False
        forms.alert("Failed to save beam type changes. Please try again.", exitscript=True)

    # Show completion dialog using TaskDialog (safe after transaction commit)
    alert_message = "Type transfer complete!\n"
    alert_message += "Successfully updated: {} beams\n".format(summary_data['successful_count'])
    alert_message += "Failed: {} beams\n".format(summary_data['failed_count'])
    if summary_data['unmatched_count'] > 0:
        alert_message += "Unmatched: {} beams\n".format(summary_data['unmatched_count'])

    TaskDialog.Show("Process Complete", alert_message, TaskDialogCommonButtons.Ok)


if __name__ == '__main__':
    main()