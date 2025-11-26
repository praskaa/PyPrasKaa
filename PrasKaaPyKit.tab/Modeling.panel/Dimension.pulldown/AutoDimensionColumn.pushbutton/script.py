# -*- coding: utf-8 -*-
"""
Auto Dimensioning Columns - Robust Framework
Automatically creates dimensions for selected columns with minimal errors
"""

import clr
import sys
import math
import json
import os
from collections import defaultdict

# Revit API
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import StructuralType
from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType

# pyRevit
from pyrevit import revit, forms, script

# Transaction for pyRevit
from Autodesk.Revit.DB import Transaction

# Windows Forms for modifier keys and advanced dialogs
import System.Windows.Forms as WinForms
from System.Windows.Forms import (
    Form, Button, Label, ListView, View, ColumnHeader,
    ListViewItem, ColumnHeaderStyle, HorizontalAlignment,
    FormBorderStyle, DockStyle, AnchorStyles, FormStartPosition,
    TextBox, DialogResult
)
from System.Drawing import Point, Size, Font, FontStyle, Color

# ============================================================================
# SELECTION FILTER
# ============================================================================
class ColumnSelectionFilter(ISelectionFilter):
    """Selection filter to allow only structural columns during selection"""

    def AllowElement(self, elem):
        """Allow only Structural Columns during selection"""
        try:
            # Primary check: category name (most reliable)
            if hasattr(elem, "Category") and elem.Category:
                cat_name = elem.Category.Name.lower()
                if 'column' in cat_name or 'kolom' in cat_name:
                    return True

            # Secondary check: built-in category ID
            if hasattr(elem, "Category") and elem.Category:
                cat_id = elem.Category.Id.Value
                if cat_id in [int(BuiltInCategory.OST_StructuralColumns),
                             int(BuiltInCategory.OST_Columns)]:
                    return True

            # Tertiary check: structural type
            if isinstance(elem, FamilyInstance):
                if hasattr(elem, 'StructuralType'):
                    if elem.StructuralType == StructuralType.Column:
                        return True

            # Debug: print what we're rejecting (only for debugging)
            # Uncomment if needed: print("Rejected: {}".format(elem.Category.Name if hasattr(elem, "Category") and elem.Category else "No Category"))

        except Exception as e:
            # Silent fail for selection filter
            pass
        return False

    def AllowReference(self, refer, point):
        return False


# ============================================================================
# CONFIGURATION
# ============================================================================
class Config:
    """Centralized configuration"""
    VERBOSE_OUTPUT = False  # Set to True for detailed debugging output
    DEFAULT_OFFSET_MM = 10
    DEFAULT_DIM_TYPE_NAME = "Arrow - 2.5mm Swis721 BT - Dimensi Kolom"
    DIM_LINE_LENGTH = 10  # feet

    # Reference plane names for columns
    REF_NAMES = {
        'x1': ['x_1', 'Back', 'Belakang'],
        'x2': ['x_2', 'Front', 'Depan'],
        'y1': ['y_1', 'Left', 'Kiri'],
        'y2': ['y_2', 'Right', 'Kanan']
    }

    # Column categories
    COLUMN_CATEGORIES = [
        BuiltInCategory.OST_StructuralColumns,
        BuiltInCategory.OST_Columns
    ]


# ============================================================================
# CONFIGURATION MANAGER
# ============================================================================
class ConfigurationManager:
    """Manages configuration persistence for pyRevit scripts"""

    def __init__(self, script_dir=None, config_filename="config.json"):
        self.script_dir = script_dir or os.path.dirname(__file__)
        self.config_filename = config_filename
        self.config_path = os.path.join(self.script_dir, config_filename)
        self.config = {}
        self._load_config()

    def _load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            else:
                # Create default configuration
                self.config = self._get_default_config()
                self._save_config()
        except Exception as e:
            print("Warning: Could not load config file: {}".format(str(e)))
            # Use defaults if loading fails
            self.config = self._get_default_config()

    def _save_config(self):
        """Save configuration to file"""
        try:
            # Ensure directory exists
            config_dir = os.path.dirname(self.config_path)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)

            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print("Error: Could not save config file: {}".format(str(e)))
            WinForms.MessageBox.Show(
                "Could not save configuration: {}".format(str(e)),
                "Configuration Error",
                WinForms.MessageBoxButtons.OK,
                WinForms.MessageBoxIcon.Warning
            )

    def _get_default_config(self):
        """Get default configuration values"""
        return {
            'offset_mm': Config.DEFAULT_OFFSET_MM,
            'dimension_type_name': Config.DEFAULT_DIM_TYPE_NAME
        }

    def get_value(self, key, default=None):
        """Get configuration value with optional default"""
        return self.config.get(key, default)

    def set_value(self, key, value):
        """Set configuration value and save"""
        self.config[key] = value
        self._save_config()

    def get_offset_mm(self):
        """Get saved offset in millimeters"""
        return self.get_value('offset_mm', Config.DEFAULT_OFFSET_MM)

    def set_offset_mm(self, offset_mm):
        """Set offset in millimeters"""
        self.set_value('offset_mm', offset_mm)

    def get_dimension_type_name(self):
        """Get saved dimension type name"""
        return self.get_value('dimension_type_name', Config.DEFAULT_DIM_TYPE_NAME)

    def set_dimension_type_name(self, name):
        """Set dimension type name"""
        self.set_value('dimension_type_name', name)

    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config = self._get_default_config()
        self._save_config()


