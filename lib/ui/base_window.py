# -*- coding: utf-8 -*-
"""
Base Window Classes

Base classes untuk semua dialog windows dengan common functionality.

Author: PrasKaa
"""

import os
import sys
from pyrevit import forms
from pyrevit import revit

# ╦ ╦╔═╗╔╦╗╔═╗╔╦╗╔═╗
# ║║║║╣  ║ ║ ║ ║║╚═╗
# ╚╩╝╚═╝ ╩ ╚═╝═╩╝╚═╝ IMPORTS
# ====================================================================================================
from ui.ui_styles import DARK_BLUE_THEME, WINDOW_SIZES, get_common_resources

# ╔╗ ╦  ╔═╗╔═╗╦╔═  ╔═╗╦ ╦╔═╗╔═╗╔╦╗
# ╠╩╗║  ║ ║║ ║╠╩╗  ╚═╗╠═╣║╣ ║╣  ║
# ╚═╝╩═╝╚═╝╚═╝╩ ╩  ╚═╝╩ ╩╚═╝╚═╝ ╩  BASE WINDOW CLASS
# ====================================================================================================

class BaseRevitWindow(forms.WPFWindow):
    """
    Base class untuk semua pyRevit dialog windows.

    Menyediakan common functionality seperti:
    - Window setup otomatis
    - Common event handlers
    - Theme consistency
    - UI element management
    """

    def __init__(self, xaml_file, title="", width=None, height=None):
        """
        Initialize base window.

        Args:
            xaml_file (str): Path ke XAML file
            title (str): Window title
            width (int, optional): Window width. Defaults to 600.
            height (int, optional): Window height. Defaults to 700.
        """
        # Set default window properties
        self._xaml_file = xaml_file
        self._title = title
        self._width = width or WINDOW_SIZES['default'][0]
        self._height = height or WINDOW_SIZES['default'][1]

        # Initialize WPF window
        xaml_path = self._get_xaml_path(xaml_file)
        forms.WPFWindow.__init__(self, xaml_path)

        # Setup window properties
        self._setup_window_properties()

        # Setup common UI elements
        self.setup_common_ui()

    def _get_xaml_path(self, xaml_file):
        """Get full path ke XAML file."""
        if os.path.isabs(xaml_file):
            return xaml_file

        # If just a filename (like "Script.xaml"), look in the calling script's directory
        # Go up the call stack to find the actual script (not UI module)
        frame = sys._getframe(1)
        while frame:
            frame_file = frame.f_code.co_filename
            # If we're not in the lib/ui directory, this is likely the script
            if 'lib' not in frame_file.replace('\\', '/').replace('/', os.sep):
                script_dir = os.path.dirname(os.path.abspath(frame_file))
                return os.path.join(script_dir, xaml_file)
            frame = frame.f_back

        # Fallback to current frame if no script found
        script_dir = os.path.dirname(os.path.abspath(sys._getframe(1).f_code.co_filename))
        return os.path.join(script_dir, xaml_file)

    def _setup_window_properties(self):
        """Setup basic window properties."""
        from System.Windows import WindowStartupLocation, ResizeMode, WindowStyle

        self.Title = self._title
        self.Width = self._width
        self.Height = self._height
        self.WindowStartupLocation = WindowStartupLocation.CenterScreen
        self.ShowInTaskbar = False
        self.ResizeMode = ResizeMode.NoResize
        # WindowStyle.None is not available in WPF, use single border instead
        # self.WindowStyle = WindowStyle.None
        pass

        # Set background color
        if hasattr(self, 'Background'):
            from System.Windows.Media import SolidColorBrush, ColorConverter
            color = ColorConverter.ConvertFromString(DARK_BLUE_THEME['background_dark'])
            self.Background = SolidColorBrush(color)

    def setup_common_ui(self):
        """Setup common UI elements seperti title dan footer."""
        try:
            # Set window title in header
            if hasattr(self, 'main_title'):
                self.main_title.Text = self._title

            # Set footer version dan user info
            if hasattr(self, 'footer_version'):
                username = revit.doc.Application.Username
                self.footer_version.Text = "Version: 1.0 | User: {}".format(username)

            # Set repository path jika ada
            if hasattr(self, 'repository_path'):
                # This will be overridden by subclasses
                pass

        except Exception as ex:
            # Log error but don't crash
            print("Warning in setup_common_ui: {}".format(str(ex)))

    # ╔═╗╦  ╦╔═╗╔╗╔╔╦╗  ╦ ╦╔═╗╔╗╔╔╦╗╦  ╔═╗╦═╗╔═╗
    # ║╣ ╚╗╔╝║╣ ║║║ ║   ╠═╣╠═╣║║║ ║║║  ║╣ ╠╦╝╚═╗
    # ╚═╝ ╚╝ ╚═╝╝╚╝ ╩   ╩ ╩╩ ╩╝╚╝═╩╝╩═╝╚═╝╩╚═╚═╝ COMMON EVENT HANDLERS
    # ====================================================================================================

    def header_drag(self, sender, args):
        """
        Handle window dragging dari header area.

        Args:
            sender: Event sender
            args: Event arguments
        """
        try:
            self.DragMove()
        except Exception as ex:
            print("Error in header_drag: {}".format(str(ex)))

    def button_close(self, sender, args):
        """
        Handle close button click.

        Args:
            sender: Event sender
            args: Event arguments
        """
        try:
            self.Close()
        except Exception as ex:
            print("Error in button_close: {}".format(str(ex)))

    # ╔═╗╦═╗╔═╗╔═╗╔═╗╦═╗╔╦╗╔═╗
    # ╠═╝╠╦╝║ ║╠═╝║╣ ╠╦╝ ║ ╚═╗
    # ╩  ╩╚═╚═╝╩  ╚═╝╩╚═ ╩ ╚═╝ PROPERTIES
    # ==================================================

    @property
    def XamlFile(self):
        """Get XAML file path."""
        return self._xaml_file

    @property
    def WindowTitle(self):
        """Get window title."""
        return self._title

    @WindowTitle.setter
    def WindowTitle(self, value):
        """Set window title."""
        self._title = value
        self.Title = value
        if hasattr(self, 'main_title'):
            self.main_title.Text = value

