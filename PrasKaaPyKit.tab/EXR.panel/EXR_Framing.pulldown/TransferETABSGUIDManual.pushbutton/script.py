# -*- coding: utf-8 -*-
"""
Transfer ETABS GUID Parameter from Linked Model using Manual Beam Selection.

This script allows manual pairing of beams between host and linked models.
Users select one beam from the host project, then one beam from the linked file.
The ETABS GUID value is automatically extracted from the linked beam's parameters
and transferred to the host beam's 'Reference ETABS GUID' parameter.

The process continues in a loop until ESC is pressed.
"""

__title__ = 'Transfer ETABS\nGUID Manual'
__author__ = 'PrasKaa+KiloCode'
__doc__ = "Manually pair beams between host and linked models to transfer ETABS GUID values " \
          "from linked beams to host beams. Press ESC to exit the continuous selection loop."

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
    Element,
    BuiltInParameter,
    StorageType
)
from Autodesk.Revit.UI.Selection import ObjectType

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
            logger.debug("Found ETABS GUID: '{}' for linked beam {}".format(guid_value, linked_beam.Id))
            return guid_value

    # Try alternative parameter names
    alt_names = ['ETABS_GUID', 'ETABS-GUID', 'ETABS ID', 'ETABS_ID']
    for alt_name in alt_names:
        alt_param = linked_beam.LookupParameter(alt_name)
        if alt_param and alt_param.HasValue:
            guid_value = alt_param.AsString()
            if guid_value:
                logger.debug("Found ETABS GUID using alt name '{}': '{}' for linked beam {}".format(
                    alt_name, guid_value, linked_beam.Id))
                return guid_value

    logger.warning("Could not find ETABS GUID parameter for linked beam {}".format(linked_beam.Id))
    return None


def get_beam_info(beam, is_linked=False):
    """Get formatted information about a beam."""
    beam_type = beam.Document.GetElement(beam.GetTypeId())
    type_name = "N/A"
    if beam_type:
        type_name_param = beam_type.LookupParameter('Type Name')
        if type_name_param:
            type_name = type_name_param.AsString() or "N/A"

    mark_param = beam.LookupParameter('Mark')
    current_mark = mark_param.AsString() if mark_param else "N/A"

    # Get Reference ETABS GUID for host beams
    ref_guid = "N/A"
    if not is_linked:
        ref_guid_param = beam.LookupParameter('Reference ETABS GUID')
        if ref_guid_param and ref_guid_param.HasValue:
            ref_guid = ref_guid_param.AsString() or "N/A"

    prefix = "Linked" if is_linked else "Host"
    return {
        'element': beam,
        'type_name': type_name,
        'current_mark': current_mark,
        'ref_etabs_guid': ref_guid,
        'prefix': prefix,
        'id': beam.Id
    }


def select_linked_model():
    """Select the linked model for GUID transfer."""
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

    return link_doc


def select_beam_interactive(prompt, is_linked=False):
    """Interactive beam selection using Revit selection tool."""
    try:
        if is_linked:
            # For linked beams, we need to use PickObject with linked instance
            ref = uidoc.Selection.PickObject(
                ObjectType.LinkedElement,
                prompt
            )
            # Get the linked element
            link_instance = doc.GetElement(ref.ElementId)
            if isinstance(link_instance, RevitLinkInstance):
                link_doc = link_instance.GetLinkDocument()
                return link_doc.GetElement(ref.LinkedElementId)
        else:
            # For host beams
            ref = uidoc.Selection.PickObject(
                ObjectType.Element,
                prompt
            )
            return doc.GetElement(ref.ElementId)
    except Exception as e:
        # User pressed ESC or cancelled
        return None


def validate_beam(element):
    """Validate if the selected element is a structural framing beam."""
    if not element:
        return False

    return (element.Category and
            element.Category.Id.IntegerValue == int(BuiltInCategory.OST_StructuralFraming))


