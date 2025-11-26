# -*- coding: utf-8 -*-
__title__   = "Stair Plan Generator"
__version__ = 'Version = 1.0 (Beta)'
__doc__ = """Date    = 02.11.2025
_____________________________________________________________________
Description:
Automatically creates plan views for multi-story stairs at selected levels.
Select stair first, then choose levels, with hardcoded view range for consistency.

Features:
- Multi-level stair support
- Hardcoded view range (Cut/Top: 900, Bottom/Depth: -1500)
- Automatic crop region calculation
- View template support
- Debug mode for troubleshooting

_____________________________________________________________________
Author: PrasKaa (revised with hardcoded view range)
"""
# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝ IMPORTS
#==================================================
from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType
from Autodesk.Revit.DB import *
import traceback

# pyRevit Imports
from pyrevit import script, forms, EXEC_PARAMS

# Import MultistoryStairs class
from Autodesk.Revit.DB.Architecture import MultistoryStairs

# Custom Imports (reuse from Wall Plan Generator)
# from lib.view_generator import ViewGenerator
# from lib.element_properties import ElementProperties

# Import TransactionGroup for cleaner console output
from Autodesk.Revit.DB import TransactionGroup

# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝ VARIABLES
#==================================================
uidoc     = __revit__.ActiveUIDocument
doc       = __revit__.ActiveUIDocument.Document #type: Document

output = script.get_output()

# Debug configuration
DEBUG_MODE = False #Set to True for detailed debug output

# ╔═╗╦ ╦╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔╔═╗
# ╠╣ ║ ║║║║║   ║ ║║ ║║║║╚═╗
# ╚  ╚═╝╝╚╝╚═╝ ╩ ╩╚═╝╝╚╝╚═╝
def debug_print(*args, **kwargs):
    """Print debug messages when debug mode is enabled"""
    if DEBUG_MODE:
        print(args, kwargs)

# ╦ ╦╔═╗╦  ╦  ╔═╗
# ║║║╠═╣║  ║  ╚═╗
# ╚╩╝╩ ╩╩═╝╩═╝╚═╝ UNIT CONVERSION UTILITIES
#==================================================

def feet_to_mm(feet):
    """Convert feet to millimeters (Revit internal unit → Display unit)"""
    return feet * 304.8

def mm_to_feet(mm):
    """Convert millimeters to feet (Display unit → Revit internal unit)"""
    return mm / 304.8

def format_elevation_mm(feet_value):
    """Format elevation in millimeters for display

    Examples:
        format_elevation_mm(10.0) → "+3048 mm"
        format_elevation_mm(-5.0) → "-1524 mm"
        format_elevation_mm(0.0) → "0 mm"
    """
    mm_value = feet_to_mm(feet_value)
    if mm_value >= 0:
        return "+{:.0f} mm".format(mm_value)
    else:
        return "{:.0f} mm".format(mm_value)

def format_offset_mm(feet_value):
    """Format offset in millimeters for display (without + sign for positive)

    Examples:
        format_offset_mm(2.95) → "900 mm"
        format_offset_mm(-4.92) → "-1500 mm"
    """
    mm_value = feet_to_mm(feet_value)
    return "{:.0f} mm".format(mm_value)