# ╔╗ ╦  ╔═╗╔═╗╦╔═  ╔═╗╦ ╦╔═╗╔═╗╔╦╗
# ╠╩╗║  ║ ║║ ║╠╩╗  ╚═╗╠═╣║╣ ║╣  ║
# ╚═╝╩═╝╚═╝╚═╝╩ ╩  ╚═╝╩ ╩╚═╝╚═╝ ╩  REPOSITORY BASE CLASS
# ====================================================================================================

class BaseRepositoryUI(BaseRevitWindow):
    """
    Base class untuk repository-style dialogs (bulk operations).

    Features:
    - Filter functionality
    - Bulk selection (select all/none)
    - Progress tracking
    - Item management
    """

    def __init__(self, xaml_file, title="", repository=None):
        """
        Initialize repository UI.

        Args:
            xaml_file (str): Path ke XAML file
            title (str): Window title
            repository: Repository instance (optional)
        """
        BaseRevitWindow.__init__(self, xaml_file, title)
        self.repository = repository
        self.items = []
        self.filtered_items = []

        # Setup repository-specific UI
        self.setup_repository_ui()

    def setup_repository_ui(self):
        """Setup repository-specific UI elements."""
        # Override in subclasses
        pass

    def load_items(self):
        """Load items dari repository. Override in subclasses."""
        self.items = []
        self.filtered_items = self.items

    def filter_items(self, search_text=""):
        """Filter items berdasarkan search text."""
        if not search_text:
            self.filtered_items = self.items
        else:
            # Default filter by name - override untuk custom filtering
            self.filtered_items = [item for item in self.items
                                 if search_text.lower() in item.Name.lower()]

        # Update UI
        self.update_list_view()

    def update_list_view(self):
        """Update list view dengan filtered items."""
        # Override in subclasses based on UI element names
        pass

    def select_all_items(self):
        """Select all items."""
        for item in self.filtered_items:
            if hasattr(item, 'IsSelected'):
                item.IsSelected = True
        self.update_list_view()

    def select_none_items(self):
        """Deselect all items."""
        for item in self.filtered_items:
            if hasattr(item, 'IsSelected'):
                item.IsSelected = False
        self.update_list_view()

    # ╔═╗╦  ╦╔═╗╔╗╔╔╦╗  ╦ ╦╔═╗╔╗╔╔╦╗╦  ╔═╗╦═╗╔═╗
    # ║╣ ╚╗╔╝║╣ ║║║ ║   ╠═╣╠═╣║║║ ║║║  ║╣ ╠╦╝╚═╗
    # ╚═╝ ╚╝ ╚═╝╝╚╝ ╩   ╩ ╩╩ ╩╝╚╝═╩╝╩═╝╚═╝╩╚═╚═╝ EVENT HANDLERS
    # ====================================================================================================

    def UIe_text_filter_updated(self, sender, args):
        """Handle filter text changes."""
        try:
            search_text = sender.Text.lower()
            self.filter_items(search_text)
        except Exception as ex:
            print("Error in filter update: {}".format(str(ex)))

    def UIe_btn_select_all(self, sender, args):
        """Handle select all button click."""
        try:
            self.select_all_items()
        except Exception as ex:
            print("Error in select all: {}".format(str(ex)))

    def UIe_btn_select_none(self, sender, args):
        """Handle select none button click."""
        try:
            self.select_none_items()
        except Exception as ex:
            print("Error in select none: {}".format(str(ex)))

    def UIe_checkbox_clicked(self, sender, args):
        """Handle checkbox click dengan multi-selection support."""
        try:
            # Get selected items dari list view
            list_view = self._get_list_view()
            if list_view and len(list_view.SelectedItems) > 1:
                # Apply same state ke semua selected items
                is_checked = sender.IsChecked
                for item in list_view.SelectedItems:
                    if hasattr(item, 'IsSelected'):
                        item.IsSelected = is_checked
                self.update_list_view()
        except Exception as ex:
            print("Error in checkbox click: {}".format(str(ex)))

    def _get_list_view(self):
        """Get list view control. Override in subclasses."""
        # Try common names
        for attr_name in ['UI_ListBox_Families', 'UI_ListBox_ViewTemplates', 'UI_ListBox']:
            if hasattr(self, attr_name):
                return getattr(self, attr_name)
        return None

