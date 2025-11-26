# -*- coding: utf-8 -*-
"""Create Dimension Lines between Grids and Wall Edges (Faces + Endpoints) - FIXED VERSION."""
__title__ = 'Dimension\nGrids with Walls'

# pyRevit imports
from pyrevit import revit, DB, forms
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from Autodesk.Revit import Exceptions

# Standard library imports
import math
import traceback

# Set the active Revit application and document
app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
active_view = doc.ActiveView
print("Script started, active view: {} type: {}".format(active_view.Name, active_view.ViewType))

# Selection Filter
class CustomISelectionFilter(ISelectionFilter):
    def __init__(self, cat):
        self.cat = cat
    
    def AllowElement(self, e):
        if e.Category.Id.IntegerValue == int(self.cat):
            return True
        else:
            return False
    
    @staticmethod
    def AllowReference(ref, point):
        return True


def get_wall_location_line(wall):
    """Get the location line of a wall."""
    loc = wall.Location
    if isinstance(loc, DB.LocationCurve):
        return loc.Curve
    return None

def is_parallel(vec1, vec2, tolerance=0.017):  # ~1 degree
    """Check if two vectors are parallel."""
    v1 = vec1.Normalize()
    v2 = vec2.Normalize()
    dot = abs(v1.DotProduct(v2))
    return dot > (1.0 - tolerance)

def is_perpendicular(vec1, vec2, tolerance=0.017):  # ~1 degree
    """Check if two vectors are perpendicular."""
    v1 = vec1.Normalize()
    v2 = vec2.Normalize()
    dot = abs(v1.DotProduct(v2))
    return dot < tolerance

def get_wall_edge_references(wall, view):
    """Get references to wall edges (faces) for dimensioning in plan view.

    In plan views, we need to get edge references rather than face references.
    Returns tuple: (exterior_edge_ref, interior_edge_ref)
    """
    try:
        # Get wall geometry with references
        options = DB.Options()
        options.View = view
        options.ComputeReferences = True
        geom_elem = wall.get_Geometry(options)

        exterior_ref = None
        interior_ref = None

        # Get wall location curve to determine direction
        loc = wall.Location
        if not isinstance(loc, DB.LocationCurve):
            return (None, None)

        curve = loc.Curve
        if not isinstance(curve, DB.Line):
            return (None, None)

        wall_dir = (curve.GetEndPoint(1) - curve.GetEndPoint(0)).Normalize()
        wall_normal = DB.XYZ.BasisZ.CrossProduct(wall_dir).Normalize()

        # Look for edges in the wall geometry that represent the faces
        for geom_obj in geom_elem:
            if isinstance(geom_obj, DB.Solid):
                # Get edges from the solid
                edges = geom_obj.Edges
                for edge in edges:
                    if isinstance(edge, DB.Edge):
                        # Check if this edge is approximately vertical (represents a wall face)
                        start_pt = edge.AsCurve().GetEndPoint(0)
                        end_pt = edge.AsCurve().GetEndPoint(1)

                        # Edge direction should be vertical (Z-direction)
                        edge_dir = (end_pt - start_pt).Normalize()
                        if abs(edge_dir.Z) > 0.9:  # Nearly vertical edge
                            edge_ref = edge.Reference
                            if edge_ref:
                                # Determine exterior vs interior based on position relative to wall center
                                # Get wall center point
                                wall_center = (curve.GetEndPoint(0) + curve.GetEndPoint(1)) / 2.0
                                edge_center = (start_pt + end_pt) / 2.0

                                # Project edge center onto wall normal direction
                                vec_to_edge = edge_center - wall_center
                                projection = vec_to_edge.DotProduct(wall_normal)

                                if projection > 0:
                                    # Exterior side
                                    if exterior_ref is None:
                                        exterior_ref = edge_ref
                                else:
                                    # Interior side
                                    if interior_ref is None:
                                        interior_ref = edge_ref

        return (exterior_ref, interior_ref)

    except Exception as e:
        print("Error getting wall edge references: {}".format(str(e)))
        return (None, None)


