# -*- coding: utf-8 -*-
"""
Parameter setting strategies for different scenarios and optimization levels.
"""

import sys
import time
from abc import ABCMeta, abstractmethod

# Mock clr for testing environments
try:
    import clr
except ImportError:
    clr = None

# Revit API imports
try:
    if clr is not None:
        clr.AddReference('RevitAPI')
        from Autodesk.Revit.DB import *
    else:
        # Mock for testing environments
        pass
except (ImportError, AttributeError):
    # Mock for testing environments
    pass

# Local imports
from .exceptions import StrategyError, TransactionError

class ParameterSettingStrategy(object):
    """Abstract base class for parameter setting strategies."""
    __metaclass__ = ABCMeta

    def __init__(self, doc, logger=None):
        self.doc = doc
        self.logger = logger
        self.performance_metrics = {
            'operation_count': 0,
            'total_time': 0.0,
            'success_count': 0,
            'error_count': 0
        }

    @abstractmethod
    def set_parameter(self, element, param_name, value, **kwargs):
        """
        Set a parameter value on an element.

        Args:
            element: Revit element
            param_name: Parameter name
            value: Value to set
            **kwargs: Additional strategy-specific options

        Returns:
            bool: Success status
        """
        pass

    def _find_parameter(self, element, param_name):
        """Find parameter on element or its type."""
        param = element.LookupParameter(param_name)
        if not param:
            # Try type parameter if instance
            if isinstance(element, FamilyInstance):
                elem_type = self.doc.GetElement(element.GetTypeId())
                if elem_type:
                    param = elem_type.LookupParameter(param_name)
            elif isinstance(element, FamilySymbol):
                param = element.LookupParameter(param_name)
        return param

    def _log_performance(self, operation_time, success=True):
        """Log performance metrics."""
        self.performance_metrics['operation_count'] += 1
        self.performance_metrics['total_time'] += operation_time
        if success:
            self.performance_metrics['success_count'] += 1
        else:
            self.performance_metrics['error_count'] += 1

class BasicParameterStrategy(ParameterSettingStrategy):
    """Basic parameter setting with individual transactions."""

    def set_parameter(self, element, param_name, value, **kwargs):
        start_time = time.time()

        try:
            param = self._find_parameter(element, param_name)
            if not param:
                raise StrategyError("Parameter '{}' not found on element.".format(param_name))

            storage_type = param.StorageType

            with Transaction(self.doc, "Set {}".format(param_name)) as t:
                t.Start()

                if storage_type == StorageType.Double:
                    param.Set(float(value))
                elif storage_type == StorageType.Integer:
                    param.Set(int(value))
                elif storage_type == StorageType.String:
                    param.Set(str(value))
                elif storage_type == StorageType.ElementId:
                    raise StrategyError("ElementId parameters not supported in basic strategy.")
                else:
                    raise StrategyError("Unsupported storage type: {}".format(storage_type))

                t.Commit()

            operation_time = time.time() - start_time
            self._log_performance(operation_time, True)

            if self.logger:
                self.logger.info("Parameter '{}' set to '{}' successfully.".format(param_name, value))

            return True

        except Exception as e:
            operation_time = time.time() - start_time
            self._log_performance(operation_time, False)

            if self.logger:
                self.logger.error("Error setting parameter '{}' to '{}': {}".format(param_name, value, str(e)))

            raise StrategyError("Failed to set parameter: {}".format(str(e)))

