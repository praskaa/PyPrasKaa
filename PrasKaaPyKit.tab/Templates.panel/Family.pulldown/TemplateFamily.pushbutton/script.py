# -*- coding: utf-8 -*-
"""Family Repository Sync Tool
Synchronize families with a template project.
"""

__title__ = "Family Repository"
__author__ = "PrasKaa Team"
__doc__ = """Synchronize families with template project.

Key features:
- Central storage in template project
- Smart sync with overwrite protection
- Filter by family category
- Multi-family type support

Author: PrasKaa
"""

import os
import sys
import clr
import traceback
from collections import defaultdict

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

# Import configuration
from config import TEMPLATE_PATTERNS, TEMPLATE_PROJECT_PATHS, COLORS, STATUS

# Initialize script
output = script.get_output()
logger = script.get_logger()
my_config = script.get_config()

# Get Revit app and doc
doc = revit.doc
uidoc = revit.uidoc
app = revit.doc.Application

class FamilyItem(object):
    """Represents a family in the sync UI."""
    
    def __init__(self, name, category, status="New", status_color="#D7EDFF", is_selected=True):
        self._name = name
        self._category = category
        self._status = status
        self._status_color = status_color
        self._is_selected = is_selected
        self._last_modified = None
        self._modified_by = None
        self._has_local_changes = False
        self._is_in_repository = False
        self._types = []
    
    @property
    def Name(self):
        return self._name
    
    @property
    def Category(self):
        return self._category
    
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
    def Types(self):
        return self._types
    
    @Types.setter
    def Types(self, value):
        self._types = value

class FamilyRepository(object):
    """Manages family synchronization with template project."""
    
    def __init__(self, template_doc):
        self.doc_template = template_doc
        
    def get_families(self):
        """Get all families from template document."""
        collector = FilteredElementCollector(self.doc_template)
        families = collector.OfClass(Family).ToElements()
        return [f for f in families if not f.IsInPlace]  # Filter out in-place families
    
    def sync_family(self, family_name, target_doc):
        """Sync a family from template to target document."""
        try:
            # Find family in template
            family = self._find_family_by_name(family_name)
            if not family:
                logger.error("Family not found in template: {}".format(family_name))
                return False
                
            # Get family document
            family_doc = self.doc_template.EditFamily(family)
            if not family_doc:
                logger.error("Could not open family: {}".format(family_name))
                return False
                
            # Load family into target document
            try:
                loaded_family = family_doc.LoadFamily(target_doc)
                family_doc.Close(False)  # Close without saving
                return loaded_family
            except Exception as ex:
                logger.error("Error loading family {}: {}".format(family_name, str(ex)))
                if family_doc:
                    family_doc.Close(False)
                return False
            
        except Exception as ex:
            logger.error("Error syncing family {}: {}".format(family_name, str(ex)))
            return False

    def _find_family_by_name(self, family_name):
        """Find a family by name in template document."""
        collector = FilteredElementCollector(self.doc_template)
        families = collector.OfClass(Family).ToElements()
        for family in families:
            if family.Name == family_name:
                return family
        return None