def get_wall_endpoint_positions(wall):
    """Get wall endpoint positions from LocationCurve (simpler and more reliable than references).

    Returns tuple: (start_xyz, end_xyz)
    """
    try:
        # Get the wall's location curve for endpoint positions
        loc = wall.Location
        if isinstance(loc, DB.LocationCurve):
            curve = loc.Curve
            if isinstance(curve, DB.Line):
                start_point = curve.GetEndPoint(0)
                end_point = curve.GetEndPoint(1)
                return (start_point, end_point)

        return (None, None)

    except Exception as e:
        print("Error getting wall endpoint positions: {}".format(str(e)))
        return (None, None)


def group_grids_by_direction(grids):
    """Group grids by their direction (parallel grids together).
    
    Returns: List of grid groups, each group is a list of grids with same direction
    """
    if not grids:
        return []
    
    groups = []
    used_grids = set()
    
    for grid in grids:
        if grid.Id in used_grids:
            continue
        
        if grid.IsCurved:
            continue
        
        # Start new group with this grid
        crv = grid.Curve
        p = crv.GetEndPoint(0)
        q = crv.GetEndPoint(1)
        grid_dir = (p - q).Normalize()
        
        current_group = [grid]
        used_grids.add(grid.Id)
        
        # Find all other grids parallel to this one
        for other_grid in grids:
            if other_grid.Id in used_grids:
                continue
            
            if other_grid.IsCurved:
                continue
            
            other_crv = other_grid.Curve
            other_p = other_crv.GetEndPoint(0)
            other_q = other_crv.GetEndPoint(1)
            other_dir = (other_p - other_q).Normalize()
            
            if is_parallel(grid_dir, other_dir):
                current_group.append(other_grid)
                used_grids.add(other_grid.Id)
        
        groups.append(current_group)
    
    return groups


def get_walls_perpendicular_to_grids(walls, grid_direction, view):
    """Get walls that are perpendicular to grid direction.

    These walls should be dimensioned (their faces are perpendicular to grids).
    Returns list of wall data dicts.
    """
    wall_data = []

    for wall in walls:
        crv = get_wall_location_line(wall)
        if not crv:
            continue

        if isinstance(crv, DB.Line):
            wall_dir = (crv.GetEndPoint(1) - crv.GetEndPoint(0)).Normalize()

            # Wall should be PERPENDICULAR to grid
            # (so wall faces are perpendicular to grid direction)
            if is_perpendicular(wall_dir, grid_direction):
                # Get edge references (representing faces in plan view)
                ext_ref, int_ref = get_wall_edge_references(wall, view)

                # Get endpoint positions (simpler than references)
                start_xyz, end_xyz = get_wall_endpoint_positions(wall)

                wall_data.append({
                    'wall': wall,
                    'curve': crv,
                    'direction': wall_dir,
                    'exterior_face': ext_ref,
                    'interior_face': int_ref,
                    'start_point': None,
                    'end_point': None,
                    'start_xyz': start_xyz if start_xyz else crv.GetEndPoint(0),
                    'end_xyz': end_xyz if end_xyz else crv.GetEndPoint(1)
                })

                print("Found perpendicular wall: {} (edges: {}/{}, positions: {}/{})".format(
                    wall.Id,
                    ext_ref is not None,
                    int_ref is not None,
                    start_xyz is not None,
                    end_xyz is not None
                ))

    return wall_data


def get_walls_parallel_to_grids(walls, grid_direction, view):
    """Get walls that are parallel to grid direction.

    These walls can be dimensioned at their endpoints for length dimensions.
    Returns list of wall data dicts.
    """
    wall_data = []

    for wall in walls:
        crv = get_wall_location_line(wall)
        if not crv:
            continue

        if isinstance(crv, DB.Line):
            wall_dir = (crv.GetEndPoint(1) - crv.GetEndPoint(0)).Normalize()

            # Wall should be PARALLEL to grid
            if is_parallel(wall_dir, grid_direction):
                # Get edge references (representing faces in plan view)
                ext_ref, int_ref = get_wall_edge_references(wall, view)

                # Get endpoint positions (simpler than references)
                start_xyz, end_xyz = get_wall_endpoint_positions(wall)

                wall_data.append({
                    'wall': wall,
                    'curve': crv,
                    'direction': wall_dir,
                    'exterior_face': ext_ref,
                    'interior_face': int_ref,
                    'start_point': None,
                    'end_point': None,
                    'start_xyz': start_xyz if start_xyz else crv.GetEndPoint(0),
                    'end_xyz': end_xyz if end_xyz else crv.GetEndPoint(1)
                })

                print("Found parallel wall: {} (edges: {}/{}, positions: {}/{})".format(
                    wall.Id,
                    ext_ref is not None,
                    int_ref is not None,
                    start_xyz is not None,
                    end_xyz is not None
                ))

    return wall_data