# ============================================================================
# ADVANCED MULTI-SELECT DIALOG
# ============================================================================
class AdvancedMultiSelectDialog(Form):
    """Advanced multi-selection dialog dengan keyboard shortcuts dan search"""

    def __init__(self, items, title="Select Items", item_display_func=None, preselected_items=None):
        """
        Parameters:
        - items: List of objects
        - title: Dialog title
        - item_display_func: Function to get display name from item (optional)
        - preselected_items: List of items that should be pre-selected (optional)
        """
        self.items = items
        self.selected_items = []
        self.filtered_items = items[:]
        self.item_display_func = item_display_func or (lambda x: str(x))
        self.preselected_items = preselected_items or []

        self.InitializeComponent()
        self.Text = title

    def InitializeComponent(self):
        """Setup UI components"""
        self.Size = Size(500, 600)
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.StartPosition = FormStartPosition.CenterScreen
        self.MaximizeBox = False
        self.MinimizeBox = False

        # Search section
        self.setup_search_section()

        # ListView section
        self.setup_list_view()

        # Buttons section
        self.setup_buttons()

    def setup_search_section(self):
        """Setup search functionality"""
        y_pos = 20

        # Search label
        search_label = Label()
        search_label.Text = "Search:"
        search_label.Location = Point(20, y_pos)
        search_label.Size = Size(50, 20)
        self.Controls.Add(search_label)

        # Search textbox
        self.search_box = TextBox()
        self.search_box.Location = Point(80, y_pos)
        self.search_box.Size = Size(300, 20)
        self.search_box.TextChanged += self.on_search_text_changed
        self.Controls.Add(self.search_box)

        # Clear button
        clear_btn = Button()
        clear_btn.Text = "Clear"
        clear_btn.Location = Point(390, y_pos)
        clear_btn.Size = Size(50, 25)
        clear_btn.Click += self.on_clear_search
        self.Controls.Add(clear_btn)

        # Search tip
        y_pos += 25
        search_tip = Label()
        search_tip.Text = "Tip: Type to filter, Shift+Click for range, Ctrl+Click for individual"
        search_tip.Location = Point(20, y_pos)
        search_tip.Size = Size(450, 15)
        search_tip.Font = Font("Segoe UI", 8, FontStyle.Italic)
        search_tip.ForeColor = Color.Gray
        self.Controls.Add(search_tip)

    def setup_list_view(self):
        """Setup ListView dengan advanced multi-select"""
        y_pos = 70

        self.list_view = ListView()
        self.list_view.Location = Point(20, y_pos)
        self.list_view.Size = Size(460, 400)
        self.list_view.View = View.Details
        self.list_view.CheckBoxes = True
        self.list_view.MultiSelect = True  # Enables Shift+Click and Ctrl+Click
        self.list_view.FullRowSelect = True
        self.list_view.GridLines = False

        # Hide headers for clean appearance
        self.list_view.HeaderStyle = ColumnHeaderStyle.Nonclickable
        self.list_view.Columns.Add("", 440, HorizontalAlignment.Left)

        # Populate items
        self.populate_list_view()

        self.Controls.Add(self.list_view)

    def setup_buttons(self):
        """Setup control buttons"""
        y_pos = 480

        # Select All button
        select_all_btn = Button()
        select_all_btn.Text = "Select All"
        select_all_btn.Location = Point(20, y_pos)
        select_all_btn.Size = Size(100, 30)
        select_all_btn.Click += self.on_select_all
        self.Controls.Add(select_all_btn)

        # Deselect All button
        deselect_all_btn = Button()
        deselect_all_btn.Text = "Deselect All"
        deselect_all_btn.Location = Point(130, y_pos)
        deselect_all_btn.Size = Size(100, 30)
        deselect_all_btn.Click += self.on_deselect_all
        self.Controls.Add(deselect_all_btn)

        # OK button
        ok_btn = Button()
        ok_btn.Text = "OK"
        ok_btn.Location = Point(300, y_pos)
        ok_btn.Size = Size(80, 30)
        ok_btn.Click += self.on_ok_click
        self.Controls.Add(ok_btn)

        # Cancel button
        cancel_btn = Button()
        cancel_btn.Text = "Cancel"
        cancel_btn.Location = Point(390, y_pos)
        cancel_btn.Size = Size(80, 30)
        cancel_btn.Click += self.on_cancel_click
        self.Controls.Add(cancel_btn)

    def populate_list_view(self, items=None):
        """Populate ListView dengan items"""
        if items is None:
            items = self.filtered_items

        self.list_view.Items.Clear()

        for item in items:
            display_name = self.item_display_func(item)
            list_item = ListViewItem(display_name)
            list_item.Tag = item  # Store original object

            # Pre-select items that were previously selected
            if item in self.preselected_items:
                list_item.Checked = True

            self.list_view.Items.Add(list_item)

    # Event Handlers
    def on_search_text_changed(self, sender, args):
        """Filter items berdasarkan search text"""
        search_text = self.search_box.Text.lower().strip()

        if not search_text:
            self.filtered_items = self.items[:]
            self.populate_list_view()
        else:
            self.filtered_items = []
            for item in self.items:
                display_name = self.item_display_func(item).lower()
                if search_text in display_name:
                    self.filtered_items.append(item)
            self.populate_list_view()

    def on_clear_search(self, sender, args):
        """Clear search"""
        self.search_box.Text = ""

    def on_select_all(self, sender, args):
        """Select all visible items"""
        for item in self.list_view.Items:
            item.Checked = True

    def on_deselect_all(self, sender, args):
        """Deselect all visible items"""
        for item in self.list_view.Items:
            item.Checked = False

    def on_ok_click(self, sender, args):
        """Process selection dan close"""
        self.selected_items = []
        for item in self.list_view.CheckedItems:
            original_item = item.Tag
            self.selected_items.append(original_item)

        if not self.selected_items:
            WinForms.MessageBox.Show(
                "Please select at least one item.",
                "No Selection",
                WinForms.MessageBoxButtons.OK,
                WinForms.MessageBoxIcon.Warning
            )
            return

        self.DialogResult = DialogResult.OK
        self.Close()

    def on_cancel_click(self, sender, args):
        """Cancel selection"""
        self.DialogResult = DialogResult.Cancel
        self.Close()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def get_view_display_name(view):
    """Custom display function untuk views"""
    level_name = view.GenLevel.Name if view.GenLevel else "No Level"
    return "{} ({})".format(view.Name, level_name)


