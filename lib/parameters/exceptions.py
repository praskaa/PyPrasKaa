# -*- coding: utf-8 -*-
"""
Custom exceptions for the Parameter Setting Framework.
"""

class ParameterSettingError(Exception):
    """Base exception for parameter setting operations."""
    pass

class ValidationError(ParameterSettingError):
    """Raised when parameter validation fails."""
    pass

class TransactionError(ParameterSettingError):
    """Raised when transaction operations fail."""
    pass

class StrategyError(ParameterSettingError):
    """Raised when strategy selection or execution fails."""
    pass