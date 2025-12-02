# -*- coding: utf-8 -*-
"""
Automation: Column Reinforcement
Description: Membuat tulangan sengkang dan longitudinal otomatis pada kolom terpilih.
Author: Your Name
"""

import math
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.DB.Structure import *
from Autodesk.Revit.UI.Selection import ObjectType
from pyrevit import revit, forms, script

# --- INISIALISASI ---
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application

# Logger untuk output
output = script.get_output()

def mm_to_feet(mm):
    """Helper: Konversi mm ke Internal Revit Unit (feet)"""
    return mm / 304.8

def get_geometry_params(col_element):
    """
    Helper: Mendapatkan dimensi b (width), h (depth), dan Length dari kolom.
    """
    elem_type = doc.GetElement(col_element.GetTypeId())
    
    # Coba berbagai kemungkinan nama parameter untuk b (width)
    p_b = (col_element.LookupParameter("b") or 
           elem_type.LookupParameter("b") or 
           col_element.LookupParameter("Width") or 
           elem_type.LookupParameter("Width"))
    
    # Coba berbagai kemungkinan nama parameter untuk h (depth)
    p_h = (col_element.LookupParameter("h") or 
           elem_type.LookupParameter("h") or 
           col_element.LookupParameter("Depth") or 
           elem_type.LookupParameter("Depth"))
    
    # Parameter Length untuk tinggi kolom
    p_length = (col_element.LookupParameter("Length") or 
                elem_type.LookupParameter("Length") or
                col_element.LookupParameter("Height") or
                elem_type.LookupParameter("Height"))
    
    if p_b and p_h and p_length:
        return p_b.AsDouble(), p_h.AsDouble(), p_length.AsDouble()
    
    return None, None, None

def get_standard_hook_type(doc):
    """Helper: Mendapatkan RebarHookType standard (90 derajat)"""
    collector = FilteredElementCollector(doc).OfClass(RebarHookType)
    for hook in collector:
        if hook.HookAngle == 90:
            return hook
    # Jika tidak ada hook 90 derajat, ambil yang pertama
    return collector.FirstElement()

def get_stirrup_hook_type(doc):
    """Helper: Mendapatkan RebarHookType untuk stirrup (180 derajat)"""
    collector = FilteredElementCollector(doc).OfClass(RebarHookType)
    for hook in collector:
        if hook.HookAngle == 180:
            return hook
    # Jika tidak ada hook 180 derajat, gunakan 90 derajat sebagai fallback
    return get_standard_hook_type(doc)

def get_rebar_shape_by_name(doc, shape_name):
    """Get RebarShape by name using proper parameter access"""
    collector = FilteredElementCollector(doc).OfClass(RebarShape)
    for shape in collector:
        try:
            # Try SYMBOL_NAME_PARAM first (for ElementType)
            type_name_param = shape.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
            if type_name_param and type_name_param.AsString() == shape_name:
                return shape
            # Fallback to Name property
            elif getattr(shape, 'Name', None) == shape_name:
                return shape
        except:
            continue
    return None

