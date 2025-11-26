# -*- coding: utf-8 -*-
__title__ = 'Check Framing Dimensions by EXR Geometry'
__author__ = 'PrasKaa+KiloCode'
__doc__ = "Validates framing dimensions by geometry intersection and parameter comparison."

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
    View3D,
    ViewFamilyType,
    ViewFamily,
    OverrideGraphicSettings,
    Color,
    Element,
    ElementId,
    Options,
    BuiltInParameter,
    StorageType,
    GeometryInstance,
    ParameterFilterElement,
    ParameterFilterRuleFactory,
    FilterRule,
    ElementParameterFilter
)
from System.Collections.Generic import List
from System import Int64

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

# Import graphic overrides utility from lib
try:
    from graphicOverrides import get_solid_fill_pattern, get_revit_version
except ImportError:
    # Fallback if import fails
    get_solid_fill_pattern = None
    get_revit_version = None

# Script configuration
SCRIPT_SUBFOLDER = "Check Framing Dimensions"

# Debug configuration - Set to True for troubleshooting, False for production
DEBUG_MODE = False  # Options: False, 'MINIMAL', 'NORMAL', 'VERBOSE', 'DIAGNOSTIC'

# 3D View creation configuration
CREATE_ISSUES_VIEW = True  # Set to True to auto-create 3D view for framing issues
ISSUES_VIEW_TRANSPARENCY = 50  # Transparency for linked model (0-100)

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


def collect_host_beams():
    """
    Collects structural framing elements from the host Revit model using smart selection.

    Logic Flow:
    1. Check for pre-selected elements - if found, validate and use them
    2. If no pre-selected elements, automatically collect ALL structural framing
    3. Validate that selected/pre-selected elements are actually structural framing
    4. Provide clear error messages if no valid beams found

    Returns:
        list: List of Element objects representing beams in the host model.

    Raises:
        SystemExit: If no beams are found in the model.
    """
    # Step 1: Check for pre-selected elements
    selection_ids = uidoc.Selection.GetElementIds()
    pre_selected_elements = []

    if selection_ids:
        debug_log("Found {} pre-selected elements".format(len(selection_ids)), level='NORMAL')

        # Validate pre-selected elements are structural framing
        for elem_id in selection_ids:
            elem = doc.GetElement(elem_id)
            if elem and elem.Category:
                # Check if it's a structural framing element (API compatibility for Revit 2024+)
                category_id_value = elem.Category.Id.Value if hasattr(elem.Category.Id, 'Value') else elem.Category.Id.IntegerValue
                if elem.Category and category_id_value == int(BuiltInCategory.OST_StructuralFraming):
                    pre_selected_elements.append(elem)
                    debug_log("Validated pre-selected beam: ID={}".format(elem.Id), level='VERBOSE')
                else:
                    debug_log("Skipping non-framing element: ID={}, Category={}".format(
                        elem.Id, elem.Category.Name), level='VERBOSE')

        if pre_selected_elements:
            debug_log("Using {} pre-selected structural framing elements".format(len(pre_selected_elements)), level='NORMAL')
            return pre_selected_elements
        else:
            debug_log("No valid structural framing elements found in pre-selection", level='NORMAL')

    # Step 2: No valid pre-selection or no selection at all - collect ALL structural framing
    debug_log("Collecting ALL structural framing elements from host model", level='NORMAL')

    all_beams = FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_StructuralFraming)\
        .WhereElementIsNotElementType()\
        .ToElements()

    if not all_beams:
        forms.alert("No structural framing elements found in the host model. "
                   "Please ensure your model contains structural framing elements.", exitscript=True)

    debug_log("Collected {} structural framing elements from host model".format(len(all_beams)), level='NORMAL')

    # Log first few element IDs for verification
    if all_beams:
        sample_ids = [str(c.Id) for c in all_beams[:5]]
        debug_log("Sample beam IDs: {}".format(", ".join(sample_ids)), level='VERBOSE')
        if len(all_beams) > 5:
            debug_log("... and {} more beams".format(len(all_beams) - 5), level='VERBOSE')

    return all_beams


