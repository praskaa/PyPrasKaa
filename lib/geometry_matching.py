# -*- coding: utf-8 -*-
"""
Geometry Matching Library - BACK TO BASICS + REAL OPTIMIZATIONS
Focus: Remove overhead, optimize only what matters.

Usage:
    from lib.geometry_matching import match_beams
    results = match_beams(link_doc, vol_threshold=1e-6)

Modules in this file:
    - Geometry extraction (get_solid, get_column_dimensions)
    - Matching algorithms (find_best_match)
    - Dimension comparison (compare_dimensions)
    - Main matching workflow (match_beams)
    - Utilities (feet3_to_mm3, debug_log)
"""

import gc
import time
import re
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, BuiltInParameter,
    Solid, BooleanOperationsType, BooleanOperationsUtils,
    Options, GeometryInstance, ElementId, View, ViewType
)
from pyrevit import revit, script

# Metric conversion
FEET3_TO_MM3 = 28316846.592

def create_geometry_options(doc):
    """Minimal geometry options."""
    options = Options()
    options.ComputeReferences = False
    options.IncludeNonVisibleObjects = False
    return options

def collect_beams(doc, preselect_ids=None):
    """Collect structural framing beams."""
    if preselect_ids and len(preselect_ids) > 0:
        beams = []
        cat_id = ElementId(BuiltInCategory.OST_StructuralFraming)
        for eid in preselect_ids:
            elem = doc.GetElement(eid)
            if elem and elem.Category and elem.Category.Id == cat_id:
                beams.append(elem)
        if beams:
            return beams
    
    return list(
        FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_StructuralFraming)
        .WhereElementIsNotElementType()
        .ToElements()
    )

def get_solid(element, options):
    """Get largest solid - simple and fast."""
    geom = element.get_Geometry(options)
    if not geom:
        return None
    
    # Just get first solid with decent volume
    for g in geom:
        if isinstance(g, Solid) and g.Volume > 1e-6:
            return g
        elif isinstance(g, GeometryInstance):
            inst_geom = g.GetInstanceGeometry()
            if inst_geom:
                for ig in inst_geom:
                    if isinstance(ig, Solid) and ig.Volume > 1e-6:
                        return ig
    return None

def find_best_match(host_solid, linked_list, vol_threshold):
    """Simple direct matching - no fancy tricks."""
    best_match = None
    max_vol = 0
    
    for data in linked_list:
        try:
            inter = BooleanOperationsUtils.ExecuteBooleanOperation(
                host_solid, data['solid'], BooleanOperationsType.Intersect
            )
            
            if inter:
                vol = inter.Volume
                if vol > max_vol and vol > vol_threshold:
                    max_vol = vol
                    best_match = data['element']
        except:
            pass
    
    return best_match, max_vol


def get_beam_dimensions(beam):
    """
    Extracts dimension parameters from a beam element.
    Returns dimensions in FEET (Revit internal units).
    
    Args:
        beam (Element): The beam element to extract dimensions from.
    
    Returns:
        dict or None: {'b': float, 'h': float, 'type': str} or None if not found.
    """
    try:
        # Try to get 'b' parameter (width/depth)
        b_param = beam.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_WIDTH)
        if not b_param or not b_param.HasValue:
            b_param = beam.LookupParameter("b") or beam.LookupParameter("B") or beam.LookupParameter("Width")
            if not b_param and beam.Symbol:
                b_param = beam.Symbol.LookupParameter("b") or beam.Symbol.LookupParameter("B") or beam.Symbol.LookupParameter("Width")
        
        # Try to get 'h' parameter (height)
        h_param = beam.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_HEIGHT)
        if not h_param or not h_param.HasValue:
            h_param = beam.LookupParameter("h") or beam.LookupParameter("H") or beam.LookupParameter("Height")
            if not h_param and beam.Symbol:
                h_param = beam.Symbol.LookupParameter("h") or beam.Symbol.LookupParameter("H") or beam.Symbol.LookupParameter("Height")
        
        b_value = b_param.AsDouble() if b_param and b_param.HasValue else None
        h_value = h_param.AsDouble() if h_param and h_param.HasValue else None
        
        if b_value is not None and h_value is not None:
            if abs(b_value - h_value) < 1e-6:  # Square if b ≈ h
                return {'b': b_value, 'h': b_value, 'type': 'square'}
            else:
                return {'b': b_value, 'h': h_value, 'type': 'rectangular'}
        elif b_value is not None:
            return {'b': b_value, 'h': b_value, 'type': 'square'}
        
        return None
    except Exception:
        return None


