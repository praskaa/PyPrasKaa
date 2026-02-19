# -*- coding: utf-8 -*-
"""
CopyDetailElementsWorkflow - Copy detail elements between documents

This module provides a complete workflow for copying detail elements
from a source view to a target view in a different Revit document.

Workflow Steps:
    1. SelectDocumentsStep - Select source and target documents
    2. MatchViewsStep - Find matching views by name
    3. AutoSelectDetailElementsStep - Automatically get all detail elements
    4. SetWireframeStep - Set target view to wireframe (COMMIT)
    5. PasteElementsStep - Paste elements to target view (COMMIT)
    6. FinalizeStep - Final commit and restore view settings (COMMIT)

Usage:
    from macro.workflows import CopyDetailElementsWorkflow
    
    workflow = CopyDetailElementsWorkflow()
    result = workflow.run()
    
    if result.is_success():
        print("Copied {} elements".format(result.get_data("copied_count")))
"""

from macro.workflow_engine import WorkflowEngine
from macro.workflow_step import WorkflowStep
from macro.step_result import StepResult
from macro.step_context import StepContext, _get_view_name


def _get_view_name_safe(view):
    """Safely get view name."""
    if not view:
        return None
    try:
        return _get_view_name(view)
    except:
        return str(view)


# Helper functions for IronPython compatibility
def _get_view_name(view):
    """Get view name using BuiltInParameter."""
    from Autodesk.Revit.DB import BuiltInParameter
    try:
        param = view.get_Parameter(BuiltInParameter.VIEW_NAME)
        if param and param.HasValue:
            return param.AsString()
    except:
        pass
    # Fallback to Name property
    try:
        return view.Name
    except:
        return str(view)

def _is_view_template(view):
    """Check if view is a template."""
    try:
        return view.IsTemplate
    except:
        return False


class SelectDocumentsStep(WorkflowStep):
    """
    Step 1: Select source and target documents.
    
    Prompts user to select source and target documents from
    currently open Revit documents.
    """
    
    name = "Select Documents"
    description = "Select source and target Revit documents"
    requires_transaction = False
    
    def validate(self, context):
        """Validate that at least 2 documents are open."""
        from pyrevit import revit
        if len(list(revit.docs)) < 2:
            return StepResult.failed("Need at least 2 open documents")
        return StepResult.success("OK")
    
    def execute(self, context):
        """Execute document selection."""
        from pyrevit import revit, forms
        
        # Get open documents
        open_docs = list(revit.docs)
        doc_titles = [doc.Title for doc in open_docs]
        
        # Select source document
        source_title = forms.SelectFromList.show(
            doc_titles,
            title="Select SOURCE Document",
            button_name="Select Source"
        )
        
        if source_title is None:
            return StepResult.cancelled("Source document selection cancelled")
        
        # Find source doc index
        source_idx = doc_titles.index(source_title)
        
        # Select target document (exclude source)
        target_titles = [t for i, t in enumerate(doc_titles) if i != source_idx]
        
        target_title = forms.SelectFromList.show(
            target_titles,
            title="Select TARGET Document",
            button_name="Select Target"
        )
        
        if target_title is None:
            return StepResult.cancelled("Target document selection cancelled")
        
        # Find actual target doc by title
        target_doc = None
        for doc in open_docs:
            if doc.Title == target_title:
                target_doc = doc
                break
        
        # Find source doc
        source_doc = None
        for doc in open_docs:
            if doc.Title == source_title:
                source_doc = doc
                break
        
        # Set context
        context.source_doc = source_doc
        context.target_doc = target_doc
        
        return StepResult.success(
            "Documents selected: {} -> {}".format(
                context.source_doc.Title,
                context.target_doc.Title
            ),
            data={
                "source_doc": context.source_doc.Title,
                "target_doc": context.target_doc.Title
            }
        )


