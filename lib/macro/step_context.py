# -*- coding: utf-8 -*-
"""
StepContext - Shared context for workflow steps

Provides a container for sharing data between workflow steps,
including documents, views, selected elements, and custom variables.
"""

from collections import defaultdict

try:
    from Autodesk.Revit.DB import Document, ElementId
    REVIT_AVAILABLE = True
except ImportError:
    REVIT_AVAILABLE = False
    Document = object
    ElementId = int


class WorkflowVariables:
    """
    Key-value store for workflow state.
    
    Provides a simple dictionary-like interface for storing
    and retrieving workflow-level variables.
    
    Usage:
        context.variables.set("my_key", "my_value")
        value = context.variables.get("my_key", "default")
    """
    
    def __init__(self):
        """Initialize empty variables store."""
        self._data = {}
    
    def get(self, key, default=None):
        """
        Get variable value.
        
        Args:
            key (str): Variable key
            default: Default value if key not found
        
        Returns:
            Variable value or default
        """
        return self._data.get(key, default)
    
    def set(self, key, value):
        """
        Set variable value.
        
        Args:
            key (str): Variable key
            value: Variable value
        """
        self._data[key] = value
    
    def has(self, key):
        """
        Check if key exists.
        
        Args:
            key (str): Variable key
        
        Returns:
            bool: True if key exists
        """
        return key in self._data
    
    def remove(self, key):
        """
        Remove variable.
        
        Args:
            key (str): Variable key
        """
        if key in self._data:
            del self._data[key]
    
    def clear(self):
        """Clear all variables."""
        self._data.clear()
    
    def to_dict(self):
        """
        Get all variables as dictionary.
        
        Returns:
            dict: Copy of all variables
        """
        return self._data.copy()
    
    def __repr__(self):
        return "WorkflowVariables({})".format(self._data)


class StepContext:
    """
    Shared context passed between workflow steps.
    
    This class holds all the data that needs to be shared
    between different steps in a workflow, including:
    - Source and target documents
    - Source and target views
    - Selected elements
    - Custom variables
    
    Attributes:
        source_doc: Source Revit document
        target_doc: Target Revit document
        source_view: Source view
        target_view: Target view
        selected_elements: List of selected ElementId
        variables: WorkflowVariables instance
    
    Usage:
        context = StepContext()
        context.source_doc = doc
        context.target_view = view
        context.selected_elements = [elem_id1, elem_id2]
    """
    
    def __init__(self):
        """Initialize StepContext with default values."""
        # Document references
        self.source_doc = None
        self.target_doc = None
        
        # View references
        self.source_view = None
        self.target_view = None
        
        # Element references
        self.selected_elements = []
        
        # Custom variables store
        self.variables = WorkflowVariables()
        
        # Internal storage for transactions and state
        self._internal = defaultdict(dict)
    
    def get(self, key, default=None):
        """
        Get context value (shortcut to variables).
        
        Args:
            key (str): Variable key
            default: Default value if key not found
        
        Returns:
            Variable value or default
        """
        return self.variables.get(key, default)
    
    def set(self, key, value):
        """
        Set context value (shortcut to variables).
        
        Args:
            key (str): Variable key
            value: Variable value
        """
        self.variables.set(key, value)
    
    def has_key(self, key):
        """
        Check if key exists (shortcut to variables).
        
        Args:
            key (str): Variable key
        
        Returns:
            bool: True if key exists
        """
        return self.variables.has(key)
    
    def get_document_by_name(self, doc_name):
        """
        Get open document by name.
        
        Args:
            doc_name (str): Document title/name
        
        Returns:
            Document or None if not found
        """
        if not REVIT_AVAILABLE:
            return None
        
        from pyrevit import revit
        for doc in list(revit.docs):
            if doc.Title == doc_name:
                return doc
        return None
    
    def find_matching_view(self, source_view_name, target_doc=None):
        """
        Find view with same name in target document.
        
        Args:
            source_view_name (str): Name of view to find
            target_doc: Target document (uses target_doc if None)
        
        Returns:
            View or None if not found
        """
        if not REVIT_AVAILABLE:
            return None
        
        if target_doc is None:
            target_doc = self.target_doc
        
        if not target_doc or not source_view_name:
            return None
        
        from Autodesk.Revit.DB import View, FilteredElementCollector
        
        # Get all views in target document
        target_views = FilteredElementCollector(target_doc)\
            .OfClass(View)\
            .WhereElementIsNotElementType()\
            .ToElements()
        
        for view in target_views:
            if _get_view_name(view) == source_view_name:
                return view
        return None
    
    def get_view_specific_elements(self, view, element_type=None):
        """
        Get all view-specific elements in a view.
        
        Args:
            view: The view to get elements from
            element_type: Optional element type filter
        
        Returns:
            List of ElementId
        """
        if not REVIT_AVAILABLE or not view:
            return []
        
        # Use source_doc if available, otherwise try view.Document
        doc = self.source_doc
        if not doc:
            try:
                doc = view.Document
            except:
                pass
        
        if not doc:
            return []
        
        from Autodesk.Revit.DB import FilteredElementCollector
        
        collector = FilteredElementCollector(doc, view.Id)
        
        if element_type:
            collector.OfClass(element_type)
        
        # Filter for view-specific elements only
        elements = collector.WhereElementIsNotElementType().ToElements()
        view_specific = [
            elem.Id for elem in elements
            if elem.ViewSpecific and elem.GroupId == elem.GroupId.InvalidElementId
        ]
        
        return view_specific
    
    def get_element_count(self):
        """
        Get count of selected elements.
        
        Returns:
            int: Number of selected elements
        """
        if self.selected_elements:
            return len(self.selected_elements)
        return 0


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
