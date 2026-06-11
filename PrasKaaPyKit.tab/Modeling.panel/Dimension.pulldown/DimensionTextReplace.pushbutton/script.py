# -*- coding: utf-8 -*-
"""
Dimension Text Override Find & Replace
Find and replace text in dimension text overrides across the project.

Author: PrasKaa
Version: 1.0.1
Last Updated: 2026-02-19

Changelog:
    v1.0.1 (2026-02-19): QA fixes - reduced console output, added worksharing check
    v1.0.0 (2026-02-19): Initial release
"""
__title__ = 'Text Replace'
__author__ = 'PrasKaa'
__doc__ = "Find and replace text in dimension overrides."

import re
import sys

# pyRevit imports
from pyrevit import revit, DB, forms, script
from Autodesk.Revit.DB import Dimension, Transaction, FilteredElementCollector
from Autodesk.Revit.DB import WorksharingUtils, CheckoutStatus

# Get document and UI
doc = revit.doc
uidoc = revit.uidoc
output = script.get_output()


def is_editable(element, doc):
    """
    Check if element is editable in workshared file.

    Args:
        element: Revit element
        doc: Active document

    Returns:
        bool: True if element can be modified
    """
    if not doc.IsWorkshared:
        return True
    try:
        status = WorksharingUtils.GetCheckoutStatus(doc, element.Id)
        return status in (CheckoutStatus.OwnedByCurrentUser, CheckoutStatus.Unowned)
    except:
        return False


def has_text_override(dimension):
    """
    Check if dimension has any text override.
    """
    try:
        return bool(
            dimension.Above or
            dimension.Below or
            dimension.Prefix or
            dimension.Suffix or
            dimension.ValueOverride
        )
    except:
        return False


def get_override_texts(dimension):
    """
    Get all override text from a dimension.
    """
    overrides = {}
    try:
        if dimension.Above:
            overrides['Above'] = dimension.Above
        if dimension.Below:
            overrides['Below'] = dimension.Below
        if dimension.Prefix:
            overrides['Prefix'] = dimension.Prefix
        if dimension.Suffix:
            overrides['Suffix'] = dimension.Suffix
        if dimension.ValueOverride:
            overrides['ValueOverride'] = dimension.ValueOverride
    except:
        pass
    return overrides


def find_matches(dimension, find_text, case_sensitive=True):
    """
    Find text matches in dimension overrides.
    """
    matches = {}
    overrides = get_override_texts(dimension)
    
    for prop, value in overrides.items():
        if case_sensitive:
            if find_text in value:
                matches[prop] = value
        else:
            if find_text.lower() in value.lower():
                matches[prop] = value
    
    return matches


def apply_replacement(doc, dimension, find_text, replace_text, case_sensitive=True):
    """
    Apply find and replace to dimension overrides.
    """
    changes = {}
    matches = find_matches(dimension, find_text, case_sensitive)
    
    if not matches:
        return False, changes
    
    for prop, old_value in matches.items():
        if case_sensitive:
            new_value = old_value.replace(find_text, replace_text)
        else:
            pattern = re.compile(re.escape(find_text), re.IGNORECASE)
            new_value = pattern.sub(replace_text, old_value)
        
        if new_value != old_value:
            try:
                setattr(dimension, prop, new_value)
                changes[prop] = {'old': old_value, 'new': new_value}
            except Exception:
                pass
    
    return bool(changes), changes


def process_dimensions(doc, matching_dims, find_text, replace_text, case_sensitive):
    """
    Process dimensions with transaction safety.

    Args:
        doc: Active document
        matching_dims: List of (dimension, matches) tuples
        find_text: Text to find
        replace_text: Text to replace with
        case_sensitive: Case sensitivity

    Returns:
        tuple: (modified_count, error_count, skipped_count)
    """
    modified_count = 0
    error_count = 0
    skipped_count = 0
    
    t = Transaction(doc, "Dimension Text Override Replace")
    t.Start()
    
    try:
        with forms.ProgressBar(
            title='Replacing text ({value} of {max_value})',
            cancellable=True
        ) as pb:
            
            for idx, (dim, matches) in enumerate(matching_dims):
                if pb.cancelled:
                    break
                
                if not is_editable(dim, doc):
                    skipped_count += 1
                    continue
                
                success, changes = apply_replacement(
                    doc, dim, find_text, replace_text, case_sensitive)
                
                if success:
                    modified_count += 1
                else:
                    error_count += 1
                
                pb.update_progress(idx + 1, len(matching_dims))
        
        t.Commit()
        
    except Exception as e:
        t.RollBack()
        forms.alert("Transaction failed:\n{}".format(str(e)), exitscript=True)
        return 0, 0, 0
    
    return modified_count, error_count, skipped_count


