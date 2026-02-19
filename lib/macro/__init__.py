# -*- coding: utf-8 -*-
"""
Macro Workflow Automation Framework for pyRevit

This module provides a macro-like system that automates sequential
pyRevit/Revit API operations with proper multi-transaction management.

Usage:
    from macro import WorkflowEngine, WorkflowStep, StepContext
    
    # Define custom steps
    class MyStep(WorkflowStep):
        name = "My Step"
        description = "Does something"
        
        def validate(self, context):
            return StepResult.success("OK")
        
        def execute(self, context):
            return StepResult.success("Done")
    
    # Create and run workflow
    context = StepContext()
    workflow = WorkflowEngine(context)
    workflow.add_step(MyStep())
    result = workflow.run()
"""

from step_result import StepResult, StepStatus
from step_context import StepContext, WorkflowVariables
from workflow_step import WorkflowStep
from workflow_engine import WorkflowEngine

__all__ = [
    'StepResult',
    'StepStatus',
    'StepContext',
    'WorkflowVariables',
    'WorkflowStep',
    'WorkflowEngine',
]
