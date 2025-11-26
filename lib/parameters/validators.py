# -*- coding: utf-8 -*-
"""
Advanced validation system for parameter setting operations.
"""

import re
try:
    from .exceptions import ValidationError
except ImportError:
    # Mock for testing
    class ValidationError(Exception):
        pass

# Mock Revit API for standalone testing
try:
    from Autodesk.Revit.DB import StorageType, ElementId
except ImportError:
    class MockStorageType:
        Double = "Double"
        Integer = "Integer"
        String = "String"
        ElementId = "ElementId"
    StorageType = MockStorageType()

    class MockElementId:
        def __init__(self, val):
            pass
        @staticmethod
        def InvalidElementId():
            return -1
    ElementId = MockElementId

class ParameterValidator:
    """Advanced parameter validation system."""

    # Common parameter name patterns
    PARAMETER_PATTERNS = {
        'length': re.compile(r'.*(length|height|width|depth|size|diameter|radius).*', re.IGNORECASE),
        'area': re.compile(r'.*(area|surface).*', re.IGNORECASE),
        'volume': re.compile(r'.*(volume).*', re.IGNORECASE),
        'angle': re.compile(r'.*(angle|rotation|tilt).*', re.IGNORECASE),
        'count': re.compile(r'.*(count|number|quantity|qty).*', re.IGNORECASE),
        'boolean': re.compile(r'.*(yes|no|true|false|on|off).*', re.IGNORECASE),
        'percentage': re.compile(r'.*(percent|percentage|ratio).*', re.IGNORECASE),
        'material': re.compile(r'.*(material|finish|color).*', re.IGNORECASE),
        'text': re.compile(r'.*(name|description|comment|note|label|tag).*', re.IGNORECASE),
    }

    # Unit conversion patterns
    UNIT_PATTERNS = {
        'length': {
            'mm': 1/304.8,      # mm to feet
            'cm': 1/30.48,      # cm to feet
            'm': 3.28084,       # m to feet
            'in': 1/12,         # inches to feet
            'ft': 1,            # feet
            "'": 1,             # feet (apostrophe)
            '"': 1/12,          # inches (quote)
        },
        'area': {
            'mm²': (1/304.8)**2,
            'cm²': (1/30.48)**2,
            'm²': 3.28084**2,
            'ft²': 1,
            'in²': (1/12)**2,
        },
        'volume': {
            'mm³': (1/304.8)**3,
            'cm³': (1/30.48)**3,
            'm³': 3.28084**3,
            'ft³': 1,
            'in³': (1/12)**3,
            'l': 0.0353147,    # liters to cubic feet
            'ml': 3.53147e-5,   # ml to cubic feet
        }
    }

    def __init__(self, logger=None):
        self.logger = logger

    def validate_parameter_value(self, param_name, value, storage_type, **kwargs):
        """
        Comprehensive parameter value validation.

        Args:
            param_name: Parameter name
            value: Value to validate
            storage_type: Revit StorageType
            **kwargs: Additional validation options

        Returns:
            tuple: (is_valid, normalized_value, warnings)
        """
        warnings = []

        # Basic type validation
        if storage_type == StorageType.Double:
            return self._validate_double_value(param_name, value, **kwargs)
        elif storage_type == StorageType.Integer:
            return self._validate_integer_value(param_name, value, **kwargs)
        elif storage_type == StorageType.String:
            return self._validate_string_value(param_name, value, **kwargs)
        elif storage_type == StorageType.ElementId:
            return self._validate_element_id_value(param_name, value, **kwargs)
        else:
            return False, None, ["Unsupported storage type"]

    def _validate_double_value(self, param_name, value, **kwargs):
        """Validate double (numeric) parameter values."""
        try:
            # Handle string inputs with units
            if isinstance(value, str):
                numeric_value, unit_warnings = self._parse_numeric_with_unit(value, param_name)
                warnings = unit_warnings
                value = numeric_value
            else:
                value = float(value)

            # Range validation
            min_val = kwargs.get('min_value')
            max_val = kwargs.get('max_value')

            if min_val is not None and value < min_val:
                return False, None, ["Value {} is below minimum {}".format(value, min_val)]
            if max_val is not None and value > max_val:
                return False, None, ["Value {} is above maximum {}".format(value, max_val)]

            # Special validations based on parameter name
            param_type = self._classify_parameter_type(param_name)
            if param_type == 'percentage' and not (0 <= value <= 1):
                warnings.append("Percentage values should typically be between 0 and 1")
            elif param_type == 'angle' and not (-360 <= value <= 360):
                warnings.append("Angle values should typically be between -360° and 360°")

            return True, value, warnings

        except (ValueError, TypeError) as e:
            return False, None, ["Invalid numeric value: {}".format(str(e))]

    def _validate_integer_value(self, param_name, value, **kwargs):
        """Validate integer parameter values."""
        try:
            if isinstance(value, str):
                # Handle boolean-like strings
                lower_val = value.lower().strip()
                if lower_val in ('true', 'yes', 'on', '1'):
                    value = 1
                elif lower_val in ('false', 'no', 'off', '0'):
                    value = 0
                else:
                    value = int(float(value))  # Allow decimal strings
            else:
                value = int(value)

            # Range validation
            min_val = kwargs.get('min_value')
            max_val = kwargs.get('max_value')

            if min_val is not None and value < min_val:
                return False, None, ["Value {} is below minimum {}".format(value, min_val)]
            if max_val is not None and value > max_val:
                return False, None, ["Value {} is above maximum {}".format(value, max_val)]

            return True, value, []

        except (ValueError, TypeError) as e:
            return False, None, ["Invalid integer value: {}".format(str(e))]

    def _validate_string_value(self, param_name, value, **kwargs):
        """Validate string parameter values."""
        try:
            value = str(value)

            # Length validation
            max_length = kwargs.get('max_length', 256)  # Default Revit limit
            if len(value) > max_length:
                return False, None, ["String length {} exceeds maximum {}".format(len(value), max_length)]

            # Pattern validation
            pattern = kwargs.get('pattern')
            if pattern and not re.match(pattern, value):
                return False, None, ["String does not match required pattern"]

            return True, value, []

        except Exception as e:
            return False, None, ["Invalid string value: {}".format(str(e))]

    def _validate_element_id_value(self, param_name, value, **kwargs):
        """Validate ElementId parameter values."""
        # ElementId validation is complex and typically handled by Revit
        # We mainly check if it's a valid identifier
        try:
            if isinstance(value, ElementId):
                return True, value, []
            elif isinstance(value, int):
                return True, ElementId(value), []
            elif isinstance(value, str):
                if value.lower() in ('none', 'null', ''):
                    return True, ElementId.InvalidElementId, []
                else:
                    return False, None, ["ElementId must be an integer or ElementId object"]
            else:
                return False, None, ["Invalid ElementId value type"]
        except Exception as e:
            return False, None, ["Invalid ElementId value: {}".format(str(e))]

    def _parse_numeric_with_unit(self, value_str, param_name):
        """Parse numeric values with units."""
        value_str = value_str.strip()
        warnings = []

        # Extract numeric part and unit
        match = re.match(r'^([+-]?\d*\.?\d+)\s*([a-zA-Z\'"]*)$', value_str)
        if not match:
            raise ValueError("Cannot parse numeric value with unit: {}".format(value_str))

        numeric_str, unit = match.groups()
        numeric_value = float(numeric_str)

        # Classify parameter type for unit conversion
        param_type = self._classify_parameter_type(param_name)

        # Apply unit conversion if applicable
        if unit and param_type in self.UNIT_PATTERNS:
            unit_lower = unit.lower()
            if unit_lower in self.UNIT_PATTERNS[param_type]:
                conversion_factor = self.UNIT_PATTERNS[param_type][unit_lower]
                numeric_value *= conversion_factor
                if conversion_factor != 1:
                    warnings.append("Converted {} {} to {:.6f} feet".format(numeric_str, unit, numeric_value))
            else:
                warnings.append("Unknown unit '{}' for {} parameter".format(unit, param_type))

        return numeric_value, warnings

    def _classify_parameter_type(self, param_name):
        """Classify parameter type based on name patterns."""
        for param_type, pattern in self.PARAMETER_PATTERNS.items():
            if pattern.match(param_name):
                return param_type
        return 'unknown'

    def validate_element_parameter(self, element, param_name, **kwargs):
        """
        Validate that parameter exists and is settable on element.

        Args:
            element: Revit element
            param_name: Parameter name
            **kwargs: Validation options

        Returns:
            tuple: (is_valid, parameter, warnings)
        """
        warnings = []

        # Find parameter
        param = element.LookupParameter(param_name)
        if not param:
            # Check type parameters for instances
            if hasattr(element, 'GetTypeId'):
                elem_type = element.Document.GetElement(element.GetTypeId())
                if elem_type:
                    param = elem_type.LookupParameter(param_name)
                    if param:
                        warnings.append("Parameter found on element type, not instance")

        if not param:
            return False, None, ["Parameter '{}' not found on element".format(param_name)]

        # Check if parameter is read-only
        if param.IsReadOnly:
            return False, None, ["Parameter '{}' is read-only".format(param_name)]

        # Check if parameter has value (for validation)
        if not param.HasValue and kwargs.get('require_existing_value', False):
            warnings.append("Parameter '{}' has no existing value".format(param_name))

        return True, param, warnings