def create_stirrup_rebar(column, cover_type, stirrup_type, max_spacing, b_ft, h_ft, length_ft, doc):
    """
    Membuat sengkang (stirrup) pada kolom menggunakan pendekatan sederhana.
    """
    try:
        # Untuk stirrup, gunakan approach yang sangat sederhana tanpa hooks
        # Stirrup shape sudah define bent ends nya sendiri

        # Dapatkan cover distance
        cover_dist = cover_type.CoverDistance

        # Dapatkan lokasi kolom
        location = column.Location
        if not isinstance(location, LocationPoint):
            return None

        origin = location.Point

        # Hitung dimensi dalam sengkang (dikurangi cover)
        half_b = (b_ft / 2.0) - cover_dist
        half_h = (h_ft / 2.0) - cover_dist

        # Buat kurva persegi sederhana
        p1 = origin + XYZ(-half_b, -half_h, 0)
        p2 = origin + XYZ(half_b, -half_h, 0)
        p3 = origin + XYZ(half_b, half_h, 0)
        p4 = origin + XYZ(-half_b, half_h, 0)

        curves = List[Curve]()
        curves.Add(Line.CreateBound(p1, p2))
        curves.Add(Line.CreateBound(p2, p3))
        curves.Add(Line.CreateBound(p3, p4))
        curves.Add(Line.CreateBound(p4, p1))

        # Normal vector
        normal = XYZ(0, 0, 1)

        output.print_md("   Creating stirrup without hooks (shape defines ends)...")

        # Buat rebar
        rebar = Rebar.CreateFromCurves(
            doc,
            RebarStyle.StirrupTie,
            stirrup_type,
            None,  # No start hook
            None,  # No end hook
            column,
            normal,
            curves,
            RebarHookOrientation.Left,
            RebarHookOrientation.Left,
            True,  # useExistingShapeIfPossible
            True   # createNewShapeIfNeeded
        )

        # Validasi hasil
        if not rebar:
            output.print_md("   ❌ CreateFromCurves returned None")
            return None

        if not rebar.IsValidObject:
            output.print_md("   ❌ Rebar object is not valid")
            return None

        output.print_md("   ✅ Stirrup created, setting layout...")

        # PENTING: Regenerate document sebelum set layout
        doc.Regenerate()

        # Set layout menggunakan GetShapeDrivenAccessor
        try:
            shape_accessor = rebar.GetShapeDrivenAccessor()

            if shape_accessor:
                # Set Maximum Spacing layout
                shape_accessor.SetLayoutAsMaximumSpacing(
                    max_spacing,  # Maximum spacing between stirrups
                    length_ft,    # Total array length (column height)
                    True,         # useBarConstraintIfPossible
                    True,         # moveEndToStartIfUnstartable
                    True          # adjustEndBarLocation
                )

                output.print_md("   ✅ Layout set: Maximum Spacing = {:.0f}mm".format(max_spacing * 304.8))

                # Regenerate setelah setting layout
                doc.Regenerate()

            else:
                output.print_md("   ⚠️ GetShapeDrivenAccessor returned None")
                return None

        except Exception as e:
            output.print_md("   ❌ Error setting layout: {}".format(str(e)))
            return None

    except Exception as e:
        output.print_md("⚠️ **Error creating stirrup**: {}".format(str(e)))
        return None