class RepositorySyncUI(WPFWindow):
    """UI for family repository synchronization."""
    
    def __init__(self):
        """Initialize the repository sync UI."""
        # Find template project
        template_doc = self._get_template_project()
        if not template_doc:
            forms.alert("Template project not found. Please open your template project.", exitscript=True)
            
        self.repository = FamilyRepository(template_doc)
        self.family_items = []
        self.filtered_items = []
        
        # Load XAML window
        xaml_file = os.path.join(os.path.dirname(__file__), 'RepositorySyncUI.xaml')
        WPFWindow.__init__(self, xaml_file)
        
        # Setup UI
        self.setup_ui()
        self.load_families()
    
    def _get_template_project(self):
        """Find the template project among open documents or load from path."""
        try:
            from config import TEMPLATE_PATTERNS, TEMPLATE_PROJECT_PATHS
            logger.info("Successfully imported config")
        except ImportError as e:
            logger.error("Could not import config.py: {}".format(str(e)))
            TEMPLATE_PATTERNS = ["TEMPLATE", "STD", "STANDARD", "_TPL", "_TEMPLATE"]
            TEMPLATE_PROJECT_PATHS = []
        
        # First try to open from configured paths
        for path in TEMPLATE_PROJECT_PATHS:
            if os.path.exists(path):
                try:
                    template_doc = app.OpenDocumentFile(path)
                    if template_doc:
                        logger.info("Opened template project from path: {}".format(path))
                        return template_doc
                except Exception as ex:
                    logger.error("Failed to open template from {}: {}".format(path, str(ex)))
                    continue
        
        # If not found in paths, check open documents
        for opened_doc in app.Documents:
            if not opened_doc.IsFamilyDocument and not opened_doc.IsLinked:
                doc_name = opened_doc.Title.upper()
                if any(pattern in doc_name for pattern in TEMPLATE_PATTERNS):
                    logger.info("Found template project in open documents: {}".format(opened_doc.Title))
                    return opened_doc
        
        # If not found, ask user to select from open documents or browse
        options = ['Select from Open Documents', 'Browse for Template File']
        selected_option = forms.CommandSwitchWindow.show(
            options,
            message='Template project not found automatically.\nHow would you like to select the template?'
        )
        
        if selected_option == 'Select from Open Documents':
            project_list = [d for d in app.Documents if not d.IsFamilyDocument and not d.IsLinked]
            if project_list:
                selected_doc = forms.SelectFromList.show(
                    [d.Title for d in project_list],
                    title='Select Template Project',
                    message='Please select your template project:',
                    multiselect=False
                )
                if selected_doc:
                    return next(d for d in project_list if d.Title == selected_doc)
        else:
            template_path = forms.pick_file(
                file_ext='rte',
                init_dir=r'I:\1_STUDI\Revit_Template',
                title='Select Template File'
            )
            if template_path:
                try:
                    template_doc = app.OpenDocumentFile(template_path)
                    if template_doc:
                        logger.info("Opened template project from selected path: {}".format(template_path))
                        return template_doc
                except Exception as ex:
                    logger.error("Failed to open selected template: {}".format(str(ex)))
        
        return None
    
    def header_drag(self, sender, args):
        """Handle window dragging from the header."""
        self.DragMove()
    
    def button_close(self, sender, args):
        """Handle close button click."""
        self.Close()
    
    def UIe_btn_select_all(self, sender, args):
        """Handle select all button click."""
        for item in self.family_items:
            item.IsSelected = True
        self.UI_ListBox_Families.Items.Refresh()
    
    def UIe_btn_select_none(self, sender, args):
        """Handle select none button click."""
        for item in self.family_items:
            item.IsSelected = False
        self.UI_ListBox_Families.Items.Refresh()
    
    def UIe_text_filter_updated(self, sender, args):
        """Handle filter text changes."""
        search_text = self.UI_TextBox_Filter.Text.lower()
        if not search_text:
            self.UI_ListBox_Families.ItemsSource = self.family_items
        else:
            filtered = [f for f in self.family_items 
                       if search_text in f.Name.lower() or 
                          search_text in f.Category.lower()]
            self.UI_ListBox_Families.ItemsSource = filtered
        self.filtered_items = self.UI_ListBox_Families.ItemsSource

    def UIe_btn_sync(self, sender, args):
        """Handle sync button click."""
        try:
            selected_items = [item for item in self.filtered_items if item.IsSelected]
            if not selected_items:
                forms.alert("Please select at least one family to sync.")
                return

            if not forms.alert("Do you want to sync {} selected families?".format(len(selected_items)), 
                             ok=False, yes=True, no=True):
                return            
            
            sync_button = self.FindName("sync_button")
            sync_button.IsEnabled = False
            sync_button.Content = "Syncing..."
            
            logger.info("Starting family sync...")
            operation_success = True
            
            for item in selected_items:
                try:
                    logger.info("Syncing family: {}".format(item.Name))
                    success = self.repository.sync_family(item.Name, doc)
                    if success:
                        logger.info("Successfully synced: {}".format(item.Name))
                        item.Status = STATUS['SYNCED']
                        item.StatusColor = COLORS['SYNCED']
                    else:
                        logger.error("Failed to sync: {}".format(item.Name))
                        operation_success = False
                except Exception as e:
                    logger.error("Error syncing {}: {}".format(item.Name, str(e)))
                    operation_success = False
            
            sync_button.IsEnabled = True
            sync_button.Content = "Sync Selected Families"
            
            if operation_success:
                forms.alert("Families synced successfully!")
            else:
                forms.alert("Some families failed to sync. Check the output window for details.")
            
            self.UI_ListBox_Families.Items.Refresh()
            
        except Exception as ex:
            logger.error("Error in sync operation: {}".format(str(ex)))
            logger.error(traceback.format_exc())
            forms.alert("Failed to sync families. See output window for details.")

    def UIe_btn_publish(self, sender, args):
        """Handle publish button click."""
        forms.alert("Publishing to repository feature will be available in a future update.")

    def UIe_checkbox_clicked(self, sender, args):
        """Handle checkbox click with multi-selection support."""
        checkbox = sender
        is_checked = checkbox.IsChecked
        
        selected_items = self.UI_ListBox_Families.SelectedItems
        if len(selected_items) > 1:
            for item in selected_items:
                item.IsSelected = is_checked
            self.UI_ListBox_Families.Items.Refresh()

    def setup_ui(self):
        """Setup the UI components."""
        try:
            self.Title = __title__ if '__title__' in globals() else "Family Repository"
            
            if hasattr(self, 'main_title'):
                self.main_title.Text = "Family Repository by {}".format(__author__)
            
            if hasattr(self, 'repository') and hasattr(self, 'repository_path'):
                template_location = self.repository.doc_template.PathName
                self.repository_path.Text = "Location: {}".format(template_location)
            
            if hasattr(self, 'footer_version'):
                username = doc.Application.Username
                self.footer_version.Text = "Version: 1.0 | User: {}".format(username)

        except Exception as ex:
            logger.error("Error in setup_ui: {}".format(str(ex)))
            logger.error(traceback.format_exc())
    
    def load_families(self):
        """Load families from template repository project."""
        try:
            self.family_items = []
            
            # Get families from template
            template_families = self.repository.get_families()
            
            # Get current document families for comparison
            current_families = FilteredElementCollector(doc).OfClass(Family).ToElements()
            current_family_names = {f.Name for f in current_families}
            
            # Create items for each template family
            for family in template_families:
                status = STATUS['NEW']
                status_color = COLORS['NEW']
                
                # Check if family exists in current document
                if family.Name in current_family_names:
                    status = STATUS['EXISTS']
                    status_color = COLORS['EXISTS']
                
                item = FamilyItem(
                    name=family.Name,
                    category=family.FamilyCategory.Name if family.FamilyCategory else "Uncategorized",
                    status=status,
                    status_color=status_color,
                    is_selected=(status == STATUS['NEW'])  # Auto-select only new families
                )
                
                try:
                    # Get family types
                    symbols = family.Symbols
                    item.Types = [symbol.Name for symbol in symbols]
                except:
                    item.Types = []
                
                self.family_items.append(item)
            
            # Sort by category then name
            self.family_items.sort(key=lambda x: (x.Category, x.Name))
            
            # Update UI
            self.UI_ListBox_Families.ItemsSource = self.family_items
            self.filtered_items = self.family_items
            
        except Exception as ex:
            logger.error("Failed to load families: {}".format(ex))
            logger.error(traceback.format_exc())
            forms.alert("Failed to load families. See log for details.")

def main():
    """Main script execution."""
    try:
        dialog = RepositorySyncUI()
        dialog.ShowDialog()
    except Exception as ex:
        logger.error("Error running Family Repository: {}".format(ex))
        logger.error(traceback.format_exc())
        forms.alert("Failed to start Family Repository. See log for details.", exitscript=True)

if __name__ == '__main__':
    main()