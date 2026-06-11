# -*- coding: utf-8 -*-
"""
Linked Elements Utilities for Revit

Provides reusable functions for:
- Collecting Revit link instances
- Getting linked documents
- Checking tags on linked elements
- Getting references to linked elements for selection

IMPORTANT: This module handles the complexity of working with linked elements
in Revit, where element visibility and tagging work differently than host elements.

Usage:
    from linked_elements import (
        get_all_revti_link_instances,
        get_linked_document,
        get_untagged_linked_elements,
        get_tagged_linked_elements_from_view
    )

Related Documentation:
    - logic-library/active/utilities/linked-elements/
"""

from Autodesk.Revit.DB import *
from pyrevit import revit, forms


# ============================================================================
# Data Classes
# ============================================================================

class LinkedElementInfo:
    """
    Container for linked element data with reference info.
    
    Attributes:
        element (Element): The linked element
        link_instance (RevitLinkInstance): The RevitLinkInstance
        linked_doc (Document): The linked Document
    """
    
    def __init__(self, element, link_instance, linked_doc):
        """
        Initialize LinkedElementInfo.
        
        Args:
            element (Element): The linked element
            link_instance (RevitLinkInstance): The link instance
            linked_doc (Document): The linked document
        """
        self.element = element
        self.link_instance = link_instance
        self.linked_doc = linked_doc
    
    @property
    def element_id(self):
        """Get the element ID in the linked document."""
        return self.element.Id
    
    @property
    def link_instance_id(self):
        """Get the link instance ID in the host document."""
        return self.link_instance.Id
    
    @property
    def name(self):
        """Get element name with link name prefix."""
        link_name = self.link_instance.Name if self.link_instance else "Unknown"
        return "{0} :: {1}".format(link_name, self.element.Name)
    
    def __repr__(self):
        return "<LinkedElementInfo: {0}>".format(self.name)


# ============================================================================
# Core Functions - Link Instance Collection
# ============================================================================

def get_all_revti_link_instances(doc):
    """
    Get all Revit link instances in the document.
    
    Args:
        doc (Document): The host Revit document
        
    Returns:
        List[RevitLinkInstance]: All RevitLinkInstance elements found
        
    Example:
        >>> links = get_all_revti_link_instances(revit.doc)
        >>> for link in links:
        ...     print(link.Name)
        "Structure.rvt"
        "Architecture.rvt"
    """
    collector = FilteredElementCollector(doc)
    collector.OfClass(RevitLinkInstance)
    return list(collector)


def get_linked_document(link_instance):
    """
    Get the Document object from a RevitLinkInstance.
    
    Args:
        link_instance (RevitLinkInstance): The link instance
        
    Returns:
        Document: The linked Revit document, or None if unavailable
        
    Example:
        >>> links = get_all_revti_link_instances(revit.doc)
        >>> for link in links:
        ...     doc = get_linked_document(link)
        ...     if doc:
        ...         beams = FilteredElementCollector(doc).OfCategory(
        ...             OST_StructuralFraming
        ...         ).WhereElementIsNotElementType().ToElements()
    """
    try:
        return link_instance.GetLinkDocument()
    except Exception:
        return None


# ============================================================================
# Tag Checking Functions
# ============================================================================