# ╔╗ ╦  ╔═╗╔═╗╦╔═  ╔═╗╦ ╦╔═╗╔═╗╔╦╗
# ╠╩╗║  ║ ║║ ║╠╩╗  ║ ╦║ ║║╣ ║╣  ║
# ╚═╝╩═╝╚═╝╚═╝╩ ╩  ╚═╝╚═╝╚═╝╚═╝ ╩  DIALOG BASE CLASS
# ====================================================================================================

class BaseDialogUI(BaseRevitWindow):
    """
    Base class untuk dialog-style windows (settings, single operations).

    Features:
    - Settings management
    - Input validation
    - State persistence
    """

    def __init__(self, xaml_file, title=""):
        """
        Initialize dialog UI.

        Args:
            xaml_file (str): Path ke XAML file
            title (str): Window title
        """
        BaseRevitWindow.__init__(self, xaml_file, title)

        # Setup dialog-specific UI
        self.setup_dialog_ui()

    def setup_dialog_ui(self):
        """Setup dialog-specific UI elements."""
        # Override in subclasses
        pass

    def validate_inputs(self):
        """Validate dialog inputs. Override in subclasses."""
        return True

    def get_dialog_state(self):
        """Get current dialog state sebagai dictionary."""
        return {}

    def set_dialog_state(self, state):
        """Set dialog state dari dictionary."""
        pass

    def reset_dialog(self):
        """Reset dialog ke default state."""
        pass