def calculate_projection(point, origin, direction):
    """Calculate projection of a point onto a line defined by origin and direction."""
    vec = point - origin
    projection = vec.DotProduct(direction)
    return projection


def get_reference_unique_key(reference):
    """Get a unique key for a reference object to identify true duplicates.
    
    Uses the stable representation which uniquely identifies the reference.
    """
    try:
        stable_rep = reference.ConvertToStableRepresentation(doc)
        return stable_rep
    except:
        # Fallback to string representation
        return str(reference)


def filter_references_smart(all_ref_data, min_distance=0.016):  # 1.6cm ~= 0.05ft
    """Smart filtering that allows same reference at different positions.
    
    Rules:
    1. Keep all grid references (they're primary reference points)
    2. For wall references:
       - Remove true duplicates (same reference, same position)
       - Keep same reference at different positions (valid for parallel walls)
       - Remove different references too close together (would create zero dimensions)
    
    Args:
        all_ref_data: List of reference data dicts with 'reference', 'position', 'projection', 'type'
        min_distance: Minimum distance between references in feet (default 1.6cm)
    
    Returns:
        Filtered list of reference data
    """
    
    # Step 1: Always keep all grid references
    grid_refs = [item for item in all_ref_data if item['type'] == 'grid']
    wall_refs = [item for item in all_ref_data if item['type'] != 'grid']
    
    print("\n=== SMART FILTERING ===")
    print("Total refs: {}, Grid refs: {}, Wall refs: {}".format(
        len(all_ref_data), len(grid_refs), len(wall_refs)))
    
    # Step 2: Remove TRUE duplicates from wall references
    # (same reference AND same position)
    seen_combinations = {}
    deduplicated_wall_refs = []
    
    for item in wall_refs:
        ref_key = get_reference_unique_key(item['reference'])
        pos_key = (round(item['position'].X, 6), 
                   round(item['position'].Y, 6), 
                   round(item['position'].Z, 6))
        
        combo_key = (ref_key, pos_key)
        
        if combo_key not in seen_combinations:
            seen_combinations[combo_key] = True
            deduplicated_wall_refs.append(item)
            print("Keeping {}: ref={}, pos=({:.2f}, {:.2f}, {:.2f}), proj={:.2f}".format(
                item['type'], ref_key[:20], 
                item['position'].X, item['position'].Y, item['position'].Z,
                item['projection']))
        else:
            print("Removing TRUE duplicate: {} at same position".format(item['type']))
    
    print("After deduplication: {} wall refs".format(len(deduplicated_wall_refs)))
    
    # Step 3: Build filtered list with WALL THICKNESS PRESERVATION
    filtered_data = []

    # Add all grid references first
    filtered_data.extend(grid_refs)

    # Process wall references - PRESERVE WALL THICKNESS PAIRS
    for wall_item in deduplicated_wall_refs:
        should_include = True
        wall_ref_key = get_reference_unique_key(wall_item['reference'])
        wall_item_wall_id = wall_item.get('wall_id')

        # Check against existing items
        for existing_item in filtered_data:
            existing_ref_key = get_reference_unique_key(existing_item['reference'])
            existing_wall_id = existing_item.get('wall_id')
            distance = abs(wall_item['projection'] - existing_item['projection'])

            # WALL THICKNESS PRESERVATION RULES:
            if wall_item_wall_id and existing_wall_id and wall_item_wall_id == existing_wall_id:
                # SAME WALL - always allow different faces (creates wall thickness)
                if wall_ref_key != existing_ref_key:  # Different faces of same wall
                    print("  ALLOWING: Different faces of same wall {} (thickness pair)".format(wall_item_wall_id))
                    break  # Allow this reference

            elif distance <= min_distance:
                # References are close in projection
                if wall_ref_key == existing_ref_key:
                    # SAME reference at different positions - VALID for parallel walls
                    print("  ALLOWING: Same reference at different positions (valid)")
                    break
                else:
                    # DIFFERENT references too close together
                    # Check for wall thickness pairs
                    is_wall_thickness_pair = (
                        (wall_item['type'] in ['wall_exterior', 'wall_interior'] and
                         existing_item['type'] in ['wall_exterior', 'wall_interior']) or
                        (wall_item['type'] in ['wall_exterior_parallel', 'wall_interior_parallel'] and
                         existing_item['type'] in ['wall_exterior_parallel', 'wall_interior_parallel'])
                    )

                    if is_wall_thickness_pair and wall_item_wall_id == existing_wall_id:
                        print("  ALLOWING: Wall thickness pair from same wall")
                        break
                    else:
                        # TRULY conflicting references - skip
                        print("  SKIPPING: Conflicting references too close (distance: {:.3f}ft = {:.1f}cm)".format(
                            distance, distance * 30.48))
                        should_include = False
                        break

        if should_include:
            filtered_data.append(wall_item)
    
    print("Final filtered count: {} refs (grids: {}, walls: {})".format(
        len(filtered_data), len(grid_refs), len(filtered_data) - len(grid_refs)))
    
    return filtered_data