class Utils:
    """Utility functions for common operations"""
    
    @staticmethod
    def mm_to_feet(mm):
        """Convert millimeters to feet"""
        return mm / 304.8
    
    @staticmethod
    def get_view_scale_factor(view):
        """Get scale factor safely"""
        try:
            scale = view.Scale
            if scale <= 0:
                forms.alert("Warning: View scale is invalid. Using scale 1:100")
                return 100
            return scale
        except:
            return 100
    
    @staticmethod
    def safe_get_parameter(element, param_name):
        """Safely get parameter value"""
        try:
            param = element.LookupParameter(param_name)
            if param and param.HasValue:
                if param.StorageType == StorageType.String:
                    return param.AsString()
                elif param.StorageType == StorageType.Double:
                    return param.AsDouble()
                elif param.StorageType == StorageType.Integer:
                    return param.AsInteger()
                elif param.StorageType == StorageType.ElementId:
                    return param.AsElementId()
        except:
            pass
        return None
    
    @staticmethod
    def is_column(element):
        """Check if element is a column"""
        if element is None:
            return False
        
        try:
            # Check category
            if hasattr(element, 'Category') and element.Category:
                cat_id = element.Category.Id.Value
                if cat_id in [int(cat) for cat in Config.COLUMN_CATEGORIES]:
                    return True
                
                cat_name = element.Category.Name
                if any(keyword in cat_name for keyword in ['Column', 'Kolom', 'column']):
                    return True
            
            # Check structural type
            if isinstance(element, FamilyInstance):
                if hasattr(element, 'StructuralType'):
                    if element.StructuralType == StructuralType.Column:
                        return True
        except:
            pass
        
        return False
    
    @staticmethod
    def should_dimension_column(column, view, doc):
        """
        Check if column continues above current level
        Returns True if column should be dimensioned (continues upward)
        """
        try:
            # Get current view level
            view_level = view.GenLevel
            if not view_level:
                return True  # If can't determine, include it

            view_elevation = view_level.Elevation

            # Get column top level/offset
            top_level_param = column.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM)
            top_offset_param = column.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM)

            if top_level_param and top_level_param.HasValue:
                top_level_id = top_level_param.AsElementId()
                if top_level_id and top_level_id != ElementId.InvalidElementId:
                    top_level = doc.GetElement(top_level_id)
                    if top_level:
                        top_elevation = top_level.Elevation

                        # Add top offset if exists
                        if top_offset_param and top_offset_param.HasValue:
                            top_elevation += top_offset_param.AsDouble()

                        # Column continues upward if top is above current level
                        if top_elevation > view_elevation:
                            return True
                        else:
                            return False

            return True  # Default: include if can't determine

        except Exception as e:
            if Config.VERBOSE_OUTPUT:
                print("Error checking column level: {}".format(e))
            return True  # Default: include if error


