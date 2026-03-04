# -*- coding: utf-8 -*-
__title__ = "Convert Linked Roof\nto Floor"
__author__ = 'PrasKaa Team'
__version__ = '1.0'
__doc__ = """Version: 1.0
Date    = 04.03.2026
_____________________________________________________________________
Description:
Converts a selected roof from a linked model to a floor instance in the current model.

How-to:
1. Click the tool button
2. Hover over a ROOF in the linked model
3. Press TAB key to highlight the roof
4. Click to select
5. Select floor type from the list
6. Select level for the floor
7. Floor is created automatically

Notes:
- Only works with roof elements from linked Revit models
- Requires the linked model to be loaded
- Boundary curves are extracted automatically using multiple methods

_____________________________________________________
Last update:
- 04.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa Team
"""

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from pyrevit import revit, DB, UI, forms
from System.Collections.Generic import List  # <- TAMBAHKAN INI
import math

doc = revit.doc
uidoc = revit.uidoc

class LinkedRoofFilter(ISelectionFilter):
    """Filter to allow only roof selection from linked models"""
    
    def AllowElement(self, element):
        if isinstance(element, RevitLinkInstance):
            return True
        return False
    
    def AllowReference(self, reference, position):
        return True

def sort_and_connect_curves(curves, tolerance=0.001):
    """Sort curves to form a continuous loop"""
    if not curves or len(curves) == 0:
        return []
    
    sorted_curves = []
    remaining_curves = list(curves)
    
    # Start with the first curve
    current_curve = remaining_curves.pop(0)
    sorted_curves.append(current_curve)
    current_end = current_curve.GetEndPoint(1)
    
    # Connect remaining curves
    while remaining_curves:
        found = False
        
        for i, curve in enumerate(remaining_curves):
            start = curve.GetEndPoint(0)
            end = curve.GetEndPoint(1)
            
            # Check if start point matches current end
            if current_end.DistanceTo(start) < tolerance:
                sorted_curves.append(curve)
                current_end = end
                remaining_curves.pop(i)
                found = True
                break
            # Check if end point matches current end (need to reverse)
            elif current_end.DistanceTo(end) < tolerance:
                # Create reversed curve
                if isinstance(curve, Line):
                    reversed_curve = Line.CreateBound(end, start)
                elif isinstance(curve, Arc):
                    reversed_curve = Arc.Create(end, start, curve.Evaluate(0.5, True))
                else:
                    reversed_curve = curve.CreateReversed()
                
                sorted_curves.append(reversed_curve)
                current_end = start
                remaining_curves.pop(i)
                found = True
                break
        
        if not found:
            # If no connection found, there might be a gap
            print("Warning: Gap detected in curve loop")
            break
    
    return sorted_curves

def close_curve_loop(curves, tolerance=0.01):
    """Ensure the curve loop is closed by adding a line if needed"""
    if not curves or len(curves) == 0:
        return curves
    
    first_point = curves[0].GetEndPoint(0)
    last_point = curves[-1].GetEndPoint(1)
    
    distance = first_point.DistanceTo(last_point)
    
    if distance > tolerance:
        # Add closing line
        closing_line = Line.CreateBound(last_point, first_point)
        curves.append(closing_line)
        print("Added closing line with length: {} ft".format(distance))
    
    return curves

def get_roof_boundary_curves(roof, transform):
    """Extract boundary curves from roof and transform them"""
    curves = []
    
    try:
        # Method 1: Try to get footprint boundary curves
        print("Trying Method 1: GetFootprintBoundaryCurves...")
        model_curves = roof.GetFootprintBoundaryCurves()
        
        for curve_loop in model_curves:
            for curve in curve_loop:
                transformed_curve = curve.CreateTransformed(transform)
                curves.append(transformed_curve)
        
        if curves:
            print("Method 1 successful: {} curves extracted".format(len(curves)))
            return curves
    except Exception as e:
        print("Method 1 failed: {}".format(str(e)))
    
    try:
        # Method 2: Get from sketch
        print("Trying Method 2: Get from sketch...")
        sketch_id = roof.GetSketchId()
        if sketch_id != ElementId.InvalidElementId:
            sketch = roof.Document.GetElement(sketch_id)
            
            profile = sketch.Profile
            for curve_array in profile:
                for curve in curve_array:
                    transformed_curve = curve.CreateTransformed(transform)
                    curves.append(transformed_curve)
            
            if curves:
                print("Method 2 successful: {} curves extracted".format(len(curves)))
                return curves
    except Exception as e:
        print("Method 2 failed: {}".format(str(e)))
    
    # Method 3: Extract from geometry
    try:
        print("Trying Method 3: Extract from geometry...")
        options = Options()
        options.ComputeReferences = False
        options.DetailLevel = ViewDetailLevel.Fine
        
        geom_elem = roof.get_Geometry(options)
        
        for geom_obj in geom_elem:
            if isinstance(geom_obj, Solid) and geom_obj.Volume > 0:
                faces = geom_obj.Faces
                
                # Find the largest horizontal face
                largest_face = None
                largest_area = 0
                
                for face in faces:
                    if isinstance(face, PlanarFace):
                        normal = face.FaceNormal
                        # Check if face is roughly horizontal
                        if abs(normal.Z) > 0.7:
                            area = face.Area
                            if area > largest_area:
                                largest_area = area
                                largest_face = face
                
                if largest_face:
                    edge_arrays = largest_face.EdgeLoops
                    if edge_arrays.Size > 0:
                        outer_loop = edge_arrays[0]
                        for edge in outer_loop:
                            curve = edge.AsCurve()
                            transformed_curve = curve.CreateTransformed(transform)
                            curves.append(transformed_curve)
                        
                        if curves:
                            print("Method 3 successful: {} curves extracted".format(len(curves)))
                            return curves
                        break
    except Exception as e:
        print("Method 3 failed: {}".format(str(e)))
    
    return curves

