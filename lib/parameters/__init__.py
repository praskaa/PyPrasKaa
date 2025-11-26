# -*- coding: utf-8 -*-
"""
Parameter Setting Framework - Standardized parameter operations for Revit elements.

This module provides a unified, robust framework for setting parameters on Revit elements,
replacing inconsistent patterns found across the extension with a standardized approach.
"""

__title__ = 'Parameter Setting Framework'
__author__ = 'Kilo Code'
__version__ = '1.0.0'

from .framework import ParameterSettingFramework
from .strategies import ParameterSettingStrategy
from .validators import ParameterValidator
from .exceptions import ParameterSettingError, ValidationError, TransactionError

__all__ = [
    'ParameterSettingFramework',
    'ParameterSettingStrategy',
    'ParameterValidator',
    'ParameterSettingError',
    'ValidationError',
    'TransactionError'
]