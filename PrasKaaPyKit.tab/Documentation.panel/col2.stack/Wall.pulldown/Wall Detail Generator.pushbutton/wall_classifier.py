# -*- coding: utf-8 -*-
"""
Wall Classifier Module
Handles wall classification and grouping based on "Wall Scheme Classification" parameter

Author: Generated from EF Element Sections Generator analysis
Version: 1.0.0
"""

from collections import defaultdict
from Autodesk.Revit.DB import StorageType
# Local parameter extraction function (supports both instance and type parameters)
def extract_parameter_by_name(element, param_name, search_type_level=False):
    """
    Extract parameter value by name with support for shared parameters

    Args:
        element: Revit element
        param_name: Parameter name to extract
        search_type_level: Also search in element type/family

    Returns:
        Parameter value or None
    """
    try:
        # First try instance parameter
        param = element.LookupParameter(param_name)
        if param and param.HasValue:
            return get_parameter_value(param)

        # If not found and type level search requested, try element type
        if search_type_level and hasattr(element, 'GetTypeId'):
            try:
                element_type = element.Document.GetElement(element.GetTypeId())
                if element_type:
                    type_param = element_type.LookupParameter(param_name)
                    if type_param and type_param.HasValue:
                        return get_parameter_value(type_param)
            except:
                pass

        return None
    except:
        return None

def get_parameter_value(parameter):
    """
    Extract parameter value based on storage type

    Args:
        parameter: Revit Parameter object

    Returns:
        Value in appropriate Python type
    """
    if not parameter or not parameter.HasValue:
        return None

    storage_type = parameter.StorageType

    try:
        if storage_type == StorageType.Double:
            return parameter.AsDouble()
        elif storage_type == StorageType.Integer:
            return parameter.AsInteger()
        elif storage_type == StorageType.String:
            value = parameter.AsString()
            # Debug: Show raw string value only in debug mode
            try:
                from script import DEBUG_MODE
                if DEBUG_MODE:
                    print("DEBUG get_parameter_value: Raw string value = '{}'".format(repr(value)))
            except:
                pass
            return value.strip() if value else None
        elif storage_type == StorageType.ElementId:
            return parameter.AsElementId()
        else:
            return None
    except Exception as e:
        # Debug: Show exception only in debug mode
        try:
            from script import DEBUG_MODE
            if DEBUG_MODE:
                print("DEBUG get_parameter_value: Exception = {}".format(str(e)))
        except:
            pass
        return None


