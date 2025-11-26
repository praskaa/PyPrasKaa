# -*- coding: utf-8 -*-
"""
Wall Plan Generator Module
Core logic for creating plan views for wall groups

Author: Generated from EF Element Sections Generator analysis
Version: 1.0.0
"""

from Autodesk.Revit.DB import *


class WallPlanGenerator:
    """
    Handles plan view creation for wall groups at specific elevations
    """

    def __init__(self, doc):
        """
        Initialize WallPlanGenerator

        Args:
            doc: Revit Document
        """
        self.doc = doc

    def create_plan_view_for_wall_group(self, walls, classification, target_level):
        """
        Create a plan view for a group of walls with the same classification

        Args:
            walls: List of wall elements
            classification: Classification string (e.g., "W5")
            target_level: Level object to create plan view on

        Returns:
            ViewPlan or None: Created plan view or None if failed
        """
        try:
            try:
                from script import DEBUG_MODE
                debug_enabled = DEBUG_MODE
            except:
                debug_enabled = False

            if debug_enabled:
                print("DEBUG WallPlanGenerator: Starting plan view creation for classification '{}' at level '{}'".format(classification, target_level.Name))

            # Generate unique view name
            view_name = self.generate_view_name(walls, classification, target_level.Name)
            view_name = self.ensure_unique_view_name(view_name)
            if debug_enabled:
                print("DEBUG WallPlanGenerator: Generated view name: '{}'".format(view_name))

            # Create plan view using the provided level
            if debug_enabled:
                print("DEBUG WallPlanGenerator: Creating ViewPlan.Create with doc={}, level_id={}, view_name='{}'".format(self.doc, target_level.Id, view_name))
            plan_view = ViewPlan.Create(self.doc, target_level.Id, view_name)
            if debug_enabled:
                print("DEBUG WallPlanGenerator: Plan view created successfully: {}".format(plan_view.Name))

            # Calculate and set crop region based on wall group
            crop_region = self.calculate_group_bounding_box(walls, target_level.Elevation)
            if debug_enabled:
                print("DEBUG WallPlanGenerator: Crop region calculated: {}".format(crop_region))
            if crop_region:
                self.set_view_crop_box(plan_view, crop_region, target_level.Elevation)
                if debug_enabled:
                    print("DEBUG WallPlanGenerator: Crop box set successfully")

            if debug_enabled:
                print("DEBUG WallPlanGenerator: Plan view creation completed successfully")
            return plan_view

        except Exception as e:
            try:
                from script import DEBUG_MODE
                if DEBUG_MODE:
                    print("DEBUG WallPlanGenerator: Exception occurred: {}".format(str(e)))
                    import traceback
                    print("DEBUG WallPlanGenerator: Full traceback:")
                    print(traceback.format_exc())
            except:
                pass
            print("Error creating plan view for {}: {}".format(classification, str(e)))
            return None

    def calculate_wall_group_elevation(self, walls):
        """
        Calculate representative elevation for plan view from wall group

        Args:
            walls: List of wall elements

        Returns:
            float: Target elevation for plan view
        """
        if not walls:
            return 0.0

        # Use first wall as representative for elevation calculation
        representative_wall = walls[0]
        return self.calculate_wall_mid_height(representative_wall)

    def calculate_wall_mid_height(self, wall):
        """
        Calculate mid-height elevation for a wall

        Args:
            wall: Revit Wall element

        Returns:
            float: Mid-height elevation
        """
        try:
            # Get wall base constraint level
            base_param = wall.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)
            if base_param and base_param.AsElementId() != ElementId.InvalidElementId:
                base_level = self.doc.GetElement(base_param.AsElementId())
                base_elevation = base_level.Elevation
            else:
                # Fallback to bounding box
                bb = wall.get_BoundingBox(None)
                if bb:
                    base_elevation = bb.Min.Z
                else:
                    return 0.0

            # Get wall height
            height_param = wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)
            if height_param and height_param.HasValue:
                wall_height = height_param.AsDouble()
            else:
                # Fallback to bounding box height
                if bb:
                    wall_height = bb.Max.Z - bb.Min.Z
                else:
                    return base_elevation

            # Calculate mid-height
            return base_elevation + (wall_height / 2)

        except Exception as e:
            print("Error calculating wall elevation: {}".format(str(e)))
            return 0.0

    def calculate_group_bounding_box(self, walls, target_elevation):
        """
        Calculate 2D bounding box for wall group at target elevation

        Args:
            walls: List of wall elements
            target_elevation: Z-coordinate for plan view

        Returns:
            dict or None: Bounding box coordinates or None if failed
        """
        if not walls:
            return None

        # Initialize with first wall
        first_bb = self.calculate_wall_2d_bounds_at_elevation(walls[0], target_elevation)
        if not first_bb:
            return None

        min_x, max_x, min_y, max_y = first_bb

        # Expand for other walls
        for wall in walls[1:]:
            wall_bb = self.calculate_wall_2d_bounds_at_elevation(wall, target_elevation)
            if wall_bb:
                min_x = min(min_x, wall_bb[0])
                max_x = max(max_x, wall_bb[1])
                min_y = min(min_y, wall_bb[2])
                max_y = max(max_y, wall_bb[3])

        # Add padding (10% of dimensions)
        width = max_x - min_x
        height = max_y - min_y
        padding_x = width * 0.1
        padding_y = height * 0.1

        return {
            'min_x': min_x - padding_x,
            'max_x': max_x + padding_x,
            'min_y': min_y - padding_y,
            'max_y': max_y + padding_y
        }

    def calculate_wall_2d_bounds_at_elevation(self, wall, elevation):
        """
        Calculate wall footprint bounds at specific elevation

        Args:
            wall: Wall element
            elevation: Target Z-coordinate

        Returns:
            tuple or None: (min_x, max_x, min_y, max_y) or None if failed
        """
        try:
            # Get wall curve
            wall_curve = wall.Location.Curve
            if not wall_curve:
                return None

            # Get wall thickness
            width_param = wall.get_Parameter(BuiltInParameter.WALL_ATTR_WIDTH_PARAM)
            wall_thickness = width_param.AsDouble() if width_param else 1.0

            # Get curve endpoints
            start_point = wall_curve.GetEndPoint(0)
            end_point = wall_curve.GetEndPoint(1)

            # Calculate wall direction vector
            wall_vector = end_point - start_point
            wall_length = wall_vector.GetLength()

            if wall_length == 0:
                return None

            # Calculate perpendicular vector for wall thickness
            perp_vector = XYZ(-wall_vector.Y, wall_vector.X, 0).Normalize()
            half_thickness = wall_thickness / 2

            # Calculate corner points of wall footprint
            p1 = start_point + (perp_vector * half_thickness)
            p2 = start_point - (perp_vector * half_thickness)
            p3 = end_point - (perp_vector * half_thickness)
            p4 = end_point + (perp_vector * half_thickness)

            # Extract X and Y coordinates
            x_coords = [p1.X, p2.X, p3.X, p4.X]
            y_coords = [p1.Y, p2.Y, p3.Y, p4.Y]

            return min(x_coords), max(x_coords), min(y_coords), max(y_coords)

        except Exception as e:
            print("Error calculating wall bounds: {}".format(str(e)))
            return None

    def get_or_create_level_at_elevation(self, elevation, level_name):
        """
        Find existing level or create new one at elevation

        Args:
            elevation: Target elevation
            level_name: Suggested level name

        Returns:
            Level: Revit Level object
        """
        levels = FilteredElementCollector(self.doc).OfClass(Level).ToElements()
        tolerance = 0.1  # 100mm tolerance

        # Search for existing level at elevation
        for level in levels:
            if abs(level.Elevation - elevation) < tolerance:
                try:
                    from script import DEBUG_MODE
                    if DEBUG_MODE:
                        print("DEBUG get_or_create_level_at_elevation: Found existing level '{}' at elevation {}".format(level.Name, level.Elevation))
                except:
                    pass
                return level

        # Create new level - but we can't do this without transaction!
        try:
            from script import DEBUG_MODE
            if DEBUG_MODE:
                print("DEBUG get_or_create_level_at_elevation: No existing level found at elevation {}, would need to create new level".format(elevation))
                print("DEBUG get_or_create_level_at_elevation: But we can't create levels without transaction!")
                print("DEBUG get_or_create_level_at_elevation: Using the selected level '{}' instead".format(level_name))
        except:
            pass

        # For now, return None - the calling code should handle this
        # In the future, we need to pass the selected level from the UI
        return None

    def set_view_crop_box(self, view, crop_region, elevation):
        """
        Set view crop box to focus on wall group

        Args:
            view: Plan view to modify
            crop_region: Dictionary with min_x, max_x, min_y, max_y
            elevation: Z-coordinate for crop box
        """
        try:
            crop_box = view.CropBox
            crop_box.Min = XYZ(crop_region['min_x'], crop_region['min_y'], elevation - 0.5)
            crop_box.Max = XYZ(crop_region['max_x'], crop_region['max_y'], elevation + 0.5)
            view.CropBox = crop_box

            view.CropBoxVisible = True
            view.CropBoxActive = True

        except Exception as e:
            print("Error setting crop box: {}".format(str(e)))

    def generate_view_name(self, walls, classification, level_name):
        """
        Generate standardized view name

        Args:
            walls: List of wall elements
            classification: Classification string
            level_name: Level name

        Returns:
            str: Generated view name
        """
        if not walls:
            return "Wall Plan-{}-{}".format(classification, level_name)

        # Get wall type name from first wall
        first_wall = walls[0]
        wall_type = self.doc.GetElement(first_wall.GetTypeId())

        # Debug: Check wall_type object
        try:
            from script import DEBUG_MODE
            if DEBUG_MODE:
                print("DEBUG generate_view_name: wall_type = {}".format(wall_type))
                print("DEBUG generate_view_name: wall_type type = {}".format(type(wall_type)))
        except:
            pass

        # Safe access to Name property
        try:
            if wall_type and hasattr(wall_type, 'Name'):
                type_name = wall_type.Name
                try:
                    from script import DEBUG_MODE
                    if DEBUG_MODE:
                        print("DEBUG generate_view_name: wall_type.Name = '{}'".format(type_name))
                except:
                    pass
            else:
                try:
                    from script import DEBUG_MODE
                    if DEBUG_MODE:
                        print("DEBUG generate_view_name: wall_type has no Name attribute or is None")
                except:
                    pass
                type_name = "Wall"
        except Exception as e:
            try:
                from script import DEBUG_MODE
                if DEBUG_MODE:
                    print("DEBUG generate_view_name: Exception accessing Name: {}".format(str(e)))
            except:
                pass
            type_name = "Wall"

        try:
            from script import DEBUG_MODE
            if DEBUG_MODE:
                print("DEBUG generate_view_name: final type_name = '{}'".format(type_name))
        except:
            pass
        result = "{}-{}-{}".format(type_name, classification, level_name)
        try:
            from script import DEBUG_MODE
            if DEBUG_MODE:
                print("DEBUG generate_view_name: generated name = '{}'".format(result))
        except:
            pass
        return result

    def ensure_unique_view_name(self, base_name):
        """
        Ensure view name is unique in document

        Args:
            base_name: Base name to make unique

        Returns:
            str: Unique view name
        """
        existing_views = FilteredElementCollector(self.doc).OfClass(View).ToElements()
        existing_names = {view.Name for view in existing_views}

        counter = 1
        unique_name = base_name

        while unique_name in existing_names:
            unique_name = "{} ({})".format(base_name, counter)
            counter += 1

        return unique_name

    def ensure_unique_level_name(self, base_name):
        """
        Ensure level name is unique in document

        Args:
            base_name: Base name to make unique

        Returns:
            str: Unique level name
        """
        levels = FilteredElementCollector(self.doc).OfClass(Level).ToElements()
        existing_names = {level.Name for level in levels}

        counter = 1
        unique_name = base_name

        while unique_name in existing_names:
            unique_name = "{} ({})".format(base_name, counter)
            counter += 1

        return unique_name