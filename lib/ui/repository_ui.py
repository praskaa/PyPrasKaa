# -*- coding: utf-8 -*-
"""
Repository UI Classes

Specialized UI classes untuk repository-style dialogs dengan bulk operations.

Author: PrasKaa
"""

# ╦ ╦╔═╗╔╦╗╔═╗╔╦╗╔═╗
# ║║║║╣  ║ ║ ║ ║║╚═╗
# ╚╩╝╚═╝ ╩ ╚═╝═╩╝╚═╝ IMPORTS
# ====================================================================================================
from ui.base_window import BaseRepositoryUI
from ui.ui_items import FamilyItem, ViewTemplateItem, create_family_item, create_view_template_item
from pyrevit import revit, forms

# ╔═╗╔═╗╔═╗╔═╗╔═╗╔╗ ╔═╗═╗ ╦
# ║ ║║  ║ ║╠═╝║╣ ╠╩╗║ ║╔╩╦╝
# ╚═╝╚═╝╚═╝╩  ╚═╝╚═╝╚═╝╩ ╚═ FAMILY REPOSITORY UI
# ==================================================

class FamilyRepositoryUI(BaseRepositoryUI):
    """
    UI untuk Family Repository synchronization.

    Features:
    - Family loading dan filtering
    - Bulk sync operations
    - Category-based organization
    - Status tracking
    """

    def __init__(self, xaml_file, title="Family Repository", repository=None):
        """
        Initialize Family Repository UI.

        Args:
            xaml_file (str): Path ke XAML file
            title (str): Window title
            repository: FamilyRepository instance
        """
        BaseRepositoryUI.__init__(self, xaml_file, title, repository)

    def setup_repository_ui(self):
        """Setup family-specific UI elements."""
        # Load families on initialization
        self.load_items()

    def load_items(self):
        """Load families dari repository."""
        try:
            if not self.repository:
                print("Warning: No repository provided for FamilyRepositoryUI")
                return

            self.items = []

            # Get families dari repository
            families = self.repository.get_families()

            # Create FamilyItem untuk setiap family
            for family in families:
                item = create_family_item(family, revit.doc)
                self.items.append(item)

            # Sort by category then name
            self.items.sort(key=lambda x: (x.Category, x.Name))

            # Update filtered items
            self.filtered_items = self.items[:]
            self.update_list_view()

        except Exception as ex:
            print(f"Error loading families: {str(ex)}")
            forms.alert("Failed to load families. See log for details.")

    def update_list_view(self):
        """Update ListView dengan filtered families."""
        try:
            # Try different common ListView names
            list_views = ['UI_ListBox_Families', 'UI_ListBox', 'families_list']

            for lv_name in list_views:
                if hasattr(self, lv_name):
                    list_view = getattr(self, lv_name)
                    list_view.ItemsSource = self.filtered_items
                    break
        except Exception as ex:
            print(f"Error updating list view: {str(ex)}")

    def filter_items(self, search_text=""):
        """Filter families berdasarkan search text."""
        if not search_text:
            self.filtered_items = self.items[:]
        else:
            search_lower = search_text.lower()
            self.filtered_items = [
                item for item in self.items
                if search_lower in item.Name.lower() or
                   search_lower in item.Category.lower()
            ]

        self.update_list_view()

    def sync_selected_items(self):
        """Sync selected families ke current document."""
        try:
            selected_items = [item for item in self.filtered_items if item.IsSelected]

            if not selected_items:
                forms.alert("Please select at least one family to sync.")
                return False

            if not forms.alert(f"Do you want to sync {len(selected_items)} selected families?",
                             ok=False, yes=True, no=True):
                return False

            # Disable sync button during operation
            self._set_sync_button_state(False, "Syncing...")

            success_count = 0
            for item in selected_items:
                try:
                    success = self.repository.sync_family(item.Name, revit.doc)
                    if success:
                        item.Status = "Synced"
                        item.StatusColor = "#90EE90"  # Light green
                        success_count += 1
                    else:
                        item.Status = "Failed"
                        item.StatusColor = "#FF6B6B"  # Red
                except Exception as ex:
                    print(f"Error syncing family {item.Name}: {str(ex)}")
                    item.Status = "Error"
                    item.StatusColor = "#FF6B6B"

            # Re-enable sync button
            self._set_sync_button_state(True, "Sync Selected Families")

            # Update UI
            self.update_list_view()

            # Show results
            if success_count == len(selected_items):
                forms.alert(f"All {success_count} families synced successfully!")
            else:
                forms.alert(f"{success_count}/{len(selected_items)} families synced successfully. Check status for details.")

            return success_count > 0

        except Exception as ex:
            print(f"Error in sync operation: {str(ex)}")
            forms.alert("Failed to sync families. See log for details.")
            return False

    def _set_sync_button_state(self, enabled, text=None):
        """Set sync button state."""
        try:
            button_names = ['sync_button', 'UI_btn_sync', 'btn_sync']
            for btn_name in button_names:
                if hasattr(self, btn_name):
                    button = getattr(self, btn_name)
                    button.IsEnabled = enabled
                    if text:
                        button.Content = text
                    break
        except Exception as ex:
            print(f"Error setting button state: {str(ex)}")

