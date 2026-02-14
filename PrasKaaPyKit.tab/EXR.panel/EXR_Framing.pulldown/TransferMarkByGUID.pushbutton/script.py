# -*- coding: utf-8 -*-
"""
Transfer Mark Parameter from Linked Model Type Name based on ETABS GUID Parameter Matching.

This script finds pairs of Structural Framing elements (beams) between the host
model and a selected linked model. The matching is done by comparing the
'Reference ETABS GUID' parameter in host beams with the 'ETABS GUID' parameter
in linked beams.

It then extracts the mark value from the 'Type Name' parameter of linked beams
(e.g., "G9-99" -> "99", "G5.99" -> "99") and copies it to the 'Mark' parameter
of the corresponding host beams.
"""

__title__ = 'Transfer Mark\nby GUID'
__author__ = 'PrasKaa+KiloCode'
__doc__ = "Extracts mark value from Type Name of linked beams and copies to host beams " \
          "by matching 'Reference ETABS GUID' parameter with 'ETABS GUID' parameter."


import re
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    RevitLinkInstance,
    ElementId,
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


def extract_etabs_guid_from_linked_beam(linked_beam):
    """
    Extracts the ETABS GUID value from a linked beam element.
    Looks for 'ETABS GUID' parameter in the linked beam.

    Args:
        linked_beam (Element): The linked beam element

    Returns:
        str: The ETABS GUID value or None if not found
    """
    if not linked_beam:
        return None

    # Try to get ETABS GUID parameter
    etabs_guid_param = linked_beam.LookupParameter('ETABS GUID')
    if etabs_guid_param and etabs_guid_param.HasValue:
        guid_value = etabs_guid_param.AsString()
        if guid_value:
            return guid_value

    # Try alternative parameter names
    alt_names = ['ETABS_GUID', 'ETABS-GUID', 'ETABS ID', 'ETABS_ID']
    for alt_name in alt_names:
        alt_param = linked_beam.LookupParameter(alt_name)
        if alt_param and alt_param.HasValue:
            guid_value = alt_param.AsString()
            if guid_value:
                return guid_value

    return None


def get_reference_etabs_guid_from_host_beam(host_beam):
    """
    Extracts the Reference ETABS GUID value from a host beam element.

    Args:
        host_beam (Element): The host beam element

    Returns:
        str: The Reference ETABS GUID value or None if not found
    """
    if not host_beam:
        return None

    ref_guid_param = host_beam.LookupParameter('Reference ETABS GUID')
    if ref_guid_param and ref_guid_param.HasValue:
        guid_value = ref_guid_param.AsString()
        if guid_value:
            return guid_value

    return None


