# -*- coding: utf-8 -*-
"""Disable Masking for Filled Region Types
Disables the masking property for selected filled region types.
"""

__title__ = "Disable Filled Region Masking"
__author__ = "PrasKaa Team"

# pyRevit imports
from pyrevit import revit, DB, forms, script

# Get document and UI document
doc = revit.doc
uidoc = revit.uidoc
output = script.get_output()


def get_selected_filled_region_types():
    """Get selected filled region types or prompt user to select them."""
    selection = uidoc.Selection.GetElementIds()

    # Get currently selected elements
    selected_elements = [doc.GetElement(elem_id) for elem_id in selection]
    selected_types = [elem for elem in selected_elements if isinstance(elem, DB.FilledRegionType)]

    # If filled region types are already selected, validate them
    if selected_types:
        # Check for invalid elements in selection
        invalid_elements = [(elem_id, doc.GetElement(elem_id).GetType().Name)
                           for elem_id in selection
                           if not isinstance(doc.GetElement(elem_id), DB.FilledRegionType)]

        if invalid_elements:
            invalid_msg = "\n".join(["- ID {}: {}".format(id.IntegerValue, name)
                                     for id, name in invalid_elements])

            proceed = forms.alert(
                "Found {} valid Filled Region Type(s) and {} invalid element(s).\n\n"
                "Invalid elements (will be skipped):\n{}\n\n"
                "Continue with valid filled region types?".format(
                    len(selected_types), len(invalid_elements), invalid_msg),
                title="Mixed Selection",
                yes=True,
                no=True
            )
            if not proceed:
                script.exit()

        return selected_types

    # No filled region types selected - show selection dialog
    all_types = DB.FilteredElementCollector(doc)\
                  .OfClass(DB.FilledRegionType)\
                  .ToElements()

    if not all_types:
        forms.alert("No Filled Region Types found in the project.", title="No Types", exitscript=True)

    # Create dictionary for selection
    type_dict = {}
    for fr_type in all_types:
        type_name = fr_type.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
        masking_status = "MASKING" if fr_type.IsMasking else "TRANSPARENT"
        display_name = "{} ({})".format(type_name, masking_status)
        type_dict[display_name] = fr_type

    # Show selection dialog
    selected_display_names = forms.SelectFromList.show(
        sorted(type_dict.keys()),
        title="Select Filled Region Types to Disable Masking",
        button_name='Disable Masking',
        multiselect=True
    )

    if not selected_display_names:
        script.exit()

    # Get the actual types
    selected_types = [type_dict[name] for name in selected_display_names]
    return selected_types


def disable_masking_for_types(filled_region_types):
    """Disable masking for the given filled region types."""
    modified_types = []

    with revit.Transaction("Disable Filled Region Masking"):
        for fr_type in filled_region_types:
            if fr_type.IsMasking:
                # Disable masking
                fr_type.IsMasking = False
                modified_types.append(fr_type)
            # If already disabled, skip silently

    return modified_types


def main():
    """Main execution function."""

    # output.print_md("## Disable Filled Region Masking")
    # output.print_md("---")

    # Step 1: Get selected filled region types
    filled_region_types = get_selected_filled_region_types()

    # output.print_md("**Processing {} filled region type(s)**".format(len(filled_region_types)))

    # Step 2: Disable masking
    modified_types = disable_masking_for_types(filled_region_types)

    # Step 3: Report results
    output.print_md("## Disable Filled Region Masking")
    output.print_md("---")
    output.print_md("## Results")

    if modified_types:
        output.print_md("**✓ Successfully disabled masking for {} type(s):**".format(len(modified_types)))
        for fr_type in modified_types:
            type_name = fr_type.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
            output.print_md("- **{}** (ID: {})".format(type_name, fr_type.Id.IntegerValue))

        output.print_md("")
        output.print_md("*These filled region types will no longer mask elements behind them.*")
    else:
        output.print_md("**ℹ All selected types already have masking disabled.**")

    # Show count of types that were already disabled
    already_disabled = len(filled_region_types) - len(modified_types)
    if already_disabled > 0:
        output.print_md("**{} type(s) were already transparent (no changes needed).**".format(already_disabled))


# Run the script
if __name__ == '__main__':
    main()