def create_dimension_for_grid_group(grid_group, wall_data, view, pick_point):
    """Create dimension for one group of parallel grids.
    
    Args:
        grid_group: List of parallel grids
        wall_data: List of all wall data dicts
        view: Active view
        pick_point: User-selected dimension placement point
    """
    if not grid_group:
        return None
    
    # Get grid direction and dimension direction
    first_grid = grid_group[0]
    crv = first_grid.Curve
    p = crv.GetEndPoint(0)
    q = crv.GetEndPoint(1)
    grid_direction = (q - p).Normalize()

    # CORRECTED: Dimension line runs PERPENDICULAR to grid direction
    # For vertical grids (Y), dimension line runs horizontally (X)
    # For horizontal grids (X), dimension line runs vertically (Y)
    up = DB.XYZ.BasisZ
    witness_direction = up.CrossProduct(grid_direction).Normalize()  # Direction of witness lines
    dimension_direction = grid_direction  # Dimension line runs along grid direction
    
    print("\n=== Processing Grid Group ===")
    print("Grid direction: ({:.6f}, {:.6f}, {:.6f})".format(
        grid_direction.X, grid_direction.Y, grid_direction.Z))
    print("Witness direction: ({:.6f}, {:.6f}, {:.6f})".format(
        witness_direction.X, witness_direction.Y, witness_direction.Z))
    print("Dimension line direction: ({:.6f}, {:.6f}, {:.6f})".format(
        dimension_direction.X, dimension_direction.Y, dimension_direction.Z))
    print("Grids in group: {}".format([g.Name for g in grid_group]))
    
    # Collect all references with their positions
    all_ref_data = []
    
    # Add grid references
    for grid in grid_group:
        ref = DB.Reference.ParseFromStableRepresentation(doc, grid.UniqueId)
        crv = grid.Curve
        mid_point = (crv.GetEndPoint(0) + crv.GetEndPoint(1)) / 2.0
        
        all_ref_data.append({
            'reference': ref,
            'position': mid_point,
            'type': 'grid',
            'name': grid.Name
        })
    
    # Add wall references
    for wall_info in wall_data:
        wall = wall_info['wall']
        wall_dir = wall_info['direction']

        # Check if wall can be dimensioned with this grid group
        can_dimension = (is_perpendicular(wall_dir, grid_direction) or
                        is_parallel(wall_dir, grid_direction))

        if not can_dimension:
            continue

        relation_type = "perpendicular" if is_perpendicular(wall_dir, grid_direction) else "parallel"
        print("\nAdding wall {} references ({} to grid)".format(wall.Id, relation_type))

        # Get wall midpoint and width
        crv = wall_info['curve']
        mid_point = (crv.GetEndPoint(0) + crv.GetEndPoint(1)) / 2.0
        wall_width = wall.Width

        # For perpendicular walls, add face references
        if is_perpendicular(wall_dir, grid_direction):
            if wall_info['exterior_face']:
                ext_pos = mid_point - dimension_direction * (wall_width / 2.0)
                all_ref_data.append({
                    'reference': wall_info['exterior_face'],
                    'position': ext_pos,
                    'type': 'wall_exterior',
                    'wall_id': wall.Id
                })
                print("  Added exterior edge at position: ({:.2f}, {:.2f}, {:.2f})".format(
                    ext_pos.X, ext_pos.Y, ext_pos.Z))

            if wall_info['interior_face']:
                int_pos = mid_point + dimension_direction * (wall_width / 2.0)
                all_ref_data.append({
                    'reference': wall_info['interior_face'],
                    'position': int_pos,
                    'type': 'wall_interior',
                    'wall_id': wall.Id
                })
                print("  Added interior edge at position: ({:.2f}, {:.2f}, {:.2f})".format(
                    int_pos.X, int_pos.Y, int_pos.Z))

        # For parallel walls, add face references offset along the wall direction
        # This creates meaningful dimension segments instead of zero-length ones
        elif is_parallel(wall_dir, grid_direction):
            print("  Parallel wall detected")

            if wall_info['exterior_face'] and wall_info['interior_face']:
                start_pos = wall_info['start_xyz']
                end_pos = wall_info['end_xyz']

                start_to_end_distance = start_pos.DistanceTo(end_pos)
                print("  Wall length: {:.2f}ft ({:.1f}cm)".format(
                    start_to_end_distance, start_to_end_distance * 30.48))

                if start_to_end_distance > 0.5:  # >50cm
                    # For parallel walls, we want to dimension the wall thickness
                    # Use exterior and interior faces at the SAME position along the wall
                    # But offset perpendicular to the dimension direction

                    # Use midpoint of wall for consistent positioning
                    wall_midpoint = mid_point

                    # Add exterior face (offset outward from wall center)
                    ext_pos = wall_midpoint - dimension_direction * (wall_width / 2.0)
                    all_ref_data.append({
                        'reference': wall_info['exterior_face'],
                        'position': ext_pos,
                        'type': 'wall_exterior_parallel',
                        'wall_id': wall.Id
                    })
                    print("  Added exterior face at: ({:.2f}, {:.2f}, {:.2f})".format(
                        ext_pos.X, ext_pos.Y, ext_pos.Z))

                    # Add interior face (offset inward from wall center)
                    int_pos = wall_midpoint + dimension_direction * (wall_width / 2.0)
                    all_ref_data.append({
                        'reference': wall_info['interior_face'],
                        'position': int_pos,
                        'type': 'wall_interior_parallel',
                        'wall_id': wall.Id
                    })
                    print("  Added interior face at: ({:.2f}, {:.2f}, {:.2f})".format(
                        int_pos.X, int_pos.Y, int_pos.Z))
                else:
                    print("  Wall too short to dimension")
            else:
                print("  Missing face references for parallel wall")
    
    if len(all_ref_data) < 2:
        print("Not enough references to create dimension (need at least 2)")
        return None
    
    # Calculate projections for all references
    # CORRECTED: Project along witness direction (perpendicular to grids)
    # This gives us the distance from grid along the perpendicular axis
    grid_refs = [item for item in all_ref_data if item['type'] == 'grid']
    if grid_refs:
        origin = grid_refs[0]['position']
    else:
        origin = all_ref_data[0]['position']

    for item in all_ref_data:
        projection = calculate_projection(item['position'], origin, witness_direction)
        item['projection'] = projection

    # Sort by projection
    all_ref_data.sort(key=lambda x: x['projection'])

    print("\nAll references before filtering:")
    for i, item in enumerate(all_ref_data):
        print("  {}: {} (proj: {:.2f}ft = {:.1f}cm, pos: ({:.2f}, {:.2f}, {:.2f}))".format(
            i, item['type'], item['projection'], item['projection'] * 30.48,
            item['position'].X, item['position'].Y, item['position'].Z))

    # Apply SMART filtering
    filtered_data = filter_references_smart(all_ref_data, min_distance=0.016)  # 1.6cm

    # Re-sort after filtering
    filtered_data.sort(key=lambda x: x['projection'])

    print("\nFiltered references (final):")
    for i, item in enumerate(filtered_data):
        print("  {}: {} (proj: {:.2f}ft = {:.1f}cm)".format(
            i, item['type'], item['projection'], item['projection'] * 30.48))
    
    if len(filtered_data) < 2:
        print("Not enough references after filtering (need at least 2)")
        return None
    
    # Create reference array
    ref_array = DB.ReferenceArray()
    for item in filtered_data:
        ref_array.Append(item['reference'])

    print("\nTotal references for dimension: {}".format(ref_array.Size))

    # ===================================================================
    # CRITICAL FIX: Dimension line must run ALONG the grid direction,
    # positioned at the AVERAGE position of references in dimension_direction
    # ===================================================================

    # Find the extent of references along grid direction
    min_grid_proj = min([calculate_projection(item['position'], origin, grid_direction)
                         for item in filtered_data])
    max_grid_proj = max([calculate_projection(item['position'], origin, grid_direction)
                         for item in filtered_data])

    # Calculate AVERAGE position along grid direction for dimension line placement
    # Dimension line runs parallel to grid direction, positioned at average grid position

    if abs(grid_direction.Y) > 0.9:  # Vertical grids - average Y position
        avg_grid_pos = sum([item['position'].Y for item in filtered_data]) / len(filtered_data)
        print("Vertical grids: averaging Y positions = {:.2f}".format(avg_grid_pos))
    else:  # Horizontal grids - average X position
        avg_grid_pos = sum([item['position'].X for item in filtered_data]) / len(filtered_data)
        print("Horizontal grids: averaging X positions = {:.2f}".format(avg_grid_pos))

    # Extend the dimension line beyond the references
    extension = 10.0  # feet
    start_proj = min_grid_proj - extension
    end_proj = max_grid_proj + extension

    # Create dimension line PERPENDICULAR to grid direction
    # Position it at the average position along grid direction

    if abs(grid_direction.Y) > 0.9:  # Vertical grids - horizontal dimension line
        # Dimension line runs horizontally (X-direction) at average Y position
        dim_line_start = DB.XYZ(origin.X + start_proj, avg_grid_pos, 0)
        dim_line_end = DB.XYZ(origin.X + end_proj, avg_grid_pos, 0)
    else:  # Horizontal grids - vertical dimension line
        # Dimension line runs vertically (Y-direction) at average X position
        dim_line_start = DB.XYZ(avg_grid_pos, origin.Y + start_proj, 0)
        dim_line_end = DB.XYZ(avg_grid_pos, origin.Y + end_proj, 0)

    line = DB.Line.CreateBound(dim_line_start, dim_line_end)

    print("\nDimension line details:")
    print("  Start: ({:.2f}, {:.2f}, {:.2f})".format(
        dim_line_start.X, dim_line_start.Y, dim_line_start.Z))
    print("  End: ({:.2f}, {:.2f}, {:.2f})".format(
        dim_line_end.X, dim_line_end.Y, dim_line_end.Z))
    print("  Direction: PERPENDICULAR to grids (standard dimensioning)")
    print("  Positioned at average grid position: {:.2f}".format(avg_grid_pos))

    # DEBUG: Create temporary geometry to visualize reference positions
    print("\n=== VISUAL DEBUGGING ===")
    try:
        # Create detail lines to show where references are positioned
        with revit.Transaction("Debug Reference Positions", doc=doc):
            for i, item in enumerate(filtered_data):
                pos = item['position']
                # Create a small cross at each reference position
                cross_size = 1.0  # 1 foot cross

                # Horizontal line
                h_start = DB.XYZ(pos.X - cross_size/2, pos.Y, pos.Z)
                h_end = DB.XYZ(pos.X + cross_size/2, pos.Y, pos.Z)
                h_line = DB.Line.CreateBound(h_start, h_end)
                doc.Create.NewDetailCurve(view, h_line)

                # Vertical line
                v_start = DB.XYZ(pos.X, pos.Y - cross_size/2, pos.Z)
                v_end = DB.XYZ(pos.X, pos.Y + cross_size/2, pos.Z)
                v_line = DB.Line.CreateBound(v_start, v_end)
                doc.Create.NewDetailCurve(view, v_line)

                print("Created debug cross {} at ({:.2f}, {:.2f}, {:.2f}) for {}".format(
                    i, pos.X, pos.Y, pos.Z, item['type']))

            # Create a line to show dimension line position
            dim_debug_line = DB.Line.CreateBound(dim_line_start, dim_line_end)
            doc.Create.NewDetailCurve(view, dim_debug_line)
            print("Created dimension line debug from ({:.2f}, {:.2f}) to ({:.2f}, {:.2f})".format(
                dim_line_start.X, dim_line_start.Y, dim_line_end.X, dim_line_end.Y))

        print("Visual debugging elements created - check your view!")
        print("RED crosses = reference positions")
        print("BLUE line = dimension line position")

    except Exception as e:
        print("Error creating debug geometry: {}".format(str(e)))

    # Create the dimension
    try:
        print("\nCreating dimension...")
        new_dim = doc.Create.NewDimension(view, line, ref_array)
        if new_dim:
            print("SUCCESS: Dimension created (ID: {})".format(new_dim.Id))

            # Verify dimension segments
            if hasattr(new_dim, 'Segments') and new_dim.Segments:
                print("Dimension segments:")
                for i, seg in enumerate(new_dim.Segments):
                    try:
                        val = seg.Value
                        print("  Segment {}: {:.2f}ft ({:.1f}cm)".format(i, val, val * 30.48))
                    except:
                        print("  Segment {}: (unable to read value)".format(i))

            return new_dim
        else:
            print("FAILED: NewDimension returned None")
            return None
    except Exception as e:
        print("ERROR creating dimension: {}".format(str(e)))
        print(traceback.format_exc())
        return None


