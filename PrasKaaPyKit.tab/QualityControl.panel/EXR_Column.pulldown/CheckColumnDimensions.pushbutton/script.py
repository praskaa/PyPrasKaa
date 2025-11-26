# -*- coding: utf-8 -*-
__title__ = 'Check Column Dimensions by EXR Geometry'
__author__ = 'PrasKaa+KiloCode'
__doc__ = "Validates column dimensions by geometry intersection and parameter comparison."

import gc
import csv
import os
import io
from datetime import datetime
from Autodesk.Revit.UI.Selection import ISelectionFilter, Selection, ObjectType
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    RevitLinkInstance,
    Solid,
    BooleanOperationsUtils,
    BooleanOperationsType,
    Transaction,
    TransactionStatus,
    View,
    ViewType,
    Element,
    Options,
    BuiltInParameter,
    StorageType,
    GeometryInstance
)

from pyrevit import revit, forms, script
from pyrevit.forms import ProgressBar

# Import parameter utilities from lib
try:
    from parameters.framework import find_parameter_element, get_parameter_type_info
except ImportError:
    # Fallback if import fails
    find_parameter_element = None
    get_parameter_type_info = None

# Import CSV configuration
try:
    from matching_config import CSV_BASE_DIR, CSV_CREATE_FOLDERS
except ImportError:
    CSV_BASE_DIR = os.path.expanduser("~/Desktop")
    CSV_CREATE_FOLDERS = True

# Import smart selection utility from lib
try:
    from Snippets.smart_selection import get_filtered_selection, create_single_category_filter
except ImportError:
    # Fallback if import fails
    get_filtered_selection = None
    create_single_category_filter = None

# Script configuration
SCRIPT_SUBFOLDER = "Check Column Dimensions"

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

# Setup
doc = revit.doc
uidoc = revit.uidoc
logger = script.get_logger()
output = script.get_output()

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


def collect_host_columns():
    """
    Collects structural column elements from the host Revit model using smart selection.

    Logic Flow:
    1. Check for pre-selected elements - if found, validate and use them
    2. If no pre-selected elements, automatically collect ALL structural columns
    3. Validate that selected/pre-selected elements are actually structural columns
    4. Provide clear error messages if no valid columns found

    Returns:
        list: List of Element objects representing columns in the host model.

    Raises:
        SystemExit: If no columns are found in the model.
    """
    # Step 1: Check for pre-selected elements
    selection_ids = uidoc.Selection.GetElementIds()
    pre_selected_elements = []

    if selection_ids:
        debug_log("Found {} pre-selected elements".format(len(selection_ids)), level='NORMAL')

        # Validate pre-selected elements are structural columns
        for elem_id in selection_ids:
            elem = doc.GetElement(elem_id)
            if elem and elem.Category:
                # Check if it's a structural column
                if elem.Category.Id == BuiltInCategory.OST_StructuralColumns:
                    pre_selected_elements.append(elem)
                    debug_log("Validated pre-selected column: ID={}".format(elem.Id), level='VERBOSE')
                else:
                    debug_log("Skipping non-column element: ID={}, Category={}".format(
                        elem.Id, elem.Category.Name), level='VERBOSE')

        if pre_selected_elements:
            debug_log("Using {} pre-selected structural columns".format(len(pre_selected_elements)), level='NORMAL')
            return pre_selected_elements
        else:
            debug_log("No valid structural columns found in pre-selection", level='NORMAL')

    # Step 2: No valid pre-selection or no selection at all - collect ALL structural columns
    debug_log("Collecting ALL structural columns from host model", level='NORMAL')

    all_columns = FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_StructuralColumns)\
        .WhereElementIsNotElementType()\
        .ToElements()

    if not all_columns:
        forms.alert("No structural column elements found in the host model. "
                   "Please ensure your model contains structural columns.", exitscript=True)

    debug_log("Collected {} structural columns from host model".format(len(all_columns)), level='NORMAL')

    # Log first few column IDs for verification
    if all_columns:
        sample_ids = [str(c.Id) for c in all_columns[:5]]
        debug_log("Sample column IDs: {}".format(", ".join(sample_ids)), level='VERBOSE')
        if len(all_columns) > 5:
            debug_log("... and {} more columns".format(len(all_columns) - 5), level='VERBOSE')

    return all_columns


def collect_linked_columns(link_doc):
    """
    Collects structural column elements from the linked EXR model.

    Args:
        link_doc (Document): The document object of the linked Revit model.

    Returns:
        list: List of Element objects representing columns in the linked model.
    """
    linked_columns = FilteredElementCollector(link_doc)\
        .OfCategory(BuiltInCategory.OST_StructuralColumns)\
        .WhereElementIsNotElementType()\
        .ToElements()

    return linked_columns


