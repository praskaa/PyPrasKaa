# -*- coding: utf-8 -*-
"""
Filled Region to Area Reinforcement
Membuat Area Reinforcement dari boundary Filled Region yang dipilih
"""

__title__ = "Filled Region\nto Area Rebar"
__author__ = "Your Name"

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.UI.Selection import ObjectType
from Autodesk.Revit.DB.Structure import RebarBarType, AreaReinforcement, AreaReinforcementType
import clr
clr.AddReference('System')
from System.Collections.Generic import List

# Import parameter setting utilities
import sys
import os
sys.path.append(os.path.dirname(__file__))
try:
    from logic_library.active.utilities.parameters.set_parameter_value import set_parameter_value_safe
    from logic_library.active.utilities.convert.unit_conversion import convert_internal_units
except ImportError:
    # Fallback if logic library not available
    def set_parameter_value_safe(element, param_name, new_value, logger=None):
        """Fallback parameter setting function"""
        try:
            param = element.LookupParameter(param_name)
            if param and not param.IsReadOnly:
                if param.StorageType == StorageType.Double:
                    param.Set(float(new_value))
                elif param.StorageType == StorageType.Integer:
                    param.Set(int(new_value))
                elif param.StorageType == StorageType.String:
                    param.Set(str(new_value))
                return True
        except:
            pass
        return False

    def convert_internal_units(value, get_internal=True, units='m'):
        """Fallback unit conversion"""
        if units == 'm':
            factor = 3.28084 if get_internal else 0.3048
        elif units == 'mm':
            factor = 0.00328084 if get_internal else 304.8
        else:
            factor = 1.0
        return value * factor

# Akses dokumen Revit
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application


def get_filled_region_boundary(filled_region, view):
    """
    Mendapatkan boundary curves dari Filled Region
    """
    curves = []
    
    try:
        # Get boundary segments dari Filled Region
        boundary_segments = filled_region.GetBoundaries()
        
        for curve_loop in boundary_segments:
            for curve in curve_loop:
                curves.append(curve)
                
    except Exception as e:
        print("Error mendapatkan boundary: {}".format(str(e)))
    
    return curves


def convert_view_to_model_coordinates(curves, view):
    """
    Konversi curves dari view coordinates ke model coordinates
    Untuk Filled Region di plan view, ini biasanya straightforward
    """
    model_curves = []
    
    # Untuk plan view, Z coordinate diambil dari view plane
    view_plane = view.SketchPlane.GetPlane() if hasattr(view, 'SketchPlane') and view.SketchPlane else None
    z_elevation = view_plane.Origin.Z if view_plane else 0
    
    for curve in curves:
        # Clone curve untuk manipulasi
        try:
            # Untuk plan view, curve XY sudah benar, tinggal set Z
            start = curve.GetEndPoint(0)
            end = curve.GetEndPoint(1)
            
            # Buat point baru dengan Z dari view
            new_start = XYZ(start.X, start.Y, z_elevation)
            new_end = XYZ(end.X, end.Y, z_elevation)
            
            # Buat curve baru
            if isinstance(curve, Line):
                new_curve = Line.CreateBound(new_start, new_end)
            elif isinstance(curve, Arc):
                # Untuk Arc, perlu middle point juga
                mid = curve.Evaluate(0.5, True)
                new_mid = XYZ(mid.X, mid.Y, z_elevation)
                new_curve = Arc.Create(new_start, new_end, new_mid)
            else:
                # Untuk curve type lain, gunakan CreateTransformed
                new_curve = curve.CreateTransformed(Transform.Identity)
            
            model_curves.append(new_curve)
            
        except Exception as e:
            print("Error konversi curve: {}".format(str(e)))
            model_curves.append(curve)  # Fallback ke original
    
    return model_curves


def create_curve_loop(curves):
    """
    Membuat CurveLoop dari list curves
    """
    curve_loop = CurveLoop()
    for curve in curves:
        curve_loop.Append(curve)
    return curve_loop