def create_longitudinal_rebars(column, cover_type, long_type, bars_per_side, b_ft, h_ft, length_ft, doc):
    """
    Membuat tulangan longitudinal pada kolom.
    
    Args:
        column: Elemen kolom
        cover_type: RebarCoverType
        long_type: RebarBarType untuk tulangan longitudinal
        bars_per_side: Jumlah tulangan per sisi
        b_ft: Lebar kolom (feet)
        h_ft: Kedalaman kolom (feet)
        length_ft: Tinggi kolom (feet)
        doc: Document
    
    Returns:
        List of Rebar objects
    """
    rebars = []
    
    try:
        # Dapatkan RebarShape untuk longitudinal (M_00 - straight bar)
        long_shape = get_rebar_shape_by_name(doc, "M_00")
        if long_shape:
            output.print_md("✅ Found longitudinal shape: M_00")
        else:
            output.print_md("⚠️ **Warning**: RebarShape 'M_00' not found, using default")
            long_shape = None

        # Dapatkan cover distance dan diameter bar
        cover_dist = cover_type.CoverDistance
        bar_diameter = long_type.BarNominalDiameter

        # Dapatkan lokasi kolom
        location = column.Location
        if not isinstance(location, LocationPoint):
            return rebars

        origin = location.Point

        # Offset = cover + setengah diameter bar
        offset = cover_dist + (bar_diameter / 2.0)
        half_b = (b_ft / 2.0) - offset
        half_h = (h_ft / 2.0) - offset
        
        # === SISI 1: Atas (sepanjang b) - FULL bars ===
        for i in range(bars_per_side):
            if bars_per_side > 1:
                spacing_b = (2.0 * half_b) / (bars_per_side - 1)
                x_pos = -half_b + (i * spacing_b)
            else:
                x_pos = 0
            
            # Titik awal dan akhir tulangan vertikal
            start_point = origin + XYZ(x_pos, half_h, 0)
            end_point = origin + XYZ(x_pos, half_h, length_ft)
            
            # Buat kurva garis vertikal
            curve = Line.CreateBound(start_point, end_point)
            curves = List[Curve]()
            curves.Add(curve)
            
            # Normal vector untuk tulangan longitudinal
            normal = XYZ(0, 1, 0)
            
            try:
                rebar = Rebar.CreateFromCurves(
                    doc,
                    RebarStyle.Standard,
                    long_type,
                    None,
                    None,
                    column,
                    normal,
                    curves,
                    RebarHookOrientation.Left,
                    RebarHookOrientation.Left,
                    True,
                    True
                )
                if rebar:
                    rebars.append(rebar)
            except:
                pass
        
        # === SISI 2: Bawah (sepanjang b) - FULL bars ===
        for i in range(bars_per_side):
            if bars_per_side > 1:
                spacing_b = (2.0 * half_b) / (bars_per_side - 1)
                x_pos = -half_b + (i * spacing_b)
            else:
                x_pos = 0
            
            start_point = origin + XYZ(x_pos, -half_h, 0)
            end_point = origin + XYZ(x_pos, -half_h, length_ft)
            
            curve = Line.CreateBound(start_point, end_point)
            curves = List[Curve]()
            curves.Add(curve)
            
            normal = XYZ(0, 1, 0)
            
            try:
                if long_shape:
                    rebar = Rebar.CreateFromCurvesAndShape(
                        doc,
                        long_shape,
                        long_type,
                        None,
                        None,
                        column,
                        normal,
                        curves,
                        RebarHookOrientation.Left,
                        RebarHookOrientation.Left
                    )
                else:
                    # Fallback tanpa shape
                    rebar = Rebar.CreateFromCurves(
                        doc,
                        RebarStyle.Standard,
                        long_type,
                        None,
                        None,
                        column,
                        normal,
                        curves,
                        RebarHookOrientation.Left,
                        RebarHookOrientation.Left,
                        True,
                        True
                    )
                if rebar:
                    rebars.append(rebar)
            except:
                pass
        
        # === SISI 3 & 4: Kiri & Kanan (sepanjang h) - MINUS corner bars ===
        # Loop hanya untuk bars di tengah (i = 1 sampai bars_per_side-2)
        for i in range(1, bars_per_side - 1):
            if bars_per_side > 1:
                spacing_h = (2.0 * half_h) / (bars_per_side - 1)
                y_pos = -half_h + (i * spacing_h)
            else:
                continue
            
            # SISI KIRI
            start_point = origin + XYZ(-half_b, y_pos, 0)
            end_point = origin + XYZ(-half_b, y_pos, length_ft)
            
            curve = Line.CreateBound(start_point, end_point)
            curves = List[Curve]()
            curves.Add(curve)
            
            normal = XYZ(1, 0, 0)
            
            try:
                if long_shape:
                    rebar = Rebar.CreateFromCurvesAndShape(
                        doc,
                        long_shape,
                        long_type,
                        None,
                        None,
                        column,
                        normal,
                        curves,
                        RebarHookOrientation.Left,
                        RebarHookOrientation.Left
                    )
                else:
                    # Fallback tanpa shape
                    rebar = Rebar.CreateFromCurves(
                        doc,
                        RebarStyle.Standard,
                        long_type,
                        None,
                        None,
                        column,
                        normal,
                        curves,
                        RebarHookOrientation.Left,
                        RebarHookOrientation.Left,
                        True,
                        True
                    )
                if rebar:
                    rebars.append(rebar)
            except:
                pass
            
            # SISI KANAN
            start_point = origin + XYZ(half_b, y_pos, 0)
            end_point = origin + XYZ(half_b, y_pos, length_ft)
            
            curve = Line.CreateBound(start_point, end_point)
            curves = List[Curve]()
            curves.Add(curve)
            
            normal = XYZ(1, 0, 0)
            
            try:
                if long_shape:
                    rebar = Rebar.CreateFromCurvesAndShape(
                        doc,
                        long_shape,
                        long_type,
                        None,
                        None,
                        column,
                        normal,
                        curves,
                        RebarHookOrientation.Left,
                        RebarHookOrientation.Left
                    )
                else:
                    # Fallback tanpa shape
                    rebar = Rebar.CreateFromCurves(
                        doc,
                        RebarStyle.Standard,
                        long_type,
                        None,
                        None,
                        column,
                        normal,
                        curves,
                        RebarHookOrientation.Left,
                        RebarHookOrientation.Left,
                        True,
                        True
                    )
                if rebar:
                    rebars.append(rebar)
            except:
                pass
        
        return rebars
        
    except Exception as e:
        output.print_md("⚠️ **Error creating longitudinal**: {}".format(str(e)))
        return rebars

# ==============================================================================
# FASE 1: COLLECTING RESOURCES
# ==============================================================================
output.print_md("# 🔍 FASE 1: Collecting Resources")

