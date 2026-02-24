# -*- coding: utf-8 -*-
"""
WorkflowStep - Base class for workflow steps

Provides a base class for defining workflow steps
with transaction management support.
"""

from step_result import StepResult


class WorkflowStep(object):
    """
    Base class for workflow steps.
    
    All workflow steps should inherit from this class and implement
    the required methods. The class provides hooks for transaction
    management and step lifecycle events.
    
    Class Attributes:
        name (str): Step display name
        description (str): Step description
        requires_transaction (bool): Whether step needs transaction
        commit_after (bool): Whether to commit after step execution
        optional (bool): Whether step can be skipped
    
    Usage:
        class MyStep(WorkflowStep):
            name = "My Step"
            description = "Does something useful"
            requires_transaction = True
            commit_after = True
            
            def validate(self, context):
                return StepResult.success("OK")
            
            def execute(self, context):
                # Do something
                return StepResult.success("Done")
    """
    
    # Marker attribute for type checking
    IS_WORKFLOW_STEP = True
    
    # Step configuration (override in subclasses)
    name = "Unnamed Step"
    description = ""
    requires_transaction = False
    commit_after = False
    optional = False
    
    def __init__(self):
        """Initialize workflow step."""
        self._current_context = None
    
    @property
    def step_name(self):
        """Get step name."""
        return self.name
    
    @property
    def step_description(self):
        """Get step description."""
        return self.description
    
    def validate(self, context):
        """
        Validate prerequisites before execution.
        
        Override this method to add validation logic that runs
        before the main execute method.
        
        Args:
            context (StepContext): Shared workflow context
        
        Returns:
            StepResult: Validation result (success or failed)
        """
        return StepResult.success("Validation passed")
    
    def execute(self, context):
        """
        Execute the step logic.
        
        This method must be implemented by subclasses.
        Override in your custom step class.
        
        Args:
            context (StepContext): Shared workflow context
        
        Returns:
            StepResult: Execution result
        
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError(
            "Subclasses must implement execute() method"
        )
    
    def rollback(self, context):
        """
        Rollback if step failed.
        
        Override this method to add rollback logic for when
        a subsequent step fails.
        
        Args:
            context (StepContext): Shared workflow context
        
        Returns:
            StepResult: Rollback result
        """
        return StepResult.success("Rollback not implemented")
    
    def before_execute(self, context):
        """
        Called before execute method.
        
        Override to add pre-execution logic like logging.
        
        Args:
            context (StepContext): Shared workflow context
        """
        self._current_context = context
    
    def after_execute(self, context, result):
        """
        Called after execute method.
        
        Override to add post-execution logic like logging.
        
        Args:
            context (StepContext): Shared workflow context
            result (StepResult): Execution result
        """
        pass
    
    def __repr__(self):
        return "WorkflowStep(name='{}', requires_tx={}, commit={})".format(
            self.name,
            self.requires_transaction,
            self.commit_after
        )


class TransactionalStep(WorkflowStep):
    """
    A workflow step that automatically handles transactions.
    
    This is a convenience base class for steps that need
    automatic transaction management.
    
    Usage:
        class MyTransactionalStep(TransactionalStep):
            name = "My Transactional Step"
            commit_after = True
            
            def execute_inside_transaction(self, context):
                # Your logic here
                return StepResult.success("Done")
    """
    
    requires_transaction = True
    commit_after = True
    
    def execute_inside_transaction(self, context):
        """
        Execute logic inside transaction.
        
        This method is called automatically within a transaction
        when requires_transaction is True.
        
        Args:
            context (StepContext): Shared workflow context
        
        Returns:
            StepResult: Execution result
        """
        raise NotImplementedError(
            "Subclasses must implement execute_inside_transaction()"
        )
    
    def execute(self, context):
        """
        Execute with automatic transaction handling.
        
        Don't override this method - override execute_inside_transaction instead.
        
        Args:
            context (StepContext): Shared workflow context
        
        Returns:
            StepResult: Execution result
        """
        # Let the workflow engine handle the transaction
        # This method will be called inside a transaction
        return self.execute_inside_transaction(context)


class SimpleStep(WorkflowStep):
    """
    A simple step without transaction requirements.
    
    This is a convenience base class for steps that don't
    need transaction management.
    
    Usage:
        class MySimpleStep(SimpleStep):
            name = "My Simple Step"
            
            def run(self, context):
                # Your logic here
                return StepResult.success("Done")
    """
    
    requires_transaction = False
    commit_after = False
    
    def run(self, context):
        """
        Run the step logic.
        
        Args:
            context (StepContext): Shared workflow context
        
        Returns:
            StepResult: Execution result
        """
        raise NotImplementedError("Subclasses must implement run()")
    
    def execute(self, context):
        """
        Execute the simple step.
        
        Don't override this method - override run instead.
        
        Args:
            context (StepContext): Shared workflow context
        
        Returns:
            StepResult: Execution result
        """
        return self.run(context)