def compare_dimensions(host_dims, linked_dims, tolerance_mm=0.01):
    """
    Compares dimension parameters between host and linked beams.
    
    Args:
        host_dims (dict): Dimensions from host beam (in feet)
        linked_dims (dict): Dimensions from linked beam (in feet)
        tolerance_mm (float): Tolerance in mm (default 0.01)
    
    Returns:
        bool: True if dimensions match within tolerance
    """
    if not host_dims or not linked_dims:
        return False
    
    if host_dims.get('type') != linked_dims.get('type'):
        return False
    
    # Convert feet to mm for comparison
    def feet_to_mm(feet_value):
        return feet_value * 304.8  # 1 ft = 304.8 mm
    
    tolerance_ft = tolerance_mm / 304.8  # Convert tolerance to feet
    
    if host_dims['type'] == 'square':
        host_b = host_dims.get('b')
        linked_b = linked_dims.get('b')
        if host_b is None or linked_b is None:
            return False
        return abs(host_b - linked_b) <= tolerance_ft
    
    elif host_dims['type'] == 'rectangular':
        host_b = host_dims.get('b')
        host_h = host_dims.get('h')
        linked_b = linked_dims.get('b')
        linked_h = linked_dims.get('h')
        if None in [host_b, host_h, linked_b, linked_h]:
            return False
        b_match = abs(host_b - linked_b) <= tolerance_ft
        h_match = abs(host_h - linked_h) <= tolerance_ft
        return b_match and h_match
    
    return False

def match_beams(link_doc, host_beams=None, uidoc=None, doc=None, vol_threshold=1e-9, validate_dimensions=False, dim_tolerance_mm=0.01):
    """
    Match beams - simple and reliable.
    
    Args:
        link_doc: Linked document (required)
        host_beams: Host beams (optional)
        uidoc: UIDocument (optional)
        doc: Document (optional)
        vol_threshold: Min volume in cu ft (default 1e-9)
        validate_dimensions: If True, also validate dimensions after geometry match (default False)
        dim_tolerance_mm: Dimension tolerance in mm (default 0.01)
    
    Returns:
        dict with matches, unmatched, time_s, match_rate, stats
    """
    if doc is None:
        doc = revit.doc
    if uidoc is None:
        uidoc = revit.uidoc
    
    start = time.time()
    
    # Collect
    if not host_beams:
        preselect = uidoc.Selection.GetElementIds()
        host_beams = collect_beams(doc, preselect)
    
    if not host_beams or not link_doc:
        return {'matches': [], 'unmatched': [], 'time_s': 0, 'match_rate': 0, 'stats': {}}
    
    linked_beams = collect_beams(link_doc)
    if not linked_beams:
        return {'matches': [], 'unmatched': host_beams, 'time_s': time.time() - start, 'match_rate': 0, 'stats': {}}
    
    # Options
    host_opts = create_geometry_options(doc)
    link_opts = create_geometry_options(link_doc)
    
    # Cache linked (simple list)
    cache_start = time.time()
    linked_list = []
    for lb in linked_beams:
        solid = get_solid(lb, link_opts)
        if solid:
            linked_list.append({'element': lb, 'solid': solid})
    cache_time = time.time() - cache_start
    
    # Match
    match_start = time.time()
    matches = []
    unmatched = []
    
    for idx, hb in enumerate(host_beams):
        host_solid = get_solid(hb, host_opts)
        if not host_solid:
            unmatched.append(hb)
            continue
        
        match, vol = find_best_match(host_solid, linked_list, vol_threshold)
        
        if match:
            if validate_dimensions:
                host_dims = get_beam_dimensions(hb)
                linked_dims = get_beam_dimensions(match)
                if host_dims and linked_dims and compare_dimensions(host_dims, linked_dims, dim_tolerance_mm):
                    matches.append((hb, match, vol))
                else:
                    unmatched.append(hb)  # Dimensions don't match
            else:
                matches.append((hb, match, vol))
        else:
            unmatched.append(hb)
        
        # GC every 200 beams
        if (idx + 1) % 200 == 0:
            gc.collect()
    
    match_time = time.time() - match_start
    total = time.time() - start
    n = len(host_beams)
    
    gc.collect()
    
    return {
        'matches': matches,
        'unmatched': unmatched,
        'time_s': total,
        'match_rate': len(matches) / n if n > 0 else 0,
        'stats': {
            'n_host': n,
            'n_linked': len(linked_beams),
            'n_cached': len(linked_list),
            'cache_time_s': cache_time,
            'match_time_s': match_time,
            'time_per_beam_s': total / n if n > 0 else 0
        }
    }