def collect_linked_beams(link_doc):
    """
    Collects structural framing elements from the linked EXR model.

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


def feet3_to_mm3(volume_cu_ft):
    """Convert cubic feet to cubic millimeters for better readability."""
    # 1 cubic foot = 28,316,846.592 mm³
    return volume_cu_ft * 28316846.592


def find_3d_view_type():
    """
    Finds the ViewFamilyType for 3D views.

    Returns:
        ViewFamilyType or None: The 3D view family type, or None if not found.
    """
    try:
        view_family_types = FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements()
        for vft in view_family_types:
            if vft.ViewFamily == ViewFamily.ThreeDimensional:
                return vft
        return None
    except Exception as e:
        logger.warning("Failed to find 3D view type: {}".format(e))
        return None


def create_linked_model_transparency_filter(doc, view, transparency_percentage=50):
    """
    Create a parameter filter targeting worksets starting with "Superimposed"
    and apply transparency override to linked models

    Args:
        doc: Revit Document
        view: Target 3D View
        transparency_percentage: Transparency value (0-100)

    Returns:
        ParameterFilterElement or None if failed
    """
    try:
        logger.info("Creating workset-based transparency filter for linked models...")

        # Create filter name with timestamp to avoid conflicts
        timestamp = datetime.now().strftime("%H%M%S")
        filter_name = "FRAMING CHECK - Linked Transparency {}".format(timestamp)

        # ================================================================
        # STEP 1: Get all filterable categories using .NET List
        # ================================================================
        logger.info("Collecting filterable categories...")

        # CRITICAL: Use System.Collections.Generic.List, NOT Python list!
        filterable_categories = List[ElementId]()

        category_count = 0
        for category in doc.Settings.Categories:
            try:
                if category.AllowsBoundParameters:
                    filterable_categories.Add(category.Id)
                    category_count += 1
            except:
                continue

        if filterable_categories.Count == 0:
            logger.warning("No filterable categories found")
            return None

        logger.info("Found {} filterable categories".format(filterable_categories.Count))

        # ================================================================
        # STEP 2: Create filter rule for workset parameter
        # ================================================================
        logger.info("Creating workset filter rule...")

        # Method 1: Convert BuiltInParameter to ElementId (CORRECT WAY)
        try:
            workset_param_id = ElementId(BuiltInParameter.ELEM_PARTITION_PARAM)
            logger.info("Created ElementId from BuiltInParameter: {}".format(workset_param_id))

            # Create "Begins with" rule for workset name
            # CORRECTED: Remove case insensitive parameter (doesn't exist in API)
            filter_rule = ParameterFilterRuleFactory.CreateBeginsWithRule(
                workset_param_id,
                "Superimposed"
            )

            logger.info("Successfully created filter rule: Workset name begins with 'Superimposed'")

        except Exception as rule_error:
            logger.warning("Failed to create filter rule: {}".format(rule_error))
            return None

        # ================================================================
        # STEP 3: Create ElementParameterFilter from filter rule
        # ================================================================
        # CORRECT: Use ElementParameterFilter, not List[FilterRule]
        element_filter = ElementParameterFilter(filter_rule)

        logger.info("Type of element_filter: {}".format(type(element_filter)))

        # ================================================================
        # STEP 4: Create the ParameterFilterElement
        # ================================================================
        logger.info("Creating ParameterFilterElement...")

        try:
            # Verify types before calling Create
            logger.info("Verifying parameter types:")
            logger.info("  - doc type: {}".format(type(doc)))
            logger.info("  - filter_name type: {}".format(type(filter_name)))
            logger.info("  - filterable_categories type: {}".format(type(filterable_categories)))
            logger.info("  - element_filter type: {}".format(type(element_filter)))

            linked_filter = ParameterFilterElement.Create(
                doc,
                filter_name,
                filterable_categories,  # ICollection[ElementId]
                element_filter          # ElementParameterFilter - CORRECT!
            )

            logger.info("Successfully created filter '{}'".format(filter_name))
            logger.info("Filter ID: {}".format(linked_filter.Id))

        except Exception as create_error:
            logger.warning("Failed to create ParameterFilterElement: {}".format(create_error))
            import traceback
            logger.warning(traceback.format_exc())
            return None

        # ================================================================
        # STEP 5: Apply transparency override to the filter in view
        # ================================================================
        logger.info("Applying transparency override...")

        try:
            filter_override = OverrideGraphicSettings()
            filter_override.SetSurfaceTransparency(transparency_percentage)

            # Add blue color to projection surface
            blue_color = Color(0, 0, 255)  # RGB for blue
            filter_override.SetSurfaceForegroundPatternColor(blue_color)
            filter_override.SetSurfaceBackgroundPatternColor(blue_color)

            # Set solid fill pattern if available
            solid_pattern = None
            if get_solid_fill_pattern:
                try:
                    solid_pattern = get_solid_fill_pattern(doc)
                    if solid_pattern:
                        filter_override.SetSurfaceForegroundPatternId(solid_pattern)
                        filter_override.SetSurfaceBackgroundPatternId(solid_pattern)
                        logger.debug("Applied solid blue pattern to linked model filter")
                except Exception as pattern_error:
                    logger.debug("Could not apply solid pattern: {}".format(pattern_error))

            # Add filter to view first
            view.AddFilter(linked_filter.Id)

            # Then set overrides
            view.SetFilterOverrides(linked_filter.Id, filter_override)

            logger.info("Applied {}% transparency and blue color to linked model filter".format(transparency_percentage))

        except Exception as override_error:
            logger.warning("Failed to apply filter overrides: {}".format(override_error))
            # Filter is created but override failed - still return the filter

        return linked_filter

    except Exception as e:
        logger.warning("Failed to create linked model transparency filter: {}".format(e))
        import traceback
        logger.warning(traceback.format_exc())
        return None


# Removed workset filter function - using direct override instead for better compatibility


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
        tuple: (best_match Element or None, max_intersection_volume float)
            - best_match: The best matching beam from the linked model, or None if no valid
              intersection is found or if geometry extraction fails.
            - max_intersection_volume: The intersection volume in cubic feet.
    """
    host_solid = get_solid(host_beam)
    if not host_solid:
        debug_log("Could not get solid for host beam {}".format(host_beam.Id), level='VERBOSE')
        return None, 0.0

    best_match = None
    max_intersection_volume = 0.0
    all_candidates = []  # For debugging

    # Only log essential info to prevent console overflow
    for linked_beam_id, linked_beam_data in linked_beams_dict.items():
        linked_solid = linked_beam_data['solid']
        if not linked_solid:
            continue

        try:
            # Calculate intersection
            intersection_solid = BooleanOperationsUtils.ExecuteBooleanOperation(
                host_solid, linked_solid, BooleanOperationsType.Intersect
            )

            volume = intersection_solid.Volume if intersection_solid else 0.0
            all_candidates.append((linked_beam_id, volume))

            # Compare volume
            if volume > max_intersection_volume:
                max_intersection_volume = volume
                best_match = linked_beam_data['element']

        except Exception as e:
            # Silent fail for geometry issues
            continue

    # Only log final result to prevent spam
    if best_match:
        max_vol_mm3 = feet3_to_mm3(max_intersection_volume)
        debug_log("Host {} matched with Linked {} (volume: {:.6f} cu ft)".format(
            host_beam.Id, best_match.Id, max_intersection_volume), level='VERBOSE')

    return best_match, max_intersection_volume