# ╔═╗╦  ╔═╗╔═╗╔═╗╔═╗╔═╗
# ║  ║  ╠═╣╚═╗╚═╗║╣ ╚═╗
# ╚═╝╩═╝╩ ╩╚═╝╚═╝╚═╝╚═╝
class StairAnalyzer:
    """
    Menganalisis struktur tangga dan menentukan visibility per level
    """

    def __init__(self, stair):
        self.stair = stair
        self.runs = []
        self.landings = []
        self.elevations = set()

        self._analyze_stair_structure()

    def _analyze_stair_structure(self):
        """Ekstrak semua komponen tangga"""
        try:
            # Get stair runs
            self.runs = list(self.stair.GetStairRuns())

            # Get stair landings
            self.landings = list(self.stair.GetStairLandings())

            # Collect all elevations
            for run in self.runs:
                self.elevations.add(run.BaseElevation)
                self.elevations.add(run.TopElevation)

            for landing in self.landings:
                self.elevations.add(landing.BaseElevation)

            debug_print("STAIR_ANALYSIS: Found {} runs, {} landings".format(len(self.runs), len(self.landings)))
            debug_print("STAIR_ANALYSIS: Elevations: {}".format(sorted(self.elevations)))

        except Exception as e:
            debug_print("STAIR_ANALYSIS_ERROR: {}".format(str(e)))
            raise

    def find_landing_for_level(self, target_elevation):
        """
        Tentukan landing mana yang "belong to" level tertentu

        Landing dianggap "milik" level yang dia layani (arrival level)
        Toleransi: ±1.5 feet dari level elevation
        """
        tolerance = 1.5  # feet

        for landing in self.landings:
            elevation_diff = abs(landing.BaseElevation - target_elevation)
            if elevation_diff <= tolerance:
                debug_print("LANDING_ASSOCIATION: Landing at {:.2f}' associated with level at {:.2f}' (diff: {:.2f}')".format(
                    landing.BaseElevation, target_elevation, elevation_diff))
                return landing

        debug_print("LANDING_ASSOCIATION: No landing found for level at {:.2f}'".format(target_elevation))
        return None

    def get_runs_for_level(self, target_elevation):
        """
        Tentukan run mana yang visible di level tertentu

        RULES:
        1. Runs BELOW (turun dari level ini):
           - run.TopElevation ≈ target_elevation
           - Show FULL (semua step visible)

        2. Runs ABOVE (naik ke level atas):
           - run.BaseElevation ≈ target_elevation
           - Show PARTIAL (hanya beberapa step pertama)
        """
        tolerance = 0.1  # feet (very tight tolerance for runs)
        runs_below = []
        runs_above = []

        for run in self.runs:
            # Check if run ends at this level (coming up to landing)
            if abs(run.TopElevation - target_elevation) <= tolerance:
                runs_below.append(run)
                debug_print("RUN_BELOW: Run ending at {:.2f}' (from {:.2f}') visible at level {:.2f}'".format(
                    run.TopElevation, run.BaseElevation, target_elevation))

            # Check if run starts at this level (going down from landing)
            elif abs(run.BaseElevation - target_elevation) <= tolerance:
                runs_above.append(run)
                debug_print("RUN_ABOVE: Run starting at {:.2f}' (to {:.2f}') visible at level {:.2f}'".format(
                    run.BaseElevation, run.TopElevation, target_elevation))

        return {'below': runs_below, 'above': runs_above}

    def get_level_visibility(self, target_elevation):
        """
        Get stair elements visible at specific level
        Returns dict with landing, runs_below, runs_above
        """
        landing = self.find_landing_for_level(target_elevation)
        runs = self.get_runs_for_level(target_elevation)

        visible_elements = {
            'landing_here': landing,
            'runs_below': runs['below'],      # Full visibility
            'runs_above': runs['above'],      # Partial visibility
            'has_visible_elements': bool(landing or runs['below'] or runs['above'])
        }

        debug_print("LEVEL_VISIBILITY: At {:.2f}' - Landing: {}, Runs below: {}, Runs above: {}".format(
            target_elevation, landing is not None, len(runs['below']), len(runs['above'])))

        return visible_elements

# ╔═╗╦  ╔═╗╔═╗╔═╗╔═╗╔═╗
# ║  ║  ╠═╣╚═╗╚═╗║╣ ╚═╗
# ╚═╝╩═╝╩ ╩╚═╝╚═╝╚═╝╚═╝
class StairCropCalculator:
    """
    Menghitung bounding box untuk crop region tangga
    Simplified approach: rectangular bounding box regardless of stair shape
    """

    def calculate_stair_bounds(self, stair, visible_elements):
        """
        Calculate rectangular crop region for stair plan view

        Algorithm:
        1. Get stair's overall BoundingBox (3D)
        2. Extract Min/Max X, Y coordinates
        3. Calculate center point
        4. Calculate dimensions
        5. Add margin (3 feet standard)
        6. Create rectangular CropRegion
        """
        try:
            # Get stair's overall bounding box
            stair_bbox = stair.get_BoundingBox(None)

            if not stair_bbox:
                debug_print("CROP_CALC: No bounding box found, using default 20x20")
                return self._get_default_crop_region()

            # Calculate dimensions at plan level
            width = abs(stair_bbox.Max.X - stair_bbox.Min.X)
            height = abs(stair_bbox.Max.Y - stair_bbox.Min.Y)

            # Ensure minimum size
            min_size = 10.0  # feet
            width = max(width, min_size)
            height = max(height, min_size)

            # Calculate center point
            center_x = (stair_bbox.Max.X + stair_bbox.Min.X) / 2
            center_y = (stair_bbox.Max.Y + stair_bbox.Min.Y) / 2

            # Add margin (3 feet standard)
            margin = 3.0

            crop_bounds = {
                'min_x': center_x - (width / 2) - margin,
                'max_x': center_x + (width / 2) + margin,
                'min_y': center_y - (height / 2) - margin,
                'max_y': center_y + (height / 2) + margin
            }

            debug_print("CROP_CALC: Stair bbox: ({:.2f}, {:.2f}) to ({:.2f}, {:.2f})".format(
                stair_bbox.Min.X, stair_bbox.Min.Y, stair_bbox.Max.X, stair_bbox.Max.Y))
            debug_print("CROP_CALC: Crop region: ({:.2f}, {:.2f}) to ({:.2f}, {:.2f})".format(
                crop_bounds['min_x'], crop_bounds['min_y'], crop_bounds['max_x'], crop_bounds['max_y']))

            return crop_bounds

        except Exception as e:
            debug_print("CROP_CALC_ERROR: {}".format(str(e)))
            return self._get_default_crop_region()

    def _get_default_crop_region(self):
        """Return default crop region when calculation fails"""
        return {
            'min_x': -10.0,
            'max_x': 10.0,
            'min_y': -10.0,
            'max_y': 10.0
        }

