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

def create_geometry_options():
    """
    Create minimal geometry options for solid extraction.
    
    Returns:
        Options: Configured geometry options
    """
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
    """
    Find the best matching linked element based on geometric intersection volume.
    
    Args:
        host_solid: Solid geometry of the host element
        linked_list: List of dicts with 'element' and 'solid' keys
        vol_threshold: Minimum volume threshold for a valid match
    
    Returns:
        tuple: (best_match element or None, max_volume float)
    """
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
        except Exception:
            # Boolean operations can fail for invalid/incompatible geometry
            # Silently continue to next candidate
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
        # Parameter access failed - element may not have expected parameters
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
    host_opts = create_geometry_options()
    link_opts = create_geometry_options()
    
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
            if not v.IsTemplate and v.ViewType == ViewType.ThreeD:
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


# ==============================================================================
# MODULAR FILTER SYSTEM - Chain of Responsibility Pattern
# ==============================================================================

class BaseFilter(object):
    """
    Base class for all filters.
    Each filter decides: PASS or REJECT
    """
    
    def __init__(self, enabled=True, **kwargs):
        """
        Args:
            enabled (bool): Whether this filter is active
            **kwargs: Filter-specific parameters
        """
        self.enabled = enabled
        self.params = kwargs
        self.stats = {
            'processed': 0,
            'passed': 0,
            'rejected': 0
        }
    
    @property
    def name(self):
        return self.__class__.__name__
    
    def filter(self, host_element, host_data, linked_candidates):
        """
        Filter linked candidates for a host element.
        
        Args:
            host_element: Host element
            host_data (dict): Pre-computed host data (solid, bbox, dims, etc)
            linked_candidates (list): List of candidate dicts
        
        Returns:
            list: Filtered candidates (subset of input)
        """
        raise NotImplementedError("Subclasses must implement filter()")
    
    def apply(self, host_element, host_data, linked_candidates):
        """Wrapper with statistics tracking"""
        if not self.enabled:
            return linked_candidates
        
        self.stats['processed'] += 1
        before = len(linked_candidates)
        
        filtered = self.filter(host_element, host_data, linked_candidates)
        
        after = len(filtered)
        self.stats['passed'] += after
        self.stats['rejected'] += (before - after)
        
        return filtered
    
    def get_stats(self):
        """Return filter statistics"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'stats': self.stats.copy()
        }
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = {'processed': 0, 'passed': 0, 'rejected': 0}


class LevelFilter(BaseFilter):
    """
    Filter 1: Level-based filtering
    Only keep candidates on the same level as host
    """
    
    def __init__(self, enabled=True, **kwargs):
        super(LevelFilter, self).__init__(enabled, **kwargs)
    
    def filter(self, host_element, host_data, linked_candidates):
        """Keep only same-level candidates"""
        host_level_id = host_data.get('level_id')
        
        if not host_level_id:
            return linked_candidates  # Can't filter without level
        
        filtered = []
        for candidate in linked_candidates:
            if candidate.get('level_id') == host_level_id:
                filtered.append(candidate)
        
        return filtered


class ConcreteBeamDimensionFilter(BaseFilter):
    """
    Filter 2: Concrete beam dimension matching (b and h)
    Only keep candidates with matching width and height
    """
    
    def __init__(self, enabled=True, tolerance_mm=1.0, **kwargs):
        """
        Args:
            tolerance_mm (float): Tolerance in millimeters (default 1.0mm)
        """
        super(ConcreteBeamDimensionFilter, self).__init__(enabled, **kwargs)
        self.tolerance_mm = tolerance_mm
        self.tolerance_ft = tolerance_mm / 304.8  # Convert to feet
    
    def filter(self, host_element, host_data, linked_candidates):
        """Keep only candidates with matching dimensions"""
        host_dims = host_data.get('dimensions')
        
        if not host_dims:
            return linked_candidates  # Can't filter without dimensions
        
        filtered = []
        for candidate in linked_candidates:
            candidate_dims = candidate.get('dimensions')
            if candidate_dims and self._dimensions_match(host_dims, candidate_dims):
                filtered.append(candidate)
        
        return filtered
    
    def _dimensions_match(self, dims1, dims2):
        """Check if two dimension sets match within tolerance"""
        # Check type compatibility
        if dims1.get('type') != dims2.get('type'):
            return False
        
        b1 = dims1.get('b')
        h1 = dims1.get('h')
        b2 = dims2.get('b')
        h2 = dims2.get('h')
        
        if None in [b1, h1, b2, h2]:
            return False
        
        # For square sections, only check one dimension
        if dims1['type'] == 'square':
            return abs(b1 - b2) <= self.tolerance_ft
        
        # For rectangular, check both
        b_match = abs(b1 - b2) <= self.tolerance_ft
        h_match = abs(h1 - h2) <= self.tolerance_ft
        
        return b_match and h_match


class ETABSTypeMarkFilter(BaseFilter):
    """
    Filter 3: Type Mark matching for ETABS comparison
    Uses existing extract_type_mark_from_type_name function
    """
    
    def __init__(self, enabled=True, use_prefix=True, exact_match=False, **kwargs):
        """
        Args:
            use_prefix (bool): Use prefix matching (e.g., GA1 matches GA1-300)
            exact_match (bool): Require exact match
        """
        super(ETABSTypeMarkFilter, self).__init__(enabled, **kwargs)
        self.use_prefix = use_prefix
        self.exact_match = exact_match
    
    def filter(self, host_element, host_data, linked_candidates):
        """Keep only candidates with matching Type Mark (ETABS mode)"""
        host_type_name = host_data.get('type_name')
        
        if not host_type_name:
            return linked_candidates
        
        # Extract type mark using existing function
        host_type_mark = extract_type_mark_from_type_name(host_type_name)
        
        if not host_type_mark:
            return linked_candidates
        
        filtered = []
        for candidate in linked_candidates:
            candidate_type_name = candidate.get('type_name')
            
            if not candidate_type_name:
                continue
            
            # Extract candidate type mark
            candidate_type_mark = extract_type_mark_from_type_name(candidate_type_name)
            
            if not candidate_type_mark:
                continue
            
            # Match
            if self.exact_match:
                if host_type_mark == candidate_type_mark:
                    filtered.append(candidate)
            elif self.use_prefix:
                if host_type_mark in candidate_type_mark or candidate_type_mark in host_type_mark:
                    filtered.append(candidate)
            else:
                if host_type_mark == candidate_type_mark:
                    filtered.append(candidate)
        
        return filtered


class RevitTypeMarkFilter(BaseFilter):
    """
    Filter 4: Type Mark matching for Revit-to-Revit comparison
    NEW - Compares Type Mark parameters between two Revit elements
    """
    
    def __init__(self, enabled=True, use_prefix=True, exact_match=False, **kwargs):
        """
        Args:
            use_prefix (bool): Use prefix matching
            exact_match (bool): Require exact match
        """
        super(RevitTypeMarkFilter, self).__init__(enabled, **kwargs)
        self.use_prefix = use_prefix
        self.exact_match = exact_match
    
    def filter(self, host_element, host_data, linked_candidates):
        """Keep only candidates with matching Type Mark (Revit mode)"""
        host_type_mark = host_data.get('type_mark')
        
        if not host_type_mark:
            return linked_candidates
        
        filtered = []
        for candidate in linked_candidates:
            candidate_type_mark = candidate.get('type_mark')
            
            if not candidate_type_mark:
                continue
            
            # Match
            if self.exact_match:
                if host_type_mark == candidate_type_mark:
                    filtered.append(candidate)
            elif self.use_prefix:
                if host_type_mark in candidate_type_mark or candidate_type_mark in host_type_mark:
                    filtered.append(candidate)
            else:
                if host_type_mark == candidate_type_mark:
                    filtered.append(candidate)
        
        return filtered


def extract_type_mark_from_element(element):
    """
    Extract Type Mark from a Revit element.
    
    Args:
        element: Revit element
    
    Returns:
        str: Type Mark value or None
    """
    try:
        type_mark_param = element.LookupParameter("Type Mark")
        if type_mark_param and type_mark_param.HasValue:
            return type_mark_param.AsString()
        return None
    except Exception:
        return None


class FamilyNameFilter(BaseFilter):
    """
    Filter 5: Family Name matching
    Only keep candidates from the same family
    """
    
    def __init__(self, enabled=True, exact_match=True, **kwargs):
        """
        Args:
            exact_match (bool): Require exact family name match
        """
        super(FamilyNameFilter, self).__init__(enabled, **kwargs)
        self.exact_match = exact_match
    
    def filter(self, host_element, host_data, linked_candidates):
        """Keep only candidates with matching family name"""
        host_family = host_data.get('family_name')
        
        if not host_family:
            return linked_candidates
        
        filtered = []
        for candidate in linked_candidates:
            candidate_family = candidate.get('family_name')
            
            if not candidate_family:
                continue
            
            if self.exact_match:
                if host_family == candidate_family:
                    filtered.append(candidate)
            else:
                if host_family.lower() in candidate_family.lower() or \
                   candidate_family.lower() in host_family.lower():
                    filtered.append(candidate)
        
        return filtered


class BoundingBoxFilter(BaseFilter):
    """
    Filter 6: Bounding box intersection with buffer
    Only keep candidates whose bbox intersects with host bbox (expanded)
    """
    
    def __init__(self, enabled=True, buffer_m=1.5, **kwargs):
        """
        Args:
            buffer_m (float): Buffer distance in meters (default 1.5m)
        """
        super(BoundingBoxFilter, self).__init__(enabled, **kwargs)
        self.buffer_m = buffer_m
        self.buffer_ft = buffer_m * 3.28084  # Convert to feet
    
    def filter(self, host_element, host_data, linked_candidates):
        """Keep only candidates with intersecting bounding boxes"""
        from Autodesk.Revit.DB import XYZ, BoundingBoxXYZ
        
        host_bbox = host_data.get('bbox')
        
        if not host_bbox:
            return linked_candidates
        
        # Expand host bbox
        expanded_bbox = self._expand_bbox(host_bbox)
        
        filtered = []
        for candidate in linked_candidates:
            candidate_bbox = candidate.get('bbox')
            if candidate_bbox and self._bboxes_intersect(expanded_bbox, candidate_bbox):
                filtered.append(candidate)
        
        return filtered
    
    def _expand_bbox(self, bbox):
        """Expand bounding box by buffer amount"""
        from Autodesk.Revit.DB import XYZ, BoundingBoxXYZ
        
        expanded = BoundingBoxXYZ()
        expanded.Min = XYZ(
            bbox.Min.X - self.buffer_ft,
            bbox.Min.Y - self.buffer_ft,
            bbox.Min.Z - self.buffer_ft
        )
        expanded.Max = XYZ(
            bbox.Max.X + self.buffer_ft,
            bbox.Max.Y + self.buffer_ft,
            bbox.Max.Z + self.buffer_ft
        )
        return expanded
    
    @staticmethod
    def _bboxes_intersect(bbox1, bbox2):
        """Check if two bounding boxes intersect"""
        return not (
            bbox1.Max.X < bbox2.Min.X or bbox1.Min.X > bbox2.Max.X or
            bbox1.Max.Y < bbox2.Min.Y or bbox1.Min.Y > bbox2.Max.Y or
            bbox1.Max.Z < bbox2.Min.Z or bbox1.Min.Z > bbox2.Max.Z
        )


class GeometryIntersectionFilter(BaseFilter):
    """
    Filter 7: Boolean geometry intersection (FINAL validator)
    Only keep candidates that actually intersect geometrically
    This is the most expensive filter - use LAST
    """
    
    def __init__(self, enabled=True, vol_threshold=1e-9, min_overlap_ratio=0.01, **kwargs):
        """
        Args:
            vol_threshold (float): Minimum intersection volume in cubic feet
            min_overlap_ratio (float): Minimum overlap ratio (intersection/host volume)
        """
        super(GeometryIntersectionFilter, self).__init__(enabled, **kwargs)
        self.vol_threshold = vol_threshold
        self.min_overlap_ratio = min_overlap_ratio
    
    def filter(self, host_element, host_data, linked_candidates):
        """Keep only candidates with geometric intersection"""
        from Autodesk.Revit.DB import BooleanOperationsUtils, BooleanOperationsType
        
        host_solid = host_data.get('solid')
        
        if not host_solid:
            return []
        
        host_volume = host_solid.Volume
        
        filtered = []
        for candidate in linked_candidates:
            candidate_solid = candidate.get('solid')
            
            if not candidate_solid:
                continue
            
            try:
                # Boolean intersection
                intersection = BooleanOperationsUtils.ExecuteBooleanOperation(
                    host_solid,
                    candidate_solid,
                    BooleanOperationsType.Intersect
                )
                
                if intersection and intersection.Volume > self.vol_threshold:
                    overlap_ratio = intersection.Volume / host_volume
                    
                    if overlap_ratio >= self.min_overlap_ratio:
                        # Store intersection volume for later ranking
                        candidate['intersection_volume'] = intersection.Volume
                        candidate['overlap_ratio'] = overlap_ratio
                        filtered.append(candidate)
                        
            except Exception:
                # Boolean operation failed - skip this candidate
                continue
        
        return filtered


class FilterPipeline(object):
    """
    Configurable filter pipeline.
    Filters are applied in sequence - each reduces the candidate pool.
    """
    
    def __init__(self, filters=None):
        """
        Args:
            filters (list): List of BaseFilter instances in desired order
        """
        self.filters = filters if filters else []
    
    def add_filter(self, filter_instance):
        """Add a filter to the pipeline"""
        self.filters.append(filter_instance)
    
    def remove_filter(self, filter_class):
        """Remove all filters of a given class"""
        self.filters = [f for f in self.filters if not isinstance(f, filter_class)]
    
    def get_filter(self, filter_class):
        """Get first filter of given class"""
        for f in self.filters:
            if isinstance(f, filter_class):
                return f
        return None
    
    def apply(self, host_element, host_data, linked_candidates):
        """
        Apply all filters in sequence.
        
        Returns:
            list: Final filtered candidates after all filters
        """
        current_candidates = linked_candidates
        
        for filter_instance in self.filters:
            if not filter_instance.enabled:
                continue
            
            current_candidates = filter_instance.apply(
                host_element, 
                host_data, 
                current_candidates
            )
            
            # Early exit if no candidates left
            if not current_candidates:
                break
        
        return current_candidates
    
    def get_stats(self):
        """Get statistics from all filters"""
        return [f.get_stats() for f in self.filters]
    
    def reset_stats(self):
        """Reset statistics for all filters"""
        for f in self.filters:
            f.reset_stats()
    
    def get_enabled_filters(self):
        """Get list of enabled filter names"""
        return [f.name for f in self.filters if f.enabled]


def create_default_pipeline():
    """
    Create default filter pipeline with recommended order.
    
    Filter order (cheap to expensive):
    1. Level (cheapest - simple ID comparison)
    2. Type Mark (cheap - string comparison)
    3. Family Name (cheap - string comparison)
    4. Bounding Box (moderate - 6 float comparisons)
    5. Concrete Beam Dimensions (moderate - 2-4 float comparisons)
    6. Geometry Intersection (EXPENSIVE - Boolean operation)
    """
    pipeline = FilterPipeline()
    
    pipeline.add_filter(LevelFilter(enabled=True))
    pipeline.add_filter(ETABSTypeMarkFilter(enabled=True, use_prefix=True))
    pipeline.add_filter(RevitTypeMarkFilter(enabled=True, use_prefix=True))
    pipeline.add_filter(FamilyNameFilter(enabled=True, exact_match=True))
    pipeline.add_filter(BoundingBoxFilter(enabled=True, buffer_m=1.5))
    pipeline.add_filter(ConcreteBeamDimensionFilter(enabled=True, tolerance_mm=1.0))
    pipeline.add_filter(GeometryIntersectionFilter(enabled=True, vol_threshold=1e-9))
    
    return pipeline


def extract_element_data(element, options, link_transform=None):
    """
    Extract all relevant data from an element for filtering.
    
    Args:
        element: Element
        options: Geometry options
        link_transform: Transform for linked elements (optional)
    
    Returns:
        dict: {
            'element': element,
            'solid': Solid,
            'bbox': BoundingBoxXYZ,
            'dimensions': {'b': float, 'h': float, 'type': str},
            'type_name': str,
            'type_mark': str,
            'family_name': str,
            'level_id': ElementId
        }
    """
    from Autodesk.Revit.DB import BuiltInParameter, SolidUtils
    
    data = {'element': element}
    
    # Geometry - Solid
    solid = get_solid(element, options)
    if solid and link_transform:
        solid = SolidUtils.CreateTransformed(solid, link_transform)
    
    data['solid'] = solid
    
    # Geometry - Bounding Box
    try:
        bbox = element.get_BoundingBox(None)
        if bbox and link_transform:
            # Transform bbox
            new_min = link_transform.OfPoint(bbox.Min)
            new_max = link_transform.OfPoint(bbox.Max)
            from Autodesk.Revit.DB import BoundingBoxXYZ
            transformed_bbox = BoundingBoxXYZ()
            transformed_bbox.Min = new_min
            transformed_bbox.Max = new_max
            data['bbox'] = transformed_bbox
        else:
            data['bbox'] = bbox
    except:
        data['bbox'] = None
    
    # Dimensions - for beams
    data['dimensions'] = get_beam_dimensions(element)
    
    # Type Name
    try:
        if hasattr(element, 'Symbol') and element.Symbol:
            type_name_param = element.Symbol.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
            data['type_name'] = type_name_param.AsString() if type_name_param else None
        else:
            data['type_name'] = None
    except:
        data['type_name'] = None
    
    # Type Mark (Revit parameter)
    data['type_mark'] = extract_type_mark_from_element(element)
    
    # Family Name
    try:
        if hasattr(element, 'Symbol') and element.Symbol and hasattr(element.Symbol, 'FamilyName'):
            data['family_name'] = element.Symbol.FamilyName
        else:
            data['family_name'] = None
    except:
        data['family_name'] = None
    
    # Level
    try:
        level_param = element.get_Parameter(BuiltInParameter.INSTANCE_REFERENCE_LEVEL_PARAM)
        data['level_id'] = level_param.AsElementId() if level_param else None
    except:
        data['level_id'] = None
    
    return data


def match_elements_modular(link_doc, link_instance, host_elements=None, 
                           element_category=None,
                           uidoc=None, doc=None, filter_pipeline=None):
    """
    Modular element matching with configurable filter pipeline.
    
    Args:
        link_doc: Linked document
        link_instance: RevitLinkInstance (for transform)
        host_elements: List of host elements (optional)
        element_category: BuiltInCategory for filtering (optional)
        uidoc: UIDocument (optional)
        doc: Document (optional)
        filter_pipeline: FilterPipeline instance (optional, creates default if None)
    
    Returns:
        dict: {
            'matches': [(host, linked, volume), ...],
            'unmatched': [host_elements],
            'stats': {...},
            'filter_stats': [...]
        }
    """
    import time
    from pyrevit import revit
    from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector
    
    if doc is None:
        doc = revit.doc
    if uidoc is None:
        uidoc = revit.uidoc
    
    start_time = time.time()
    
    # Get link transform
    link_transform = link_instance.GetTotalTransform()
    
    # Collect elements
    if not host_elements:
        preselect = uidoc.Selection.GetElementIds()
        host_elements = []
        for eid in preselect:
            elem = doc.GetElement(eid)
            if elem:
                if element_category is None or (elem.Category and elem.Category.BuiltInCategory == element_category):
                    host_elements.append(elem)
    
    if not host_elements or not link_doc:
        return {
            'matches': [],
            'unmatched': host_elements if host_elements else [],
            'stats': {},
            'filter_stats': []
        }
    
    # Collect linked elements
    linked_elements = list(
        FilteredElementCollector(link_doc)
        .OfCategory(element_category)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    
    if not linked_elements:
        return {
            'matches': [],
            'unmatched': host_elements,
            'stats': {'error': 'No linked elements found'},
            'filter_stats': []
        }
    
    # Create default pipeline if none provided
    if filter_pipeline is None:
        filter_pipeline = create_default_pipeline()
    
    # Geometry options
    host_opts = create_geometry_options()
    link_opts = create_geometry_options()
    
    # Pre-extract ALL linked element data (cache)
    print("Extracting linked element data...")
    linked_data_list = []
    for le in linked_elements:
        data = extract_element_data(le, link_opts, link_transform)
        if data.get('solid') or data.get('bbox'):  # Cache elements with geometry
            linked_data_list.append(data)
    
    print("Cached {} linked elements with valid data".format(len(linked_data_list)))
    
    # Match each host element
    print("\nMatching {} host elements...".format(len(host_elements)))
    matches = []
    unmatched = []
    
    for idx, he in enumerate(host_elements):
        # Extract host data
        host_data = extract_element_data(he, host_opts, None)
        
        if not host_data.get('solid') and not host_data.get('bbox'):
            unmatched.append(he)
            continue
        
        # Apply filter pipeline
        filtered_candidates = filter_pipeline.apply(
            he,
            host_data,
            linked_data_list
        )
        
        # Find best match from filtered candidates
        if filtered_candidates:
            # Sort by intersection volume (stored by GeometryIntersectionFilter)
            filtered_candidates.sort(
                key=lambda c: c.get('intersection_volume', 0),
                reverse=True
            )
            
            best_candidate = filtered_candidates[0]
            matches.append((
                he,
                best_candidate['element'],
                best_candidate.get('intersection_volume', 0)
            ))
        else:
            unmatched.append(he)
        
        # Progress
        if (idx + 1) % 50 == 0:
            print("  Processed {}/{}".format(idx + 1, len(host_elements)))
    
    total_time = time.time() - start_time
    
    print("\n=== MATCHING COMPLETE ===")
    print("Total time: {:.1f}s".format(total_time))
    print("Matches: {}/{}".format(len(matches), len(host_elements)))
    print("Match rate: {:.1f}%".format(100.0 * len(matches) / len(host_elements)))
    
    return {
        'matches': matches,
        'unmatched': unmatched,
        'time_s': total_time,
        'match_rate': len(matches) / len(host_elements) if host_elements else 0,
        'stats': {
            'n_host': len(host_elements),
            'n_linked': len(linked_elements),
            'n_linked_valid': len(linked_data_list),
            'time_per_element_s': total_time / len(host_elements) if host_elements else 0
        },
        'filter_stats': filter_pipeline.get_stats()
    }