def get_tagged_linked_elements_from_view(doc, view):
    """
    Get all linked elements that have tags in the specified view.
    
    This function collects all tags in a view and extracts the linked
    elements they reference. This is useful for identifying which linked
    elements are already tagged.
    
    Args:
        doc (Document): The host document
        view (View): The view to check
        
    Returns:
        dict: {(link_instance_id, linked_element_id): LinkedElementInfo}
              Mapping of tagged linked element pairs to their info
        
    Example:
        >>> tagged = get_tagged_linked_elements_from_view(
        ...     revit.doc,
        ...     revit.active_view
        ... )
        >>> len(tagged)
        15
        >>> (link_inst_id, elem_id) in tagged
        True
    """
    tagged = {}
    
    # Collect all tags in the view
    collector = FilteredElementCollector(doc, view.Id)
    collector.OfClass(IndependentTag)
    collector.WhereElementIsNotElementType()
    
    for tag in collector:
        try:
            # Get the tagged local element IDs (works for Revit 2023+)
            tagged_ids = tag.GetTaggedLocalElementIds()
            
            # Check if valid
            if tagged_ids is None or tagged_ids == ElementId.InvalidElementId:
                continue
            
            # Process each tagged ID
            for tagged_id in tagged_ids:
                # Check if this is a linked element (has LinkInstanceId)
                link_instance_id = tagged_id.LinkInstanceId
                
                if link_instance_id and link_instance_id != ElementId.InvalidElementId:
                    # This is a linked element
                    linked_element_id = tagged_id.LinkedElementId
                    
                    # Get the link instance
                    link_instance = doc.GetElement(link_instance_id)
                    
                    if link_instance:
                        linked_doc = get_linked_document(link_instance)
                        
                        if linked_doc:
                            element = linked_doc.GetElement(linked_element_id)
                            
                            if element:
                                info = LinkedElementInfo(element, link_instance, linked_doc)
                                tagged[(link_instance_id, linked_element_id)] = info
        
        except Exception:
            # Try older API as fallback
            try:
                if hasattr(tag, 'TaggedLocalElementId'):
                    tagged_id = tag.TaggedLocalElementId
                    
                    if tagged_id and tagged_id != ElementId.InvalidElementId:
                        link_instance_id = tagged_id.LinkInstanceId
                        
                        if link_instance_id and link_instance_id != ElementId.InvalidElementId:
                            linked_element_id = tagged_id.LinkedElementId
                            
                            link_instance = doc.GetElement(link_instance_id)
                            
                            if link_instance:
                                linked_doc = get_linked_document(link_instance)
                                
                                if linked_doc:
                                    element = linked_doc.GetElement(linked_element_id)
                                    
                                    if element:
                                        info = LinkedElementInfo(
                                            element, link_instance, linked_doc
                                        )
                                        tagged[(link_instance_id, linked_element_id)] = info
            except Exception:
                continue
    
    return tagged


def get_all_linked_elements_by_category(doc, category):
    """
    Collect ALL elements of a category from ALL linked documents.
    
    WARNING: This collects elements from ALL linked documents without
    filtering by view visibility. Use with caution on large models.
    
    Args:
        doc (Document): The host document
        category (BuiltInCategory): Category to collect
        
    Returns:
        List[LinkedElementInfo]: All linked elements of the category
        
    Example:
        >>> all_beams = get_all_linked_elements_by_category(
        ...     revit.doc,
        ...     OST_StructuralFraming
        ... )
        >>> len(all_beams)
        150
    """
    results = []
    
    # Get all link instances
    link_instances = get_all_revti_link_instances(doc)
    
    for link_instance in link_instances:
        linked_doc = get_linked_document(link_instance)
        
        if linked_doc is None:
            continue
        
        # Collect all elements of the category from linked doc
        collector = FilteredElementCollector(linked_doc)
        collector.OfCategory(category)
        collector.WhereElementIsNotElementType()
        
        for element in collector:
            info = LinkedElementInfo(element, link_instance, linked_doc)
            results.append(info)
    
    return results


def get_untagged_linked_elements(doc, view, category):
    """
    Get untagged elements from linked documents in a view.
    
    This function:
    1. Collects all elements of the category from all linked documents
    2. Gets all tagged linked elements from the view
    3. Returns only untagged elements
    
    Args:
        doc (Document): The host document
        view (View): The view to check
        category (BuiltInCategory): Category to collect
        
    Returns:
        List[LinkedElementInfo]: Untagged linked elements
        
    Example:
        >>> untagged = get_untagged_linked_elements(
        ...     revit.doc,
        ...     revit.active_view,
        ...     OST_StructuralFraming
        ... )
        >>> for info in untagged:
        ...     print(info.name)
        "Structure.rvt :: W24x76"
    """
    # Get all tagged linked elements in the view
    tagged = get_tagged_linked_elements_from_view(doc, view)
    
    # Get all linked elements of the category
    all_linked = get_all_linked_elements_by_category(doc, category)
    
    # Filter to untagged elements
    untagged = []
    
    for info in all_linked:
        key = (info.link_instance_id, info.element_id)
        
        if key not in tagged:
            untagged.append(info)
    
    return untagged


# ============================================================================
# Selection Functions
# ============================================================================

def get_references_for_selection(linked_elements):
    """
    Get Reference objects for selecting linked elements.
    
    Args:
        linked_elements (List[LinkedElementInfo]): List of linked elements
        
    Returns:
        List[Reference]: Reference objects for selection
        
    Example:
        >>> untagged = get_untagged_linked_elements(...)
        >>> refs = get_references_for_selection(untagged)
        >>> selection.set_to(refs)
    """
    references = []
    
    for info in linked_elements:
        try:
            reference = Reference(info.element)
            references.append(reference)
        except Exception:
            continue
    
    return references


