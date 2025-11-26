# -*- coding: utf-8 -*-
"""
Dialog UI Classes

Specialized UI classes untuk dialog-style windows dengan settings dan single operations.

Author: PrasKaa
"""

# ╦ ╦╔═╗╔╦╗╔═╗╔╦╗╔═╗
# ║║║║╣  ║ ║ ║ ║║╚═╗
# ╚╩╝╚═╝ ╩ ╚═╝═╩╝╚═╝ IMPORTS
# ====================================================================================================
from ui.base_window import BaseDialogUI
from ui.ui_items import SheetItem, create_sheet_item
from pyrevit import revit, forms

# ╔═╗╦  ╦╔═╗╔╗╔╔╦╗  ╦ ╦╔═╗╔╦╗╔═╗╔╦╗╔═╗
# ║╣ ╚╗╔╝║╣ ║║║ ║   ║║║║╣  ║ ║ ║ ║║╚═╗
# ╚═╝ ╚╝ ╚═╝╝╚╝ ╩   ╚╩╝╚═╝ ╩ ╚═╝═╩╝╚═╝ ALIGN VIEWPORTS UI
# ====================================================================================================

class AlignViewportsUI(BaseDialogUI):
    """
    UI untuk Align Viewports dialog.

    Features:
    - Sheet selection dengan radio button behavior
    - Settings checkboxes (crop, titleblock, legend)
    - Single run operation
    """

    def __init__(self, xaml_file, title="Align Viewports"):
        """
        Initialize Align Viewports UI.

        Args:
            xaml_file (str): Path ke XAML file
            title (str): Window title
        """
        BaseDialogUI.__init__(self, xaml_file, title)

    def setup_dialog_ui(self):
        """Setup align viewports specific UI elements."""
        # Load selected sheets
        self.selected_sheets = self.get_selected_sheets()
        if self.selected_sheets:
            self.generate_list_items()

    def get_selected_sheets(self):
        """Get selected sheets dari Revit UI."""
        try:
            from Snippets._selection import get_selected_sheets

            selected_sheets = get_selected_sheets(
                given_uidoc=revit.uidoc,
                title=self.WindowTitle,
                label='Select Sheet to Align Viewports',
                exit_if_none=True
            )

            # Validate minimum sheets
            if len(selected_sheets) < 2:
                msg = "Not enough sheets were selected. Min 2 is required. Please, Try again."
                forms.alert(msg, title=self.WindowTitle, exitscript=True)
                return []

            # Format sheets
            selected_sheets = {"{} - {}".format(sheet.SheetNumber, sheet.Name): sheet for sheet in selected_sheets}
            return selected_sheets

        except Exception as ex:
            print("Error getting selected sheets: {}".format(str(ex)))
            forms.alert("Failed to get selected sheets.", exitscript=True)
            return []

    def generate_list_items(self):
        """Generate SheetItem list untuk display."""
        try:
            self.sheet_items = []

            # Create SheetItem untuk setiap sheet
            first = True
            for sheet_name, sheet in sorted(self.selected_sheets.items()):
                # First item auto-selected sebagai main sheet
                item = SheetItem(name=sheet_name, sheet_element=sheet, is_selected=first)
                self.sheet_items.append(item)
                first = False

            # Update UI
            self.update_list_view()

        except Exception as ex:
            print("Error generating list items: {}".format(str(ex)))

    def update_list_view(self):
        """Update ListView dengan sheet items."""
        try:
            # Try different common ListView names
            list_views = ['test_ListBox', 'UI_ListBox', 'sheets_list']

            for lv_name in list_views:
                if hasattr(self, lv_name):
                    list_view = getattr(self, lv_name)
                    list_view.ItemsSource = self.sheet_items
                    break
        except Exception as ex:
            print("Error updating list view: {}".format(str(ex)))

    def validate_inputs(self):
        """Validate dialog inputs."""
        try:
            # Check if main sheet is selected
            selected_main = None
            for item in self.sheet_items:
                if item.IsSelected:
                    selected_main = item
                    break

            if not selected_main:
                forms.alert("Please select a main sheet for alignment.")
                return False

            return True

        except Exception as ex:
            print("Error validating inputs: {}".format(str(ex)))
            return False

    def get_dialog_state(self):
        """Get current dialog state."""
        try:
            state = {
                'apply_crop': self.apply_crop,
                'apply_titleblock': self.apply_titleblock,
                'align_legend': self.align_legend,
                'overlap': self.overlap,
                'main_sheet': None,
                'other_sheets': []
            }

            # Get selected sheets
            for item in self.sheet_items:
                if item.IsSelected:
                    state['main_sheet'] = item.Element
                else:
                    state['other_sheets'].append(item.Element)

            return state

        except Exception as ex:
            print("Error getting dialog state: {}".format(str(ex)))
            return {}

    # ╔═╗╦  ╦╔═╗╔╗╔╔╦╗  ╦ ╦╔═╗╔╗╔╔╦╗╦  ╔═╗╦═╗╔═╗
    # ║╣ ╚╗╔╝║╣ ║║║ ║   ╠═╣╠═╣║║║ ║║║  ║╣ ╠╦╝╚═╗
    # ╚═╝ ╚╝ ╚═╝╝╚╝ ╩   ╩ ╩╩ ╩╝╚╝═╩╝╩═╝╚═╝╩╚═╚═╝ PROPERTIES
    # ====================================================================================================

    @property
    def apply_crop(self):
        """Get apply crop setting."""
        try:
            return self.UI_checkbox_apply_same_crop.IsChecked if hasattr(self, 'UI_checkbox_apply_same_crop') else False
        except:
            return False

    @property
    def apply_titleblock(self):
        """Get apply titleblock setting."""
        try:
            return self.UI_checkbox_apply_same_titleblock.IsChecked if hasattr(self, 'UI_checkbox_apply_same_titleblock') else False
        except:
            return False

    @property
    def align_legend(self):
        """Get align legend setting."""
        try:
            return self.UI_checkbox_align_legend.IsChecked if hasattr(self, 'UI_checkbox_align_legend') else False
        except:
            return False

    @property
    def overlap(self):
        """Get overlap setting."""
        try:
            return self.UI_checkbox_overlap.IsChecked if hasattr(self, 'UI_checkbox_overlap') else False
        except:
            return False

    # ╔═╗╦  ╦╔═╗╔╗╔╔╦╗  ╦ ╦╔═╗╔╗╔╔╦╗╦  ╔═╗╦═╗╔═╗
    # ║╣ ╚╗╔╝║╣ ║║║ ║   ╠═╣╠═╣║║║ ║║║  ║╣ ╠╦╝╚═╗
    # ╚═╝ ╚╝ ╚═╝╝╚╝ ╩   ╩ ╩╩ ╩╝╚╝═╩╝╩═╝╚═╝╩╚═╚═╝ EVENT HANDLERS
    # ====================================================================================================

    def button_run_click(self, sender, args):
        """Handle run button click."""
        try:
            if not self.validate_inputs():
                return

            # Get dialog state
            state = self.get_dialog_state()

            # Close dialog
            self.Close()

            # Execute alignment
            self.execute_alignment(state)

        except Exception as ex:
            print("Error in run button click: {}".format(str(ex)))
            forms.alert("Failed to execute alignment. See log for details.")

    def execute_alignment(self, state):
        """Execute viewport alignment dengan given state."""
        try:
            from Snippets._context_manager import ef_Transaction
            from Snippets._sheets import get_titleblock_on_sheet

            main_sheet = state['main_sheet']
            other_sheets = state['other_sheets']

            print("- MainSheet selected: {}".format(main_sheet.SheetNumber))

            # Process each other sheet
            for i, other_sheet in enumerate(other_sheets):
                print('- Aligning Viewports on Sheet {} [{}/{}]'.format(other_sheet.SheetNumber, i+1, len(other_sheets)))

                # Create sheet objects and align
                # This would need the actual SheetObject class implementation
                # For now, just show the pattern
                self.align_sheet_viewports(other_sheet, main_sheet, state)

        except Exception as ex:
            print("Error executing alignment: {}".format(str(ex)))
            forms.alert("Failed to complete alignment. See log for details.")

    def align_sheet_viewports(self, sheet, main_sheet, settings):
        """Align viewports pada single sheet. Placeholder implementation."""
        # This would contain the actual alignment logic
        # extracted from the original script
        print("Aligning sheet {} with settings: {}".format(sheet.SheetNumber, settings))

