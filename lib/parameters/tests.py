# -*- coding: utf-8 -*-
"""
Comprehensive test suite for the Parameter Setting Framework.
"""

import unittest
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Mock Revit API classes for testing
class MockStorageType:
    Double = "Double"
    Integer = "Integer"
    String = "String"
    ElementId = "ElementId"

class MockElementId:
    def __init__(self, value):
        self.IntegerValue = value
        self.value = value

    @staticmethod
    def InvalidElementId():
        return MockElementId(-1)

class MockParameter:
    def __init__(self, name, storage_type, value=None, has_value=True, is_readonly=False):
        self.Definition = Mock()
        self.Definition.Name = name
        self.StorageType = storage_type
        self._value = value
        self._has_value = has_value
        self.IsReadOnly = is_readonly

    def HasValue(self):
        return self._has_value

    def AsDouble(self):
        return float(self._value) if self._value is not None else 0.0

    def AsInteger(self):
        return int(self._value) if self._value is not None else 0

    def AsString(self):
        return str(self._value) if self._value is not None else ""

    def AsElementId(self):
        return MockElementId(self._value) if self._value is not None else MockElementId.InvalidElementId()

    def Set(self, value):
        self._value = value
        return True

class MockElement:
    def __init__(self, element_id=1, name="Test Element"):
        self.Id = MockElementId(element_id)
        self.Name = name
        self._parameters = {}

    def LookupParameter(self, name):
        return self._parameters.get(name)

    def add_parameter(self, param):
        self._parameters[param.Definition.Name] = param

class MockDocument:
    def __init__(self):
        self.elements = {}

    def GetElement(self, element_id):
        return self.elements.get(element_id.IntegerValue)

class MockTransaction:
    def __init__(self, doc, name):
        self.doc = doc
        self.name = name
        self.started = False
        self.committed = False
        self.rolled_back = False

    def Start(self):
        self.started = True

    def Commit(self):
        self.committed = True

    def RollBack(self):
        self.rolled_back = True

    def HasStarted(self):
        return self.started

    def GetStatus(self):
        if self.committed:
            return "Committed"
        elif self.rolled_back:
            return "RolledBack"
        elif self.started:
            return "Started"
        else:
            return "NotStarted"

# Mock clr module and Revit API before importing framework
with patch.dict('sys.modules', {
    'clr': Mock(),
    'Autodesk.Revit.DB': Mock(),
    'Autodesk.Revit.DB.StorageType': MockStorageType,
    'Autodesk.Revit.DB.ElementId': MockElementId,
    'Autodesk.Revit.DB.Transaction': MockTransaction,
}):
    # Import framework components after mocks
    from .exceptions import ValidationError, ParameterSettingError
    from .validators import ParameterValidator
    from .strategies import BasicParameterStrategy, OptimizedParameterStrategy
    from .framework import ParameterSettingFramework, OptimizationLevel

class TestParameterValidator(unittest.TestCase):
    """Test cases for ParameterValidator."""

    def setUp(self):
        self.validator = ParameterValidator()

    def test_validate_double_value(self):
        # Test basic double validation
        is_valid, value, warnings = self.validator.validate_parameter_value(
            "Length", 10.5, MockStorageType.Double
        )
        self.assertTrue(is_valid)
        self.assertEqual(value, 10.5)
        self.assertEqual(len(warnings), 0)

    def test_validate_double_with_units(self):
        # Test unit conversion
        is_valid, value, warnings = self.validator.validate_parameter_value(
            "Length", "1000 mm", MockStorageType.Double
        )
        self.assertTrue(is_valid)
        self.assertAlmostEqual(value, 1000/304.8, places=5)  # mm to feet
        self.assertTrue(len(warnings) > 0)  # Should have conversion warning

    def test_validate_integer_value(self):
        is_valid, value, warnings = self.validator.validate_parameter_value(
            "Count", "5", MockStorageType.Integer
        )
        self.assertTrue(is_valid)
        self.assertEqual(value, 5)
        self.assertEqual(len(warnings), 0)

    def test_validate_string_value(self):
        is_valid, value, warnings = self.validator.validate_parameter_value(
            "Name", "Test Name", MockStorageType.String
        )
        self.assertTrue(is_valid)
        self.assertEqual(value, "Test Name")
        self.assertEqual(len(warnings), 0)

    def test_validate_string_too_long(self):
        long_string = "A" * 300
        is_valid, value, warnings = self.validator.validate_parameter_value(
            "Description", long_string, MockStorageType.String
        )
        self.assertFalse(is_valid)
        self.assertIn("exceeds maximum", warnings[0])

    def test_classify_parameter_type(self):
        self.assertEqual(self.validator._classify_parameter_type("Length"), "length")
        self.assertEqual(self.validator._classify_parameter_type("Area"), "area")
        self.assertEqual(self.validator._classify_parameter_type("Volume"), "volume")
        self.assertEqual(self.validator._classify_parameter_type("Angle"), "angle")
        self.assertEqual(self.validator._classify_parameter_type("Count"), "count")
        self.assertEqual(self.validator._classify_parameter_type("Material"), "material")
        self.assertEqual(self.validator._classify_parameter_type("Unknown"), "unknown")

