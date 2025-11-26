# -*- coding: utf-8 -*-
"""
Family Manager
This module encapsulates the logic for interacting with the Revit Family API.
It handles creation of family types and setting their parameters.
"""

from pyrevit import revit, DB
from pyrevit import script

# Conversion factor from mm to feet
MM_TO_FEET_CONVERSION = 304.8

class FamilyManager:
    """
    Manages operations within a Revit family document.
    """
    def __init__(self, doc):
        """
        Initializes the FamilyManager.
        
        Args:
            doc (Revit Document): The active family document.
        """
        if not doc.IsFamilyDocument:
            raise TypeError("This class requires a family document.")
        self.doc = doc
        self.family_mgr = doc.FamilyManager
        self.results = []

    def process_profiles(self, profiles_data, config):
        """
        Processes a list of profile data to create or update family types.
        
        Args:
            profiles_data (list[dict]): A list of dictionaries, each representing a profile.
            config (dict): The configuration for the current profile type.
            
        Returns:
            list[str]: A list of log messages detailing the results.
        """
        self.results = []
        with revit.Transaction("Create/Update Family Types"):
            for profile in profiles_data:
                self._process_single_profile(profile, config)
        
        return self.results

    def _process_single_profile(self, profile_data, config):
        """Processes a single profile to create a family type."""
        type_name = profile_data.get('Name')
        if not type_name:
            self.results.append("SKIPPED: Profile data is missing a 'Name'.")
            return

        if any(t.Name == type_name for t in self.family_mgr.Types):
            self.results.append("INFO: Type '{}' already exists. Skipping.".format(type_name))
            return

        try:
            new_type = self.family_mgr.NewType(type_name)
            if not new_type:
                self.results.append("ERROR: Failed to create type '{}'.".format(type_name))
                return

            self.family_mgr.CurrentType = new_type
            
            errors = []
            for csv_header, value_str in profile_data.items():
                if csv_header == 'Name' or not value_str.strip():
                    continue

                param_map = config['parameter_mapping'].get(csv_header)
                if not param_map:
                    continue

                param_name = param_map['revit_param']
                param = self.family_mgr.get_Parameter(param_name)

                if param:
                    error = self._set_parameter_value(param, value_str, param_map)
                    if error:
                        errors.append(error)
                else:
                    errors.append("Parameter '{}' not found".format(param_name))

            if errors:
                self.results.append("WARNING: Type '{}' created with issues: {}".format(type_name, "; ".join(errors)))
            else:
                self.results.append("SUCCESS: Created and configured type '{}'.".format(type_name))

        except Exception as e:
            self.results.append("ERROR processing type '{}': {}".format(type_name, str(e)))

    def _set_parameter_value(self, param, value_str, param_map):
        """
        Sets a parameter's value, handling type and unit conversion.
        Returns an error message string on failure, otherwise None.
        """
        try:
            value = float(value_str)

            if param_map.get('unit_conversion'):
                value_to_set = value / MM_TO_FEET_CONVERSION
            else:
                value_to_set = value

            if param.IsReadOnly:
                return "Parameter '{}' is read-only".format(param.Definition.Name)

            self.family_mgr.Set(param, value_to_set)
            return None

        except ValueError:
            return "Invalid number format for '{}' on param '{}'".format(value_str, param.Definition.Name)
        except Exception as e:
            return "Error setting param '{}': {}".format(param.Definition.Name, str(e))