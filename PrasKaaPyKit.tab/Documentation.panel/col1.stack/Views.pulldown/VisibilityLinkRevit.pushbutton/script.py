# -*- coding: utf-8 -*-
__title__ = "Hidden Link Revit in Views/Templates"
__doc__ = "Pilih Link, lalu pilih View/Template mana saja secara manual untuk di-hide."

from Autodesk.Revit.DB import *
from pyrevit import revit, forms, script
import System.Collections.Generic as List

doc = revit.doc

# Pilih Link
links = {l.Name: l for l in FilteredElementCollector(doc).OfClass(RevitLinkInstance)}
sel_link = forms.SelectFromList.show(sorted(links.keys()), title='Pilih Link')
if not sel_link: script.exit()

# Pilih Views
views = {}
for v in FilteredElementCollector(doc).OfClass(View):
    if v.IsTemplate or (v.ViewTemplateId == ElementId.InvalidElementId and v.CanEnableTemporaryViewPropertiesMode()):
        views[("T-" if v.IsTemplate else "V-") + v.Name] = v

sel_views = forms.SelectFromList.show(sorted(views.keys()), multiselect=True)
if not sel_views: script.exit()

# Hide dengan chunking
link_ids = List.List[ElementId]([links[sel_link].Id])
tg = TransactionGroup(doc, "Hide Link")
tg.Start()

for i in range(0, len(sel_views), 10):
    t = Transaction(doc, "Hide")
    t.Start()
    for name in sel_views[i:i+10]:
        try: views[name].HideElements(link_ids)
        except: pass
    t.Commit()

tg.Assimilate()
forms.alert("Done.")