class BatchParameterStrategy(ParameterSettingStrategy):
    """Batch parameter setting with single transaction for multiple operations."""

    def __init__(self, doc, logger=None):
        ParameterSettingStrategy.__init__(self, doc, logger)
        self.batch_operations = []

    def add_operation(self, element, param_name, value):
        """Add operation to batch."""
        self.batch_operations.append((element, param_name, value))

    def execute_batch(self, transaction_name="Batch Parameter Setting"):
        """Execute all batched operations in single transaction."""
        if not self.batch_operations:
            return True

        start_time = time.time()

        try:
            with Transaction(self.doc, transaction_name) as t:
                t.Start()

                for element, param_name, value in self.batch_operations:
                    param = self._find_parameter(element, param_name)
                    if not param:
                        raise StrategyError("Parameter '{}' not found on element.".format(param_name))

                    storage_type = param.StorageType

                    if storage_type == StorageType.Double:
                        param.Set(float(value))
                    elif storage_type == StorageType.Integer:
                        param.Set(int(value))
                    elif storage_type == StorageType.String:
                        param.Set(str(value))
                    elif storage_type == StorageType.ElementId:
                        raise StrategyError("ElementId parameters not supported in batch strategy.")
                    else:
                        raise StrategyError("Unsupported storage type: {}".format(storage_type))

                t.Commit()

            operation_time = time.time() - start_time
            self._log_performance(operation_time, True)

            if self.logger:
                self.logger.info("Batch operation completed: {} parameters set.".format(len(self.batch_operations)))

            del self.batch_operations[:]
            return True

        except Exception as e:
            operation_time = time.time() - start_time
            self._log_performance(operation_time, False)

            if self.logger:
                self.logger.error("Batch operation failed: {}".format(str(e)))

            del self.batch_operations[:]
            raise StrategyError("Batch operation failed: {}".format(str(e)))

    def set_parameter(self, element, param_name, value, **kwargs):
        """Add to batch instead of immediate execution."""
        self.add_operation(element, param_name, value)
        return True  # Deferred execution

class OptimizedParameterStrategy(ParameterSettingStrategy):
    """Optimized strategy with caching and smart validation."""

    def __init__(self, doc, logger=None):
        ParameterSettingStrategy.__init__(self, doc, logger)
        self.parameter_cache = {}  # Cache for parameter lookups
        self.element_cache = {}    # Cache for element type lookups

    def _cached_find_parameter(self, element, param_name):
        """Find parameter with caching."""
        element_id = element.Id.IntegerValue
        cache_key = (element_id, param_name)

        if cache_key in self.parameter_cache:
            return self.parameter_cache[cache_key]

        param = self._find_parameter(element, param_name)
        self.parameter_cache[cache_key] = param
        return param

    def _get_element_type_cached(self, element):
        """Get element type with caching."""
        if isinstance(element, FamilyInstance):
            element_id = element.Id.IntegerValue
            if element_id not in self.element_cache:
                self.element_cache[element_id] = self.doc.GetElement(element.GetTypeId())
            return self.element_cache[element_id]
        return None

    def set_parameter(self, element, param_name, value, **kwargs):
        start_time = time.time()

        try:
            param = self._cached_find_parameter(element, param_name)
            if not param:
                raise StrategyError("Parameter '{}' not found on element.".format(param_name))

            storage_type = param.StorageType

            with Transaction(self.doc, "Set {}".format(param_name)) as t:
                t.Start()

                if storage_type == StorageType.Double:
                    # Smart unit conversion if needed
                    if isinstance(value, str) and ('mm' in value.lower() or 'm' in value.lower()):
                        # Convert mm/m to feet for Revit
                        numeric_value = float(''.join(c for c in value if c.isdigit() or c in '.-'))
                        if 'mm' in value.lower():
                            numeric_value /= 304.8  # mm to feet
                        elif 'm' in value.lower():
                            numeric_value *= 3.28084  # m to feet
                        param.Set(numeric_value)
                    else:
                        param.Set(float(value))
                elif storage_type == StorageType.Integer:
                    param.Set(int(value))
                elif storage_type == StorageType.String:
                    param.Set(str(value))
                elif storage_type == StorageType.ElementId:
                    raise StrategyError("ElementId parameters not supported in optimized strategy.")
                else:
                    raise StrategyError("Unsupported storage type: {}".format(storage_type))

                t.Commit()

            operation_time = time.time() - start_time
            self._log_performance(operation_time, True)

            if self.logger:
                self.logger.info("Parameter '{}' set to '{}' successfully (optimized).".format(param_name, value))

            return True

        except Exception as e:
            operation_time = time.time() - start_time
            self._log_performance(operation_time, False)

            if self.logger:
                self.logger.error("Error setting parameter '{}' to '{}': {}".format(param_name, value, str(e)))

            raise StrategyError("Failed to set parameter: {}".format(str(e)))

    def clear_cache(self):
        """Clear all caches."""
        self.parameter_cache.clear()
        self.element_cache.clear()