# -*- coding: utf-8 -*-
"""
Transfer Mark Parameter from Linked Revit Model based on Geometry Intersection.

This script finds pairs of Structural Framing elements (beams) between the host
model and a selected linked Revit model. The matching is done by finding the
largest intersection volume between elements.

It then directly copies the 'Mark' parameter value from linked beams to the
corresponding host beams.

Features:
- Uses largest intersection volume to find matching beams
- Applies coordinate transformation from linked model (handles different internal origins)
- Directly copies Mark parameter (no Type Name parsing)
- Works with selection or all Structural Framing elements
"""

__title__ = 'TransferMark with Revit Model'
__author__ = 'PrasKaa'
__doc__ = "Copies Mark parameter from linked Revit model beams to host beams " \
          "by finding the best geometric match (intersection volume) with " \
          "coordinate transformation to handle different internal origins."


from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    RevitLinkInstance,
    Solid,
    BooleanOperationsUtils,
    BooleanOperationsType,
    Transaction,
    View,
    ViewType,
    GeometryInstance,
    Transform,
    XYZ
)

from pyrevit import revit, forms, script

# Setup
doc = revit.doc
uidoc = revit.uidoc
logger = script.get_logger()
output = script.get_output()

# Revit API Options for geometry extraction
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


def get_transformed_solid(element, transform=None):
    """
    Extracts the solid geometry from a given element with optional coordinate transformation.
    
    This function handles GeometryInstance objects which are common in family-based elements.
    When a transform is provided (from linked model), it will be stored and used during
    intersection calculations.
    
    Args:
        element: The Revit element to extract geometry from.
        transform: Optional Transform to apply to the geometry (for linked elements).
                  The transform is stored for use during intersection calculations.
    
    Returns:
        tuple: (Solid, Transform) - The extracted solid geometry and the transform,
               or (None, None) if extraction fails.
    """
    geom_element = element.get_Geometry(options)
    if not geom_element:
        return None, transform

    solids = []
    for geom_obj in geom_element:
        if isinstance(geom_obj, Solid) and geom_obj.Volume > 0:
            solids.append(geom_obj)
        elif isinstance(geom_obj, GeometryInstance):
            # Handle geometry instances (common for families)
            instance_geom = geom_obj.GetInstanceGeometry()
            if instance_geom:
                for inst_obj in instance_geom:
                    if isinstance(inst_obj, Solid) and inst_obj.Volume > 0:
                        solids.append(inst_obj)
    
    if not solids:
        return None, transform
    
    # If multiple solids, unite them into one for accurate volume calculation
    if len(solids) > 1:
        main_solid = solids[0]
        for s in solids[1:]:
            try:
                main_solid = BooleanOperationsUtils.ExecuteBooleanOperation(
                    main_solid, s, BooleanOperationsType.Union
                )
            except Exception as e:
                logger.warning("Could not unite solids for element {}. Error: {}".format(
                    element.Id, e))
        return main_solid, transform
    
    return solids[0], transform


def find_best_match(host_beam, linked_beams_dict, link_transform=None):
    """
    Finds the best matching linked beam for a host beam based on intersection volume.
    
    The matching algorithm calculates the geometric intersection volume between
    the host beam and all linked beams. The linked beam with the largest
    intersection volume is considered the best match.
    
    Args:
        host_beam (Element): The beam in the host model.
        linked_beams_dict (dict): Dictionary of {ElementId: {'element': Element, 'solid': Solid}}
                                  from the linked model.
        link_transform (Transform): The transformation matrix from the linked model.
                                    Used to transform linked solids for accurate intersection.
        
    Returns:
        Element: The best matching beam from the linked model, or None.
    """
    host_solid, _ = get_transformed_solid(host_beam)
    if not host_solid:
        return None

    best_match = None
    max_intersection_volume = 0.0

    for linked_beam_id, linked_beam_data in linked_beams_dict.items():
        linked_solid = linked_beam_data['solid']
        if not linked_solid:
            continue

        try:
            # Calculate intersection between host and linked solids
            # Note: For linked models, the transform is already applied via GetTotalTransform
            # when extracting geometry from the linked document
            intersection_solid = BooleanOperationsUtils.ExecuteBooleanOperation(
                host_solid, linked_solid, BooleanOperationsType.Intersect
            )
            
            # Check if intersection exists and has positive volume
            if intersection_solid and intersection_solid.Volume > max_intersection_volume:
                max_intersection_volume = intersection_solid.Volume
                best_match = linked_beam_data['element']

        except Exception as e:
            # Boolean operation can fail if solids are disjoint or have geometric issues
            logger.debug("Boolean operation failed between host {} and linked {}. Error: {}".format(
                host_beam.Id, linked_beam_id, e))
            continue
            
    return best_match


