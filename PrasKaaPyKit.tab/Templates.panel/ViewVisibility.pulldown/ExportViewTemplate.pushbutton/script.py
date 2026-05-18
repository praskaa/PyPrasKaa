# -*- coding: utf-8 -*-
# pylint: disable=import-error,invalid-name
__title__   = "Export VG"
__doc__     = """Version   = 1.3
Date        = 2026-03-13
Description = Export Visibility/Graphics dari View Template ke JSON.
              Mendukung transfer lintas versi Revit (2019+).
Author      = PrasKaa"""

import os
import json

from pyrevit import forms, script
from pyrevit import revit, DB

doc = revit.doc
app = __revit__.Application  # type: ignore

NO_VG_VIEWTYPES = [
    DB.ViewType.Schedule,
    DB.ViewType.DrawingSheet,
    DB.ViewType.Undefined,
    DB.ViewType.Internal,
    DB.ViewType.ProjectBrowser,
    DB.ViewType.SystemBrowser,
]


# =============================================================================
# HELPER: Color
# =============================================================================

def color_to_dict(color):
    """DB.Color -> dict {r,g,b}. Return None jika tidak valid."""
    if color is None:
        return None
    try:
        if not color.IsValid:
            return None
        return {"r": int(color.Red), "g": int(color.Green), "b": int(color.Blue)}
    except Exception:
        return None


# =============================================================================
# HELPER: OverrideGraphicSettings
# =============================================================================

def overrides_to_dict(ogs):
    """DB.OverrideGraphicSettings -> dict yang bisa di-JSON-kan."""
    if ogs is None:
        return None

    def eid_to_int(eid):
        # IronPython: ElementId tidak selalu expose .IntegerValue
        # str(ElementId) menghasilkan angka langsung, misal "1176"
        try:
            return eid.IntegerValue
        except AttributeError:
            try:
                return int(str(eid))
            except Exception:
                return -1

    def lp_to_str(lp_id):
        """LinePatternId -> nama string / '__SOLID__' / None."""
        if lp_id is None:
            return None
        try:
            if lp_id == DB.LinePatternElement.GetSolidPatternId():
                return "__SOLID__"
            if eid_to_int(lp_id) == -1:
                return None
            elem = doc.GetElement(DB.ElementId(eid_to_int(lp_id)))
            return elem.Name if elem else None
        except Exception:
            return None

    def fp_to_dict(fp_id):
        """FillPatternId -> dict {name, target, is_solid, grids}.
        Grids disimpan agar pattern bisa di-recreate di dokumen tujuan."""
        if fp_id is None:
            return None
        try:
            int_val = eid_to_int(fp_id)
            if int_val == -1:
                return None
            fp_elem = doc.GetElement(DB.ElementId(int_val))
            if not fp_elem:
                return None
            fp = fp_elem.GetFillPattern()
            if fp is None:
                return {"name": fp_elem.Name, "target": None,
                        "is_solid": False, "grids": []}
            grids_data = []
            try:
                for grid in fp.GetFillGrids():
                    try:
                        segments = list(grid.GetSegments())
                    except Exception:
                        segments = []
                    grids_data.append({
                        "angle":    grid.Angle,
                        "offset":   grid.Offset,
                        "shift":    grid.Shift,
                        "origin_u": grid.Origin.U,
                        "origin_v": grid.Origin.V,
                        "segments": segments,
                    })
            except Exception:
                pass
            return {
                "name":     fp_elem.Name,
                "target":   str(fp.Target),
                "is_solid": fp.IsSolidFill,
                "grids":    grids_data,
            }
        except Exception:
            return None

    def safe_get(obj, *attrs):
        # Revit 2019+ rename property fill. Coba nama baru dulu, fallback nama lama.
        for a in attrs:
            try:
                return getattr(obj, a)
            except AttributeError:
                pass
        return None

    try:
        dl = int(ogs.DetailLevel)
        dl = dl if dl != -1 else None
    except Exception:
        dl = None

    return {
        "proj_line_weight":             ogs.ProjectionLineWeight,
        "proj_line_color":              color_to_dict(ogs.ProjectionLineColor),
        "proj_line_pattern":            lp_to_str(ogs.ProjectionLinePatternId),
        "proj_fill_color":              color_to_dict(safe_get(ogs, "SurfaceForegroundPatternColor", "ProjectionFillColor")),
        "proj_fill_pattern":            fp_to_dict(safe_get(ogs,   "SurfaceForegroundPatternId",     "ProjectionFillPatternId")),
        "proj_fill_pattern_visible":    safe_get(ogs, "IsSurfaceForegroundPatternVisible",            "IsProjectionFillPatternVisible"),
        "proj_bg_fill_color":           color_to_dict(safe_get(ogs, "SurfaceBackgroundPatternColor")),
        "proj_bg_fill_pattern":         fp_to_dict(safe_get(ogs,   "SurfaceBackgroundPatternId")),
        "proj_bg_fill_pattern_visible": safe_get(ogs, "IsSurfaceBackgroundPatternVisible"),
        "cut_line_weight":              ogs.CutLineWeight,
        "cut_line_color":               color_to_dict(ogs.CutLineColor),
        "cut_line_pattern":             lp_to_str(ogs.CutLinePatternId),
        "cut_fill_color":               color_to_dict(safe_get(ogs, "CutForegroundPatternColor", "CutFillColor")),
        "cut_fill_pattern":             fp_to_dict(safe_get(ogs,   "CutForegroundPatternId",    "CutFillPatternId")),
        "cut_fill_pattern_visible":     safe_get(ogs, "IsCutForegroundPatternVisible",          "IsCutFillPatternVisible"),
        "cut_bg_fill_color":            color_to_dict(safe_get(ogs, "CutBackgroundPatternColor")),
        "cut_bg_fill_pattern":          fp_to_dict(safe_get(ogs,   "CutBackgroundPatternId")),
        "cut_bg_fill_pattern_visible":  safe_get(ogs, "IsCutBackgroundPatternVisible"),
        "halftone":                     ogs.Halftone,
        "transparency":                 ogs.Transparency,
        "detail_level":                 dl,
    }


