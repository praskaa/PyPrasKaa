# -*- coding: utf-8 -*-
"""
Multi-Layer Area Reinforcement by Settings
Processor-based implementation menggunakan LOG-UTIL-REBAR-007
"""

__title__ = "Multi-Layer\nArea Rebar"
__author__ = "PrasKaaPyKit"

import sys
import os

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.UI.Selection import ObjectType
from Autodesk.Revit.DB.Structure import RebarBarType, AreaReinforcement, AreaReinforcementType
import clr
clr.AddReference('System')
clr.AddReference('PresentationCore')
clr.AddReference('PresentationFramework')
clr.AddReference('WindowsBase')
from System.Collections.Generic import List
from System.Collections.ObjectModel import ObservableCollection
from System.Windows import Window
from System.Windows.Markup import XamlReader
from System.IO import StringReader
from System.ComponentModel import INotifyPropertyChanged, PropertyChangedEventArgs
import tempfile
import codecs

# Import pyRevit forms
from pyrevit import forms, script

# Add lib folder to path
script_dir = os.path.dirname(__file__)
lib_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))), 'lib')
if lib_path not in sys.path:
    sys.path.append(lib_path)

try:
    from area_reinforcement import process_multi_layer_area_reinforcement
    # from rebar_selection import select_rebar_bar_type  # Commented out to avoid ISelectionFilter issues
except ImportError:
    # Fallback if lib not available
    def process_multi_layer_area_reinforcement(doc, processor_input, logger=None):
        print("ERROR: area_reinforcement library not available")
        return []

# Akses dokumen Revit
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application


# ============================================================================
# UI SETTINGS MODEL - Enhanced for 4 Layers
# ============================================================================
class LayerSettings:
    """Enhanced data model untuk 4 layer settings dengan additional support"""

    def __init__(self, layer_id, bar_type_name=None, spacing=150, enabled=False, is_additional=False):
        self.layer_id = layer_id
        self.bar_type_name = bar_type_name
        self.spacing = spacing
        self.enabled = enabled
        self.is_additional = is_additional  # Flag for additional layers

    def to_dict(self):
        """Convert to dictionary format untuk processor"""
        return {
            "layer_id": self.layer_id,
            "bar_type_name": self.bar_type_name,
            "spacing": self.spacing,
            "enabled": self.enabled,
            "is_additional": self.is_additional
        }


