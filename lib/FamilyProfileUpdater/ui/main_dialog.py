# -*- coding: utf-8 -*-
"""
Main Dialog Logic
This file contains the Python class that controls the main UI window.
It loads the XAML file and handles all the UI events.
"""

import clr
import os
clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import OpenFileDialog

from pyrevit import forms, script, revit
from pyrevit.forms import WPFWindow

# Import project modules from the shared lib
from FamilyProfileUpdater.config.profile_configs import PROFILE_CONFIGS
from FamilyProfileUpdater.core.csv_processor import CSVProcessor
from FamilyProfileUpdater.core.family_manager import FamilyManager

class MainDialog(WPFWindow):
    """
    Main UI window for the Family Profile Updater tool.
    """
    def __init__(self):
        # Construct the path to the XAML file relative to this script
        xaml_path = os.path.join(os.path.dirname(__file__), 'MainDialog.xaml')
        super(MainDialog, self).__init__(xaml_path)
        
        self._setup_ui()

    def _setup_ui(self):
        """Initial setup of the UI components."""
        self.ProfileTypeComboBox.ItemsSource = [cfg['display_name'] for cfg in PROFILE_CONFIGS.values()]
        self.ProfileTypeComboBox.SelectedIndex = -1
        self.log_message("Tool initialized. Please select a profile type.")

    def profile_type_changed(self, sender, args):
        """Handles the event when the profile type selection changes."""
        if self.ProfileTypeComboBox.SelectedIndex == -1:
            return
        
        selected_profile_name = self.ProfileTypeComboBox.SelectedItem
        self.selected_config_key = next((key for key, cfg in PROFILE_CONFIGS.items() if cfg['display_name'] == selected_profile_name), None)
        
        if self.selected_config_key:
            config = PROFILE_CONFIGS[self.selected_config_key]
            preview_text = "Expected Headers: {}\n".format(', '.join(config['csv_headers']))
            preview_text += "Sample Data: {}".format(config['sample_data'])
            self.PreviewTextBlock.Text = preview_text
            self.log_message("Selected profile: {}. Ready to select CSV file.".format(selected_profile_name))
        self.check_process_button_state()

    def browse_for_csv(self, sender, args):
        """Opens a file dialog to select a CSV file."""
        file_dialog = OpenFileDialog()
        file_dialog.Filter = "CSV Files (*.csv)|*.csv|All files (*.*)|*.*"
        file_dialog.Title = "Select a CSV file"
        
        if file_dialog.ShowDialog() == clr.System.Windows.Forms.DialogResult.OK:
            self.CsvPathTextBox.Text = file_dialog.FileName
            self.log_message("CSV file selected: {}".format(file_dialog.FileName))
        self.check_process_button_state()

    def process_data(self, sender, args):
        """Starts the data processing task."""
        self.log_message("="*50)
        self.log_message("Starting processing...")
        self.ProgressBar.Value = 0
        self.ProgressTextBlock.Text = "Starting..."

        config = PROFILE_CONFIGS[self.selected_config_key]
        csv_path = self.CsvPathTextBox.Text
        
        self.ProgressTextBlock.Text = "Reading and validating CSV..."
        self.ProgressBar.Value = 20
        csv_processor = CSVProcessor(config)
        if not csv_processor.read_and_validate(csv_path):
            errors = "\n".join(csv_processor.get_errors())
            forms.alert("Invalid CSV file:\n{}".format(errors), title="CSV Error")
            self.log_message("Error: CSV validation failed.")
            self.ProgressTextBlock.Text = "CSV Error!"
            return
        
        profiles_data = csv_processor.get_data()
        self.log_message("CSV validation successful. Found {} profiles.".format(len(profiles_data)))
        self.ProgressBar.Value = 40

        self.ProgressTextBlock.Text = "Updating Revit family types..."
        self.ProgressBar.Value = 60
        try:
            doc = revit.doc
            family_manager = FamilyManager(doc)
            results = family_manager.process_profiles(profiles_data, config)
            
            for result in results:
                self.log_message(result)
            
            self.ProgressBar.Value = 100
            self.ProgressTextBlock.Text = "Processing Complete!"
            self.log_message("Processing finished successfully.")
            forms.alert("Family types updated successfully!", title="Success")

        except Exception as e:
            self.log_message("An error occurred during Revit processing: {}".format(e))
            self.ProgressTextBlock.Text = "Revit Error!"
            forms.alert("An error occurred: {}".format(e), title="Revit Error")

    def close_dialog(self, sender, args):
        """Closes the dialog window."""
        self.Close()

    def log_message(self, message):
        """Appends a message to the log text block."""
        self.LogTextBlock.Text += message + "\n"

    def check_process_button_state(self):
        """Enables or disables the Process button based on UI state."""
        if self.ProfileTypeComboBox.SelectedIndex != -1 and self.CsvPathTextBox.Text:
            self.ProcessButton.IsEnabled = True
        else:
            self.ProcessButton.IsEnabled = False

    def show_dialog(self):
        """Shows the modal dialog."""
        self.ShowDialog()