# ╔═╗╦═╗╔═╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ╠═╝╠╦╝║ ║╠═╝║╣ ╠╦╝ ║ ╚═╗
# ╩  ╩╚═╚═╝╩  ╚═╝╩╚═ ╩ ╚═╝ UTILITY FUNCTIONS
# ==================================================

def create_align_viewports_ui(xaml_file="Script.xaml", title="Align Viewports"):
    """
    Factory function untuk membuat Align Viewports UI.

    Args:
        xaml_file (str): Path ke XAML file
        title (str): Window title

    Returns:
        AlignViewportsUI: Configured UI instance
    """
    return AlignViewportsUI(xaml_file, title)

# ╔═╗╔═╗╔═╗╔═╗╔═╗╔╗ ╔═╗═╗ ╦
# ║ ║║  ║ ║╠═╝║╣ ╠╩╗║ ║╔╩╦╝
# ╚═╝╚═╝╚═╝╩  ╚═╝╚═╝╚═╝╩ ╚═ BASE SETTINGS DIALOG
# ==================================================

class BaseSettingsDialog(BaseDialogUI):
    """
    Base class untuk settings dialogs dengan multiple checkboxes.

    Features:
    - Multiple settings checkboxes
    - Settings persistence
    - Input validation
    """

    def __init__(self, xaml_file, title="Settings", settings_key="default"):
        """
        Initialize settings dialog.

        Args:
            xaml_file (str): Path ke XAML file
            title (str): Window title
            settings_key (str): Key untuk settings persistence
        """
        self.settings_key = settings_key
        BaseDialogUI.__init__(self, xaml_file, title)

    def setup_dialog_ui(self):
        """Setup settings-specific UI elements."""
        # Load saved settings
        self.load_settings()

    def load_settings(self):
        """Load settings dari config atau defaults."""
        try:
            from pyrevit import script
            my_config = script.get_config()

            # Load settings dengan key
            saved_settings = my_config.get(self.settings_key, {})
            self.set_dialog_state(saved_settings)

        except Exception as ex:
            print("Warning: Could not load settings: {}".format(str(ex)))

    def save_settings(self):
        """Save current settings ke config."""
        try:
            from pyrevit import script
            my_config = script.get_config()

            # Get current state
            current_state = self.get_dialog_state()

            # Save dengan key
            my_config.set(self.settings_key, current_state)

        except Exception as ex:
            print("Warning: Could not save settings: {}".format(str(ex)))

    def get_available_settings(self):
        """Get list of available setting names. Override in subclasses."""
        return []

    def validate_inputs(self):
        """Validate settings inputs."""
        # Basic validation - override untuk specific validation
        return True

    def apply_settings(self):
        """Apply settings dan close dialog."""
        try:
            if not self.validate_inputs():
                return

            # Save settings
            self.save_settings()

            # Close dialog
            self.Close()

            # Call success callback if available
            if hasattr(self, 'on_settings_applied'):
                self.on_settings_applied(self.get_dialog_state())

        except Exception as ex:
            print("Error applying settings: {}".format(str(ex)))
            forms.alert("Failed to apply settings. See log for details.")

    def reset_to_defaults(self):
        """Reset settings ke default values."""
        try:
            # Clear saved settings
            from pyrevit import script
            my_config = script.get_config()
            my_config.set(self.settings_key, {})

            # Reset UI to defaults
            self.reset_dialog()

        except Exception as ex:
            print("Error resetting settings: {}".format(str(ex)))

    # ╔═╗╦  ╦╔═╗╔╗╔╔╦╗  ╦ ╦╔═╗╔╗╔╔╦╗╦  ╔═╗╦═╗╔═╗
    # ║╣ ╚╗╔╝║╣ ║║║ ║   ╠═╣╠═╣║║║ ║║║  ║╣ ╠╦╝╚═╗
    # ╚═╝ ╚╝ ╚═╝╝╚╝ ╩   ╩ ╩╩ ╩╝╚╝═╩╝╩═╝╚═╝╩╚═╚═╝ EVENT HANDLERS
    # ====================================================================================================

    def button_apply_click(self, sender, args):
        """Handle apply button click."""
        self.apply_settings()

    def button_reset_click(self, sender, args):
        """Handle reset button click."""
        if forms.alert("Reset all settings to defaults?", ok=False, yes=True, no=True):
            self.reset_to_defaults()

    def button_cancel_click(self, sender, args):
        """Handle cancel button click."""
        self.Close()