def extract_type_mark_from_type_name(type_name):
    """
    Extracts the Type Mark prefix from Type Name (front part like GA1, G9, GB9, B4).

    Args:
        type_name (str): The Type Name parameter value
        
    Returns:
        str: The extracted Type Mark or None if pattern not found
    """
    if not type_name:
        return None
    
    # Pattern: Starts with uppercase letters followed by digits (e.g., GA1, G9, GB9, B4)
    pattern = r'^([A-Z]+\d+)'
    match = re.search(pattern, type_name)
    
    if match:
        return match.group(1)
    else:
        return None


# ==============================================================================
# EXTENDED UTILITIES - For EXR Framing & Column Tools
# ==============================================================================

def feet3_to_mm3(volume_cu_ft):
    """
    Convert cubic feet to cubic millimeters for better readability.
    
    Args:
        volume_cu_ft (float): Volume in cubic feet (Revit internal units)
    
    Returns:
        float: Volume in cubic millimeters
    """
    return volume_cu_ft * FEET3_TO_MM3


def create_geometry_options_with_view(doc):
    """
    Create geometry options with proper view context.
    
    Args:
        doc: Revit Document
    
    Returns:
        Options: Geometry options configured with active view or fallback 3D view
    """
    app = doc.Application
    options = app.Create.NewGeometryOptions()
    
    active_view = doc.ActiveView
    if active_view:
        options.View = active_view
    else:
        # If no active view, find any 3D view to get geometry
        view_collector = FilteredElementCollector(doc).OfClass(View)
        for v in view_collector:
            if not v.IsTemplates and v.ViewType == ViewType.ThreeD:
                options.View = v
                break
    
    return options


# Debug logging configuration
DEBUG_LEVELS = {
    False: -1,        # No debug output
    'MINIMAL': 0,     # Only essential progress info
    'NORMAL': 1,      # Standard operation logs
    'VERBOSE': 2,     # Detailed operation logs
    'DIAGNOSTIC': 3   # Full diagnostic logs
}


def debug_log(message, level='NORMAL', force=False, debug_mode=False, logger=None):
    """
    Smart logging function with debug toggle support.
    
    Args:
        message (str): Log message
        level (str): Debug level ('MINIMAL', 'NORMAL', 'VERBOSE', 'DIAGNOSTIC')
        force (bool): Force logging regardless of debug mode
        debug_mode (bool or str): Current debug mode setting
        logger: Logger instance (optional, will get from pyrevit if not provided)
    """
    if not force and not debug_mode:
        return
    
    # Get logger if not provided
    if logger is None:
        try:
            logger = script.get_logger()
        except:
            pass
    
    if logger is None:
        return
    
    # Determine current debug level
    if debug_mode is False:
        current_level = -1
    elif debug_mode is True:
        current_level = DEBUG_LEVELS['DIAGNOSTIC']
    else:
        current_level = DEBUG_LEVELS.get(debug_mode, DEBUG_LEVELS['NORMAL'])
    
    required_level = DEBUG_LEVELS.get(level, DEBUG_LEVELS['NORMAL'])
    
    if current_level >= required_level or force:
        if level in ('MINIMAL', 'NORMAL'):
            logger.info(message)
        elif level in ('VERBOSE', 'DIAGNOSTIC'):
            logger.debug(message)