# ╔═╗╦  ╔═╗╔═╗╔═╗╔═╗╔═╗
# ║  ║  ╠═╣╚═╗╚═╗║╣ ╚═╗
# ╚═╝╩═╝╩ ╩╚═╝╚═╝╚═╝╚═╝
class StairPlanGenerator:
    """
    Generate plan views untuk tangga di level-level tertentu
    Level-centric approach dengan hardcoded view range
    """

    def __init__(self, doc):
        self.doc = doc

    def create_stair_plan(self, stair, level, base_name, template=None):
        """
        Create plan view untuk satu level
        Returns tuple: (view, needs_view_range_setup)
        """
        try:
            # 1. VALIDATE INPUT
            if not stair or not level or not base_name:
                raise ValueError("Invalid input parameters")

            # 2. GENERATE VIEW NAME
            view_name = self._generate_view_name(base_name, level.Name)
            view_name = self._ensure_unique_view_name(view_name)

            # 3. CREATE VIEW
            debug_print("VIEW_CREATION: Creating plan view '{}' at level '{}'".format(view_name, level.Name))

            # Get plan view type - PRIORITIZE STRUCTURAL PLAN
            plan_view_types = FilteredElementCollector(self.doc)\
                .OfClass(ViewFamilyType)\
                .ToElements()

            structural_plan_type = None
            floor_plan_type = None  # Fallback only

            # Debug: Show all available view families first
            if DEBUG_MODE:
                debug_print("VIEW_TYPE_SEARCH: Available ViewFamily enum values:")
                try:
                    # Try to list all ViewFamily attributes
                    vf_attrs = [attr for attr in dir(ViewFamily) if not attr.startswith('_')]
                    debug_print("VIEW_TYPE_SEARCH: ViewFamily attributes: {}".format(vf_attrs))
                except Exception as e:
                    debug_print("VIEW_TYPE_SEARCH: Could not list ViewFamily attributes: {}".format(str(e)))

            for vft in plan_view_types:
                # Get ViewFamily FIRST (safer than Name property)
                try:
                    vft_family = vft.ViewFamily
                except Exception as e:
                    debug_print("VIEW_TYPE_SEARCH: Error accessing ViewFamily property: {}".format(str(e)))
                    continue

                # Get Name for logging (not critical)
                try:
                    vft_name = vft.Name if hasattr(vft, 'Name') else "ViewFamilyType_{}".format(vft.Id)
                except Exception as e:
                    vft_name = "ViewFamilyType_{}".format(vft.Id)
                    debug_print("VIEW_TYPE_SEARCH: Could not get Name property (but ViewFamily is valid): {}".format(str(e)))

                debug_print("VIEW_TYPE_SEARCH: Checking view family type: '{}' (ViewFamily: {})".format(vft_name, vft_family))

                # Check for StructuralPlan first (required)
                if vft_family == ViewFamily.StructuralPlan:
                    if structural_plan_type is None:  # Take first valid one
                        structural_plan_type = vft
                        debug_print("VIEW_TYPE_SEARCH: ✓ Found StructuralPlan type: '{}' (Id: {})".format(vft_name, vft.Id))

                # Check for FloorPlan (fallback, though we require StructuralPlan)
                elif vft_family == ViewFamily.FloorPlan:
                    if floor_plan_type is None:  # Take first valid one
                        floor_plan_type = vft
                        debug_print("VIEW_TYPE_SEARCH: ✓ Found FloorPlan type: '{}' (Id: {})".format(vft_name, vft.Id))

            # Require StructuralPlan - no fallback to FloorPlan
            if not structural_plan_type:
                raise ValueError("StructuralPlan view family type not found. This script requires StructuralPlan view type to be available in the project.")

            selected_view_type = structural_plan_type
            try:
                selected_name = selected_view_type.Name if hasattr(selected_view_type, 'Name') else "Unknown"
                debug_print("VIEW_TYPE_SEARCH: Selected StructuralPlan view type: '{}' (Id: {})".format(selected_name, selected_view_type.Id))
            except Exception as e:
                debug_print("VIEW_TYPE_SEARCH: Error accessing selected view type properties: {}".format(str(e)))
                debug_print("VIEW_TYPE_SEARCH: Selected view type Id: {}".format(selected_view_type.Id if selected_view_type else "None"))

            # Debug: Show which view type is being used
            if DEBUG_MODE:
                if structural_plan_type:
                    debug_print("VIEW_TYPE: ✓ Using StructuralPlan view family type")
                else:
                    debug_print("VIEW_TYPE: ⚠ WARNING - StructuralPlan not available, using FloorPlan as fallback")
                    debug_print("VIEW_TYPE: Available view families: {}".format([vft.ViewFamily for vft in plan_view_types]))

            # Create the view with selected type
            try:
                selected_name = selected_view_type.Name if hasattr(selected_view_type, 'Name') else "Unknown"
                debug_print("VIEW_CREATION: Attempting to create view with type: '{}' (Id: {})".format(selected_name, selected_view_type.Id))
            except Exception as e:
                debug_print("VIEW_CREATION: Error accessing view type name: {}".format(str(e)))
                debug_print("VIEW_CREATION: Attempting to create view with type Id: {}".format(selected_view_type.Id))

            try:
                plan_view = ViewPlan.Create(self.doc, selected_view_type.Id, level.Id)
                debug_print("VIEW_CREATION: ✓ View created successfully with Id: {}".format(plan_view.Id))
            except Exception as e:
                debug_print("VIEW_CREATION_ERROR: Failed to create view with selected type: {}".format(str(e)))
                debug_print("VIEW_CREATION_ERROR: Exception type: {}".format(type(e).__name__))
                try:
                    selected_name = selected_view_type.Name if hasattr(selected_view_type, 'Name') else "Unknown"
                    debug_print("VIEW_CREATION_ERROR: Selected type: '{}' (Id: {})".format(selected_name, selected_view_type.Id))
                except:
                    debug_print("VIEW_CREATION_ERROR: Selected type Id: {}".format(selected_view_type.Id))
                try:
                    debug_print("VIEW_CREATION_ERROR: Level: '{}' (Id: {})".format(level.Name, level.Id))
                except:
                    debug_print("VIEW_CREATION_ERROR: Level Id: {}".format(level.Id))
                import traceback
                debug_print("VIEW_CREATION_ERROR: Full traceback: {}".format(traceback.format_exc()))
                raise

            # Set view name - with better error handling
            try:
                # Check if name already exists first
                existing_views = FilteredElementCollector(self.doc)\
                    .OfClass(View)\
                    .ToElements()

                existing_names = [v.Name for v in existing_views]
                if view_name in existing_names:
                    debug_print("VIEW_CREATION: Warning - View name '{}' already exists, generating unique name".format(view_name))
                    view_name = self._ensure_unique_view_name(view_name)

                plan_view.get_Parameter(BuiltInParameter.VIEW_NAME).Set(view_name)
                debug_print("VIEW_CREATION: ✓ View name set to: '{}'".format(view_name))
            except Exception as e:
                debug_print("VIEW_CREATION_ERROR: Failed to set view name '{}': {}".format(view_name, str(e)))
                debug_print("VIEW_CREATION_ERROR: Exception type: {}".format(type(e).__name__))
                debug_print("VIEW_CREATION_ERROR: View Id: {}".format(plan_view.Id if plan_view else "None"))
                import traceback
                debug_print("VIEW_CREATION_ERROR: Full traceback: {}".format(traceback.format_exc()))
                raise

            # 4. SET BASIC PROPERTIES FIRST (before template)
            plan_view.Scale = 50
            plan_view.DetailLevel = ViewDetailLevel.Fine

            # 5. APPLY TEMPLATE (if provided)
            # NOTE: Template akan di-apply, tapi view range akan di-override SETELAH commit
            if template:
                plan_view.ViewTemplateId = template.Id
                debug_print("TEMPLATE: Applied template '{}' to view".format(template.Name))

            # 6. CALCULATE CROP REGION
            crop_calculator = StairCropCalculator()
            crop_bounds = crop_calculator.calculate_stair_bounds(stair, {})

            # 7. APPLY CROP BOX
            self._apply_crop_box(plan_view, crop_bounds)

            debug_print("VIEW_CREATION: View created successfully (Id: {})".format(plan_view.Id))

            # Verify view type
            if DEBUG_MODE:
                try:
                    view_family_type = self.doc.GetElement(plan_view.GetTypeId())
                    actual_view_family = view_family_type.ViewFamily
                    debug_print("VIEW_VERIFICATION: Created view type = {}".format(actual_view_family))
                    debug_print("VIEW_VERIFICATION: View family = {}".format(
                        "StructuralPlan" if actual_view_family == ViewFamily.StructuralPlan else "FloorPlan"))
                except Exception as e:
                    debug_print("VIEW_VERIFICATION_ERROR: {}".format(str(e)))

            # Return view and level for post-commit processing
            return (plan_view, level)

        except Exception as e:
            debug_print("VIEW_CREATION_ERROR: {}".format(str(e)))
            if EXEC_PARAMS.debug_mode:
                import traceback
                print(traceback.format_exc())
            return None

    def _find_stairs_for_level(self, level):
        """Find semua stairs yang terasosiasi dengan level tertentu"""
        stairs = []
        tolerance = 2.0  # 2 feet tolerance

        # Get all stairs in document
        stair_collector = FilteredElementCollector(self.doc)\
            .OfClass(Stairs)\
            .ToElements()

        for stair in stair_collector:
            # Check if stair spans this level
            stair_analyzer = StairAnalyzer(stair)
            if level.Elevation in stair_analyzer.elevations:
                stairs.append(stair)
            else:
                # Check with tolerance
                for elev in stair_analyzer.elevations:
                    if abs(level.Elevation - elev) <= tolerance:
                        stairs.append(stair)
                        break

        return stairs

    def _create_floor_plan_view(self, level, view_name):
        """Create floor plan view untuk level tertentu"""
        # Get plan view type - try StructuralPlan first, fallback to FloorPlan
        plan_view_types = FilteredElementCollector(self.doc)\
            .OfClass(ViewFamilyType)\
            .ToElements()

        structural_plan_type = None
        floor_plan_type = None

        for vft in plan_view_types:
            if vft.ViewFamily == ViewFamily.StructuralPlan:
                structural_plan_type = vft
            elif vft.ViewFamily == ViewFamily.FloorPlan:
                floor_plan_type = vft

        # Prioritas: StructuralPlan > FloorPlan
        selected_view_type = structural_plan_type or floor_plan_type

        if not selected_view_type:
            raise ValueError("No structural plan or floor plan view type found")

        if DEBUG_MODE:
            view_type_name = "StructuralPlan" if structural_plan_type else "FloorPlan (fallback)"
            debug_print("VIEW_TYPE: Using {} view family type".format(view_type_name))
            debug_print("VIEW_TYPE: StructuralPlan available: {}, FloorPlan available: {}".format(
                structural_plan_type is not None, floor_plan_type is not None))

        # Create the view
        plan_view = ViewPlan.Create(self.doc, selected_view_type.Id, level.Id)
        plan_view.Name = view_name

        return plan_view

    def _apply_hardcoded_view_range(self, plan_view, level):
        """
        Apply hardcoded view range: Cut/Top=900mm, Bottom/Depth=-1500mm
        MUST BE CALLED AFTER VIEW IS COMMITTED!
        """
        try:
            debug_print("VIEW_RANGE: Setting up view range for view '{}'".format(plan_view.Name))

            # Get current view range
            view_range = plan_view.GetViewRange()

            # HARDCODED VALUES IN MILLIMETERS (converted to feet for API)
            cut_height_mm = 900.0       # 900mm above level
            top_height_mm = 900.0       # 900mm above level
            bottom_offset_mm = -1500.0  # 1500mm below level
            depth_offset_mm = -1500.0   # 1500mm below level

            # Convert mm to feet for Revit API
            cut_height = mm_to_feet(cut_height_mm)
            top_height = mm_to_feet(top_height_mm)
            bottom_offset = mm_to_feet(bottom_offset_mm)
            depth_offset = mm_to_feet(depth_offset_mm)

            # Set Cut Plane
            view_range.SetLevelId(PlanViewPlane.CutPlane, level.Id)
            view_range.SetOffset(PlanViewPlane.CutPlane, cut_height)
            debug_print("  - Cut Plane: Level '{}' + {} ({:.3f}')".format(
                level.Name, format_offset_mm(cut_height), cut_height))

            # Set Top Clip Plane
            view_range.SetLevelId(PlanViewPlane.TopClipPlane, level.Id)
            view_range.SetOffset(PlanViewPlane.TopClipPlane, top_height)
            debug_print("  - Top Clip: Level '{}' + {} ({:.3f}')".format(
                level.Name, format_offset_mm(top_height), top_height))

            # Set Bottom Clip Plane
            view_range.SetLevelId(PlanViewPlane.BottomClipPlane, level.Id)
            view_range.SetOffset(PlanViewPlane.BottomClipPlane, bottom_offset)
            debug_print("  - Bottom Clip: Level '{}' {} ({:.3f}')".format(
                level.Name, format_offset_mm(bottom_offset), bottom_offset))

            # Set View Depth Plane
            view_range.SetLevelId(PlanViewPlane.ViewDepthPlane, level.Id)
            view_range.SetOffset(PlanViewPlane.ViewDepthPlane, depth_offset)
            debug_print("  - View Depth: Level '{}' {} ({:.3f}')".format(
                level.Name, format_offset_mm(depth_offset), depth_offset))

            # CRITICAL: Apply the view range back to the view
            plan_view.SetViewRange(view_range)

            debug_print("VIEW_RANGE: Successfully applied to '{}'".format(plan_view.Name))

            # Verify the settings
            verify_range = plan_view.GetViewRange()
            actual_cut = verify_range.GetOffset(PlanViewPlane.CutPlane)
            actual_bottom = verify_range.GetOffset(PlanViewPlane.BottomClipPlane)

            debug_print("VIEW_RANGE_VERIFY: Cut={} (expected: {}), Bottom={} (expected: {})".format(
                format_offset_mm(actual_cut), format_offset_mm(cut_height),
                format_offset_mm(actual_bottom), format_offset_mm(bottom_offset)))

        except Exception as e:
            debug_print("VIEW_RANGE_ERROR: {}".format(str(e)))
            if EXEC_PARAMS.debug_mode:
                import traceback
                print(traceback.format_exc())
            raise

    def _generate_view_name(self, base_name, level_name):
        """Generate view name: 'STAIRS-02_Level16'"""
        # Sanitize level name to remove invalid characters
        import re
        # Replace spaces and special characters with underscores
        sanitized_level_name = re.sub(r'[^\w\-]', '_', level_name)
        # Remove multiple consecutive underscores
        sanitized_level_name = re.sub(r'_+', '_', sanitized_level_name)
        # Remove leading/trailing underscores
        sanitized_level_name = sanitized_level_name.strip('_')

        return "{}_{}".format(base_name, sanitized_level_name)

    def _ensure_unique_view_name(self, view_name):
        """Ensure view name is unique by appending numbers if needed"""
        original_name = view_name
        counter = 1

        existing_views = FilteredElementCollector(self.doc)\
            .OfClass(View)\
            .ToElements()

        existing_names = [v.Name for v in existing_views]

        while view_name in existing_names:
            view_name = "{}({})".format(original_name, counter)
            counter += 1

        if view_name != original_name:
            debug_print("VIEW_NAMING: Renamed '{}' to '{}' for uniqueness".format(original_name, view_name))

        return view_name

    def _apply_crop_box(self, plan_view, crop_bounds):
        """Apply crop box to plan view"""
        try:
            # Enable crop box
            plan_view.CropBoxActive = True
            plan_view.CropBoxVisible = True

            # Get crop box
            crop_box = plan_view.CropBox

            # Set crop box coordinates
            crop_box.Min = XYZ(crop_bounds['min_x'], crop_bounds['min_y'], crop_box.Min.Z)
            crop_box.Max = XYZ(crop_bounds['max_x'], crop_bounds['max_y'], crop_box.Max.Z)

            debug_print("CROP_BOX: Applied to view - Min: ({:.2f}, {:.2f}), Max: ({:.2f}, {:.2f})".format(
                crop_bounds['min_x'], crop_bounds['min_y'], crop_bounds['max_x'], crop_bounds['max_y']))

        except Exception as e:
            debug_print("CROP_BOX_ERROR: {}".format(str(e)))
            raise

    def batch_create_stair_plans(self, stair, selected_levels, base_name, template=None):
        """
        Create multiple plan views for stairs - NO TRANSACTION MANAGEMENT HERE
        Transaction will be handled at the calling level (like Wall Plan Generator)
        """
        created_views = []
        failed_levels = []
        views_with_levels = []  # Store (view, level) tuples for post-processing

        if DEBUG_MODE:
            debug_print("BATCH_CREATION: Starting batch creation for {} levels".format(len(selected_levels)))

        # NO TRANSACTION HERE - let caller handle it
        for level in selected_levels:
            try:
                result = self.create_stair_plan(stair, level, base_name, template)
                if result:
                    view, level_ref = result
                    views_with_levels.append((view, level_ref))
                    created_views.append(view)
                    if DEBUG_MODE:
                        debug_print("BATCH_CREATION: ✓ Created view for level {}".format(level.Name))
                else:
                    failed_levels.append((level, "Failed to create view"))
                    if DEBUG_MODE:
                        debug_print("BATCH_CREATION: ✗ Failed for level {}".format(level.Name))

            except Exception as e:
                failed_levels.append((level, str(e)))
                if DEBUG_MODE:
                    debug_print("BATCH_CREATION: ✗ Failed for level {}: {}".format(level.Name, str(e)))

        result = {
            'success': created_views,
            'failed': failed_levels,
            'count': len(created_views),
            'views_with_levels': views_with_levels  # Return this for post-processing
        }

        if DEBUG_MODE:
            debug_print("BATCH_CREATION: Completed - {} success, {} failed".format(len(created_views), len(failed_levels)))

        return result