# ============================================================================
# REFERENCE HANDLER
# ============================================================================
class ReferenceHandler:
    """Handle getting references from columns"""
    
    def __init__(self, doc, view):
        self.doc = doc
        self.view = view
    
    def get_references(self, column):
        """
        Get all 4 references (x1, x2, y1, y2) from column
        Returns: tuple (refs_dict, method_name) or (None, None) if failed
        method_name: 'named_references', 'geometry_references', 'face_references', or None
        """
        refs = {}

        # Get column orientation first (needed for geometry-based methods)
        location_data = self._get_column_orientation(column)

        # Method 1: Try named references
        refs = self._get_named_references(column)
        if self._validate_references(refs):
            return refs, 'named_references'

        # Method 2: Try geometry references (using local orientation)
        if location_data:
            refs = self._get_geometry_references(column, location_data)
            if self._validate_references(refs):
                return refs, 'geometry_references'

        # Method 3: Try faces (using local orientation)
        if location_data:
            refs = self._get_face_references(column, location_data)
            if self._validate_references(refs):
                return refs, 'face_references'

        return None, None
    
    def _get_column_orientation(self, column):
        """Get column center point and local orientation axes"""
        try:
            location = column.Location
            
            if isinstance(location, LocationPoint):
                center = location.Point
                angle = location.Rotation
                x_axis = XYZ(math.cos(angle), math.sin(angle), 0)
                y_axis = XYZ(-math.sin(angle), math.cos(angle), 0)
                
                return {
                    'center': center,
                    'x_axis': x_axis,
                    'y_axis': y_axis
                }
            
            elif isinstance(location, LocationCurve):
                curve = location.Curve
                center = curve.Evaluate(0.5, True)
                direction = (curve.GetEndPoint(1) - curve.GetEndPoint(0)).Normalize()
                
                # Check if vertical
                if direction.IsAlmostEqualTo(XYZ.BasisZ) or direction.IsAlmostEqualTo(-XYZ.BasisZ):
                    x_axis = XYZ.BasisX
                    y_axis = XYZ.BasisY
                else:
                    x_axis = direction
                    y_axis = XYZ.BasisZ.CrossProduct(x_axis).Normalize()
                
                return {
                    'center': center,
                    'x_axis': x_axis,
                    'y_axis': y_axis
                }
        
        except Exception as e:
            print("Error getting column orientation: {}".format(e))
        
        return None
    
    def _get_named_references(self, column):
        """Try to get references by name"""
        refs = {}
        
        for key, names in Config.REF_NAMES.items():
            for name in names:
                try:
                    ref = column.GetReferenceByName(name)
                    if ref:
                        refs[key] = ref
                        break
                except:
                    continue
        
        return refs
    
    def _get_geometry_references(self, column, location_data):
        """Get references from geometry edges - finds opposing faces using LOCAL column orientation"""
        refs = {}
        
        try:
            # Extract local orientation
            center = location_data['center']
            x_axis = location_data['x_axis']
            y_axis = location_data['y_axis']
            
            geo_options = Options()
            geo_options.ComputeReferences = True
            geo_options.View = self.view
            geo_options.IncludeNonVisibleObjects = False
            
            geo_element = column.get_Geometry(geo_options)
            if not geo_element:
                return refs
            
            # Collect all planar faces with their normals
            faces_data = []
            
            for geo_obj in geo_element:
                solid = None
                
                if isinstance(geo_obj, Solid) and geo_obj.Volume > 0:
                    solid = geo_obj
                elif isinstance(geo_obj, GeometryInstance):
                    inst_geo = geo_obj.GetInstanceGeometry()
                    for inst_obj in inst_geo:
                        if isinstance(inst_obj, Solid) and inst_obj.Volume > 0:
                            solid = inst_obj
                            break
                
                if solid:
                    for face in solid.Faces:
                        if isinstance(face, PlanarFace) and face.Reference:
                            normal = face.FaceNormal
                            # Only get vertical faces (perpendicular to Z)
                            if abs(normal.Z) < 0.1:  # Nearly horizontal normal = vertical face
                                faces_data.append({
                                    'reference': face.Reference,
                                    'normal': normal,
                                    'center': face.Origin
                                })
            
            if len(faces_data) < 4:
                if Config.VERBOSE_OUTPUT:
                    print("Not enough planar faces found: {}".format(len(faces_data)))
                return refs
            
            # Find pairs of opposite faces using LOCAL orientation
            # X direction: faces perpendicular to LOCAL x_axis (normal parallel to y_axis)
            # Y direction: faces perpendicular to LOCAL y_axis (normal parallel to x_axis)
            
            x_faces = []  # Faces perpendicular to LOCAL X axis
            y_faces = []  # Faces perpendicular to LOCAL Y axis
            
            for face_data in faces_data:
                normal = face_data['normal']
                
                # Project normal onto local axes using dot product
                dot_x = abs(normal.DotProduct(x_axis))  # How parallel to local x_axis
                dot_y = abs(normal.DotProduct(y_axis))  # How parallel to local y_axis
                
                # SWAPPED: Vertical faces (normal parallel to X) measure horizontal distance (Y)
                # Horizontal faces (normal parallel to Y) measure vertical distance (X)
                if dot_x > dot_y:  # Normal more aligned with X axis = vertical faces
                    y_faces.append(face_data)  # For Y dimension (horizontal measurement)
                else:  # Normal more aligned with Y axis = horizontal faces
                    x_faces.append(face_data)  # For X dimension (vertical measurement)
            
            # Get opposing X faces (perpendicular to local x_axis)
            if len(x_faces) >= 2:
                # Sort by position projected onto local x_axis
                x_faces.sort(key=lambda f: (f['center'] - center).DotProduct(x_axis))
                refs['x1'] = x_faces[0]['reference']  # Face on negative x_axis side
                refs['x2'] = x_faces[-1]['reference']  # Face on positive x_axis side
            
            # Get opposing Y faces (perpendicular to local y_axis)
            if len(y_faces) >= 2:
                # Sort by position projected onto local y_axis
                y_faces.sort(key=lambda f: (f['center'] - center).DotProduct(y_axis))
                refs['y1'] = y_faces[0]['reference']  # Face on negative y_axis side
                refs['y2'] = y_faces[-1]['reference']  # Face on positive y_axis side
        
        except Exception as e:
            print("Error getting geometry references: {}".format(e))
        
        return refs
    
    def _get_face_references(self, column, location_data):
        """Get references from faces - finds opposing faces using LOCAL column orientation"""
        refs = {}
        
        try:
            # Extract local orientation
            center = location_data['center']
            x_axis = location_data['x_axis']
            y_axis = location_data['y_axis']
            
            geo_options = Options()
            geo_options.ComputeReferences = True
            geo_options.View = self.view
            
            geo_element = column.get_Geometry(geo_options)
            if not geo_element:
                return refs
            
            # Collect planar faces
            faces_data = []
            for geo_obj in geo_element:
                if isinstance(geo_obj, Solid) and geo_obj.Volume > 0:
                    for face in geo_obj.Faces:
                        if isinstance(face, PlanarFace) and face.Reference:
                            normal = face.FaceNormal
                            # Only vertical faces
                            if abs(normal.Z) < 0.1:
                                faces_data.append({
                                    'reference': face.Reference,
                                    'normal': normal,
                                    'center': face.Origin
                                })
            
            if len(faces_data) < 4:
                return refs
            
            # Separate X and Y aligned faces using LOCAL orientation
            x_faces = []  # Faces perpendicular to LOCAL X axis
            y_faces = []  # Faces perpendicular to LOCAL Y axis
            
            for face_data in faces_data:
                normal = face_data['normal']
                
                # Project normal onto local axes
                dot_x = abs(normal.DotProduct(x_axis))
                dot_y = abs(normal.DotProduct(y_axis))
                
                # SWAPPED: Vertical faces (normal parallel to X) measure horizontal distance (Y)
                # Horizontal faces (normal parallel to Y) measure vertical distance (X)
                if dot_x > dot_y:  # Normal parallel to x_axis = vertical faces
                    y_faces.append(face_data)  # For Y dimension (horizontal measurement)
                else:  # Normal parallel to y_axis = horizontal faces
                    x_faces.append(face_data)  # For X dimension (vertical measurement)
            
            # Get opposing faces using LOCAL coordinate system
            if len(x_faces) >= 2:
                # Sort by position projected onto local x_axis
                x_faces.sort(key=lambda f: (f['center'] - center).DotProduct(x_axis))
                refs['x1'] = x_faces[0]['reference']
                refs['x2'] = x_faces[-1]['reference']
            
            if len(y_faces) >= 2:
                # Sort by position projected onto local y_axis
                y_faces.sort(key=lambda f: (f['center'] - center).DotProduct(y_axis))
                refs['y1'] = y_faces[0]['reference']
                refs['y2'] = y_faces[-1]['reference']
        
        except Exception as e:
            print("Error getting face references: {}".format(e))
        
        return refs
    
    def _validate_references(self, refs):
        """Check if we have all 4 valid references"""
        required_keys = ['x1', 'x2', 'y1', 'y2']
        return all(key in refs and refs[key] is not None for key in required_keys)