def get_solid_with_debug(element, options, debug_mode=False, logger=None, element_id=None):
    """
    Extracts the solid geometry from a given element with optional debug logging.
    
    Args:
        element: Revit element to extract geometry from
        options: Geometry options
        debug_mode (bool or str): Debug mode setting
        logger: Logger instance
        element_id: Element ID for debug messages
    
    Returns:
        Solid or None: The extracted solid geometry
    """
    debug_log(
        "=== GEOMETRY EXTRACTION DEBUG for Element {} ===".format(element_id or element.Id),
        level='DIAGNOSTIC',
        debug_mode=debug_mode,
        logger=logger
    )

    try:
        geom_element = element.get_Geometry(options)
        debug_log(
            "Geometry element retrieved: {}".format(geom_element is not None),
            level='DIAGNOSTIC',
            debug_mode=debug_mode,
            logger=logger
        )

        if not geom_element:
            debug_log(
                "❌ FAILED: No geometry found for element {}".format(element_id or element.Id),
                level='VERBOSE',
                debug_mode=debug_mode,
                logger=logger
            )
            return None

        solids = []
        geom_count = 0

        for geom_obj in geom_element:
            geom_count += 1

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

        # If multiple solids exist, unite them into a single solid
        if len(solids) > 1:
            main_solid = solids[0]
            for s in solids[1:]:
                try:
                    main_solid = BooleanOperationsUtils.ExecuteBooleanOperation(
                        main_solid, s, BooleanOperationsType.Union
                    )
                except Exception as e:
                    debug_log(
                        "Could not unite solids for element {}: {}".format(
                            element_id or element.Id, e
                        ),
                        level='VERBOSE',
                        debug_mode=debug_mode,
                        logger=logger
                    )
            return main_solid
        else:
            return solids[0]

    except Exception as e:
        debug_log(
            "❌ CRITICAL ERROR in geometry extraction for element {}: {}".format(
                element_id or element.Id, e
            ),
            level='NORMAL',
            debug_mode=debug_mode,
            logger=logger
        )
        return None


def get_column_dimensions(column):
    """
    Extracts dimension parameters from a column element.
    Returns dimensions in FEET (Revit internal units).
    
    Args:
        column (Element): The column element to extract dimensions from.
    
    Returns:
        dict or None: {'b': float, 'h': float, 'type': str} or None if not found.
    """
    try:
        # Try to get 'b' parameter (width)
        b_param = column.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_WIDTH)
        if not b_param or not b_param.HasValue:
            b_param = column.LookupParameter("b") or column.LookupParameter("B") or column.LookupParameter("Width")
            if not b_param and hasattr(column, 'Symbol'):
                b_param = column.Symbol.LookupParameter("b") or column.Symbol.LookupParameter("B") or column.Symbol.LookupParameter("Width")
        
        # Try to get 'h' parameter (depth)
        h_param = column.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_DEPTH)
        if not h_param or not h_param.HasValue:
            h_param = column.LookupParameter("h") or column.LookupParameter("H") or column.LookupParameter("Depth")
            if not h_param and hasattr(column, 'Symbol'):
                h_param = column.Symbol.LookupParameter("h") or column.Symbol.LookupParameter("H") or column.Symbol.LookupParameter("Depth")
        
        b_value = b_param.AsDouble() if b_param and b_param.HasValue else None
        h_value = h_param.AsDouble() if h_param and h_param.HasValue else None
        
        if b_value is not None and h_value is not None:
            if abs(b_value - h_value) < 1e-6:  # Square if b ≈ h
                return {'b': b_value, 'h': b_value, 'type': 'square'}
            else:
                return {'b': b_value, 'h': h_value, 'type': 'rectangular'}
        elif b_value is not None:
            return {'b': b_value, 'h': b_value, 'type': 'square'}
        
        return None
    except Exception:
        return None