# Check if view is a plan
is_plan = True
try:
    view_type = doc.GetElement(active_view.GetTypeId())
    print("View type element: {}".format(view_type))
    if hasattr(view_type, 'FamilyName'):
        print("View family name: {}".format(view_type.FamilyName))
        if view_type.FamilyName in ['Floor Plan', 'Structural Plan']:
            is_plan = True
        else:
            is_plan = False
    else:
        print("View type has no FamilyName attribute")
        is_plan = False
except Exception as e:
    print("Error checking view type: {}".format(str(e)))
    is_plan = False

print("Is plan view: {}".format(is_plan))

# Select grids
with forms.WarningBar(title="Select all grids (script will group them automatically)"):
    try:
        grids = uidoc.Selection.PickElementsByRectangle(
            CustomISelectionFilter(DB.BuiltInCategory.OST_Grids), 
            "Select Grids"
        )
    except Exceptions.OperationCanceledException:
        forms.alert("Cancelled", ok=True, exitscript=True)

print("Selected {} grids".format(len(grids)))

if not grids:
    forms.alert("No grids selected.", ok=True, exitscript=True)

# Group grids by direction
grid_groups = group_grids_by_direction(grids)
print("Grid groups created: {}".format(len(grid_groups)))

print("\n" + "="*50)
print("GRID GROUPING RESULTS")
print("="*50)
print("Total grids selected: {}".format(len(grids)))
print("Number of grid groups: {}".format(len(grid_groups)))
for i, group in enumerate(grid_groups):
    print("  Group {}: {} grids - {}".format(
        i+1, len(group), [g.Name for g in group]))

