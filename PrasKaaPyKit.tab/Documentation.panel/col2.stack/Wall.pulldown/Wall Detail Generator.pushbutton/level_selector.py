# -*- coding: utf-8 -*-
"""
Level Selector Module
Handles level selection and validation for Wall Plan Generator

Author: Generated from EF Element Sections Generator analysis
Version: 1.0.0
"""

from Autodesk.Revit.DB import *


class LevelSelector:
    """
    Handles level selection and validation for wall plan generation
    """

    def __init__(self, doc):
        """
        Initialize LevelSelector

        Args:
            doc: Revit Document
        """
        self.doc = doc

    def select_target_levels(self):
        """
        Present level selection dialog to user

        Returns:
            list: List of selected Level objects
        """
        from pyrevit import forms

        # Get all levels in document
        levels = FilteredElementCollector(self.doc).OfClass(Level).ToElements()

        if not levels:
            forms.alert("No levels found in document.", title="No Levels")
            return []

        # Create selection options with elevation info
        level_options = {}
        for level in levels:
            elevation_text = "{:.2f}'".format(level.Elevation * 3.28084)  # Convert to feet
            display_name = "{} ({})".format(level.Name, elevation_text)
            level_options[display_name] = level

        # Show multi-select dialog
        from GUI.forms import select_from_dict
        selected_items = select_from_dict(
            level_options,
            title="Select Target Levels",
            label="Choose levels where wall plan details should be created:",
            SelectMultiple=True
        )

        if not selected_items:
            return []

        # Debug: Show what we got back from select_from_dict
        try:
            from script import DEBUG_MODE
            if DEBUG_MODE:
                print("DEBUG level_selector: selected_items = {}".format(selected_items))
                print("DEBUG level_selector: selected_items type = {}".format(type(selected_items)))
                if selected_items:
                    print("DEBUG level_selector: first item type = {}".format(type(selected_items[0])))
        except:
            pass

        # Handle different return types from select_from_dict
        # It might return keys (display names) or values (Level objects) directly
        try:
            from script import DEBUG_MODE
            debug_enabled = DEBUG_MODE
        except:
            debug_enabled = False

        if selected_items and isinstance(selected_items[0], str):
            # select_from_dict returned display names (keys)
            if debug_enabled:
                print("DEBUG level_selector: select_from_dict returned display names (keys)")
            try:
                result = [level_options[name] for name in selected_items]
                if debug_enabled:
                    print("DEBUG level_selector: successfully converted {} names to {} level objects".format(len(selected_items), len(result)))
                return result
            except KeyError as e:
                if debug_enabled:
                    print("DEBUG level_selector: KeyError when converting names to levels")
                    print("DEBUG level_selector: Available keys in level_options: {}".format(list(level_options.keys())))
                    print("DEBUG level_selector: selected_items content: {}".format(selected_items))
                    print("DEBUG level_selector: Error key: {}".format(e))
                raise  # Re-raise the error
        else:
            # select_from_dict returned Level objects directly (values)
            if debug_enabled:
                print("DEBUG level_selector: select_from_dict returned Level objects directly (values)")
                print("DEBUG level_selector: returning selected_items as-is")
            return selected_items

    def validate_level_selection(self, selected_levels):
        """
        Validate selected levels

        Args:
            selected_levels: List of Level objects

        Returns:
            bool: True if valid, False otherwise
        """
        if not selected_levels:
            from pyrevit import forms
            forms.alert("No levels selected.", title="Selection Error")
            return False

        # Check for duplicate elevations (within tolerance)
        elevations = [level.Elevation for level in selected_levels]
        tolerance = 0.1  # 100mm tolerance

        for i, elev1 in enumerate(elevations):
            for j, elev2 in enumerate(elevations[i+1:], i+1):
                if abs(elev1 - elev2) < tolerance:
                    from pyrevit import forms
                    level1_name = selected_levels[i].Name
                    level2_name = selected_levels[j].Name
                    message = "Warning: Levels '{}' and '{}' have very similar elevations.\n\nContinue anyway?".format(level1_name, level2_name)
                    if not forms.alert(message, yes=True, no=True):
                        return False

        return True

    def get_levels_info(self, levels):
        """
        Get detailed information about levels

        Args:
            levels: List of Level objects

        Returns:
            list: List of dictionaries with level information
        """
        level_info = []

        for level in levels:
            info = {
                'name': level.Name,
                'elevation': level.Elevation,
                'elevation_feet': level.Elevation * 3.28084,  # Convert to feet
                'id': level.Id.IntegerValue
            }
            level_info.append(info)

        return level_info

    def find_level_by_elevation(self, elevation, tolerance=0.1):
        """
        Find level at specific elevation

        Args:
            elevation: Target elevation
            tolerance: Search tolerance (default 100mm)

        Returns:
            Level or None: Found level or None
        """
        levels = FilteredElementCollector(self.doc).OfClass(Level).ToElements()

        for level in levels:
            if abs(level.Elevation - elevation) < tolerance:
                return level

        return None

    def find_level_by_name(self, name):
        """
        Find level by name

        Args:
            name: Level name to search for

        Returns:
            Level or None: Found level or None
        """
        levels = FilteredElementCollector(self.doc).OfClass(Level).ToElements()

        for level in levels:
            if level.Name == name:
                return level

        return None

    def get_all_levels_sorted(self):
        """
        Get all levels sorted by elevation

        Returns:
            list: Sorted list of Level objects
        """
        levels = FilteredElementCollector(self.doc).OfClass(Level).ToElements()
        return sorted(levels, key=lambda l: l.Elevation)

    def create_level_at_elevation(self, elevation, name):
        """
        Create new level at specific elevation

        Args:
            elevation: Elevation for new level
            name: Name for new level

        Returns:
            Level: Created level object
        """
        # Ensure unique name
        unique_name = self._ensure_unique_level_name(name)

        # Create level
        new_level = Level.Create(self.doc, elevation)
        new_level.Name = unique_name

        return new_level

    def _ensure_unique_level_name(self, base_name):
        """
        Ensure level name is unique

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