def select_untagged_linked_elements(doc, view, category, show_message=True):
    """
    Select all untagged elements from linked documents in the view.
    
    Args:
        doc (Document): The host document
        view (View): The view to check
        category (BuiltInCategory): Category to collect
        show_message (bool): Whether to show result message
        
    Returns:
        int: Number of elements selected
        
    Example:
        >>> count = select_untagged_linked_elements(
        ...     revit.doc,
        ...     revit.active_view,
        ...     OST_StructuralFraming
        ... )
    """
    # Get untagged elements
    untagged = get_untagged_linked_elements(doc, view, category)
    
    if not untagged:
        if show_message:
            forms.alert(
                "No untagged linked elements found.",
                title="Linked Tag Check"
            )
        return 0
    
    # Get references
    refs = get_references_for_selection(untagged)
    
    if not refs:
        if show_message:
            forms.alert(
                "Could not create references for selection.",
                title="Selection Error"
            )
        return 0
    
    # Select in UI
    selection = revit.get_selection()
    selection.set_to(refs)
    
    if show_message:
        forms.alert(
            "Selected {0} untagged linked elements".format(len(untagged)),
            title="Linked Tag Finder"
        )
    
    return len(untagged)


# ============================================================================
# Host Document Functions (for combined checking)
# ============================================================================

def get_tagged_host_elements_from_view(doc, view):
    """
    Get all host elements that have tags in the specified view.
    
    Args:
        doc (Document): The document to check
        view (View): The view to check
        
    Returns:
        set: Set of tagged ElementIds
    """
    tagged_ids = set()
    
    # Collect all tags in view
    collector = FilteredElementCollector(doc, view.Id)
    collector.OfClass(IndependentTag)
    collector.WhereElementIsNotElementType()
    
    for tag in collector:
        try:
            tagged_local = tag.GetTaggedLocalElementIds()
            
            if tagged_local and tagged_local != ElementId.InvalidElementId:
                for tid in tagged_local:
                    # Only include non-linked elements
                    if tid.LinkInstanceId == ElementId.InvalidElementId:
                        tagged_ids.add(tid)
        except Exception:
            try:
                if hasattr(tag, 'TaggedLocalElementId'):
                    tid = tag.TaggedLocalElementId
                    if tid and tid != ElementId.InvalidElementId:
                        if tid.LinkInstanceId == ElementId.InvalidElementId:
                            tagged_ids.add(tid)
            except Exception:
                continue
    
    return tagged_ids


def get_untagged_host_elements(doc, view, category):
    """
    Get untagged elements from the host document.
    
    Args:
        doc (Document): The document to check
        view (View): The view to check
        category (BuiltInCategory): Category to check
        
    Returns:
        List[Element]: Untagged elements
    """
    # Get tagged elements
    tagged_ids = get_tagged_host_elements_from_view(doc, view)
    
    # Collect all elements of category in view
    collector = FilteredElementCollector(doc, view.Id)
    collector.OfCategory(category)
    collector.WhereElementIsNotElementType()
    
    untagged = []
    
    for elem in collector:
        if elem.Id not in tagged_ids:
            untagged.append(elem)
    
    return untagged


# ============================================================================
# Combined Functions
# ============================================================================

def find_missing_tags(doc, view, category, include_host=True, include_linked=True):
    """
    Find all untagged elements from host and/or linked documents.
    
    Args:
        doc (Document): The host document
        view (View): The view to check
        category (BuiltInCategory): Category to check
        include_host (bool): Include host document elements
        include_linked (bool): Include linked document elements
        
    Returns:
        dict: {
            'host': [Element, ...],  # Untagged host elements
            'linked': [LinkedElementInfo, ...],  # Untagged linked elements
            'total': int  # Total count
        }
        
    Example:
        >>> result = find_missing_tags(
        ...     revit.doc,
        ...     revit.active_view,
        ...     OST_StructuralFraming
        ... )
        >>> print("Host: {}, Linked: {}".format(
        ...     len(result['host']),
        ...     len(result['linked'])
        ... ))
    """
    result = {
        'host': [],
        'linked': [],
        'total': 0
    }
    
    # Check host document
    if include_host:
        result['host'] = get_untagged_host_elements(doc, view, category)
    
    # Check linked documents
    if include_linked:
        result['linked'] = get_untagged_linked_elements(doc, view, category)
    
    # Calculate total
    result['total'] = len(result['host']) + len(result['linked'])
    
    return result