# ============================================================================
# COLUMN PROCESSOR
# ============================================================================
class ColumnProcessor:
    """Process individual column for dimensioning"""
    
    def __init__(self, doc, view, dim_type, offset_internal):
        self.doc = doc
        self.view = view
        self.dim_type = dim_type
        self.offset_internal = offset_internal
        self.ref_handler = ReferenceHandler(doc, view)
    
    def process(self, column):
        """
        Process one column and create dimensions
        Returns: tuple (success, dimension_ids, error_message, method_name)
        """
        try:
            # Get references
            refs, method = self.ref_handler.get_references(column)
            if not refs:
                return False, [], "Could not get references from column", None

            # Get location and orientation using ReferenceHandler method
            location_data = self.ref_handler._get_column_orientation(column)
            if not location_data:
                return False, [], "Could not get column location", method

            center = location_data['center']
            x_axis = location_data['x_axis']
            y_axis = location_data['y_axis']

            # Create dimensions
            dim_ids = []

            # X Dimension: x1,x2 are horizontal planes measuring vertical distance
            # Line direction must be vertical (y_axis), offset horizontal (x_axis)
            dim_x = self._create_dimension(
                refs['x1'], refs['x2'],
                center, x_axis, y_axis
            )
            if dim_x:
                dim_ids.append(dim_x.Id)

            # Y Dimension: y1,y2 are vertical planes measuring horizontal distance
            # Line direction must be horizontal (x_axis), offset vertical (y_axis)
            dim_y = self._create_dimension(
                refs['y1'], refs['y2'],
                center, y_axis, x_axis
            )
            if dim_y:
                dim_ids.append(dim_y.Id)

            if len(dim_ids) > 0:
                return True, dim_ids, None, method
            else:
                return False, [], "Failed to create dimensions", method

        except Exception as e:
            return False, [], str(e), None
    
    def _create_dimension(self, ref1, ref2, center, offset_direction, line_direction):
        """Create a single dimension line"""
        try:
            # Create reference array
            ref_array = ReferenceArray()
            ref_array.Append(ref1)
            ref_array.Append(ref2)
            
            # Calculate dimension line position
            offset_vec = offset_direction.Multiply(self.offset_internal)
            line_vec = line_direction.Multiply(Config.DIM_LINE_LENGTH)
            
            base_point = center.Add(offset_vec)
            line_start = base_point.Subtract(line_vec)
            line_end = base_point.Add(line_vec)
            
            dim_line = Line.CreateBound(line_start, line_end)
            
            # Create dimension
            if self.dim_type:
                dimension = self.doc.Create.NewDimension(
                    self.view, dim_line, ref_array, self.dim_type
                )
            else:
                dimension = self.doc.Create.NewDimension(
                    self.view, dim_line, ref_array
                )
            
            return dimension
        
        except Exception as e:
            if Config.VERBOSE_OUTPUT:
                print("Error creating dimension: {}".format(e))
            return None


