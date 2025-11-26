# -*- coding: utf-8 -*-
"""Bake Filled Region Color Override to New Type
Creates new FilledRegionTypes with overridden colors from selected filled regions.
Supports both single and multiple selections with automatic numbering.
"""


__title__ = "Bake Hatch Color"
__author__ = "PrasKaa Team"

# pyRevit imports
from pyrevit import revit, DB, forms, script
from collections import defaultdict

# Selection filter imports
from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType
from System.Collections.Generic import List

# Get document and UI document
doc = revit.doc
uidoc = revit.uidoc
output = script.get_output()


class ISelectionFilter_Classes(ISelectionFilter):
    """Selection filter for specific Revit element classes."""
    def __init__(self, allowed_types):
        """Initialize filter with allowed element types.
        :param allowed_types: list of allowed element Types"""
        self.allowed_types = allowed_types

    def AllowElement(self, element):
        """Check if element is of allowed type."""
        if type(element) in self.allowed_types:
            return True
        return False


def get_selected_filled_regions():
    """Get all selected filled region elements and validate selection.
    If no filled regions are selected, prompt user to select them."""
    selection = uidoc.Selection.GetElementIds()

    # Get currently selected elements
    selected_elements = [doc.GetElement(elem_id) for elem_id in selection]
    selected_filled_regions = [elem for elem in selected_elements if isinstance(elem, DB.FilledRegion)]

    # If filled regions are already selected, validate them
    if selected_filled_regions:
        # Check for invalid elements in selection
        invalid_elements = [(elem_id, doc.GetElement(elem_id).GetType().Name)
                           for elem_id in selection
                           if not isinstance(doc.GetElement(elem_id), DB.FilledRegion)]

        if invalid_elements:
            invalid_msg = "\n".join(["- ID {}: {}".format(id.IntegerValue, name)
                                     for id, name in invalid_elements])

            proceed = forms.alert(
                "Found {} valid Filled Region(s) and {} invalid element(s).\n\n"
                "Invalid elements (will be skipped):\n{}\n\n"
                "Continue with valid filled regions?".format(
                    len(selected_filled_regions), len(invalid_elements), invalid_msg),
                title="Mixed Selection",
                yes=True,
                no=True
            )
            if not proceed:
                script.exit()

        return selected_filled_regions

    # No filled regions selected - prompt user to select them
    filled_regions = []
    try:
        with forms.WarningBar(title='Select Filled Regions with color overrides and click "Finish"'):
            ref_selected_regions = uidoc.Selection.PickObjects(
                ObjectType.Element,
                'Select Filled Regions'
            )

        # Filter to only FilledRegion elements
        for ref in ref_selected_regions:
            elem = doc.GetElement(ref)
            if isinstance(elem, DB.FilledRegion):
                filled_regions.append(elem)

    except:
        # User cancelled selection
        pass

    if not filled_regions:
        forms.alert("No Filled Regions were selected.\nPlease try again.",
                   title="Selection Cancelled",
                   exitscript=True)

    return filled_regions


def get_override_color(elem, view):
    """Get the overridden foreground color from view graphics overrides."""
    elem_id = elem.Id
    overrides = view.GetElementOverrides(elem_id)

    # Get the surface foreground pattern color
    override_color = overrides.SurfaceForegroundPatternColor

    # Check if color is valid (overrides may return invalid colors when not set)
    if not override_color.IsValid:
        return None

    return override_color


def color_to_tuple(color):
    """Convert DB.Color to RGB tuple for comparison."""
    return (color.Red, color.Green, color.Blue)


def group_elements_by_color(filled_regions, view):
    """Group filled regions by their override colors."""
    color_groups = defaultdict(list)
    no_override = []
    same_as_type = []

    for elem in filled_regions:
        override_color = get_override_color(elem, view)

        if override_color is None:
            no_override.append(elem)
            continue

        # Get type color for comparison
        type_id = elem.GetTypeId()
        current_type = doc.GetElement(type_id)
        type_color = current_type.ForegroundPatternColor

        # Check if override is same as type
        if color_to_tuple(override_color) == color_to_tuple(type_color):
            same_as_type.append(elem)
            continue

        # Group by color (use tuple as key)
        color_key = color_to_tuple(override_color)
        color_groups[color_key].append({
            'element': elem,
            'override_color': override_color,
            'type': current_type
        })

    return color_groups, no_override, same_as_type


def get_existing_type_names():
    """Get all existing FilledRegionType names."""
    collector = DB.FilteredElementCollector(doc)\
                  .OfClass(DB.FilledRegionType)\
                  .ToElements()

    return [t.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
            for t in collector]


def generate_unique_name(base_name, suffix_number, existing_names):
    """Generate a unique type name with suffix."""
    if suffix_number == 1:
        # First one: try without suffix
        candidate = base_name
        if candidate not in existing_names:
            return candidate

    # With suffix
    candidate = "{}_{}".format(base_name, suffix_number)
    counter = suffix_number

    # Keep incrementing if name exists
    while candidate in existing_names:
        counter += 1
        candidate = "{}_{}".format(base_name, counter)

    return candidate


def create_new_filled_region_type(original_type, new_name, new_color):
    """Duplicate the filled region type and set the new color."""
    try:
        # Duplicate the type
        new_type = original_type.Duplicate(new_name)

        # Set the color at type level
        new_type.ForegroundPatternColor = new_color

        return new_type

    except Exception as e:
        # output.print_md("**✗ Error creating type '{}': {}**".format(new_name, str(e)))
        return None