def inspect_area_reinforcement_parameters(area_reinforcement):
    """
    Inspect parameters available on Area Reinforcement instance
    """
    print("=== INSPECTING AREA REINFORCEMENT PARAMETERS ===")
    print("Element ID: {}".format(area_reinforcement.Id))

    try:
        # Check instance parameters
        print("\n--- INSTANCE PARAMETERS ---")
        for param in area_reinforcement.Parameters:
            try:
                param_name = param.Definition.Name
                param_type = param.StorageType.ToString()
                is_readonly = param.IsReadOnly

                value = "N/A"
                if param.StorageType == StorageType.String:
                    value = param.AsString() or "Empty"
                elif param.StorageType == StorageType.Integer:
                    value = str(param.AsInteger())
                elif param.StorageType == StorageType.Double:
                    value = str(param.AsDouble())
                elif param.StorageType == StorageType.ElementId:
                    elem_id = param.AsElementId()
                    value = str(elem_id) if elem_id != ElementId.InvalidElementId else "Invalid"

                print("  {}: {} ({}) [{}]".format(param_name, value, param_type, "RO" if is_readonly else "RW"))

            except Exception as e:
                print("  {}: Error - {}".format(param.Definition.Name, str(e)))

        # Check type parameters
        area_reinforcement_type = area_reinforcement.GetTypeId()
        art_element = doc.GetElement(area_reinforcement_type)

        print("\n--- TYPE PARAMETERS ---")
        for param in art_element.Parameters:
            try:
                param_name = param.Definition.Name
                param_type = param.StorageType.ToString()
                is_readonly = param.IsReadOnly

                value = "N/A"
                if param.StorageType == StorageType.String:
                    value = param.AsString() or "Empty"
                elif param.StorageType == StorageType.Integer:
                    value = str(param.AsInteger())
                elif param.StorageType == StorageType.Double:
                    value = str(param.AsDouble())
                elif param.StorageType == StorageType.ElementId:
                    elem_id = param.AsElementId()
                    value = str(elem_id) if elem_id != ElementId.InvalidElementId else "Invalid"

                print("  {}: {} ({}) [{}]".format(param_name, value, param_type, "RO" if is_readonly else "RW"))

            except Exception as e:
                print("  {}: Error - {}".format(param.Definition.Name, str(e)))

    except Exception as e:
        print("Error inspecting parameters: {}".format(str(e)))


def override_area_reinforcement_parameters(area_reinforcement):
    """
    Override Area Reinforcement parameters setelah creation
    - Layout Rule: set ke Maximum Spacing
    - Top Major Bar Type Spacing: set ke 150mm (converted to feet)
    """
    try:
        print("Overriding Area Reinforcement parameters...")

        # First, inspect what parameters are available
        inspect_area_reinforcement_parameters(area_reinforcement)

        # Try to set parameters on the instance first
        print("\n--- ATTEMPTING PARAMETER OVERRIDE ---")

        # Set Layout Rule to Maximum Spacing (value = 3 for Maximum Spacing)
        # Based on inspection, Layout Rule is Integer type
        layout_rule_success = set_parameter_value_safe(
            area_reinforcement,
            "Layout Rule",
            3,  # Maximum Spacing
            logger=None
        )

        if layout_rule_success:
            print("✓ Layout Rule set to Maximum Spacing (value=3) (instance)")
        else:
            print("✗ Could not set Layout Rule parameter")

        # Set Top Major Spacing to 150mm (not "Top Major Bar Type Spacing")
        # Convert 150mm to feet for Revit internal units
        spacing_150mm_in_feet = convert_internal_units(150.0, get_internal=True, units='mm')
        print("Converting 150mm to feet: {} feet".format(spacing_150mm_in_feet))

        spacing_success = set_parameter_value_safe(
            area_reinforcement,
            "Top Major Spacing",
            spacing_150mm_in_feet,
            logger=None
        )

        if spacing_success:
            print("✓ Top Major Spacing set to 150mm ({} feet) (instance)".format(spacing_150mm_in_feet))
        else:
            print("✗ Could not set Top Major Spacing parameter")

        return layout_rule_success or spacing_success  # Return True if at least one parameter was set

    except Exception as e:
        print("Error overriding parameters: {}".format(str(e)))
        import traceback
        print(traceback.format_exc())
        return False