# ============================================================================
# MAIN CONTROLLER
# ============================================================================
class AutoDimensionController:
    """Main controller for auto dimensioning"""

    def __init__(self):
        self.doc = revit.doc
        self.uidoc = revit.uidoc
        self.active_view = self.doc.ActiveView
        self.output = script.get_output()

    def get_all_plan_views(self):
        """Get all plan views (floor and structural) in the project, sorted by elevation"""
        try:
            collector = FilteredElementCollector(self.doc).OfClass(ViewPlan)
            plan_views = []

            for view in collector:
                # Skip template views and non-printable views
                if not view.IsTemplate and view.CanBePrinted:
                    # Check if it's a plan view (floor, structural, etc.)
                    view_family_type = self.doc.GetElement(view.GetTypeId())
                    if view_family_type:
                        family_name = view_family_type.get_Parameter(
                            BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
                        if family_name:
                            name_lower = family_name.lower()
                            # Include floor plans, structural plans, and any plan views
                            if ('floor' in name_lower or
                                'lantai' in name_lower or
                                'structural' in name_lower or
                                'struktur' in name_lower or
                                'plan' in name_lower):
                                plan_views.append(view)

            # Sort by level elevation
            plan_views.sort(key=lambda v: v.GenLevel.Elevation if v.GenLevel else 0)
            return plan_views

        except Exception as e:
            print("Error getting plan views: {}".format(e))
            return []

    def get_columns_in_view(self, view):
        """Get all columns visible in a specific view"""
        try:
            # Get all structural columns in project
            collector = FilteredElementCollector(self.doc)
            columns = collector.OfCategory(BuiltInCategory.OST_StructuralColumns).ToElements()

            # Also get architectural columns
            arch_collector = FilteredElementCollector(self.doc)
            arch_columns = arch_collector.OfCategory(BuiltInCategory.OST_Columns).ToElements()

            all_columns = list(columns) + list(arch_columns)

            # Filter columns that are visible in this view
            visible_columns = []

            for column in all_columns:
                if self.is_column_visible_in_view(column, view):
                    visible_columns.append(column)

            return visible_columns

        except Exception as e:
            print("Error getting columns in view: {}".format(e))
            return []

    def is_column_visible_in_view(self, column, view):
        """Check if column is visible in the given view"""
        try:
            # Get view level
            view_level = view.GenLevel
            if not view_level:
                return False

            # Get column's base level
            base_level_param = column.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)
            if base_level_param and base_level_param.HasValue:
                base_level_id = base_level_param.AsElementId()
                if base_level_id and base_level_id != ElementId.InvalidElementId:
                    base_level = self.doc.GetElement(base_level_id)
                    if base_level and base_level.Id == view_level.Id:
                        return True

            return False

        except Exception as e:
            print("Error checking column visibility: {}".format(e))
            return False

    def show_settings_dialog(self):
        """Show settings dialog for configuring default values"""
        config = ConfigurationManager()

        # Get current values
        current_offset = config.get_offset_mm()
        current_dim_type_name = config.get_dimension_type_name()

        # Ask for offset
        offset_str = forms.ask_for_string(
            prompt="Enter default offset distance in millimeters:",
            default=str(current_offset),
            title="Default Offset Distance"
        )

        if not offset_str:
            return False

        try:
            offset_mm = float(offset_str)
            if offset_mm <= 0:
                forms.alert("Offset must be a positive number.", title="Invalid Input")
                return False
        except ValueError:
            forms.alert("Invalid offset value. Please enter a valid number.", title="Invalid Input")
            return False

        # Get available dimension types
        dim_types = self._get_available_dimension_types()

        if not dim_types:
            forms.alert("No dimension types found in project.", title="No Dimension Types")
            return False

        # Ask for dimension type
        selected_dim_type = forms.SelectFromList.show(
            dim_types,
            title="Select Default Dimension Type",
            button_name="Select",
            multiselect=False,
            default=current_dim_type_name if current_dim_type_name in dim_types else None
        )

        if not selected_dim_type:
            return False

        # Save settings
        config.set_offset_mm(offset_mm)
        config.set_dimension_type_name(selected_dim_type)

        forms.alert("Settings saved successfully!\n\nOffset: {} mm\nDimension Type: {}".format(
            offset_mm, selected_dim_type), title="Settings Saved")
        return True

    def _get_available_dimension_types(self):
        """Get list of available dimension type names"""
        try:
            collector = FilteredElementCollector(self.doc).OfClass(DimensionType)
            dim_type_names = []

            for dt in collector:
                try:
                    name = dt.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
                    if name:
                        dim_type_names.append(name)
                except:
                    continue

            return sorted(dim_type_names) if dim_type_names else []
        except Exception as e:
            print("Error getting dimension types: {}".format(e))
            return []

    def run(self):
        """Main execution flow - supports both single view and batch processing with Shift+Click settings"""
        # Check for Shift+Click to open settings
        if WinForms.Control.ModifierKeys == WinForms.Keys.Shift:
            self.show_settings_dialog()
            return

        # Normal execution - ask user for processing mode
        processing_mode = forms.CommandSwitchWindow.show(
            ['Current View Only', 'Batch Process in Selected Plan Views'],
            message='Select processing mode:'
        )

        if not processing_mode:
            return

        if processing_mode == 'Current View Only':
            # Original single view processing
            self._run_single_view()
        else:
            # Batch processing all plan views (floor and structural)
            self._run_batch_processing()

    def _run_single_view(self):
        """Process columns in current view only"""
        # Step 1: Validate view
        if not self._validate_view():
            return

        # Step 2: Get user inputs
        config = self._get_user_inputs()
        if not config:
            return

        # Step 3: Get and validate columns
        columns = self._get_selected_columns()
        if not columns:
            return

        # Step 4: Process columns
        results = self._process_columns(columns, config)

        # Step 5: Show results
        self._show_results(results)

    def _run_batch_processing(self):
        """Batch process selected floor plan views"""
        # Get all plan views (floor and structural)
        plan_views = self.get_all_plan_views()
        if not plan_views:
            forms.alert("No plan views found in project.", title="No Plan Views")
            return

        # Store previously selected views for pre-selection when looping
        previous_selection = []

        # Loop for plan selection and confirmation
        while True:
            # Show advanced multi-select dialog for plan views
            dialog = AdvancedMultiSelectDialog(
                plan_views,
                "Select Plan Views to Process",
                item_display_func=get_view_display_name,
                preselected_items=previous_selection
            )
            result = dialog.ShowDialog()

            if result != DialogResult.OK:
                return  # User canceled selection

            selected_views = dialog.selected_items
            previous_selection = selected_views[:]  # Remember this selection

            # Show confirmation with selected plans
            message = "Selected {} plan views to process:\n\n".format(len(selected_views))
            selected_names = [get_view_display_name(view) for view in selected_views]
            message += "\n".join(selected_names)
            message += "\n\nProcess these plan views?"

            if forms.alert(message, title="Confirm Selection", yes=True, no=True):
                break  # User confirmed, exit loop and proceed
            # If user selected "No", loop continues to show selection dialog again with previous selection remembered

        # Get user inputs for selected plans
        config = self._get_user_inputs()
        if not config:
            return

        # Process each selected plan view
        total_processed = 0
        total_dimensions = 0
        plan_results = []

        if Config.VERBOSE_OUTPUT:
            print("Starting batch processing of {} selected plan views...".format(len(selected_views)))

        for plan_view in selected_views:
            if Config.VERBOSE_OUTPUT:
                print("\n=== Processing plan: {} ===".format(plan_view.Name))

            # Get columns visible in this view
            columns = self.get_columns_in_view(plan_view)
            if not columns:
                if Config.VERBOSE_OUTPUT:
                    print("No columns found in plan: {}".format(plan_view.Name))
                continue

            if Config.VERBOSE_OUTPUT:
                print("Found {} columns in plan".format(len(columns)))

            # Filter columns that continue upward from this level
            filtered_columns = []
            skipped_count = 0

            for column in columns:
                if Utils.should_dimension_column(column, plan_view, self.doc):
                    filtered_columns.append(column)
                else:
                    skipped_count += 1

            if skipped_count > 0 and Config.VERBOSE_OUTPUT:
                print("Skipped {} columns that stop at current level".format(skipped_count))

            if not filtered_columns:
                if Config.VERBOSE_OUTPUT:
                    print("No columns to dimension in plan: {}".format(plan_view.Name))
                continue

            if Config.VERBOSE_OUTPUT:
                print("Processing {} columns that continue upward".format(len(filtered_columns)))

            # Process columns for this view
            try:
                results = self._process_columns_for_view(filtered_columns, plan_view, config)
            except Exception as e:
                print("Error processing view {}: {}".format(plan_view.Name, e))
                results = {'success': [], 'failed': [{'element': None, 'name': 'All', 'id': 0, 'error': str(e)}], 'total': len(filtered_columns)}

            plan_result = {
                'view_name': plan_view.Name,
                'columns_processed': len(filtered_columns),
                'dimensions_created': len(results['success']) * 2,  # 2 dimensions per column
                'success_count': len(results['success']),
                'failed_count': len(results['failed'])
            }
            plan_results.append(plan_result)

            total_processed += len(filtered_columns)
            total_dimensions += len(results['success']) * 2

            if Config.VERBOSE_OUTPUT:
                print("Completed plan {}: {} columns, {} dimensions created".format(
                    plan_view.Name, len(filtered_columns), len(results['success']) * 2))

        # Show final summary
        self._show_batch_results(plan_results, total_processed, total_dimensions)
    
    def _validate_view(self):
        """Validate that current view supports dimensions"""
        if not isinstance(self.active_view, ViewPlan):
            forms.alert(
                "Active view '{}' is not a plan view.\n"
                "Please switch to a floor plan or ceiling plan.".format(
                    self.active_view.Name
                ),
                title="Invalid View Type"
            )
            return False
        return True
    
    def _get_user_inputs(self):
        """Get configuration, automatically using saved settings"""
        config = ConfigurationManager()

        # Load saved settings
        offset_mm = config.get_offset_mm()
        dim_type_name = config.get_dimension_type_name()

        # Find dimension type by name
        dim_type = self._find_dimension_type_by_name(dim_type_name)

        # If no dimension type found, prompt user to configure
        if not dim_type:
            forms.alert("Saved dimension type not found. Please configure settings using Shift+Click.", title="Configuration Needed")
            return None

        # Calculate internal offset
        offset_feet = Utils.mm_to_feet(offset_mm)
        scale = Utils.get_view_scale_factor(self.active_view)
        offset_internal = offset_feet * scale

        return {
            'offset_mm': offset_mm,
            'offset_internal': offset_internal,
            'dim_type': dim_type
        }
    
    def _select_dimension_type_name(self):
        """Let user select dimension type name"""
        try:
            # Get all dimension types
            collector = FilteredElementCollector(self.doc).OfClass(DimensionType)
            dim_type_names = []

            for dt in collector:
                try:
                    name = dt.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
                    if name:
                        dim_type_names.append(name)
                except:
                    continue

            if not dim_type_names:
                forms.alert("No dimension types found. Using default.")
                return Config.DEFAULT_DIM_TYPE_NAME

            # Sort names
            sorted_names = sorted(dim_type_names)

            # Select
            selected_name = forms.SelectFromList.show(
                sorted_names,
                title="Select Dimension Type",
                button_name="Select",
                multiselect=False
            )

            if selected_name:
                return selected_name
            else:
                return Config.DEFAULT_DIM_TYPE_NAME

        except Exception as e:
            print("Error selecting dimension type: {}".format(e))
            return Config.DEFAULT_DIM_TYPE_NAME

    def _find_dimension_type_by_name(self, type_name):
        """Find dimension type by name"""
        try:
            collector = FilteredElementCollector(self.doc).OfClass(DimensionType)

            for dt in collector:
                try:
                    name = dt.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
                    if name == type_name:
                        return dt
                except:
                    continue

            # If exact match not found, try partial match
            for dt in collector:
                try:
                    name = dt.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
                    if name and Config.DEFAULT_DIM_TYPE_NAME in name:
                        return dt
                except:
                    continue

            # Return first available if nothing matches
            collector = FilteredElementCollector(self.doc).OfClass(DimensionType)
            for dt in collector:
                return dt

        except Exception as e:
            print("Error finding dimension type: {}".format(e))

        return None
    
    def _get_selected_columns(self):
        """Get selected columns from Revit, with interactive selection if none selected"""
        selection = revit.get_selection()

        if not selection:
            # No pre-selection, prompt user to select columns
            try:
                selection_filter = ColumnSelectionFilter()

                # Prompt user to select columns
                selected_refs = self.uidoc.Selection.PickObjects(
                    ObjectType.Element,
                    selection_filter,
                    "Select structural columns to dimension (ESC to finish)"
                )

                if not selected_refs:
                    forms.alert("No columns selected.", title="Selection Cancelled")
                    return None

                # Convert references to elements
                columns = []
                processed_ids = set()

                for ref in selected_refs:
                    element = self.doc.GetElement(ref.ElementId)
                    if element and element.Id.Value not in processed_ids:
                        if Utils.is_column(element):
                            columns.append(element)
                            processed_ids.add(element.Id.Value)

            except Exception as e:
                forms.alert(
                    "Selection cancelled or failed: {}".format(str(e)),
                    title="Selection Error"
                )
                return None
        else:
            # Filter existing selection
            columns = []
            processed_ids = set()

            for element in selection:
                if not element or element.Id.Value in processed_ids:
                    continue

                if Utils.is_column(element):
                    columns.append(element)
                    processed_ids.add(element.Id.Value)

        if not columns:
            forms.alert(
                "No columns found in selection.\n"
                "Please select structural or architectural columns.",
                title="No Columns Found"
            )
            return None

        if Config.VERBOSE_OUTPUT:
            print("Found {} columns in selection".format(len(columns)))
        
        # Filter columns that continue above current level
        filtered_columns = []
        skipped_count = 0
        
        for column in columns:
            if Utils.should_dimension_column(column, self.active_view, self.doc):
                filtered_columns.append(column)
            else:
                skipped_count += 1
                print("Skipped: Column {} stops at current level".format(column.Id.Value))
        
        if skipped_count > 0 and Config.VERBOSE_OUTPUT:
            print("Filtered out {} columns that stop at current level".format(skipped_count))

        if not filtered_columns:
            forms.alert(
                "All selected columns stop at current level.\n"
                "No columns to dimension.",
                title="No Columns to Dimension"
            )
            return None

        if Config.VERBOSE_OUTPUT:
            print("Processing {} columns that continue upward".format(len(filtered_columns)))
        return filtered_columns
    
    def _process_columns(self, columns, config):
        """Process all columns and create dimensions"""
        return self._process_columns_for_view(columns, self.active_view, config)

    def _process_columns_for_view(self, columns, view, config):
        """Process columns for a specific view"""
        # Make view active for dimension creation
        self.uidoc.ActiveView = view

        # Recalculate offset for this view's scale
        scale = Utils.get_view_scale_factor(view)
        offset_feet = Utils.mm_to_feet(config['offset_mm'])
        offset_internal = offset_feet * scale

        processor = ColumnProcessor(
            self.doc,
            view,
            config['dim_type'],
            offset_internal
        )

        results = {
            'success': [],
            'failed': [],
            'total': len(columns)
        }

        # Use standard Revit Transaction
        t = Transaction(self.doc, "Auto Dimension Columns - {}".format(view.Name))
        t.Start()
        try:
            for column in columns:
                success, dim_ids, error, method = processor.process(column)

                col_id = column.Id.Value
                col_name = "Column {}".format(col_id)

                try:
                    if hasattr(column, 'Name') and column.Name:
                        col_name = column.Name
                except:
                    pass

                if success:
                    results['success'].append({
                        'element': column,
                        'name': col_name,
                        'id': col_id,
                        'dimensions': len(dim_ids),
                        'method': method
                    })
                    if Config.VERBOSE_OUTPUT:
                        print("✓ {} - {} dimensions created using {}".format(col_name, len(dim_ids), method))
                else:
                    results['failed'].append({
                        'element': column,
                        'name': col_name,
                        'id': col_id,
                        'error': error
                    })
                    if Config.VERBOSE_OUTPUT:
                        print("✗ {} - Failed: {}".format(col_name, error))
        except Exception as e:
            t.RollBack()
            raise e
        else:
            t.Commit()

        return results
    
    def _show_results(self, results):
        """Show summary of results"""
        success_count = len(results['success'])
        failed_count = len(results['failed'])
        total = results['total']

        message = "Dimension Creation Complete\n\n"
        message += "Total columns: {}\n".format(total)
        message += "Success: {}\n".format(success_count)
        message += "Failed: {}\n".format(failed_count)

        if success_count > 0:
            message += "\nSuccessful columns:\n"
            for item in results['success']:
                method_display = item.get('method', 'unknown').replace('_', ' ')
                message += "- {} (ID: {}): {} dimensions using {}\n".format(
                    item['name'], item['id'], item['dimensions'], method_display
                )

        if failed_count > 0:
            message += "\nFailed columns:\n"
            for item in results['failed']:
                message += "- {} (ID: {}): {}\n".format(
                    item['name'], item['id'], item['error']
                )

        forms.alert(message, title="Auto Dimension Results")

    def _show_batch_results(self, plan_results, total_columns, total_dimensions):
        """Show summary of batch processing results in console"""
        print("\n" + "="*60)
        print("BATCH PROCESSING COMPLETE!")
        print("="*60)
        print("Summary:")
        print("- Floor plans processed: {}".format(len(plan_results)))
        print("- Total columns processed: {}".format(total_columns))
        print("- Total dimensions created: {}".format(total_dimensions))

        if plan_results:
            print("\nResults by floor plan:")
            print("-" * 50)

            for result in plan_results:
                print("{}:".format(result['view_name']))
                print("  Columns: {} | Dimensions: {} | Success: {} | Failed: {}".format(
                    result['columns_processed'],
                    result['dimensions_created'],
                    result['success_count'],
                    result['failed_count']
                ))

        # Show detailed results if there were failures
        failed_plans = [r for r in plan_results if r['failed_count'] > 0]
        if failed_plans:
            print("\nPlans with failures:")
            for plan in failed_plans:
                print("- {}: {} failed".format(plan['view_name'], plan['failed_count']))

        print("="*60)


# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    controller = AutoDimensionController()
    controller.run()