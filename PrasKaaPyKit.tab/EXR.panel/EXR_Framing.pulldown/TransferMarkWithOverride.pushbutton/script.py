# -*- coding: utf-8 -*-
"""
Transfer Mark Parameter from Linked Model Type Name based on Geometry Intersection.

This script finds pairs of Structural Framing elements (beams) between the host
model and a selected linked model. The matching is done by finding the
largest intersection volume between elements.

It then extracts the mark value from the 'Type Name' parameter of linked beams
(e.g., "G9-99" -> "99", "G5.99" -> "99") and copies it to the 'Mark' parameter
of the corresponding host beams.
"""

__title__ = 'Transfer Mark From ETABS EXR Models'
__author__ = 'Prasetyo'
__doc__ = "Extracts mark value from Type Name of linked beams and copies to host beams " \
          "by finding the best geometric match (intersection volume)."


import re
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    RevitLinkInstance,
    ElementId,
    Solid,
    BooleanOperationsUtils,
    BooleanOperationsType,
    Transaction,
    View,
    ViewType,
    Element
)

from pyrevit import revit, forms, script

# Setup
doc = revit.doc
uidoc = revit.uidoc
logger = script.get_logger()
output = script.get_output()

# Revit API Options for geometry extraction
# Using a detail level is important to get proper geometry
app = doc.Application
options = app.Create.NewGeometryOptions()
active_view = doc.ActiveView
if active_view:
    options.View = active_view
else:
    # If no active view, find any 3D view to get geometry
    view_collector = FilteredElementCollector(doc).OfClass(View)
    for v in view_collector:
        if not v.IsTemplate and v.ViewType == ViewType.ThreeD:
            options.View = v
            break

def get_solid(element):
    """Extracts the solid geometry from a given element."""
    geom_element = element.get_Geometry(options)
    if not geom_element:
        return None

    solids = []
    for geom_obj in geom_element:
        if isinstance(geom_obj, Solid) and geom_obj.Volume > 0:
            solids.append(geom_obj)
    
    if not solids:
        return None
    
    # If multiple solids, unite them into one
    if len(solids) > 1:
        main_solid = solids[0]
        for s in solids[1:]:
            try:
                main_solid = BooleanOperationsUtils.ExecuteBooleanOperation(main_solid, s, BooleanOperationsType.Union)
            except Exception as e:
                logger.warning("Could not unite solids for element {}. Error: {}".format(element.Id, e))
        return main_solid
    return solids[0]


def extract_mark_from_type_name(type_name):
    """
    Extracts the mark value from Type Name parameter.
    Pattern: Extract numbers after "." or "-" from type names like "G9-99" or "G5.99"
    Also handles patterns like "B4-4(fc 40)-CI" -> "4", "B4-40fc 35)" -> "40", etc.
    
    Args:
        type_name (str): The Type Name parameter value
        
    Returns:
        str: The extracted mark value or None if pattern not found
    """
    if not type_name:
        return None
    
    # Pattern to match numbers after "." or "-"
    # Examples: "G9-99" -> "99", "G5.99" -> "99", "GA1-6-CJ" -> "6"
    # Also: "B4-4(fc 40)-CI" -> "4", "B4-40fc 35)" -> "40", "B4-40(c 40)" -> "40", "B4-41(fc 35)" -> "41"
    pattern = r'[.-](\d+)(?:-C[IJ])?'
    match = re.search(pattern, type_name)
    
    if match:
        return match.group(1)
    else:
        logger.warning("Could not extract mark from Type Name: {}".format(type_name))
        return None


