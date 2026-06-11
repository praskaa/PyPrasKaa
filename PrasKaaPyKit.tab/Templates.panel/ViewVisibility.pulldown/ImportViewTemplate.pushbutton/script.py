# -*- coding: utf-8 -*-
# pylint: disable=import-error,invalid-name
__title__   = "Import VG"
__doc__     = """Version   = 1.3
Date        = 2026-03-13
Description = Import Visibility/Graphics dari JSON ke View Template baru (nama + suffix '*').
              Mendukung transfer lintas versi Revit (2019+).
              Fill Pattern yang tidak ada akan di-recreate dari geometry data.
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

def dict_to_color(d):
    """dict {r,g,b} -> DB.Color. Return InvalidColorValue jika None."""
    if not d:
        return DB.Color.InvalidColorValue
    return DB.Color(int(d["r"]), int(d["g"]), int(d["b"]))


# =============================================================================
# HELPER: LinePattern
# =============================================================================

def resolve_line_pattern(name):
    """Cari LinePatternElement by name. Return ElementId atau InvalidElementId."""
    if not name:
        return DB.ElementId.InvalidElementId
    if name == "__SOLID__":
        return DB.LinePatternElement.GetSolidPatternId()
    for lp in DB.FilteredElementCollector(doc).OfClass(DB.LinePatternElement).ToElements():
        if lp.Name == name:
            return lp.Id
    return DB.ElementId.InvalidElementId


# =============================================================================
# HELPER: FillPattern
# =============================================================================

def resolve_fill_pattern(fp_data):
    """Resolve FillPattern dari dict {name, target, is_solid, grids}.
    1. Cari by name di dokumen.
    2. Jika tidak ada, buat FillPatternElement baru dari data geometry.
    Harus dipanggil dalam Transaction aktif.
    Return ElementId."""

    if not fp_data:
        return DB.ElementId.InvalidElementId

    # Backward compat: terima string biasa
    if isinstance(fp_data, str):
        name, grids_data, target_str, is_solid = fp_data, [], "Drafting", False
    else:
        name       = fp_data.get("name")
        grids_data = fp_data.get("grids", [])
        target_str = fp_data.get("target", "Drafting")
        is_solid   = fp_data.get("is_solid", False)

    if not name:
        return DB.ElementId.InvalidElementId

    # 1. Cari by name
    for fp in DB.FilteredElementCollector(doc).OfClass(DB.FillPatternElement).ToElements():
        if fp.Name == name:
            return fp.Id

    # 2. Recreate dari geometry
    if not grids_data:
        return DB.ElementId.InvalidElementId
    try:
        fp_target = DB.FillPatternTarget.Model if target_str == "Model" \
                    else DB.FillPatternTarget.Drafting
        new_fp = DB.FillPattern(name, fp_target, DB.FillPatternHostOrientation.ToView)

        fill_grids = []
        for g in grids_data:
            grid        = DB.FillGrid()
            grid.Angle  = g.get("angle",  0.0)
            grid.Offset = g.get("offset", 0.01)
            grid.Shift  = g.get("shift",  0.0)
            grid.Origin = DB.UV(g.get("origin_u", 0.0), g.get("origin_v", 0.0))
            segs = g.get("segments", [])
            if segs:
                from pyrevit.framework import List
                grid.SetSegments(List[float](segs))
            fill_grids.append(grid)

        if fill_grids:
            from pyrevit.framework import List
            new_fp.SetFillGrids(List[DB.FillGrid](fill_grids))

        return DB.FillPatternElement.Create(doc, new_fp).Id
    except Exception:
        return DB.ElementId.InvalidElementId


# =============================================================================
# HELPER: OverrideGraphicSettings
# =============================================================================

def dict_to_overrides(d):
    """dict -> DB.OverrideGraphicSettings."""
    ogs = DB.OverrideGraphicSettings()
    if not d:
        return ogs

    def safe_set(fn, *args):
        try:
            fn(*args)
        except Exception:
            pass

    # Line
    if d.get("proj_line_weight", -1) > 0:
        safe_set(ogs.SetProjectionLineWeight, d["proj_line_weight"])
    if d.get("proj_line_color"):
        safe_set(ogs.SetProjectionLineColor, dict_to_color(d["proj_line_color"]))
    if d.get("proj_line_pattern"):
        safe_set(ogs.SetProjectionLinePatternId, resolve_line_pattern(d["proj_line_pattern"]))
    if d.get("cut_line_weight", -1) > 0:
        safe_set(ogs.SetCutLineWeight, d["cut_line_weight"])
    if d.get("cut_line_color"):
        safe_set(ogs.SetCutLineColor, dict_to_color(d["cut_line_color"]))
    if d.get("cut_line_pattern"):
        safe_set(ogs.SetCutLinePatternId, resolve_line_pattern(d["cut_line_pattern"]))

    # Surface Foreground (Projection Fill)
    if d.get("proj_fill_color"):
        safe_set(ogs.SetSurfaceForegroundPatternColor, dict_to_color(d["proj_fill_color"]))
    if d.get("proj_fill_pattern"):
        safe_set(ogs.SetSurfaceForegroundPatternId, resolve_fill_pattern(d["proj_fill_pattern"]))
    if d.get("proj_fill_pattern_visible") is not None:
        safe_set(ogs.SetSurfaceForegroundPatternVisible, d["proj_fill_pattern_visible"])

    # Surface Background
    if d.get("proj_bg_fill_color"):
        safe_set(ogs.SetSurfaceBackgroundPatternColor, dict_to_color(d["proj_bg_fill_color"]))
    if d.get("proj_bg_fill_pattern"):
        safe_set(ogs.SetSurfaceBackgroundPatternId, resolve_fill_pattern(d["proj_bg_fill_pattern"]))
    if d.get("proj_bg_fill_pattern_visible") is not None:
        safe_set(ogs.SetSurfaceBackgroundPatternVisible, d["proj_bg_fill_pattern_visible"])

    # Cut Foreground
    if d.get("cut_fill_color"):
        safe_set(ogs.SetCutForegroundPatternColor, dict_to_color(d["cut_fill_color"]))
    if d.get("cut_fill_pattern"):
        safe_set(ogs.SetCutForegroundPatternId, resolve_fill_pattern(d["cut_fill_pattern"]))
    if d.get("cut_fill_pattern_visible") is not None:
        safe_set(ogs.SetCutForegroundPatternVisible, d["cut_fill_pattern_visible"])

    # Cut Background
    if d.get("cut_bg_fill_color"):
        safe_set(ogs.SetCutBackgroundPatternColor, dict_to_color(d["cut_bg_fill_color"]))
    if d.get("cut_bg_fill_pattern"):
        safe_set(ogs.SetCutBackgroundPatternId, resolve_fill_pattern(d["cut_bg_fill_pattern"]))
    if d.get("cut_bg_fill_pattern_visible") is not None:
        safe_set(ogs.SetCutBackgroundPatternVisible, d["cut_bg_fill_pattern_visible"])

    # Other
    if d.get("halftone") is not None:
        safe_set(ogs.SetHalftone, d["halftone"])
    if d.get("transparency") is not None:
        # Revit 2026+: SetSurfaceTransparency; versi lama: SetTransparency
        try:
            ogs.SetSurfaceTransparency(d["transparency"])
        except AttributeError:
            safe_set(ogs.SetTransparency, d["transparency"])
    if d.get("detail_level") is not None:
        safe_set(ogs.SetDetailLevel, DB.ViewDetailLevel(d["detail_level"]))

    return ogs


# =============================================================================
# HELPER: Resolve category & subcategory
# =============================================================================

def resolve_category_id(bic_name):
    """BuiltInCategory string -> ElementId kategori di dokumen ini."""
    try:
        bic = getattr(DB.BuiltInCategory, bic_name, None)
        if bic is None:
            bic = DB.BuiltInCategory(int(bic_name))
        cat = doc.Settings.Categories.get_Item(bic)
        return cat.Id if cat else None
    except Exception:
        return None


def resolve_subcategory_id(parent_bic_name, sub_name):
    """Nama parent BIC + nama subcat -> ElementId."""
    try:
        bic = getattr(DB.BuiltInCategory, parent_bic_name, None)
        if bic is None:
            bic = DB.BuiltInCategory(int(parent_bic_name))
        parent_cat = doc.Settings.Categories.get_Item(bic)
        if parent_cat:
            for sub in parent_cat.SubCategories:
                if sub.Name == sub_name:
                    return sub.Id
    except Exception:
        pass
    return None


# =============================================================================
# MAIN: Apply categories & filters ke View Template
# =============================================================================

def apply_categories(vt, categories_data):
    """Apply visibility & overrides semua kategori ke View Template.
    Return list nama kategori yang di-skip (tidak ditemukan di dokumen)."""
    skipped = []
    for cat_data in categories_data:
        cat_id = resolve_category_id(cat_data["bic"])
        if not cat_id:
            skipped.append(cat_data.get("name", cat_data["bic"]))
            continue
        try:
            vt.SetCategoryHidden(cat_id, not cat_data["visible"])
        except Exception:
            pass  # beberapa kategori tidak bisa di-hide, lanjut apply overrides
        try:
            vt.SetCategoryOverrides(cat_id, dict_to_overrides(cat_data.get("overrides")))
        except Exception:
            pass
        for sub in cat_data.get("subcategories", []):
            sub_id = resolve_subcategory_id(cat_data["bic"], sub["name"])
            if not sub_id:
                continue
            try:
                vt.SetCategoryHidden(sub_id, not sub["visible"])
                vt.SetCategoryOverrides(sub_id, dict_to_overrides(sub.get("overrides")))
            except Exception:
                pass
    return skipped


def apply_filters(vt, filters_data):
    """Apply filter visibility & overrides ke View Template.
    Return list nama filter yang di-skip (tidak ada di dokumen)."""
    skipped = []
    filter_by_name = {
        f.Name: f for f in DB.FilteredElementCollector(doc)
                              .OfClass(DB.FilterElement).ToElements()
    }
    for f_data in filters_data:
        fname = f_data.get("name")
        if fname not in filter_by_name:
            skipped.append(fname)
            continue
        try:
            fid = filter_by_name[fname].Id
            vt.AddFilter(fid)
            vt.SetFilterVisibility(fid, f_data["visible"])
            vt.SetFilterOverrides(fid, dict_to_overrides(f_data.get("overrides")))
        except Exception:
            skipped.append(fname)
    return skipped


# =============================================================================
# MAIN: Buat View Template baru sebagai target
# =============================================================================

def create_new_template(base_name, target_viewtype_str=None):
    """Duplicate View Template yang ada, rename ke base_name + '*'.
    Pilih base template yang ViewType-nya sama dengan sumber JSON."""
    from pyrevit.framework import List

    all_templates = [
        v for v in DB.FilteredElementCollector(doc).OfClass(DB.View).ToElements()
        if v.IsTemplate
    ]
    vg_templates = [v for v in all_templates if v.ViewType not in NO_VG_VIEWTYPES]
    if not vg_templates:
        forms.alert("Tidak ada View Template dengan VG support untuk dijadikan base.",
                    exitscript=True)

    # Cari ViewType yang sama dengan sumber, fallback ke template pertama
    base = next((v for v in vg_templates
                 if str(v.ViewType) == target_viewtype_str), vg_templates[0])

    # Generate nama unik (tambah '*' sampai tidak konflik)
    existing = {v.Name for v in all_templates}
    new_name = base_name + "*"
    while new_name in existing:
        new_name += "*"

    # Duplicate via CopyElements (tidak perlu Transaction aktif)
    new_ids      = DB.ElementTransformUtils.CopyElements(
                        doc, List[DB.ElementId]([base.Id]),
                        doc, DB.Transform.Identity, DB.CopyPasteOptions())
    new_vt       = doc.GetElement(list(new_ids)[0])
    new_vt.Name  = new_name
    return new_vt


# =============================================================================
# RUN
# =============================================================================

json_files = forms.pick_file(
    files_filter="JSON Files (*.json)|*.json",
    multi_file=True,
    title="Pilih file JSON VG untuk di-Import",
)
if not json_files:
    script.exit()
if isinstance(json_files, str):
    json_files = [json_files]

summary_lines = []

for filepath in json_files:
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except Exception as ex:
        summary_lines.append("[GAGAL baca] {} - {}".format(
            os.path.basename(filepath), ex))
        continue

    template_name   = data.get("template_name", "Unknown")
    source_version  = data.get("revit_version", "?")
    categories_data = data.get("categories", [])
    filters_data    = data.get("filters", [])

    # Step 0: Pre-create FillPattern yang belum ada (harus transaction tersendiri)
    t0 = DB.Transaction(doc, "Pre-create Fill Patterns")
    t0.Start()
    try:
        for cat_data in categories_data:
            for key in ["proj_fill_pattern", "proj_bg_fill_pattern",
                        "cut_fill_pattern",  "cut_bg_fill_pattern"]:
                fp_data = (cat_data.get("overrides") or {}).get(key)
                if fp_data and isinstance(fp_data, dict):
                    resolve_fill_pattern(fp_data)
        t0.Commit()
    except Exception:
        t0.RollBack()

    # Step 1: Duplicate template (CopyElements tidak bisa dalam Transaction)
    t1 = DB.Transaction(doc, "Duplicate Template: {}*".format(template_name))
    t1.Start()
    try:
        new_vt = create_new_template(template_name, data.get("view_type"))
        t1.Commit()
    except Exception as ex:
        t1.RollBack()
        summary_lines.append("[GAGAL duplicate] {} - {}".format(template_name, ex))
        continue

    # Step 2: Apply VG
    new_vt_id = new_vt.Id
    t2 = DB.Transaction(doc, "Apply VG: {}*".format(template_name))
    t2.Start()
    try:
        new_vt          = doc.GetElement(new_vt_id)
        skipped_cats    = apply_categories(new_vt, categories_data)
        skipped_filters = apply_filters(new_vt, filters_data)
        t2.Commit()
    except Exception as ex:
        t2.RollBack()
        summary_lines.append("[GAGAL apply VG] {} - {}".format(template_name, ex))
        continue

    line = "[OK] '{}' -> '{}' (dari Revit {})".format(
        template_name, new_vt.Name, source_version)
    if skipped_cats:
        line += "\n     Skip kategori ({}): {}".format(
            len(skipped_cats), ", ".join(skipped_cats[:5]))
    if skipped_filters:
        line += "\n     Skip filter ({}): {}".format(
            len(skipped_filters), ", ".join(skipped_filters[:5]))
    summary_lines.append(line)

forms.alert("Import VG selesai!\n\n" + "\n\n".join(summary_lines),
            title="Import VG - Selesai")