# -*- coding: utf-8 -*-
"""
Clear Column Comments - Remove Dimension Validation Comments
"""

__title__ = 'Clear\nColumn\nComments'
__author__ = 'Kilo Code'
__doc__ = "Removes dimension validation comments from column elements."

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
COMMENTS_TO_CLEAR = ["Approved", "Dimension to be checked", "Unmatched"]


def collect_host_columns():
    """Collects structural column elements from the host Revit model."""
    host_columns = FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_StructuralColumns)\
        .WhereElementIsNotElementType()\
        .ToElements()
    return host_columns


def clear_comment_if_validation_result(column):
    """Clears the comment parameter if it contains a validation result."""
    try:
        comments_param = column.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
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
    """Main execution function that clears validation comments from columns."""
    
    output.print_md("# Clear Column Comments")
    output.print_md("---\n")

    # Collect columns
    output.print_md("📋 Collecting structural columns...")
    host_columns = collect_host_columns()

    if not host_columns:
        forms.alert("No structural column elements found in the model.", exitscript=True)

    total_columns = len(host_columns)
    output.print_md("Found **{}** columns to process\n".format(total_columns))
    output.print_md("⏳ Processing columns...\n")

    # Process columns with progress bar
    cleared_count = 0
    
    with Transaction(doc, 'Clear Column Validation Comments') as t:
        t.Start()

        with forms.ProgressBar(title='Clearing Column Comments ({value} of {max_value})', 
                              cancellable=True) as pb:
            
            for idx, column in enumerate(host_columns, 1):
                if pb.cancelled:
                    t.RollBack()
                    forms.alert("Operation cancelled by user.", exitscript=True)
                
                if clear_comment_if_validation_result(column):
                    cleared_count += 1
                
                pb.update_progress(idx, total_columns)

        # Print summary BEFORE commit
        output.print_md("\n---")
        output.print_md("## ✅ Results Summary\n")
        output.print_md("- **Total columns processed:** {}".format(total_columns))
        output.print_md("- **Comments cleared:** {}".format(cleared_count))
        output.print_md("- **Columns unchanged:** {}".format(total_columns - cleared_count))
        output.print_md("\n⏳ Saving changes to model...")
        
        # Commit - NO OUTPUT AFTER THIS
        status = t.Commit()

        if status != TransactionStatus.Committed:
            # Only show alert for errors, no print
            forms.alert("Failed to clear column comments. Please try again.", exitscript=True)
        
        # DON'T print anything here - this triggers new console!

    # Script ends here - all output already printed before commit


if __name__ == '__main__':
    main()