def get_beam_dimensions(beam):
    """
    Extracts dimension parameters from a beam element.
    Returns dimensions in FEET (Revit internal units) - conversion to mm done in compare_dimensions.

    Args:
        beam (Element): The beam element to extract dimensions from.

    Returns:
        dict or None: Dictionary with dimension values, or None if parameters not found.
            Format: {'b': float, 'h': float, 'type': str}
            type can be: 'rectangular', 'square', or 'unknown'
    """
    try:
        # Debug: Check if function is being called
        debug_log("DEBUG: get_beam_dimensions called for beam {}".format(beam.Id), level='DIAGNOSTIC')

        # Debug: Log all available type parameters for first few beams
        debug_count = getattr(get_beam_dimensions, '_debug_count', 0)
        if debug_count < 3:  # Show parameters for first 3 beams
            debug_log("DEBUG: Starting type parameter inspection for beam {} (count: {})".format(beam.Id, debug_count + 1), level='DIAGNOSTIC')

            # Check type parameters - show ALL of them
            debug_log("DEBUG: Type parameters:", level='DIAGNOSTIC')
            if beam.Symbol:
                type_param_info = []
                for param in beam.Symbol.Parameters:
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
                debug_log("DEBUG: No symbol/type found for beam", level='DIAGNOSTIC')

            debug_log("DEBUG: Type parameter inspection complete for beam {}".format(beam.Id), level='DIAGNOSTIC')
            get_beam_dimensions._debug_count = debug_count + 1

        # Try to get 'b' parameter (width/depth) - check both instance and type parameters
        b_param = beam.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_WIDTH)
        if not b_param or not b_param.HasValue:
            # Check instance level first
            b_param = beam.LookupParameter("b") or beam.LookupParameter("B") or beam.LookupParameter("Width")
            # If not found in instance, check type level
            if not b_param and beam.Symbol:
                b_param = beam.Symbol.LookupParameter("b") or beam.Symbol.LookupParameter("B") or beam.Symbol.LookupParameter("Width")

        # Try to get 'h' parameter (height) - check both instance and type parameters
        h_param = beam.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_HEIGHT)
        if not h_param or not h_param.HasValue:
            # Check instance level first
            h_param = beam.LookupParameter("h") or beam.LookupParameter("H") or beam.LookupParameter("Height")
            # If not found in instance, check type level
            if not h_param and beam.Symbol:
                h_param = beam.Symbol.LookupParameter("h") or beam.Symbol.LookupParameter("H") or beam.Symbol.LookupParameter("Height")

        # Extract values (in feet - Revit internal units)
        b_value = b_param.AsDouble() if b_param and b_param.HasValue else None
        h_value = h_param.AsDouble() if h_param and h_param.HasValue else None

        # Determine beam type and return appropriate dimensions
        if b_value is not None and h_value is not None:
            if abs(b_value - h_value) < 1e-6:  # Consider equal if difference < 0.001mm (converted to feet)
                # Square beam (b ≈ h)
                return {
                    'b': b_value,
                    'type': 'square'
                }
            else:
                # Rectangular beam
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
            debug_log("No dimension parameters found for beam {}".format(beam.Id), level='VERBOSE')
            return None

    except Exception as e:
        debug_log("Failed to get dimensions for beam {}. Error: {}".format(beam.Id, e), level='VERBOSE')
        return None


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


