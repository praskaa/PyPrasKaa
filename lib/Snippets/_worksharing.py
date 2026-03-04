# -*- coding: utf-8 -*-
# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#==================================================
"""
Worksharing Utilities for Multi-User Revit Models.

This module provides utilities for checking and managing element ownership
in workshared Revit models. Essential for batch operations in collaborative
environments.

Usage:
    from Snippets._worksharing import is_element_editable, get_checkout_status

Author: PrasKaa
Version: 1.0.0
Last Updated: 2026-02-14
"""

# PYREVIT IMPORTS
from pyrevit import revit, DB

# REVIT API IMPORTS
from Autodesk.Revit.DB import WorksharingUtils, CheckoutStatus


# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#==================================================

def is_workshared(doc):
    """
    Check if the document is workshared.
    
    Args:
        doc: Revit Document
        
    Returns:
        bool: True if document is workshared, False otherwise
    """
    return doc.IsWorkshared


def get_checkout_status(element, doc):
    """
    Get the checkout status of an element.
    
    Args:
        element: Revit Element
        doc: Revit Document
        
    Returns:
        CheckoutStatus: One of:
            - OwnedByCurrentUser
            - OwnedByOtherUser
            - NotOwned
            - NotApplicable
    """
    return WorksharingUtils.GetCheckoutStatus(doc, element.Id)


def is_element_editable(element, doc):
    """
    Check if an element can be modified in the current workshared model.
    
    Args:
        element: Revit Element
        doc: Revit Document
        
    Returns:
        bool: True if element is editable, False if owned by another user
    """
    status = get_checkout_status(element, doc)
    return status != CheckoutStatus.OwnedByOtherUser


def is_element_owned_by_current_user(element, doc):
    """
    Check if element is owned by the current user.
    
    Args:
        element: Revit Element
        doc: Revit Document
        
    Returns:
        bool: True if owned by current user
    """
    status = get_checkout_status(element, doc)
    return status == CheckoutStatus.OwnedByCurrentUser


def is_element_owned_by_other_user(element, doc):
    """
    Check if element is owned by another user.
    
    Args:
        element: Revit Element
        doc: Revit Document
        
    Returns:
        bool: True if owned by another user
    """
    status = get_checkout_status(element, doc)
    return status == CheckoutStatus.OwnedByOtherUser


def is_element_not_owned(element, doc):
    """
    Check if element is not owned by anyone.
    
    Args:
        element: Revit Element
        doc: Revit Document
        
    Returns:
        bool: True if not owned
    """
    status = get_checkout_status(element, doc)
    return status == CheckoutStatus.NotOwned


def get_checkout_status_name(status):
    """
    Get human-readable name for checkout status.
    
    Args:
        status: CheckoutStatus enum value
        
    Returns:
        str: Human-readable status name
    """
    status_names = {
        CheckoutStatus.OwnedByCurrentUser: "Owned by Current User",
        CheckoutStatus.OwnedByOtherUser: "Owned by Other User",
        CheckoutStatus.NotOwned: "Not Owned",
        CheckoutStatus.NotApplicable: "Not Applicable"
    }
    return status_names.get(status, "Unknown")


def get_ownership_summary(elements, doc):
    """
    Get a summary of ownership status for a list of elements.
    
    Args:
        elements: List of Revit Elements
        doc: Revit Document
        
    Returns:
        dict: Dictionary with counts for each status
            {
                'owned_by_current': count,
                'owned_by_other': count,
                'not_owned': count,
                'not_applicable': count,
                'total': count
            }
    """
    summary = {
        'owned_by_current': 0,
        'owned_by_other': 0,
        'not_owned': 0,
        'not_applicable': 0,
        'total': len(elements)
    }
    
    for elem in elements:
        status = get_checkout_status(elem, doc)
        
        if status == CheckoutStatus.OwnedByCurrentUser:
            summary['owned_by_current'] += 1
        elif status == CheckoutStatus.OwnedByOtherUser:
            summary['owned_by_other'] += 1
        elif status == CheckoutStatus.NotOwned:
            summary['not_owned'] += 1
        else:
            summary['not_applicable'] += 1
    
    return summary


def filter_editable_elements(elements, doc):
    """
    Filter elements that can be edited (not owned by other users).
    
    Args:
        elements: List of Revit Elements
        doc: Revit Document
        
    Returns:
        list: Elements that can be edited
    """
    editable = []
    for elem in elements:
        if is_element_editable(elem, doc):
            editable.append(elem)
    return editable


def filter_owned_by_other(elements, doc):
    """
    Filter elements that are owned by other users.
    
    Args:
        elements: List of Revit Elements
        doc: Revit Document
        
    Returns:
        list: Elements owned by other users
    """
    owned_by_other = []
    for elem in elements:
        if is_element_owned_by_other_user(elem, doc):
            owned_by_other.append(elem)
    return owned_by_other


def get_editable_and_non_editable(elements, doc):
    """
    Separate elements into editable and non-editable categories.
    
    Args:
        elements: List of Revit Elements
        doc: Revit Document
        
    Returns:
        tuple: (editable_elements, non_editable_elements)
    """
    editable = []
    non_editable = []
    
    for elem in elements:
        if is_element_editable(elem, doc):
            editable.append(elem)
        else:
            non_editable.append(elem)
    
    return editable, non_editable