if not grid_groups:
    forms.alert("No valid grid groups found.", ok=True, exitscript=True)

# Get all walls in the active view
try:
    collector = DB.FilteredElementCollector(doc, active_view.Id)
    walls = collector.OfCategory(DB.BuiltInCategory.OST_Walls)\
                    .WhereElementIsNotElementType()\
                    .ToElements()
    walls_list = list(walls)
    print("Walls collected: {}".format(len(walls_list)))
except Exception as e:
    print("Error collecting walls: {}".format(str(e)))
    walls_list = []
    walls = []

print("\n" + "="*50)
print("WALL ANALYSIS")
print("="*50)
print("Total walls in view: {}".format(len(walls_list)))

# Collect all walls that can be dimensioned with grids
all_wall_data = []

for i, grid_group in enumerate(grid_groups):
    first_grid = grid_group[0]
    crv = first_grid.Curve
    grid_dir = (crv.GetEndPoint(1) - crv.GetEndPoint(0)).Normalize()

    print("\nAnalyzing walls for Grid Group {} (direction: ({:.6f}, {:.6f}, {:.6f}))".format(
        i+1, grid_dir.X, grid_dir.Y, grid_dir.Z))

    try:
        perpendicular_walls = get_walls_perpendicular_to_grids(walls, grid_dir, active_view)
    except Exception as e:
        print("Error finding perpendicular walls: {}".format(str(e)))
        perpendicular_walls = []

    try:
        parallel_walls = get_walls_parallel_to_grids(walls, grid_dir, active_view)
    except Exception as e:
        print("Error finding parallel walls: {}".format(str(e)))
        parallel_walls = []

    all_walls_for_group = perpendicular_walls + parallel_walls

    for wall_info in all_walls_for_group:
        wall_id = wall_info['wall'].Id
        if not any(w['wall'].Id == wall_id for w in all_wall_data):
            all_wall_data.append(wall_info)

    print("  Found {} perpendicular + {} parallel walls".format(
        len(perpendicular_walls), len(parallel_walls)))