# ╔═╗╦  ╔═╗╔═╗╔═╗╔═╗╔═╗
# ║  ║  ╠═╣╚═╗╚═╗║╣ ╚═╗
# ╚═╝╩═╝╩ ╩╚═╝╚═╝╚═╝╚═╝
class LevelSelector:
    """
    Menentukan level mana saja yang bisa menampilkan tangga
    Level-centric approach: pilih level dulu, baru cari stairs
    """

    def __init__(self, doc):
        self.doc = doc

    def get_applicable_levels(self, multistory_stairs):
        """
        Get all levels in the project for stair plan creation

        Algorithm:
        1. Get all levels in the document
        2. Sort by elevation (bottom to top)
        3. Return list of all levels
        """
        try:
            # Get all levels in the document
            all_levels_collector = FilteredElementCollector(self.doc)\
                .OfClass(Level)\
                .ToElements()

            # Convert to Python list for sorting
            all_levels = list(all_levels_collector)

            debug_print("ALL_LEVELS: Found {} levels in project".format(len(all_levels)))

            # Sort by elevation (bottom to top)
            all_levels.sort(key=lambda l: l.Elevation)

            for level in all_levels:
                debug_print("PROJECT_LEVEL: '{}' at {:.2f}'".format(level.Name, level.Elevation))

            return all_levels

        except Exception as e:
            debug_print("LEVEL_ANALYSIS_ERROR: {}".format(str(e)))
            return []

    def select_target_levels(self, applicable_levels):
        """
        Present level selection dialog to user WITH MILLIMETER DISPLAY
        Returns list of selected levels
        """
        if not applicable_levels:
            forms.alert("No applicable levels found for this stair.", title="Level Selection")
            return []

        # Prepare options for selection WITH MILLIMETER DISPLAY
        level_options = []
        for level in applicable_levels:
            elev_mm = feet_to_mm(level.Elevation)
            # Format: "Level 1 (+0 mm)" or "Level 2 (+3500 mm)"
            option_text = "{} ({})".format(level.Name, format_elevation_mm(level.Elevation))

            level_options.append({
                'name': option_text,
                'value': level
            })

        # Show selection dialog
        selected_options = forms.SelectFromList.show(
            [opt['name'] for opt in level_options],
            title="Select Target Levels for Stair Plans (elevations in mm)",
            multiselect=True
        )

        if not selected_options:
            return []

        # Convert back to level objects
        selected_levels = []
        for selected_name in selected_options:
            for option in level_options:
                if option['name'] == selected_name:
                    selected_levels.append(option['value'])
                    break

        debug_print("LEVEL_SELECTION: User selected {} levels".format(len(selected_levels)))

        return selected_levels

