# -*- coding: utf-8 -*-
"""Create Dimension Lines for Visible Stair Runs in Active Plan View."""
__title__ = 'Dimension\nStair Runs'

from pyrevit import revit, DB, forms, script
import traceback

# Setup
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
active_view = doc.ActiveView

print("="*60)
print("STAIR RUN DIMENSION TOOL")
print("="*60)
print("Active view: {} (Type: {})".format(active_view.Name, active_view.ViewType))

# Configuration
DEBUG_MODE = True

def debug_print(*args):
    if DEBUG_MODE:
        for arg in args:
            print("  DEBUG: {}".format(arg))

def feet_to_mm(feet):
    return feet * 304.8

def format_elevation_mm(feet_value):
    mm_value = feet_to_mm(feet_value)
    return "+{:.0f} mm".format(mm_value) if mm_value >= 0 else "{:.0f} mm".format(mm_value)

# ═══════════════════════════════════════════════════════════
# STAIR ANALYZER CLASS
# ═══════════════════════════════════════════════════════════

class StairAnalyzer:
    """Analyze stair structure and find visible runs"""
    
    def __init__(self, stair):
        self.stair = stair
        self.runs = []
        self.landings = []
        self.stair_base_elevation = 0.0
        self._analyze()
    
    def _analyze(self):
        """Extract all stair components"""
        try:
            # Determine if multistory or regular stair
            if hasattr(self.stair, 'GetAllStairsIds'):
                stair_ids = list(self.stair.GetAllStairsIds())
                debug_print("Multistory stair with {} elements".format(len(stair_ids)))
            else:
                stair_ids = [self.stair.Id]
                debug_print("Regular stair")
                if hasattr(self.stair, 'BaseElevation'):
                    self.stair_base_elevation = self.stair.BaseElevation
                    debug_print("Base elevation: {:.2f}'".format(self.stair_base_elevation))
            
            # Process each stair element
            for stair_id in stair_ids:
                stair_elem = doc.GetElement(stair_id)
                if not stair_elem or not hasattr(stair_elem, 'GetStairsRuns'):
                    continue
                
                # Update base elevation
                if hasattr(stair_elem, 'BaseElevation'):
                    self.stair_base_elevation = stair_elem.BaseElevation
                
                # Get runs
                run_ids = stair_elem.GetStairsRuns()
                for run_id in run_ids:
                    run = doc.GetElement(run_id)
                    if run:
                        self.runs.append(run)
                        abs_base = self.stair_base_elevation + run.BaseElevation
                        abs_top = self.stair_base_elevation + run.TopElevation
                        debug_print("Run {}: Rel[{:.2f}'-{:.2f}'] -> Abs[{:.2f}'-{:.2f}']".format(
                            run.Id, run.BaseElevation, run.TopElevation, abs_base, abs_top))
                
                # Get landings
                landing_ids = stair_elem.GetStairsLandings()
                for landing_id in landing_ids:
                    landing = doc.GetElement(landing_id)
                    if landing:
                        self.landings.append(landing)
            
            debug_print("Analysis complete: {} runs, {} landings".format(
                len(self.runs), len(self.landings)))
        
        except Exception as e:
            print("ERROR analyzing stair: {}".format(str(e)))
            raise
    
    def get_visible_runs_at_level(self, target_elevation):
        """Find runs visible at specific level elevation"""
        tolerance = 5.0  # feet
        extended_range = 15.0  # feet
        visible = []
        
        debug_print("Finding runs at elevation {:.2f}'".format(target_elevation))
        
        for run in self.runs:
            abs_base = self.stair_base_elevation + run.BaseElevation
            abs_top = self.stair_base_elevation + run.TopElevation
            
            # Check various visibility conditions
            ends_here = abs(abs_top - target_elevation) <= tolerance
            starts_here = abs(abs_base - target_elevation) <= tolerance
            spans_level = abs_base < target_elevation < abs_top
            in_range = (abs(abs_base - target_elevation) <= extended_range or 
                       abs(abs_top - target_elevation) <= extended_range)
            
            if ends_here or starts_here or spans_level or in_range:
                visible.append(run)
                debug_print("Run {} VISIBLE (Base:{:.2f}' Top:{:.2f}')".format(
                    run.Id, abs_base, abs_top))
            else:
                debug_print("Run {} not visible (Base:{:.2f}' Top:{:.2f}')".format(
                    run.Id, abs_base, abs_top))
        
        debug_print("Total visible: {}".format(len(visible)))
        return visible
    
    def get_run_references(self, run, view):
        """Get dimensionable references for run endpoints using multiple strategies"""
        
        # First, do detailed geometry inspection
        print("\n  ═══ GEOMETRY INSPECTION ═══")
        try:
            self._inspect_run_geometry(run, view)
        except Exception as e:
            print("  INSPECTION ERROR: {}".format(str(e)))
            import traceback
            print("  {}".format(traceback.format_exc()))
        print("  ═══════════════════════════\n")
        
        # Strategy 1: PlanarFace method
        print("  Trying Strategy 1: PlanarFace method...")
        start_ref, end_ref = self._try_planar_face_method(run, view)
        if start_ref and end_ref:
            print("  ✅ SUCCESS with PlanarFace method")
            return (start_ref, end_ref)
        print("  ❌ PlanarFace method failed")
        
        # Strategy 2: Solid edges method
        print("  Trying Strategy 2: Solid edges method...")
        start_ref, end_ref = self._try_solid_edges_method(run, view)
        if start_ref and end_ref:
            print("  ✅ SUCCESS with Solid edges method")
            return (start_ref, end_ref)
        print("  ❌ Solid edges method failed")
        
        # Strategy 3: Any geometry reference method
        print("  Trying Strategy 3: Any geometry method...")
        start_ref, end_ref = self._try_any_geometry_method(run, view)
        if start_ref and end_ref:
            print("  ✅ SUCCESS with Any geometry method")
            return (start_ref, end_ref)
        print("  ❌ Any geometry method failed")
        
        # Strategy 4: Use StairsPath if available
        print("  Trying Strategy 4: StairsPath method...")
        start_ref, end_ref = self._try_stairs_path_method(run, view)
        if start_ref and end_ref:
            print("  ✅ SUCCESS with StairsPath method")
            return (start_ref, end_ref)
        print("  ❌ StairsPath method failed")
        
        print("  ⚠️  All 4 strategies failed - no valid references found")
        return (None, None)
    
    def _inspect_run_geometry(self, run, view):
        """Inspect and print detailed geometry information"""
        print("  Run ID: {}".format(run.Id))
        
        # Test 1: Basic properties
        print("  Test 1: Basic properties")
        try:
            print("    Category: {}".format(run.Category.Name if run.Category else "None"))
            print("    BaseElevation: {:.2f}".format(run.BaseElevation))
            print("    TopElevation: {:.2f}".format(run.TopElevation))
        except Exception as e:
            print("    ERROR: {}".format(str(e)))
        
        # Test 2: Location
        print("  Test 2: Location")
        try:
            loc = run.Location
            print("    Location type: {}".format(type(loc).__name__ if loc else "None"))
            if isinstance(loc, DB.LocationCurve):
                curve = loc.Curve
                print("    Curve type: {}".format(type(curve).__name__))
        except Exception as e:
            print("    ERROR: {}".format(str(e)))
        
        # Test 3: GetStairsPath
        print("  Test 3: GetStairsPath")
        try:
            path = run.GetStairsPath()
            print("    Path type: {}".format(type(path).__name__ if path else "None"))
            if path:
                print("    Path has Reference attr: {}".format(hasattr(path, 'Reference')))
                if hasattr(path, 'Reference'):
                    print("    Path.Reference is None: {}".format(path.Reference is None))
        except Exception as e:
            print("    ERROR: {}".format(str(e)))
        
        # Test 4: Geometry - SIMPLIFIED
        print("  Test 4: Geometry (simplified)")
        try:
            options = DB.Options()
            options.View = view
            options.ComputeReferences = True
            
            geom_elem = run.get_Geometry(options)
            print("    GeometryElement: {}".format(geom_elem is not None))
            
            if geom_elem:
                count = 0
                for geom_obj in geom_elem:
                    count += 1
                    obj_type = type(geom_obj).__name__
                    print("    Geometry[{}]: {}".format(count, obj_type))
                    
                    if count >= 5:  # Limit to first 5 items
                        print("    ... (more items)")
                        break
                
                if count == 0:
                    print("    WARNING: GeometryElement is empty!")
        except Exception as e:
            print("    ERROR: {}".format(str(e)))
            import traceback
            print("    Traceback: {}".format(traceback.format_exc()))
    
    def _try_planar_face_method(self, run, view):
        """Strategy 1: Find vertical planar faces at run endpoints"""
        try:
            options = DB.Options()
            options.View = view
            options.ComputeReferences = True
            geom_elem = run.get_Geometry(options)
            
            # Get run orientation
            loc = run.Location
            if not isinstance(loc, DB.LocationCurve):
                return (None, None)
            curve = loc.Curve
            if not isinstance(curve, DB.Line):
                return (None, None)
            
            run_start = curve.GetEndPoint(0)
            run_end = curve.GetEndPoint(1)
            run_direction = (run_end - run_start).Normalize()
            run_length = curve.Length
            
            # Find vertical planar faces at run endpoints
            start_faces = []
            end_faces = []
            
            for geom_obj in geom_elem:
                if not isinstance(geom_obj, DB.Solid):
                    continue
                
                for face in geom_obj.Faces:
                    if not isinstance(face, DB.PlanarFace):
                        continue
                    
                    # Check if face is vertical (parallel to run direction)
                    face_normal = face.FaceNormal
                    dot = abs(face_normal.DotProduct(run_direction))
                    
                    if dot > 0.95:  # Nearly vertical
                        # Get face position along run
                        bbox = face.GetBoundingBox()
                        face_center = (bbox.Min + bbox.Max) / 2.0
                        vec_to_face = face_center - run_start
                        projection = vec_to_face.DotProduct(run_direction)
                        
                        # Classify as start or end
                        if projection <= run_length * 0.3:
                            start_faces.append((face, projection))
                        elif projection >= run_length * 0.7:
                            end_faces.append((face, projection))
            
            # Get closest faces
            start_ref = None
            end_ref = None
            
            if start_faces:
                start_faces.sort(key=lambda x: x[1])
                start_ref = start_faces[0][0].Reference
            
            if end_faces:
                end_faces.sort(key=lambda x: -x[1])
                end_ref = end_faces[0][0].Reference
            
            return (start_ref, end_ref)
        
        except Exception as e:
            debug_print("PlanarFace method error: {}".format(str(e)))
            return (None, None)
    
    def _try_solid_edges_method(self, run, view):
        """Strategy 2: Find vertical edges at run endpoints"""
        try:
            options = DB.Options()
            options.View = view
            options.ComputeReferences = True
            geom_elem = run.get_Geometry(options)
            
            # Get run orientation
            loc = run.Location
            if not isinstance(loc, DB.LocationCurve):
                return (None, None)
            
            curve = loc.Curve
            if not isinstance(curve, DB.Line):
                return (None, None)
            
            run_start = curve.GetEndPoint(0)
            run_end = curve.GetEndPoint(1)
            run_direction = (run_end - run_start).Normalize()
            run_length = curve.Length
            
            start_edges = []
            end_edges = []
            
            for geom_obj in geom_elem:
                if not isinstance(geom_obj, DB.Solid):
                    continue
                
                for edge in geom_obj.Edges:
                    if not isinstance(edge, DB.Edge):
                        continue
                    
                    edge_curve = edge.AsCurve()
                    if not edge_curve:
                        continue
                    
                    # Check if edge is vertical
                    edge_start = edge_curve.GetEndPoint(0)
                    edge_end = edge_curve.GetEndPoint(1)
                    edge_direction = (edge_end - edge_start).Normalize()
                    
                    # Vertical edges have high Z component
                    if abs(edge_direction.Z) > 0.9:
                        # Get edge position along run
                        edge_center = (edge_start + edge_end) / 2.0
                        vec_to_edge = edge_center - run_start
                        projection = vec_to_edge.DotProduct(run_direction)
                        
                        edge_ref = edge.Reference
                        if not edge_ref:
                            continue
                        
                        # Classify as start or end
                        if projection <= run_length * 0.3:
                            start_edges.append((edge_ref, projection))
                        elif projection >= run_length * 0.7:
                            end_edges.append((edge_ref, projection))
            
            start_ref = start_edges[0][0] if start_edges else None
            end_ref = end_edges[-1][0] if end_edges else None
            
            return (start_ref, end_ref)
        
        except Exception as e:
            debug_print("Solid edges method error: {}".format(str(e)))
            return (None, None)
    
    def _try_any_geometry_method(self, run, view):
        """Strategy 3: Use any available geometry references"""
        try:
            options = DB.Options()
            options.View = view
            options.ComputeReferences = True
            geom_elem = run.get_Geometry(options)
            
            # Get run orientation
            loc = run.Location
            if not isinstance(loc, DB.LocationCurve):
                return (None, None)
            
            curve = loc.Curve
            if not isinstance(curve, DB.Line):
                return (None, None)
            
            run_start = curve.GetEndPoint(0)
            run_end = curve.GetEndPoint(1)
            run_direction = (run_end - run_start).Normalize()
            run_length = curve.Length
            
            all_refs = []
            
            # Collect all geometry references
            for geom_obj in geom_elem:
                if isinstance(geom_obj, DB.Solid):
                    # Try faces
                    for face in geom_obj.Faces:
                        if face.Reference:
                            bbox = face.GetBoundingBox()
                            if bbox:
                                center = (bbox.Min + bbox.Max) / 2.0
                                vec = center - run_start
                                proj = vec.DotProduct(run_direction)
                                all_refs.append((face.Reference, proj))
                    
                    # Try edges
                    for edge in geom_obj.Edges:
                        if edge.Reference:
                            edge_curve = edge.AsCurve()
                            if edge_curve:
                                center = (edge_curve.GetEndPoint(0) + edge_curve.GetEndPoint(1)) / 2.0
                                vec = center - run_start
                                proj = vec.DotProduct(run_direction)
                                all_refs.append((edge.Reference, proj))
                
                elif isinstance(geom_obj, DB.Curve):
                    if geom_obj.Reference:
                        center = (geom_obj.GetEndPoint(0) + geom_obj.GetEndPoint(1)) / 2.0
                        vec = center - run_start
                        proj = vec.DotProduct(run_direction)
                        all_refs.append((geom_obj.Reference, proj))
            
            if not all_refs:
                return (None, None)
            
            # Sort by projection and pick extremes
            all_refs.sort(key=lambda x: x[1])
            start_ref = all_refs[0][0]
            end_ref = all_refs[-1][0]
            
            # Make sure they're different
            if start_ref == end_ref and len(all_refs) > 1:
                end_ref = all_refs[-2][0]
            
            return (start_ref, end_ref)
        
        except Exception as e:
            debug_print("Any geometry method error: {}".format(str(e)))
            return (None, None)

