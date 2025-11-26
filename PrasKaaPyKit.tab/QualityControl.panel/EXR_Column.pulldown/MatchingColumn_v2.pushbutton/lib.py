# -*- coding: utf-8 -*-
"""
Library for Matching Dimension Column v2 - Configuration and UI
"""

import os
import json
import clr

clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import (
    Form, Button, Label, TextBox, CheckBox, GroupBox,
    FormBorderStyle, FormStartPosition, DialogResult, MessageBox, MessageBoxButtons, MessageBoxIcon
)
from System.Drawing import Point, Size, Font, FontStyle

from pyrevit import script

logger = script.get_logger()

class MatchingConfig:
    """Configuration manager for Matching Dimension Column v2 script"""

    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(__file__), 'matching_config.json')
        self.default_config = {
            'batch_size': 150,
            'disable_joins': True,
            'cleanup_geometry_cache': True,
            'export_results_to_csv': True,
            'max_table_rows': 50,
            'enable_progress_detail': True,
            'csv_base_dir': os.path.expanduser("~/Documents/pyRevit/Output"),
            'csv_create_folders': True
        }
        self.config = self.load_config()

    def load_config(self):
        """Load configuration from file, fallback to defaults"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    config = self.default_config.copy()
                    config.update(loaded_config)
                    return config
            else:
                return self.default_config.copy()
        except Exception as e:
            logger.warning("Failed to load config file: {}. Using defaults.".format(e))
            return self.default_config.copy()

    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            logger.error("Failed to save configuration: {}".format(e))
            return False

    def get(self, key):
        """Get a configuration value by key"""
        return self.config.get(key, self.default_config.get(key))

    def set(self, key, value):
        """Set a configuration value by key"""
        self.config[key] = value

class ConfigDialog(Form):
    """Configuration dialog for Matching Dimension Column v2"""

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.InitializeComponent()

    def InitializeComponent(self):
        self.Text = "Matching Column v2 - Configuration"
        self.Size = Size(400, 450)
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = False
        self.MinimizeBox = False

        y_pos = 20

        # Batch Processing Group
        batch_group = GroupBox()
        batch_group.Text = "Performance Settings"
        batch_group.Location = Point(20, y_pos)
        batch_group.Size = Size(350, 150)

        self.batch_size_label = Label()
        self.batch_size_label.Text = "Batch Size:"
        self.batch_size_label.Location = Point(15, 30)
        self.batch_size_label.Size = Size(100, 20)
        batch_group.Controls.Add(self.batch_size_label)

        self.batch_size_box = TextBox()
        self.batch_size_box.Text = str(self.config_manager.get('batch_size'))
        self.batch_size_box.Location = Point(120, 27)
        self.batch_size_box.Size = Size(80, 20)
        batch_group.Controls.Add(self.batch_size_box)

        self.disable_joins_check = CheckBox()
        self.disable_joins_check.Text = "Disable Auto-Joins During Transfer"
        self.disable_joins_check.Checked = self.config_manager.get('disable_joins')
        self.disable_joins_check.Location = Point(15, 60)
        self.disable_joins_check.Size = Size(300, 20)
        batch_group.Controls.Add(self.disable_joins_check)

        self.cleanup_cache_check = CheckBox()
        self.cleanup_cache_check.Text = "Cleanup Geometry Cache (Frees Memory)"
        self.cleanup_cache_check.Checked = self.config_manager.get('cleanup_geometry_cache')
        self.cleanup_cache_check.Location = Point(15, 90)
        self.cleanup_cache_check.Size = Size(300, 20)
        batch_group.Controls.Add(self.cleanup_cache_check)

        self.Controls.Add(batch_group)
        y_pos += 170

        # Reporting Group
        reporting_group = GroupBox()
        reporting_group.Text = "Reporting Settings"
        reporting_group.Location = Point(20, y_pos)
        reporting_group.Size = Size(350, 120)

        self.export_csv_check = CheckBox()
        self.export_csv_check.Text = "Export Full Results to CSV"
        self.export_csv_check.Checked = self.config_manager.get('export_results_to_csv')
        self.export_csv_check.Location = Point(15, 30)
        self.export_csv_check.Size = Size(300, 20)
        reporting_group.Controls.Add(self.export_csv_check)

        self.progress_detail_check = CheckBox()
        self.progress_detail_check.Text = "Show Detailed Batch Progress"
        self.progress_detail_check.Checked = self.config_manager.get('enable_progress_detail')
        self.progress_detail_check.Location = Point(15, 60)
        self.progress_detail_check.Size = Size(300, 20)
        reporting_group.Controls.Add(self.progress_detail_check)

        self.Controls.Add(reporting_group)
        y_pos += 140

        # Buttons
        self.save_btn = Button()
        self.save_btn.Text = "Save"
        self.save_btn.Location = Point(100, y_pos)
        self.save_btn.Size = Size(80, 30)
        self.save_btn.Click += self.on_save
        self.Controls.Add(self.save_btn)

        self.cancel_btn = Button()
        self.cancel_btn.Text = "Cancel"
        self.cancel_btn.Location = Point(200, y_pos)
        self.cancel_btn.Size = Size(80, 30)
        self.cancel_btn.Click += self.on_cancel
        self.Controls.Add(self.cancel_btn)

    def on_save(self, sender, args):
        try:
            batch_size = int(self.batch_size_box.Text)
            if batch_size <= 0:
                raise ValueError("Batch size must be a positive integer.")

            self.config_manager.set('batch_size', batch_size)
            self.config_manager.set('disable_joins', self.disable_joins_check.Checked)
            self.config_manager.set('cleanup_geometry_cache', self.cleanup_cache_check.Checked)
            self.config_manager.set('export_results_to_csv', self.export_csv_check.Checked)
            self.config_manager.set('enable_progress_detail', self.progress_detail_check.Checked)

            if self.config_manager.save_config():
                MessageBox.Show("Configuration saved successfully!", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information)
                self.DialogResult = DialogResult.OK
                self.Close()
            else:
                MessageBox.Show("Failed to save configuration.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)

        except ValueError as ve:
            MessageBox.Show("Invalid input: {}".format(ve), "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
        except Exception as e:
            MessageBox.Show("An error occurred: {}".format(e), "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)

    def on_cancel(self, sender, args):
        self.DialogResult = DialogResult.Cancel
        self.Close()