def get_beam_dimensions(beam):
    """
    Extracts dimension parameters from a beam element.
    Returns dimensions in FEET (Revit internal units) - conversion to mm done in compare_dimensions.

    Args:
        beam (Element): The beam element to extract dimensions from.

    Returns:
        dict or None: Dictionary with dimension values, or None if parameters not found.
            Format: {'b': float, 'h': float, 'type': str}
            type can be: 'rectangular', 'square', or 'unknown'
    """
    try:
        # Try to get 'b' parameter (width/depth) - check both instance and type parameters
        b_param = beam.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_WIDTH)
        if not b_param or not b_param.HasValue:
            # Check instance level first
            b_param = beam.LookupParameter("b") or beam.LookupParameter("B") or beam.LookupParameter("Width")
            # If not found in instance, check type level
            if not b_param and beam.Symbol:
                b_param = beam.Symbol.LookupParameter("b") or beam.Symbol.LookupParameter("B") or beam.Symbol.LookupParameter("Width")

        # Try to get 'h' parameter (height) - check both instance and type parameters
        h_param = beam.get_Parameter(BuiltInParameter.STRUCTURAL_SECTION_COMMON_HEIGHT)
        if not h_param or not h_param.HasValue:
            # Check instance level first
            h_param = beam.LookupParameter("h") or beam.LookupParameter("H") or beam.LookupParameter("Height")
            # If not found in instance, check type level
            if not h_param and beam.Symbol:
                h_param = beam.Symbol.LookupParameter("h") or beam.Symbol.LookupParameter("H") or beam.Symbol.LookupParameter("Height")

        # Extract values (in feet - Revit internal units)
        b_value = b_param.AsDouble() if b_param and b_param.HasValue else None
        h_value = h_param.AsDouble() if h_param and h_param.HasValue else None

        # Determine beam type and return appropriate dimensions
        if b_value is not None and h_value is not None:
            if abs(b_value - h_value) < 1e-6:  # Consider equal if difference < 0.001mm (converted to feet)
                # Square beam (b ≈ h)
                return {
                    'b': b_value,
                    'type': 'square'
                }
            else:
                # Rectangular beam
                return {
                    'b': b_value,
                    'h': h_value,
                    'type': 'rectangular'
                }
        elif b_value is not None:
            # Assume square if only b is available
            return {
                'b': b_value,
                'type': 'square'
            }
        else:
            logger.warning("No dimension parameters found for beam {}".format(beam.Id))
            return None

    except Exception as e:
        logger.warning("Failed to get dimensions for beam {}. Error: {}".format(beam.Id, e))
        return None


def get_family_type(beam):
    """
    Retrieves the FamilySymbol (family type) of a given beam element.

    Args:
        beam (Element): The structural framing element to get the type for.

    Returns:
        FamilySymbol or None: The family symbol of the beam, or None if not found.
    """
    try:
        beam_type_id = beam.GetTypeId()
        if beam_type_id:
            beam_type = beam.Document.GetElement(beam_type_id)
            if beam_type and hasattr(beam_type, 'Family') and beam_type.Family and hasattr(beam_type.Family, 'Name'):
                return beam_type
    except Exception as e:
        logger.debug("Failed to get family type for beam {}. Error: {}".format(beam.Id, e))
    return None