# ╔═╗╦ ╦╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔╔═╗
# ╠╣ ║ ║║║║║   ║ ║║ ║║║║╚═╗
# ╚  ╚═╝╝╚╝╚═╝ ╩ ╩╚═╝╝╚╝╚═╝
class StairSelectionFilter(ISelectionFilter):
    """Filter untuk memilih hanya MULTISTORY stair elements"""

    def AllowElement(self, element):
        if element.ViewSpecific:
            return False

        # Check if element is a MultistoryStairs (proper Revit API class)
        return isinstance(element, MultistoryStairs)

    def AllowReference(self, reference, position):
        return False

# ╦ ╦╔═╗╦  ╦  ╔═╗
# ║║║╠═╣║  ║  ╚═╗
# ╚╩╝╩ ╩╩═╝╩═╝╚═╝ MAIN WORKFLOW
#----------------------------------------------------------------------
# 1️⃣ User Input - Select Stair
selected_stair = None

try:
    # Create selection filter for stairs
    stair_filter = StairSelectionFilter()

    # Prompt user to select stair
    with forms.WarningBar(title='Select a MULTISTORY STAIRS element and click "Finish"'):
        stair_refs = uidoc.Selection.PickObjects(ObjectType.Element, stair_filter)

    if stair_refs:
        selected_stair = doc.GetElement(stair_refs[0].ElementId)

        # Additional validation and info for MultistoryStairs
        debug_print("SELECTED_MULTISTORY_STAIRS: Id {}".format(selected_stair.Id))

        # Get all stairs IDs in this multistory element
        all_stairs_ids = selected_stair.GetAllStairsIds()
        debug_print("TOTAL_STAIRS_IN_MULTISTORY: {}".format(len(all_stairs_ids)))

        # Get connected levels - check available methods
        try:
            # Try different methods to get connected levels
            if hasattr(selected_stair, 'GetConnectedLevels'):
                connected_levels = selected_stair.GetConnectedLevels()
                debug_print("CONNECTED_LEVELS: {}".format([level.Name for level in connected_levels]))
            else:
                debug_print("GetConnectedLevels method not available, checking alternatives...")

                # Alternative: get all stairs and extract levels
                all_stairs_ids = selected_stair.GetAllStairsIds()
                connected_levels = []
                debug_print("DEBUGGING_STAIRS: Processing {} stairs".format(len(all_stairs_ids)))

                for i, stair_id in enumerate(all_stairs_ids):
                    stair = doc.GetElement(stair_id)
                    debug_print("STAIR_{}: Id={}, Element={}".format(i, stair_id, stair is not None))

                    if stair:
                        # Check what attributes the stair has
                        stair_attrs = [attr for attr in dir(stair) if 'level' in attr.lower() or 'Level' in attr]
                        debug_print("STAIR_{}_ATTRS: {}".format(i, stair_attrs))

                        # Try different ways to get level
                        level = None
                        if hasattr(stair, 'LevelId') and stair.LevelId != ElementId.InvalidElementId:
                            level = doc.GetElement(stair.LevelId)
                            debug_print("STAIR_{}_LEVEL_FROM_LevelId: {}".format(i, level.Name if level else None))
                        elif hasattr(stair, 'get_Parameter'):
                            # Try to get level from parameter
                            level_param = stair.get_Parameter(BuiltInParameter.STAIRS_BASE_LEVEL_PARAM)
                            if level_param and level_param.HasValue:
                                level_id = level_param.AsElementId()
                                level = doc.GetElement(level_id)
                                debug_print("STAIR_{}_LEVEL_FROM_PARAM: {}".format(i, level.Name if level else None))

                        if level and level not in connected_levels:
                            connected_levels.append(level)
                            debug_print("ADDED_LEVEL: {}".format(level.Name))

                debug_print("EXTRACTED_LEVELS_FROM_STAIRS: {}".format([level.Name for level in connected_levels]))

        except Exception as e:
            debug_print("ERROR_GETTING_LEVELS: {}".format(str(e)))
            connected_levels = []

    else:
        forms.alert("No stair selected. Please try again.", title="Selection Cancelled")
        script.exit()