def find_best_match(host_beam, linked_beams_dict):
    """
    Finds the best matching linked beam for a host beam based on intersection volume.
    
    Args:
        host_beam (Element): The beam in the host model.
        linked_beams_dict (dict): A dictionary of {ElementId: {'element': Element, 'solid': Solid}} from the linked model.
        
    Returns:
        Element: The best matching beam from the linked model or None.
    """
    host_solid = get_solid(host_beam)
    if not host_solid:
        return None

    best_match = None
    max_intersection_volume = 0.0

    for linked_beam_id, linked_beam_data in linked_beams_dict.items():
        linked_solid = linked_beam_data['solid']
        if not linked_solid:
            continue

        try:
            # Calculate intersection
            intersection_solid = BooleanOperationsUtils.ExecuteBooleanOperation(
                host_solid, linked_solid, BooleanOperationsType.Intersect
            )
            
            # Compare volume
            if intersection_solid and intersection_solid.Volume > max_intersection_volume:
                max_intersection_volume = intersection_solid.Volume
                best_match = linked_beam_data['element']

        except Exception as e:
            # This can fail if solids are disjoint or have issues
            logger.debug("Boolean operation failed between host {} and linked {}. Error: {}".format(host_beam.Id, linked_beam_id, e))
            continue
            
    return best_match