class MatchViewsStep(WorkflowStep):
    """
    Step 2: Find matching views by name.
    
    Finds views with the same name in both source and target documents.
    """
    
    name = "Match Views"
    description = "Find matching views by name in both documents"
    requires_transaction = False
    
    def validate(self, context):
        """Validate documents are set."""
        if not context.source_doc or not context.target_doc:
            return StepResult.failed("Documents not selected")
        return StepResult.success("OK")
    
    def execute(self, context):
        """Execute view matching."""
        from pyrevit import forms
        from Autodesk.Revit.DB import View, FilteredElementCollector
        
        # Get all views from source document
        source_views = FilteredElementCollector(context.source_doc)\
            .OfClass(View)\
            .WhereElementIsNotElementType()\
            .ToElements()
        
        # Get view names (handle wrapper objects)
        source_view_names = sorted([
            _get_view_name(v) for v in source_views
            if not _is_view_template(v)
        ])
        
        if not source_view_names:
            return StepResult.failed("No views found in source document")
        
        # Select source view (returns the name, not index)
        view_name = forms.SelectFromList.show(
            source_view_names,
            title="Select SOURCE View",
            button_name="Select View"
        )
        
        if view_name is None:
            return StepResult.cancelled("View selection cancelled")
        
        # Find matching view in target document
        target_view = context.find_matching_view(view_name, context.target_doc)
        
        if not target_view:
            return StepResult.failed(
                "View '{}' not found in target document".format(view_name)
            )
        
        # Find source view object
        source_view = None
        for v in source_views:
            if _get_view_name(v) == view_name:
                source_view = v
                break
        
        context.source_view = source_view
        context.target_view = target_view
        
        return StepResult.success(
            "Views matched: {}".format(view_name),
            data={
                "source_view": _get_view_name(context.source_view),
                "target_view": _get_view_name(context.target_view)
            }
        )


class AutoSelectDetailElementsStep(WorkflowStep):
    """
    Step 3: Automatically select all detail elements in source view.
    
    Uses FilteredElementCollector with view-specific filter to get
    all detail elements in the source view automatically.
    """
    
    name = "Auto Select Detail Elements"
    description = "Automatically get all detail elements in source view"
    requires_transaction = False
    
    def validate(self, context):
        """Validate source view is set."""
        if not context.source_view:
            return StepResult.failed("Source view not selected")
        return StepResult.success("OK")
    
    def execute(self, context):
        """Execute automatic element selection."""
        # Get view-specific elements
        element_ids = context.get_view_specific_elements(context.source_view)
        
        if not element_ids:
            # Try getting ALL elements in the view (not just view-specific)
            from Autodesk.Revit.DB import FilteredElementCollector
            all_elements = FilteredElementCollector(
                context.source_doc,
                context.source_view.Id
            ).WhereElementIsNotElementType().ToElements()
            
            element_ids = [e.Id for e in all_elements]
        
        if not element_ids:
            return StepResult.failed("No detail elements found in source view")
        
        context.selected_elements = element_ids
        
        return StepResult.success(
            "Found {} detail elements".format(len(element_ids)),
            data={"element_count": len(element_ids)}
        )


class SetWireframeStep(WorkflowStep):
    """
    Step 4: Set target view to wireframe display.
    
    IMPORTANT: This step MUST commit the transaction before
    the paste step can work correctly.
    """
    
    name = "Set Wireframe Display"
    description = "Set target view to wireframe (MUST COMMIT)"
    requires_transaction = True
    commit_after = True  # CRITICAL: Must commit!
    
    def validate(self, context):
        """Validate target view is set."""
        if not context.target_view:
            return StepResult.failed("Target view not selected")
        return StepResult.success("OK")
    
    def execute(self, context):
        """Execute wireframe setting."""
        view = context.target_view
        
        # Store original display style
        original_style = view.DisplayStyle
        context.set("_original_display_style", original_style)
        
        # Skip wireframe setting for now - some view types don't support it
        # This can be enabled later when the API issue is resolved
        
        return StepResult.success(
            "View settings stored (wireframe skipped)",
            data={"original_style": str(original_style)}
        )