all_bar_types = FilteredElementCollector(doc).OfClass(RebarBarType).ToElements()
all_cover_types = FilteredElementCollector(doc).OfClass(RebarCoverType).ToElements()

if not all_bar_types:
    forms.alert("Project tidak memiliki RebarBarType!")
    raise SystemExit()
if not all_cover_types:
    forms.alert("Project tidak memiliki RebarCoverType!")
    raise SystemExit()

output.print_md("✅ Ditemukan **{}** RebarBarType".format(len(all_bar_types)))
output.print_md("✅ Ditemukan **{}** RebarCoverType".format(len(all_cover_types)))

# ==============================================================================
# FASE 2: USER INPUT TERPUSAT
# ==============================================================================
output.print_md("\n# 📝 FASE 2: User Input")

# Helper function to get proper name for RebarBarType
def get_rebar_bar_type_name(rbt):
    """Get name for RebarBarType using proper parameter access"""
    try:
        # Try SYMBOL_NAME_PARAM first (for ElementType)
        type_name_param = rbt.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
        if type_name_param and type_name_param.AsString():
            return type_name_param.AsString()
        else:
            # Fallback to Name property
            return getattr(rbt, 'Name', 'Unnamed Bar Type')
    except:
        return 'Unnamed Bar Type'

# Helper function to get proper name for RebarCoverType
def get_rebar_cover_type_name(cover_type):
    """Get name for RebarCoverType using proper access"""
    try:
        # For Element, try Name property
        return getattr(cover_type, 'Name', 'Unnamed Cover Type')
    except:
        return 'Unnamed Cover Type'

# Buat list objek valid dengan nama proper
cover_list = []
cover_names = []
for c in all_cover_types:
    if c and c.IsValidObject and isinstance(c, RebarCoverType):
        name = get_rebar_cover_type_name(c)
        cover_list.append(c)
        cover_names.append(name)

bar_list = []
bar_names = []
for b in all_bar_types:
    if b and b.IsValidObject and isinstance(b, RebarBarType):
        name = get_rebar_bar_type_name(b)
        bar_list.append(b)
        bar_names.append(name)

cover_dict = dict(zip(cover_names, cover_list))
bar_dict = dict(zip(bar_names, bar_list))

output.print_md("✅ Valid cover types: {}".format(len(cover_list)))
output.print_md("✅ Valid bar types: {}".format(len(bar_list)))

# Input 1: Pilih Cover Type
selected_cover_name = forms.SelectFromList.show(
    sorted(cover_dict.keys()),
    title="1. Pilih Rebar Cover Type",
    button_name="Pilih"
)

if not selected_cover_name:
    # User cancelled
    output.print_md("❌ User cancelled selection")
    raise SystemExit()

selected_cover = cover_dict[selected_cover_name]

# Input 2: Pilih Bar Type untuk Sengkang
selected_stirrup_name = forms.SelectFromList.show(
    sorted(bar_dict.keys()),
    title="2. Pilih Rebar Bar Type untuk Sengkang",
    button_name="Pilih"
)

if not selected_stirrup_name:
    # User cancelled
    output.print_md("❌ User cancelled selection")
    raise SystemExit()

stirrup_type = bar_dict[selected_stirrup_name]

# Input 3: Pilih Bar Type untuk Longitudinal
selected_long_name = forms.SelectFromList.show(
    sorted(bar_dict.keys()),
    title="3. Pilih Rebar Bar Type untuk Tulangan Longitudinal",
    button_name="Pilih"
)

if not selected_long_name:
    # User cancelled
    output.print_md("❌ User cancelled selection")
    raise SystemExit()

long_type = bar_dict[selected_long_name]

# Input 4: Jarak maksimum sengkang
spacing_input = forms.ask_for_string(
    prompt="4. Masukkan jarak maksimum sengkang (mm):",
    title="Maximum Distance Sengkang",
    default="150"
)

if not spacing_input:
    # User cancelled
    output.print_md("❌ User cancelled input")
    raise SystemExit()

# Input 5: Jumlah tulangan per sisi
bars_input = forms.ask_for_string(
    prompt="5. Masukkan jumlah tulangan longitudinal per sisi:",
    title="Jumlah Tulangan per Sisi",
    default="3"
)

if not bars_input:
    # User cancelled
    output.print_md("❌ User cancelled input")
    raise SystemExit()

# Konversi input
try:
    spacing_ft = mm_to_feet(float(spacing_input))
    n_bars = int(bars_input)
