# -*- coding: utf-8 -*-
__title__ = "Hide Link Revit in Views/Templates (VG Level)"
__doc__ = "Pilih Link Type (bisa multiple), lalu pilih View/Template mana saja untuk disembunyikan. Semua instance dari link type tersebut akan terpengaruh."

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

# Kumpulkan Link Types (bukan Instance) - agar semua instance terpengaruh
link_types = {lt.Name: lt for lt in FilteredElementCollector(doc).OfClass(RevitLinkType)}

if not link_types:
    forms.alert("Tidak ada Revit Link Type ditemukan.", exitscript=True)

# Pilih Link Types (MULTI-SELECT)
sel_link_types = forms.SelectFromList.show(
    sorted(link_types.keys()), 
    title='Pilih Link Type (bisa multiple)',
    multiselect=True
)
if not sel_link_types: script.exit()

# Pilih Views
views = {}
for v in FilteredElementCollector(doc).OfClass(View):
    if v.IsTemplate or (v.ViewTemplateId == ElementId.InvalidElementId and v.CanEnableTemporaryViewPropertiesMode()):
        views[("T-" if v.IsTemplate else "V-") + v.Name] = v

sel_views = forms.SelectFromList.show(sorted(views.keys()), multiselect=True)
if not sel_views: script.exit()

# Hide dengan chunking dan progress bar (cancellable)
total_links = len(sel_link_types)
total_views = len(sel_views)
output = script.get_output()

# Check Revit version for SetLinkOverrides support
# SetLinkOverrides is available in Revit 2023+
revit_version = int(doc.Application.VersionNumber)
use_vg_method = revit_version >= 2023

if not use_vg_method:
    output.log_warning(
        "Revit {} terdeteksi. SetLinkOverrides() hanya tersedia di Revit 2023+.\n"
        "Akan menggunakan metode HideElements() sebagai fallback.".format(revit_version)
    )

try:
    tg = TransactionGroup(doc, "Hide Link di Views")
    tg.Start()
    
    try:
        # Progress bar
        total_ops = total_links * total_views
        with forms.ProgressBar(
            title='Hiding Links in Views ({value} of {max_value})',
            cancellable=True,
            steps=10
        ) as pb:
            op_count = 0
            
            for link_type_name in sel_link_types:
                link_type = link_types[link_type_name]
                link_type_id = link_type.Id
                
                for view_name in sel_views:
                    # Check cancel
                    if pb.cancelled:
                        tg.RollBack()
                        forms.alert("Operation cancelled by user.")
                        script.exit()
                    
                    view = views[view_name]
                    
                    try:
                        if use_vg_method:
                            # Method VG/Graphics - checkbox akan unchecked
                            link_settings = RevitLinkGraphicsSettings()
                            link_settings.LinkVisibilityType = LinkVisibility.Hidden
                            
                            t = Transaction(doc, "Hide Link (VG)")
                            t.Start()
                            view.SetLinkOverrides(link_type_id, link_settings)
                            t.Commit()
                        else:
                            # Fallback: HideElements - checkbox tetap checked
                            # Get semua instance dari link type ini
                            link_instances = [
                                inst for inst in 
                                FilteredElementCollector(doc).OfClass(RevitLinkInstance)
                                if inst.GetTypeId() == link_type_id
                            ]
                            
                            if link_instances:
                                link_ids = List.List[ElementId]([inst.Id for inst in link_instances])
                                
                                t = Transaction(doc, "Hide")
                                t.Start()
                                view.HideElements(link_ids)
                                t.Commit()
                        
                        op_count += 1
                        pb.update_progress(op_count, total_ops)
                        
                    except Exception as e:
                        # Skip errors untuk view tertentu
                        pass
    
    except Exception as e:
        # Fallback: Use output-based progress
        use_ui_progress = False
        output.print_md("## Processing {} links x {} views...".format(total_links, total_views))
        
        op_count = 0
        for link_type_name in sel_link_types:
            link_type = link_types[link_type_name]
            link_type_id = link_type.Id
            
            for view_name in sel_views:
                view = views[view_name]
                current_count = op_count + 1
                output.update_progress(current_count, total_ops)
                
                try:
                    if use_vg_method:
                        link_settings = RevitLinkGraphicsSettings()
                        link_settings.LinkVisibilityType = LinkVisibility.Hidden
                        
                        t = Transaction(doc, "Hide Link (VG)")
                        t.Start()
                        view.SetLinkOverrides(link_type_id, link_settings)
                        t.Commit()
                    else:
                        link_instances = [
                            inst for inst in 
                            FilteredElementCollector(doc).OfClass(RevitLinkInstance)
                            if inst.GetTypeId() == link_type_id
                        ]
                        
                        if link_instances:
                            link_ids = List.List[ElementId]([inst.Id for inst in link_instances])
                            
                            t = Transaction(doc, "Hide")
                            t.Start()
                            view.HideElements(link_ids)
                            t.Commit()
                    
                    op_count += 1
                    
                except Exception:
                    pass
    
    tg.Assimilate()
    
    method_used = "VG/Graphics" if use_vg_method else "Hide Elements"
    forms.alert(
        "Selesai!\n\n"
        "{} link type disembunyikan di {} view.\n"
        "Method: {}"
        .format(total_links, total_views, method_used)
    )

except Exception as e:
    try:
        tg.RollBack()
    except:
        pass
    forms.alert("Error: {}".format(str(e)))
