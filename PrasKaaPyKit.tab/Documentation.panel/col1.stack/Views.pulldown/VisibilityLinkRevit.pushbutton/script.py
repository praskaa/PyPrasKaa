# -*- coding: utf-8 -*-
__title__ = "Hidden Link Revit in Views/Templates"
__doc__ = "Pilih Link, lalu pilih View/Template mana saja secara manual untuk di-hide."

from Autodesk.Revit.DB import *
from pyrevit import revit, forms, script
import System.Collections.Generic as List

# WORKSHARING CHECK - Import worksharing utilities
from Snippets._worksharing import (
    is_workshared,
    is_element_owned_by_other_user,
    get_checkout_status,
    get_checkout_status_name
)

doc = revit.doc

# Pilih Link
links = {l.Name: l for l in FilteredElementCollector(doc).OfClass(RevitLinkInstance)}
sel_link = forms.SelectFromList.show(sorted(links.keys()), title='Pilih Link')
if not sel_link: script.exit()

# WORKSHARING CHECK - Verify link is not owned by another user
if is_workshared(doc):
    link_element = links[sel_link]
    if is_element_owned_by_other_user(link_element, doc):
        status = get_checkout_status_name(get_checkout_status(link_element, doc))
        forms.alert(
            "Link '{}' is currently owned by another user.\n\n"
            "Status: {}\n\n"
            "Please wait until they release the element or coordinate with them directly.".format(
                sel_link, status
            ),
            title="Worksharing Alert"
        )
        script.exit()

# Pilih Views
views = {}
for v in FilteredElementCollector(doc).OfClass(View):
    if v.IsTemplate or (v.ViewTemplateId == ElementId.InvalidElementId and v.CanEnableTemporaryViewPropertiesMode()):
        views[("T-" if v.IsTemplate else "V-") + v.Name] = v

sel_views = forms.SelectFromList.show(sorted(views.keys()), multiselect=True)
if not sel_views: script.exit()

# Hide dengan chunking dan progress bar (cancellable)
link_ids = List.List[ElementId]([links[sel_link].Id])
total_views = len(sel_views)

# Use output-based progress as primary (more reliable)
# with optional UI progress bar fallback
output = script.get_output()

try:
    tg = TransactionGroup(doc, "Hide Link")
    tg.Start()
    
    try:
        # Try UI progress bar first
        with forms.ProgressBar(
            title='Hiding Link in Views ({value} of {max_value})',
            cancellable=True,
            steps=10
        ) as pb:
            use_ui_progress = True
            for i in range(0, total_views, 10):
                # Check cancel SETIAP iterasi
                if pb.cancelled:
                    tg.RollBack()
                    forms.alert("Operation cancelled by user.")
                    script.exit()
                
                # Calculate progress
                current_count = min(i + 10, total_views)
                pb.update_progress(current_count, total_views)
                
                t = Transaction(doc, "Hide")
                t.Start()
                for name in sel_views[i:i+10]:
                    try: 
                        views[name].HideElements(link_ids)
                    except Exception:
                        pass
                t.Commit()
    except Exception as e:
        # Fallback: Use output-based progress if UI progress bar fails
        use_ui_progress = False
        output.print_md("## Processing {} views...".format(total_views))
        
        for i in range(0, total_views, 10):
            current_count = min(i + 10, total_views)
            output.update_progress(i, total_views)
            
            t = Transaction(doc, "Hide")
            t.Start()
            for name in sel_views[i:i+10]:
                try: 
                    views[name].HideElements(link_ids)
                except Exception:
                    pass
            t.Commit()
    
    tg.Assimilate()
    
    if use_ui_progress:
        forms.alert("Done. Link hidden in {} views.".format(total_views))
    else:
        output.log_success("Done. Link hidden in {} views.".format(total_views))

except Exception as e:
    # Ensure transaction is rolled back on any error
    try:
        tg.RollBack()
    except:
        pass
    forms.alert("Error: {}".format(str(e)))