def find_matching_linked_beam_by_guid(host_beam, linked_beams_dict):
    """
    Finds the matching linked beam for a host beam based on ETABS GUID parameter matching.

    Args:
        host_beam (Element): The host beam to match
        linked_beams_dict (dict): Dictionary mapping ETABS GUID to linked beam elements

    Returns:
        Element: The matching linked beam or None if no match found
    """
    host_ref_guid = get_reference_etabs_guid_from_host_beam(host_beam)
    if not host_ref_guid:
        logger.debug("No Reference ETABS GUID found for host beam {}".format(host_beam.Id))
        return None

    # Look up the matching linked beam
    matching_linked_beam = linked_beams_dict.get(host_ref_guid)
    if matching_linked_beam:
        logger.debug("Found GUID match for host beam {}: '{}' -> linked beam {}".format(
            host_beam.Id, host_ref_guid, matching_linked_beam.Id))
        return matching_linked_beam
    else:
        logger.debug("No linked beam found with ETABS GUID '{}' for host beam {}".format(
            host_ref_guid, host_beam.Id))
        return None


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
        title='Select Source Linked EXR Model (from ETABS)',
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

    # 3. Build linked beams dictionary by ETABS GUID
    linked_beams_by_guid = {}
    guid_extraction_fail_count = 0

    with forms.ProgressBar(title='Processing linked beams... ({value} of {max_value})', cancellable=True) as pb:
        for i, beam in enumerate(linked_beams):
            if pb.cancelled:
                forms.alert("Operation cancelled by user during linked beam processing.", exitscript=True)
            pb.update_progress(i, len(linked_beams))

            etabs_guid = extract_etabs_guid_from_linked_beam(beam)
            if etabs_guid:
                linked_beams_by_guid[etabs_guid] = beam
            else:
                guid_extraction_fail_count += 1

    logger.info("Processed {} linked beams: {} with valid ETABS GUID, {} without".format(
        len(linked_beams), len(linked_beams_by_guid), guid_extraction_fail_count))

    # 4. Find matches and prepare data for update
    updates_to_make = []
    no_guid_beams = []
    no_match_beams = []

    with forms.ProgressBar(title='Finding matches by GUID... ({value} of {max_value})', cancellable=True) as pb:
        for i, host_beam in enumerate(host_beams):
            if pb.cancelled:
                forms.alert("Operation cancelled by user during match finding.", exitscript=True)
            pb.update_progress(i, len(host_beams))

            host_ref_guid = get_reference_etabs_guid_from_host_beam(host_beam)
            if not host_ref_guid:
                no_guid_beams.append(host_beam)
                continue

            matching_linked_beam = find_matching_linked_beam_by_guid(host_beam, linked_beams_by_guid)
            if matching_linked_beam:
                updates_to_make.append((host_beam, matching_linked_beam))
            else:
                no_match_beams.append(host_beam)

    if not updates_to_make:
        forms.alert("No matching beams found between the host and linked model based on GUID matching.", exitscript=True)

    # 5. Perform the update within a transaction
    updated_count = 0
    extraction_fail_count = 0
    results_data = []
    extraction_fail_data = []
    transaction_name = 'Transfer Beam Marks by GUID to "{}"'.format(target_param_name)
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
                            # Mark extraction failed
                            extraction_fail_count += 1
                            extraction_fail_data.append([
                                output.linkify(host_beam.Id),
                                host_beam.Name,
                                output.linkify(linked_beam.Id),
                                type_name or "N/A",
                                'Mark extraction failed'
                            ])
            except Exception as e:
                logger.error("Failed to update beam {}. Error: {}".format(host_beam.Id, e))

        t.Commit()

    # 6. Report results
    output.print_md("## Mark Transfer by GUID Report")
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

    # Report beams without Reference ETABS GUID
    if no_guid_beams:
        output.print_md("### Beams Without Reference ETABS GUID")
        output.print_md("The following {} beams in the host model do not have 'Reference ETABS GUID' parameter set:".format(len(no_guid_beams)))

        # Prepare table data for beams without GUID
        no_guid_data = []
        max_display = 5  # Limit display

        for i, beam in enumerate(no_guid_beams):
            if i >= max_display:
                break
            no_guid_data.append([
                output.linkify(beam.Id),
                beam.Name
            ])

        if len(no_guid_beams) > max_display:
            output.print_md("*Showing first {} of {} beams without GUID for performance*".format(max_display, len(no_guid_beams)))

        output.print_table(
            table_data=no_guid_data,
            title="Beams Without Reference ETABS GUID",
            columns=["Beam ID", "Type Name"]
        )

    # Report beams with GUID but no match found
    if no_match_beams:
        output.print_md("### Beams With GUID But No Match Found")
        output.print_md("The following {} beams have 'Reference ETABS GUID' but no matching linked beam was found:".format(len(no_match_beams)))

        # Prepare table data for unmatched beams
        no_match_data = []
        max_display = 5  # Limit display

        for i, beam in enumerate(no_match_beams):
            if i >= max_display:
                break
            ref_guid = get_reference_etabs_guid_from_host_beam(beam)
            no_match_data.append([
                output.linkify(beam.Id),
                beam.Name,
                ref_guid or "N/A"
            ])

        if len(no_match_beams) > max_display:
            output.print_md("*Showing first {} of {} unmatched beams for performance*".format(max_display, len(no_match_beams)))

        output.print_table(
            table_data=no_match_data,
            title="Beams With GUID But No Match",
            columns=["Beam ID", "Type Name", "Reference ETABS GUID"]
        )


if __name__ == '__main__':
    main()