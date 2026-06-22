"""
Unit conversion utilities for Revit parameter mapping.

This module provides conversion functions for different unit types
used in steel profile CSV files to Revit internal units.
"""

class UnitConverter:
    """Handles unit conversions for different parameter types."""

    def parse_parameter_key(self, parameter_key):
        """
        Parses a parameter key string like "UNIT_TYPE:param_name" into its components.
        
        Args:
            parameter_key (str): The parameter key string.
            
        Returns:
            tuple: (unit_type, param_name)
        """
        if ':' in parameter_key:
            parts = parameter_key.split(':', 1)
            return parts[0].upper(), parts[1]
        return 'NONE', parameter_key

    def get_unit_label(self, unit_type):
        """Gets a display label for a given unit type."""
        labels = {
            'LENGTH': 'mm',
            'WEIGHT': 'kg/m',
            'AREA': 'cm2',
            'MOMENT': 'cm3',
            'MODULUS': 'cm4',
            'NONE': ''
        }
        return labels.get(unit_type, '')
    
    # Conversion factors to Revit internal units (mm, kg, mm2, mm3, mm4)
    CONVERSION_FACTORS = {
        'LENGTH': {
            'mm': 1.0,
            'cm': 10.0,
            'm': 1000.0,
            'in': 25.4,
            'ft': 304.8
        },
        'WEIGHT': {
            'kg/m': 1.0,
            'lb/ft': 1.48816
        },
        'AREA': {
            'mm2': 1.0,
            'cm2': 100.0,
            'm2': 1000000.0,
            'in2': 645.16,
            'ft2': 92903.0
        },
        'MOMENT': {
            'mm3': 1.0,
            'cm3': 1000.0,
            'm3': 1000000000.0,
            'in3': 16387.1
        },
        'MODULUS': {
            'mm4': 1.0,
            'cm4': 10000.0,
            'm4': 1000000000000.0,
            'in4': 416231.0
        }
    }
    
    @staticmethod
    def convert_value(value, unit_type, from_unit='mm', to_unit='feet'):
        """
        Convert a value from one unit to another for Revit family parameters.
        Revit family parameters expect values in feet for LENGTH type.
        
        Args:
            value (float): The value to convert
            unit_type (str): Type of unit (LENGTH, WEIGHT, AREA, MOMENT, MODULUS)
            from_unit (str): Source unit (default: mm)
            to_unit (str): Target unit (default: feet for Revit)
            
        Returns:
            float: Converted value in appropriate units for Revit
        """
        # For LENGTH parameters, convert mm to feet (Revit internal unit)
        if unit_type == 'LENGTH':
            return value / 304.8  # Convert mm to feet
        
        # For other parameter types, return original value
        return value
    
    @staticmethod
    def get_unit_type_from_prefix(prefix):
        """Get unit type from parameter prefix."""
        prefix_map = {
            'LENGTH:': 'LENGTH',
            'WEIGHT:': 'WEIGHT',
            'AREA:': 'AREA',
            'MOMENT:': 'MOMENT',
            'MODULUS:': 'MODULUS'
        }
        return prefix_map.get(prefix.upper(), 'LENGTH')
    
    @staticmethod
    def extract_prefix_and_name(parameter_name):
        """Extract prefix and actual parameter name."""
        prefixes = ['LENGTH:', 'WEIGHT:', 'AREA:', 'MOMENT:', 'MODULUS:']
        
        for prefix in prefixes:
            if parameter_name.upper().startswith(prefix):
                actual_name = parameter_name[len(prefix):].strip()
                unit_type = UnitConverter.get_unit_type_from_prefix(prefix)
                return prefix.strip(':'), actual_name, unit_type
                
        return None, parameter_name, 'LENGTH'