def print_ownership_report(elements, doc, element_name_func=None):
    """
    Print a detailed ownership report for elements.
    
    Args:
        elements: List of Revit Elements
        doc: Revit Document
        element_name_func: Optional function to get element name (default: uses ElementId)
    """
    if element_name_func is None:
        def element_name_func(e):
            return "Element #{}".format(e.Id.IntegerValue)
    
    print("\n" + "="*60)
    print("WORKSHARING OWNERSHIP REPORT")
    print("="*60)
    
    # Group elements by status
    owned_current = []
    owned_other = []
    not_owned = []
    not_applicable = []
    
    for elem in elements:
        status = get_checkout_status(elem, doc)
        
        if status == CheckoutStatus.OwnedByCurrentUser:
            owned_current.append(elem)
        elif status == CheckoutStatus.OwnedByOtherUser:
            owned_other.append(elem)
        elif status == CheckoutStatus.NotOwned:
            not_owned.append(elem)
        else:
            not_applicable.append(elem)
    
    # Print summary
    print("\nSUMMARY:")
    print("-" * 40)
    print("Total Elements:    {}".format(len(elements)))
    print("Owned by You:      {}".format(len(owned_current)))
    print("Owned by Others:   {}".format(len(owned_other)))
    print("Not Owned:          {}".format(len(not_owned)))
    print("Not Applicable:    {}".format(len(not_applicable)))
    
    # Print details for owned by others
    if owned_other:
        print("\n" + "-" * 40)
        print("ELEMENTS OWNED BY OTHER USERS:")
        print("-" * 40)
        for elem in owned_other:
            print("  - {} ({})".format(element_name_func(elem), elem.Id))
    
    print("\n" + "="*60 + "\n")


def batch_modify_with_worksharing_check(elements, doc, modify_func, 
                                          skip_owned_by_others=True,
                                          report_progress=False):
    """
    Modify elements with worksharing status check.
    
    Args:
        elements: List of Revit Elements to modify
        doc: Revit Document
        modify_func: Function to apply to each element (should accept element and doc)
        skip_owned_by_others: If True, skip elements owned by other users
        report_progress: If True, print progress messages
        
    Returns:
        dict: Results with 'success', 'skipped', and 'failed' counts
    """
    from Autodesk.Revit.DB import Transaction
    
    results = {
        'success': 0,
        'skipped_owned_by_others': 0,
        'skipped_not_workshared': 0,
        'failed': 0,
        'failed_elements': []
    }
    
    # Filter elements based on settings
    elements_to_modify = []
    
    for elem in elements:
        if skip_owned_by_others:
            status = get_checkout_status(elem, doc)
            
            if status == CheckoutStatus.OwnedByOtherUser:
                results['skipped_owned_by_others'] += 1
                continue
            elif not doc.IsWorkshared:
                # In non-workshared, all elements are editable
                pass
        
        elements_to_modify.append(elem)
    
    if not elements_to_modify:
        if report_progress:
            print("No elements to modify after filtering.")
        return results
    
    # Perform modification in a single transaction
    t = Transaction(doc, "Batch Modify with Worksharing Check")
    t.Start()
    
    try:
        for elem in elements_to_modify:
            try:
                modify_func(elem, doc)
                results['success'] += 1
                
                if report_progress:
                    print("Modified element: {}".format(elem.Id))
                    
            except Exception as e:
                results['failed'] += 1
                results['failed_elements'].append((elem.Id, str(e)))
                
                if report_progress:
                    print("Failed to modify element {}: {}".format(elem.Id, str(e)))
        
        t.Commit()
        
        if report_progress:
            print("\nBatch modification complete:")
            print("  Success: {}".format(results['success']))
            print("  Skipped (owned by others): {}".format(results['skipped_owned_by_others']))
            print("  Failed: {}".format(results['failed']))
            
    except Exception as e:
        t.RollBack()
        results['failed'] += len(elements_to_modify)
        results['failed_elements'].append((None, "Transaction failed: " + str(e)))
        
        if report_progress:
            print("Transaction failed and rolled back: {}".format(str(e)))
    
    return results


# ╔═╗╔═╗╔╦╗  ╔═╗╔═╗╦  ╔═╗╔═╗╔╦╗╔═╗╔╦╗
# ║ ╦║╣  ║   ╚═╗║╣ ║  ║╣ ║   ║ ║╣  ║║
# ╚═╝╚═╝ ╩   ╚═╝╚═╝╩═╝╚═╝╚═╝ ╩ ╚═╝═╩╝
#==================================================
# Example usage and testing (uncomment to test)
# def test_worksharing():
#     """Test function to verify worksharing utilities."""
#     doc = revit.doc
#     
#     if not is_workshared(doc):
#         print("Document is not workshared. Worksharing features not applicable.")
#         return
#     
#     # Get selected elements
#     from pyrevit import revit
#     selection = revit.uidoc.Selection.GetElementIds()
#     elements = [doc.GetElement(eid) for eid in selection]
#     
#     if not elements:
#         print("No elements selected.")
#         return
#     
#     # Test various functions
#     print("Testing worksharing utilities...")
#     print("Is workshared: {}".format(is_workshared(doc)))
#     
#     summary = get_ownership_summary(elements, doc)
#     print("Ownership Summary: {}".format(summary))
#     
#     editable, non_editable = get_editable_and_non_editable(elements, doc)
#     print("Editable: {}, Non-editable: {}".format(len(editable), len(non_editable)))