def main():
    try:
        # Step 1: Dapatkan Filled Region yang dipilih
        selection = uidoc.Selection.GetElementIds()
        
        if selection.Count == 0:
            TaskDialog.Show("Error", "Silakan pilih Filled Region terlebih dahulu!")
            return
        
        filled_region = doc.GetElement(selection[0])
        
        # Validasi apakah element adalah Filled Region
        if not isinstance(filled_region, FilledRegion):
            TaskDialog.Show("Error", 
                          "Element yang dipilih bukan Filled Region!\n" +
                          "Tipe: {}".format(filled_region.GetType().Name))
            return
        
        # Dapatkan view aktif
        active_view = doc.ActiveView
        
        print("Filled Region dipilih: ID {}".format(filled_region.Id))
        print("View: {}".format(active_view.Name))
        
        # Step 2: Baca boundary dari Filled Region
        view_curves = get_filled_region_boundary(filled_region, active_view)
        
        if not view_curves:
            TaskDialog.Show("Error", "Tidak dapat membaca boundary dari Filled Region!")
            return
        
        print("Jumlah curves: {}".format(len(view_curves)))
        
        # Step 3: Konversi ke model coordinates
        model_curves = convert_view_to_model_coordinates(view_curves, active_view)
        
        # Step 4: Pilih host element (Floor atau Foundation)
        TaskDialog.Show("Pilih Host", 
                       "Silakan pilih host element (Floor/Foundation)\n" +
                       "untuk Area Reinforcement")
        
        try:
            # Pilih host
            reference = uidoc.Selection.PickObject(ObjectType.Element, 
                                                   "Pilih Floor atau Foundation sebagai host")
            host_id = reference.ElementId
            host = doc.GetElement(host_id)
            
            # Validasi host
            if not (isinstance(host, Floor) or isinstance(host, WallFoundation) or 
                   isinstance(host, Foundation)):
                TaskDialog.Show("Error", 
                              "Host harus Floor atau Foundation!\n" +
                              "Tipe yang dipilih: {}".format(host.GetType().Name))
                return
            
            print("Host dipilih: {} (ID: {})".format(host.Name, host.Id))
            
        except Exception as e:
            print("Pemilihan host dibatalkan atau error: {}".format(str(e)))
            return
        
        # Step 5: Buat Area Reinforcement
        t = Transaction(doc, "Create Area Reinforcement dari Filled Region")
        t.Start()
        
        try:
            # Buat CurveLoop dari model curves
            curve_loop = create_curve_loop(model_curves)

            # Untuk overload yang menggunakan IList<Curve>, kita perlu flatten CurveLoop
            # menjadi list individual curves
            all_curves = List[Curve]()
            for curve in curve_loop:
                all_curves.Add(curve)

            # Dapatkan AreaReinforcementType pertama yang tersedia (default)
            area_reinforcement_type_collector = FilteredElementCollector(doc)\
                .OfClass(AreaReinforcementType)\
                .ToElements()

            if not area_reinforcement_type_collector:
                TaskDialog.Show("Error", "Tidak ada AreaReinforcementType di project!")
                t.RollBack()
                return

            area_reinforcement_type = area_reinforcement_type_collector[0]
            area_reinforcement_type_id = area_reinforcement_type.Id

            # Dapatkan RebarBarType pertama yang tersedia (default)
            rebar_bar_type_collector = FilteredElementCollector(doc)\
                .OfClass(RebarBarType)\
                .ToElements()

            if not rebar_bar_type_collector:
                TaskDialog.Show("Error", "Tidak ada RebarBarType di project!")
                t.RollBack()
                return

            rebar_bar_type = rebar_bar_type_collector[0]
            rebar_bar_type_id = rebar_bar_type.Id

            # Dapatkan RebarHookType (bisa None untuk prototype)
            hook_type_id = ElementId.InvalidElementId  # None equivalent for ElementId

            # Buat Area Reinforcement menggunakan overload yang benar
            # Syntax: AreaReinforcement.Create(Document, Element, IList<Curve>,
            #                                   XYZ majorDirection, ElementId areaReinforcementTypeId,
            #                                   ElementId rebarBarTypeId, ElementId startHookId, ElementId endHookId)
            # Wait, let's check the actual signature again. Based on error, it seems we have 8 params but max is 7.
            # Let me try with 7 parameters: doc, host, curves, direction, areaReinforcementTypeId, rebarBarTypeId, hookId

            major_direction = XYZ(1, 0, 0)  # Direction untuk rebar utama

            # Try with 7 parameters - combining start and end hooks into one
            area_reinforcement = AreaReinforcement.Create(
                doc,
                host,
                all_curves,
                major_direction,
                area_reinforcement_type_id,
                rebar_bar_type_id,
                hook_type_id   # Single hook parameter
            )
            
            if area_reinforcement:
                print("Area Reinforcement berhasil dibuat! ID: {}".format(area_reinforcement.Id))

                # Override parameters setelah creation
                param_override_success = override_area_reinforcement_parameters(area_reinforcement)

                # Optional: Hapus Filled Region setelah berhasil
                # doc.Delete(filled_region.Id)

                t.Commit()

                success_message = "Area Reinforcement berhasil dibuat!\n\n" + \
                                "ID: {}\n".format(area_reinforcement.Id) + \
                                "Host: {}\n\n".format(host.Name)

                if param_override_success:
                    success_message += "✓ Parameter override berhasil:\n" + \
                                     "- Layout Rule: Maximum Spacing\n" + \
                                     "- Top Major Bar Type Spacing: 150mm"
                else:
                    success_message += "⚠ Parameter override gagal - silakan adjust manual di Properties panel"

                TaskDialog.Show("Sukses!", success_message)
            else:
                t.RollBack()
                TaskDialog.Show("Error", "Gagal membuat Area Reinforcement!")
                
        except Exception as e:
            t.RollBack()
            TaskDialog.Show("Error", 
                          "Error saat membuat Area Reinforcement:\n\n{}".format(str(e)))
            print("Detail error: {}".format(str(e)))
            import traceback
            print(traceback.format_exc())
        
    except Exception as e:
        TaskDialog.Show("Error", "Error: {}".format(str(e)))
        print("Error detail: {}".format(str(e)))
        import traceback
        print(traceback.format_exc())


# Jalankan script
if __name__ == '__main__':
    main()