except Exception as e:
    if EXEC_PARAMS.debug_mode:
        print("STAIR_SELECTION_ERROR: {}".format(str(e)))
        import traceback
        print(traceback.format_exc())
    forms.alert("Error selecting stair: {}".format(str(e)), title="Selection Error")
    script.exit()

#----------------------------------------------------------------------
# 2️⃣ User Input - Enter Base Name
base_name = forms.ask_for_string(
    default="STAIRS-01",
    prompt="Enter base name for stair plans (e.g., STAIRS-02):",
    title="Stair Plan Naming"
)

if not base_name:
    forms.alert("No name provided. Using default name.", title="Naming")
    base_name = "STAIRS-01"

debug_print("NAMING: User selected base name: '{}'".format(base_name))

#----------------------------------------------------------------------
# 3️⃣ Determine Applicable Levels
level_selector = LevelSelector(doc)
applicable_levels = level_selector.get_applicable_levels(selected_stair)

if not applicable_levels:
    forms.alert("No applicable levels found for the selected stair. "
               "The stair may not span multiple levels or levels may not be properly defined.",
               title="No Applicable Levels")
    script.exit()

debug_print("LEVELS: Found {} applicable levels: {}".format(
    len(applicable_levels), [l.Name for l in applicable_levels]))

#----------------------------------------------------------------------
# 4️⃣ User Select Target Levels
selected_levels = level_selector.select_target_levels(applicable_levels)