except:
    forms.alert("Input tidak valid!")
    raise SystemExit()

output.print_md("✅ Cover Type: **{}**".format(selected_cover_name))
output.print_md("✅ Stirrup Type: **{}**".format(selected_stirrup_name))
output.print_md("✅ Longitudinal Type: **{}**".format(selected_long_name))
output.print_md("✅ Max Spacing: **{} mm**".format(spacing_input))
output.print_md("✅ Bars per Side: **{}**".format(n_bars))

# ==============================================================================
# FASE 3: SELEKSI KOLOM
# ==============================================================================
output.print_md("\n# 🎯 FASE 3: Seleksi Kolom")

try:
    selected_refs = uidoc.Selection.PickObjects(
        ObjectType.Element,
        "Pilih Kolom Struktural"
    )
    selected_cols = [doc.GetElement(r) for r in selected_refs]
except:
    output.print_md("❌ User cancelled selection")
    raise SystemExit()

if not selected_cols:
    forms.alert("Tidak ada kolom dipilih.")
    raise SystemExit()

output.print_md("✅ Dipilih **{}** kolom".format(len(selected_cols)))

# ==============================================================================
# FASE 4: TRANSACTION & PROCESSING
# ==============================================================================
output.print_md("\n# ⚙️ FASE 4: Processing")

t = Transaction(doc, "Create Column Rebar")
t.Start()

success_count = 0
fail_count = 0

try:
    for col in selected_cols:
        col_id = col.Id.IntegerValue
        
        # VALIDASI 1: Cek Category
        if col.Category.Id.IntegerValue != int(BuiltInCategory.OST_StructuralColumns):
            output.print_md("⚠️ **Skip ID {}**: Bukan structural column".format(col_id))
            fail_count += 1
            continue
        
        # VALIDASI 2: Ambil Geometri
        b_ft, h_ft, length_ft = get_geometry_params(col)
        if not b_ft or not h_ft or not length_ft:
            output.print_md("⚠️ **Skip ID {}**: Parameter b, h, atau Length tidak ditemukan".format(col_id))
            fail_count += 1
            continue
        
        # Info dimensi
        output.print_md("🔧 Processing ID {}: b={:.0f}mm, h={:.0f}mm, L={:.0f}mm".format(
            col_id, 
            b_ft * 304.8, 
            h_ft * 304.8, 
            length_ft * 304.8
        ))
        
        # Buat Sengkang
        stirrup = create_stirrup_rebar(
            col, selected_cover, stirrup_type, spacing_ft, 
            b_ft, h_ft, length_ft, doc
        )
        
        # Buat Tulangan Longitudinal
        long_rebars = create_longitudinal_rebars(
            col, selected_cover, long_type, n_bars,
            b_ft, h_ft, length_ft, doc
        )
        
        # Hitung hasil
        if stirrup or long_rebars:
            success_count += 1
            output.print_md("   ✅ Sukses: {} stirrup, {} longitudinal bars".format(
                1 if stirrup else 0,
                len(long_rebars)
            ))
        else:
            fail_count += 1
            output.print_md("   ❌ Gagal membuat rebar")

except Exception as e:
    # Error handling
    t.RollBack()
    output.print_md("\n# ❌ CRITICAL ERROR")
    output.print_md("```\n{}\n```".format(str(e)))
    forms.alert("CRITICAL ERROR:\n{}".format(str(e)))
    raise SystemExit()

# ==============================================================================
# FASE 5: FINALISASI (COMMIT / ROLLBACK)
# ==============================================================================
output.print_md("\n# 📊 FASE 5: Finalisasi")

if success_count > 0:
    t.Commit()
    output.print_md("## ✅ SUKSES")
    output.print_md("Berhasil memproses: **{}** kolom".format(success_count))
    if fail_count > 0:
        output.print_md("Gagal/Skip: **{}** kolom".format(fail_count))
    forms.alert("Selesai! {} Kolom berhasil diberi tulangan.".format(success_count))
else:
    t.RollBack()
    output.print_md("## ⚠️ PERINGATAN")
    output.print_md("Tidak ada kolom yang berhasil diproses.")
    output.print_md("Total skip/gagal: **{}** kolom".format(fail_count))
    forms.alert("⚠️ PERINGATAN: Tidak ada kolom yang berhasil diproses.\nTransaksi dibatalkan.", title="Warning")