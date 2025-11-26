# -*- coding: utf-8 -*-
"""View Template Repository Sync Tool
Synchronize view templates with a template project.
"""

__title__ = "View Template\nRepository"
__author__ = "PrasKaa"
__doc__ = """Synchronize view templates with template project.

Key features:
- Central storage in template project
- Smart sync with overwrite protection
- Filter and category preservation

Author: PrasKaa
"""

import os
import sys
import clr
import traceback
from collections import defaultdict

# Add parent directory to Python path for config import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Add references
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('PresentationFramework')
clr.AddReference('PresentationCore')
clr.AddReference('WindowsBase')
from Autodesk.Revit.DB import *

# Import pyRevit modules
from pyrevit import script
from pyrevit import forms
from pyrevit import revit
from pyrevit.forms import WPFWindow

# Import custom modules
from repository_manager import ViewTemplateRepository

# Initialize script
output = script.get_output()
logger = script.get_logger()
my_config = script.get_config()

# Get Revit app and doc
doc = revit.doc
uidoc = revit.uidoc
app = revit.doc.Application

class ViewTemplateItem(object):
    """Represents a view template in the sync UI."""
    
    def __init__(self, name, status="New", status_color="#D7EDFF", is_selected=True):
        self._name = name
        self._status = status
        self._status_color = status_color
        self._is_selected = is_selected
        self._last_modified = None
        self._modified_by = None
        self._has_local_changes = False
        self._is_in_repository = False
    
    @property
    def Name(self):
        return self._name
    
    @property
    def Status(self):
        return self._status
    
    @Status.setter
    def Status(self, value):
        self._status = value
    
    @property
    def StatusColor(self):
        return self._status_color
    
    @StatusColor.setter
    def StatusColor(self, value):
        self._status_color = value
    
    @property
    def IsSelected(self):
        return self._is_selected
    
    @IsSelected.setter
    def IsSelected(self, value):
        self._is_selected = value
    
    @property
    def ModifiedBy(self):
        return self._modified_by
    
    @ModifiedBy.setter
    def ModifiedBy(self, value):
        self._modified_by = value