def main():
    """Main execution logic."""
    # 1. Select the Linked Model
    link_instances = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()
    if not link_instances:
        forms.alert("No Revit links found in the current project.", exitscript=True)

    # Create a dictionary of link instances for selection
    link_dict = {link.Name: link for link in link_instances}
    
    selected_link_name = forms.SelectFromList.show(
        sorted(link_dict.keys()),
        title='Select Source Linked Model (from ETABS)',
        button_name='Select Link',
        multiselect=False
    )
    
    selected_link = link_dict.get(selected_link_name) if selected_link_name else None

    if not selected_link:
        forms.alert("No link selected. Script will exit.", exitscript=True)

    link_doc = selected_link.GetLinkDocument()
    if not link_doc:
        forms.alert("Could not access the document of the selected link. Ensure it is loaded.", exitscript=True)

    # Ask for the target parameter name
    target_param_name = forms.ask_for_string(
        default='Mark',
        prompt='Enter the target parameter name for host beams:',
        title='Target Parameter'
    )

    if not target_param_name:
        forms.alert("No target parameter name entered. Script will exit.", exitscript=True)

    # 2. Collect Beams from Host and Link
    # Get selection from the active document
    selection_ids = uidoc.Selection.GetElementIds()
    host_beams = []

    if selection_ids:
        # If user has pre-selected elements, use them
        for elem_id in selection_ids:
            elem = doc.GetElement(elem_id)
            # Make sure the selected element is a Structural Framing element
            if (elem.Category and
                    elem.Category.Id.IntegerValue == int(BuiltInCategory.OST_StructuralFraming)):
                host_beams.append(elem)
        
        if not host_beams:
            forms.alert("Tidak ada elemen balok (Structural Framing) yang ditemukan dalam seleksi Anda. "
                        "Silakan pilih beberapa balok dan coba lagi.", exitscript=True)
    else:
        # If nothing is selected, get all structural framing in the project
        host_beams = FilteredElementCollector(doc)\
            .OfCategory(BuiltInCategory.OST_StructuralFraming)\
            .WhereElementIsNotElementType()\
            .ToElements()

    linked_beams = FilteredElementCollector(link_doc)\
        .OfCategory(BuiltInCategory.OST_StructuralFraming)\
        .WhereElementIsNotElementType()\
        .ToElements()

    if not host_beams or not linked_beams:
        forms.alert("No structural framing elements found in the host or linked model.", exitscript=True)

    # Pre-calculate solids for linked beams for performance
    linked_beams_dict = {}
    with forms.ProgressBar(title='Processing linked beams... ({value} of {max_value})', cancellable=True) as pb:
        for i, beam in enumerate(linked_beams):
            if pb.cancelled:
                forms.alert("Operation cancelled by user during linked beam processing.", exitscript=True)
            pb.update_progress(i, len(linked_beams))
            solid = get_solid(beam)
            if solid:
                linked_beams_dict[beam.Id] = {'element': beam, 'solid': solid}

    # 3. Find matches and prepare data for update
    updates_to_make = []
    unmatched_beams = []
    extraction_fail_beams = []

    with forms.ProgressBar(title='Finding matches... ({value} of {max_value})', cancellable=True) as pb:
        for i, host_beam in enumerate(host_beams):
            if pb.cancelled:
                forms.alert("Operation cancelled by user during match finding.", exitscript=True)
            pb.update_progress(i, len(host_beams))
            best_match_linked_beam = find_best_match(host_beam, linked_beams_dict)

            if best_match_linked_beam:
                updates_to_make.append((host_beam, best_match_linked_beam))
            else:
                unmatched_beams.append(host_beam)

    if not updates_to_make:
        forms.alert("No matching beams found between the host and linked model.", exitscript=True)

    # 4. Perform the update within a transaction
    updated_count = 0
    extraction_fail_count = 0
    comment_update_count = 0
    results_data = []
    extraction_fail_data = []
    transaction_name = 'Transfer Beam Marks to "{}"'.format(target_param_name)
    with Transaction(doc, transaction_name) as t:
        t.Start()
        
        # Process matched beams
        for host_beam, linked_beam in updates_to_make:
            try:
                host_mark_param = host_beam.LookupParameter(target_param_name)
                
                # Get Type Name from linked beam
                linked_type = linked_beam.Document.GetElement(linked_beam.GetTypeId())
                if linked_type:
                    type_name_param = linked_type.LookupParameter('Type Name')
                    if type_name_param:
                        type_name = type_name_param.AsString()
                        mark_value = extract_mark_from_type_name(type_name)
                        
                        if host_mark_param and not host_mark_param.IsReadOnly and mark_value:
                            host_mark_param.Set(mark_value)
                            updated_count += 1
                            results_data.append([
                                output.linkify(host_beam.Id),
                                host_beam.Name,
                                output.linkify(linked_beam.Id),
                                mark_value,
                                type_name or "N/A"
                            ])
                        else:
                            # Mark extraction failed, set Comment to "Extract Fail"
                            host_comment_param = host_beam.LookupParameter('Comments')
                            if host_comment_param and not host_comment_param.IsReadOnly:
                                host_comment_param.Set('Extract Fail')
                                extraction_fail_count += 1
                                extraction_fail_data.append([
                                    output.linkify(host_beam.Id),
                                    host_beam.Name,
                                    output.linkify(linked_beam.Id),
                                    type_name or "N/A",
                                    'Extract Fail'
                                ])
            except Exception as e:
                logger.error("Failed to update beam {}. Error: {}".format(host_beam.Id, e))
        
        # Process unmatched beams - set Comment to "Failed"
        for host_beam in unmatched_beams:
            try:
                host_comment_param = host_beam.LookupParameter('Comments')
                if host_comment_param and not host_comment_param.IsReadOnly:
                    host_comment_param.Set('Failed')
                    comment_update_count += 1
            except Exception as e:
                logger.error("Failed to update Comment for unmatched beam {}. Error: {}".format(host_beam.Id, e))
                
        t.Commit()

    # 5. Report results
    output.print_md("## Mark Transfer Report")
    output.print_md("---")
    forms.alert(
        "Successfully updated {} of {} host beams.".format(updated_count, len(host_beams)),
        title="Process Complete"
    )

    if results_data:
        # Limit display to prevent performance issues and crashes
        max_display = 10
        display_data = results_data[:max_display]

        output.print_table(
            table_data=display_data,
            title="Updated Beams",
            columns=["Host Beam ID", "Host Type", "Matched Linked Beam ID", "Extracted Mark", "Linked Type Name"]
        )

        if len(results_data) > max_display:
            output.print_md("*Showing first {} of {} updated beams for performance*".format(max_display, len(results_data)))

    if unmatched_beams:
        output.print_md("### Unmatched Beams")
        output.print_md("The following {} beams in the host model could not be matched to any beam in the linked model:".format(len(unmatched_beams)))

        # Prepare table data for unmatched beams
        unmatched_data = []
        max_display = 5  # Limit display to first 50 for performance

        for i, beam in enumerate(unmatched_beams):
            if i >= max_display:
                break
            unmatched_data.append([
                output.linkify(beam.Id),
                beam.Name
            ])

        if len(unmatched_beams) > max_display:
            output.print_md("*Showing first {} of {} unmatched beams for performance*".format(max_display, len(unmatched_beams)))

        output.print_table(
            table_data=unmatched_data,
            title="Unmatched Beams List",
            columns=["Beam ID", "Type Name"]
        )


if __name__ == '__main__':
    main()
