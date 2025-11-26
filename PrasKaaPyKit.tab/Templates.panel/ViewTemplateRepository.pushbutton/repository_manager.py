# -*- coding: utf-8 -*-
"""ViewTemplate Repository Manager.
Handles interactions with the template repository project.
"""

import os
import clr
from collections import defaultdict

# Add references
clr.AddReference("System.Windows.Forms")
clr.AddReference("System")
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import *
from System.Collections.Generic import List

class ViewTemplateRepository(object):
    """Manages synchronization of View Templates using a template project as repository."""

    def __init__(self, template_doc=None):
        """Initialize repository manager.
        
        Args:
            template_doc: The template document to use as repository. If None, tries to find template project.
        """
        self.doc_template = template_doc
        if not self.doc_template:
            raise Exception("Template project not provided.")
    
    def get_template_list(self):
        """Get list of view templates from template project."""
        try:
            templates = FilteredElementCollector(self.doc_template).OfClass(View).ToElements()
            templates_dict = {}
            
            for v in templates:
                if v.IsTemplate:
                    view_family = "Unknown"
                    try:
                        view_family = str(v.ViewType) if hasattr(v, 'ViewType') else "Unknown"
                    except:
                        pass
                        
                    templates_dict[v.Name] = {
                        'Id': v.Id,
                        'ViewType': str(v.ViewType),
                        'ViewFamily': view_family,
                        'ModifiedBy': self.doc_template.Application.Username,
                    }
            return templates_dict
        except Exception as ex:
            print("Error getting template list: {}".format(str(ex)))
            return {}
    
    def sync_template(self, template_name, target_doc):
        """Copy a template from repository to target document.
        
        Args:
            template_name: Name of the template to sync
            target_doc: Target document to sync to
            
        Returns:
            bool: True if sync was successful
        """
        try:
            # Find template in repository
            repo_templates = FilteredElementCollector(self.doc_template).OfClass(View).ToElements()
            source_template = next((t for t in repo_templates if t.IsTemplate and t.Name == template_name), None)
            
            if not source_template:
                print("Template {} not found in repository".format(template_name))
                return False
                
            # Check if template exists in target
            target_templates = FilteredElementCollector(target_doc).OfClass(View).ToElements()
            existing_template = next((t for t in target_templates if t.IsTemplate and t.Name == template_name), None)
            
            with Transaction(target_doc, "Import View Template") as t:
                t.Start()
                
                # Delete existing if found
                if existing_template:
                    # Store views using this template
                    views_using_template = []
                    for view in FilteredElementCollector(target_doc).OfClass(View).ToElements():
                        if not view.IsTemplate and view.ViewTemplateId == existing_template.Id:
                            views_using_template.append(view)
                    
                    target_doc.Delete(existing_template.Id)
                
                # Create List of IDs and perform copy (exactly matching working script)
                selected_viewtemplates_ids = [source_template.Id]
                List_selected_viewtemplates = List[ElementId](selected_viewtemplates_ids)
                copy_opts = CopyPasteOptions()
                new_ids = ElementTransformUtils.CopyElements(
                    self.doc_template,
                    List_selected_viewtemplates,
                    target_doc,
                    Transform.Identity,
                    copy_opts)
                
                # Reassign template to views if needed
                if existing_template and views_using_template and len(new_ids) > 0:
                    new_template = target_doc.GetElement(new_ids[0])
                    for view in views_using_template:
                        view.ViewTemplateId = new_template.Id
                
                t.Commit()
            
            return True
            
        except Exception as ex:
            print("Error importing template {}: {}".format(template_name, str(ex)))
            return False
    
    def update_template_status(self, template_items):
        """Update status of template items by comparing with repository.
        
        Args:
            template_items: List of ViewTemplateItem objects to update
        """
        try:
            # Get repository templates
            repo_templates = self.get_template_list()
            
            # Update status for each template
            for item in template_items:
                if item.Name in repo_templates:
                    repo_data = repo_templates[item.Name]
                    item.IsInRepository = True
                    
                    # Compare with repository version
                    if repo_data['ModifiedBy'] != item.ModifiedBy:
                        item.Status = "Modified"
                        item.StatusColor = "#FFD700"  # Gold
                        item.HasLocalChanges = True
                    else:
                        item.Status = "Synced"
                        item.StatusColor = "#90EE90"  # Light green
                        item.HasLocalChanges = False
                else:
                    item.Status = "New"
                    item.StatusColor = "#D7EDFF"  # Light blue
                    item.HasLocalChanges = True
                    item.IsInRepository = False
                
        except Exception as ex:
            print("Error updating template status: {}".format(str(ex)))