# Main script
try:
    # Prompt user to select element from linked model
    print("="*50)
    print("Starting Roof to Floor Conversion")
    print("="*50)
    
    forms.alert(
        "HOW TO SELECT:\n\n" +
        "1. Hover mouse over a ROOF in the linked model\n" +
        "2. Press TAB key to highlight the roof\n" +
        "3. Click to select\n\n" +
        "Ready? Click OK to continue..."
    )
    
    selection_filter = LinkedRoofFilter()
    
    try:
        reference = uidoc.Selection.PickObject(
            ObjectType.LinkedElement,
            selection_filter,
            "Select a ROOF from the linked model"
        )
    except Exception as e:
        forms.alert("Selection cancelled: {}".format(str(e)))
        import sys
        sys.exit()
    
    # Get the link instance
    link_instance = doc.GetElement(reference.ElementId)
    
    if not isinstance(link_instance, RevitLinkInstance):
        forms.alert("Selected element is not from a linked model!")
        import sys
        sys.exit()
    
    # Get the linked document
    linked_doc = link_instance.GetLinkDocument()
    
    if not linked_doc:
        forms.alert("Cannot access linked document!")
        import sys
        sys.exit()
    
    # Get the selected element from linked model
    linked_elem_id = reference.LinkedElementId
    selected_element = linked_doc.GetElement(linked_elem_id)
    
    # Verify it's a roof
    if not isinstance(selected_element, RoofBase):
        forms.alert(
            "Selected element is NOT a roof!\n\n" +
            "Element Type: {}\n".format(type(selected_element).__name__) +
            "Please select a ROOF element."
        )
        import sys
        sys.exit()
    
    print("\nRoof selected:")
    print("  ID: {}".format(selected_element.Id.IntegerValue))
    print("  Type: {}".format(selected_element.Name))
    
    # Get transform from link
    transform = link_instance.GetTotalTransform()
    
    # Extract boundary curves
    print("\nExtracting roof boundary curves...")
    curves = get_roof_boundary_curves(selected_element, transform)
    
    if not curves or len(curves) == 0:
        forms.alert("Could not extract roof boundary curves!")
        import sys
        sys.exit()
    
    print("Extracted {} curves".format(len(curves)))
    
    # Sort and connect curves
    print("\nSorting and connecting curves...")
    sorted_curves = sort_and_connect_curves(curves)
    
    if len(sorted_curves) < len(curves):
        print("Warning: Some curves could not be connected")
        print("  Original: {} curves".format(len(curves)))
        print("  Connected: {} curves".format(len(sorted_curves)))
    
    # Close the loop if needed
    sorted_curves = close_curve_loop(sorted_curves)
    
    print("Final curve count: {}".format(len(sorted_curves)))
    
    # Get floor types
    floor_types = FilteredElementCollector(doc)\
        .OfClass(FloorType)\
        .ToElements()
    
    floor_type_dict = {}
    for ft in floor_types:
        type_name = ft.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
        floor_type_dict[type_name] = ft
    
    selected_floor_type_name = forms.SelectFromList.show(
        sorted(floor_type_dict.keys()),
        title="Select Floor Type",
        button_name="Select"
    )
    
    if not selected_floor_type_name:
        forms.alert("No floor type selected")
        import sys
        sys.exit()
    
    selected_floor_type = floor_type_dict[selected_floor_type_name]
    
    # Get levels
    levels = FilteredElementCollector(doc)\
        .OfClass(Level)\
        .ToElements()
    
    level_dict = {level.Name: level for level in levels}
    
    selected_level_name = forms.SelectFromList.show(
        sorted(level_dict.keys()),
        title="Select Level for Floor",
        button_name="Create Floor"
    )
    
    if not selected_level_name:
        forms.alert("No level selected")
        import sys
        sys.exit()
    
    selected_level = level_dict[selected_level_name]
    
    # Create floor
    print("\nCreating floor...")
    t = Transaction(doc, "Convert Linked Roof to Floor")
    t.Start()
    
    try:
        # Create CurveLoop from sorted curves
        curve_loop = CurveLoop()
        for curve in sorted_curves:
            curve_loop.Append(curve)
        
        curve_loops = List[CurveLoop]()
        curve_loops.Add(curve_loop)
        
        # Create floor
        new_floor = Floor.Create(doc, curve_loops, selected_floor_type.Id, selected_level.Id)
        
        t.Commit()
        
        print("\n" + "="*50)
        print("SUCCESS!")
        print("="*50)
        print("Floor ID: {}".format(new_floor.Id.IntegerValue))
        print("Floor Type: {}".format(selected_floor_type_name))
        print("Level: {}".format(selected_level_name))
        
        forms.alert(
            "✓ SUCCESS!\n\n" +
            "Floor created successfully!\n\n" +
            "Floor ID: {}\n".format(new_floor.Id.IntegerValue) +
            "Type: {}\n".format(selected_floor_type_name) +
            "Level: {}".format(selected_level_name)
        )
        
    except Exception as e:
        t.RollBack()
        error_msg = str(e)
        print("\nERROR: {}".format(error_msg))
        
        forms.alert(
            "Error creating floor:\n\n" +
            "{}\n\n".format(error_msg) +
            "Check the pyRevit output window for details."
        )
        
        import traceback
        print("\nFull traceback:")
        print(traceback.format_exc())

except Exception as e:
    print("\nUNEXPECTED ERROR: {}".format(str(e)))
    forms.alert("Error: {}".format(str(e)))
    import traceback
    print(traceback.format_exc())