def feet3_to_mm3(volume_cu_ft):
    """Convert cubic feet to cubic millimeters for better readability."""
    # 1 cubic foot = 28,316,846.592 mm³
    return volume_cu_ft * 28316846.592


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


def get_column_dimensions(column):
    """
    Extracts dimension parameters from a column element.
    Returns dimensions in FEET (Revit internal units) - conversion to mm done in compare_dimensions.

    Args:
        column (Element): The column element to extract dimensions from.

    Returns:
        dict or None: Dictionary with dimension values, or None if parameters not found.
            Format: {'b': float, 'h': float, 'diameter': float, 'type': str}
            type can be: 'rectangular', 'square', 'circular', or 'unknown'
    """
    try:
        # Debug: Check if function is being called
        debug_log("DEBUG: get_column_dimensions called for column {}".format(column.Id), level='DIAGNOSTIC')

        # Debug: Log all available type parameters for first few columns
        debug_count = getattr(get_column_dimensions, '_debug_count', 0)
        if debug_count < 3:  # Show parameters for first 3 columns
            debug_log("DEBUG: Starting type parameter inspection for column {} (count: {})".format(column.Id, debug_count + 1), level='DIAGNOSTIC')

            # Check type parameters - show ALL of them
            debug_log("DEBUG: Type parameters:", level='DIAGNOSTIC')
            if column.Symbol:
                type_param_info = []
                for param in column.Symbol.Parameters:
                    param_name = param.Definition.Name
                    param_value = "N/A"
                    has_value = param.HasValue
                    try:
                        if param.StorageType == StorageType.Double:
                            if has_value:
                                param_value = "{:.6f}".format(param.AsDouble())
                            else:
                                param_value = "No value"
                        elif param.StorageType == StorageType.Integer:
                            if has_value:
                                param_value = str(param.AsInteger())
                            else:
                                param_value = "No value"
                        elif param.StorageType == StorageType.String:
                            if has_value:
                                param_value = param.AsString()[:30] + "..." if len(param.AsString()) > 30 else param.AsString()
                            else:
                                param_value = "No value"
                        else:
                            param_value = "Other type"
                    except Exception as e:
                        param_value = "Error: {}".format(str(e))
                    type_param_info.append("{}: {}".format(param_name, param_value))
                debug_log("DEBUG: All type parameters: {}".format(", ".join(type_param_info)), level='DIAGNOSTIC')
            else:
                debug_log("DEBUG: No symbol/type found for column", level='DIAGNOSTIC')

            debug_log("DEBUG: Type parameter inspection complete for column {}".format(column.Id), level='DIAGNOSTIC')
            get_column_dimensions._debug_count = debug_count + 1

        # Try to get 'b' parameter (width/depth) - check both instance and type parameters
        b_param = column.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_WIDTH)
        if not b_param or not b_param.HasValue:
            # Check instance level first
            b_param = column.LookupParameter("b") or column.LookupParameter("B") or column.LookupParameter("Width")
            # If not found in instance, check type level
            if not b_param and column.Symbol:
                b_param = column.Symbol.LookupParameter("b") or column.Symbol.LookupParameter("B") or column.Symbol.LookupParameter("Width")

        # Try to get 'h' parameter (height) - check both instance and type parameters
        h_param = column.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_HEIGHT)
        if not h_param or not h_param.HasValue:
            # Check instance level first
            h_param = column.LookupParameter("h") or column.LookupParameter("H") or column.LookupParameter("Height")
            # If not found in instance, check type level
            if not h_param and column.Symbol:
                h_param = column.Symbol.LookupParameter("h") or column.Symbol.LookupParameter("H") or column.Symbol.LookupParameter("Height")

        # Try to get diameter parameter for circular columns - check both instance and type parameters
        diameter_param = column.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_DIAMETER)
        if not diameter_param or not diameter_param.HasValue:
            # Check instance level first
            diameter_param = column.LookupParameter("Diameter") or column.LookupParameter("D")
            # If not found in instance, check type level
            if not diameter_param and column.Symbol:
                diameter_param = column.Symbol.LookupParameter("Diameter") or column.Symbol.LookupParameter("D")

        # Extract values (in feet - Revit internal units)
        b_value = b_param.AsDouble() if b_param and b_param.HasValue else None
        h_value = h_param.AsDouble() if h_param and h_param.HasValue else None
        diameter_value = diameter_param.AsDouble() if diameter_param and diameter_param.HasValue else None

        # Determine column type and return appropriate dimensions
        if diameter_value is not None:
            # Circular column
            return {
                'diameter': diameter_value,
                'type': 'circular'
            }
        elif b_value is not None and h_value is not None:
            if abs(b_value - h_value) < 1e-6:  # Consider equal if difference < 0.001mm (converted to feet)
                # Square column (b ≈ h)
                return {
                    'b': b_value,
                    'type': 'square'
                }
            else:
                # Rectangular column
                return {
                    'b': b_value,
                    'h': h_value,
                    'type': 'rectangular'
                }
        elif b_value is not None:
            # Assume square if only b is available
            return {
                'b': b_value,
                'type': 'square'
            }
        else:
            debug_log("No dimension parameters found for column {}".format(column.Id), level='VERBOSE')
            return None

    except Exception as e:
        debug_log("Failed to get dimensions for column {}. Error: {}".format(column.Id, e), level='VERBOSE')
        return None