def get_family_geometry_type(beam):
    """
    Detects family geometry type by checking family/type names first, then parameters.

    This function prioritizes family and type names to determine geometry type,
    falling back to parameter analysis if names don't provide clear indication.

    Args:
        beam (Element): The beam element to analyze

    Returns:
        str: Geometry type ('circular', 'square', 'rectangular', or 'unknown')
    """
    try:
        # Get family symbol for name-based detection
        family_symbol = get_family_type(beam)
        if not family_symbol:
            debug_log("No family symbol found for beam {}, using parameter detection".format(beam.Id), level='DIAGNOSTIC')
            # Fallback to parameter-based detection
            dims = get_beam_dimensions(beam)
            if dims and 'type' in dims:
                debug_log("Detected {} from parameters for beam {}".format(dims['type'], beam.Id), level='DIAGNOSTIC')
                return dims['type']
            return 'unknown'

        # PERBAIKAN: Get names with proper null checking BEFORE calling .lower()
        family_name = ""
        type_name = ""

        try:
            if family_symbol.Family and hasattr(family_symbol.Family, 'Name') and family_symbol.Family.Name:
                family_name = str(family_symbol.Family.Name).lower()
        except Exception as e:
            debug_log("Could not get family name for beam {}: {}".format(beam.Id, e), level='DIAGNOSTIC')

        try:
            if hasattr(family_symbol, 'Name') and family_symbol.Name:
                type_name = str(family_symbol.Name).lower()
        except Exception as e:
            debug_log("Could not get type name for beam {}: {}".format(beam.Id, e), level='DIAGNOSTIC')

        # Log for debugging
        debug_log("Analyzing beam {}: Family='{}', Type='{}'".format(
            beam.Id, family_name, type_name), level='DIAGNOSTIC')

        # If both names are empty, skip to parameter detection
        if not family_name and not type_name:
            debug_log("Both family and type names empty for beam {}, using parameter detection".format(beam.Id), level='DIAGNOSTIC')
            dims = get_beam_dimensions(beam)
            if dims and 'type' in dims:
                debug_log("Detected {} from parameters for beam {}".format(dims['type'], beam.Id), level='DIAGNOSTIC')
                return dims['type']
            return 'unknown'

        # Check for circular indicators
        circular_keywords = ['round', 'circular', 'circle', 'pipe', 'tube', 'diameter', 'ø', 'bulat']
        for keyword in circular_keywords:
            if keyword in family_name or keyword in type_name:
                debug_log("Detected circular from keyword '{}' for beam {}".format(keyword, beam.Id), level='DIAGNOSTIC')
                return 'circular'

        # Check for square indicators
        square_keywords = ['square', 'box', 'kuadrat']
        for keyword in square_keywords:
            if keyword in family_name or keyword in type_name:
                debug_log("Detected square from keyword '{}' for beam {}".format(keyword, beam.Id), level='DIAGNOSTIC')
                return 'square'

        # Check for rectangular indicators
        rectangular_keywords = ['rectangular', 'rectangle', 'rect', 'persegi panjang']
        for keyword in rectangular_keywords:
            if keyword in family_name or keyword in type_name:
                debug_log("Detected rectangular from keyword '{}' for beam {}".format(keyword, beam.Id), level='DIAGNOSTIC')
                return 'rectangular'

        # PERBAIKAN: Parse family name with dash/underscore separators
        # Handle formats like "Concrete-Rectangular-Beam" or "Steel_Square_Beam"
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
                debug_log("Detected circular from part '{}' for beam {}".format(part, beam.Id), level='DIAGNOSTIC')
                return 'circular'

            # Check square
            if part_lower in ['square', 'box', 'kuadrat']:
                debug_log("Detected square from part '{}' for beam {}".format(part, beam.Id), level='DIAGNOSTIC')
                return 'square'

            # Check rectangular
            if part_lower in ['rectangular', 'rectangle', 'rect']:
                debug_log("Detected rectangular from part '{}' for beam {}".format(part, beam.Id), level='DIAGNOSTIC')
                return 'rectangular'

        # Fallback to parameter-based detection
        debug_log("Name-based detection inconclusive for beam {}, using parameter detection".format(beam.Id), level='DIAGNOSTIC')
        dims = get_beam_dimensions(beam)
        if dims and 'type' in dims:
            debug_log("Detected {} from parameters for beam {}".format(dims['type'], beam.Id), level='DIAGNOSTIC')
            return dims['type']

        debug_log("Could not detect geometry type for beam {}".format(beam.Id), level='VERBOSE')
        return 'unknown'

    except Exception as e:
        debug_log("Error detecting family geometry type for beam {}: {}".format(beam.Id, e), level='NORMAL')
        # Even in error, try parameter detection as last resort
        try:
            dims = get_beam_dimensions(beam)
            if dims and 'type' in dims:
                debug_log("Fallback: Detected {} from parameters for beam {} after error".format(dims['type'], beam.Id), level='DIAGNOSTIC')
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
        filename = "CheckFramingDimensions_{}_{}.csv".format(safe_doc_title, timestamp)

        # Get organized output path
        output_dir = get_csv_output_path()
        filepath = os.path.join(output_dir, filename)

        # Write CSV
        with io.open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            writer.writerow([
                'Host Beam ID', 'Linked Beam ID', 'Host Family Name', 'Host Type Name',
                'Linked Family Name', 'Linked Type Name', 'Host Family Type', 'Linked Family Type',
                'Host Dimensions', 'Linked Dimensions', 'Intersection Volume (cu ft)',
                'Intersection Volume (mm³)', 'Status', 'Debug Info'
            ])

            # Write results
            for result in validation_results:
                writer.writerow([
                    result.get('host_beam_id', ''),
                    result.get('linked_beam_id', ''),
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

        # Log the CSV path for user reference
        logger.info("CSV Results: {}".format(filepath))
        return filepath

    except Exception as e:
        logger.error("Failed to export validation results to CSV: {}".format(e))
        return None


def create_framing_issues_view(validation_results, selected_link):
    """
    Creates a 3D view showing only framing elements that need attention.

    Args:
        validation_results (list): List of validation result dictionaries
        selected_link (RevitLinkInstance): The selected linked model instance

    Returns:
        View3D or None: The created 3D view, or None if creation failed
    """
    try:
        logger.info("Starting 3D issues view creation...")

        # Find 3D view type
        logger.info("Finding 3D view type...")
        view_type = find_3d_view_type()
        if not view_type:
            logger.warning("Could not find 3D view type for issues view")
            return None
        logger.info("Found 3D view type: {}".format(view_type.Id))

        # Create view name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        view_name = "FRAMING CHECK - Issues Only {}".format(timestamp)
        logger.info("View name will be: {}".format(view_name))

        # Delete existing view with same name if exists
        logger.info("Checking for existing views to delete...")
        existing_views = FilteredElementCollector(doc).OfClass(View3D).ToElements()
        deleted_count = 0
        for view in existing_views:
            if view.Name == view_name:
                try:
                    doc.Delete(view.Id)
                    deleted_count += 1
                    logger.info("Deleted existing issues view: {}".format(view_name))
                    break
                except Exception as e:
                    logger.warning("Could not delete existing view {}: {}".format(view_name, e))
        logger.info("Deleted {} existing views".format(deleted_count))

        # Create new 3D view
        logger.info("Creating new 3D view...")
        with Transaction(doc, 'Create Framing Issues View') as t:
            t.Start()
            logger.info("Transaction started")

            try:
                new_view = View3D.CreateIsometric(doc, view_type.Id)
                new_view.Name = view_name
                logger.info("3D view created successfully: {}".format(new_view.Id))
            except Exception as e:
                logger.error("Failed to create 3D view: {}".format(e))
                t.RollBack()
                return None

            # Set linked model transparency using advanced workset filter approach
            linked_filter = None
            if selected_link:
                try:
                    logger.info("Setting linked model transparency using workset filter...")
                    linked_filter = create_linked_model_transparency_filter(
                        doc, new_view, ISSUES_VIEW_TRANSPARENCY
                    )
                    if linked_filter:
                        logger.info("Successfully created linked model transparency filter")
                    else:
                        logger.warning("Workset filter approach failed, linked model will be opaque")
                except Exception as e:
                    logger.warning("Could not create linked model transparency filter: {}".format(e))
                    logger.info("Linked model will be displayed without transparency")

            # Apply graphic overrides to problematic beams
            problematic_beams = []
            status_counts = {'Approved': 0, 'Family unmatched': 0, 'Dimension to be checked': 0, 'Unmatched': 0}

            # Count status distribution (lightweight)
            for result in validation_results:
                status = result.get('status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1

                # Only process problematic beams
                if status in ['Family unmatched', 'Dimension to be checked', 'Unmatched']:
                    # Only debug for 'Dimension to be checked' to avoid spam
                    debug_this = (status == 'Dimension to be checked')
                    if debug_this:
                        logger.info("Processing problematic beam with status: '{}'".format(status))
                    try:
                        beam_id_str = result.get('host_beam_id', '')
                        if debug_this:
                            logger.info("Beam ID string: '{}'".format(beam_id_str))
                        if beam_id_str:
                            # Explicit ElementId creation to avoid .NET overload ambiguity
                            beam_id_int = Int64.Parse(beam_id_str)
                            beam_id = ElementId(beam_id_int)
                            beam = doc.GetElement(beam_id)
                            if beam:
                                problematic_beams.append((beam, status))
                                if debug_this:
                                    logger.info("Successfully added problematic beam: {}".format(beam.Id))
                            else:
                                if debug_this:
                                    logger.info("Could not get beam element for ID: {}".format(beam_id))
                        else:
                            if debug_this:
                                logger.info("Empty beam_id_str for result: {}".format(result))
                    except Exception as e:
                        if debug_this:
                            logger.info("Error processing beam: {}".format(str(e)))
                        continue

            logger.info("Validation results status distribution: {}".format(status_counts))
            logger.info("Found {} problematic beams for issues view".format(len(problematic_beams)))

            # Apply color overrides based on status
            logger.info("Applying graphic overrides to {} problematic beams...".format(len(problematic_beams)))
            override_count = 0
            for beam, status in problematic_beams:
                try:
                    override = OverrideGraphicSettings()

                    # Get solid fill pattern for surfaces using proven library function
                    solid_pattern = None
                    if get_solid_fill_pattern:
                        try:
                            solid_pattern = get_solid_fill_pattern(doc)
                            if solid_pattern:
                                logger.info("Successfully got solid fill pattern: {}".format(solid_pattern))
                            else:
                                logger.warning("No solid fill pattern found using library function")
                        except Exception as e:
                            logger.error("Error getting solid pattern from library: {}".format(e))
                    else:
                        logger.warning("get_solid_fill_pattern function not available")

                    if status == 'Unmatched':
                        # Red for unmatched
                        red_color = Color(255, 0, 0)
                        override.SetProjectionLineColor(red_color)
                        override.SetCutLineColor(red_color)
                        override.SetSurfaceForegroundPatternColor(red_color)
                        override.SetSurfaceBackgroundPatternColor(red_color)
                        if solid_pattern:
                            override.SetSurfaceForegroundPatternId(solid_pattern)
                            override.SetSurfaceBackgroundPatternId(solid_pattern)
                            override.SetCutForegroundPatternId(solid_pattern)
                            logger.debug("Applied solid red override to beam {}".format(beam.Id))
                    elif status == 'Family unmatched':
                        # Orange for family unmatched
                        orange_color = Color(255, 165, 0)
                        override.SetProjectionLineColor(orange_color)
                        override.SetCutLineColor(orange_color)
                        override.SetSurfaceForegroundPatternColor(orange_color)
                        override.SetSurfaceBackgroundPatternColor(orange_color)
                        if solid_pattern:
                            override.SetSurfaceForegroundPatternId(solid_pattern)
                            override.SetSurfaceBackgroundPatternId(solid_pattern)
                            override.SetCutForegroundPatternId(solid_pattern)
                            logger.debug("Applied solid orange override to beam {}".format(beam.Id))
                    elif status == 'Dimension to be checked':
                        # Yellow for dimension check needed
                        yellow_color = Color(255, 255, 0)
                        override.SetProjectionLineColor(yellow_color)
                        override.SetCutLineColor(yellow_color)
                        override.SetSurfaceForegroundPatternColor(yellow_color)
                        override.SetSurfaceBackgroundPatternColor(yellow_color)
                        if solid_pattern:
                            override.SetSurfaceForegroundPatternId(solid_pattern)
                            override.SetSurfaceBackgroundPatternId(solid_pattern)
                            override.SetCutForegroundPatternId(solid_pattern)
                            logger.debug("Applied solid yellow override to beam {}".format(beam.Id))

                    new_view.SetElementOverrides(beam.Id, override)
                    override_count += 1
                except Exception as e:
                    logger.debug("Could not apply override to beam {}: {}".format(beam.Id, e))

            logger.info("Applied overrides to {} beams".format(override_count))

            # Hide approved beams (comment = "Approved")
            logger.info("Processing approved beams to hide...")
            approved_beams = []
            approved_count = 0
            for result in validation_results:
                if result.get('status') == 'Approved':
                    try:
                        beam_id_str = result.get('host_beam_id', '')
                        if beam_id_str:
                            beam_id_int = Int64.Parse(beam_id_str)
                            beam_id = ElementId(beam_id_int)
                            beam = doc.GetElement(beam_id)
                            if beam:
                                approved_beams.append(beam)
                                approved_count += 1
                                if approved_count <= 5:  # Log first 5 only
                                    logger.debug("Will hide approved beam: {}".format(beam.Id))
                    except Exception as e:
                        logger.debug("Error processing approved beam: {}".format(str(e)))
                        continue

            logger.info("Found {} approved beams to hide".format(len(approved_beams)))

            # Hide approved beams using HideElements method
            if approved_beams:
                try:
                    # Convert to ElementId collection
                    approved_ids = List[ElementId]()
                    for beam in approved_beams:
                        approved_ids.Add(beam.Id)

                    # Hide all approved beams at once
                    new_view.HideElements(approved_ids)
                    logger.info("Successfully hid {} approved beams using HideElements".format(len(approved_beams)))
                except Exception as e:
                    logger.warning("Could not hide approved beams using HideElements: {}".format(e))
                    # Fallback: try individual hiding
                    hidden_count = 0
                    for beam in approved_beams[:5]:  # Only try first 5 to avoid spam
                        try:
                            new_view.HideElements(List[ElementId]([beam.Id]))
                            hidden_count += 1
                        except:
                            pass
                    logger.info("Fallback: hid {} approved beams individually".format(hidden_count))
            else:
                logger.info("No approved beams to hide")

            # ================================================================
            # STEP 1: Collect ALL linked model instances
            # ================================================================
            logger.info("Collecting all linked Revit models in project...")
            link_instances = FilteredElementCollector(doc)\
                .OfClass(RevitLinkInstance)\
                .ToElements()

            all_link_ids = List[ElementId]()
            for link in link_instances:
                all_link_ids.Add(link.Id)
                logger.debug("Found link: {} (ID: {})".format(link.Name, link.Id))

            logger.info("Found {} linked Revit models total".format(len(link_instances)))

            # ================================================================
            # STEP 2: Set category visibility - EXCLUDE RvtLinks category
            # ================================================================
            logger.info("Setting category visibility for clean view...")

            try:
                # Define categories to keep visible (with transparency settings)
                visible_categories_config = {
                    'structural framing': {'transparency': 0, 'description': 'Host framing'},
                    'structuralframing': {'transparency': 0, 'description': 'Host framing (no space)'},
                    'structural columns': {'transparency': 50, 'description': 'Columns'},
                    'structuralcolumns': {'transparency': 50, 'description': 'Columns (no space)'},
                    'walls': {'transparency': 60, 'description': 'Walls'}
                }

                hidden_count = 0
                visible_count = 0
                rvt_links_category_found = False

                # Process each category using reliable name-based identification
                for category in doc.Settings.Categories:
                    try:
                        category_id = category.Id
                        category_name = category.Name if hasattr(category, 'Name') else ""
                        name_lower = category_name.lower()

                        # CRITICAL FIX: Skip RvtLinks category entirely
                        # We'll handle linked models as elements, not by category
                        if "rvt" in name_lower and "link" in name_lower:
                            rvt_links_category_found = True
                            logger.info("Skipping RvtLinks category: '{}' (will show links as elements)".format(category_name))
                            continue

                        # Check if this is a desired visible category
                        category_visible = False
                        transparency = 0
                        description = ""

                        # Match against our visible categories config
                        name_normalized = name_lower.replace(' ', '').replace('_', '')
                        for key, config in visible_categories_config.items():
                            key_normalized = key.replace(' ', '').replace('_', '')
                            if key_normalized in name_normalized:
                                category_visible = True
                                transparency = config['transparency']
                                description = config['description']
                                break

                        if category_visible:
                            # Keep these categories visible with specific transparency
                            new_view.SetCategoryHidden(category_id, False)

                            if transparency > 0:
                                # Apply transparency override
                                category_override = OverrideGraphicSettings()
                                category_override.SetSurfaceTransparency(transparency)
                                new_view.SetCategoryOverrides(category_id, category_override)
                                logger.debug("Set {}% transparency for: {} ({})".format(
                                    transparency, category_name, description))
                            else:
                                logger.debug("Kept visible (solid): {} ({})".format(
                                    category_name, description))

                            visible_count += 1
                        else:
                            # Hide all other categories
                            new_view.SetCategoryHidden(category_id, True)
                            hidden_count += 1

                    except Exception as cat_error:
                        logger.debug("Could not process category {}: {}".format(category.Name if hasattr(category, 'Name') else 'Unknown', cat_error))
                        # Continue with other categories
                        continue

            except Exception as e:
                logger.warning("Failed to set category visibility: {}".format(e))

            logger.info("Category visibility set: {} visible, {} hidden".format(
                visible_count, hidden_count))

            if not rvt_links_category_found:
                logger.warning("RvtLinks category not found - this is unusual")

            # ================================================================
            # STEP 3: Explicitly ensure ALL linked models are visible
            # ================================================================
            logger.info("Ensuring all linked models are visible...")

            if all_link_ids.Count > 0:
                try:
                    # First, unhide any that might be hidden
                    new_view.UnhideElements(all_link_ids)
                    logger.info("Successfully ensured {} linked models are visible".format(
                        all_link_ids.Count))

                    # Verify visibility
                    hidden_links = []
                    for link_id in all_link_ids:
                        link = doc.GetElement(link_id)
                        if link and link.IsHidden(new_view):
                            hidden_links.append(link_id)

                    if hidden_links:
                        logger.warning("{} links still hidden after unhide attempt".format(
                            len(hidden_links)))
                    else:
                        logger.info("All linked models confirmed visible")

                except Exception as e:
                    logger.error("Failed to unhide linked models: {}".format(e))
            else:
                logger.warning("No linked models found to unhide")

            # VALIDATION: Check if view will have visible elements before committing
            logger.info("Validating view visibility before commit...")
            visible_elements_count = 0

            # Quick check: count visible elements in the categories we care about
            for category in doc.Settings.Categories:
                try:
                    category_id = category.Id
                    category_name = category.Name if hasattr(category, 'Name') else ""

                    # Check if this is one of our desired visible categories using name
                    name_lower = category_name.lower()
                    is_desired_visible = (
                        "structural framing" in name_lower or "structuralframing" in name_lower or
                        "structural columns" in name_lower or "structuralcolumns" in name_lower or
                        name_lower == "walls"
                    )

                    if is_desired_visible:
                        # Check if category is not hidden
                        if not new_view.GetCategoryHidden(category_id):
                            visible_elements_count += 1
                            logger.debug("Found visible desired category: {}".format(category_name))
                            break  # We just need at least one visible category

                except Exception as check_error:
                    logger.debug("Could not check category {}: {}".format(category.Name if hasattr(category, 'Name') else 'Unknown', check_error))
                    continue

            if visible_elements_count == 0:
                logger.warning("WARNING: No visible categories found in issues view!")
                logger.warning("This may cause 'No good view could be found' error")
                logger.warning("Applying fallback: showing all structural categories")

                # FALLBACK: Show all structural categories if our selective approach fails
                for category in doc.Settings.Categories:
                    try:
                        category_id = category.Id
                        category_name = category.Name if hasattr(category, 'Name') else ""

                        # Show all structural-related categories as fallback using name matching
                        name_lower = category_name.lower()
                        is_structural = (
                            "structural" in name_lower or
                            name_lower in ["walls", "floors", "grids"]
                        )

                        if is_structural:
                            new_view.SetCategoryHidden(category_id, False)
                            logger.debug("Fallback: Made visible category: {}".format(category_name))

                    except Exception as fallback_error:
                        logger.debug("Fallback failed for category: {}".format(fallback_error))
                        continue

            logger.info("Committing transaction...")
            t.Commit()
            logger.info("Transaction committed successfully")

        logger.info("Created framing issues view: %s with %d problematic beams" % (view_name, len(problematic_beams)))
        return new_view

    except Exception as e:
        logger.error("Failed to create framing issues view: {}".format(e))
        return None


def compare_dimensions(host_dims, linked_dims):
    """
    Compares dimension parameters between host and linked beams.
    Converts feet to millimeters FIRST, then compares with 0.01mm tolerance.

    Args:
        host_dims (dict): Dimension dictionary from host beam (in feet)
        linked_dims (dict): Dimension dictionary from linked beam (in feet)

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

    if host_dims['type'] == 'square':
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

def set_comment_parameter(beam, comment_text):
    """
    Sets the comment parameter for a beam element.

    Args:
        beam (Element): The beam element to modify
        comment_text (str): The comment text to set

    Returns:
        bool: True if parameter was set successfully, False otherwise
    """
    try:
        comments_param = beam.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        if comments_param and not comments_param.IsReadOnly:
            comments_param.Set(comment_text)
            logger.debug("Set Comments parameter to '{}' for beam {}".format(comment_text, beam.Id))
            return True
        else:
            logger.warning("Could not set Comments parameter for beam {} (parameter not found or read-only)".format(beam.Id))
            return False
    except Exception as e:
        logger.warning("Failed to set Comments parameter for beam {}. Error: {}".format(beam.Id, e))
        return False


def process_beam_validation(host_beam, linked_beams_dict):
    """
    Processes dimension validation for a single host beam with family geometry type checking.

    Args:
        host_beam (Element): The host beam to validate
        linked_beams_dict (dict): Dictionary of linked beams with geometry

    Returns:
        tuple: (comment_text, validation_data)
            - comment_text (str): Comment text to set
            - validation_data (dict): Detailed validation information for CSV export
    """
    validation_data = {
        'host_beam_id': str(host_beam.Id),
        'linked_beam_id': None,
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

    # Get host beam family info
    try:
        host_family_symbol = get_family_type(host_beam)
        if host_family_symbol:
            validation_data['host_family_name'] = host_family_symbol.Family.Name
            validation_data['host_type_name'] = host_family_symbol.Name
    except Exception as e:
        validation_data['debug_info'] = "Host family info error: {}".format(str(e))

    # Find best geometric match
    best_match, intersection_volume = find_best_match(host_beam, linked_beams_dict)

    if not best_match:
        # No geometric intersection found
        validation_data['status'] = 'Unmatched'
        validation_data['intersection_volume_cu_ft'] = 0.0
        validation_data['intersection_volume_mm3'] = 0.0
        validation_data['debug_info'] = "No geometric intersection found"
        return "Unmatched", validation_data

    validation_data['linked_beam_id'] = str(best_match.Id)
    validation_data['intersection_volume_cu_ft'] = intersection_volume
    validation_data['intersection_volume_mm3'] = feet3_to_mm3(intersection_volume)

    # Get linked beam family info
    try:
        linked_family_symbol = get_family_type(best_match)
        if linked_family_symbol:
            validation_data['linked_family_name'] = linked_family_symbol.Family.Name
            validation_data['linked_type_name'] = linked_family_symbol.Name
    except Exception as e:
        validation_data['debug_info'] = "Linked family info error: {}".format(str(e))

    # Check family geometry types first
    host_family_type = get_family_geometry_type(host_beam)
    linked_family_type = get_family_geometry_type(best_match)

    validation_data['host_family_type'] = host_family_type
    validation_data['linked_family_type'] = linked_family_type

    if host_family_type != linked_family_type:
        # Family geometry types don't match
        validation_data['status'] = 'Family unmatched'
        validation_data['debug_info'] = "Family types don't match: {} vs {}".format(host_family_type, linked_family_type)
        return "Family unmatched", validation_data

    # Family types match, now check dimensions
    host_dims = get_beam_dimensions(host_beam)
    linked_dims = get_beam_dimensions(best_match)

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
    Main execution function that orchestrates the beam dimension validation process.

    Handles the complete workflow from model selection through results reporting,
    including error handling and user feedback.
    """
    # Step 1: Select the linked EXR model from available Revit links
    link_doc, selected_link = select_linked_model()

    # Step 2: Gather structural framing elements from both host and linked models
    host_beams = collect_host_beams()
    linked_beams = collect_linked_beams(link_doc)

    if not host_beams:
        forms.alert("No structural framing elements found in the host model. "
                   "Please ensure your model contains structural framing elements.", exitscript=True)

    if not linked_beams:
        forms.alert("No structural framing elements found in the linked EXR model. "
                   "Please ensure the linked model contains structural framing elements.", exitscript=True)

    # Log collection details
    debug_log("=== BEAM COLLECTION SUMMARY ===", level='NORMAL')
    debug_log("Host beams found: {}".format(len(host_beams)), level='NORMAL')
    debug_log("Linked beams found: {}".format(len(linked_beams)), level='NORMAL')

    # Log first few IDs for verification
    if host_beams:
        host_ids = [str(c.Id) for c in host_beams[:5]]
        debug_log("First 5 host beam IDs: {}".format(", ".join(host_ids)), level='VERBOSE')
        if len(host_beams) > 5:
            debug_log("... and {} more beams".format(len(host_beams) - 5), level='VERBOSE')

    if linked_beams:
        linked_ids = [str(c.Id) for c in linked_beams[:5]]
        debug_log("First 5 linked beam IDs: {}".format(", ".join(linked_ids)), level='VERBOSE')
        if len(linked_beams) > 5:
            debug_log("... and {} more linked beams".format(len(linked_beams) - 5), level='VERBOSE')

    debug_log("=" * 50, level='NORMAL')

    # Provide clear feedback about selection method used
    selection_ids = uidoc.Selection.GetElementIds()
    pre_selected_elements = []

    if selection_ids:
        for elem_id in selection_ids:
            elem = doc.GetElement(elem_id)
            if elem and elem.Category and elem.Category.Id == BuiltInCategory.OST_StructuralFraming:
                pre_selected_elements.append(elem)

    # Step 3: Extract and cache solid geometries for linked beams to optimize matching performance

    debug_log("=== LINKED BEAMS GEOMETRY PROCESSING START ===", level='NORMAL')
    debug_log("Total linked beams to process: {}".format(len(linked_beams)), level='NORMAL')

    linked_beams_dict = {}
    geometry_success_count = 0
    geometry_fail_count = 0

    with ProgressBar(title='Processing Linked Beam Geometry ({value} of {max_value})') as pb:
        for i, beam in enumerate(linked_beams):
            debug_log("Processing linked beam {}/{}: ID={}".format(i+1, len(linked_beams), beam.Id), level='VERBOSE')
            solid = get_solid(beam)
            if solid:
                linked_beams_dict[beam.Id] = {'element': beam, 'solid': solid}
                geometry_success_count += 1
            else:
                geometry_fail_count += 1
            pb.update_progress(i+1, len(linked_beams))

    debug_log("=== LINKED BEAMS GEOMETRY PROCESSING COMPLETE ===", level='NORMAL')
    debug_log("Total processed: {}".format(len(linked_beams)), level='NORMAL')
    debug_log("Geometry extraction successful: {} beams".format(geometry_success_count), level='NORMAL')
    debug_log("Geometry extraction failed: {} beams".format(geometry_fail_count), level='NORMAL')
    debug_log("Beams cached for matching: {}".format(len(linked_beams_dict)), level='NORMAL')

    # Log IDs of successfully processed beams
    if linked_beams_dict:
        successful_ids = [str(id.Value) for id in list(linked_beams_dict.keys())[:10]]  # First 10
        debug_log("First 10 successfully processed beam IDs: {}".format(successful_ids), level='VERBOSE')
        if len(linked_beams_dict) > 10:
            debug_log("... and {} more".format(len(linked_beams_dict) - 10), level='VERBOSE')

    # Geometry processing completed

    # Step 4: Validate dimensions for each host beam

    approved_count = 0
    family_unmatched_count = 0
    dimension_check_count = 0
    unmatched_count = 0
    validation_results = []

    # Process in transaction
    with Transaction(doc, 'Validate Beam Dimensions') as t:
        t.Start()

        with ProgressBar(title='Validating Beam Dimensions ({value} of {max_value})') as pb:
            for i, host_beam in enumerate(host_beams):
                comment, validation_data = process_beam_validation(host_beam, linked_beams_dict)
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
                set_comment_parameter(host_beam, comment)

                pb.update_progress(i+1, len(host_beams))

        # === CRITICAL: Print ALL Results BEFORE Commit ===
        output.print_md("## Results Summary")
        output.print_md("---")
        output.print_md("**Total beams processed**: {}".format(len(host_beams)))
        output.print_md("**Approved (family & dimensions match)**: {}".format(approved_count))
        output.print_md("**Family unmatched**: {}".format(family_unmatched_count))
        output.print_md("**Dimension to be checked**: {}".format(dimension_check_count))
        output.print_md("**Unmatched (no intersection)**: {}".format(unmatched_count))

        # Commit the transaction
        status = t.Commit()

        # === POST-COMMIT: Add view creation info to output if view was created ===
        if CREATE_ISSUES_VIEW and 'issues_view' in locals() and issues_view:
            output.print_md("")
            output.print_md("**3D Issues View Created**: {}".format(issues_view.Name))
            output.print_md("*Red*: Unmatched beams | *Orange*: Family unmatched | *Yellow*: Dimension check needed")

        if status != TransactionStatus.Committed:
            logger.warning("Transaction was not committed successfully")
            forms.alert("Failed to update beam comments. Please try again.", exitscript=True)

    # === SAFE ZONE: Post-commit operations ===
    # Export results to CSV (uses logger, not output.print_md)
    csv_path = export_validation_results_to_csv(validation_results, doc.Title)

    # Create 3D issues view for visual verification (post-commit to avoid transaction conflicts)
    issues_view = None
    if CREATE_ISSUES_VIEW:
        try:
            issues_view = create_framing_issues_view(validation_results, selected_link)
            if issues_view:
                logger.info("Created issues view: {}".format(issues_view.Name))
                # Try to show the view, but don't fail if it doesn't work
                try:
                    # Use RequestViewChange instead of ShowElements for better compatibility
                    uidoc.RequestViewChange(issues_view)
                    logger.info("Successfully switched to issues view")
                except Exception as show_error:
                    logger.warning("Could not switch to issues view automatically: {}".format(show_error))
                    logger.info("View created successfully but could not be shown. Please open manually: {}".format(issues_view.Name))
        except Exception as e:
            logger.warning("Failed to create issues view: {}".format(e))

    # Clean up geometry cache to free memory
    linked_beams_dict.clear()
    gc.collect()

    # Use logger for post-commit messages (safe) - REMOVE DUPLICATE LOGGING
    # CSV export function already logs the path, so we don't need to log it again
    # if csv_path:
    #     logger.info("Detailed results exported to: {}".format(csv_path))

    # Add debug summary only when debug is enabled (using logger, not output.print_md)
    if DEBUG_MODE:
        logger.info("=== DEBUG ANALYSIS SUMMARY ===")

        # Geometry extraction summary
        total_linked = len(linked_beams) if 'linked_beams' in locals() else 0
        cached_linked = len(linked_beams_dict) if 'linked_beams_dict' in locals() else 0

        logger.info("Geometry Processing:")
        logger.info("- Total linked beams: {}".format(total_linked))
        logger.info("- Successfully cached: {}".format(cached_linked))
        if total_linked > 0:
            success_rate = (cached_linked / float(total_linked)) * 100
            logger.info("- Success rate: {:.1f}%".format(success_rate))

        # Intersection analysis
        matched_results = [r for r in validation_results if r.get('intersection_volume_cu_ft', 0) > 0]
        unmatched_results = [r for r in validation_results if r.get('status') == 'Unmatched']

        logger.info("Matching Results:")
        logger.info("- Total host beams processed: {}".format(len(validation_results)))
        logger.info("- Beams with intersections: {}".format(len(matched_results)))
        logger.info("- Unmatched beams: {}".format(len(unmatched_results)))

        if matched_results:
            logger.info("Sample Intersection Volumes (first 5):")
            for result in matched_results[:5]:
                vol_cu_ft = result.get('intersection_volume_cu_ft', 0)
                vol_mm3 = result.get('intersection_volume_mm3', 0)
                status = result.get('status', 'Unknown')

                logger.info("- Host {} → Linked {}: {:.6f} cu ft ({:.0f} mm³) | {}".format(
                    result.get('host_beam_id', 'Unknown'),
                    result.get('linked_beam_id', 'Unknown'),
                    vol_cu_ft, vol_mm3, status
                ))

            if len(matched_results) > 5:
                logger.info("... and {} more matched beams".format(len(matched_results) - 5))
        else:
            logger.info("CRITICAL: No beams found with intersection volumes > 0")
            logger.info("This indicates geometry extraction failures or no actual intersections exist.")
            logger.info("Check pyRevit console logs for detailed geometry extraction errors.")

        logger.info("Next Steps:")
        logger.info("1. Check pyRevit console for geometry extraction logs")
        logger.info("2. Verify beam IDs in collection vs visual model")
        logger.info("3. Review CSV for complete intersection data")
        logger.info("=" * 80)

    # Show completion message (safe - uses forms.alert, not output.print_md)
    alert_message = "Beam dimension validation complete!\n\n"
    alert_message += "Approved: {} beams\n".format(approved_count)
    alert_message += "Family unmatched: {} beams\n".format(family_unmatched_count)
    alert_message += "Need checking: {} beams\n".format(dimension_check_count)
    alert_message += "Unmatched: {} beams\n".format(unmatched_count)
    alert_message += "\n\nCheck the Comments parameter on each beam for details."

    if CREATE_ISSUES_VIEW and issues_view:
        alert_message += "\n\n3D Issues View created: {}".format(issues_view.Name)

    forms.alert(alert_message, title="Validation Complete")


if __name__ == '__main__':
    main()

