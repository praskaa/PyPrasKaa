# -*- coding: utf-8 -*-
"""
StepResult - Result container for workflow step execution

Provides a standardized way to track the result of each workflow step
including status, data, and error information.
"""

from enum import Enum


class StepStatus(Enum):
    """Status enumeration for step execution results"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class StepResult:
    """
    Encapsulates the result of a workflow step execution.
    
    Attributes:
        status (StepStatus): Execution status
        message (str): Human-readable message
        data (dict): Step-specific data output
        error (Exception): Exception object if failed
        transaction_committed (bool): Whether transaction was committed
    
    Usage:
        return StepResult.success("Operation completed", {"count": 5})
        return StepResult.failed("Error occurred", error=e)
        return StepResult.skipped("Step skipped")
    """
    
    def __init__(
        self,
        status,
        message="",
        data=None,
        error=None,
        transaction_committed=False
    ):
        """
        Initialize StepResult.
        
        Args:
            status (StepStatus): Execution status
            message (str): Human-readable message
            data (dict): Step-specific data output
            error (Exception): Exception object if failed
            transaction_committed (bool): Whether transaction was committed
        """
        self.status = status
        self.message = message
        self.data = data or {}
        self.error = error
        self.transaction_committed = transaction_committed
    
    @staticmethod
    def success(message="", data=None, transaction_committed=False):
        """
        Create a success result.
        
        Args:
            message (str): Success message
            data (dict): Optional data to return
            transaction_committed (bool): Whether transaction was committed
        
        Returns:
            StepResult: Success result instance
        """
        return StepResult(
            status=StepStatus.SUCCESS,
            message=message,
            data=data,
            transaction_committed=transaction_committed
        )
    
    @staticmethod
    def failed(message="", error=None, data=None):
        """
        Create a failed result.
        
        Args:
            message (str): Error message
            error (Exception): Exception object
            data (dict): Optional data to return
        
        Returns:
            StepResult: Failed result instance
        """
        return StepResult(
            status=StepStatus.FAILED,
            message=message,
            data=data,
            error=error
        )
    
    @staticmethod
    def skipped(message="", data=None):
        """
        Create a skipped result.
        
        Args:
            message (str): Skip message
            data (dict): Optional data to return
        
        Returns:
            StepResult: Skipped result instance
        """
        return StepResult(
            status=StepStatus.SKIPPED,
            message=message,
            data=data
        )
    
    @staticmethod
    def cancelled(message="", data=None):
        """
        Create a cancelled result.
        
        Args:
            message (str): Cancellation message
            data (dict): Optional data to return
        
        Returns:
            StepResult: Cancelled result instance
        """
        return StepResult(
            status=StepStatus.CANCELLED,
            message=message,
            data=data
        )
    
    def is_success(self):
        """Check if result is successful."""
        return self.status == StepStatus.SUCCESS
    
    def is_failed(self):
        """Check if result failed."""
        return self.status == StepStatus.FAILED
    
    def is_skipped(self):
        """Check if result was skipped."""
        return self.status == StepStatus.SKIPPED
    
    def is_cancelled(self):
        """Check if result was cancelled."""
        return self.status == StepStatus.CANCELLED
    
    def get_data(self, key, default=None):
        """
        Get data value by key.
        
        Args:
            key (str): Data key
            default: Default value if key not found
        
        Returns:
            Data value or default
        """
        return self.data.get(key, default)
    
    def __repr__(self):
        return "StepResult(status={}, message='{}')".format(
            self.status.value,
            self.message
        )
    
    def __str__(self):
        return "[{}] {}".format(
            self.status.value.upper(),
            self.message
        )
