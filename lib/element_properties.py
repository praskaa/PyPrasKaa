# -*- coding: utf-8 -*-
"""
Element Properties Library
Reusable element property extraction utilities

Author: Generated from EF Element Sections Generator analysis
Version: 1.0.0
"""

from Autodesk.Revit.DB import *


class ElementProperties:
    """
    Extract geometric and spatial properties from Revit elements
    Based on EF Element Sections Generator logic
    """

    def __init__(self, element, doc=None):
        """
        Initialize ElementProperties

        Args:
            element: Revit element to analyze
            doc: Revit document (optional, for type-based calculations)
        """
        self.element = element
        self.doc = doc

        # Properties to be calculated
        self.origin = None      # XYZ: Geometric center
        self.vector = None      # XYZ: Directional vector
        self.width = None       # float: Element width
        self.height = None      # float: Element height
        self.depth = None       # float: Element depth
        self.offset = 1.0       # float: Section offset
        self.depth_offset = 1.0 # float: Depth offset
        self.valid = False      # bool: Whether properties are valid

        # Calculate properties based on element type
        self._calculate_properties()

    def _calculate_properties(self):
        """Calculate properties based on element type"""
        try:
            if isinstance(self.element, Wall):
                self._get_wall_properties()
            else:
                self._get_generic_properties()
        except Exception as e:
            print("Error calculating element properties: {}".format(str(e)))
            self.valid = False

    def _get_wall_properties(self):
        """Extract properties specific to Wall elements"""
        try:
            wall_curve = self.element.Location.Curve
            if not wall_curve:
                return

            # Get wall endpoints
            pt_start = wall_curve.GetEndPoint(0)
            pt_end = wall_curve.GetEndPoint(1)

            # Calculate directional vector
            self.vector = pt_end - pt_start
            self.width = self.vector.GetLength()

            # Get wall height from parameter
            height_param = self.element.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)
            if height_param and height_param.HasValue:
                self.height = height_param.AsDouble()
            else:
                # Fallback to bounding box
                bb = self.element.get_BoundingBox(None)
                if bb:
                    self.height = bb.Max.Z - bb.Min.Z

            # Calculate origin from bounding box center
            bb = self.element.get_BoundingBox(None)
            if bb:
                self.origin = (bb.Max + bb.Min) / 2

            self.valid = True

        except Exception as e:
            print("Error getting wall properties: {}".format(str(e)))

    def _get_generic_properties(self):
        """Extract properties for generic elements"""
        try:
            if not self.doc:
                return

            # Get element type
            el_type = self.doc.GetElement(self.element.GetTypeId())
            if not el_type:
                return

            # Get bounding boxes
            bb = self.element.get_BoundingBox(None)
            bb_typ = el_type.get_BoundingBox(None)

            if not bb or not bb_typ:
                return

            # Get family and placement type
            el_fam = el_type.Family
            if not el_fam:
                return

            el_placement = el_fam.FamilyPlacementType
            fpt = FamilyPlacementType

            # Calculate based on placement type
            if el_placement in [fpt.OneLevelBased, fpt.TwoLevelsBased, fpt.WorkPlaneBased]:
                self._get_point_based_properties(bb, bb_typ)
            elif el_placement in [fpt.CurveBased, fpt.CurveDrivenStructural]:
                self._get_curve_based_properties(bb, bb_typ)
            elif el_placement == fpt.OneLevelBasedHosted:
                self._get_hosted_properties(bb, bb_typ)
            else:
                self._get_fallback_properties(bb, bb_typ)

        except Exception as e:
            print("Error getting generic properties: {}".format(str(e)))

    def _get_point_based_properties(self, bb, bb_typ):
        """Properties for point-based families"""
        try:
            # Origin from instance bounding box center
            self.origin = (bb.Max + bb.Min) / 2

            # Dimensions from type bounding box
            self.width = (bb_typ.Max.X - bb_typ.Min.X)
            self.height = (bb_typ.Max.Z - bb_typ.Min.Z)
            self.depth = (bb_typ.Max.Y - bb_typ.Min.Y)

            # Calculate directional vector from type geometry
            pt_start = XYZ(bb_typ.Min.X, (bb_typ.Min.Y + bb_typ.Max.Y) / 2, bb_typ.Min.Z)
            pt_end = XYZ(bb_typ.Max.X, (bb_typ.Min.Y + bb_typ.Max.Y) / 2, bb_typ.Min.Z)
            self.vector = pt_end - pt_start

            # Apply rotation if element is rotated
            try:
                rotation_rad = self.element.Location.Rotation
                from Snippets._vectors import rotate_vector
                self.vector = rotate_vector(self.vector, rotation_rad)
            except:
                pass  # No rotation or rotation not applicable

            self.valid = True

        except Exception as e:
            print("Error getting point-based properties: {}".format(str(e)))

    def _get_curve_based_properties(self, bb, bb_typ):
        """Properties for curve-based families"""
        try:
            # Get curve from location
            curve = self.element.Location.Curve
            if not curve:
                return

            # Origin from bounding box center
            self.origin = (bb.Max + bb.Min) / 2

            # Get curve endpoints
            pt_start = curve.GetEndPoint(0)
            pt_end = curve.GetEndPoint(1)

            # Normalize Z coordinates
            if pt_start.Z != pt_end.Z:
                pt_start = XYZ(pt_start.X, pt_start.Y, pt_start.Z)
                pt_end = XYZ(pt_end.X, pt_end.Y, pt_start.Z)

            # Calculate vector and dimensions
            self.vector = pt_end - pt_start
            self.width = self.vector.GetLength()
            self.height = (bb.Max.Z - bb.Min.Z)

            self.valid = True

        except Exception as e:
            print("Error getting curve-based properties: {}".format(str(e)))

    def _get_hosted_properties(self, bb, bb_typ):
        """Properties for hosted families"""
        try:
            host = self.element.Host
            if not host:
                return

            # Special handling for wall-hosted elements
            if isinstance(host, Wall):
                wall_curve = host.Location.Curve
                if wall_curve:
                    pt_start = wall_curve.GetEndPoint(0)
                    pt_end = wall_curve.GetEndPoint(1)
                    self.vector = pt_end - pt_start

                    # Handle facing orientation
                    try:
                        if self.element.FacingFlipped:
                            self.vector = -self.vector
                    except:
                        pass

            # Calculate dimensions from type
            self.width = (bb_typ.Max.X - bb_typ.Min.X)
            self.height = (bb_typ.Max.Z - bb_typ.Min.Z)
            self.origin = (bb.Max + bb.Min) / 2

            self.valid = True

        except Exception as e:
            print("Error getting hosted properties: {}".format(str(e)))

    def _get_fallback_properties(self, bb, bb_typ):
        """Fallback properties calculation"""
        try:
            # Basic properties from bounding boxes
            self.origin = (bb.Max + bb.Min) / 2
            self.width = (bb_typ.Max.X - bb_typ.Min.X)
            self.height = (bb_typ.Max.Z - bb_typ.Min.Z)
            self.depth = (bb_typ.Max.Y - bb_typ.Min.Y)

            # Default vector
            pt_start = XYZ(bb_typ.Min.X, (bb_typ.Min.Y + bb_typ.Max.Y) / 2, bb_typ.Min.Z)
            pt_end = XYZ(bb_typ.Max.X, (bb_typ.Min.Y + bb_typ.Max.Y) / 2, bb_typ.Min.Z)
            self.vector = pt_end - pt_start

            # Try to apply rotation
            try:
                rotation_rad = self.element.Location.Rotation
                from Snippets._vectors import rotate_vector
                self.vector = rotate_vector(self.vector, rotation_rad)
            except:
                pass

            self.valid = True

        except Exception as e:
            print("Error getting fallback properties: {}".format(str(e)))

    def get_bounding_box_2d(self, elevation=None):
        """
        Get 2D bounding box at specified elevation

        Args:
            elevation: Z coordinate (optional, uses element elevation if None)

        Returns:
            tuple or None: (min_x, max_x, min_y, max_y) or None
        """
        try:
            bb = self.element.get_BoundingBox(None)
            if not bb:
                return None

            return bb.Min.X, bb.Max.X, bb.Min.Y, bb.Max.Y

        except Exception as e:
            print("Error getting 2D bounding box: {}".format(str(e)))
            return None

    def get_mid_height_elevation(self):
        """
        Calculate mid-height elevation for the element

        Returns:
            float: Mid-height elevation
        """
        try:
            # Get base elevation
            base_elevation = self._get_base_elevation()

            # Get element height
            element_height = self.height or 0.0

            return base_elevation + (element_height / 2)

        except Exception as e:
            print("Error calculating mid-height elevation: {}".format(str(e)))
            return 0.0

    def _get_base_elevation(self):
        """Get base elevation of element"""
        try:
            # Try to get from level constraint
            if hasattr(self.element, 'LevelId') and self.element.LevelId != ElementId.InvalidElementId:
                level = self.doc.GetElement(self.element.LevelId)
                if level:
                    return level.Elevation

            # Fallback to bounding box
            bb = self.element.get_BoundingBox(None)
            if bb:
                return bb.Min.Z

            return 0.0

        except Exception as e:
            print("Error getting base elevation: {}".format(str(e)))
            return 0.0