def main():
    """Main execution function."""
    active_view = uidoc.ActiveView
    if not active_view:
        forms.alert("No active view found.", exitscript=True)
    
    # Scope Selection
    scope_options = [
        "Active View ({})".format(active_view.Name),
        "Selected Dimensions",
        "Entire Document"
    ]
    
    scope_choice = forms.CommandSwitchWindow.show(
        scope_options,
        message="Select scope for dimension search:"
    )
    
    if not scope_choice:
        return
    
    # Determine scope
    if "Selected" in scope_choice:
        scope = 'selection'
    elif "Document" in scope_choice:
        scope = 'document'
    else:
        scope = 'view'
    
    # Collect dimensions
    dimensions = collect_dimensions_with_overrides(doc, uidoc, scope)
    
    if not dimensions:
        forms.alert(
            "No dimensions with text overrides found.\n\n"
            "This tool only finds dimensions that have text overrides.\n"
            "Check: Select dimension → Properties panel → Value Override",
            title="No Dimensions Found"
        )
        return
    
    # Get find text
    find_text = forms.ask_for_string(
        prompt="Text to FIND:",
        title="Find Text",
        default=""
    )
    
    if not find_text:
        return
    
    # Get replace text
    replace_text = forms.ask_for_string(
        prompt="Text to REPLACE with (leave empty to delete):",
        title="Replace Text",
        default=""
    )
    
    if replace_text is None:
        return
    
    # Case sensitivity
    case_sensitive = forms.alert(
        "Case sensitive search?\n\n"
        "Yes = Exact match only\n"
        "No = Match any case",
        yes=True,
        no=True,
        exitscript=False
    )
    
    # Find matching dimensions
    matching_dims = []
    for dim in dimensions:
        matches = find_matches(dim, find_text, case_sensitive)
        if matches:
            matching_dims.append((dim, matches))
    
    if not matching_dims:
        forms.alert(
            "No dimensions found containing '{}'.".format(find_text),
            title="No Matches"
        )
        return
    
    # Show preview in console
    output.print_md("**Preview** - {} dimensions will be modified:".format(len(matching_dims)))
    preview_count = 0
    for dim, matches in matching_dims:
        if preview_count >= 10:
            output.print_md("*... and more ...*")
            break
        dim_id = dim.Id.IntegerValue
        for prop, old_val in matches.items():
            if case_sensitive:
                new_val = old_val.replace(find_text, replace_text)
            else:
                pattern = re.compile(re.escape(find_text), re.IGNORECASE)
                new_val = pattern.sub(replace_text, old_val)
            output.print_md("  {}: `{}` → `{}`".format(prop, old_val, new_val))
        preview_count += 1
    
    # Confirm
    confirm = forms.alert(
        "Modify {} dimensions?\n\nFIND: '{}'\nREPLACE: '{}'".format(
            len(matching_dims), find_text, replace_text if replace_text else '(empty)'),
        yes=True,
        no=True,
        title="Confirm Changes"
    )
    
    if not confirm:
        return
    
    # Process
    modified, errors, skipped = process_dimensions(
        doc, matching_dims, find_text, replace_text, case_sensitive)
    
    # Report results
    if skipped > 0:
        forms.alert(
            "Complete!\n\nModified: {}\nErrors: {}\nSkipped (owned by other): {}".format(
                modified, errors, skipped),
            title="Done"
        )
    elif errors > 0:
        forms.alert(
            "Complete with errors!\n\nModified: {}\nErrors: {}".format(modified, errors),
            title="Done"
        )
    else:
        forms.alert(
            "Successfully modified {} dimensions.".format(modified),
            title="Done"
        )


# Collect functions - pass doc/uidoc as parameters
def collect_dimensions_with_overrides(doc, uidoc, scope='view'):
    """
    Collect dimensions with text overrides based on scope.
    """
    from Autodesk.Revit.DB import Dimension, FilteredElementCollector
    
    if scope == 'selection':
        try:
            selected_ids = uidoc.Selection.GetElementIds()
        except:
            return []
        
        dimensions = []
        for elem_id in selected_ids:
            elem = doc.GetElement(elem_id)
            if isinstance(elem, Dimension):
                dimensions.append(elem)
    
    elif scope == 'document':
        dimensions = FilteredElementCollector(doc) \
            .OfClass(Dimension) \
            .WhereElementIsNotElementType() \
            .ToElements()
    
    else:  # 'view'
        active_view = uidoc.ActiveView
        if not active_view:
            return []
        dimensions = FilteredElementCollector(doc, active_view.Id) \
            .OfClass(Dimension) \
            .WhereElementIsNotElementType() \
            .ToElements()
    
    return [d for d in dimensions if has_text_override(d)]


if __name__ == '__main__':
    main()
