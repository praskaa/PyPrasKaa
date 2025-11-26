# -*- coding: utf-8 -*-
"""
Section Generator Library
Wrapper for EF SectionGenerator with reusable interface

Author: Generated from EF Element Sections Generator analysis
Version: 1.0.0
"""

from Autodesk.Revit.DB import *


class SectionGeneratorWrapper:
    """
    Wrapper for EF SectionGenerator to provide reusable interface
    """

    def __init__(self, doc):
        """
        Initialize SectionGeneratorWrapper

        Args:
            doc: Revit Document
        """
        self.doc = doc

    def create_plan_view(self, origin, vector, width, height, view_name_base, **kwargs):
        """
        Create a plan view using EF SectionGenerator

        Args:
            origin: XYZ origin point
            vector: XYZ directional vector
            width: float view width
            height: float view height
            view_name_base: str base name for view
            **kwargs: Additional parameters (offset, depth, depth_offset)

        Returns:
            ViewPlan or None: Created plan view
        """
        try:
            # Extract parameters with defaults
            offset = kwargs.get('offset', 1.0)
            depth = kwargs.get('depth', 1.0)
            depth_offset = kwargs.get('depth_offset', 1.0)

            # Import EF SectionGenerator
            from Snippets._views import SectionGenerator

            # Create generator
            gen = SectionGenerator(self.doc,
                                 origin=origin,
                                 vector=vector,
                                 width=width,
                                 height=height,
                                 offset=offset,
                                 depth=depth,
                                 depth_offset=depth_offset)

            # Generate views and return plan
            elev, cross, plan = gen.create_sections(view_name_base=view_name_base)

            return plan

        except Exception as e:
            print("Error creating plan view: {}".format(str(e)))
            return None

    def create_elevation_view(self, origin, vector, width, height, view_name_base, **kwargs):
        """
        Create an elevation view using EF SectionGenerator

        Args:
            origin: XYZ origin point
            vector: XYZ directional vector
            width: float view width
            height: float view height
            view_name_base: str base name for view
            **kwargs: Additional parameters

        Returns:
            ViewSection or None: Created elevation view
        """
        try:
            offset = kwargs.get('offset', 1.0)
            depth = kwargs.get('depth', 1.0)
            depth_offset = kwargs.get('depth_offset', 1.0)

            from Snippets._views import SectionGenerator

            gen = SectionGenerator(self.doc,
                                 origin=origin,
                                 vector=vector,
                                 width=width,
                                 height=height,
                                 offset=offset,
                                 depth=depth,
                                 depth_offset=depth_offset)

            # Generate views and return elevation
            elev, cross, plan = gen.create_sections(view_name_base=view_name_base)

            return elev

        except Exception as e:
            print("Error creating elevation view: {}".format(str(e)))
            return None

    def create_cross_section_view(self, origin, vector, width, height, view_name_base, **kwargs):
        """
        Create a cross section view using EF SectionGenerator

        Args:
            origin: XYZ origin point
            vector: XYZ directional vector
            width: float view width
            height: float view height
            view_name_base: str base name for view
            **kwargs: Additional parameters

        Returns:
            ViewSection or None: Created cross section view
        """
        try:
            offset = kwargs.get('offset', 1.0)
            depth = kwargs.get('depth', 1.0)
            depth_offset = kwargs.get('depth_offset', 1.0)

            from Snippets._views import SectionGenerator

            gen = SectionGenerator(self.doc,
                                 origin=origin,
                                 vector=vector,
                                 width=width,
                                 height=height,
                                 offset=offset,
                                 depth=depth,
                                 depth_offset=depth_offset)

            # Generate views and return cross section
            elev, cross, plan = gen.create_sections(view_name_base=view_name_base)

            return cross

        except Exception as e:
            print("Error creating cross section view: {}".format(str(e)))
            return None

    def create_all_views(self, origin, vector, width, height, view_name_base, **kwargs):
        """
        Create all three views (elevation, cross section, plan) at once

        Args:
            origin: XYZ origin point
            vector: XYZ directional vector
            width: float view width
            height: float view height
            view_name_base: str base name for views
            **kwargs: Additional parameters

        Returns:
            tuple: (elevation_view, cross_section_view, plan_view)
        """
        try:
            offset = kwargs.get('offset', 1.0)
            depth = kwargs.get('depth', 1.0)
            depth_offset = kwargs.get('depth_offset', 1.0)

            from Snippets._views import SectionGenerator

            gen = SectionGenerator(self.doc,
                                 origin=origin,
                                 vector=vector,
                                 width=width,
                                 height=height,
                                 offset=offset,
                                 depth=depth,
                                 depth_offset=depth_offset)

            # Generate all views
            elev, cross, plan = gen.create_sections(view_name_base=view_name_base)

            return elev, cross, plan

        except Exception as e:
            print("Error creating views: {}".format(str(e)))
            return None, None, None