# ╔═╗╦  ╦╔═╗╔╗╔╔╦╗  ╦ ╦╔═╗╔╦╗╔═╗╔╦╗╔═╗
# ║╣ ╚╗╔╝║╣ ║║║ ║   ║║║║╣  ║ ║ ║ ║║╚═╗
# ╚═╝ ╚╝ ╚═╝╝╚╝ ╩   ╚╩╝╚═╝ ╩ ╚═╝═╩╝╚═╝ VIEW TEMPLATE REPOSITORY UI
# ====================================================================================================

class ViewTemplateRepositoryUI(BaseRepositoryUI):
    """
    UI untuk View Template Repository synchronization.

    Features:
    - View template loading dan filtering
    - Bulk sync operations
    - Status tracking
    """

    def __init__(self, xaml_file, title="View Template Repository", repository=None):
        """
        Initialize View Template Repository UI.

        Args:
            xaml_file (str): Path ke XAML file
            title (str): Window title
            repository: ViewTemplateRepository instance
        """
        BaseRepositoryUI.__init__(self, xaml_file, title, repository)

    def setup_repository_ui(self):
        """Setup view template-specific UI elements."""
        # Load templates on initialization
        self.load_items()

    def load_items(self):
        """Load view templates dari repository."""
        try:
            if not self.repository:
                print("Warning: No repository provided for ViewTemplateRepositoryUI")
                return

            self.items = []

            # Get view templates dari repository
            templates = self.repository.get_templates()

            # Create ViewTemplateItem untuk setiap template
            for template in templates:
                item = create_view_template_item(template, revit.doc)
                self.items.append(item)

            # Sort by name
            self.items.sort(key=lambda x: x.Name)

            # Update filtered items
            self.filtered_items = self.items[:]
            self.update_list_view()

        except Exception as ex:
            print(f"Error loading view templates: {str(ex)}")
            forms.alert("Failed to load view templates. See log for details.")

    def update_list_view(self):
        """Update ListView dengan filtered templates."""
        try:
            # Try different common ListView names
            list_views = ['UI_ListBox_ViewTemplates', 'UI_ListBox', 'templates_list']

            for lv_name in list_views:
                if hasattr(self, lv_name):
                    list_view = getattr(self, lv_name)
                    list_view.ItemsSource = self.filtered_items
                    break
        except Exception as ex:
            print(f"Error updating list view: {str(ex)}")

    def filter_items(self, search_text=""):
        """Filter templates berdasarkan search text."""
        if not search_text:
            self.filtered_items = self.items[:]
        else:
            search_lower = search_text.lower()
            self.filtered_items = [
                item for item in self.items
                if search_lower in item.Name.lower()
            ]

        self.update_list_view()

    def sync_selected_items(self):
        """Sync selected view templates ke current document."""
        try:
            selected_items = [item for item in self.filtered_items if item.IsSelected]

            if not selected_items:
                forms.alert("Please select at least one template to sync.")
                return False

            if not forms.alert(f"Do you want to sync {len(selected_items)} selected templates?",
                             ok=False, yes=True, no=True):
                return False

            # Disable sync button during operation
            self._set_sync_button_state(False, "Syncing...")

            success_count = 0
            for item in selected_items:
                try:
                    success = self.repository.sync_template(item.Name, revit.doc)
                    if success:
                        item.Status = "Synced"
                        item.StatusColor = "#90EE90"  # Light green
                        success_count += 1
                    else:
                        item.Status = "Failed"
                        item.StatusColor = "#FF6B6B"  # Red
                except Exception as ex:
                    print(f"Error syncing template {item.Name}: {str(ex)}")
                    item.Status = "Error"
                    item.StatusColor = "#FF6B6B"

            # Re-enable sync button
            self._set_sync_button_state(True, "Sync Selected Templates")

            # Update UI
            self.update_list_view()

            # Show results
            if success_count == len(selected_items):
                forms.alert(f"All {success_count} templates synced successfully!")
            else:
                forms.alert(f"{success_count}/{len(selected_items)} templates synced successfully. Check status for details.")

            return success_count > 0

        except Exception as ex:
            print(f"Error in sync operation: {str(ex)}")
            forms.alert("Failed to sync templates. See log for details.")
            return False

    def _set_sync_button_state(self, enabled, text=None):
        """Set sync button state."""
        try:
            button_names = ['sync_button', 'UI_btn_sync', 'btn_sync']
            for btn_name in button_names:
                if hasattr(self, btn_name):
                    button = getattr(self, btn_name)
                    button.IsEnabled = enabled
                    if text:
                        button.Content = text
                    break
        except Exception as ex:
            print(f"Error setting button state: {str(ex)}")

