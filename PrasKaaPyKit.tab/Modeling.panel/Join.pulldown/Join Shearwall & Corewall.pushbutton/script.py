"""Join and Switch Wall Connections with Structure.
Join walls with intersecting elements and ensure structural elements cut through walls."""

__title__ = 'Join Shearwall\n& Corewall'
__author__ = 'PyRevit'
__doc__ = 'Automatically joins selected walls with intersecting elements and ensures structural elements cut through the walls.'

# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System')
clr.AddReference('System.Collections')

from Autodesk.Revit.DB import *
from System.Collections.Generic import List
from pyrevit import forms
from pyrevit import script
from pyrevit import revit

# Import smart selection utility from lib
from Snippets.smart_selection import get_filtered_selection

# Get current document and UI
doc = revit.doc
uidoc = revit.uidoc
# Helper function for cross-version ElementId value access
def id_val(eid):
    """Extract numeric value from ElementId, compatible with Revit 2020-2025 (IntegerValue) and 2026+ (Value).

    Args:
        eid (ElementId): The ElementId to extract value from.

    Returns:
        int: The numeric ID value.
    """
    try:
        return eid.Value
    except AttributeError:
        return eid.IntegerValue


# Configuration
structural_categories = [
    BuiltInCategory.OST_Walls,  # ONLY Shearwalls and Corewalls!
    BuiltInCategory.OST_StructuralFraming,
    BuiltInCategory.OST_StructuralColumns,
    BuiltInCategory.OST_Floors,
    BuiltInCategory.OST_StructuralFoundation,  # Main foundation category
    BuiltInCategory.OST_IOSModelGroups  # Added support for Model Groups
]

# Get filtered walls using smart selection
walls_to_process = get_filtered_selection(
    doc=doc,
    uidoc=uidoc,
    category_filter_func=lambda elem: isinstance(elem, Wall),
    prompt_message="Select Walls to join with structure",
    no_selection_message="No walls selected. Please select walls to process.",
    filter_name="Wall Selection"
)

# Initialize counters
num_walls_processed = 0
total_join_success = 0
total_join_fail = 0
total_switch_success = 0
error_messages = []  # For storing specific errors

# Start Transaction
t = Transaction(doc, "Join Walls to Structure")
t.Start()

try:
    for wall in walls_to_process:
        num_walls_processed += 1
        
        # Phase 1: Check Intersection and Join
        try:
            wall_bb = wall.get_BoundingBox(None)
            if wall_bb:
                # Expand bounding box slightly to catch touching elements
                tolerance = 0.001  # 1mm tolerance for touching elements
                expanded_min = XYZ(wall_bb.Min.X - tolerance,
                                 wall_bb.Min.Y - tolerance,
                                 wall_bb.Min.Z - tolerance)
                expanded_max = XYZ(wall_bb.Max.X + tolerance,
                                 wall_bb.Max.Y + tolerance,
                                 wall_bb.Max.Z + tolerance)
                outline = Outline(expanded_min, expanded_max)
                bb_filter = BoundingBoxIntersectsFilter(outline)
                ids_to_exclude = List[ElementId]([wall.Id])
                exclude_self_filter = ExclusionFilter(ids_to_exclude)
                not_element_type_filter = ElementIsElementTypeFilter(True)
                  # Get all potential elements to join
                intersect_candidates = (FilteredElementCollector(doc)
                    .WherePasses(bb_filter)
                    .WherePasses(exclude_self_filter)
                    .WherePasses(not_element_type_filter)
                    .ToElements())
                
                # Try to join with found elements
                for intersecting_element in intersect_candidates:
                    # Skip if not a structural element except for foundations
                    if intersecting_element.Category and id_val(intersecting_element.Category.Id) not in [int(cat) for cat in structural_categories]:
                        continue
                    
                    # Only try to join if not already joined
                    if not JoinGeometryUtils.AreElementsJoined(doc, wall, intersecting_element):
                        try:
                            JoinGeometryUtils.JoinGeometry(doc, wall, intersecting_element)
                            total_join_success += 1
                        except Exception as join_err:
                            if "cannot be joined" in str(join_err):
                                total_join_fail += 1
                            else:
                                error_messages.append("Join Error (Wall {} - Elem {}): {}".format(
                                    str(id_val(wall.Id)), 
                                    str(id_val(intersecting_element.Id)), 
                                    str(join_err)))
                                total_join_fail += 1

        except Exception as e1:
            error_messages.append("Intersection Check Error (Wall {}): {}".format(
                str(id_val(wall.Id)), str(e1)))

        # Phase 2: Check Join with Structural Elements and Switch Order
        # ENSURE SHEARWALL/COREWALL ALWAYS CUT THROUGH OTHER ELEMENTS (TOP PRIORITY)
        try:
            joined_elements_ids = JoinGeometryUtils.GetJoinedElements(doc, wall)
            if joined_elements_ids:
                for joined_id in joined_elements_ids:
                    joined_element = doc.GetElement(joined_id)
                    if joined_element and joined_element.Category:
                        joined_cat = joined_element.Category.BuiltInCategory
                        if joined_cat in structural_categories:
                            # SHEARWALL/COREWALL MUST ALWAYS BE CUTTING ELEMENT
                            # If wall is NOT cutting element, switch order to make it cutting
                            if not JoinGeometryUtils.IsCuttingElementInJoin(doc, wall, joined_element):
                                try:
                                    JoinGeometryUtils.SwitchJoinOrder(doc, wall, joined_element)
                                    total_switch_success += 1
                                except Exception as switch_err:
                                    error_messages.append("Switch Error (Wall {} - Elem {}): {}".format(
                                        str(id_val(wall.Id)),
                                        str(id_val(joined_element.Id)),
                                        str(switch_err)))
        except Exception as e2:
            error_messages.append("Join/Switch Check Error (Wall {}): {}".format(
                str(id_val(wall.Id)), str(e2)))

    # Commit the transaction if everything went well
    t.Commit()
except Exception as e3:
    # If something went wrong, roll back the transaction
    t.RollBack()
    error_messages.append("Transaction Error: {}".format(str(e3)))

# Final Summary Output
output = script.get_output()
output.print_md("# Wall Join Process Results")
output.print_md("- **Total Walls Processed:** {}".format(num_walls_processed))
output.print_md("- **Total New Joins Successful:** {}".format(total_join_success))
output.print_md("- **Total New Joins Failed:** {}".format(total_join_fail))
output.print_md("- **Total Join Switches Successful:** {}".format(total_switch_success))

if error_messages:
    output.print_md("\n### Error/Warning Messages:")
    for error in error_messages:
        output.print_md("- {}".format(error))