if not selected_levels:
    forms.alert("No levels selected. Operation cancelled.", title="Level Selection")
    script.exit()

debug_print("LEVELS: User selected {} levels: {}".format(
    len(selected_levels), [l.Name for l in selected_levels]))

#----------------------------------------------------------------------
# 5️⃣ User Select View Template (Optional)
view_templates = [v for v in FilteredElementCollector(doc)\
    .OfClass(View)\
    .ToElements() if v.IsTemplate and (v.ViewType == ViewType.FloorPlan)]  # Only FloorPlan for now

# Add "None" option
template_options = [{'name': 'None (use default)', 'value': None}]
for template in view_templates:
    template_options.append({'name': template.Name, 'value': template})

selected_template_option = forms.SelectFromList.show(
    [opt['name'] for opt in template_options],
    title="Select View Template (Optional)",
    multiselect=False
)

selected_template = None
if selected_template_option and selected_template_option[0] != 'None (use default)':
    for opt in template_options:
        if opt['name'] == selected_template_option[0]:
            selected_template = opt['value']
            break

debug_print("TEMPLATE: Selected template: {}".format(selected_template.Name if selected_template else 'None'))

#----------------------------------------------------------------------
# 6️⃣ Generate Stair Plans (WITH TRANSACTION LIKE WALL PLAN GENERATOR)
debug_print("GENERATION: Starting stair plan generation...")

