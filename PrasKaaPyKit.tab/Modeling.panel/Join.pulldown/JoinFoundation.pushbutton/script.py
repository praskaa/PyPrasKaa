# -*- coding: utf-8 -*-
"""
This script joins structural foundations with intersecting structural elements
(framing, columns, floors) and allows the user to define the join priority.
"""
__title__ = "Join Foundations"
__author__ = "Prasetyo"
__version__ = "1.0.0"

import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System')
clr.AddReference('System.Collections')

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ISelectionFilter, Selection, ObjectType
from System.Collections.Generic import List
from pyrevit import forms
from pyrevit import script
from pyrevit import revit

doc = revit.doc
uidoc = revit.uidoc

# --- Configuration ---
# Define join priority: Floor > Foundation > Column > Framing > Wall
# Elements higher in this list should cut elements lower in this list
join_priority_categories = [
    BuiltInCategory.OST_Floors,
    BuiltInCategory.OST_StructuralFoundation,
    BuiltInCategory.OST_StructuralColumns,
    BuiltInCategory.OST_StructuralFraming,
    BuiltInCategory.OST_Walls
]

# --- Selection Filter for Foundations ---
class FoundationSelectionFilter(ISelectionFilter):
    def AllowElement(self, elem):
        # Allow only Structural Foundations during selection
        if hasattr(elem, "Category") and elem.Category and \
           elem.Category.Id.IntegerValue == int(BuiltInCategory.OST_StructuralFoundation):
            return True
        return False

    def AllowReference(self, refer, point):
        return False

# --- Input from PyRevit ---
# 1. Get selected elements (foundations) using a category filter
try:
    ref_elems = uidoc.Selection.PickObjects(ObjectType.Element, FoundationSelectionFilter(), "Select Structural Foundations")
    initial_selected_foundations = [doc.GetElement(ref) for ref in ref_elems]
except Exception as e:
    # User cancelled selection or other selection error
    forms.alert("Selection cancelled or an error occurred during selection: {}".format(str(e)), title="Selection Cancelled")
    script.exit()

if not initial_selected_foundations:
    forms.alert("No structural foundations were selected. Please select valid foundations.", title="No Foundations Selected")
    script.exit()

# Filter out "Foundation Pile - Rectangular" after initial selection
foundations_to_process = []
excluded_count = 0
for foundation in initial_selected_foundations:
    # Get the element type of the foundation
    foundation_type = doc.GetElement(foundation.GetTypeId())
    # Check if the type exists and has a Name property before accessing it
    if foundation_type and hasattr(foundation_type, "Name") and foundation_type.Name == "Foundation Pile - Rectangular":
        excluded_count += 1
    else:
        foundations_to_process.append(foundation)

if not foundations_to_process:
    if excluded_count > 0:
        forms.alert("All selected foundations were excluded because their type is 'Foundation Pile - Rectangular'. Please select other foundation types.", title="No Valid Foundations")
    else:
        forms.alert("No structural foundations were selected or found after filtering. Please select valid foundations.", title="No Foundations Selected")
    script.exit()

# --- Initialize Counters ---
num_foundations_processed = 0
total_join_success = 0
total_join_fail = 0
total_switch_success = 0
error_messages = [] # To store specific errors only

