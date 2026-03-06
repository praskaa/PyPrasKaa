# -*- coding: utf-8 -*-
__title__   = "Create Load Plan Legend"
__author__  = "PrasKaa"
__version__ = "Version: 1.0"
__doc__ = '''Version: 1.0
Date    = 06.03.2026
_____________________________________________________________________
Description:
Generate a legend for Load Plan Areas from the Color Fill Scheme.
Columns: LOAD DESCRIPTION | COLOR LEGEND | SDL | LL
_____________________________________________________________________
How-to:
1. Ensure "Load Plan by Area" Color Fill Scheme exists
2. Create at least one Legend View in the project
3. Run the script and select a Legend View to duplicate
4. Choose a Text Note Type for the legend
5. The legend will be created with color fills and load values

____________________________________
Last update:
- [06.03.2026] - 1.0 Initial release
_____________________________________________________________________
Author: PrasKaa'''

import os
from pyrevit import forms, script

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, BuiltInParameter, Category,
    ColorFillScheme, StorageType, UnitUtils, UnitTypeId,
    ViewType, FilledRegion, FillPatternElement,
    OverrideGraphicSettings, ElementId, Color,
    Transaction, TextNoteType,
    TextNote, TextNoteOptions, HorizontalTextAlignment, XYZ,
    FormattedText, TextRange
)

from Snippets._annotations  import create_region
from Snippets._overrides    import override_graphics_region
from Snippets._convert      import convert_cm_to_feet

import clr
clr.AddReference('RevitAPI')

uidoc = __revit__.ActiveUIDocument
doc   = __revit__.ActiveUIDocument.Document

TARGET_SCHEME_NAME = "Load Plan by Area"

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def create_text_centered(doc, view, x, y, text, text_type, bold=False):
    """Create a TextNote with center horizontal alignment."""
    text = '-' if not text else text
    opts = TextNoteOptions(text_type.Id)
    opts.HorizontalAlignment = HorizontalTextAlignment.Center
    tn = TextNote.Create(doc, view.Id, XYZ(x, y, 0), text, opts)
    # FormattedText does not support newline characters
    if bold and chr(10) not in text:
        ft = FormattedText(text)
        ft.SetBoldStatus(True)
        tn.SetFormattedText(ft)
    return tn

def get_area_scheme():
    all_schemes = FilteredElementCollector(doc)\
        .OfClass(ColorFillScheme).ToElements()
    area_cat_id = Category.GetCategory(doc, BuiltInCategory.OST_Areas).Id
    return next(
        (s for s in all_schemes
         if s.CategoryId == area_cat_id and s.Name == TARGET_SCHEME_NAME),
        None
    )

def get_param_knm2(area, param_name):
    param = area.LookupParameter(param_name)
    if not param or param.StorageType != StorageType.Double:
        return '-'
    val = param.AsDouble()
    if val == 0:
        return '0'
    converted = UnitUtils.ConvertFromInternalUnits(val, UnitTypeId.KilonewtonsPerSquareMeter)
    return str(round(converted, 4))

def get_solid_fill_pattern_id():
    all_patterns = FilteredElementCollector(doc)\
        .OfClass(FillPatternElement).ToElements()
    for p in all_patterns:
        if p.GetFillPattern().IsSolidFill:
            return p.Id
    return ElementId(-1)

def get_legend_views():
    all_views = FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_Views).ToElements()
    return [v for v in all_views
            if v.ViewType == ViewType.Legend and not v.IsTemplate]