print("\nTotal unique walls: {}".format(len(all_wall_data)))

# Set sketch plane for non-plan views
if not is_plan:
    print("Setting sketch plane for non-plan view")
    try:
        with revit.Transaction("Dim Grids Sketch Plane", doc=doc):
            origin = active_view.Origin
            view_direction = active_view.ViewDirection
            plane = DB.Plane.CreateByNormalAndOrigin(view_direction, origin)
            sp = DB.SketchPlane.Create(doc, plane)
            active_view.SketchPlane = sp
            doc.Regenerate()
            print("Sketch plane set")
    except Exception as e:
        print("Error setting sketch plane: {}".format(str(e)))
        raise

# Pick placement point
print("Picking dimension line placement point")
with forms.WarningBar(title="Pick dimension line placement point"):
    try:
        pick_point = uidoc.Selection.PickPoint()
        print("Pick point: ({:.2f}, {:.2f}, {:.2f})".format(
            pick_point.X, pick_point.Y, pick_point.Z))
    except Exceptions.OperationCanceledException:
        forms.alert("Cancelled", ok=True, exitscript=True)
    except Exception as e:
        print("Error picking point: {}".format(str(e)))
        forms.alert("Error: {}".format(str(e)), ok=True, exitscript=True)

# Create dimensions
print("\n" + "="*50)
print("CREATING DIMENSIONS")
print("="*50)