# ═══════════════════════════════════════════════════════════
# DIMENSION CREATION
# ═══════════════════════════════════════════════════════════

def create_dimension_for_run(run, view, offset=3.0):
    """Create dimension for a single run"""
    try:
        print("\nCreating dimension for run {}".format(run.Id))
        
        # Get parent stair and analyze
        parent_stair = run.GetStairs()
        analyzer = StairAnalyzer(parent_stair)
        
        # Get references
        start_ref, end_ref = analyzer.get_run_references(run, view)
        if not start_ref or not end_ref:
            print("  WARNING: Could not get valid references")
            return None
        
        # Get run geometry
        loc = run.Location
        if not isinstance(loc, DB.LocationCurve):
            print("  WARNING: No location curve")
            return None
        
        curve = loc.Curve
        if not isinstance(curve, DB.Line):
            print("  WARNING: Location is not a line")
            return None
        
        # Calculate dimension line position
        run_start = curve.GetEndPoint(0)
        run_end = curve.GetEndPoint(1)
        run_direction = (run_end - run_start).Normalize()
        perpendicular = DB.XYZ.BasisZ.CrossProduct(run_direction).Normalize()
        
        mid_point = (run_start + run_end) / 2.0
        dim_start = mid_point + perpendicular * offset
        dim_end = mid_point - perpendicular * offset
        
        # Create dimension
        line = DB.Line.CreateBound(dim_start, dim_end)
        ref_array = DB.ReferenceArray()
        ref_array.Append(start_ref)
        ref_array.Append(end_ref)
        
        dim = doc.Create.NewDimension(view, line, ref_array)
        
        if dim:
            print("  SUCCESS: Dimension created (ID: {})".format(dim.Id))
            return dim
        else:
            print("  FAILED: Dimension creation returned None")
            return None
    
    except Exception as e:
        print("  ERROR: {}".format(str(e)))
        print("  {}".format(traceback.format_exc()))
        return None