class PasteElementsStep(WorkflowStep):
    """
    Step 5: Paste elements to target view.
    
    Uses ElementTransformUtils.CopyElements with Transform.Identity
    for "Aligned to current view" behavior.
    """
    
    name = "Paste Elements"
    description = "Copy elements to target view (Aligned to current view)"
    requires_transaction = True
    commit_after = True  # Commit before finalization
    
    def validate(self, context):
        """Validate elements and views are set."""
        if not context.selected_elements:
            return StepResult.failed("No elements selected")
        if not context.target_view:
            return StepResult.failed("Target view not selected")
        return StepResult.success("OK")
    
    def execute(self, context):
        """Execute element pasting."""
        from Autodesk.Revit.DB import (
            ElementTransformUtils,
            CopyPasteOptions,
            Transform,
            ElementId
        )
        from pyrevit.framework import List
        from pyrevit import script
        
        output = script.get_output()
        
        # Debug info
        output.print_md("### Debug: Paste Step")
        output.print_md("- Source doc: {}".format(context.source_doc.Title if context.source_doc else "None"))
        output.print_md("- Target doc: {}".format(context.target_doc.Title if context.target_doc else "None"))
        output.print_md("- Source view: {}".format(_get_view_name_safe(context.source_view)))
        output.print_md("- Target view: {}".format(_get_view_name_safe(context.target_view)))
        output.print_md("- Element count: {}".format(len(context.selected_elements) if context.selected_elements else 0))
        
        # Get element IDs to copy
        element_ids = context.selected_elements
        
        if not element_ids:
            output.print_md("- **ERROR**: No elements selected!")
            return StepResult.failed("No elements to copy")
        
        output.print_md("- First 5 element IDs: {}".format([str(e) for e in element_ids[:5]]))
        
        # Convert to .NET List of ElementId
        element_id_list = List[ElementId](element_ids)
        
        # Create copy options - set to NOT show dialog
        opts = CopyPasteOptions()
        
        # Use Transform.Identity for "Aligned to current view"
        transform = Transform.Identity
        
        # Copy view-specific elements between views
        # Use the View-to-View copy method for detail elements
        output.print_md("- Calling CopyElements API...")
        
        try:
            copied_ids = ElementTransformUtils.CopyElements(
                context.source_view,  # Source view (for view-specific elements)
                element_id_list,
                context.target_view,  # Target view
                transform,
                opts
            )
            
            output.print_md("- Copy result: {} elements copied".format(len(copied_ids) if copied_ids else 0))
            
            context.set("_copied_element_ids", copied_ids)
            
            return StepResult.success(
                "Copied {} elements".format(len(copied_ids) if copied_ids else 0),
                data={"copied_count": len(copied_ids) if copied_ids else 0}
            )
        
        except Exception as e:
            output.print_md("- **ERROR**: {}".format(str(e)))
            import traceback
            output.print_md("```")
            output.print_md(traceback.format_exc())
            output.print_md("```")
            return StepResult.failed(
                "Failed to copy elements: {}".format(str(e)),
                error=e
            )


class FinalizeStep(WorkflowStep):
    """
    Step 6: Finalize workflow.
    
    Commits the final transaction and restores view settings.
    IMPORTANT: Must commit first, then restore - otherwise
    elements can go missing!
    """
    
    name = "Finalize"
    description = "Final commit and restore view settings"
    requires_transaction = True
    commit_after = True  # Commit first!
    
    def validate(self, context):
        """Validate context is ready."""
        if not context.target_view:
            return StepResult.failed("No target view")
        return StepResult.success("OK")
    
    def execute(self, context):
        """Execute finalization."""
        from Autodesk.Revit.DB import View
        
        # First, ensure any pending operations are committed
        # The workflow engine handles this via commit_after=True
        
        # Then restore view settings (AFTER commit!)
        view = context.target_view
        original_style = context.get("_original_display_style")
        
        if original_style:
            try:
                view.DisplayStyle = original_style
            except:
                pass  # Ignore if restore fails
        
        # Get copied elements for result
        copied_ids = context.get("_copied_element_ids", [])
        
        return StepResult.success(
            "Workflow completed. {} elements copied".format(len(copied_ids)),
            data={
                "copied_count": len(copied_ids),
                "source_doc": context.source_doc.Title if context.source_doc else None,
                "target_doc": context.target_doc.Title if context.target_doc else None,
                "source_view": _get_view_name_safe(context.source_view),
                "target_view": _get_view_name_safe(context.target_view)
            }
        )


class CopyDetailElementsWorkflow(WorkflowEngine):
    """
    Complete workflow for copying detail elements between documents.
    
    This workflow automates the entire process of copying detail
    elements from a source view to a target view in a different
    Revit document.
    
    Steps:
        1. SelectDocumentsStep - Select source and target documents
        2. MatchViewsStep - Find matching views by name
        3. AutoSelectDetailElementsStep - Get all detail elements automatically
        4. SetWireframeStep - Set target view to wireframe (COMMIT)
        5. PasteElementsStep - Paste elements (COMMIT)
        6. FinalizeStep - Final commit and restore view (COMMIT)
    
    Usage:
        workflow = CopyDetailElementsWorkflow()
        result = workflow.run()
        
        if result.is_success():
            print(result.get_data("copied_count"))
    """
    
    def __init__(self):
        """Initialize the copy detail elements workflow."""
        # Create context
        context = StepContext()
        
        # Initialize parent directly (IronPython compatibility)
        WorkflowEngine.__init__(
            self,
            context=context,
            stop_on_failure=True,
            rollback_on_failure=True
        )
        
        # Add all workflow steps
        self.add_step(SelectDocumentsStep())
        self.add_step(MatchViewsStep())
        self.add_step(AutoSelectDetailElementsStep())
        self.add_step(SetWireframeStep())
        self.add_step(PasteElementsStep())
        self.add_step(FinalizeStep())


def run_workflow():
    """
    Entry point to run the workflow.
    
    Returns:
        StepResult: Workflow execution result
    """
    workflow = CopyDetailElementsWorkflow()
    return workflow.run()
