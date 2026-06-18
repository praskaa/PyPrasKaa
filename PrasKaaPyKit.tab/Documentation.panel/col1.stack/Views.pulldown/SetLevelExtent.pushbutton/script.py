# -*- coding: utf-8 -*-
# Author: PrasKaa
# Description: Diagnostic 3 — exact datum curve XYZ and Grid method names
# Version: 1.0

from pyrevit import revit, DB, forms, script

doc   = revit.doc
uidoc = revit.uidoc

out = script.get_output()
out.print_html("<h3>Datum Diagnostic 3 — Exact Coords + Grid Methods</h3>")

active_view = uidoc.ActiveView
out.print_html("<p>View: <b>{}</b></p>".format(active_view.Name))

# --- Visible levels ---
levels = list(
    DB.FilteredElementCollector(doc, active_view.Id)
      .OfClass(DB.Level)
      .WhereElementIsNotElementType()
      .ToElements()
)
out.print_html("<h4>Level curves — full XYZ (ViewSpecific):</h4>")
for lv in levels:
    try:
        curves = list(lv.GetCurvesInView(DB.DatumExtentType.ViewSpecific, active_view))
        if curves:
            c = curves[0]
            p0 = c.GetEndPoint(0)
            p1 = c.GetEndPoint(1)
            out.print_html(
                "<p><b>{}</b>: ({:.6f}, {:.6f}, {:.6f}) &rarr; ({:.6f}, {:.6f}, {:.6f})</p>".format(
                    lv.Name, p0.X, p0.Y, p0.Z, p1.X, p1.Y, p1.Z
                )
            )
        else:
            out.print_html("<p><b>{}</b>: no curves</p>".format(lv.Name))
    except Exception as e:
        out.print_html("<p style='color:red'><b>{}</b>: {}</p>".format(lv.Name, str(e)))

# --- CropBox transform ---
out.print_html("<h4>CropBox details:</h4>")
cb = active_view.CropBox
out.print_html("<p>Min: ({:.6f}, {:.6f}, {:.6f})</p>".format(cb.Min.X, cb.Min.Y, cb.Min.Z))
out.print_html("<p>Max: ({:.6f}, {:.6f}, {:.6f})</p>".format(cb.Max.X, cb.Max.Y, cb.Max.Z))
t = cb.Transform
out.print_html("<p>Transform.Origin: ({:.3f}, {:.3f}, {:.3f})</p>".format(
    t.Origin.X, t.Origin.Y, t.Origin.Z))

# --- Grid method names ---
grids = list(
    DB.FilteredElementCollector(doc, active_view.Id)
      .OfClass(DB.Grid)
      .WhereElementIsNotElementType()
      .ToElements()
)
out.print_html("<h4>Grid methods containing 'Curve' or 'Extent' or 'Line':</h4><ul>")
if grids:
    for attr in dir(grids[0]):
        if any(kw in attr for kw in ["Curve", "Extent", "Line", "curve", "extent"]):
            out.print_html("<li>{}</li>".format(attr))
else:
    out.print_html("<li>No grids visible in this view</li>")
out.print_html("</ul>")

# --- Try SetCurveInView on first level inside transaction ---
out.print_html("<h4>Test SetCurveInView with Z=0.0 forced:</h4>")
if levels:
    lv = levels[0]
    try:
        curves = list(lv.GetCurvesInView(DB.DatumExtentType.ViewSpecific, active_view))
        if curves:
            c  = curves[0]
            p0 = c.GetEndPoint(0)
            p1 = c.GetEndPoint(1)
            # Force Z to exactly 0.0
            test_line = DB.Line.CreateBound(
                DB.XYZ(p0.X - 0.1, p0.Y, 0.0),
                DB.XYZ(p1.X + 0.1, p1.Y, 0.0)
            )
            tx = DB.Transaction(doc, "diag_test")
            tx.Start()
            try:
                lv.SetCurveInView(DB.DatumExtentType.ViewSpecific, active_view, test_line)
                tx.Commit()
                out.print_html("<p style='color:lime'>SUCCESS with Z=0.0</p>")
            except Exception as e:
                tx.RollbackIfPending()
                out.print_html("<p style='color:red'>Failed Z=0.0: {}</p>".format(str(e)))

            # Try with original Z
            test_line2 = DB.Line.CreateBound(
                DB.XYZ(p0.X - 0.1, p0.Y, p0.Z),
                DB.XYZ(p1.X + 0.1, p1.Y, p1.Z)
            )
            tx2 = DB.Transaction(doc, "diag_test2")
            tx2.Start()
            try:
                lv.SetCurveInView(DB.DatumExtentType.ViewSpecific, active_view, test_line2)
                tx2.Commit()
                out.print_html("<p style='color:lime'>SUCCESS with original Z={:.6f}</p>".format(p0.Z))
            except Exception as e:
                tx2.RollbackIfPending()
                out.print_html("<p style='color:red'>Failed original Z: {}</p>".format(str(e)))
    except Exception as e:
        out.print_html("<p style='color:red'>Outer error: {}</p>".format(str(e)))