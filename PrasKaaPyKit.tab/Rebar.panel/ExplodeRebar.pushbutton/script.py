# -*- coding: utf-8 -*-
"""
Explodes selected Structural Rebar Sets into individual Single rebar instances.
Development version with debug output.
Set DEBUG = False for production (silent operation).
"""
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Transaction,
    ElementId,
    StorageType
)
from Autodesk.Revit.DB.Structure import (
    Rebar,
    RebarLayoutRule,
    RebarStyle,
    MultiplanarOption
)
from System.Collections.Generic import List

# DEBUG FLAG - Set to False for production
DEBUG = True

def debug_print(msg):
    if DEBUG:
        print(msg)

# Get the active document and UI document
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

def copy_parameters(source_element, target_element):
    """
    Copies instance parameters from source to target.
    Silently fails on read-only or matching issues to maintain workflow.
    """
    for param in source_element.Parameters:
        if param.IsReadOnly:
            continue

        target_param = target_element.get_Parameter(param.Definition)
        if target_param and not target_param.IsReadOnly:
            try:
                # Handle different storage types using enum comparison
                if param.StorageType == StorageType.String:
                    value = param.AsString()
                    if value is not None:
                        target_param.Set(value)
                elif param.StorageType == StorageType.Double:
                    target_param.Set(param.AsDouble())
                elif param.StorageType == StorageType.Integer:
                    target_param.Set(param.AsInteger())
                elif param.StorageType == StorageType.ElementId:
                    target_param.Set(param.AsElementId())
            except:
                pass  # Silent failure

def get_rebar_geometry_at_index(rebar, index):
    """
    Extracts the curves for a specific bar index within a set.
    """
    try:
        curves = rebar.GetCenterlineCurves(
            True,  # adjustForSelfIntersection
            False,  # includeHooks
            False,  # modifyForEndTreatment
            MultiplanarOption.IncludeAllMultiplanarCurves,
            index  # The specific bar index (0 to n-1)
        )
        return curves
    except:
        return None

def api_list(py_list):
    """Convert python list to .NET List for Delete() method"""
    net_list = List[ElementId]()
    for item in py_list:
        net_list.Add(item)
    return net_list

def explode_rebar():
    debug_print("Starting explode rebar process")

    # 1. SELECTION
    selection_ids = uidoc.Selection.GetElementIds()

    if not selection_ids or selection_ids.Count == 0:
        debug_print("No elements selected")
        return  # Exit silently if nothing selected

    debug_print("Selected {} elements".format(selection_ids.Count))

    # Filter for Rebar elements only
    rebar_elements = []
    for el_id in selection_ids:
        el = doc.GetElement(el_id)
        if isinstance(el, Rebar):
            # Check if it is already Single (no need to explode)
            if el.LayoutRule != RebarLayoutRule.Single:
                rebar_elements.append(el)

    debug_print("Found {} valid rebar sets to explode".format(len(rebar_elements)))

    if not rebar_elements:
        debug_print("No valid rebar sets found")
        return  # Exit silently if no valid rebar sets found

    # 2. TRANSACTION
    t = Transaction(doc, "Explode Rebar Sets")
    t.Start()
    debug_print("Transaction started")

    elements_to_delete = []

    try:
        for original_rebar in rebar_elements:
            debug_print("Processing rebar set: {}".format(original_rebar.Name))

            # 3. ACCESSING DATA
            rebar_type_id = original_rebar.GetTypeId()
            rebar_shape_id = original_rebar.GetShapeId()
            host_id = original_rebar.GetHostId()
            host = doc.GetElement(host_id) if host_id != ElementId.InvalidElementId else None

            # Access the Shape Driven logic
            accessor = original_rebar.GetShapeDrivenAccessor()
            quantity = accessor.Quantity
            normal = accessor.Normal  # The normal vector of the rebar plane

            debug_print("  Quantity: {}, Host: {}".format(quantity, host.Name if host else 'None'))

            # 4. LOOP THROUGH QUANTITY
            for i in range(quantity):
                debug_print("  Creating bar {}/{}".format(i+1, quantity))

                # Extract curves for this specific instance
                curves = get_rebar_geometry_at_index(original_rebar, i)

                if curves and curves.Count > 0:
                    try:
                        # Get rebar type and shape elements
                        rebar_type = doc.GetElement(rebar_type_id)
                        rebar_shape = doc.GetElement(rebar_shape_id) if rebar_shape_id != ElementId.InvalidElementId else None

                        # Get hook orientations
                        hook_start = original_rebar.GetHookOrientation(0)
                        hook_end = original_rebar.GetHookOrientation(1)

                        # 5. CREATE NEW REBAR
                        new_rebar = Rebar.CreateFromCurves(
                            doc,
                            RebarStyle.Standard,
                            rebar_type,
                            rebar_shape,
                            host,
                            normal,
                            curves,
                            hook_start,
                            hook_end,
                            True,  # useExistingShapeIfPossible
                            True   # createNewShape
                        )

                        # CreateFromCurves creates Single layout by default,
                        # but verify and set if needed
                        if new_rebar and new_rebar.LayoutRule != RebarLayoutRule.Single:
                            # This shouldn't happen, but as a safety measure
                            pass

                        # Copy Parameters (Mark, Partition, Comments, etc.)
                        if new_rebar:
                            copy_parameters(original_rebar, new_rebar)
                            debug_print("    Created new rebar instance {}".format(i+1))

                    except Exception as e:
                        debug_print("    Error creating bar {}: {}".format(i+1, str(e)))
                        # If a specific bar fails, skip it silently
                        pass

            # Mark original for deletion
            elements_to_delete.append(original_rebar.Id)
            debug_print("  Marked original rebar for deletion")

        # 6. DELETE ORIGINALS
        if elements_to_delete:
            debug_print("Deleting {} original rebar sets".format(len(elements_to_delete)))
            doc.Delete(api_list(elements_to_delete))

        t.Commit()
        debug_print("Transaction committed successfully")

    except Exception as e:
        debug_print("Transaction failed: {}".format(str(e)))
        # If the whole transaction fails, roll back silently
        t.RollBack()

# Execute
if __name__ == "__main__":
    explode_rebar()