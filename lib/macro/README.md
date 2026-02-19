# Macro Workflow Automation Framework

A macro-like system for pyRevit that automates sequential Revit API operations with proper multi-transaction management.

## Overview

This framework provides a structured way to create and run multi-step workflows in Revit, with built-in support for:
- Sequential step execution
- Transaction management per step
- Data sharing between steps
- Progress tracking and error handling

## Quick Start

### Using the Pre-built Workflow

```python
from macro.workflows import CopyDetailElementsWorkflow

# Create and run workflow
workflow = CopyDetailElementsWorkflow()
result = workflow.run()

if result.is_success():
    print("Copied {} elements".format(result.get_data("copied_count")))
```

### Creating Custom Workflows

```python
from macro import WorkflowEngine, WorkflowStep, StepContext, StepResult

# Define a custom step
class MyStep(WorkflowStep):
    name = "My Step"
    description = "Does something useful"
    requires_transaction = True
    commit_after = True
    
    def validate(self, context):
        return StepResult.success("OK")
    
    def execute(self, context):
        # Your logic here
        return StepResult.success("Done", data={"key": "value"})

# Create workflow
context = StepContext()
workflow = WorkflowEngine(context)
workflow.add_step(MyStep())

# Run
result = workflow.run()
```

## Core Classes

### StepResult

Encapsulates the result of a workflow step.

```python
from macro import StepResult

# Success
return StepResult.success("Message", data={"count": 5})

# Failure
return StepResult.failed("Error message", error=e)

# Skip
return StepResult.skipped("Skipped reason")
```

### StepContext

Shared context for workflow steps.

```python
from macro import StepContext

context = StepContext()
context.source_doc = doc
context.target_view = view
context.selected_elements = [elem_id1, elem_id2]

# Custom variables
context.set("my_key", "my_value")
value = context.get("my_key", "default")
```

### WorkflowStep (Abstract)

Base class for workflow steps.

```python
from macro import WorkflowStep, StepResult

class MyStep(WorkflowStep):
    name = "Step Name"
    description = "Description"
    requires_transaction = True  # Needs transaction?
    commit_after = True          # Commit after execution?
    optional = False             # Can be skipped?
    
    def validate(self, context):
        # Check prerequisites
        return StepResult.success("OK")
    
    def execute(self, context):
        # Do work
        return StepResult.success("Done")
    
    def rollback(self, context):
        # Optional rollback
        return StepResult.success("Rolled back")
```

### WorkflowEngine

Orchestrates workflow execution.

```python
from macro import WorkflowEngine, StepContext

workflow = WorkflowEngine(
    context=StepContext(),
    stop_on_failure=True,
    rollback_on_failure=True
)

# Add steps
workflow.add_step(StepOne())
workflow.add_step(StepTwo())

# Run all
result = workflow.run()

# Or run step by step
workflow.run_step(0)  # Run first step
```

## Workflow Steps for Copy Detail Elements

The pre-built `CopyDetailElementsWorkflow` includes these steps:

| Step | Name | Transaction | Commit | Description |
|------|------|-------------|--------|-------------|
| 1 | SelectDocumentsStep | ❌ | - | Select source and target documents |
| 2 | MatchViewsStep | ❌ | - | Find matching views by name |
| 3 | AutoSelectDetailElementsStep | ❌ | - | Auto-select all detail elements |
| 4 | SetWireframeStep | ✅ | ✅ | Set target view to wireframe |
| 5 | PasteElementsStep | ✅ | ✅ | Paste with "Aligned to current view" |
| 6 | FinalizeStep | ✅ | ✅ | Final commit and restore view |

**Important:** Steps 4, 5, and 6 all commit their transactions - this is critical for the copy operation to work correctly.

## Transaction Management

Each step can specify:

- `requires_transaction = True/False` - Whether the step needs a transaction
- `commit_after = True/False` - Whether to commit after execution

The workflow engine automatically handles:
- Creating transactions for steps that need them
- Committing or rolling back based on step configuration
- Managing transactions across different documents

## File Structure

```
lib/macro/
├── __init__.py                 # Package exports
├── step_result.py              # StepResult class
├── step_context.py             # StepContext and WorkflowVariables
├── workflow_step.py            # WorkflowStep base classes
├── workflow_engine.py          # WorkflowEngine orchestrator
└── workflows/
    ├── __init__.py
    └── copy_detail_elements.py # Pre-built workflow
```

## UI Integration

The workflow is exposed as a pyRevit button:

```
PrasKaaPyKit.tab/
└── Automation.panel/
    └── CopyDetailElements.pushbutton/
        ├── bundle.yaml
        └── script.py
```

## Error Handling

The framework provides comprehensive error handling:

- **Validation** - Check prerequisites before execution
- **Transactions** - Automatic commit/rollback
- **Results** - Detailed success/failure information
- **Logging** - Integration with pyRevit output

```python
result = workflow.run()

if result.is_success():
    # Handle success
    data = result.data
    
elif result.is_failed():
    # Handle failure
    error = result.error
    message = result.message
    
elif result.is_cancelled():
    # Handle cancellation
    pass
```

## Extending the Framework

### Custom Step with Transaction

```python
class MyTransactionalStep(WorkflowStep):
    name = "My Transaction"
    requires_transaction = True
    commit_after = True
    
    def execute_inside_transaction(self, context):
        # Your logic here - runs inside transaction
        return StepResult.success("Done")
```

### Custom Simple Step

```python
class MySimpleStep(WorkflowStep):
    name = "My Simple Step"
    requires_transaction = False
    
    def run(self, context):
        # No transaction needed
        return StepResult.success("Done")
```

## Version

- **Version:** 1.0.0
- **Author:** PrasKaa

## See Also

- [SPEC.md](../../plans/MacroWorkflow_SPEC.md) - Full specification
- [ARCHITECTURE_GUIDE.md](../../ARCHITECTURE_GUIDE.md) - Project architecture
- [revit-transaction-rules.md](../../rules/revit-transaction-rules.md) - Transaction best practices
