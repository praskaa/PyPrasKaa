# -*- coding: utf-8 -*-
"""
View Generator Library
Reusable view generation utilities for pyRevit scripts

Author: Generated from EF Element Sections Generator analysis
Version: 1.0.0
"""

from Autodesk.Revit.DB import *


class ViewGenerator:
    """
    Reusable view generation utilities based on EF Element Sections Generator
    """

    def __init__(self, doc):
        """
        Initialize ViewGenerator

        Args:
            doc: Revit Document
        """
        self.doc = doc

    def create_plan_view_for_elements(self, elements, level, view_name_base, crop_region=True):
        """
        Create a plan view for a group of elements at specified level

        Based on EF Element Sections Generator logic

        Args:
            elements: List of Revit elements
            level: Level object for the plan view
            view_name_base: Base name for the view
            crop_region: Whether to set crop region (default True)

        Returns:
            ViewPlan or None: Created plan view or None if failed
        """
        try:
            # Get element properties using EF logic
            element_props = self._get_element_properties(elements[0])  # Use first element as representative

            # Create SectionGenerator (from EF Snippets._views)
            from Snippets._views import SectionGenerator

            gen = SectionGenerator(self.doc,
                                 origin=element_props.origin,
                                 vector=element_props.vector,
                                 width=element_props.width,
                                 height=element_props.height,
                                 offset=element_props.offset,
                                 depth=element_props.depth,
                                 depth_offset=element_props.depth_offset)

            # Generate views using EF method
            elev, cross, plan = gen.create_sections(view_name_base=view_name_base)

            # Set crop region if requested
            if crop_region and plan:
                crop_bounds = self._calculate_group_crop_region(elements, level.Elevation)
                if crop_bounds:
                    self._set_view_crop_box(plan, crop_bounds, level.Elevation)

            return plan

        except Exception as e:
            print("Error creating plan view: {}".format(str(e)))
            return None

    def create_elevation_view_for_elements(self, elements, level, view_name_base, crop_region=True):
        """
        Create an elevation view for a group of elements

        Args:
            elements: List of Revit elements
            level: Level object for reference
            view_name_base: Base name for the view
            crop_region: Whether to set crop region (default True)

        Returns:
            ViewSection or None: Created elevation view or None if failed
        """
        try:
            # Get element properties
            element_props = self._get_element_properties(elements[0])

            # Create SectionGenerator
            from Snippets._views import SectionGenerator

            gen = SectionGenerator(self.doc,
                                 origin=element_props.origin,
                                 vector=element_props.vector,
                                 width=element_props.width,
                                 height=element_props.height,
                                 offset=element_props.offset,
                                 depth=element_props.depth,
                                 depth_offset=element_props.depth_offset)

            # Generate views and return elevation
            elev, cross, plan = gen.create_sections(view_name_base=view_name_base)

            # Set crop region if requested
            if crop_region and elev:
                crop_bounds = self._calculate_group_crop_region(elements, level.Elevation)
                if crop_bounds:
                    self._set_view_crop_box(elev, crop_bounds, level.Elevation)

            return elev

        except Exception as e:
            print("Error creating elevation view: {}".format(str(e)))
            return None

    def create_cross_section_view_for_elements(self, elements, level, view_name_base, crop_region=True):
        """
        Create a cross section view for a group of elements

        Args:
            elements: List of Revit elements
            level: Level object for reference
            view_name_base: Base name for the view
            crop_region: Whether to set crop region (default True)

        Returns:
            ViewSection or None: Created cross section view or None if failed
        """
        try:
            # Get element properties
            element_props = self._get_element_properties(elements[0])

            # Create SectionGenerator
            from Snippets._views import SectionGenerator

            gen = SectionGenerator(self.doc,
                                 origin=element_props.origin,
                                 vector=element_props.vector,
                                 width=element_props.width,
                                 height=element_props.height,
                                 offset=element_props.offset,
                                 depth=element_props.depth,
                                 depth_offset=element_props.depth_offset)

            # Generate views and return cross section
            elev, cross, plan = gen.create_sections(view_name_base=view_name_base)

            # Set crop region if requested
            if crop_region and cross:
                crop_bounds = self._calculate_group_crop_region(elements, level.Elevation)
                if crop_bounds:
                    self._set_view_crop_box(cross, crop_bounds, level.Elevation)

            return cross

        except Exception as e:
            print("Error creating cross section view: {}".format(str(e)))
            return None

    def _get_element_properties(self, element):
        """
        Get element properties using EF ElementProperties logic

        Args:
            element: Revit element

        Returns:
            ElementProperties object
        """
        # Import and use EF ElementProperties class
        # This replicates the logic from EF script
        from Snippets._vectors import rotate_vector

        class ElementProperties:
            def __init__(self, el):
                self.el = el
                self.origin = None
                self.vector = None
                self.width = None
                self.height = None
                self.offset = 1.0
                self.depth = 1.0
                self.depth_offset = 1.0
                self.valid = False

                if type(el) == Wall:
                    self._get_wall_properties()
                else:
                    self._get_generic_properties()

            def _get_wall_properties(self):
                wall_curve = self.el.Location.Curve
                pt_start = wall_curve.GetEndPoint(0)
                pt_end = wall_curve.GetEndPoint(1)
                self.vector = pt_end - pt_start
                self.width = self.vector.GetLength()
                self.height = self.el.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).AsDouble()

                BB = self.el.get_BoundingBox(None)
                self.origin = (BB.Max + BB.Min) / 2

            def _get_generic_properties(self):
                el_type = self.doc.GetElement(self.el.GetTypeId())
                BB = self.el.get_BoundingBox(None)
                BB_typ = el_type.get_BoundingBox(None)

                el_fam = el_type.Family
                el_placement = el_fam.FamilyPlacementType
                fpt = FamilyPlacementType

                # Point-based families
                if el_placement in [fpt.OneLevelBased, fpt.TwoLevelsBased, fpt.WorkPlaneBased]:
                    self.origin = (BB.Max + BB.Min) / 2
                    self.width = (BB_typ.Max.X - BB_typ.Min.X)
                    self.height = (BB_typ.Max.Z - BB_typ.Min.Z)
                    self.depth = (BB_typ.Max.Y - BB_typ.Min.Y)

                    pt_start = XYZ(BB_typ.Min.X, (BB_typ.Min.Y + BB_typ.Max.Y) / 2, BB_typ.Min.Z)
                    pt_end = XYZ(BB_typ.Max.X, (BB_typ.Min.Y + BB_typ.Max.Y) / 2, BB_typ.Min.Z)
                    self.vector = pt_end - pt_start

                    try:
                        rotation_rad = self.el.Location.Rotation
                        self.vector = rotate_vector(self.vector, rotation_rad)
                    except:
                        pass

                # Curve-based families
                elif el_placement in [fpt.CurveBased, fpt.CurveDrivenStructural]:
                    curve = self.el.Location.Curve
                    self.origin = (BB.Max + BB.Min) / 2
                    pt_start = curve.GetEndPoint(0)
                    pt_end = curve.GetEndPoint(1)

                    if pt_start.Z != pt_end.Z:
                        pt_start = XYZ(pt_start.X, pt_start.Y, pt_start.Z)
                        pt_end = XYZ(pt_end.X, pt_end.Y, pt_start.Z)

                    self.vector = pt_end - pt_start
                    self.width = self.vector.GetLength()
                    self.height = (BB.Max.Z - BB.Min.Z)

                # Hosted families
                elif el_placement == fpt.OneLevelBasedHosted:
                    host = self.el.Host
                    if type(host) == Wall:
                        wall_curve = host.Location.Curve
                        pt_start = wall_curve.GetEndPoint(0)
                        pt_end = wall_curve.GetEndPoint(1)
                        self.vector = pt_end - pt_start

                        try:
                            if self.el.FacingFlipped:
                                self.vector = -self.vector
                        except:
                            pass

                        self.origin = (BB.Max + BB.Min) / 2
                        self.width = (BB_typ.Max.X - BB_typ.Min.X)
                        self.height = (BB_typ.Max.Z - BB_typ.Min.Z)

        return ElementProperties(element)

    def _calculate_group_crop_region(self, elements, elevation):
        """
        Calculate crop region for group of elements

        Args:
            elements: List of elements
            elevation: Z elevation for plan

        Returns:
            dict or None: Crop region bounds
        """
        if not elements:
            return None

        # Initialize with first element
        first_bb = self._calculate_element_2d_bounds_at_elevation(elements[0], elevation)
        if not first_bb:
            return None

        min_x, max_x, min_y, max_y = first_bb

        # Expand for other elements
        for element in elements[1:]:
            element_bb = self._calculate_element_2d_bounds_at_elevation(element, elevation)
            if element_bb:
                min_x = min(min_x, element_bb[0])
                max_x = max(max_x, element_bb[1])
                min_y = min(min_y, element_bb[2])
                max_y = max(max_y, element_bb[3])

        # Add padding
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

    def _calculate_element_2d_bounds_at_elevation(self, element, elevation):
        """
        Calculate 2D bounds of element at specific elevation

        Args:
            element: Revit element
            elevation: Z coordinate

        Returns:
            tuple or None: (min_x, max_x, min_y, max_y) or None
        """
        try:
            BB = element.get_BoundingBox(None)
            if not BB:
                return None

            return BB.Min.X, BB.Max.X, BB.Min.Y, BB.Max.Y

        except Exception as e:
            print("Error calculating element bounds: {}".format(str(e)))
            return None

    def _set_view_crop_box(self, view, crop_region, elevation):
        """
        Set view crop box to specified region

        Args:
            view: View to modify
            crop_region: Dict with min_x, max_x, min_y, max_y
            elevation: Z elevation
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

    def get_floor_plan_view_type(self):
        """Get the Floor Plan view family type"""
        view_family_types = FilteredElementCollector(self.doc)\
            .OfClass(ViewFamilyType)\
            .ToElements()

        for vft in view_family_types:
            if vft.ViewFamily == ViewFamily.FloorPlan:
                return vft.Id

        # Fallback: return first available
        return view_family_types[0].Id

    def calculate_walls_bounding_box(self, elements, level):
        """
        Calculate bounding box that encompasses all walls
        Returns BoundingBoxXYZ for crop region
        """
        if not elements:
            return None

        # Initialize min/max coordinates
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')

        # Get level elevation
        level_elevation = level.Elevation

        # Collect all wall endpoints and expand bounds
        for wall in elements:
            try:
                # Get wall location curve
                location_curve = wall.Location
                if location_curve:
                    curve = location_curve.Curve

                    # Get start and end points
                    start_point = curve.GetEndPoint(0)
                    end_point = curve.GetEndPoint(1)

                    # Update bounds
                    min_x = min(min_x, start_point.X, end_point.X)
                    min_y = min(min_y, start_point.Y, end_point.Y)
                    max_x = max(max_x, start_point.X, end_point.X)
                    max_y = max(max_y, start_point.Y, end_point.Y)

                    # Also consider wall width
                    wall_width = wall.Width
                    buffer = wall_width / 2.0

                    min_x -= buffer
                    min_y -= buffer
                    max_x += buffer
                    max_y += buffer

            except Exception as e:
                print("Warning: Could not process wall {}: {}".format(
                    wall.Id, str(e)))
                continue

        # Add margin (3 feet = ~0.9m on each side)
        margin = 0.5
        min_x -= margin
        min_y -= margin
        max_x += margin
        max_y += margin

        # Create BoundingBoxXYZ
        bbox = BoundingBoxXYZ()
        bbox.Min = XYZ(min_x, min_y, level_elevation - 1.0)
        bbox.Max = XYZ(max_x, max_y, level_elevation + 10.0)

        try:
            from PrasKaaPyKit.tab.Documentation.panel.Section.pulldown.WallPlanGenerator.pushbutton.script import DEBUG_MODE
            if DEBUG_MODE:
                print("DEBUG: Calculated bounding box:")
                print("  Min: ({:.2f}, {:.2f}, {:.2f})".format(
                    bbox.Min.X, bbox.Min.Y, bbox.Min.Z))
                print("  Max: ({:.2f}, {:.2f}, {:.2f})".format(
                    bbox.Max.X, bbox.Max.Y, bbox.Max.Z))
        except:
            pass

        return bbox

    def create_only_plan_view_for_elements(self, elements, level, view_name_base, crop_region=True):
        """
        Create only a plan view for elements (no elevation/cross section)
        Based on Claude's solution using proper ViewPlan.Create()

        Args:
            elements: List of Revit elements
            level: Level object for the view
            view_name_base: Base name for the view (string)
            crop_region: Whether to set crop region

        Returns:
            ViewPlan or None: Created plan view
        """
        try:
            # Ensure unique view name
            unique_name = self.ensure_unique_view_name(view_name_base)

            # Get Floor Plan view type
            view_type_id = self.get_floor_plan_view_type()

            try:
                from PrasKaaPyKit.tab.Documentation.panel.Section.pulldown.WallPlanGenerator.pushbutton.script import DEBUG_MODE
                debug_enabled = DEBUG_MODE
            except:
                debug_enabled = False

            if debug_enabled:
                print("DEBUG: Creating plan view '{}' at level '{}'".format(
                    unique_name, level.Name))

            # Create the plan view using proper ViewPlan.Create()
            plan_view = ViewPlan.Create(self.doc, view_type_id, level.Id)
            plan_view.Name = unique_name
            plan_view.Scale = 50

            if debug_enabled:
                print("DEBUG: ViewPlan created successfully, Id: {}".format(
                    plan_view.Id))

            # Enable and set crop region
            if crop_region:
                # Calculate bounding box for walls
                bbox = self.calculate_walls_bounding_box(elements, level)

                if bbox:
                    # Enable crop box
                    plan_view.CropBoxActive = True
                    plan_view.CropBoxVisible = True

                    # Set crop region
                    plan_view.CropBox = bbox

                    if debug_enabled:
                        print("DEBUG: Crop region applied successfully")
                else:
                    if debug_enabled:
                        print("WARNING: Could not calculate bounding box")

            return plan_view

        except Exception as e:
            try:
                from PrasKaaPyKit.tab.Documentation.panel.Section.pulldown.WallPlanGenerator.pushbutton.script import DEBUG_MODE
                if DEBUG_MODE:
                    print("Error creating plan-only view for elements: {}".format(str(e)))
                    import traceback
                    print(traceback.format_exc())
            except:
                pass
            return None