def main():
    """
    Main execution logic for transferring Mark parameters.
    
    Workflow:
    1. Select a linked Revit model from available links
    2. Get the coordinate transformation from the linked model
    3. Input the target parameter name for host beams
    4. Collect host beams (from selection or all)
    5. Collect linked beams from the selected model
    6. Pre-calculate solids for linked beams with transform
    7. Find best matches using intersection volume
    8. Copy Mark parameter from linked to host
    9. Report results
    """
    # =========================================================================
    # STEP 1: Select the Linked Model
    # =========================================================================
    link_instances = FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()
    
    if not link_instances:
        forms.alert("No Revit links found in the current project.", exitscript=True)

    # Create a dictionary of link instances for selection
    link_dict = {link.Name: link for link in link_instances}
    
    selected_link_name = forms.SelectFromList.show(
        sorted(link_dict.keys()),
        title='Select Source Linked Revit Model',
        button_name='Select Link',
        multiselect=False
    )
    
    selected_link = link_dict.get(selected_link_name) if selected_link_name else None

    if not selected_link:
        forms.alert("No link selected. Script will exit.", exitscript=True)

    link_doc = selected_link.GetLinkDocument()
    if not link_doc:
        forms.alert("Could not access the document of the selected link. Ensure it is loaded.", exitscript=True)

    # =========================================================================
    # STEP 2: Get the transformation matrix for the linked model
    # =========================================================================
    # This transformation handles different internal origins between host and linked models
    link_transform = selected_link.GetTotalTransform()
    
    if link_transform:
        logger.info("Link transformation matrix:")
        logger.info("  Origin: {}".format(link_transform.Origin))
        logger.info("  BasisX: {}".format(link_transform.BasisX))
        logger.info("  BasisY: {}".format(link_transform.BasisY))
        logger.info("  BasisZ: {}".format(link_transform.BasisZ))
    else:
        logger.warning("Could not get transformation matrix for linked model. Using identity transform.")
        link_transform = Transform.Identity

    # =========================================================================
    # STEP 3: Ask for the target parameter name
    # =========================================================================
    target_param_name = forms.ask_for_string(
        default='Mark',
        prompt='Enter the target parameter name for host beams:',
        title='Target Parameter'
    )

    if not target_param_name:
        forms.alert("No target parameter name entered. Script will exit.", exitscript=True)

    # =========================================================================
    # STEP 4: Collect Beams from Host Model
    # =========================================================================
    selection_ids = uidoc.Selection.GetElementIds()
    host_beams = []

    if selection_ids:
        # If user has pre-selected elements, use them
        for elem_id in selection_ids:
            elem = doc.GetElement(elem_id)
            # Check if the element is a Structural Framing element
            if (elem.Category and
                    elem.Category.Id.IntegerValue == int(BuiltInCategory.OST_StructuralFraming)):
                host_beams.append(elem)
        
        if not host_beams:
            forms.alert("No structural framing elements found in your selection. "
                        "Please select some beams and try again.", exitscript=True)
    else:
        # If nothing is selected, get all structural framing in the project
        host_beams = FilteredElementCollector(doc)\
            .OfCategory(BuiltInCategory.OST_StructuralFraming)\
            .WhereElementIsNotElementType()\
            .ToElements()

    # =========================================================================
    # STEP 5: Collect Beams from Linked Model
    # =========================================================================
    linked_beams = FilteredElementCollector(link_doc)\
        .OfCategory(BuiltInCategory.OST_StructuralFraming)\
        .WhereElementIsNotElementType()\
        .ToElements()

    if not host_beams or not linked_beams:
        forms.alert("No structural framing elements found in the host or linked model.", exitscript=True)

    # =========================================================================
    # STEP 6: Pre-calculate solids for linked beams with transformation
    # =========================================================================
    linked_beams_dict = {}
    with forms.ProgressBar(title='Processing linked beams... ({value} of {max_value})', cancellable=True) as pb:
        for i, beam in enumerate(linked_beams):
            if pb.cancelled:
                forms.alert("Operation cancelled by user during linked beam processing.", exitscript=True)
            pb.update_progress(i, len(linked_beams))
            
            # Get solid with transformation from linked model
            solid, _ = get_transformed_solid(beam, link_transform)
            if solid:
                linked_beams_dict[beam.Id] = {'element': beam, 'solid': solid}

    if not linked_beams_dict:
        forms.alert("Could not extract geometry from any linked beam. "
                    "Please check if the linked model has valid geometry.", exitscript=True)

    # =========================================================================
    # STEP 7: Find best matches using intersection volume
    # =========================================================================
    updates_to_make = []
    unmatched_beams = []

    with forms.ProgressBar(title='Finding matches... ({value} of {max_value})', cancellable=True) as pb:
        for i, host_beam in enumerate(host_beams):
            if pb.cancelled:
                forms.alert("Operation cancelled by user during match finding.", exitscript=True)
            pb.update_progress(i, len(host_beams))
            
            best_match_linked_beam = find_best_match(host_beam, linked_beams_dict, link_transform)
            
            if best_match_linked_beam:
                updates_to_make.append((host_beam, best_match_linked_beam))
            else:
                unmatched_beams.append(host_beam)

    if not updates_to_make:
        forms.alert("No matching beams found between the host and linked model.", exitscript=True)

    # =========================================================================
    # STEP 8: Copy Mark parameter from linked to host
    # =========================================================================
    updated_count = 0
    skipped_count = 0
    results_data = []

    transaction_name = 'Transfer Mark from Linked Model to "{}"'.format(target_param_name)
    
    with Transaction(doc, transaction_name) as t:
        t.Start()
        
        for host_beam, linked_beam in updates_to_make:
            try:
                # Get the Mark parameter from the linked beam
                linked_mark_param = linked_beam.LookupParameter('Mark')
                
                if not linked_mark_param or not linked_mark_param.HasValue:
                    logger.info("Linked beam {} has no Mark value. Skipping.".format(linked_beam.Id))
                    skipped_count += 1
                    continue
                
                linked_mark_value = linked_mark_param.AsString()
                
                if not linked_mark_value:
                    logger.info("Linked beam {} has empty Mark value. Skipping.".format(linked_beam.Id))
                    skipped_count += 1
                    continue
                
                # Get the target parameter from the host beam
                host_mark_param = host_beam.LookupParameter(target_param_name)
                
                if not host_mark_param:
                    logger.warning("Host beam {} does not have parameter '{}'. Skipping.".format(
                        host_beam.Id, target_param_name))
                    skipped_count += 1
                    continue
                
                if host_mark_param.IsReadOnly:
                    logger.warning("Parameter '{}' on host beam {} is read-only. Skipping.".format(
                        target_param_name, host_beam.Id))
                    skipped_count += 1
                    continue
                
                # Copy the Mark value
                host_mark_param.Set(linked_mark_value)
                updated_count += 1
                
                results_data.append([
                    output.linkify(host_beam.Id),
                    host_beam.Name,
                    output.linkify(linked_beam.Id),
                    linked_mark_value
                ])
                
            except Exception as e:
                logger.error("Failed to update beam {}. Error: {}".format(host_beam.Id, e))
                skipped_count += 1
        
        t.Commit()

    # =========================================================================
    # STEP 9: Report results
    # =========================================================================
    output.print_md("## Mark Transfer Report")
    output.print_md("---")
    output.print_md("**Source Linked Model:** {}".format(selected_link_name))
    output.print_md("**Target Parameter:** {}".format(target_param_name))
    output.print_md("**Coordinate Transformation:** Applied")
    output.print_md("---")
    
    # Summary
    total_host = len(host_beams)
    matched = len(updates_to_make)
    output.print_md("**Summary:**")
    output.print_md("- Total host beams processed: **{}**".format(total_host))
    output.print_md("- Successfully updated: **{}**".format(updated_count))
    output.print_md("- Skipped (no match/error): **{}**".format(skipped_count))
    output.print_md("- Unmatched (no intersection): **{}**".format(len(unmatched_beams)))

    # Show detailed results
    if results_data:
        output.print_md("---")
        output.print_md("### Updated Beams")
        
        # Limit display to prevent performance issues
        max_display = 20
        display_data = results_data[:max_display]
        
        output.print_table(
            table_data=display_data,
            title="Updated Beams",
            columns=["Host Beam ID", "Host Type Name", "Linked Beam ID", "Mark Value"]
        )

        if len(results_data) > max_display:
            output.print_md("*Showing first {} of {} updated beams*".format(
                max_display, len(results_data)))

    # Show unmatched beams
    if unmatched_beams:
        output.print_md("---")
        output.print_md("### Unmatched Beams")
        output.print_md("The following {} beams in the host model could not be matched to any beam in the linked model:".format(
            len(unmatched_beams)))
        
        max_display = 10
        unmatched_data = []
        
        for i, beam in enumerate(unmatched_beams):
            if i >= max_display:
                break
            unmatched_data.append([
                output.linkify(beam.Id),
                beam.Name
            ])
        
        if len(unmatched_beams) > max_display:
            output.print_md("*Showing first {} of {} unmatched beams*".format(
                max_display, len(unmatched_beams)))
        
        output.print_table(
            table_data=unmatched_data,
            title="Unmatched Beams",
            columns=["Beam ID", "Type Name"]
        )

    # Final alert
    forms.alert(
        "Successfully updated {} of {} host beams.".format(updated_count, total_host),
        title="Process Complete"
    )


if __name__ == '__main__':
    main()