# ╔═╗╦═╗╔═╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ╠═╝╠╦╝║ ║╠═╝║╣ ╠╦╝ ║ ╚═╗
# ╩  ╩╚═╚═╝╩  ╚═╝╩╚═ ╩ ╚═╝ UTILITY FUNCTIONS
# ==================================================

def create_family_repository_ui(xaml_file="RepositorySyncUI.xaml", title="Family Repository"):
    """
    Factory function untuk membuat Family Repository UI.

    Args:
        xaml_file (str): Path ke XAML file
        title (str): Window title

    Returns:
        FamilyRepositoryUI: Configured UI instance
    """
    # Import here to avoid circular imports
    from family_repository import FamilyRepository

    # Create repository instance
    template_doc = get_template_document()
    if not template_doc:
        forms.alert("Template project not found. Please open your template project.", exitscript=True)
        return None

    repository = FamilyRepository(template_doc)
    return FamilyRepositoryUI(xaml_file, title, repository)

def create_view_template_repository_ui(xaml_file="RepositorySyncUI.xaml", title="View Template Repository"):
    """
    Factory function untuk membuat View Template Repository UI.

    Args:
        xaml_file (str): Path ke XAML file
        title (str): Window title

    Returns:
        ViewTemplateRepositoryUI: Configured UI instance
    """
    # Import here to avoid circular imports
    from view_template_repository import ViewTemplateRepository

    # Create repository instance
    template_doc = get_template_document()
    if not template_doc:
        forms.alert("Template project not found. Please open your template project.", exitscript=True)
        return None

    repository = ViewTemplateRepository(template_doc)
    return ViewTemplateRepositoryUI(xaml_file, title, repository)

def get_template_document():
    """
    Get template document dari open documents atau config.

    Returns:
        Document: Template document atau None
    """
    try:
        # Try to get from config first
        from config import TEMPLATE_PATTERNS, TEMPLATE_PROJECT_PATHS
        app = revit.doc.Application

        # Check configured paths
        for path in TEMPLATE_PROJECT_PATHS:
            if os.path.exists(path):
                try:
                    template_doc = app.OpenDocumentFile(path)
                    if template_doc:
                        return template_doc
                except:
                    continue

        # Check open documents
        for opened_doc in app.Documents:
            if not opened_doc.IsFamilyDocument and not opened_doc.IsLinked:
                doc_name = opened_doc.Title.upper()
                if any(pattern in doc_name for pattern in TEMPLATE_PATTERNS):
                    return opened_doc

        return None

    except:
        # Fallback to simple pattern matching
        app = revit.doc.Application
        for opened_doc in app.Documents:
            if not opened_doc.IsFamilyDocument and not opened_doc.IsLinked:
                doc_name = opened_doc.Title.upper()
                if any(pattern in doc_name for pattern in ["TEMPLATE", "STD", "STANDARD"]):
                    return opened_doc

        return None