created_dimensions = []

with revit.Transaction("Dim Grids and Wall Faces", doc=doc):
    try:
        for i, grid_group in enumerate(grid_groups):
            print("\nProcessing Grid Group {} of {}".format(i+1, len(grid_groups)))

            dim = create_dimension_for_grid_group(
                grid_group,
                all_wall_data,
                active_view,
                pick_point
            )

            if dim:
                created_dimensions.append(dim)
                print("Dimension created: ID {}".format(dim.Id))
            else:
                print("No dimension created for group {}".format(i+1))
        print("All grid groups processed")
    except Exception as e:
        print("Error during dimension creation: {}".format(str(e)))
        print(traceback.format_exc())
        raise

print("Transaction completed")
print("Created {} dimensions".format(len(created_dimensions)))

# Show results
print("\n" + "="*50)
print("RESULTS")
print("="*50)
print("Grid groups: {}".format(len(grid_groups)))
print("Dimensions created: {}".format(len(created_dimensions)))
print("Script completed successfully")

if created_dimensions:
    forms.alert(
        "Successfully created {} dimension(s)!\n\n"
        "Grid groups: {}\n"
        "Dimensions: {}".format(
            len(created_dimensions),
            len(grid_groups),
            len(created_dimensions)
        ),
        ok=True
    )
else:
    forms.alert(
        "No dimensions were created.\n\n"
        "Please check:\n"
        "- Grids are properly selected\n"
        "- Walls are perpendicular or parallel to grids\n"
        "- View contains valid geometry\n"
        "- Check console output for details",
        ok=True
    )