class TestBasicParameterStrategy(unittest.TestCase):
    """Test cases for BasicParameterStrategy."""

    def setUp(self):
        self.doc = MockDocument()
        self.strategy = BasicParameterStrategy(self.doc)

    def test_set_double_parameter(self):
        element = MockElement()
        param = MockParameter("Length", MockStorageType.Double, 0.0)
        element.add_parameter(param)

        result = self.strategy.set_parameter(element, "Length", 10.5)
        self.assertTrue(result)
        self.assertEqual(param._value, 10.5)

    def test_set_integer_parameter(self):
        element = MockElement()
        param = MockParameter("Count", MockStorageType.Integer, 0)
        element.add_parameter(param)

        result = self.strategy.set_parameter(element, "Count", 5)
        self.assertTrue(result)
        self.assertEqual(param._value, 5)

    def test_set_string_parameter(self):
        element = MockElement()
        param = MockParameter("Name", MockStorageType.String, "")
        element.add_parameter(param)

        result = self.strategy.set_parameter(element, "Name", "Test Name")
        self.assertTrue(result)
        self.assertEqual(param._value, "Test Name")

    def test_parameter_not_found(self):
        element = MockElement()

        with self.assertRaises(Exception):
            self.strategy.set_parameter(element, "NonExistent", 10)

class TestOptimizedParameterStrategy(unittest.TestCase):
    """Test cases for OptimizedParameterStrategy."""

    def setUp(self):
        self.doc = MockDocument()
        self.strategy = OptimizedParameterStrategy(self.doc)

    def test_caching(self):
        element = MockElement()
        param = MockParameter("Length", MockStorageType.Double, 0.0)
        element.add_parameter(param)

        # First call should cache
        result1 = self.strategy.set_parameter(element, "Length", 10.5)
        self.assertTrue(result1)

        # Second call should use cache
        result2 = self.strategy.set_parameter(element, "Length", 20.5)
        self.assertTrue(result2)

        # Verify final value
        self.assertEqual(param._value, 20.5)

    def test_unit_conversion(self):
        element = MockElement()
        param = MockParameter("Length", MockStorageType.Double, 0.0)
        element.add_parameter(param)

        # Test mm to feet conversion
        result = self.strategy.set_parameter(element, "Length", "1000 mm")
        self.assertTrue(result)
        expected_feet = 1000 / 304.8
        self.assertAlmostEqual(param._value, expected_feet, places=5)

class TestParameterSettingFramework(unittest.TestCase):
    """Test cases for ParameterSettingFramework."""

    def setUp(self):
        self.doc = MockDocument()
        self.framework = ParameterSettingFramework(self.doc)

    def test_single_parameter_setting(self):
        element = MockElement()
        param = MockParameter("Length", MockStorageType.Double, 0.0)
        element.add_parameter(param)

        result = self.framework.set_parameter(element, "Length", 15.5)
        self.assertTrue(result)
        self.assertEqual(param._value, 15.5)

    def test_multiple_parameter_setting(self):
        element1 = MockElement(1)
        element2 = MockElement(2)

        param1 = MockParameter("Length", MockStorageType.Double, 0.0)
        param2 = MockParameter("Width", MockStorageType.Double, 0.0)

        element1.add_parameter(param1)
        element2.add_parameter(param2)

        operations = [
            (element1, "Length", 10.0),
            (element2, "Width", 20.0)
        ]

        results = self.framework.set_multiple_parameters(operations)
        self.assertTrue(results[(1, "Length")]['success'])
        self.assertTrue(results[(2, "Width")]['success'])
        self.assertEqual(param1._value, 10.0)
        self.assertEqual(param2._value, 20.0)

    def test_validation_failure(self):
        element = MockElement()
        param = MockParameter("Length", MockStorageType.Double, 0.0)
        element.add_parameter(param)

        # Try to set invalid value
        with self.assertRaises(ParameterSettingError):
            self.framework.set_parameter(element, "Length", "invalid")

    def test_performance_tracking(self):
        element = MockElement()
        param = MockParameter("Length", MockStorageType.Double, 0.0)
        element.add_parameter(param)

        self.framework.set_parameter(element, "Length", 5.0)

        metrics = self.framework.get_performance_metrics()
        self.assertEqual(metrics['total_operations'], 1)
        self.assertIn('strategy_metrics', metrics)
        self.assertIn('history', metrics)

    def test_optimization_level_recommendation(self):
        # Test recommendation logic
        self.assertEqual(
            self.framework.recommend_optimization_level(1),
            OptimizationLevel.BASIC
        )
        self.assertEqual(
            self.framework.recommend_optimization_level(15),
            OptimizationLevel.BATCH
        )
        self.assertEqual(
            self.framework.recommend_optimization_level(7, has_repeated_elements=True),
            OptimizationLevel.OPTIMIZED
        )

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)