class WallClassifier:
    """
    Handles wall classification and grouping logic for Wall Plan Generator
    """

    def __init__(self, walls):
        """
        Initialize WallClassifier with wall elements

        Args:
            walls: List of Revit Wall elements
        """
        self.walls = walls
        self.classification_param = "Wall scheme classification"
        self.classified_walls = {}
        self.unclassified_walls = []

    def classify_walls(self):
        """
        Group walls by classification parameter value

        Returns:
            dict: Dictionary with classification as key and list of walls as value
        """
        groups = defaultdict(list)

        for wall in self.walls:
            classification = self._get_wall_classification(wall)

            if classification:
                groups[classification].append(wall)
            else:
                self.unclassified_walls.append(wall)

        self.classified_walls = dict(groups)
        return self.classified_walls

    def validate_classifications(self):
        """
        Validate that walls have valid classifications

        Returns:
            tuple: (is_valid, unclassified_walls)
                is_valid: Boolean indicating if all walls are classified
                unclassified_walls: List of walls without classification
        """
        self.unclassified_walls = []

        for wall in self.walls:
            if not self._get_wall_classification(wall):
                self.unclassified_walls.append(wall)

        is_valid = len(self.unclassified_walls) == 0
        return is_valid, self.unclassified_walls

    def get_classification_summary(self):
        """
        Get summary of wall classifications

        Returns:
            dict: Summary statistics
        """
        if not self.classified_walls:
            self.classify_walls()

        return {
            'total_walls': len(self.walls),
            'classified_walls': sum(len(walls) for walls in self.classified_walls.values()),
            'unclassified_walls': len(self.unclassified_walls),
            'classifications': list(self.classified_walls.keys()),
            'classification_counts': {k: len(v) for k, v in self.classified_walls.items()}
        }

    def _get_wall_classification(self, wall):
        """
        Extract classification parameter from wall (supports shared parameters)
        Uses definitive extraction approach with detailed debugging

        Args:
            wall: Revit Wall element

        Returns:
            str or None: Classification value or None if not found
        """
        try:
            # Debug: Show wall basic info
            self._debug_wall_info(wall, "=== STARTING CLASSIFICATION EXTRACTION ===")

            # Try instance parameter first (most common for shared parameters)
            self._debug_wall_info(wall, "Step 1: Checking instance parameter")
            param = wall.LookupParameter(self.classification_param)
            if param:
                self._debug_wall_info(wall, "Instance parameter found: HasValue={}, StorageType={}".format(param.HasValue, param.StorageType))
                if param.HasValue:
                    classification = get_parameter_value(param)
                    self._debug_wall_info(wall, "Instance parameter RAW value: '{}' (type: {})".format(repr(classification), type(classification)))
                else:
                    classification = None
                    self._debug_wall_info(wall, "Instance parameter has no value")
            else:
                classification = None
                self._debug_wall_info(wall, "Instance parameter not found")

            # If not found in instance, try type parameter
            if classification is None:
                self._debug_wall_info(wall, "Step 2: Checking type parameter (instance was None)")
                wall_type = wall.Document.GetElement(wall.GetTypeId())
                if wall_type:
                    self._debug_wall_info(wall, "Wall type found: {}".format(getattr(wall_type, 'Name', 'No Name Attr')))
                    type_param = wall_type.LookupParameter(self.classification_param)
                    if type_param:
                        self._debug_wall_info(wall, "Type parameter found: HasValue={}, StorageType={}".format(type_param.HasValue, type_param.StorageType))
                        if type_param.HasValue:
                            classification = get_parameter_value(type_param)
                            self._debug_wall_info(wall, "Type parameter RAW value: '{}' (type: {})".format(repr(classification), type(classification)))
                        else:
                            self._debug_wall_info(wall, "Type parameter has no value")
                    else:
                        self._debug_wall_info(wall, "Type parameter not found")
                else:
                    self._debug_wall_info(wall, "Wall type not found")

            # Final processing
            self._debug_wall_info(wall, "Step 3: Final processing - Raw classification: '{}' (type: {})".format(repr(classification), type(classification)))

            # Return None for empty strings
            if classification is None:
                self._debug_wall_info(wall, "Classification is None - returning None")
                return None

            if isinstance(classification, str):
                original = classification
                classification = classification.strip()
                self._debug_wall_info(wall, "String processing: '{}' -> '{}' after strip".format(original, classification))

                if classification:
                    self._debug_wall_info(wall, "Returning valid classification: '{}'".format(classification))
                    return classification
                else:
                    self._debug_wall_info(wall, "Empty string after strip - returning None")
                    return None
            else:
                self._debug_wall_info(wall, "Classification is not string (type: {}) - returning as-is: {}".format(type(classification), repr(classification)))
                return classification

        except Exception as e:
            self._debug_wall_info(wall, "CRITICAL ERROR: {}".format(str(e)))
            import traceback
            self._debug_wall_info(wall, "Traceback: {}".format(traceback.format_exc()))
            return None

    def _debug_wall_info(self, wall, message):
        """
        Debug helper for wall parameter extraction

        Args:
            wall: Wall element
            message: Debug message
        """
        # Only print debug info if DEBUG_MODE is True (from main script)
        try:
            # Import DEBUG_MODE from main script
            from script import DEBUG_MODE
            if DEBUG_MODE:
                wall_type = wall.Document.GetElement(wall.GetTypeId())
                type_name = getattr(wall_type, 'Name', 'No Name') if wall_type else "Unknown"
                print("[WALL_DEBUG] ID:{} Type:'{}' - {}".format(wall.Id, type_name, message))
        except Exception as e:
            # Fallback: only print critical errors
            try:
                from script import DEBUG_MODE
                if DEBUG_MODE:
                    print("[WALL_DEBUG] ID:{} - Error in debug: {} - {}".format(wall.Id, str(e), message))
            except:
                # If import fails, don't print anything
                pass

    def get_walls_by_classification(self, classification):
        """
        Get all walls with specific classification

        Args:
            classification: Classification value to filter by

        Returns:
            list: List of walls with matching classification
        """
        if not self.classified_walls:
            self.classify_walls()

        return self.classified_walls.get(classification, [])

    def get_unique_classifications(self):
        """
        Get list of unique classification values

        Returns:
            list: Sorted list of unique classifications
        """
        if not self.classified_walls:
            self.classify_walls()

        return sorted(self.classified_walls.keys())