def main():
    """Main execution function."""

    # output.print_md("## Baking Filled Region Color Overrides")
    # output.print_md("---")

    # Step 1: Get selected filled regions
    filled_regions = get_selected_filled_regions()

    # Step 2: Get the active view
    view = uidoc.ActiveView
    # output.print_md("**Active View:** {}".format(view.Name))
    # output.print_md("")

    # Step 3: Group elements by color
    # output.print_md("**Analyzing selections...**")
    color_groups, no_override, same_as_type = group_elements_by_color(filled_regions, view)

    # Report elements that can't be processed
    if no_override:
        # output.print_md("")
        # output.print_md("⚠ **{} element(s) without color override (skipped):**".format(len(no_override)))
        # for elem in no_override:
        #     output.print_md("  - ID: {}".format(elem.Id.IntegerValue))

        pass

    if same_as_type:
        # output.print_md("")
        # output.print_md("⚠ **{} element(s) with override matching type color (skipped):**".format(len(same_as_type)))
        # for elem in same_as_type:
        #     output.print_md("  - ID: {}".format(elem.Id.IntegerValue))

        pass

    # Check if we have any valid groups
    if not color_groups:
        forms.alert("No valid filled regions with unique color overrides found.\n\n"
                   "Please ensure:\n"
                   "1. Elements have color overrides applied\n"
                   "2. Override colors differ from type colors",
                   title="No Valid Elements",
                   exitscript=True)

    # output.print_md("")
    # output.print_md("**✓ Found {} unique color(s) to process**".format(len(color_groups)))

    # Display color groups
    # output.print_md("")
    # output.print_md("### Color Groups:")
    # for i, (color_tuple, items) in enumerate(color_groups.items(), 1):
    #     output.print_md("{}. **RGB({}, {}, {})** - {} element(s)".format(
    #         i, color_tuple[0], color_tuple[1], color_tuple[2], len(items)))

    # output.print_md("---")

    # Step 4: Ask for prefix name
    # Suggest a prefix based on the first element's type name
    first_item = list(color_groups.values())[0][0]
    first_type_name = first_item['type'].get_Parameter(
        DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString()

    default_prefix = "{}_BakedColor".format(first_type_name)

    prefix_name = forms.ask_for_string(
        prompt="Enter PREFIX name for new types:\n\n"
               "(Suffix numbers will be added automatically: _1, _2, _3, etc.)\n"
               "Total types to create: {}".format(len(color_groups)),
        default=default_prefix,
        title="Type Name Prefix"
    )

    if not prefix_name:
        # output.print_md("**✗ Operation cancelled by user**")
        script.exit()

    # Step 5: Get existing type names
    existing_names = get_existing_type_names()

    # Step 6: Create types for each color group
    # output.print_md("")
    # output.print_md("### Creating New Types:")
    # output.print_md("")

    created_types = []  # Store (new_type, color_tuple, elements) tuples

    with revit.Transaction("Bake Hatch Color Overrides", doc=doc):

        suffix_counter = 1

        for color_tuple, items in sorted(color_groups.items()):
            # Use the first element's type as template
            template_type = items[0]['type']
            override_color = items[0]['override_color']

            # Generate unique name
            new_type_name = generate_unique_name(prefix_name, suffix_counter, existing_names)

            # Create the new type
            new_type = create_new_filled_region_type(template_type, new_type_name, override_color)

            if new_type:
                # Add to existing names to avoid duplicates in this batch
                existing_names.append(new_type_name)

                created_types.append((new_type, color_tuple, items))

                # output.print_md("**✓ Created:** {}".format(new_type_name))
                # output.print_md("  - **Color RGB:** ({}, {}, {})".format(
                #     override_color.Red, override_color.Green, override_color.Blue))
                # output.print_md("  - **Pattern:** {}".format(
                #     doc.GetElement(new_type.ForegroundPatternId).Name))
                # output.print_md("  - **Elements:** {}".format(len(items)))
                # output.print_md("")

                suffix_counter += 1

    if not created_types:
        # output.print_md("**✗ No types were created**")
        script.exit()

   #output.print_md("---")

    # Step 7: Ask if user wants to apply new types to elements
    apply_to_elements = forms.alert(
        "Successfully created {} new type(s)!\n\n"
        "Do you want to apply these new types to the selected elements?".format(len(created_types)),
        title="Apply New Types?",
        yes=True,
        no=True
    )

    if apply_to_elements:
        # output.print_md("### Applying Types to Elements:")
        # output.print_md("")

        with revit.Transaction("Apply New Types", doc=doc):
            total_applied = 0

            for new_type, color_tuple, items in created_types:
                type_name = new_type.get_Parameter(
                    DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString()

                for item in items:
                    elem = item['element']
                    elem.ChangeTypeId(new_type.Id)
                    total_applied += 1

                # output.print_md("**✓ Applied '{}' to {} element(s)**".format(
                #     type_name, len(items)))

        # output.print_md("")
        # output.print_md("**✓ Total: {} element(s) updated**".format(total_applied))

    # Step 8: Summary
    output.print_md("## Summary")
    output.print_md("")
    output.print_md("- **Total Selections:** {}".format(len(filled_regions)))
    output.print_md("- **Types Created:** {}".format(len(created_types)))
    output.print_md("- **Elements Skipped:** {}".format(len(no_override) + len(same_as_type)))

    if apply_to_elements:
        output.print_md("- **Elements Updated:** {}".format(total_applied))

    output.print_md("")
    output.print_md("### Created Types:")
    for new_type, color_tuple, items in created_types:
        type_name = new_type.get_Parameter(
            DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
        output.print_md("- **{}** - RGB({}, {}, {}) - ID: {}".format(
            type_name, color_tuple[0], color_tuple[1], color_tuple[2],
            new_type.Id.IntegerValue))

    output.print_md("")
    output.print_md("*New types are now available in your project!*")


# Run the script
if __name__ == '__main__':
    main()