def get_family_geometry_type(beam):
    """
    Detects family geometry type by checking family/type names first, then parameters.

    This function prioritizes family and type names to determine geometry type,
    falling back to parameter analysis if names don't provide clear indication.

    Args:
        beam (Element): The beam element to analyze

    Returns:
        str: Geometry type ('circular', 'square', 'rectangular', or 'unknown')
    """
    try:
        # Get family symbol for name-based detection
        family_symbol = get_family_type(beam)
        if not family_symbol:
            logger.debug("No family symbol found for beam {}, using parameter detection".format(beam.Id))
            # Fallback to parameter-based detection
            dims = get_beam_dimensions(beam)
            if dims and 'type' in dims:
                logger.debug("Detected {} from parameters for beam {}".format(dims['type'], beam.Id))
                return dims['type']
            return 'unknown'

        # Get names with proper null checking
        family_name = ""
        type_name = ""

        try:
            if family_symbol.Family and hasattr(family_symbol.Family, 'Name') and family_symbol.Family.Name:
                family_name = str(family_symbol.Family.Name).lower()
        except Exception as e:
            logger.debug("Could not get family name for beam {}: {}".format(beam.Id, e))

        try:
            if hasattr(family_symbol, 'Name') and family_symbol.Name:
                type_name = str(family_symbol.Name).lower()
        except Exception as e:
            logger.debug("Could not get type name for beam {}: {}".format(beam.Id, e))

        # Log for debugging
        logger.debug("Analyzing beam {}: Family='{}', Type='{}'".format(
            beam.Id, family_name, type_name))

        # If both names are empty, skip to parameter detection
        if not family_name and not type_name:
            logger.debug("Both family and type names empty for beam {}, using parameter detection".format(beam.Id))
            dims = get_beam_dimensions(beam)
            if dims and 'type' in dims:
                logger.debug("Detected {} from parameters for beam {}".format(dims['type'], beam.Id))
                return dims['type']
            return 'unknown'

        # Check for circular indicators
        circular_keywords = ['round', 'circular', 'circle', 'pipe', 'tube', 'diameter', 'ø', 'bulat']
        for keyword in circular_keywords:
            if keyword in family_name or keyword in type_name:
                logger.debug("Detected circular from keyword '{}' for beam {}".format(keyword, beam.Id))
                return 'circular'

        # Check for square indicators
        square_keywords = ['square', 'box', 'kuadrat']
        for keyword in square_keywords:
            if keyword in family_name or keyword in type_name:
                logger.debug("Detected square from keyword '{}' for beam {}".format(keyword, beam.Id))
                return 'square'

        # Check for rectangular indicators
        rectangular_keywords = ['rectangular', 'rectangle', 'rect', 'persegi panjang']
        for keyword in rectangular_keywords:
            if keyword in family_name or keyword in type_name:
                logger.debug("Detected rectangular from keyword '{}' for beam {}".format(keyword, beam.Id))
                return 'rectangular'

        # Parse family name with dash/underscore separators
        all_parts = []

        # Split family name by common separators
        if family_name:
            for separator in ['-', '_', ' ']:
                if separator in family_name:
                    all_parts.extend([part.strip() for part in family_name.split(separator)])
                    break
            else:
                # No separator found, use whole name
                all_parts.append(family_name)

        # Split type name by common separators
        if type_name:
            for separator in ['-', '_', ' ']:
                if separator in type_name:
                    all_parts.extend([part.strip() for part in type_name.split(separator)])
                    break
            else:
                # No separator found, use whole name
                all_parts.append(type_name)

        # Check each part for geometry type keywords
        for part in all_parts:
            part_lower = part.lower()

            # Check circular
            if part_lower in ['circular', 'circle', 'round', 'pipe', 'tube', 'bulat']:
                logger.debug("Detected circular from part '{}' for beam {}".format(part, beam.Id))
                return 'circular'

            # Check square
            if part_lower in ['square', 'box', 'kuadrat']:
                logger.debug("Detected square from part '{}' for beam {}".format(part, beam.Id))
                return 'square'

            # Check rectangular
            if part_lower in ['rectangular', 'rectangle', 'rect']:
                logger.debug("Detected rectangular from part '{}' for beam {}".format(part, beam.Id))
                return 'rectangular'

        # Fallback to parameter-based detection
        logger.debug("Name-based detection inconclusive for beam {}, using parameter detection".format(beam.Id))
        dims = get_beam_dimensions(beam)
        if dims and 'type' in dims:
            logger.debug("Detected {} from parameters for beam {}".format(dims['type'], beam.Id))
            return dims['type']

        logger.debug("Could not detect geometry type for beam {}".format(beam.Id))
        return 'unknown'

    except Exception as e:
        logger.warning("Error detecting family geometry type for beam {}: {}".format(beam.Id, e))
        # Even in error, try parameter detection as last resort
        try:
            dims = get_beam_dimensions(beam)
            if dims and 'type' in dims:
                logger.debug("Fallback: Detected {} from parameters for beam {} after error".format(dims['type'], beam.Id))
                return dims['type']
        except:
            pass
        return 'unknown'


