# -*- coding: utf-8 -*-
"""Beam Level Offset by Slope
Adjust beam level offsets based on slope/ramp surface projection.
"""
__title__ = "Beam Level\nOffset by Slope"
__author__ = "Your Name"

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType
from pyrevit import revit, DB, UI, forms
import math

doc = revit.doc
uidoc = revit.uidoc

def get_beam_curve(beam):
    """Get beam location curve"""
    location = beam.Location
    if isinstance(location, LocationCurve):
        return location.Curve
    return None

def project_point_to_face(point, face):
    """Project point to face and return elevation"""
    try:
        result = face.Project(point)
        if result:
            return result.XYZPoint.Z
        return None
    except:
        return None

def get_beam_width(beam):
    """Get beam width from parameter 'b'"""
    param = beam.LookupParameter("b")
    if param and param.HasValue:
        return param.AsDouble()
    return None

def get_beam_corners(curve, width, beam):
    """Get 4 bottom corners of beam"""
    try:
        start = curve.GetEndPoint(0)
        end = curve.GetEndPoint(1)
        
        # Get beam direction
        direction = (end - start).Normalize()
        
        # Get perpendicular vector in horizontal plane
        up = XYZ.BasisZ
        perpendicular = direction.CrossProduct(up).Normalize()
        
        # Offset by half width
        half_width = width / 2.0
        
        # 4 corners at bottom
        corners = [
            XYZ(start.X + perpendicular.X * half_width, start.Y + perpendicular.Y * half_width, start.Z),
            XYZ(start.X - perpendicular.X * half_width, start.Y - perpendicular.Y * half_width, start.Z),
            XYZ(end.X + perpendicular.X * half_width, end.Y + perpendicular.Y * half_width, end.Z),
            XYZ(end.X - perpendicular.X * half_width, end.Y - perpendicular.Y * half_width, end.Z)
        ]
        
        return corners
    except:
        return None

def get_base_level_elevation(beam):
    """Get base level elevation from beam Reference Level parameter"""
    ref_level_param = beam.get_Parameter(BuiltInParameter.INSTANCE_REFERENCE_LEVEL_PARAM)
    if ref_level_param and ref_level_param.HasValue:
        level_id = ref_level_param.AsElementId()
        level = doc.GetElement(level_id)
        if level:
            return level.Elevation
    return None

