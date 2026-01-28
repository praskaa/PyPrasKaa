# -*- coding: utf-8 -*-
from pyrevit import forms, revit, script
from Autodesk.Revit.DB import *
import math

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

# 1. Minta user input sudut rotasi
angle_deg = forms.ask_for_string(
    default="90",
    prompt="Masukkan sudut rotasi (derajat):",
    title="Bulk Rotate Elements"
)

if angle_deg:
    try:
        angle_rad = float(angle_deg) * (math.pi / 180.0) # Konversi ke Radian
        
        # 2. Pilih elemen (bisa pilih dulu baru klik tombol, atau sebaliknya)
        selection = revit.get_selection()
        
        if not selection:
            forms.alert("Pilih elemen terlebih dahulu!", exitscript=True)

        with revit.Transaction("Rotate Elements Individually"):
            count = 0
            for el in selection:
                # Mendapatkan titik pusat elemen (LocationPoint)
                loc = el.Location
                
                if isinstance(loc, LocationPoint):
                    center_pt = loc.Point
                    
                    # Membuat sumbu rotasi (garis vertikal/Z-axis yang melewati center)
                    # Titik 1: Center, Titik 2: Center ke atas sedikit
                    pt2 = XYZ(center_pt.X, center_pt.Y, center_pt.Z + 10)
                    rotation_axis = Line.CreateBound(center_pt, pt2)
                    
                    # Eksekusi Rotasi
                    ElementTransformUtils.RotateElement(doc, el.Id, rotation_axis, angle_rad)
                    count += 1
                
                elif isinstance(loc, LocationCurve):
                    # Jika elemen berbasis garis (seperti wall/beam), ambil titik tengah garisnya
                    center_pt = loc.Curve.Evaluate(0.5, True)
                    pt2 = XYZ(center_pt.X, center_pt.Y, center_pt.Z + 10)
                    rotation_axis = Line.CreateBound(center_pt, pt2)
                    
                    ElementTransformUtils.RotateElement(doc, el.Id, rotation_axis, angle_rad)
                    count += 1

            forms.alert("Berhasil memutar {} elemen sebesar {} derajat.".format(count, angle_deg))

    except ValueError:
        forms.alert("Input harus berupa angka!")
    except Exception as e:
        forms.alert("Error: {}".format(str(e)))