def compare_dimensions(host_dims, linked_dims):
    """
    Compares dimension parameters between host and linked beams.
    Converts feet to millimeters FIRST, then compares with 0.01mm tolerance.

    Args:
        host_dims (dict): Dimension dictionary from host beam (in feet)
        linked_dims (dict): Dimension dictionary from linked beam (in feet)

    Returns:
        bool: True if dimensions match within tolerance, False otherwise
    """
    if not host_dims or not linked_dims:
        return False

    if host_dims.get('type') != linked_dims.get('type'):
        return False

    # Import UnitUtils with fallback for compatibility
    try:
        from Autodesk.Revit.DB import UnitUtils, UnitTypeId
        USE_NEW_API = True
    except ImportError:
        from Autodesk.Revit.DB import UnitUtils
        USE_NEW_API = False

    # Tolerance in mm (not converted to feet)
    tolerance_mm = 0.01

    # Helper function to convert feet to mm
    def feet_to_mm(feet_value):
        if USE_NEW_API:
            return UnitUtils.ConvertFromInternalUnits(feet_value, UnitTypeId.Millimeters)
        else:
            # Fallback: manual conversion for older Revit versions
            return feet_value * 304.8

    if host_dims['type'] == 'square':
        host_b = host_dims.get('b')
        linked_b = linked_dims.get('b')
        if host_b is None or linked_b is None:
            return False

        # Convert to mm first, then compare
        host_b_mm = feet_to_mm(host_b)
        linked_b_mm = feet_to_mm(linked_b)
        diff_mm = abs(host_b_mm - linked_b_mm)
        match = diff_mm <= tolerance_mm

        if not match:
            logger.debug("Square dimension mismatch: host_b={:.2f}mm, linked_b={:.2f}mm, diff={:.2f}mm".format(
                host_b_mm, linked_b_mm, diff_mm))
        return match

    elif host_dims['type'] == 'rectangular':
        host_b = host_dims.get('b')
        host_h = host_dims.get('h')
        linked_b = linked_dims.get('b')
        linked_h = linked_dims.get('h')
        if None in [host_b, host_h, linked_b, linked_h]:
            return False

        # Convert to mm first, then compare
        host_b_mm = feet_to_mm(host_b)
        host_h_mm = feet_to_mm(host_h)
        linked_b_mm = feet_to_mm(linked_b)
        linked_h_mm = feet_to_mm(linked_h)

        b_diff_mm = abs(host_b_mm - linked_b_mm)
        h_diff_mm = abs(host_h_mm - linked_h_mm)

        b_match = b_diff_mm <= tolerance_mm
        h_match = h_diff_mm <= tolerance_mm

        if not (b_match and h_match):
            logger.debug("Rectangular dimension mismatch: host_b={:.2f}mm, linked_b={:.2f}mm (diff={:.2f}mm), host_h={:.2f}mm, linked_h={:.2f}mm (diff={:.2f}mm)".format(
                host_b_mm, linked_b_mm, b_diff_mm, host_h_mm, linked_h_mm, h_diff_mm))
        return b_match and h_match

    return False


def format_dimensions_for_display(dims):
    """
    Format dimensions for display in alerts, converting to mm.

    Args:
        dims (dict): Dimension dictionary with 'type', 'b', 'h' keys

    Returns:
        str: Formatted dimension string like "300x400mm" or "300mm"
    """
    if not dims:
        return "Unknown"

    try:
        from Autodesk.Revit.DB import UnitUtils, UnitTypeId
        USE_NEW_API = True
    except ImportError:
        from Autodesk.Revit.DB import UnitUtils
        USE_NEW_API = False

    def feet_to_mm(feet_value):
        if USE_NEW_API:
            return UnitUtils.ConvertFromInternalUnits(feet_value, UnitTypeId.Millimeters)
        else:
            return feet_value * 304.8

    if dims['type'] == 'square':
        b_mm = feet_to_mm(dims['b'])
        return "{:.0f}mm".format(b_mm)
    elif dims['type'] == 'rectangular':
        b_mm = feet_to_mm(dims['b'])
        h_mm = feet_to_mm(dims['h'])
        return "{:.0f}x{:.0f}mm".format(b_mm, h_mm)
    else:
        return "Unknown"