def classify_and_process_beams(beams, face):
    """Classify beams and process based on orientation"""
    
    threshold = 0.0328  # 10mm in feet
    
    parallel_beams = []
    perpendicular_beams = []
    skipped_beams = []
    
    results = {
        'parallel': 0,
        'perpendicular': 0,
        'skipped': 0,
        'errors': []
    }
    
    print("\n" + "="*50)
    print("CLASSIFYING BEAMS...")
    print("="*50)
    
    # Classification phase
    for beam in beams:
        try:
            curve = get_beam_curve(beam)
            if not curve:
                skipped_beams.append(beam)
                results['errors'].append("Beam ID {}: No location curve".format(beam.Id))
                continue
            
            start = curve.GetEndPoint(0)
            end = curve.GetEndPoint(1)
            
            # Project to slope
            start_elev = project_point_to_face(start, face)
            end_elev = project_point_to_face(end, face)
            
            if start_elev is None or end_elev is None:
                skipped_beams.append(beam)
                results['errors'].append("Beam ID {}: Projection failed".format(beam.Id))
                continue
            
            # Check elevation difference
            elev_diff = abs(start_elev - end_elev)
            
            if elev_diff < threshold:
                perpendicular_beams.append(beam)
            else:
                parallel_beams.append(beam)
                
        except Exception as e:
            skipped_beams.append(beam)
            results['errors'].append("Beam ID {}: {}".format(beam.Id, str(e)))
    
    print("Parallel to slope: {} beams".format(len(parallel_beams)))
    print("Perpendicular to slope: {} beams".format(len(perpendicular_beams)))
    print("Skipped: {} beams".format(len(skipped_beams)))
    
    print("\n" + "="*50)
    print("PROCESSING BEAMS...")
    print("="*50)
    
    # Processing phase
    t = Transaction(doc, "Adjust Beam Level Offsets")
    t.Start()
    
    try:
        # Process parallel beams
        for beam in parallel_beams:
            try:
                curve = get_beam_curve(beam)
                start = curve.GetEndPoint(0)
                end = curve.GetEndPoint(1)
                
                start_elev = project_point_to_face(start, face)
                end_elev = project_point_to_face(end, face)
                
                base_elev = get_base_level_elevation(beam)
                if base_elev is None:
                    results['errors'].append("Beam ID {}: No reference level".format(beam.Id))
                    continue
                
                start_offset = start_elev - base_elev
                end_offset = end_elev - base_elev
                
                # Set parameters
                start_param = beam.LookupParameter("Start Level Offset")
                end_param = beam.LookupParameter("End Level Offset")
                
                if start_param:
                    start_param.Set(start_offset)
                if end_param:
                    end_param.Set(end_offset)
                
                results['parallel'] += 1
                
            except Exception as e:
                results['errors'].append("Beam ID {}: {}".format(beam.Id, str(e)))
        
        # Process perpendicular beams
        for beam in perpendicular_beams:
            try:
                curve = get_beam_curve(beam)
                width = get_beam_width(beam)
                
                if width is None:
                    results['errors'].append("Beam ID {}: No width parameter 'b'".format(beam.Id))
                    continue
                
                corners = get_beam_corners(curve, width, beam)
                if not corners:
                    results['errors'].append("Beam ID {}: Failed to get corners".format(beam.Id))
                    continue
                
                # Project all corners
                corner_elevations = []
                for corner in corners:
                    elev = project_point_to_face(corner, face)
                    if elev is not None:
                        corner_elevations.append(elev)
                
                if not corner_elevations:
                    results['errors'].append("Beam ID {}: No valid corner projections".format(beam.Id))
                    continue
                
                min_elevation = min(corner_elevations)
                
                base_elev = get_base_level_elevation(beam)
                if base_elev is None:
                    results['errors'].append("Beam ID {}: No reference level".format(beam.Id))
                    continue
                
                offset = min_elevation - base_elev
                
                # Set both offsets to same value
                start_param = beam.LookupParameter("Start Level Offset")
                end_param = beam.LookupParameter("End Level Offset")
                
                if start_param:
                    start_param.Set(offset)
                if end_param:
                    end_param.Set(offset)
                
                results['perpendicular'] += 1
                
            except Exception as e:
                results['errors'].append("Beam ID {}: {}".format(beam.Id, str(e)))
        
        t.Commit()
        
    except Exception as e:
        t.RollBack()
        print("\nERROR: Transaction failed - {}".format(str(e)))
        return
    
    # Print results
    print("\n" + "="*50)
    print("RESULTS")
    print("="*50)
    print("Processed parallel: {} beams".format(results['parallel']))
    print("Processed perpendicular: {} beams".format(results['perpendicular']))
    print("Skipped: {} beams".format(results['skipped']))
    
    if results['errors']:
        print("\nWarnings/Errors:")
        for error in results['errors']:
            print("  - {}".format(error))

# Main execution
if __name__ == '__main__':
    try:
        # Select beams
        beam_refs = uidoc.Selection.PickObjects(
            ObjectType.Element,
            "Select beams"
        )
        
        if not beam_refs:
            print("No beams selected")
            import sys
            sys.exit()
        
        beams = [doc.GetElement(ref) for ref in beam_refs]
        
        # Select slope face
        print("\nSelect slope/ramp face...")
        face_ref = uidoc.Selection.PickObject(
            ObjectType.Face,
            "Select slope/ramp face"
        )
        
        element = doc.GetElement(face_ref)
        face = element.GetGeometryObjectFromReference(face_ref)
        
        if not isinstance(face, Face):
            print("ERROR: Selected object is not a face")
            import sys
            sys.exit()
        
        # Process beams
        classify_and_process_beams(beams, face)
        
    except Exception as e:
        print("\nERROR: {}".format(str(e)))
        import traceback
        traceback.print_exc()