# ═══════════════════════════════════════════════════════════
# MAIN WORKFLOW
# ═══════════════════════════════════════════════════════════

# Validate view type
try:
    view_type = doc.GetElement(active_view.GetTypeId())
    is_plan = (hasattr(view_type, 'FamilyName') and 
               view_type.FamilyName in ['Floor Plan', 'Structural Plan', 'Engineering Plan'])
except:
    is_plan = False

if not is_plan:
    forms.alert("This tool only works in plan views.", title="Invalid View")
    script.exit()

# Get view level
try:
    active_level = active_view.GenLevel
    if not active_level:
        forms.alert("View does not have an associated level.", title="Error")
        script.exit()
    
    level_elevation = active_level.Elevation
    print("\nView level: {} at {:.2f}' ({})".format(
        active_level.Name, level_elevation, format_elevation_mm(level_elevation)))
except:
    forms.alert("Could not determine view level.", title="Error")
    script.exit()

# Collect stairs in view
print("\nCollecting stairs...")
stairs = list(DB.FilteredElementCollector(doc, active_view.Id)
              .OfCategory(DB.BuiltInCategory.OST_Stairs)
              .WhereElementIsNotElementType()
              .ToElements())

print("Found {} stair(s) in view".format(len(stairs)))

if not stairs:
    forms.alert("No stairs found in view.", title="No Stairs")
    script.exit()

