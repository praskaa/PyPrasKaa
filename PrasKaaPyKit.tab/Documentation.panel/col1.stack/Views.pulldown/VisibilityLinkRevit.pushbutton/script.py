# -*- coding: utf-8 -*-
'''
Version: 2.0
Date    = 10.03.2026
_____________________________________________________________________
Description:
Hides Revit link types in selected views or view templates via VG
(Visibility/Graphics) checkbox — same as unchecking the link in
VG > Revit Links tab.

Works by calling view.HideElements([link_type_id]) which correctly
unchecks the checkbox per link type per view.
_____________________________________________________________________
How-to:
1. Click "Hide Link Revit"
2. Select one or more Link Types to hide
3. Select views and/or view templates
4. Links will be hidden (VG checkbox unchecked) in selected views

Notes:
- Uses HideElements(RevitLinkType.Id) — the correct API for VG checkbox
- SetLinkOverrides is NOT used (it has no Hidden option)
- If a view has an active View Template, override is applied to the
  template instead (since template controls VG settings)
- Progress bar with cancel option
- Full error reporting per view/link

_____________________________________________________
Last update:
- 10.03.2026 - 2.0 Full rewrite: use HideElements(link_type_id) as
                   correct method to uncheck VG checkbox per link type.
                   Fixed view filter, template redirect, error reporting.
- 09.03.2026 - 1.1 Fix: lt.get_Name -> lt.Name
- 04.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa
'''

__title__ = "Hides Revit Link In Views"
__author__ = "PrasKaa"

# ── Imports ───────────────────────────────────────────────────────────────
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    RevitLinkType,
    RevitLinkInstance,
    View,
    ViewType,
    ElementId,
    Transaction,
    TransactionGroup,
    Element,
)
import System.Collections.Generic as SCG
from pyrevit import revit, forms, script

doc = revit.doc

# ── 1. Kumpulkan Revit Link Types ─────────────────────────────────────────
# Gunakan RevitLinkType (bukan Instance) agar HideElements bekerja di VG level
all_link_types = list(FilteredElementCollector(doc).OfClass(RevitLinkType))

if not all_link_types:
    forms.alert("Tidak ada Revit Link Type ditemukan di dokumen ini.", exitscript=True)

# Build dict: name -> link_type element
# Gunakan Element.Name.GetValue() untuk IronPython compatibility
link_type_map = {}
for lt in all_link_types:
    try:
        name = Element.Name.GetValue(lt)
    except Exception:
        try:
            name = lt.Name
        except Exception:
            name = str(lt.Id)
    link_type_map[name] = lt

# ── 2. User pilih Link Types ──────────────────────────────────────────────
sel_link_names = forms.SelectFromList.show(
    sorted(link_type_map.keys()),
    title='Pilih Revit Link Type (bisa multiple)',
    multiselect=True,
    button_name='Pilih Link'
)
if not sel_link_names:
    script.exit()

# ── 3. Kumpulkan Views + View Templates ───────────────────────────────────
# Exclude view types yang tidak support HideElements / VG override
EXCLUDED_VIEW_TYPES = {
    ViewType.Schedule,
    ViewType.ColumnSchedule,
    ViewType.PanelSchedule,
    ViewType.Walkthrough,
    ViewType.Rendering,
    ViewType.SystemBrowser,
    ViewType.ProjectBrowser,
    ViewType.DrawingSheet,
    ViewType.Undefined,
    ViewType.Internal,
    ViewType.Report,
}

view_map = {}
for v in FilteredElementCollector(doc).OfClass(View):
    if not v.IsValidObject:
        continue
    if v.ViewType in EXCLUDED_VIEW_TYPES:
        continue
    prefix = "[TEMPLATE] " if v.IsTemplate else "[VIEW]     "
    display_name = prefix + v.Name
    view_map[display_name] = v

if not view_map:
    forms.alert("Tidak ada view yang valid ditemukan.", exitscript=True)

sel_view_names = forms.SelectFromList.show(
    sorted(view_map.keys()),
    title='Pilih Views / View Templates',
    multiselect=True,
    button_name='Pilih View'
)
if not sel_view_names:
    script.exit()

# ── 4. Helper: redirect ke View Template jika aktif ───────────────────────
def get_override_target(view):
    """
    Jika view punya View Template aktif, override VG harus dilakukan
    di View Template-nya — bukan di view biasa.
    Return: (target_view, redirect_info_string_or_None)
    """
    if view.IsTemplate:
        return view, None

    template_id = view.ViewTemplateId
    if template_id != ElementId.InvalidElementId:
        template = doc.GetElement(template_id)
        if template and template.IsValidObject:
            return template, "{} -> template: {}".format(view.Name, template.Name)

    return view, None

# ── 5. Main Processing ────────────────────────────────────────────────────
total_links = len(sel_link_names)
total_views = len(sel_view_names)

results = {
    "success"  : 0,
    "errors"   : [],
    "redirects": [],
}

tg = TransactionGroup(doc, "Hide Revit Links (VG)")
tg.Start()

op_count = 0

try:
    for link_name in sel_link_names:
        link_type    = link_type_map[link_name]
        link_type_id = link_type.Id

        id_list = SCG.List[ElementId]()
        id_list.Add(link_type_id)

        for view_name in sel_view_names:
            op_count += 1
            view = view_map[view_name]

            target_view, redirect_msg = get_override_target(view)
            if redirect_msg and redirect_msg not in results["redirects"]:
                results["redirects"].append(redirect_msg)

            t = Transaction(doc, "Hide Link")
            t.Start()
            try:
                target_view.HideElements(id_list)
                t.Commit()
                results["success"] += 1
            except Exception as e:
                t.RollBack()
                results["errors"].append("{} | {}: {}".format(
                    link_name, view_name.strip(), str(e)
                ))

    tg.Assimilate()

    # ── Report ringkas ─────────────────────────────────────────────────────
    summary = (
        "Selesai!\n\n"
        "✓ Berhasil : {s} operasi\n"
        "✗ Error    : {e} operasi"
    ).format(s=results["success"], e=len(results["errors"]))

    if results["redirects"]:
        summary += "\n\n⚠ Redirect ke View Template ({} view):".format(
            len(results["redirects"])
        )
        for r in results["redirects"]:
            summary += "\n  • " + r

    if results["errors"]:
        summary += "\n\n⚠ Errors:\n"
        for e in results["errors"]:
            summary += "  • " + e + "\n"

    forms.alert(summary, title="Hide Link Revit - Selesai")

except Exception as fatal:
    try:
        tg.RollBack()
    except Exception:
        pass
    forms.alert(
        "Error kritis:\n{}\n\nSemua perubahan di-rollback.".format(str(fatal)),
        title="Error"
    )