# =============================================================================
# HELPER: Iterasi kategori (IronPython-safe, ForwardIterator)
# =============================================================================

def iter_categories(cat_collection):
    it = cat_collection.ForwardIterator()
    it.Reset()
    while it.MoveNext():
        yield it.Current


# =============================================================================
# HELPER: Export categories & filters
# =============================================================================

def export_categories(view):
    result = []
    for cat in iter_categories(doc.Settings.Categories):
        if int(cat.BuiltInCategory) >= -1:
            continue
        try:
            hidden    = view.GetCategoryHidden(cat.Id)
            overrides = view.GetCategoryOverrides(cat.Id)
        except Exception:
            continue
        subcats = []
        for sub in iter_categories(cat.SubCategories):
            if int(sub.BuiltInCategory) >= -1:
                continue
            try:
                subcats.append({
                    "bic":       str(sub.BuiltInCategory),
                    "name":      sub.Name,
                    "visible":   not view.GetCategoryHidden(sub.Id),
                    "overrides": overrides_to_dict(view.GetCategoryOverrides(sub.Id)),
                })
            except Exception:
                pass
        result.append({
            "bic":           str(cat.BuiltInCategory),
            "name":          cat.Name,
            "visible":       not hidden,
            "overrides":     overrides_to_dict(overrides),
            "subcategories": subcats,
        })
    return result


def export_filters(view):
    result = []
    try:
        filter_ids = view.GetFilters()
    except Exception:
        return result
    for fid in filter_ids:
        try:
            f = doc.GetElement(fid)
            if not f:
                continue
            result.append({
                "name":      f.Name,
                "visible":   view.GetFilterVisibility(fid),
                "overrides": overrides_to_dict(view.GetFilterOverrides(fid)),
            })
        except Exception:
            pass
    return result


# =============================================================================
# RUN
# =============================================================================

all_templates = [
    v for v in DB.FilteredElementCollector(doc).OfClass(DB.View).ToElements()
    if v.IsTemplate and v.ViewType not in NO_VG_VIEWTYPES
]
if not all_templates:
    forms.alert("Tidak ada View Template dengan VG support di dokumen ini.",
                exitscript=True)

selected = forms.SelectFromList.show(
    sorted(all_templates, key=lambda v: v.Name),
    name_attr="Name",
    title="Pilih View Template untuk di-Export VG",
    button_name="Export",
    multiselect=True,
)
if not selected:
    script.exit()

output_folder = forms.pick_folder(title="Pilih folder untuk menyimpan file JSON")
if not output_folder:
    script.exit()

exported = []
for vt in selected:
    data = {
        "template_name": vt.Name,
        "revit_version": str(app.VersionNumber),
        "view_type":     str(vt.ViewType),
        "categories":    export_categories(vt),
        "filters":       export_filters(vt),
    }
    safe_name = vt.Name.replace(" ", "_").replace("/", "-").replace("\\", "-")
    filepath  = os.path.join(output_folder, "VG_{}.json".format(safe_name))
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    exported.append("{} ({} kat, {} filter)".format(
        os.path.basename(filepath), len(data["categories"]), len(data["filters"])))

forms.alert("Export selesai!\n\n" + "\n".join(exported), title="Export VG - Selesai")