# Analyze all stairs and collect visible runs
print("\n" + "="*60)
print("ANALYZING STAIRS")
print("="*60)

all_visible_runs = []

for stair in stairs:
    print("\nStair ID: {}".format(stair.Id))
    analyzer = StairAnalyzer(stair)
    visible = analyzer.get_visible_runs_at_level(level_elevation)
    all_visible_runs.extend(visible)
    print("  {} visible run(s) from this stair".format(len(visible)))

print("\n" + "="*60)
print("TOTAL: {} visible run(s)".format(len(all_visible_runs)))
print("="*60)

if len(all_visible_runs) == 0:
    forms.alert("No stair runs visible at this level.", title="No Visible Runs")
    script.exit()

if len(all_visible_runs) < 2:
    forms.alert("Only 1 run visible. Need at least 2 runs.", title="Insufficient Runs")
    script.exit()

# Sort runs by position
def sort_key(run):
    try:
        loc = run.Location
        if isinstance(loc, DB.LocationCurve):
            curve = loc.Curve
            if isinstance(curve, DB.Line):
                return curve.GetEndPoint(0).X
    except:
        pass
    return run.Id.IntegerValue

sorted_runs = sorted(all_visible_runs, key=sort_key)

print("\nSorted runs:")
for i, run in enumerate(sorted_runs):
    print("  {}: Run ID {}".format(i+1, run.Id))

# Create dimensions
print("\n" + "="*60)
print("CREATING DIMENSIONS")
print("="*60)

created_dims = []

with revit.Transaction("Dimension Stair Runs", doc=doc):
    for i, run in enumerate(sorted_runs):
        print("\n[{}/{}] Processing run {}".format(i+1, len(sorted_runs), run.Id))
        dim = create_dimension_for_run(run, active_view)
        if dim:
            created_dims.append(dim)

print("\n" + "="*60)
print("RESULTS")
print("="*60)

if created_dims:
    print("\nSUCCESS: Created {} dimension(s)".format(len(created_dims)))
    for i, dim in enumerate(created_dims):
        print("  Dimension {}: ID {}".format(i+1, dim.Id))
    
    forms.alert("Successfully created {} dimension(s)!".format(len(created_dims)), 
                title="Success")
else:
    print("\nWARNING: No dimensions were created")
    forms.alert("No dimensions created. Check console for details.", title="Warning")

print("\n" + "="*60)
print("SCRIPT COMPLETED")
print("="*60)