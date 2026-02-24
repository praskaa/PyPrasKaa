# -*- coding: utf-8 -*-
__title__ = "Hide Link in Views"

from Autodesk.Revit.DB import *
from pyrevit import revit, forms, script
import System.Collections.Generic as SCG

doc = revit.doc

# Links — group by nama dari instance
link_dict = {}
for inst in FilteredElementCollector(doc).OfClass(RevitLinkInstance):
    name = inst.Name.split(" : ")[0]
    link_dict.setdefault(name, []).append(inst)

if not link_dict:
    forms.alert("Tidak ada Revit Link.", exitscript=True)

# Views — skip yang punya active template
SKIP_TYPES = {ViewType.ProjectBrowser, ViewType.SystemBrowser, ViewType.Undefined, ViewType.DrawingSheet}
view_dict = {}
for v in FilteredElementCollector(doc).OfClass(View):
    if v.IsTemplate:
        view_dict["[T] " + v.Name] = v
    elif v.ViewType not in SKIP_TYPES and v.ViewTemplateId == ElementId.InvalidElementId:
        view_dict["[V] " + v.Name] = v

# UI
sel_links = forms.SelectFromList.show(sorted(link_dict), title="Pilih Link", multiselect=True)
if not sel_links: script.exit()

sel_views = forms.SelectFromList.show(sorted(view_dict), title="Pilih View / Template", multiselect=True)
if not sel_views: script.exit()

total = len(sel_links) * len(sel_views)

with forms.ProgressBar(title="{value} / {max_value} — Hiding Links", cancellable=True) as pb:
    with Transaction(doc, "Hide Revit Links") as t:
        t.Start()
        n = 0
        for vk in sel_views:
            if pb.cancelled: break
            view = view_dict[vk]
            for lk in sel_links:
                ids = SCG.List[ElementId]([i.Id for i in link_dict[lk]])
                try:
                    view.HideElements(ids)
                except:
                    pass
                n += 1
                pb.update_progress(n, total)
        t.Commit() if not pb.cancelled else t.RollBack()

if not pb.cancelled:
    forms.alert("Selesai.")