# -*- coding: utf-8 -*-
'''
Version: 2.1
Date    = 06.05.2026
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
- Worksharing check: skips views/templates owned by another user
- Progress bar with cancel option
- Full error reporting per view/link

_____________________________________________________
Last update:
- 06.05.2026 - 2.1 Added worksharing ownership check before processing.
                   Views/templates owned by another user are skipped
                   and reported separately.
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
    WorksharingUtils,
    CheckoutStatus,
)
import System.Collections.Generic as SCG
from pyrevit import revit, forms, script

doc = revit.doc

# ── Worksharing helper ────────────────────────────────────────────────────
IS_WORKSHARED = doc.IsWorkshared

def is_view_modifiable(view):
    """
    Returns (ok, reason_string).
    ok=True  → safe to modify.
    ok=False → owned by another user; reason_string names the owner.
    When file is NOT workshared, always returns (True, None).
    """
    if not IS_WORKSHARED:
        return True, None

    status = WorksharingUtils.GetCheckoutStatus(doc, view.Id)

    if status == CheckoutStatus.OwnedByOtherUser:
        owner = "another user"
        try:
            info = WorksharingUtils.GetWorksharingTooltipInfo(doc, view.Id)
            if info:
                # CurrentOwner holds the checked-out username
                candidate = info.CurrentOwner
                if candidate and str(candidate).strip():
                    owner = str(candidate)
        except Exception:
            pass  # fallback to "another user" is fine
        return False, owner

    return True, None
    
# ── 1. Collect Revit Link Types ───────────────────────────────────────────
all_link_types = list(FilteredElementCollector(doc).OfClass(RevitLinkType))

if not all_link_types:
    forms.alert("No Revit Link Types found in this document.", exitscript=True)

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

# ── 2. User selects Link Types ────────────────────────────────────────────
sel_link_names = forms.SelectFromList.show(
    sorted(link_type_map.keys()),
    title='Select Revit Link Type(s)',
    multiselect=True,
    button_name='Select Links'
)
if not sel_link_names:
    script.exit()

# ── 3. Collect Views + View Templates ────────────────────────────────────
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
    forms.alert("No valid views found.", exitscript=True)

sel_view_names = forms.SelectFromList.show(
    sorted(view_map.keys()),
    title='Select Views / View Templates',
    multiselect=True,
    button_name='Select Views'
)
if not sel_view_names:
    script.exit()

# ── 4. Helper: redirect to View Template if active ────────────────────────
def get_override_target(view):
    """
    If the view has an active View Template, VG overrides must be
    applied to the template instead.
    Returns: (target_view, redirect_info_string_or_None)
    """
    if view.IsTemplate:
        return view, None

    template_id = view.ViewTemplateId
    if template_id != ElementId.InvalidElementId:
        template = doc.GetElement(template_id)
        if template and template.IsValidObject:
            return template, "{} -> template: {}".format(view.Name, template.Name)

    return view, None

# ── 5. Pre-flight: worksharing ownership check ────────────────────────────
# Resolve target views first, then check ownership once per unique target.
# This avoids checking the same template multiple times when many views
# share it.
blocked_views   = []   # list of (display_name, owner_string)
valid_view_names = []  # display names that passed the check

# Track already-checked targets to avoid duplicate alerts on shared templates
checked_targets = {}   # target_view.Id (int) -> (ok, owner)

def get_target_id_int(v):
    try:
        return v.Id.Value
    except AttributeError:
        return v.Id.IntegerValue

for view_name in sel_view_names:
    view = view_map[view_name]
    target_view, _ = get_override_target(view)
    target_int = get_target_id_int(target_view)

    if target_int not in checked_targets:
        ok, owner = is_view_modifiable(target_view)
        checked_targets[target_int] = (ok, owner)
    else:
        ok, owner = checked_targets[target_int]

    if ok:
        valid_view_names.append(view_name)
    else:
        blocked_views.append((view_name.strip(), owner))

# Report blocked views before proceeding
if blocked_views:
    block_msg = "The following views/templates are owned by another user and will be skipped:\n\n"
    for vn, own in blocked_views:
        block_msg += "  • {} (owned by: {})\n".format(vn, own)

    if not valid_view_names:
        forms.alert(
            block_msg + "\nNo modifiable views remain. Script cancelled.",
            title="Worksharing Conflict"
        )
        script.exit()

    block_msg += "\nContinue with the remaining {} view(s)?".format(len(valid_view_names))
    if not forms.alert(block_msg, title="Worksharing Conflict", yes=True, no=True):
        script.exit()

# ── 6. Main Processing ────────────────────────────────────────────────────
results = {
    "success"  : 0,
    "errors"   : [],
    "redirects": [],
    "blocked"  : blocked_views,
}

tg = TransactionGroup(doc, "Hide Revit Links (VG)")
tg.Start()

try:
    for link_name in sel_link_names:
        link_type    = link_type_map[link_name]
        link_type_id = link_type.Id

        id_list = SCG.List[ElementId]()
        id_list.Add(link_type_id)

        for view_name in valid_view_names:
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

    # ── Summary report ─────────────────────────────────────────────────
    summary = (
        "Done!\n\n"
        "[OK] Success : {s} operation(s)\n"
        "[X] Errors  : {e} operation(s)\n"
        "[/] Skipped : {b} view(s) (worksharing conflict)"
    ).format(
        s=results["success"],
        e=len(results["errors"]),
        b=len(results["blocked"])
    )

    if results["redirects"]:
        summary += "\n\n[!] Redirected to View Template ({} view(s)):".format(
            len(results["redirects"])
        )
        for r in results["redirects"]:
            summary += "\n  • " + r

    if results["blocked"]:
        summary += "\n\n[!] Skipped (owned by another user):"
        for vn, own in results["blocked"]:
            summary += "\n  • {} (owner: {})".format(vn, own)

    if results["errors"]:
        summary += "\n\n[!] Errors:"
        for e in results["errors"]:
            summary += "\n  • " + e

    forms.alert(summary, title="Hide Revit Links - Done")

except Exception as fatal:
    try:
        tg.RollBack()
    except Exception:
        pass
    forms.alert(
        "Fatal error:\n{}\n\nAll changes rolled back.".format(str(fatal)),
        title="Error"
    )