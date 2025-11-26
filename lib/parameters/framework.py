# -*- coding: utf-8 -*-
"""
Core Parameter Setting Framework - Main orchestration class.
"""

import time
from enum import Enum
try:
    from .strategies import BasicParameterStrategy, BatchParameterStrategy, OptimizedParameterStrategy
    from .validators import ParameterValidator
    from .exceptions import ParameterSettingError, ValidationError, StrategyError
except ImportError:
    # Mock for testing
    class ParameterSettingError(Exception):
        pass
    class ValidationError(Exception):
        pass
    class StrategyError(Exception):
        pass
    class ParameterValidator:
        pass
    class BasicParameterStrategy:
        pass
    class BatchParameterStrategy:
        pass
    class OptimizedParameterStrategy:
        pass

class OptimizationLevel(Enum):
    """Optimization levels for parameter setting."""
    BASIC = "basic"           # Individual transactions, no caching
    BATCH = "batch"           # Single transaction for multiple operations
    OPTIMIZED = "optimized"   # Caching and smart optimizations

class ParameterSettingFramework:
    """
    Main framework class for standardized parameter setting operations.

    This class orchestrates parameter setting operations using different strategies
    based on the optimization level and operation requirements.
    """

    def __init__(self, doc, logger=None, default_optimization=OptimizationLevel.OPTIMIZED):
        """
        Initialize the framework.

        Args:
            doc: Revit Document
            logger: Optional logger instance
            default_optimization: Default optimization level
        """
        self.doc = doc
        self.logger = logger
        self.default_optimization = default_optimization

        # Initialize components
        self.validator = ParameterValidator(logger)
        self.strategies = {
            OptimizationLevel.BASIC: BasicParameterStrategy(doc, logger),
            OptimizationLevel.BATCH: BatchParameterStrategy(doc, logger),
            OptimizationLevel.OPTIMIZED: OptimizedParameterStrategy(doc, logger)
        }

        # Performance tracking
        self.performance_history = []
        self.operation_count = 0

        if self.logger:
            self.logger.info("Parameter Setting Framework initialized")

    def set_parameter(self, element, param_name, value, optimization_level=None, validate=True, **kwargs):
        """
        Set a parameter value using the framework.

        Args:
            element: Revit element
            param_name: Parameter name
            value: Value to set
            optimization_level: Optimization level (uses default if None)
            validate: Whether to validate before setting
            **kwargs: Additional options for validation/strategy

        Returns:
            bool: Success status

        Raises:
            ParameterSettingError: If operation fails
        """
        start_time = time.time()
        self.operation_count += 1

        try:
            # Determine optimization level
            if optimization_level is None:
                optimization_level = self.default_optimization

            # Select strategy
            strategy = self.strategies[optimization_level]

            # Validation
            if validate:
                is_valid, normalized_value, warnings = self._validate_operation(
                    element, param_name, value, **kwargs
                )

                if not is_valid:
                    raise ValidationError("Validation failed: {}".format(warnings))

                if warnings and self.logger:
                    for warning in warnings:
                        self.logger.warning(warning)

                # Use normalized value if provided
                if normalized_value is not None:
                    value = normalized_value

            # Execute operation
            if optimization_level == OptimizationLevel.BATCH:
                # For batch operations, add to batch and return success
                # (actual execution happens on execute_batch)
                strategy.add_operation(element, param_name, value)
                result = True
            else:
                # Execute immediately
                result = strategy.set_parameter(element, param_name, value, **kwargs)

            # Track performance
            operation_time = time.time() - start_time
            self._track_performance(optimization_level, operation_time, result)

            return result

        except Exception as e:
            operation_time = time.time() - start_time
            self._track_performance(optimization_level, operation_time, False)

            if self.logger:
                self.logger.error("Parameter setting failed: {}".format(str(e)))

            raise ParameterSettingError("Failed to set parameter '{}': {}".format(param_name, str(e)))

    def set_multiple_parameters(self, operations, optimization_level=None, validate=True, **kwargs):
        """
        Set multiple parameters efficiently.

        Args:
            operations: List of (element, param_name, value) tuples
            optimization_level: Optimization level
            validate: Whether to validate
            **kwargs: Additional options

        Returns:
            dict: Results for each operation
        """
        if optimization_level is None:
            optimization_level = self.default_optimization

        results = {}

        if optimization_level == OptimizationLevel.BATCH:
            # Use batch strategy for all operations
            strategy = self.strategies[OptimizationLevel.BATCH]

            for element, param_name, value in operations:
                if validate:
                    is_valid, normalized_value, warnings = self._validate_operation(
                        element, param_name, value, **kwargs
                    )
                    if not is_valid:
                        results[(element.Id.IntegerValue, param_name)] = {
                            'success': False,
                            'error': "Validation failed: {}".format(warnings)
                        }
                        continue
                    if normalized_value is not None:
                        value = normalized_value

                strategy.add_operation(element, param_name, value)
                results[(element.Id.IntegerValue, param_name)] = {'success': True}

            # Execute batch
            try:
                strategy.execute_batch()
            except Exception as e:
                # Mark all as failed if batch fails
                for key in results:
                    if results[key]['success']:
                        results[key] = {'success': False, 'error': str(e)}
        else:
            # Execute individually
            for element, param_name, value in operations:
                try:
                    success = self.set_parameter(
                        element, param_name, value,
                        optimization_level=optimization_level,
                        validate=validate, **kwargs
                    )
                    results[(element.Id.IntegerValue, param_name)] = {'success': success}
                except Exception as e:
                    results[(element.Id.IntegerValue, param_name)] = {
                        'success': False,
                        'error': str(e)
                    }

        return results

    def execute_batch_operations(self, transaction_name="Batch Parameter Operations"):
        """
        Execute all pending batch operations.

        Returns:
            bool: Success status
        """
        strategy = self.strategies[OptimizationLevel.BATCH]
        return strategy.execute_batch(transaction_name)

    def get_performance_metrics(self):
        """
        Get performance metrics for all strategies.

        Returns:
            dict: Performance data
        """
        metrics = {
            'total_operations': self.operation_count,
            'strategy_metrics': {},
            'history': self.performance_history[-10:]  # Last 10 operations
        }

        for level, strategy in self.strategies.items():
            metrics['strategy_metrics'][level.value] = strategy.performance_metrics.copy()

        return metrics

    def clear_caches(self):
        """Clear all caches in optimized strategies."""
        for strategy in self.strategies.values():
            if hasattr(strategy, 'clear_cache'):
                strategy.clear_cache()

    def _validate_operation(self, element, param_name, value, **kwargs):
        """Internal validation method."""
        # First validate parameter existence
        is_valid, param, warnings = self.validator.validate_element_parameter(
            element, param_name, **kwargs
        )

        if not is_valid:
            return False, None, warnings

        # Then validate value against storage type
        storage_type = param.StorageType
        value_valid, normalized_value, value_warnings = self.validator.validate_parameter_value(
            param_name, value, storage_type, **kwargs
        )

        warnings.extend(value_warnings)

        return value_valid, normalized_value, warnings

    def _track_performance(self, optimization_level, operation_time, success):
        """Track performance metrics."""
        self.performance_history.append({
            'timestamp': time.time(),
            'optimization_level': optimization_level.value,
            'operation_time': operation_time,
            'success': success
        })

        # Keep only last 100 operations
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]

    def recommend_optimization_level(self, operation_count, has_repeated_elements=False):
        """
        Recommend optimization level based on operation characteristics.

        Args:
            operation_count: Number of operations
            has_repeated_elements: Whether operations involve repeated elements

        Returns:
            OptimizationLevel: Recommended level
        """
        if operation_count >= 10:
            return OptimizationLevel.BATCH
        elif has_repeated_elements or operation_count >= 5:
            return OptimizationLevel.OPTIMIZED
        else:
            return OptimizationLevel.BASIC