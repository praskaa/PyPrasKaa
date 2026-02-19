# -*- coding: utf-8 -*-
"""
Copy Detail Elements - pyRevit Macro Workflow

This script copies detail elements from a source view in one document
to a matching view in another document using a multi-step workflow
with proper transaction management.

Workflow Steps:
    1. Select source and target documents
    2. Match views by name
    3. Auto-select detail elements in source view
    4. Set target view to wireframe (COMMIT REQUIRED)
    5. Paste elements with "Aligned to current view"
    6. Finalize (COMMIT first, then restore view)

Author: PrasKaa
Version: 1.0.0
"""

# pyRevit imports
from pyrevit import revit, DB, forms, script

# Macro workflow imports
from macro.workflows import CopyDetailElementsWorkflow
from macro.step_result import StepStatus


# Get output for logging
output = script.get_output()


def log_step(step_name, result):
    """Log step result to output."""
    if result.is_success():
        output.log_success(":white_check_mark: {}: {}".format(
            step_name,
            result.message
        ))
    elif result.is_failed():
        output.log_error(":x: {}: {}".format(
            step_name,
            result.message
        ))
    elif result.is_cancelled():
        output.log_warning(":warning: {}: Cancelled".format(step_name))
    else:
        output.log_info("{}: {}".format(step_name, result.message))


def main():
    """Main entry point for the script."""
    output.print_md("# 📋 Copy Detail Elements Workflow")
    output.print_md("---")
    
    # Check if multiple documents are open
    docs = list(revit.docs)
    if len(docs) < 2:
        output.log_error(
            ":x: Need at least 2 open Revit documents!\n"
            "Please open the source and target documents first."
        )
        forms.alert(
            "Need at least 2 open documents.\n"
            "Please open both the source and target documents.",
            title="Copy Detail Elements"
        )
        return
    
    output.log_info(":information_source: Found {} open documents".format(len(docs)))
    
    # Create and run workflow
    workflow = CopyDetailElementsWorkflow()
    
    # Add progress tracking
    output.print_md("## Starting Workflow...")
    
    # Run the workflow
    result = workflow.run()
    
    # Process results
    output.print_md("---")
    output.print_md("## Results")
    
    # Log each step
    output.print_md("### Step Results:")
    for i, step_result in enumerate(workflow.results):
        step = workflow.get_step(i)
        log_step("{}. {}".format(i + 1, step.name), step_result)
    
    output.print_md("---")
    
    # Final result
    if result.is_success():
        # Get summary data
        data = result.data or {}
        copied_count = data.get("copied_count", 0)
        source_doc = data.get("source_doc", "N/A")
        target_doc = data.get("target_doc", "N/A")
        target_view = data.get("target_view", "N/A")
        
        output.log_success(
            ":white_check_mark: Workflow completed successfully!"
        )
        
        output.print_md("### Summary")
        output.print_md("- **Elements copied:** {}".format(copied_count))
        output.print_md("- **Source:** {}".format(source_doc))
        output.print_md("- **Target:** {}".format(target_doc))
        output.print_md("- **Target View:** {}".format(target_view))
        
        forms.alert(
            "Successfully copied {} detail elements!\n\n"
            "From: {}\n"
            "To: {} > {}".format(
                copied_count,
                source_doc,
                target_doc,
                target_view
            ),
            title="Copy Detail Elements - Success"
        )
    
    elif result.is_failed():
        output.log_error(":x: Workflow failed: {}".format(result.message))
        
        # Show error details
        if result.error:
            output.print_md("### Error Details")
            output.print_code(str(result.error))
        
        forms.alert(
            "Workflow failed: {}".format(result.message),
            title="Copy Detail Elements - Error"
        )
    
    elif result.is_cancelled():
        output.log_warning(":warning: Workflow cancelled by user")
        output.print_md("Workflow was cancelled.")
    
    output.print_md("---")
    output.print_md(":OK_hand: Done")


if __name__ == "__main__":
    main()