def get_family_type(column):
    """
    Retrieves the FamilySymbol (family type) of a given column element.

    Args:
        column (Element): The structural column element to get the type for.

    Returns:
        FamilySymbol or None: The family symbol of the column, or None if not found.
    """
    try:
        column_type_id = column.GetTypeId()
        if column_type_id:
            column_type = column.Document.GetElement(column_type_id)
            if column_type and hasattr(column_type, 'Family') and column_type.Family and hasattr(column_type.Family, 'Name'):
                return column_type
    except Exception as e:
        logger.debug("Failed to get family type for column {}. Error: {}".format(column.Id, e))
    return None


def get_family_geometry_type(column):
    """
    Detects family geometry type by checking family/type names first, then parameters.

    This function prioritizes family and type names to determine geometry type,
    falling back to parameter analysis if names don't provide clear indication.

    Args:
        column (Element): The column element to analyze

    Returns:
        str: Geometry type ('circular', 'square', 'rectangular', or 'unknown')
    """
    try:
        # Get family symbol for name-based detection
        family_symbol = get_family_type(column)
        if not family_symbol:
            debug_log("No family symbol found for column {}, using parameter detection".format(column.Id), level='DIAGNOSTIC')
            # Fallback to parameter-based detection
            dims = get_column_dimensions(column)
            if dims and 'type' in dims:
                debug_log("Detected {} from parameters for column {}".format(dims['type'], column.Id), level='DIAGNOSTIC')
                return dims['type']
            return 'unknown'

        # PERBAIKAN: Get names with proper null checking BEFORE calling .lower()
        family_name = ""
        type_name = ""

        try:
            if family_symbol.Family and hasattr(family_symbol.Family, 'Name') and family_symbol.Family.Name:
                family_name = str(family_symbol.Family.Name).lower()
        except Exception as e:
            debug_log("Could not get family name for column {}: {}".format(column.Id, e), level='DIAGNOSTIC')

        try:
            if hasattr(family_symbol, 'Name') and family_symbol.Name:
                type_name = str(family_symbol.Name).lower()
        except Exception as e:
            debug_log("Could not get type name for column {}: {}".format(column.Id, e), level='DIAGNOSTIC')

        # Log for debugging
        debug_log("Analyzing column {}: Family='{}', Type='{}'".format(
            column.Id, family_name, type_name), level='DIAGNOSTIC')

        # If both names are empty, skip to parameter detection
        if not family_name and not type_name:
            debug_log("Both family and type names empty for column {}, using parameter detection".format(column.Id), level='DIAGNOSTIC')
            dims = get_column_dimensions(column)
            if dims and 'type' in dims:
                debug_log("Detected {} from parameters for column {}".format(dims['type'], column.Id), level='DIAGNOSTIC')
                return dims['type']
            return 'unknown'

        # Check for circular indicators
        circular_keywords = ['round', 'circular', 'circle', 'pipe', 'tube', 'diameter', 'ø', 'bulat']
        for keyword in circular_keywords:
            if keyword in family_name or keyword in type_name:
                debug_log("Detected circular from keyword '{}' for column {}".format(keyword, column.Id), level='DIAGNOSTIC')
                return 'circular'

        # Check for square indicators
        square_keywords = ['square', 'box', 'kuadrat']
        for keyword in square_keywords:
            if keyword in family_name or keyword in type_name:
                debug_log("Detected square from keyword '{}' for column {}".format(keyword, column.Id), level='DIAGNOSTIC')
                return 'square'

        # Check for rectangular indicators
        rectangular_keywords = ['rectangular', 'rectangle', 'rect', 'persegi panjang']
        for keyword in rectangular_keywords:
            if keyword in family_name or keyword in type_name:
                debug_log("Detected rectangular from keyword '{}' for column {}".format(keyword, column.Id), level='DIAGNOSTIC')
                return 'rectangular'

        # PERBAIKAN: Parse family name with dash/underscore separators
        # Handle formats like "Concrete-Rectangular-Column" or "Steel_Square_Column"
        all_parts = []

        # Split family name by common separators
        if family_name:
            for separator in ['-', '_', ' ']:
                if separator in family_name:
                    all_parts.extend([part.strip() for part in family_name.split(separator)])
                    break
            else:
                # No separator found, use whole name
                all_parts.append(family_name)

        # Split type name by common separators
        if type_name:
            for separator in ['-', '_', ' ']:
                if separator in type_name:
                    all_parts.extend([part.strip() for part in type_name.split(separator)])
                    break
            else:
                # No separator found, use whole name
                all_parts.append(type_name)

        # Check each part for geometry type keywords
        for part in all_parts:
            part_lower = part.lower()

            # Check circular
            if part_lower in ['circular', 'circle', 'round', 'pipe', 'tube', 'bulat']:
                debug_log("Detected circular from part '{}' for column {}".format(part, column.Id), level='DIAGNOSTIC')
                return 'circular'

            # Check square
            if part_lower in ['square', 'box', 'kuadrat']:
                debug_log("Detected square from part '{}' for column {}".format(part, column.Id), level='DIAGNOSTIC')
                return 'square'

            # Check rectangular
            if part_lower in ['rectangular', 'rectangle', 'rect']:
                debug_log("Detected rectangular from part '{}' for column {}".format(part, column.Id), level='DIAGNOSTIC')
                return 'rectangular'

        # Fallback to parameter-based detection
        debug_log("Name-based detection inconclusive for column {}, using parameter detection".format(column.Id), level='DIAGNOSTIC')
        dims = get_column_dimensions(column)
        if dims and 'type' in dims:
            debug_log("Detected {} from parameters for column {}".format(dims['type'], column.Id), level='DIAGNOSTIC')
            return dims['type']

        debug_log("Could not detect geometry type for column {}".format(column.Id), level='VERBOSE')
        return 'unknown'

    except Exception as e:
        debug_log("Error detecting family geometry type for column {}: {}".format(column.Id, e), level='NORMAL')
        # Even in error, try parameter detection as last resort
        try:
            dims = get_column_dimensions(column)
            if dims and 'type' in dims:
                debug_log("Fallback: Detected {} from parameters for column {} after error".format(dims['type'], column.Id), level='DIAGNOSTIC')
                return dims['type']
        except:
            pass
        return 'unknown'