class RepositorySyncUI(WPFWindow):
    """UI for repository synchronization."""
    
    def __init__(self):
        """Initialize the repository sync UI."""
        # Find template project
        template_doc = self._get_template_project()
        if not template_doc:
            forms.alert("Template project not found. Please open your template project.", exitscript=True)
            
        self.repository = ViewTemplateRepository(template_doc)
        self.template_items = []
        self.filtered_items = []
        
        # Load XAML window
        xaml_file = os.path.join(os.path.dirname(__file__), 'RepositorySyncUI.xaml')
        WPFWindow.__init__(self, xaml_file)
        
        # Setup UI
        self.setup_ui()
        self.load_templates()
    
    def _get_template_project(self):
        """Find the template project among open documents or load from path."""
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from config import TEMPLATE_PATTERNS, TEMPLATE_PROJECT_PATHS
            logger.info("Successfully imported config")
        except ImportError as e:
            logger.error("Could not import config.py: {}".format(str(e)))
            TEMPLATE_PATTERNS = ["TEMPLATE", "STD", "STANDARD", "_TPL", "_TEMPLATE"]
            TEMPLATE_PROJECT_PATHS = []
        
        # First check open documents
        for opened_doc in app.Documents:
            if not opened_doc.IsFamilyDocument and not opened_doc.IsLinked:
                doc_name = opened_doc.Title.upper()
                if any(pattern in doc_name for pattern in TEMPLATE_PATTERNS):
                    logger.info("Found template project in open documents: {}".format(opened_doc.Title))
                    return opened_doc
        
        # Try to open from configured paths
        for path in TEMPLATE_PROJECT_PATHS:
            if os.path.exists(path):
                try:
                    # Try to open the template project
                    template_doc = app.OpenDocumentFile(path)
                    if template_doc:
                        logger.info("Opened template project from path: {}".format(path))
                        return template_doc
                except Exception as ex:
                    logger.error("Failed to open template from {}: {}".format(path, str(ex)))
                    continue
        
        # If not found, ask user to select from open documents
        project_list = [d for d in app.Documents if not d.IsFamilyDocument and not d.IsLinked]
        if project_list:
            selected_doc = forms.SelectFromList.show(
                [d.Title for d in project_list],
                title='Select Template Project',
                message='Template project not found automatically.\nPlease select your template project:',
                multiselect=False
            )
            if selected_doc:
                return next(d for d in project_list if d.Title == selected_doc)
        
        return None
    
    def header_drag(self, sender, args):
        """Handle window dragging from the header."""
        try:
            self.DragMove()
        except Exception as ex:
            logger.error("Error in header drag: {}".format(str(ex)))
    
    def button_close(self, sender, args):
        """Handle close button click."""
        try:
            self.Close()
        except Exception as ex:
            logger.error("Error in close button: {}".format(str(ex)))
    
    def UIe_btn_select_all(self, sender, args):
        """Handle select all button click."""
        try:
            for item in self.template_items:
                item.IsSelected = True
            self.UI_ListBox_ViewTemplates.Items.Refresh()
        except Exception as ex:
            logger.error("Error in select all: {}".format(str(ex)))
    
    def UIe_btn_select_none(self, sender, args):
        """Handle select none button click."""
        try:
            for item in self.template_items:
                item.IsSelected = False
            self.UI_ListBox_ViewTemplates.Items.Refresh()
        except Exception as ex:
            logger.error("Error in select none: {}".format(str(ex)))
    
    def UIe_text_filter_updated(self, sender, args):
        """Handle filter text changes."""
        try:
            search_text = self.UI_TextBox_Filter.Text.lower()
            if not search_text:
                self.UI_ListBox_ViewTemplates.ItemsSource = self.template_items
            else:
                filtered = [t for t in self.template_items 
                          if search_text in t.Name.lower()]
                self.UI_ListBox_ViewTemplates.ItemsSource = filtered
            self.filtered_items = self.UI_ListBox_ViewTemplates.ItemsSource
        except Exception as ex:
            logger.error("Error in filter update: {}".format(str(ex)))

    def UIe_btn_sync(self, sender, args):
        """Handle sync button click."""
        try:
            # Get selected items from current filter view
            selected_items = [item for item in self.filtered_items if item.IsSelected]
            if not selected_items:
                forms.alert("Please select at least one template to sync.")
                return

            # Confirm sync operation
            if not forms.alert("Do you want to sync {} selected templates?".format(len(selected_items)), 
                             ok=False, yes=True, no=True):
                return            
            
            # Disable sync button during operation
            sync_button = self.FindName("sync_button")
            sync_button.IsEnabled = False
            sync_button.Content = "Syncing..."
            
            # Start sync
            logger.info("Starting template sync...")
            operation_success = True
            
            for item in selected_items:
                try:
                    logger.info("Syncing template: {}".format(item.Name))
                    success = self.repository.sync_template(item.Name, doc)
                    if success:
                        logger.info("Successfully synced: {}".format(item.Name))
                    else:
                        logger.error("Failed to sync: {}".format(item.Name))
                        operation_success = False
                except Exception as e:
                    logger.error("Error syncing {}: {}".format(item.Name, str(e)))
                    operation_success = False
            
            # Re-enable sync button
            sync_button.IsEnabled = True
            sync_button.Content = "Sync Selected Templates"
            
            # Show results and refresh list
            if operation_success:
                forms.alert("Templates synced successfully!")
            else:
                forms.alert("Some templates failed to sync. Check the output window for details.")
            
            self.load_templates()  # Refresh the list
            
        except Exception as ex:
            logger.error("Error in sync operation: {}".format(str(ex)))
            logger.error(traceback.format_exc())
            forms.alert("Failed to sync templates. See output window for details.")

    def UIe_btn_publish(self, sender, args):
        """Handle publish button click."""
        # This is a placeholder for future functionality
        forms.alert("Publishing to repository feature will be available in a future update.")

    def UIe_checkbox_clicked(self, sender, args):
        """Handle checkbox click with multi-selection support."""
        try:
            # Get the checkbox that was clicked
            checkbox = sender
            is_checked = checkbox.IsChecked
            
            # Get all selected items in the ListView
            selected_items = self.UI_ListBox_ViewTemplates.SelectedItems
            if len(selected_items) > 1:
                # Apply the same checked state to all selected items
                for item in selected_items:
                    item.IsSelected = is_checked
                self.UI_ListBox_ViewTemplates.Items.Refresh()
        except Exception as ex:
            logger.error("Error in checkbox click: {}".format(str(ex)))

    def setup_ui(self):
        """Setup the UI components."""
        try:
            # Set window title
            self.Title = __title__ if '__title__' in globals() else "View Template Repository"
              # Set main title in header
            if hasattr(self, 'main_title'):
                self.main_title.Text = "View Templates Repository by {}".format(__author__)
            
            # Set repository location
            if hasattr(self, 'repository') and hasattr(self, 'repository_path'):
                template_location = self.repository.doc_template.PathName
                self.repository_path.Text = "Location: {}".format(template_location)
              # Set footer version and user info
            if hasattr(self, 'footer_version'):
                username = doc.Application.Username
                self.footer_version.Text = "Version: 1.0 | User: {}".format(username)

        except Exception as ex:
            logger.error("Error in setup_ui: {}".format(str(ex)))
            logger.error(traceback.format_exc())
    
    def load_templates(self):
        """Load view templates from template repository project."""
        try:
            # Clear existing items
            self.template_items = []
            
            # Get view templates from template project
            collector = FilteredElementCollector(self.repository.doc_template)
            view_templates = collector.OfClass(View).ToElements()
            templates = [v for v in view_templates if v.IsTemplate]
            
            # Get view templates from current document for status comparison
            current_templates = FilteredElementCollector(doc).OfClass(View).ToElements()
            current_template_names = {v.Name for v in current_templates if v.IsTemplate}
            
            # Create template items
            for template in templates:
                status = "New"
                status_color = "#D7EDFF"  # Light blue
                
                # Check if template exists in current project
                if template.Name in current_template_names:
                    status = "Available"
                    status_color = "#90EE90"  # Light green
                
                item = ViewTemplateItem(
                    name=template.Name,
                    status=status,
                    status_color=status_color,
                    is_selected=False
                )
                self.template_items.append(item)
            
            # Sort templates by name
            self.template_items.sort(key=lambda x: x.Name)
            
            # Update UI
            self.UI_ListBox_ViewTemplates.ItemsSource = self.template_items
            self.filtered_items = self.template_items
            
        except Exception as ex:
            logger.error("Failed to load templates: {}".format(ex))
            logger.error(traceback.format_exc())
            forms.alert("Failed to load templates. See log for details.")

def main():
    """Main script execution."""
    try:
        dialog = RepositorySyncUI()
        dialog.ShowDialog()
    except Exception as ex:
        logger.error("Error running View Template Repository: {}".format(ex))
        logger.error(traceback.format_exc())
        forms.alert("Failed to start View Template Repository. See log for details.", exitscript=True)

if __name__ == '__main__':
    main()
