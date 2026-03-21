# -*- coding: utf-8 -*-
"""
Wall Plan Generator
Creates plan views for walls based on "Wall Scheme Classification" parameter
Generates one plan view per classification per selected level at wall mid-height

Author: Generated from EF Element Sections Generator analysis
Version: 1.0.0
"""

__title__ = "Wall Plan Generator"
__version__ = "1.0.0"
__doc__ = """Wall Plan Generator

Creates plan views for walls based on "Wall Scheme Classification" parameter.
Generates one plan view per classification per selected level at wall mid-height.

Features:
- Wall classification by "Wall Scheme Classification" parameter
- Multi-level plan generation
- Automatic view naming: Type-Classification-Level
- 2D crop region focusing on wall groups
- Progress tracking and error handling

Usage:
1. Select walls in the model
2. Choose target levels for plan generation
3. Script automatically creates plan views for each classification-level combination
"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝ IMPORTS
#==================================================

from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType
from Autodesk.Revit.DB import *
import traceback
from collections import defaultdict

# pyRevit Imports
from pyrevit import script, forms, EXEC_PARAMS

# Custom Imports
from wall_classifier import WallClassifier
from wall_plan_generator import WallPlanGenerator
from level_selector import LevelSelector
from utils import *

# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝ VARIABLES
#==================================================

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

output = script.get_output()

# ╔═╗╔═╗╔═╗╦═╗╔═╗╔═╗╔═╗╔╦╗╔═╗╔╗╔╔═╗
# ║ ╦║╣ ║ ║╠╦╝║╣ ╚═╗╚═╗ ║ ║╣ ║║║╚═╗
# ╚═╝╚═╝╚═╝╩╚═╚═╝╚═╝╚═╝ ╩ ╚═╝╝╚╝╚═╝ DEBUG CONFIGURATION
#==================================================

DEBUG_MODE = False  # Set to True for detailed debug output

def debug_print(*args, **kwargs):
    """Print debug messages only when DEBUG_MODE is True"""
    if DEBUG_MODE:
        # Convert args to strings and join them
        message_parts = []
        for arg in args:
            if isinstance(arg, str):
                message_parts.append(arg)
            else:
                message_parts.append(str(arg))
        message = ' '.join(message_parts)
        print(message)

def debug_log(message):
    """Log debug message with consistent formatting"""
    if DEBUG_MODE:
        print("[DEBUG] {}".format(message))

# ╔═╗╦ ╦╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔╔═╗
# ╠╣ ║ ║║║║║   ║ ║║ ║║║║╚═╗
# ╚  ╚═╝╝╚╝╚═╝ ╩ ╩╚═╝╝╚╝╚═╝
def select_walls_for_plan_generation():
    """Present wall selection interface to user"""
    wall_categories = [BuiltInCategory.OST_Walls]

    selection_filter = EF_SelectionFilter(wall_categories)

    try:
        with forms.WarningBar(title='Select walls for plan generation and click "Finish"'):
            ref_selected_walls = uidoc.Selection.PickObjects(
                ObjectType.Element, selection_filter
            )

        selected_walls = [doc.GetElement(ref) for ref in ref_selected_walls]
        return selected_walls

    except:
        return []

def show_classification_summary(wall_groups):
    """Display wall classification summary"""
    output.print_md("# Wall Classification Summary")
    output.print_md("---")

    total_walls = sum(len(walls) for walls in wall_groups.values())
    output.print_md("**Total Walls Selected:** {}".format(total_walls))
    output.print_md("**Classifications Found:** {}".format(len(wall_groups)))
    output.print_md("")

    for classification, walls in wall_groups.items():
        output.print_md("- **{}**: {} walls".format(classification, len(walls)))

    output.print_md("---")

def show_unclassified_walls_warning(unclassified_walls):
    """Show warning about unclassified walls"""
    if not unclassified_walls:
        return

    output.print_md("## Warning: Unclassified Walls")
    output.print_md("**{} walls** do not have 'Wall Scheme Classification' parameter or it's empty:".format(len(unclassified_walls)))
    output.print_md("")

    for wall in unclassified_walls[:5]:  # Show first 5
        wall_type = doc.GetElement(wall.GetTypeId())
        output.print_md("- {} (ID: {})".format(wall_type.Name, wall.Id))

    if len(unclassified_walls) > 5:
        output.print_md("- ... and {} more".format(len(unclassified_walls) - 5))

    output.print_md("")
    output.print_md("These walls will be skipped. Continue with classified walls only?")

def generate_wall_plans_with_progress_using_library(view_gen, wall_groups, target_levels):
    """
    Generate wall plans using new ViewGenerator library

    Args:
        view_gen: ViewGenerator instance
        wall_groups: Dict of wall groups by classification
        target_levels: List of target Level objects

    Returns:
        list: List of generation results
    """
    results = []

    # Calculate total operations
    total_operations = len(wall_groups) * len(target_levels)

    from pyrevit.forms import ProgressBar
    with ProgressBar(cancellable=True, title="Generating Wall Plans") as pb:
        operation_count = 0

        for classification, walls in wall_groups.items():
            for level in target_levels:
                if pb.cancelled:
                    break

                operation_count += 1
                pb.update_progress(operation_count, total_operations)
                pb.title = "Creating plan for {} at {}".format(classification, level.Name)

                try:
                    # Generate unique view name
                    view_name_base = "{}-{}".format(classification, level.Name)
                    view_name = view_gen.ensure_unique_view_name(view_name_base)

                    # Generate ONLY plan view (no elevation/cross section)
                    plan_view = view_gen.create_only_plan_view_for_elements(
                        walls, level, view_name, crop_region=True
                    )

                    # Record result
                    result = {
                        'classification': classification,
                        'level': level.Name,
                        'wall_count': len(walls),
                        'status': 'success' if plan_view else 'failed',
                        'view': plan_view
                    }
                    results.append(result)

                except Exception as e:
                    result = {
                        'classification': classification,
                        'level': level.Name,
                        'wall_count': len(walls),
                        'status': 'error',
                        'error': str(e),
                        'view': None
                    }
                    results.append(result)

    return results

def display_generation_results(results):
    """Display generation results in table format"""

    output = script.get_output()

    output.print_md("# Wall Plan Generation Results")
    output.print_md("---")

    # Prepare table data
    table_data = []
    success_count = 0
    error_count = 0

    for result in results:
        status_icon = "✅" if result['status'] == 'success' else "❌"
        view_link = output.linkify(result['view'].Id) if result['view'] else "Failed"

        row = [
            result['classification'],
            result['level'],
            result['wall_count'],
            status_icon,
            view_link
        ]

        table_data.append(row)

        if result['status'] == 'success':
            success_count += 1
        else:
            error_count += 1

    # Display summary
    output.print_md("**Successful:** {}".format(success_count))
    output.print_md("**Failed:** {}".format(error_count))
    output.print_md("")

    # Display table
    output.print_table(
        table_data=table_data,
        title="Generation Results",
        columns=["Classification", "Level", "Wall Count", "Status", "View"]
    )

# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝ MAIN EXECUTION
#----------------------------------------------------------------------
def wall_plan_generator_main():
    """
    Main function for Wall Plan Generator
    """

    # 1. Wall Selection
    selected_walls = select_walls_for_plan_generation()
    if not selected_walls:
        forms.alert("No walls selected.", title="Selection Cancelled")
        return

    # 2. Classification
    debug_print("=== WALL PLAN GENERATOR DEBUG ===")
    debug_print("Starting classification process...")

    classifier = WallClassifier(selected_walls)
    debug_print("WallClassifier initialized with {} walls".format(len(selected_walls)))

    is_valid, unclassified_walls = classifier.validate_classifications()
    debug_print("Classification validation complete: is_valid={}, unclassified_count={}".format(
        is_valid, len(unclassified_walls)))

    # Minimal debug output - only show summary
    if DEBUG_MODE:
        debug_print("\n=== WALL CLASSIFICATION SUMMARY ===")
        debug_print("Total walls: {}".format(len(selected_walls)))
        debug_print("Valid classifications: {}".format(is_valid))
        debug_print("Unclassified walls: {}".format(len(unclassified_walls)))

    if not is_valid:
        show_unclassified_walls_warning(unclassified_walls)
        if not forms.alert("Continue with classified walls only?", yes=True, no=True):
            return

    wall_groups = classifier.classify_walls()

    if not wall_groups:
        forms.alert("No valid wall classifications found.", title="Classification Error")
        return

    # 3. Show classification summary
    show_classification_summary(wall_groups)

    # 4. Level Selection
    level_selector = LevelSelector(doc)
    target_levels = level_selector.select_target_levels()

    if not level_selector.validate_level_selection(target_levels):
        return

    # 5. Start Transaction BEFORE calling ViewGenerator (like EF script)
    t = Transaction(doc, 'Wall Plan Generation')
    t.Start()

    try:
        # Import from local directory relative to script location
        import sys
        import os

        # Get script directory and construct lib path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        lib_path = os.path.join(script_dir, '..', '..', '..', 'lib')

        if lib_path not in sys.path:
            sys.path.insert(0, lib_path)

        from view_generator import ViewGenerator
        view_gen = ViewGenerator(doc)
        debug_print("ViewGenerator initialized successfully")

        # 6. Generate with progress tracking (WITHIN transaction)
        results = generate_wall_plans_with_progress_using_library(
            view_gen, wall_groups, target_levels
        )
        debug_print("Plan generation completed with {} results".format(len(results)))

        # 7. Show minimal results summary
        successful_views = [r for r in results if r['status'] == 'success']
        failed_views = [r for r in results if r['status'] != 'success']

        # Create clean table output
        output.print_md("\n## Wall Plan Generation Results")
        output.print_md("---")

        # Prepare table data
        table_data = []
        for result in results:
            status_icon = "✅" if result['status'] == 'success' else "❌"
            view_link = output.linkify(result['view'].Id) if result['view'] else "Failed"
            row = [
                result['classification'],
                result['level'],
                view_link
            ]
            table_data.append(row)

        # Display table
        output.print_table(
            table_data=table_data,
            title="Generated Plan Views",
            columns=["Classification", "Level", "View"]
        )

        # Summary
        output.print_md("**Summary:** {} views created, {} failed".format(
            len(successful_views), len(failed_views)
        ))

        # 9. Commit transaction AFTER showing results
        t.Commit()
        # Removed print statement to avoid console clutter

    except Exception as e:
        # Rollback on error
        t.RollBack()
        debug_print("Transaction rolled back due to error")
        print("❌ Error during plan generation: {}".format(str(e)))
        if DEBUG_MODE:
            import traceback
            print(traceback.format_exc())
        forms.alert("Plan generation failed: {}".format(str(e)), title="Generation Error")
        return

# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝ SCRIPT ENTRY POINT
#----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        wall_plan_generator_main()
    except Exception as e:
        error_msg = "An error occurred: {}".format(str(e))
        print("❌ CRITICAL ERROR: {}".format(error_msg))

        if DEBUG_MODE:
            import traceback
            full_traceback = traceback.format_exc()
            print("FULL TRACEBACK:")
            print(full_traceback)

            # Show detailed error info in debug mode
            print("\n=== ERROR DETAILS ===")
            print("Error Type: {}".format(type(e).__name__))
            print("Error Message: {}".format(str(e)))
            print("Traceback:")
            print(full_traceback)

        # Show alert with basic error message
        forms.alert("{}".format(error_msg), title="Wall Plan Generator Error")