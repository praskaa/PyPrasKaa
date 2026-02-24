# -*- coding: utf-8 -*-
"""
WorkflowEngine - Orchestrates workflow step execution

The main engine that manages sequential step execution
with proper transaction management.
"""

from step_result import StepResult, StepStatus
from step_context import StepContext
from workflow_step import WorkflowStep


class WorkflowEngine:
    """
    Orchestrates workflow step execution with transaction management.
    
    This class manages the execution of a sequence of workflow steps,
    handling transaction commits, rollbacks, and error propagation.
    
    Attributes:
        steps (list): Ordered list of WorkflowStep instances
        context (StepContext): Shared context for all steps
        results (list): Results of each step execution
        stop_on_failure (bool): Stop workflow on step failure
        rollback_on_failure (bool): Attempt rollback on failure
    
    Usage:
        context = StepContext()
        workflow = WorkflowEngine(context)
        workflow.add_step(MyStep1())
        workflow.add_step(MyStep2())
        result = workflow.run()
    """
    
    def __init__(
        self,
        context=None,
        steps=None,
        stop_on_failure=True,
        rollback_on_failure=True
    ):
        """
        Initialize WorkflowEngine.
        
        Args:
            context (StepContext): Shared context (creates new if None)
            steps (list): Initial list of steps
            stop_on_failure (bool): Stop on step failure
            rollback_on_failure (bool): Rollback on failure
        """
        self.context = context or StepContext()
        self.steps = list(steps) if steps else []
        self.results = []
        self.current_step_index = -1
        self.stop_on_failure = stop_on_failure
        self.rollback_on_failure = rollback_on_failure
        self._is_running = False
        self._has_committed = False
    
    def add_step(self, step):
        """
        Add a step to the workflow.
        
        Args:
            step (WorkflowStep): Step to add
        
        Returns:
            self: For method chaining
        """
        # Use marker attribute for IronPython compatibility
        if hasattr(step, 'IS_WORKFLOW_STEP'):
            self.steps.append(step)
        return self
    
    def insert_step(self, index, step):
        """
        Insert a step at specific index.
        
        Args:
            index (int): Index to insert at
            step (WorkflowStep): Step to insert
        
        Returns:
            self: For method chaining
        """
        # Use marker attribute for IronPython compatibility
        if hasattr(step, 'IS_WORKFLOW_STEP'):
            self.steps.insert(index, step)
        return self
    
    def remove_step(self, index):
        """
        Remove step at index.
        
        Args:
            index (int): Index of step to remove
        
        Returns:
            WorkflowStep: Removed step
        """
        if 0 <= index < len(self.steps):
            return self.steps.pop(index)
        return None
    
    def get_step(self, index):
        """
        Get step at index.
        
        Args:
            index (int): Step index
        
        Returns:
            WorkflowStep or None
        """
        if 0 <= index < len(self.steps):
            return self.steps[index]
        return None
    
    def get_previous_result(self, index=-1):
        """
        Get result of a previous step.
        
        Args:
            index (int): Step index (default: -1 for last step)
        
        Returns:
            StepResult or None
        """
        if not self.results:
            return None
        
        if index < 0:
            index = len(self.results) + index
        
        if 0 <= index < len(self.results):
            return self.results[index]
        return None
    
    def can_continue(self):
        """
        Check if workflow can continue to next step.
        
        Returns:
            bool: True if can continue
        """
        # Can't continue if not running
        if not self._is_running:
            return False
        
        # Can't continue if already at last step
        if self.current_step_index >= len(self.steps) - 1:
            return False
        
        # Can't continue if last result was failure and stop_on_failure
        if self.results:
            last_result = self.results[-1]
            if last_result.is_failed() and self.stop_on_failure:
                return False
        
        return True
    
    def run(self):
        """
        Run all workflow steps sequentially.
        
        Returns:
            StepResult: Final workflow result
        """
        self._is_running = True
        self.results = []
        self.current_step_index = -1
        self._has_committed = False
        
        try:
            # Run each step
            for i, step in enumerate(self.steps):
                self.current_step_index = i
                
                # Execute step
                result = self._run_step(i, step)
                self.results.append(result)
                
                # Check if should stop
                if result.is_failed() and self.stop_on_failure:
                    # Include original error info
                    error_info = ""
                    if result.error:
                        error_info = " - {}".format(str(result.error))
                    return StepResult.failed(
                        "Workflow stopped at step '{}': {}{}".format(
                            step.name,
                            result.message,
                            error_info
                        ),
                        data={
                            "failed_step": i,
                            "step_name": step.name,
                            "original_message": result.message,
                            "original_error": str(result.error) if result.error else None
                        },
                        error=result.error
                    )
                
                if result.is_cancelled():
                    return StepResult.cancelled(
                        "Workflow cancelled at step '{}'".format(step.name),
                        data={"cancelled_step": i, "step_name": step.name}
                    )
            
            # All steps completed
            return StepResult.success(
                "Workflow completed successfully",
                data={
                    "steps_completed": len(self.steps),
                    "results": [r.status.value for r in self.results]
                }
            )
        
        except Exception as e:
            return StepResult.failed(
                "Workflow failed with exception: {}".format(str(e)),
                error=e
            )
        finally:
            self._is_running = False
    
    def run_step(self, index):
        """
        Run a single step by index.
        
        Args:
            index (int): Step index to run
        
        Returns:
            StepResult: Step execution result
        """
        if index < 0 or index >= len(self.steps):
            return StepResult.failed("Invalid step index: {}".format(index))
        
        step = self.steps[index]
        return self._run_step(index, step)
    
    def _run_step(self, index, step):
        """
        Internal method to run a single step with transaction handling.
        
        Args:
            index (int): Step index
            step (WorkflowStep): Step to run
        
        Returns:
            StepResult: Step execution result
        """
        # Validate step
        validation_result = step.validate(self.context)
        if validation_result.is_failed():
            if step.optional:
                return StepResult.skipped(
                    "Step '{}' skipped: {}".format(step.name, validation_result.message)
                )
            return StepResult.failed(
                "Step '{}' validation failed: {}".format(
                    step.name,
                    validation_result.message
                )
            )
        
        # Before execute hook
        step.before_execute(self.context)
        
        # Execute step
        if step.requires_transaction:
            result = self._execute_with_transaction(step)
        else:
            result = step.execute(self.context)
        
        # After execute hook
        step.after_execute(self.context, result)
        
        # Update committed state
        if result.transaction_committed:
            self._has_committed = True
        
        return result
    
    def _execute_with_transaction(self, step):
        """
        Execute step with transaction management.
        
        Args:
            step (WorkflowStep): Step to execute
        
        Returns:
            StepResult: Execution result
        """
        try:
            from Autodesk.Revit.DB import Transaction
            
            # Determine which document to use
            doc = self._get_transaction_document(step)
            if not doc:
                return StepResult.failed(
                    "No valid document for transaction"
                )
            
            # Create transaction
            t = Transaction(doc, step.name)
            t.Start()
            
            try:
                # Execute step logic
                result = step.execute(self.context)
                
                # Check if commit is needed
                if step.commit_after and result.is_success():
                    t.Commit()
                    result.transaction_committed = True
                else:
                    t.RollBack()
                    result.transaction_committed = False
                
                return result
            
            except Exception as e:
                # Rollback on exception
                if t.HasStarted():
                    t.RollBack()
                return StepResult.failed(
                    "Transaction failed: {}".format(str(e)),
                    error=e
                )
        
        except ImportError:
            # Not in Revit environment - just execute
            return step.execute(self.context)
    
    def _get_transaction_document(self, step):
        """
        Determine which document to use for transaction.
        
        Args:
            step (WorkflowStep): Current step
        
        Returns:
            Document or None
        """
        # Prefer target doc for operations that modify target
        if step.commit_after and self.context.target_doc:
            return self.context.target_doc
        
        if self.context.source_doc:
            return self.context.source_doc
        
        if self.context.target_doc:
            return self.context.target_doc
        
        return None
    
    def get_progress(self):
        """
        Get workflow progress information.
        
        Returns:
            dict: Progress information
        """
        total = len(self.steps)
        completed = len(self.results)
        
        current_step = None
        if self.current_step_index >= 0 and self.current_step_index < total:
            current_step = self.steps[self.current_step_index].name
        
        return {
            "total_steps": total,
            "completed_steps": completed,
            "current_step": current_step,
            "current_index": self.current_step_index,
            "has_failures": any(r.is_failed() for r in self.results),
            "has_committed": self._has_committed
        }
    
    def __repr__(self):
        return "WorkflowEngine(steps={}, context={})".format(
            len(self.steps),
            repr(self.context)
        )
