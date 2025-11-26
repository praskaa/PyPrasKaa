# -*- coding: utf-8 -*-
"""
Clear Framing Comments - Remove Dimension Validation Comments
"""

__title__ = 'Clear Framing Comments'
__author__ = 'PrasKaa Team'
__doc__ = "Removes dimension validation comments from framing elements."

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Transaction,
    TransactionStatus,
    BuiltInParameter
)

from pyrevit import revit, forms, script

# Setup
doc = revit.doc
output = script.get_output()

# Comments to clear
COMMENTS_TO_CLEAR = ["Approved", "Dimension to be checked", "Unmatched", "Family unmatched"]


def collect_host_beams():
    """Collects structural framing elements from the host Revit model."""
    host_beams = FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_StructuralFraming)\
        .WhereElementIsNotElementType()\
        .ToElements()
    return host_beams


def clear_comment_if_validation_result(beam):
    """Clears the comment parameter if it contains a validation result."""
    try:
        comments_param = beam.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        if not comments_param or comments_param.IsReadOnly:
            return False

        if not comments_param.HasValue:
            return False

        current_comment = comments_param.AsString()
        if current_comment in COMMENTS_TO_CLEAR:
            comments_param.Set("")
            return True

        return False

    except Exception as e:
        return False


def main():
    # Collect beams
    host_beams = collect_host_beams()

    if not host_beams:
        forms.alert("No structural framing elements found in the model.", exitscript=True)

    total_beams = len(host_beams)

    # Process beams with progress bar
    cleared_count = 0

    with Transaction(doc, 'Clear Framing Validation Comments') as t:
        t.Start()

        with forms.ProgressBar(title='Clearing Framing Comments ({value} of {max_value})',
                              cancellable=True) as pb:

            for idx, beam in enumerate(host_beams, 1):
                if pb.cancelled:
                    t.RollBack()
                    forms.alert("Operation cancelled by user.", exitscript=True)

                if clear_comment_if_validation_result(beam):
                    cleared_count += 1

                pb.update_progress(idx, total_beams)


        # Commit - NO OUTPUT AFTER THIS
        status = t.Commit()

        if status != TransactionStatus.Committed:
            # Only show alert for errors, no print
            forms.alert("Failed to clear framing comments. Please try again.", exitscript=True)

        # DON'T print anything here - this triggers new console!


if __name__ == '__main__':
    main()