def duplicate_legend(base_legend, name):
    from Autodesk.Revit.DB import ViewDuplicateOption
    new_id   = base_legend.Duplicate(ViewDuplicateOption.Duplicate)
    new_view = doc.GetElement(new_id)
    new_view.Scale = 1
    for i in range(50):
        try:
            new_view.Name = name
            break
        except:
            name += "*"
    return new_view

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    # 1. Get scheme
    scheme = get_area_scheme()
    if not scheme:
        forms.alert("Scheme '{}' not found.".format(TARGET_SCHEME_NAME), exitscript=True)

    entries = scheme.GetEntries()
    if not entries:
        forms.alert("No entries found in scheme.", exitscript=True)

    # 2. Color map: name -> (R, G, B)
    color_map = {}
    for entry in entries:
        name = entry.GetStringValue()
        if name:
            color_map[name] = (entry.Color.Red, entry.Color.Green, entry.Color.Blue)

    # 3. Area data map: name -> {sdl, ll}
    areas = FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_Areas)\
        .WhereElementIsNotElementType().ToElements()

    area_data = {}
    for area in areas:
        p = area.LookupParameter("Name")
        if p:
            n = p.AsString()
            if n:
                area_data[n] = {
                    'sdl': get_param_knm2(area, 'SDL'),
                    'll' : get_param_knm2(area, 'LL')
                }

    # 4. Pick legend view
    legend_views = get_legend_views()
    if not legend_views:
        forms.alert("No Legend View found. Please create one first.", exitscript=True)

    legend_names = {v.Name: v for v in legend_views}
    selected_name = forms.SelectFromList.show(
        sorted(legend_names.keys()),
        title='Select Legend View to Duplicate From',
        multiselect=False
    )
    if not selected_name:
        return
    base_legend = legend_names[selected_name]

    # 5. Pick text type
    text_types = FilteredElementCollector(doc)\
        .OfClass(TextNoteType).WhereElementIsElementType().ToElements()
    text_type_map = {
        t.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString(): t
        for t in text_types
    }
    selected_tt = forms.SelectFromList.show(
        sorted(text_type_map.keys()),
        title='Select Text Note Type',
        multiselect=False
    )
    if not selected_tt:
        return
    text_type = text_type_map[selected_tt]

    # 6. Solid fill pattern
    solid_fill_id = get_solid_fill_pattern_id()

    # ─────────────────────────────────────────────
    # 7. LAYOUT — all in feet, tuned for 1:1, 3.5mm text
    # ─────────────────────────────────────────────
    # Column widths
    w_name   = convert_cm_to_feet(4.5)   # LOAD DESCRIPTION column width
    w_region = convert_cm_to_feet(2.5 + 0.42 + 0.42)   # COLOR LEGEND column width (+4.2mm each side)
    w_sdl    = convert_cm_to_feet(2.5)   # SDL column width
    w_ll     = convert_cm_to_feet(2.5)   # LL column width

    # Column left-edge X positions
    col_name   = 0.0
    col_region = col_name   + w_name
    col_sdl    = col_region + w_region
    col_ll     = col_sdl    + w_sdl

    # Column center X positions (for centered text)
    cx_name   = col_name   + w_name   / 2.0
    cx_region = col_region + w_region / 2.0
    cx_sdl    = col_sdl    + w_sdl    / 2.0
    cx_ll     = col_ll     + w_ll     / 2.0

    # Row dimensions
    row_height    = convert_cm_to_feet(0.8)    # height of each row
    region_height = convert_cm_to_feet(0.45)   # filled region height inside row
    region_width  = convert_cm_to_feet(2.0)    # filled region width

    # Region X offset to center inside column
    region_x = col_region + (w_region - region_width) / 2.0

    # ─────────────────────────────────────────────
    # GRID HELPER
    # ─────────────────────────────────────────────
    from Autodesk.Revit.DB import Line, XYZ as _XYZ

    def draw_line(view, x1, y1, x2, y2):
        """Draw a detail line in the legend view."""
        p1 = _XYZ(x1, y1, 0)
        p2 = _XYZ(x2, y2, 0)
        doc.Create.NewDetailCurve(view, Line.CreateBound(p1, p2))

    # ─────────────────────────────────────────────
    # 8. CREATE LEGEND
    # ─────────────────────────────────────────────
    header_height = row_height * 1.8  # header row is taller
    n_rows        = len(color_map)
    total_width   = col_ll + w_ll
    total_height  = header_height + n_rows * row_height

    # All column X boundaries
    col_boundaries = [col_name, col_region, col_sdl, col_ll, col_ll + w_ll]

    t = Transaction(doc, "Create Load Plan Legend")
    t.Start()

    try:
        new_legend = duplicate_legend(base_legend, "Legend_LoadPlan")

        Y_top = 0.0  # top of header

        # ── TEXT: Header row ──
        text_offset   = convert_cm_to_feet(0.31)   # shift all text up 3.1mm
        Y_header_text = Y_top - row_height * 0.9 + text_offset  # vertically center in header
        create_text_centered(doc, new_legend, cx_name,   Y_header_text, "LOAD DESCRIPTION", text_type, bold=True)
        create_text_centered(doc, new_legend, cx_region, Y_header_text, "COLOR LEGEND", text_type, bold=True)

        # SDL header with superscript "2"
        opts_sdl = TextNoteOptions(text_type.Id)
        opts_sdl.HorizontalAlignment = HorizontalTextAlignment.Center
        tn_sdl = TextNote.Create(doc, new_legend.Id, XYZ(cx_sdl, Y_header_text, 0),
                                 "SDL (kN/m2)", opts_sdl)
        ft_sdl = tn_sdl.GetFormattedText()
        ft_sdl.SetBoldStatus(True)
        # superscript the last char "2"
        sdl_text = "SDL (kN/m2)"
        sup_range = TextRange(9, 1)  # index of "2" in "SDL (kN/m2)"
        ft_sdl.SetSuperscriptStatus(sup_range, True)
        tn_sdl.SetFormattedText(ft_sdl)

        # LL header with superscript "2"
        opts_ll = TextNoteOptions(text_type.Id)
        opts_ll.HorizontalAlignment = HorizontalTextAlignment.Center
        tn_ll = TextNote.Create(doc, new_legend.Id, XYZ(cx_ll, Y_header_text, 0),
                                "LL (kN/m2)", opts_ll)
        ft_ll = tn_ll.GetFormattedText()
        ft_ll.SetBoldStatus(True)
        ll_text = "LL (kN/m2)"
        sup_range2 = TextRange(8, 1)  # index of "2" in "LL (kN/m2)"
        ft_ll.SetSuperscriptStatus(sup_range2, True)
        tn_ll.SetFormattedText(ft_ll)

        Y = Y_top - header_height  # Y of first data row top

        # ── TEXT + REGION: Data rows — sorted by LL asc, then SDL asc ──
        def sort_key(name):
            d = area_data.get(name, {"sdl": "-", "ll": "-"})
            try:    ll_val  = float(d["ll"])
            except: ll_val  = float("inf")
            try:    sdl_val = float(d["sdl"])
            except: sdl_val = float("inf")
            return (sdl_val, ll_val)

        for area_name in sorted(color_map.keys(), key=sort_key):
            r, g, b = color_map[area_name]
            data    = area_data.get(area_name, {'sdl': '-', 'll': '-'})

            Y_text = Y - row_height * 0.55 + text_offset  # vertically center text in row

            create_text_centered(doc, new_legend, cx_name, Y_text, area_name, text_type)

            # Filled region fills the full cell with small padding
            padding    = convert_cm_to_feet(0.08)
            region = create_region(
                doc, new_legend,
                col_region + padding,
                Y - padding,
                w_region - padding * 2,
                row_height - padding * 2
            )

            revit_color = Color(r, g, b)
            override_graphics_region(
                doc, new_legend, region,
                fg_pattern_id = solid_fill_id,
                fg_color      = revit_color,
                bg_pattern_id = solid_fill_id,
                bg_color      = revit_color
            )

            create_text_centered(doc, new_legend, cx_sdl, Y_text, data['sdl'], text_type)
            create_text_centered(doc, new_legend, cx_ll,  Y_text, data['ll'],  text_type)

            Y -= row_height

        Y_bottom = Y  # bottom edge of table

        # ── GRID LINES ──
        # Horizontal lines: top of header + after header + after each data row
        h_lines = [Y_top]
        h_lines.append(Y_top - header_height)
        row_y = Y_top - header_height
        for _ in range(n_rows):
            row_y -= row_height
            h_lines.append(row_y)

        for hy in h_lines:
            draw_line(new_legend, col_name, hy, total_width, hy)

        # Vertical lines: one per column boundary
        for cx in col_boundaries:
            draw_line(new_legend, cx, Y_top, cx, Y_bottom)

        t.Commit()
        print("Legend created: {}".format(new_legend.Name))
        print("{} rows written.".format(len(color_map)))
        uidoc.ActiveView = new_legend

    except Exception as ex:
        t.RollBack()
        import traceback
        print("ERROR: {}".format(str(ex)))
        print(traceback.format_exc())


if __name__ == '__main__':
    main()