# Start Transaction BEFORE calling generator (like Wall Plan Generator)
t = Transaction(doc, 'Stair Plan Generation')
t.Start()

try:
    generator = StairPlanGenerator(doc)
    result = generator.batch_create_stair_plans(
        selected_stair,
        selected_levels,
        base_name,
        selected_template
    )

    # Apply view ranges AFTER view creation (within same transaction)
    if result['views_with_levels']:
        debug_print("VIEW_RANGE_SETUP: Applying view ranges to {} views".format(len(result['views_with_levels'])))

        for view, level in result['views_with_levels']:
            try:
                generator._apply_hardcoded_view_range(view, level)
                debug_print("VIEW_RANGE_SETUP: ✓ Applied to '{}'".format(view.Name))
            except Exception as e:
                debug_print("VIEW_RANGE_SETUP: ✗ Failed for '{}': {}".format(view.Name, str(e)))

    # Commit transaction AFTER all operations complete
    t.Commit()
    debug_print("TRANSACTION: Successfully committed all changes")

except Exception as e:
    # Rollback on error
    t.RollBack()
    debug_print("TRANSACTION: Rolled back due to error: {}".format(str(e)))
    forms.alert("Plan generation failed: {}".format(str(e)), title="Generation Error")
    script.exit()

#----------------------------------------------------------------------
# 7️⃣ Display Results
output.print_md("# Stair Plan Generation Results")
output.print_md("---")

if result['success']:
    output.print_md("## ✅ Successfully Created Views")
    output.print_md("**Stair:** {}  |  **Base Name:** {}".format(
        output.linkify(selected_stair.Id), base_name))

    table_data = []
    for view in result['success']:
        level = view.GenLevel
        level_name = level.Name if level else "Unknown"
        level_elevation = format_elevation_mm(level.Elevation) if level else "N/A"
        table_data.append([
            base_name,
            level_name,
            level_elevation,
            output.linkify(view.Id)
        ])

    output.print_table(
        table_data=table_data,
        title="Generated Stair Plan Views",
        columns=["Base Name", "Level", "Elevation", "View"]
    )

if result['failed']:
    output.print_md("## ⚠️ Failed Levels")
    for level, error in result['failed']:
        level_elevation = format_elevation_mm(level.Elevation)
        output.print_md("- **{} ({})**: {}".format(level.Name, level_elevation, error))

output.print_md("---")
output.print_md("**Summary:** {} views created, {} failed".format(result['count'], len(result['failed'])))

#----------------------------------------------------------------------
# Debug Summary
if DEBUG_MODE:
    output.print_md("## 🔍 Debug Information")
    output.print_md("**Selected Stair ID:** {}".format(selected_stair.Id))
    output.print_md("**Base Name:** {}".format(base_name))

    # Show selected levels with elevations in mm
    level_list = []
    for lvl in selected_levels:
        level_list.append("{} ({})".format(lvl.Name, format_elevation_mm(lvl.Elevation)))
    output.print_md("**Selected Levels:** {}".format(", ".join(level_list)))

    output.print_md("**Template:** {}".format(selected_template.Name if selected_template else "None"))
    output.print_md("**View Range (in mm):**")
    output.print_md("- Cut Plane: +900 mm")
    output.print_md("- Top Clip: +900 mm")
    output.print_md("- Bottom Clip: -1500 mm")
    output.print_md("- View Depth: -1500 mm")
    output.print_md("**Display Units:** Millimeters (mm)")
    output.print_md("**Debug Mode:** Enabled")

debug_print("SCRIPT_COMPLETION: Stair Plan Generator finished")