def main():
    """Main execution logic for manual ETABS GUID transfer."""
    # 1. Setup - Select linked model once
    link_doc = select_linked_model()

    # 2. Continuous loop for manual beam pairing

    transfer_count = 0

    while True:
        try:
            # Select host beam
            host_beam = select_beam_interactive(
                "Select a HOST beam (press ESC to exit)...",
                is_linked=False
            )

            if not host_beam:
                break  # User pressed ESC

            if not validate_beam(host_beam):
                forms.alert("Selected element is not a structural framing beam. Please try again.", exitscript=False)
                continue

            host_info = get_beam_info(host_beam, is_linked=False)

            # Select linked beam
            linked_beam = select_beam_interactive(
                "Select a LINKED beam (press ESC to exit)...",
                is_linked=True
            )

            if not linked_beam:
                break  # User pressed ESC

            if not validate_beam(linked_beam):
                forms.alert("Selected element is not a structural framing beam. Please try again.", exitscript=False)
                continue

            linked_info = get_beam_info(linked_beam, is_linked=True)

            # Check dimensions before GUID transfer - STRICT VALIDATION REQUIRED
            host_dims = get_beam_dimensions(host_beam)
            linked_dims = get_beam_dimensions(linked_beam)

            dimensions_match = False
            if host_dims and linked_dims:
                # Check family geometry types first
                host_family_type = get_family_geometry_type(host_beam)
                linked_family_type = get_family_geometry_type(linked_beam)

                if host_family_type == linked_family_type:
                    # Family types match, now check dimensions
                    dimensions_match = compare_dimensions(host_dims, linked_dims)
                else:
                    logger.debug("Family geometry types don't match: {} vs {}".format(host_family_type, linked_family_type))

            # STRICT RULE: Dimensions MUST match for ETABS GUID transfer
            if not dimensions_match:
                host_dim_str = format_dimensions_for_display(host_dims) if host_dims else "Unknown"
                linked_dim_str = format_dimensions_for_display(linked_dims) if linked_dims else "Unknown"

                forms.alert(("❌ ETABS GUID transfer FORBIDDEN!\n\n"
                            "Dimensions do not match:\n"
                            "Host beam: {}\n"
                            "Linked beam: {}\n\n"
                            "ETABS GUID transfer is only allowed for beams with identical dimensions.").format(
                    host_dim_str, linked_dim_str), exitscript=False)
                continue

            # Dimensions match - proceed with automatic transfer (no confirmation needed)
            logger.info("Dimensions match for beams {} and {}. Proceeding with automatic ETABS GUID transfer.".format(
                host_beam.Id, linked_beam.Id))

            # Extract ETABS GUID from linked beam
            etabs_guid_value = extract_etabs_guid_from_linked_beam(linked_beam)
            if not etabs_guid_value:
                forms.alert("Could not extract ETABS GUID value from linked beam. Please check if the linked beam has 'ETABS GUID' parameter.", exitscript=False)
                continue

            # Perform the GUID transfer automatically
            host_guid_param = host_beam.LookupParameter('Reference ETABS GUID')
            if not host_guid_param or host_guid_param.IsReadOnly:
                forms.alert("Cannot set 'Reference ETABS GUID' parameter on selected host beam. Please ensure this parameter exists and is writable.", exitscript=False)
                continue

            # Transaction for single beam update
            transaction_name = 'Transfer ETABS GUID to Beam {}'.format(host_beam.Id)
            with Transaction(doc, transaction_name) as t:
                t.Start()
                host_guid_param.Set(etabs_guid_value)

                # Update Comments to mark as approved with reference
                host_comment_param = host_beam.LookupParameter('Comments')
                if host_comment_param and not host_comment_param.IsReadOnly:
                    host_comment_param.Set('Approved w referenced')
                    logger.debug("Updated Comments to 'Approved w referenced' for beam {}".format(host_beam.Id))

                t.Commit()

            transfer_count += 1
            logger.info("Successfully transferred ETABS GUID '{}' to host beam {} and marked as 'Approved w referenced'".format(
                etabs_guid_value, host_beam.Id))

        except Exception as e:
            logger.error("Error during beam selection: {}".format(str(e)))
            forms.alert("An error occurred: {}. Please try again.".format(str(e)), exitscript=False)
            continue

    # Final report
    forms.alert(
        "Manual ETABS GUID transfer complete.\n\nTransferred GUIDs to {} beams.".format(transfer_count),
        title="Process Complete"
    )


if __name__ == '__main__':
    main()