def get_csv_output_path():
    """Gets the organized output path for CSV files."""
    script_path = os.path.join(CSV_BASE_DIR, SCRIPT_SUBFOLDER)

    if CSV_CREATE_FOLDERS:
        if not os.path.exists(CSV_BASE_DIR):
            os.makedirs(CSV_BASE_DIR)
        if not os.path.exists(script_path):
            os.makedirs(script_path)

    return script_path


def export_validation_results_to_csv(validation_results, doc_title):
    """
    Exports validation results to a CSV file for debugging.

    Args:
        validation_results (list): List of validation data dictionaries
        doc_title (str): Document title for filename

    Returns:
        str: Path to the exported CSV file, or None if export failed
    """
    try:
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_doc_title = "".join(c for c in doc_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = "CheckColumnDimensions_{}_{}.csv".format(safe_doc_title, timestamp)

        # Get organized output path
        output_dir = get_csv_output_path()
        filepath = os.path.join(output_dir, filename)

        # Write CSV
        with io.open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            writer.writerow([
                'Host Column ID', 'Linked Column ID', 'Host Family Name', 'Host Type Name',
                'Linked Family Name', 'Linked Type Name', 'Host Family Type', 'Linked Family Type',
                'Host Dimensions', 'Linked Dimensions', 'Intersection Volume (cu ft)',
                'Intersection Volume (mm³)', 'Status', 'Debug Info'
            ])

            # Write results
            for result in validation_results:
                writer.writerow([
                    result.get('host_column_id', ''),
                    result.get('linked_column_id', ''),
                    result.get('host_family_name', ''),
                    result.get('host_type_name', ''),
                    result.get('linked_family_name', ''),
                    result.get('linked_type_name', ''),
                    result.get('host_family_type', ''),
                    result.get('linked_family_type', ''),
                    result.get('host_dimensions', ''),
                    result.get('linked_dimensions', ''),
                    result.get('intersection_volume_cu_ft', ''),
                    result.get('intersection_volume_mm3', ''),
                    result.get('status', ''),
                    result.get('debug_info', '')
                ])

        # Remove this logging - it causes console splitting
        # logger.info("Validation results exported to: {}".format(filepath))
        return filepath

    except Exception as e:
        logger.error("Failed to export validation results to CSV: {}".format(e))
        return None


def compare_dimensions(host_dims, linked_dims):
    """
    Compares dimension parameters between host and linked columns.
    Converts feet to millimeters FIRST, then compares with 0.01mm tolerance.

    Args:
        host_dims (dict): Dimension dictionary from host column (in feet)
        linked_dims (dict): Dimension dictionary from linked column (in feet)

    Returns:
        bool: True if dimensions match within tolerance, False otherwise
    """
    if not host_dims or not linked_dims:
        return False

    if host_dims.get('type') != linked_dims.get('type'):
        return False

    # PERBAIKAN: Import UnitUtils dengan fallback untuk compatibility
    try:
        from Autodesk.Revit.DB import UnitUtils, UnitTypeId
        USE_NEW_API = True
    except ImportError:
        from Autodesk.Revit.DB import UnitUtils
        USE_NEW_API = False

    # Tolerance dalam mm (tidak perlu konversi ke feet lagi)
    tolerance_mm = 0.01

    # Helper function to convert feet to mm
    def feet_to_mm(feet_value):
        if USE_NEW_API:
            return UnitUtils.ConvertFromInternalUnits(feet_value, UnitTypeId.Millimeters)
        else:
            # Fallback: manual conversion for older Revit versions
            return feet_value * 304.8

    if host_dims['type'] == 'circular':
        host_diam = host_dims.get('diameter')
        linked_diam = linked_dims.get('diameter')
        if host_diam is None or linked_diam is None:
            return False
        
        # PERBAIKAN: Konversi ke mm DULU, baru bandingkan
        host_diam_mm = feet_to_mm(host_diam)
        linked_diam_mm = feet_to_mm(linked_diam)
        diff_mm = abs(host_diam_mm - linked_diam_mm)
        match = diff_mm <= tolerance_mm
        
        if not match:
            logger.debug("Circular dimension mismatch: host_diam={:.2f}mm, linked_diam={:.2f}mm, diff={:.2f}mm".format(
                host_diam_mm, linked_diam_mm, diff_mm))
        return match

    elif host_dims['type'] == 'square':
        host_b = host_dims.get('b')
        linked_b = linked_dims.get('b')
        if host_b is None or linked_b is None:
            return False
        
        # PERBAIKAN: Konversi ke mm DULU, baru bandingkan
        host_b_mm = feet_to_mm(host_b)
        linked_b_mm = feet_to_mm(linked_b)
        diff_mm = abs(host_b_mm - linked_b_mm)
        match = diff_mm <= tolerance_mm
        
        if not match:
            logger.debug("Square dimension mismatch: host_b={:.2f}mm, linked_b={:.2f}mm, diff={:.2f}mm".format(
                host_b_mm, linked_b_mm, diff_mm))
        return match

    elif host_dims['type'] == 'rectangular':
        host_b = host_dims.get('b')
        host_h = host_dims.get('h')
        linked_b = linked_dims.get('b')
        linked_h = linked_dims.get('h')
        if None in [host_b, host_h, linked_b, linked_h]:
            return False
        
        # PERBAIKAN: Konversi ke mm DULU, baru bandingkan
        host_b_mm = feet_to_mm(host_b)
        host_h_mm = feet_to_mm(host_h)
        linked_b_mm = feet_to_mm(linked_b)
        linked_h_mm = feet_to_mm(linked_h)
        
        b_diff_mm = abs(host_b_mm - linked_b_mm)
        h_diff_mm = abs(host_h_mm - linked_h_mm)
        
        b_match = b_diff_mm <= tolerance_mm
        h_match = h_diff_mm <= tolerance_mm
        
        if not (b_match and h_match):
            logger.debug("Rectangular dimension mismatch: host_b={:.2f}mm, linked_b={:.2f}mm (diff={:.2f}mm), host_h={:.2f}mm, linked_h={:.2f}mm (diff={:.2f}mm)".format(
                host_b_mm, linked_b_mm, b_diff_mm, host_h_mm, linked_h_mm, h_diff_mm))
        return b_match and h_match

    return False

def set_comment_parameter(column, comment_text):
    """
    Sets the comment parameter for a column element.

    Args:
        column (Element): The column element to modify
        comment_text (str): The comment text to set

    Returns:
        bool: True if parameter was set successfully, False otherwise
    """
    try:
        comments_param = column.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        if comments_param and not comments_param.IsReadOnly:
            comments_param.Set(comment_text)
            logger.debug("Set Comments parameter to '{}' for column {}".format(comment_text, column.Id))
            return True
        else:
            logger.warning("Could not set Comments parameter for column {} (parameter not found or read-only)".format(column.Id))
            return False
    except Exception as e:
        logger.warning("Failed to set Comments parameter for column {}. Error: {}".format(column.Id, e))
        return False


def process_column_validation(host_column, linked_columns_dict):
    """
    Processes dimension validation for a single host column with family geometry type checking.

    Args:
        host_column (Element): The host column to validate
        linked_columns_dict (dict): Dictionary of linked columns with geometry

    Returns:
        tuple: (comment_text, validation_data)
            - comment_text (str): Comment text to set
            - validation_data (dict): Detailed validation information for CSV export
    """
    validation_data = {
        'host_column_id': str(host_column.Id),
        'linked_column_id': None,
        'host_family_name': None,
        'host_type_name': None,
        'linked_family_name': None,
        'linked_type_name': None,
        'host_family_type': None,
        'linked_family_type': None,
        'host_dimensions': None,
        'linked_dimensions': None,
        'intersection_volume_cu_ft': None,
        'intersection_volume_mm3': None,
        'status': None,
        'debug_info': None
    }

    # Get host column family info
    try:
        host_family_symbol = get_family_type(host_column)
        if host_family_symbol:
            validation_data['host_family_name'] = host_family_symbol.Family.Name
            validation_data['host_type_name'] = host_family_symbol.Name
    except Exception as e:
        validation_data['debug_info'] = "Host family info error: {}".format(str(e))

    # Find best geometric match
    best_match, intersection_volume = find_best_match(host_column, linked_columns_dict)

    if not best_match:
        # No geometric intersection found
        validation_data['status'] = 'Unmatched'
        validation_data['intersection_volume_cu_ft'] = 0.0
        validation_data['intersection_volume_mm3'] = 0.0
        validation_data['debug_info'] = "No geometric intersection found"
        return "Unmatched", validation_data

    validation_data['linked_column_id'] = str(best_match.Id)
    validation_data['intersection_volume_cu_ft'] = intersection_volume
    validation_data['intersection_volume_mm3'] = feet3_to_mm3(intersection_volume)

    # Get linked column family info
    try:
        linked_family_symbol = get_family_type(best_match)
        if linked_family_symbol:
            validation_data['linked_family_name'] = linked_family_symbol.Family.Name
            validation_data['linked_type_name'] = linked_family_symbol.Name
    except Exception as e:
        validation_data['debug_info'] = "Linked family info error: {}".format(str(e))

    # Check family geometry types first
    host_family_type = get_family_geometry_type(host_column)
    linked_family_type = get_family_geometry_type(best_match)

    validation_data['host_family_type'] = host_family_type
    validation_data['linked_family_type'] = linked_family_type

    if host_family_type != linked_family_type:
        # Family geometry types don't match
        validation_data['status'] = 'Family unmatched'
        validation_data['debug_info'] = "Family types don't match: {} vs {}".format(host_family_type, linked_family_type)
        return "Family unmatched", validation_data

    # Family types match, now check dimensions
    host_dims = get_column_dimensions(host_column)
    linked_dims = get_column_dimensions(best_match)

    validation_data['host_dimensions'] = str(host_dims) if host_dims else None
    validation_data['linked_dimensions'] = str(linked_dims) if linked_dims else None

    if not host_dims or not linked_dims:
        # Could not get dimensions
        debug_msg = "Could not get dimensions - Host: {}, Linked: {}".format(
            "OK" if host_dims else "FAILED", "OK" if linked_dims else "FAILED")
        validation_data['status'] = 'Dimension to be checked'
        validation_data['debug_info'] = debug_msg
        return "Dimension to be checked", validation_data

    # Compare dimensions
    if compare_dimensions(host_dims, linked_dims):
        validation_data['status'] = 'Approved'
        validation_data['debug_info'] = "Dimensions match within tolerance"
        return "Approved", validation_data
    else:
        validation_data['status'] = 'Dimension to be checked'
        validation_data['debug_info'] = "Dimensions don't match"
        return "Dimension to be checked", validation_data


def main():
    """
    Main execution function that orchestrates the column dimension validation process.

    Handles the complete workflow from model selection through results reporting,
    including error handling and user feedback.
    """
    # Step 1: Select the linked EXR model from available Revit links
    link_doc, selected_link = select_linked_model()

    # Step 2: Gather structural column elements from both host and linked models
    host_columns = collect_host_columns()
    linked_columns = collect_linked_columns(link_doc)

    if not host_columns:
        forms.alert("No structural column elements found in the host model. "
                   "Please ensure your model contains structural columns.", exitscript=True)

    if not linked_columns:
        forms.alert("No structural column elements found in the linked EXR model. "
                   "Please ensure the linked model contains structural columns.", exitscript=True)

    # Log collection details
    debug_log("=== COLUMN COLLECTION SUMMARY ===", level='NORMAL')
    debug_log("Host columns found: {}".format(len(host_columns)), level='NORMAL')
    debug_log("Linked columns found: {}".format(len(linked_columns)), level='NORMAL')

    # Log first few IDs for verification
    if host_columns:
        host_ids = [str(c.Id) for c in host_columns[:5]]
        debug_log("First 5 host column IDs: {}".format(", ".join(host_ids)), level='VERBOSE')
        if len(host_columns) > 5:
            debug_log("... and {} more host columns".format(len(host_columns) - 5), level='VERBOSE')

    if linked_columns:
        linked_ids = [str(c.Id) for c in linked_columns[:5]]
        debug_log("First 5 linked column IDs: {}".format(", ".join(linked_ids)), level='VERBOSE')
        if len(linked_columns) > 5:
            debug_log("... and {} more linked columns".format(len(linked_columns) - 5), level='VERBOSE')

    debug_log("=" * 50, level='NORMAL')

    # Provide clear feedback about selection method used
    selection_ids = uidoc.Selection.GetElementIds()
    pre_selected_elements = []

    if selection_ids:
        for elem_id in selection_ids:
            elem = doc.GetElement(elem_id)
            if elem and elem.Category and elem.Category.Id == BuiltInCategory.OST_StructuralColumns:
                pre_selected_elements.append(elem)

    # Column collection completed

    # Step 3: Extract and cache solid geometries for linked columns to optimize matching performance

    debug_log("=== LINKED COLUMNS GEOMETRY PROCESSING START ===", level='NORMAL')
    debug_log("Total linked columns to process: {}".format(len(linked_columns)), level='NORMAL')

    linked_columns_dict = {}
    geometry_success_count = 0
    geometry_fail_count = 0

    with ProgressBar(title='Processing Linked Column Geometry ({value} of {max_value})') as pb:
        for i, column in enumerate(linked_columns):
            debug_log("Processing linked column {}/{}: ID={}".format(i+1, len(linked_columns), column.Id), level='VERBOSE')
            solid = get_solid(column)
            if solid:
                linked_columns_dict[column.Id] = {'element': column, 'solid': solid}
                geometry_success_count += 1
            else:
                geometry_fail_count += 1
            pb.update_progress(i+1, len(linked_columns))

    debug_log("=== LINKED COLUMNS GEOMETRY PROCESSING COMPLETE ===", level='NORMAL')
    debug_log("Total processed: {}".format(len(linked_columns)), level='NORMAL')
    debug_log("Geometry extraction successful: {} columns".format(geometry_success_count), level='NORMAL')
    debug_log("Geometry extraction failed: {} columns".format(geometry_fail_count), level='NORMAL')
    debug_log("Columns cached for matching: {}".format(len(linked_columns_dict)), level='NORMAL')

    # Log IDs of successfully processed columns
    if linked_columns_dict:
        successful_ids = [str(id.Value) for id in list(linked_columns_dict.keys())[:10]]  # First 10
        debug_log("First 10 successfully processed column IDs: {}".format(successful_ids), level='VERBOSE')
        if len(linked_columns_dict) > 10:
            debug_log("... and {} more".format(len(linked_columns_dict) - 10), level='VERBOSE')

    # Geometry processing completed

    # Step 4: Validate dimensions for each host column

    approved_count = 0
    family_unmatched_count = 0
    dimension_check_count = 0
    unmatched_count = 0
    validation_results = []

    # Process in transaction
    with Transaction(doc, 'Validate Column Dimensions') as t:
        t.Start()

        with ProgressBar(title='Validating Column Dimensions ({value} of {max_value})') as pb:
            for i, host_column in enumerate(host_columns):
                comment, validation_data = process_column_validation(host_column, linked_columns_dict)
                validation_results.append(validation_data)

                if comment == "Approved":
                    approved_count += 1
                elif comment == "Family unmatched":
                    family_unmatched_count += 1
                elif comment == "Dimension to be checked":
                    dimension_check_count += 1
                elif comment == "Unmatched":
                    unmatched_count += 1

                # Set the comment parameter
                set_comment_parameter(host_column, comment)

                pb.update_progress(i+1, len(host_columns))

        # === CRITICAL: Print ALL Results BEFORE Commit ===
        output.print_md("## Results Summary")
        output.print_md("---")
        output.print_md("Total columns processed: {}".format(len(host_columns)))
        output.print_md("Approved (family & dimensions match): {}".format(approved_count))
        output.print_md("Family unmatched: {}".format(family_unmatched_count))
        output.print_md("Dimension to be checked: {}".format(dimension_check_count))
        output.print_md("Unmatched (no intersection): {}".format(unmatched_count))
        output.print_md("Saving changes...")

        # Commit the transaction
        status = t.Commit()

        if status != TransactionStatus.Committed:
            logger.warning("Transaction was not committed successfully")
            forms.alert("Failed to update column comments. Please try again.", exitscript=True)

    # === SAFE ZONE: Post-commit operations ===
    # Export results to CSV (uses logger, not output.print_md)
    csv_path = export_validation_results_to_csv(validation_results, doc.Title)

    # Clean up geometry cache to free memory
    linked_columns_dict.clear()
    gc.collect()

    # Use logger for post-commit messages (safe) - REMOVE DUPLICATE LOGGING
    # CSV export function already logs the path, so we don't need to log it again
    # if csv_path:
    #     logger.info("Detailed results exported to: {}".format(csv_path))

    # Add debug summary only when debug is enabled (using logger, not output.print_md)
    if DEBUG_MODE:
        logger.info("=== DEBUG ANALYSIS SUMMARY ===")

        # Geometry extraction summary
        total_linked = len(linked_columns) if 'linked_columns' in locals() else 0
        cached_linked = len(linked_columns_dict) if 'linked_columns_dict' in locals() else 0

        logger.info("Geometry Processing:")
        logger.info("- Total linked columns: {}".format(total_linked))
        logger.info("- Successfully cached: {}".format(cached_linked))
        if total_linked > 0:
            success_rate = (cached_linked / float(total_linked)) * 100
            logger.info("- Success rate: {:.1f}%".format(success_rate))

        # Intersection analysis
        matched_results = [r for r in validation_results if r.get('intersection_volume_cu_ft', 0) > 0]
        unmatched_results = [r for r in validation_results if r.get('status') == 'Unmatched']

        logger.info("Matching Results:")
        logger.info("- Total host columns processed: {}".format(len(validation_results)))
        logger.info("- Columns with intersections: {}".format(len(matched_results)))
        logger.info("- Unmatched columns: {}".format(len(unmatched_results)))

        if matched_results:
            logger.info("Sample Intersection Volumes (first 5):")
            for result in matched_results[:5]:
                vol_cu_ft = result.get('intersection_volume_cu_ft', 0)
                vol_mm3 = result.get('intersection_volume_mm3', 0)
                status = result.get('status', 'Unknown')

                logger.info("- Host {} → Linked {}: {:.6f} cu ft ({:.0f} mm³) | {}".format(
                    result.get('host_column_id', 'Unknown'),
                    result.get('linked_column_id', 'Unknown'),
                    vol_cu_ft, vol_mm3, status
                ))

            if len(matched_results) > 5:
                logger.info("... and {} more matched columns".format(len(matched_results) - 5))
        else:
            logger.info("CRITICAL: No columns found with intersection volumes > 0")
            logger.info("This indicates geometry extraction failures or no actual intersections exist.")
            logger.info("Check pyRevit console logs for detailed geometry extraction errors.")

        logger.info("Next Steps:")
        logger.info("1. Check pyRevit console for geometry extraction logs")
        logger.info("2. Verify column IDs in collection vs visual model")
        logger.info("3. Review CSV for complete intersection data")
        logger.info("=" * 80)

    # Show completion message (safe - uses forms.alert, not output.print_md)
    alert_message = "Column dimension validation complete!\n\n"
    alert_message += "Approved: {} columns\n".format(approved_count)
    alert_message += "Family unmatched: {} columns\n".format(family_unmatched_count)
    alert_message += "Need checking: {} columns\n".format(dimension_check_count)
    alert_message += "Unmatched: {} columns\n".format(unmatched_count)
    alert_message += "\n\nCheck the Comments parameter on each column for details."

    # Add intersection volume summary
    matched_count = len([r for r in validation_results if r.get('intersection_volume_cu_ft', 0) > 0])
    alert_message += "\n\nIntersection Analysis:"
    alert_message += "\nColumns with intersections: {}".format(matched_count)

    if csv_path:
        alert_message += "\n\nDetailed results: Desktop\\{}".format(os.path.basename(csv_path))
        alert_message += "\nCheck pyRevit console for debug logs."

    forms.alert(alert_message, title="Validation Complete")


if __name__ == '__main__':
    main()