# ============================================================================
# UI WINDOW CLASS - Simplified
# ============================================================================
class MultiLayerWindow(forms.WPFWindow):
    """Simplified WPF Window untuk multi layer settings"""

    def __init__(self):
        # Setup UI
        self.setup_ui()
        self.setup_event_handlers()

        # Initialize layer settings
        self.initialize_layer_settings()

    def setup_ui(self):
        """Setup UI dengan XAML untuk 4 layers dengan additional support"""
        xaml = '''<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
                xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
                Title="Multi-Layer Area Reinforcement"
                Height="600" Width="650"
                WindowStartupLocation="CenterScreen"
                ResizeMode="CanResize">

            <Grid Margin="15">
                <Grid.RowDefinitions>
                    <RowDefinition Height="Auto"/>
                    <RowDefinition Height="*"/>
                    <RowDefinition Height="Auto"/>
                </Grid.RowDefinitions>

                <!-- Header -->
                <TextBlock Grid.Row="0" Text="Configure Multi-Layer Area Reinforcement"
                           FontSize="16" FontWeight="SemiBold" Margin="0,0,0,15"/>

                <!-- Main Content -->
                <ScrollViewer Grid.Row="1" VerticalScrollBarVisibility="Auto">
                    <StackPanel>

                        <!-- Major Direction -->
                        <GroupBox Header="Major Direction" Margin="0,0,0,10">
                            <StackPanel Orientation="Horizontal">
                                <RadioButton x:Name="rbXDirection" Content="X Direction" IsChecked="True" Margin="0,0,20,0"/>
                                <RadioButton x:Name="rbYDirection" Content="Y Direction"/>
                            </StackPanel>
                        </GroupBox>

                        <!-- Primary Layers -->
                        <GroupBox Header="Primary Layers" Margin="0,0,0,10">
                            <Grid>
                                <Grid.ColumnDefinitions>
                                    <ColumnDefinition Width="*"/>
                                    <ColumnDefinition Width="*"/>
                                </Grid.ColumnDefinitions>

                                <!-- Bottom Primary -->
                                <StackPanel Grid.Column="0" Margin="0,0,10,0">
                                    <TextBlock Text="Bottom Side" FontWeight="SemiBold" Margin="0,0,0,8"/>

                                    <!-- Bottom Major -->
                                    <CheckBox x:Name="cbBottomMajor" Content="Layer 1: Bottom Major" Margin="0,0,0,5" IsChecked="True"/>
                                    <StackPanel Orientation="Horizontal" Margin="20,0,0,10" IsEnabled="{Binding ElementName=cbBottomMajor, Path=IsChecked}">
                                        <TextBlock Text="Bar Type:" Width="60" VerticalAlignment="Center"/>
                                        <ComboBox x:Name="cbBottomMajorBarType" Width="100" Margin="5,0"/>
                                        <TextBlock Text="Spacing:" Margin="10,0,5,0" VerticalAlignment="Center"/>
                                        <TextBox x:Name="tbBottomMajorSpacing" Text="150" Width="50"/>
                                        <TextBlock Text="mm" VerticalAlignment="Center" Margin="5,0"/>
                                    </StackPanel>

                                    <!-- Bottom Minor -->
                                    <CheckBox x:Name="cbBottomMinor" Content="Layer 2: Bottom Minor" Margin="0,0,0,5" IsChecked="True"/>
                                    <StackPanel Orientation="Horizontal" Margin="20,0,0,10" IsEnabled="{Binding ElementName=cbBottomMinor, Path=IsChecked}">
                                        <TextBlock Text="Bar Type:" Width="60" VerticalAlignment="Center"/>
                                        <ComboBox x:Name="cbBottomMinorBarType" Width="100" Margin="5,0"/>
                                        <TextBlock Text="Spacing:" Margin="10,0,5,0" VerticalAlignment="Center"/>
                                        <TextBox x:Name="tbBottomMinorSpacing" Text="200" Width="50"/>
                                        <TextBlock Text="mm" VerticalAlignment="Center" Margin="5,0"/>
                                    </StackPanel>
                                </StackPanel>

                                <!-- Top Primary -->
                                <StackPanel Grid.Column="1">
                                    <TextBlock Text="Top Side" FontWeight="SemiBold" Margin="0,0,0,8"/>

                                    <!-- Top Major -->
                                    <CheckBox x:Name="cbTopMajor" Content="Layer 1: Top Major" Margin="0,0,0,5" IsChecked="True"/>
                                    <StackPanel Orientation="Horizontal" Margin="20,0,0,10" IsEnabled="{Binding ElementName=cbTopMajor, Path=IsChecked}">
                                        <TextBlock Text="Bar Type:" Width="60" VerticalAlignment="Center"/>
                                        <ComboBox x:Name="cbTopMajorBarType" Width="100" Margin="5,0"/>
                                        <TextBlock Text="Spacing:" Margin="10,0,5,0" VerticalAlignment="Center"/>
                                        <TextBox x:Name="tbTopMajorSpacing" Text="150" Width="50"/>
                                        <TextBlock Text="mm" VerticalAlignment="Center" Margin="5,0"/>
                                    </StackPanel>

                                    <!-- Top Minor -->
                                    <CheckBox x:Name="cbTopMinor" Content="Layer 2: Top Minor" Margin="0,0,0,5" IsChecked="True"/>
                                    <StackPanel Orientation="Horizontal" Margin="20,0,0,10" IsEnabled="{Binding ElementName=cbTopMinor, Path=IsChecked}">
                                        <TextBlock Text="Bar Type:" Width="60" VerticalAlignment="Center"/>
                                        <ComboBox x:Name="cbTopMinorBarType" Width="100" Margin="5,0"/>
                                        <TextBlock Text="Spacing:" Margin="10,0,5,0" VerticalAlignment="Center"/>
                                        <TextBox x:Name="tbTopMinorSpacing" Text="200" Width="50"/>
                                        <TextBlock Text="mm" VerticalAlignment="Center" Margin="5,0"/>
                                    </StackPanel>
                                </StackPanel>
                            </Grid>
                        </GroupBox>

                        <!-- Additional Layers -->
                        <GroupBox Header="Additional Layers (Optional)" Margin="0,0,0,10">
                            <StackPanel>

                                <!-- Enable Additional Bottom -->
                                <CheckBox x:Name="cbEnableAdditionalBottom" Content="Enable Additional Bottom Layers" Margin="0,0,0,10"/>

                                <!-- Additional Bottom Controls -->
                                <StackPanel x:Name="spAdditionalBottom" Margin="20,0,0,15" Visibility="Collapsed">
                                    <TextBlock Text="Additional Bottom Side" FontWeight="SemiBold" Margin="0,0,0,8"/>

                                    <!-- Bottom Major Additional -->
                                    <CheckBox x:Name="cbBottomMajorAdditional" Content="Layer 3: Bottom Major (Additional)" Margin="0,0,0,5" IsChecked="True"/>
                                    <StackPanel Orientation="Horizontal" Margin="20,0,0,10" IsEnabled="{Binding ElementName=cbBottomMajorAdditional, Path=IsChecked}">
                                        <TextBlock Text="Bar Type:" Width="60" VerticalAlignment="Center"/>
                                        <ComboBox x:Name="cbBottomMajorAdditionalBarType" Width="100" Margin="5,0"/>
                                        <TextBlock Text="Spacing:" Margin="10,0,5,0" VerticalAlignment="Center"/>
                                        <TextBox x:Name="tbBottomMajorAdditionalSpacing" Text="150" Width="50"/>
                                        <TextBlock Text="mm" VerticalAlignment="Center" Margin="5,0"/>
                                    </StackPanel>

                                    <!-- Bottom Minor Additional -->
                                    <CheckBox x:Name="cbBottomMinorAdditional" Content="Layer 4: Bottom Minor (Additional)" Margin="0,0,0,5" IsChecked="True"/>
                                    <StackPanel Orientation="Horizontal" Margin="20,0,0,10" IsEnabled="{Binding ElementName=cbBottomMinorAdditional, Path=IsChecked}">
                                        <TextBlock Text="Bar Type:" Width="60" VerticalAlignment="Center"/>
                                        <ComboBox x:Name="cbBottomMinorAdditionalBarType" Width="100" Margin="5,0"/>
                                        <TextBlock Text="Spacing:" Margin="10,0,5,0" VerticalAlignment="Center"/>
                                        <TextBox x:Name="tbBottomMinorAdditionalSpacing" Text="200" Width="50"/>
                                        <TextBlock Text="mm" VerticalAlignment="Center" Margin="5,0"/>
                                    </StackPanel>
                                </StackPanel>

                                <!-- Enable Additional Top -->
                                <CheckBox x:Name="cbEnableAdditionalTop" Content="Enable Additional Top Layers" Margin="0,0,0,10"/>

                                <!-- Additional Top Controls -->
                                <StackPanel x:Name="spAdditionalTop" Margin="20,0,0,10" Visibility="Collapsed">
                                    <TextBlock Text="Additional Top Side" FontWeight="SemiBold" Margin="0,0,0,8"/>

                                    <!-- Top Major Additional -->
                                    <CheckBox x:Name="cbTopMajorAdditional" Content="Layer 3: Top Major (Additional)" Margin="0,0,0,5"/>
                                    <StackPanel Orientation="Horizontal" Margin="20,0,0,10" IsEnabled="{Binding ElementName=cbTopMajorAdditional, Path=IsChecked}">
                                        <TextBlock Text="Bar Type:" Width="60" VerticalAlignment="Center"/>
                                        <ComboBox x:Name="cbTopMajorAdditionalBarType" Width="100" Margin="5,0"/>
                                        <TextBlock Text="Spacing:" Margin="10,0,5,0" VerticalAlignment="Center"/>
                                        <TextBox x:Name="tbTopMajorAdditionalSpacing" Text="150" Width="50"/>
                                        <TextBlock Text="mm" VerticalAlignment="Center" Margin="5,0"/>
                                    </StackPanel>

                                    <!-- Top Minor Additional -->
                                    <CheckBox x:Name="cbTopMinorAdditional" Content="Layer 4: Top Minor (Additional)" Margin="0,0,0,5"/>
                                    <StackPanel Orientation="Horizontal" Margin="20,0,0,10" IsEnabled="{Binding ElementName=cbTopMinorAdditional, Path=IsChecked}">
                                        <TextBlock Text="Bar Type:" Width="60" VerticalAlignment="Center"/>
                                        <ComboBox x:Name="cbTopMinorAdditionalBarType" Width="100" Margin="5,0"/>
                                        <TextBlock Text="Spacing:" Margin="10,0,5,0" VerticalAlignment="Center"/>
                                        <TextBox x:Name="tbTopMinorAdditionalSpacing" Text="200" Width="50"/>
                                        <TextBlock Text="mm" VerticalAlignment="Center" Margin="5,0"/>
                                    </StackPanel>
                                </StackPanel>

                            </StackPanel>
                        </GroupBox>

                        <!-- Summary -->
                        <GroupBox Header="Configuration Summary">
                            <StackPanel>
                                <TextBlock x:Name="txtSummary" Text="Primary layers selected"/>
                                <TextBlock Text="💡 Additional layers will create separate AR elements with automatic cover offsets"
                                           FontSize="10" Foreground="#666666" FontStyle="Italic" Margin="0,8,0,0"/>
                            </StackPanel>
                        </GroupBox>

                    </StackPanel>
                </ScrollViewer>

                <!-- Footer -->
                <StackPanel Grid.Row="2" Orientation="Horizontal" HorizontalAlignment="Right" Margin="0,15,0,0">
                    <Button x:Name="btnCancel" Content="Cancel" Width="80" Margin="0,0,10,0"/>
                    <Button x:Name="btnCreate" Content="Create Reinforcement" Width="150"
                            Background="#0078D7" Foreground="White" FontWeight="SemiBold"/>
                </StackPanel>
            </Grid>
        </Window>'''

        # Create window from XAML
        self._xaml_file = self._create_temp_xaml_file(xaml)
        forms.WPFWindow.__init__(self, self._xaml_file)

    def _create_temp_xaml_file(self, xaml_content):
        """Create temporary XAML file"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.xaml', delete=False)
        with codecs.open(temp_file.name, 'w', 'utf-8') as f:
            f.write(xaml_content)
        temp_file.close()
        return temp_file.name

    def setup_event_handlers(self):
        """Setup event handlers untuk semua 8 layers + toggles + collapsible panels"""
        try:
            self.btnCancel.Click += self.on_cancel
            self.btnCreate.Click += self.on_create

            # Update summary when checkboxes change (primary + additional + toggles)
            all_checkboxes = [
                self.cbBottomMajor, self.cbBottomMinor, self.cbTopMajor, self.cbTopMinor,
                self.cbBottomMajorAdditional, self.cbBottomMinorAdditional,
                self.cbTopMajorAdditional, self.cbTopMinorAdditional,
                self.cbEnableAdditionalBottom, self.cbEnableAdditionalTop
            ]

            for cb in all_checkboxes:
                cb.Checked += self.update_summary
                cb.Unchecked += self.update_summary

            # Handle collapsible panels
            self.cbEnableAdditionalBottom.Checked += self.on_toggle_additional_bottom
            self.cbEnableAdditionalBottom.Unchecked += self.on_toggle_additional_bottom
            self.cbEnableAdditionalTop.Checked += self.on_toggle_additional_top
            self.cbEnableAdditionalTop.Unchecked += self.on_toggle_additional_top

        except Exception as e:
            print("Error setting up event handlers: {}".format(str(e)))

    def initialize_layer_settings(self):
        """Initialize layer settings dan populate bar types untuk semua 8 layers"""
        try:
            # Get available bar types
            bar_types = self._get_bar_types()

            # Populate combo boxes untuk semua layers (primary + additional)
            all_combo_boxes = [
                self.cbBottomMajorBarType, self.cbBottomMinorBarType,
                self.cbTopMajorBarType, self.cbTopMinorBarType,
                self.cbBottomMajorAdditionalBarType, self.cbBottomMinorAdditionalBarType,
                self.cbTopMajorAdditionalBarType, self.cbTopMinorAdditionalBarType
            ]

            for cb in all_combo_boxes:
                cb.ItemsSource = bar_types
                cb.DisplayMemberPath = "Name"
                cb.SelectedValuePath = "Name"
                if bar_types:
                    cb.SelectedIndex = 0

            self.update_summary()

        except Exception as e:
            print("Error initializing: {}".format(str(e)))

    def _get_bar_types(self):
        """Get available RebarBarTypes"""
        bar_types = []
        try:
            collector = FilteredElementCollector(doc).OfClass(RebarBarType).ToElements()
            for rbt in collector:
                name = rbt.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() or "Unnamed"
                bar_types.append(type('BarType', (), {'Name': name, 'Element': rbt})())
        except Exception as e:
            print("Error getting bar types: {}".format(str(e)))
        return bar_types

    def update_summary(self, sender=None, args=None):
        """Update summary text untuk semua 8 layers"""
        try:
            enabled_layers = []
            ar_count = 0

            # Primary layers
            if self.cbBottomMajor.IsChecked:
                enabled_layers.append("Layer 1: Bottom Major")
            if self.cbBottomMinor.IsChecked:
                enabled_layers.append("Layer 2: Bottom Minor")
            if self.cbTopMajor.IsChecked:
                enabled_layers.append("Layer 1: Top Major")
            if self.cbTopMinor.IsChecked:
                enabled_layers.append("Layer 2: Top Minor")

            # Count primary AR elements
            if self.cbBottomMajor.IsChecked or self.cbBottomMinor.IsChecked:
                ar_count += 1  # AR 1: Bottom Primary
            if self.cbTopMajor.IsChecked or self.cbTopMinor.IsChecked:
                ar_count += 1  # AR 3: Top Primary

            # Additional layers
            if self.cbEnableAdditionalBottom.IsChecked:
                if self.cbBottomMajorAdditional.IsChecked:
                    enabled_layers.append("Layer 3: Bottom Major (Additional)")
                if self.cbBottomMinorAdditional.IsChecked:
                    enabled_layers.append("Layer 4: Bottom Minor (Additional)")
                ar_count += 1  # AR 2: Bottom Additional

            if self.cbEnableAdditionalTop.IsChecked:
                if self.cbTopMajorAdditional.IsChecked:
                    enabled_layers.append("Layer 3: Top Major (Additional)")
                if self.cbTopMinorAdditional.IsChecked:
                    enabled_layers.append("Layer 4: Top Minor (Additional)")
                ar_count += 1  # AR 4: Top Additional

            if enabled_layers:
                summary = "Active layers: {}\nWill create {} Area Reinforcement element(s)".format(
                    ", ".join(enabled_layers), ar_count)
                self.txtSummary.Text = summary
            else:
                self.txtSummary.Text = "No layers selected"

        except Exception as e:
            print("Error updating summary: {}".format(str(e)))

    def on_cancel(self, sender, args):
        """Cancel dialog"""
        self.DialogResult = False
        self.Close()

    def on_toggle_additional_bottom(self, sender, args):
        """Toggle visibility of additional bottom layers"""
        try:
            from System.Windows import Visibility
            if self.cbEnableAdditionalBottom.IsChecked:
                self.spAdditionalBottom.Visibility = Visibility.Visible
            else:
                self.spAdditionalBottom.Visibility = Visibility.Collapsed
        except Exception as e:
            print("Error toggling additional bottom: {}".format(str(e)))

    def on_toggle_additional_top(self, sender, args):
        """Toggle visibility of additional top layers"""
        try:
            from System.Windows import Visibility
            if self.cbEnableAdditionalTop.IsChecked:
                self.spAdditionalTop.Visibility = Visibility.Visible
            else:
                self.spAdditionalTop.Visibility = Visibility.Collapsed
        except Exception as e:
            print("Error toggling additional top: {}".format(str(e)))

    def on_create(self, sender, args):
        """Create reinforcement dengan validasi untuk semua 8 layers"""
        try:
            # Validate primary layers
            primary_enabled = sum([1 for cb in [self.cbBottomMajor, self.cbBottomMinor,
                                              self.cbTopMajor, self.cbTopMinor] if cb.IsChecked])

            # Validate additional layers (only if enabled)
            additional_enabled = 0
            if self.cbEnableAdditionalBottom.IsChecked:
                additional_enabled += sum([1 for cb in [self.cbBottomMajorAdditional,
                                                       self.cbBottomMinorAdditional] if cb.IsChecked])
            if self.cbEnableAdditionalTop.IsChecked:
                additional_enabled += sum([1 for cb in [self.cbTopMajorAdditional,
                                                       self.cbTopMinorAdditional] if cb.IsChecked])

            total_enabled = primary_enabled + additional_enabled

            if total_enabled == 0:
                forms.alert("Please select at least one layer!")
                return

            self.DialogResult = True
            self.Close()

        except Exception as e:
            print("Error on create: {}".format(str(e)))

    def get_processor_input(self, boundary_curves, host):
        """Get processor input dari UI settings untuk semua 8 layers"""
        # Get major direction
        major_direction = "X" if self.rbXDirection.IsChecked else "Y"

        # Get ui_settings untuk semua layers
        ui_settings = []

        # Primary Bottom Layers
        if self.cbBottomMajor.IsChecked:
            bar_type = self.cbBottomMajorBarType.SelectedItem.Name if self.cbBottomMajorBarType.SelectedItem else None
            spacing = int(self.tbBottomMajorSpacing.Text) if self.tbBottomMajorSpacing.Text else 150
            ui_settings.append({
                "layer_id": "Bottom Major",
                "bar_type_name": bar_type,
                "spacing": spacing,
                "enabled": True,
                "is_additional": False
            })

        if self.cbBottomMinor.IsChecked:
            bar_type = self.cbBottomMinorBarType.SelectedItem.Name if self.cbBottomMinorBarType.SelectedItem else None
            spacing = int(self.tbBottomMinorSpacing.Text) if self.tbBottomMinorSpacing.Text else 200
            ui_settings.append({
                "layer_id": "Bottom Minor",
                "bar_type_name": bar_type,
                "spacing": spacing,
                "enabled": True,
                "is_additional": False
            })

        # Primary Top Layers
        if self.cbTopMajor.IsChecked:
            bar_type = self.cbTopMajorBarType.SelectedItem.Name if self.cbTopMajorBarType.SelectedItem else None
            spacing = int(self.tbTopMajorSpacing.Text) if self.tbTopMajorSpacing.Text else 150
            ui_settings.append({
                "layer_id": "Top Major",
                "bar_type_name": bar_type,
                "spacing": spacing,
                "enabled": True,
                "is_additional": False
            })

        if self.cbTopMinor.IsChecked:
            bar_type = self.cbTopMinorBarType.SelectedItem.Name if self.cbTopMinorBarType.SelectedItem else None
            spacing = int(self.tbTopMinorSpacing.Text) if self.tbTopMinorSpacing.Text else 200
            ui_settings.append({
                "layer_id": "Top Minor",
                "bar_type_name": bar_type,
                "spacing": spacing,
                "enabled": True,
                "is_additional": False
            })

        # Additional Bottom Layers (only if enabled)
        if self.cbEnableAdditionalBottom.IsChecked:
            if self.cbBottomMajorAdditional.IsChecked:
                bar_type = self.cbBottomMajorAdditionalBarType.SelectedItem.Name if self.cbBottomMajorAdditionalBarType.SelectedItem else None
                spacing = int(self.tbBottomMajorAdditionalSpacing.Text) if self.tbBottomMajorAdditionalSpacing.Text else 150
                ui_settings.append({
                    "layer_id": "Bottom Major Additional",
                    "bar_type_name": bar_type,
                    "spacing": spacing,
                    "enabled": True,
                    "is_additional": True
                })

            if self.cbBottomMinorAdditional.IsChecked:
                bar_type = self.cbBottomMinorAdditionalBarType.SelectedItem.Name if self.cbBottomMinorAdditionalBarType.SelectedItem else None
                spacing = int(self.tbBottomMinorAdditionalSpacing.Text) if self.tbBottomMinorAdditionalSpacing.Text else 200
                ui_settings.append({
                    "layer_id": "Bottom Minor Additional",
                    "bar_type_name": bar_type,
                    "spacing": spacing,
                    "enabled": True,
                    "is_additional": True
                })

        # Additional Top Layers (only if enabled)
        if self.cbEnableAdditionalTop.IsChecked:
            if self.cbTopMajorAdditional.IsChecked:
                bar_type = self.cbTopMajorAdditionalBarType.SelectedItem.Name if self.cbTopMajorAdditionalBarType.SelectedItem else None
                spacing = int(self.tbTopMajorAdditionalSpacing.Text) if self.tbTopMajorAdditionalSpacing.Text else 150
                ui_settings.append({
                    "layer_id": "Top Major Additional",
                    "bar_type_name": bar_type,
                    "spacing": spacing,
                    "enabled": True,
                    "is_additional": True
                })

            if self.cbTopMinorAdditional.IsChecked:
                bar_type = self.cbTopMinorAdditionalBarType.SelectedItem.Name if self.cbTopMinorAdditionalBarType.SelectedItem else None
                spacing = int(self.tbTopMinorAdditionalSpacing.Text) if self.tbTopMinorAdditionalSpacing.Text else 200
                ui_settings.append({
                    "layer_id": "Top Minor Additional",
                    "bar_type_name": bar_type,
                    "spacing": spacing,
                    "enabled": True,
                    "is_additional": True
                })

        return {
            "major_direction": major_direction,
            "boundary_curves": boundary_curves,
            "host": host,
            "ui_settings": ui_settings
        }


# ============================================================================
# MAIN EXECUTION - Simplified
# ============================================================================


def main():
    """Main execution function"""
    try:
        output = script.get_output()

        # Step 1: Get Filled Region selection
        selection = uidoc.Selection.GetElementIds()
        if selection.Count == 0:
            forms.alert("Please select a Filled Region first!")
            return

        filled_region = doc.GetElement(selection[0])
        if not isinstance(filled_region, FilledRegion):
            forms.alert("Selected element is not a Filled Region!")
            return

        active_view = doc.ActiveView

        # Step 2: Get boundary curves
        import sys
        import os
        sys.path.append(os.path.dirname(__file__))
        try:
            from lib.area_reinforcement import get_filled_region_boundary, convert_view_to_model_coordinates
        except ImportError:
            # Fallback functions
            def get_filled_region_boundary(filled_region, view):
                curves = []
                try:
                    boundary_segments = filled_region.GetBoundaries()
                    for curve_loop in boundary_segments:
                        for curve in curve_loop:
                            curves.append(curve)
                except Exception as e:
                    print("Error getting boundary: {}".format(str(e)))
                return curves

            def convert_view_to_model_coordinates(curves, view):
                model_curves = []
                view_plane = view.SketchPlane.GetPlane() if hasattr(view, 'SketchPlane') and view.SketchPlane else None
                z_elevation = view_plane.Origin.Z if view_plane else 0

                for curve in curves:
                    try:
                        start = curve.GetEndPoint(0)
                        end = curve.GetEndPoint(1)
                        new_start = XYZ(start.X, start.Y, z_elevation)
                        new_end = XYZ(end.X, end.Y, z_elevation)

                        if isinstance(curve, Line):
                            new_curve = Line.CreateBound(new_start, new_end)
                        elif isinstance(curve, Arc):
                            mid = curve.Evaluate(0.5, True)
                            new_mid = XYZ(mid.X, mid.Y, z_elevation)
                            new_curve = Arc.Create(new_start, new_end, new_mid)
                        else:
                            new_curve = curve.CreateTransformed(Transform.Identity)

                        model_curves.append(new_curve)
                    except Exception as e:
                        print("Error converting curve: {}".format(str(e)))
                        model_curves.append(curve)

                return model_curves

        view_curves = get_filled_region_boundary(filled_region, active_view)
        if not view_curves:
            forms.alert("Cannot read boundary from Filled Region!")
            return

        model_curves = convert_view_to_model_coordinates(view_curves, active_view)

        # Step 3: Select host
        forms.alert("Select Floor or Foundation as host element")
        try:
            reference = uidoc.Selection.PickObject(ObjectType.Element, "Select host element")
            host = doc.GetElement(reference.ElementId)

            if not (isinstance(host, Floor) or isinstance(host, WallFoundation) or isinstance(host, Foundation)):
                forms.alert("Host must be Floor or Foundation!")
                return
        except:
            output.print_md("❌ **Host selection cancelled**")
            return

        # Step 4: Show simplified UI
        wpf_window = MultiLayerWindow()

        if not wpf_window.ShowDialog():
            output.print_md("❌ **Dialog cancelled by user**")
            return

        # Step 5: Get processor input
        processor_input = wpf_window.get_processor_input(model_curves, host)

        # Step 6: Process multi layer - SILENT MODE
        created_area_reinforcements = process_multi_layer_area_reinforcement(
            doc, processor_input, logger=output
        )

        # Step 7: Show results - SILENT MODE (no duplicate output)
        if created_area_reinforcements:
            success_msg = "Successfully created {} Area Reinforcement(s)!\n\n".format(
                len(created_area_reinforcements))

            success_msg += "Details:\n"
            for i, ar in enumerate(created_area_reinforcements, 1):
                success_msg += "• AR {}: ID {}\n".format(i, ar.Id)

            forms.alert(success_msg)

            # SILENT - No additional print_md to avoid double console
        else:
            forms.alert("Failed to create any Area Reinforcement elements!")
            output.print_md("\n## ❌ **Error: No elements created**")

    except Exception as e:
        forms.alert("Unexpected error: {}".format(str(e)))
        import traceback
        print(traceback.format_exc())




if __name__ == '__main__':
    main()