# Use pyRevit's transaction context manager
with revit.Transaction("Join Foundations") as t:
    for foundation in foundations_to_process:
        num_foundations_processed += 1

        # --- Stage 1: Check Intersection and Join ---
        try:
            foundation_bb = foundation.get_BoundingBox(None)
            if foundation_bb:
                # Expand bounding box slightly to catch touching elements
                tolerance = 0.001  # 1mm tolerance for touching elements
                expanded_min = XYZ(foundation_bb.Min.X - tolerance,
                                 foundation_bb.Min.Y - tolerance,
                                 foundation_bb.Min.Z - tolerance)
                expanded_max = XYZ(foundation_bb.Max.X + tolerance,
                                 foundation_bb.Max.Y + tolerance,
                                 foundation_bb.Max.Z + tolerance)
                outline = Outline(expanded_min, expanded_max)
                bb_filter = BoundingBoxIntersectsFilter(outline)
                ids_to_exclude = List[ElementId]([foundation.Id])
                exclude_self_filter = ExclusionFilter(ids_to_exclude)
                not_element_type_filter = ElementIsElementTypeFilter(True)

                intersect_candidates = FilteredElementCollector(doc)\
                                             .WherePasses(bb_filter)\
                                             .WherePasses(exclude_self_filter)\
                                             .WherePasses(not_element_type_filter)\
                                             .ToElements()

                for intersecting_element in intersect_candidates:
                    # Only attempt to join if not already joined
                    if not JoinGeometryUtils.AreElementsJoined(doc, foundation, intersecting_element):
                         try:
                             JoinGeometryUtils.JoinGeometry(doc, foundation, intersecting_element)
                             total_join_success += 1
                         except Exception as join_err:
                             if "cannot be joined" in str(join_err).lower():
                                 total_join_fail += 1
                             else:
                                 error_messages.append("Join Error (Foundation {} - Elem {}): {}".format(foundation.Id.ToString(), intersecting_element.Id.ToString(), str(join_err)))
                                 total_join_fail += 1

        except Exception as e:
             error_messages.append("Error Checking Intersection (Foundation {}): {}".format(foundation.Id.ToString(), str(e)))

        # --- Stage 2: Check Join with Structural Elements and Switch Order based on Priority ---
        try:
            joined_elements_ids = JoinGeometryUtils.GetJoinedElements(doc, foundation)

            if joined_elements_ids:
                for joined_id in joined_elements_ids:
                    joined_element = doc.GetElement(joined_id)

                    if joined_element and joined_element.Category:
                        joined_cat = joined_element.Category.BuiltInCategory
                        
                        # Determine the priority of the foundation and the joined element
                        foundation_priority_idx = join_priority_categories.index(BuiltInCategory.OST_StructuralFoundation) if BuiltInCategory.OST_StructuralFoundation in join_priority_categories else -1
                        joined_element_priority_idx = join_priority_categories.index(joined_cat) if joined_cat in join_priority_categories else -1

                        # If both elements are in our priority list
                        if foundation_priority_idx != -1 and joined_element_priority_idx != -1:
                            # If foundation has higher priority (lower index) and is currently being cut by joined_element
                            if foundation_priority_idx < joined_element_priority_idx:
                                if JoinGeometryUtils.IsCuttingElementInJoin(doc, joined_element, foundation):
                                    try:
                                        JoinGeometryUtils.SwitchJoinOrder(doc, foundation, joined_element)
                                        total_switch_success += 1
                                    except Exception as switch_err:
                                        error_messages.append("Switch Error (Foundation {} - Elem {}): {}".format(foundation.Id.ToString(), joined_element.Id.ToString(), str(switch_err)))
                            # If joined_element has higher priority (lower index) and is currently being cut by foundation
                            elif joined_element_priority_idx < foundation_priority_idx:
                                if JoinGeometryUtils.IsCuttingElementInJoin(doc, foundation, joined_element):
                                    try:
                                        JoinGeometryUtils.SwitchJoinOrder(doc, foundation, joined_element)
                                        total_switch_success += 1
                                    except Exception as switch_err:
                                        error_messages.append("Switch Error (Foundation {} - Elem {}): {}".format(foundation.Id.ToString(), joined_element.Id.ToString(), str(switch_err)))

        except Exception as e:
             error_messages.append("Error Checking/Switching Join (Foundation {}): {}".format(foundation.Id.ToString(), str(e)))

# --- Final Summary Output ---
output = script.get_output()
output.print_md("# Foundation Join Process Results")
output.print_md("- **Total Foundations Processed:** {}".format(num_foundations_processed))
output.print_md("- **Total New Joins Successful:** {}".format(total_join_success))
output.print_md("- **Total New Joins Failed:** {}".format(total_join_fail))
output.print_md("- **Total Join Switches Successful:** {}".format(total_switch_success))

if error_messages:
    output.print_md("\n### Error/Warning Messages:")
    for error in error_messages:
        output.print_md("- {}".format(error))
