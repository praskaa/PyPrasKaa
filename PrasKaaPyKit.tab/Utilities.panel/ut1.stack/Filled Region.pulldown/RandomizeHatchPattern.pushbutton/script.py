# -*- coding: utf-8 -*-
"""Randomize Filled Region Foreground Pattern Types
Randomly assigns FilledRegionTypes with selected foreground patterns to multiple filled regions.
"""

__title__ = "Randomize Hatch Pattern"
__author__ = "PrasKaa Team"

# pyRevit imports
from pyrevit import revit, DB, forms, script
import random

# Selection filter imports
from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType

# Get document and UI document
doc = revit.doc
uidoc = revit.uidoc
output = script.get_output()


def get_all_filled_region_types():
    """Get all FilledRegionType elements in the project."""
    collector = DB.FilteredElementCollector(doc)\
                  .OfClass(DB.FilledRegionType)\
                  .ToElements()
    return list(collector)


def select_filled_region_types(all_types):
    """Show UI for user to select which FilledRegionTypes to randomize."""
    if not all_types:
        forms.alert("No Filled Region Types found in the project.", 
                   title="No Types", 
                   exitscript=True)

    # Create dictionary for selection
    type_dict = {}
    for fr_type in all_types:
        type_name = fr_type.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
        type_dict[type_name] = fr_type

    # Show selection dialog
    selected_names = forms.SelectFromList.show(
        sorted(type_dict.keys()),
        title="Select Filled Region Types to Randomize",
        button_name='Select Types',
        multiselect=True
    )

    if not selected_names:
        script.exit()

    # Get the actual types
    selected_types = [type_dict[name] for name in selected_names]
    return selected_types


def get_all_fill_patterns():
    """Get all FillPatternElements in the project."""
    collector = DB.FilteredElementCollector(doc)\
                  .OfClass(DB.FillPatternElement)\
                  .ToElements()

    return collector


def select_patterns_for_randomization(fill_patterns):
    """Show UI for user to select which patterns to use for randomization."""
    if not fill_patterns:
        forms.alert("No Fill Patterns found in the project.", title="No Patterns", exitscript=True)

    # Create dictionary for selection
    pattern_dict = {}
    for pattern in fill_patterns:
        pattern_name = pattern.Name
        pattern_dict[pattern_name] = pattern

    # Show selection dialog
    selected_names = forms.SelectFromList.show(
        sorted(pattern_dict.keys()),
        title="Select Fill Patterns for Randomization",
        button_name='Use Selected Patterns',
        multiselect=True
    )

    if not selected_names:
        script.exit()

    # Get the actual patterns
    selected_patterns = [pattern_dict[name] for name in selected_names]
    return selected_patterns


def randomize_filled_region_patterns(selected_types, selected_patterns):
    """Randomize foreground patterns by modifying FilledRegionType properties.
    
    Assigns random patterns from the selected pool to each selected type,
    distributing patterns evenly.
    """
    if not selected_patterns:
        forms.alert("No patterns selected for randomization.",
                   title="No Patterns",
                   exitscript=True)

    # Get pattern IDs
    selected_pattern_ids = [pattern.Id for pattern in selected_patterns]

    num_types = len(selected_types)
    num_patterns = len(selected_pattern_ids)

    # Determine assignment strategy
    if num_patterns >= num_types:
        # Unique assignment: each type gets a unique pattern
        # Shuffle patterns to randomize assignment
        shuffled_patterns = selected_pattern_ids[:]
        random.shuffle(shuffled_patterns)
        pattern_assignments = shuffled_patterns[:num_types]
    else:
        # Distribute patterns evenly across types
        # Calculate how many types per pattern
        types_per_pattern = num_types // num_patterns
        extra_types = num_types % num_patterns

        pattern_assignments = []
        for i in range(num_patterns):
            count = types_per_pattern + (1 if i < extra_types else 0)
            pattern_assignments.extend([selected_pattern_ids[i]] * count)

    changes = []

    with revit.Transaction("Randomize Filled Region Patterns", doc=doc):
        for fr_type, assigned_pattern_id in zip(selected_types, pattern_assignments):
            # Get current pattern
            current_pattern_id = fr_type.ForegroundPatternId
            
            # Skip if same pattern
            if current_pattern_id == assigned_pattern_id:
                continue
            
            # Get pattern names for reporting
            old_pattern = doc.GetElement(current_pattern_id)
            old_pattern_name = old_pattern.Name if old_pattern else "None"
            
            new_pattern = doc.GetElement(assigned_pattern_id)
            new_pattern_name = new_pattern.Name if new_pattern else "Unknown"
            
            # Get type name
            type_name = fr_type.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
            
            # Modify the type's ForegroundPatternId
            fr_type.ForegroundPatternId = assigned_pattern_id
            
            # Record change
            changes.append({
                'type_id': fr_type.Id.IntegerValue,
                'type_name': type_name,
                'old_pattern': old_pattern_name,
                'new_pattern': new_pattern_name
            })

    return changes


def main():
    """Main execution function."""

    # Step 1: Get all filled region types in project
    all_types = get_all_filled_region_types()

    # Step 2: Let user select which types to randomize
    selected_types = select_filled_region_types(all_types)

    # Step 3: Get all fill patterns
    all_patterns = get_all_fill_patterns()

    # Step 4: Let user select patterns for randomization
    selected_patterns = select_patterns_for_randomization(all_patterns)

    # Step 5: Randomize patterns of selected types
    changes = randomize_filled_region_patterns(selected_types, selected_patterns)

    # Step 6: Report results
    if not changes:
        output.print_md("ℹ No changes made")


# Run the script
if __name__ == '__main__':
    main()