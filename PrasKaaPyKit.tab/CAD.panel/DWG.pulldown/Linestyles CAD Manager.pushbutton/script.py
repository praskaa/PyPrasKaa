# -*- coding: utf-8 -*-
__title__ = "Linestyles CAD Manager"
__author__ = "PrasKaa"
__version__ = 'Version: 1.1'
__doc__ = """Version: 1.1
Date    = 03.03.2026
_____________________________________________________________________
Description:
CAD Layer Manager - Manage line styles for linked CAD files in Revit.
Provides a unified interface to view and edit line weight and line 
pattern overrides for all layers in linked CAD files.
_____________________________________________________________________
How-to:
1. Open Revit with PrasKaaPyKit extension loaded
2. Navigate to: CAD → DWG → Linestyles CAD Manager
3. The tool will automatically detect all linked CAD files
4. Use filters to find specific CAD files or layers
5. Select layers in the grid and edit using:
   - Quick Presets buttons for common configurations
   - Batch Edit panel for custom line weight/pattern
6. Click "Apply All Pending Changes" to apply changes to Revit

Changes in v1.1:
- Form no longer closes after applying changes (allows iteration)
- Removed confusing checkbox mechanism; direct apply buttons instead
- Added "Select All Visible" button
- Improved color contrast for accessibility (WCAG AA compliant)
- Pending changes highlighted with blue border style instead of yellow
- Renamed ambiguous preset "LW1 Only" to "Weight 1 Only"
- Increased minimum font sizes
- Clearer GroupBox layout for batch editing

_____________________________________________________
Last update:
- [04.03.2026] - 1.1 UI/UX improvements
- [03.03.2026] - 1.0 RELEASE
_____________________________________________________________________
Author:  PrasKaa"""

from pyrevit import revit, DB, script, forms
import clr

clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')

import System
from System.Windows.Forms import (
    Form, DataGridView, Button, DockStyle, FormBorderStyle,
    DataGridViewAutoSizeColumnsMode, DataGridViewSelectionMode,
    DataGridViewTextBoxColumn, DataGridViewComboBoxColumn, DialogResult,
    Panel, FormStartPosition, TextBox, Label, CheckBox, GroupBox,
    ComboBox, ComboBoxStyle, Padding, AnchorStyles, ToolTip,
    BorderStyle, FlatStyle
)
from System.Drawing import Size, Point, Color, Font, FontStyle
from System.ComponentModel import BindingList

# Initialize
doc = revit.doc
logger = script.get_logger()


# ============================================================================
# DATA MODELS
# ============================================================================

class CADLayer:
    """Simplified CAD layer model."""
    
    def __init__(self, category, cad_name):
        self.category = category
        self.cad_name = cad_name
        self.name = category.Name if category else "Unknown"
        
        # Current values
        self.current_weight = self._get_line_weight()
        self.current_pattern = self._get_line_pattern()
        
        # New values (for changes)
        self.new_weight = None
        self.new_pattern = None
    
    def _get_line_weight(self):
        try:
            return self.category.GetLineWeight(DB.GraphicsStyleType.Projection)
        except:
            return 1
    
    def _get_line_pattern(self):
        try:
            pattern_id = self.category.GetLinePatternId(DB.GraphicsStyleType.Projection)
            if pattern_id and pattern_id != DB.ElementId.InvalidElementId:
                pattern = doc.GetElement(pattern_id)
                return pattern.Name if pattern else "Solid"
            return "Solid"
        except:
            return "Solid"
    
    def has_changes(self):
        return self.new_weight is not None or self.new_pattern is not None
    
    def get_changes_text(self):
        if not self.has_changes():
            return ""
        changes = []
        if self.new_weight is not None:
            changes.append("LW: {} → {}".format(self.current_weight, self.new_weight))
        if self.new_pattern is not None:
            changes.append("LP: {} → {}".format(self.current_pattern, self.new_pattern))
        return " | ".join(changes)
    
    def apply_changes(self):
        success = True
        if self.new_weight is not None:
            try:
                self.category.SetLineWeight(self.new_weight, DB.GraphicsStyleType.Projection)
                self.current_weight = self.new_weight
            except Exception as e:
                logger.error("Failed to set weight for {}: {}".format(self.name, e))
                success = False
        
        if self.new_pattern is not None:
            try:
                pattern = get_pattern_by_name(self.new_pattern)
                if pattern:
                    self.category.SetLinePatternId(pattern.Id, DB.GraphicsStyleType.Projection)
                    self.current_pattern = self.new_pattern
            except Exception as e:
                logger.error("Failed to set pattern for {}: {}".format(self.name, e))
                success = False
        
        return success
    
    def clear_changes(self):
        self.new_weight = None
        self.new_pattern = None


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_cad_files():
    cad_data = {}
    cad_types = DB.FilteredElementCollector(doc)\
        .OfClass(DB.CADLinkType)\
        .WhereElementIsElementType()\
        .ToElements()
    
    for cad_type in cad_types:
        try:
            cad_name = cad_type.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
        except:
            cad_name = cad_type.Name if hasattr(cad_type, 'Name') else "Unknown"
        
        layers = []
        if cad_type.Category and cad_type.Category.SubCategories:
            for sub_cat in cad_type.Category.SubCategories:
                if sub_cat and sub_cat.Name:
                    layers.append(CADLayer(sub_cat, cad_name))
        
        if layers:
            cad_data[cad_name] = layers
    
    return cad_data


def get_line_patterns():
    patterns = []
    collector = DB.FilteredElementCollector(doc).OfClass(DB.LinePatternElement)
    for pattern in collector:
        patterns.append(pattern.Name)
    return sorted(patterns)


def get_pattern_by_name(pattern_name):
    collector = DB.FilteredElementCollector(doc).OfClass(DB.LinePatternElement)
    for pattern in collector:
        if pattern.Name == pattern_name:
            return pattern
    return None


# ============================================================================
# COLORS & FONTS  (WCAG AA compliant)
# ============================================================================

# Background palette
CLR_BG_TOP       = Color.FromArgb(240, 243, 248)   # soft blue-grey
CLR_BG_BATCH     = Color.FromArgb(245, 247, 250)
CLR_BG_BOTTOM    = Color.FromArgb(230, 233, 238)

# Accent
CLR_APPLY_BG     = Color.FromArgb(30, 120, 60)     # dark green  — white text → 7.1:1
CLR_APPLY_DIS    = Color.FromArgb(130, 140, 130)
CLR_APPLY_BOTH   = Color.FromArgb(25, 100, 175)    # dark blue   — white text → 7.4:1

# Pending row highlight — blue tint, clearly distinguishable for deuteranopia
CLR_PENDING_ROW  = Color.FromArgb(210, 230, 255)   # light blue
CLR_PENDING_TXT  = Color.FromArgb(20, 60, 140)     # dark blue text on pending

FNT_DEFAULT  = Font("Segoe UI", 9,  FontStyle.Regular)
FNT_BOLD     = Font("Segoe UI", 9,  FontStyle.Bold)
FNT_SMALL    = Font("Segoe UI", 9,  FontStyle.Regular)   # was 8pt — raised to 9pt
FNT_BIG_BTN  = Font("Segoe UI", 10, FontStyle.Bold)


# ============================================================================
# MAIN UI FORM
# ============================================================================

class CADLayerManagerForm(Form):

    def __init__(self, cad_data):
        self.cad_data = cad_data
        self.all_layers = []
        self.filtered_layers = []
        self.line_patterns = get_line_patterns()
        self._tooltip = ToolTip()

        for layers in cad_data.values():
            self.all_layers.extend(layers)
        self.filtered_layers = self.all_layers[:]

        self.Text = "CAD Layer Manager  v1.1"
        self.Size = Size(1050, 740)
        self.StartPosition = FormStartPosition.CenterScreen
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.MinimumSize = Size(950, 640)
        self.Font = FNT_DEFAULT

        self._build_ui()
        self._populate_grid()

    # ------------------------------------------------------------------
    # UI CONSTRUCTION
    # ------------------------------------------------------------------

    def _build_ui(self):
        top_panel   = self._create_top_panel()
        top_panel.Dock   = DockStyle.Top
        top_panel.Height = 88

        grid_panel  = self._create_grid_panel()
        grid_panel.Dock  = DockStyle.Fill

        batch_panel = self._create_batch_panel()
        batch_panel.Dock   = DockStyle.Bottom
        batch_panel.Height = 110

        btn_panel   = self._create_button_panel()
        btn_panel.Dock   = DockStyle.Bottom
        btn_panel.Height = 54

        # Order matters for DockStyle
        self.Controls.Add(grid_panel)
        self.Controls.Add(batch_panel)
        self.Controls.Add(btn_panel)
        self.Controls.Add(top_panel)

    # --- Top panel ---------------------------------------------------

    def _create_top_panel(self):
        panel = Panel()
        panel.BackColor = CLR_BG_TOP
        panel.Padding   = Padding(8, 8, 8, 4)

        # ── Row 1: CAD file filter + layer text filter ──────────────
        lbl_cad = self._lbl("CAD File:", Point(10, 14))

        self.cmb_cad = ComboBox()
        self.cmb_cad.Location = Point(80, 11)
        self.cmb_cad.Size = Size(260, 22)
        self.cmb_cad.DropDownStyle = ComboBoxStyle.DropDownList
        self.cmb_cad.Font = FNT_DEFAULT
        self.cmb_cad.Items.Add("All CAD Files")
        for name in sorted(self.cad_data.keys()):
            self.cmb_cad.Items.Add(name)
        self.cmb_cad.SelectedIndex = 0
        self.cmb_cad.SelectedIndexChanged += self._on_filter_changed

        lbl_lf = self._lbl("Layer Filter:", Point(355, 14))

        self.txt_filter = TextBox()
        self.txt_filter.Location = Point(440, 11)
        self.txt_filter.Size = Size(210, 22)
        self.txt_filter.Font = FNT_DEFAULT
        self.txt_filter.TextChanged += self._on_filter_changed
        self._tooltip.SetToolTip(self.txt_filter, "Type to filter layer names (case-insensitive)")

        btn_clear_f = self._btn("✕ Clear", Point(660, 10), Size(70, 24))
        btn_clear_f.Click += self._clear_filters
        self._tooltip.SetToolTip(btn_clear_f, "Clear text filter and CAD file selection")

        # Select All Visible
        btn_sel_all = self._btn("☑ Select All Visible", Point(745, 10), Size(150, 24))
        btn_sel_all.Click += self._select_all_visible
        self._tooltip.SetToolTip(btn_sel_all, "Select all rows currently shown in the grid")

        # ── Row 2: Quick presets ────────────────────────────────────
        lbl_pre = self._lbl("Quick Presets:", Point(10, 52), bold=True)

        # (label, pattern_or_None, weight_or_None, tooltip)
        presets = [
            ("Solid  LW1",      "Solid",  1,    "Set pattern=Solid and weight=1"),
            ("Dashed  LW1",     "Dashed", 1,    "Set pattern=Dashed and weight=1"),
            ("Solid  LW2",      "Solid",  2,    "Set pattern=Solid and weight=2"),
            ("Weight 1 Only",   None,     1,    "Set weight=1, leave pattern unchanged"),
        ]

        x = 110
        for text, pat, wt, tip in presets:
            b = self._btn(text, Point(x, 50), Size(110, 26))
            b.Tag = (pat, wt)
            b.Click += self._apply_preset
            self._tooltip.SetToolTip(b, tip)
            panel.Controls.Add(b)
            x += 116

        for ctrl in [lbl_cad, self.cmb_cad, lbl_lf, self.txt_filter,
                     btn_clear_f, btn_sel_all, lbl_pre]:
            panel.Controls.Add(ctrl)

        return panel

    # --- Grid panel --------------------------------------------------

    def _create_grid_panel(self):
        panel = Panel()

        self.grid = DataGridView()
        self.grid.Dock = DockStyle.Fill
        self.grid.AutoGenerateColumns = False
        self.grid.SelectionMode = DataGridViewSelectionMode.FullRowSelect
        self.grid.MultiSelect = True
        self.grid.AllowUserToAddRows = False
        self.grid.AllowUserToDeleteRows = False
        self.grid.RowHeadersVisible = False
        self.grid.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill
        self.grid.Font = FNT_DEFAULT
        self.grid.GridColor = Color.FromArgb(200, 205, 215)
        self.grid.BackgroundColor = Color.White
        self.grid.BorderStyle = BorderStyle.None
        self.grid.ColumnHeadersDefaultCellStyle.Font = FNT_BOLD
        self.grid.ColumnHeadersDefaultCellStyle.BackColor = Color.FromArgb(220, 225, 235)
        self.grid.ColumnHeadersDefaultCellStyle.ForeColor = Color.FromArgb(30, 30, 50)
        self.grid.EnableHeadersVisualStyles = False
        self.grid.ColumnHeadersHeight = 28
        self.grid.AllowUserToResizeRows = False
        self.grid.RowTemplate.Height = 24   

        from System.Windows.Forms import DataGridViewContentAlignment as Align

        def _col(header, prop, fill, readonly=True, align=Align.MiddleLeft):
            c = DataGridViewTextBoxColumn()
            c.HeaderText = header
            c.DataPropertyName = prop
            c.FillWeight = fill
            c.ReadOnly = readonly
            c.DefaultCellStyle.Alignment = align
            c.HeaderCell.Style.Alignment = align
            return c

        self.grid.Columns.Add(_col("Name CAD File",     "cad_name",        25))
        self.grid.Columns.Add(_col("Layer Name",         "name",            25))
        self.grid.Columns.Add(_col("Current Lineweight", "current_weight",  12, align=Align.MiddleCenter))
        self.grid.Columns.Add(_col("Current Linestyle",  "current_pattern", 18, align=Align.MiddleCenter))

        col_changes = DataGridViewTextBoxColumn()
        col_changes.HeaderText = "Pending Changes"
        col_changes.Name = "col_changes"
        col_changes.FillWeight = 20
        col_changes.ReadOnly = True
        self.grid.Columns.Add(col_changes)

        self.grid.SelectionChanged += self._on_selection_changed

        # Info bar
        self.lbl_info = Label()
        self.lbl_info.Dock = DockStyle.Top
        self.lbl_info.Height = 26
        self.lbl_info.Padding = Padding(6, 5, 0, 0)
        self.lbl_info.Font = FNT_DEFAULT
        self.lbl_info.BackColor = Color.FromArgb(235, 238, 245)

        panel.Controls.Add(self.grid)
        panel.Controls.Add(self.lbl_info)
        return panel

    # --- Batch panel -------------------------------------------------

    def _create_batch_panel(self):
        """
        Redesigned: no checkboxes.
        Line Weight group and Line Pattern group each have a ComboBox + Apply button.
        An 'Apply Both' button applies both simultaneously.
        All buttons are disabled when nothing is selected.
        """
        panel = Panel()
        panel.BackColor = CLR_BG_BATCH

        self.lbl_batch = Label()
        self.lbl_batch.Text = "BATCH EDIT  —  0 rows selected"
        self.lbl_batch.Location = Point(10, 8)
        self.lbl_batch.Font = FNT_BOLD
        self.lbl_batch.AutoSize = True
        self.lbl_batch.ForeColor = Color.FromArgb(50, 50, 80)

        # ── Line Weight group ────────────────────────────────────────
        grp_lw = GroupBox()
        grp_lw.Text = "Line Weight"
        grp_lw.Location = Point(10, 30)
        grp_lw.Size = Size(210, 68)
        grp_lw.Font = FNT_BOLD

        self.cmb_lw = ComboBox()
        self.cmb_lw.Location = Point(10, 28)
        self.cmb_lw.Size = Size(70, 22)
        self.cmb_lw.DropDownStyle = ComboBoxStyle.DropDownList
        self.cmb_lw.Font = FNT_DEFAULT
        for i in range(1, 17):
            self.cmb_lw.Items.Add(str(i))
        self.cmb_lw.SelectedIndex = 0

        self.btn_apply_lw = self._btn("Apply Weight", Point(90, 26), Size(108, 26))
        self.btn_apply_lw.Click += lambda s, e: self._apply_batch(apply_weight=True, apply_pattern=False)
        self.btn_apply_lw.Enabled = False
        self._tooltip.SetToolTip(self.btn_apply_lw,
            "Apply the chosen line weight to all selected rows")

        grp_lw.Controls.Add(self.cmb_lw)
        grp_lw.Controls.Add(self.btn_apply_lw)

        # ── Line Pattern group ───────────────────────────────────────
        grp_lp = GroupBox()
        grp_lp.Text = "Line Pattern"
        grp_lp.Location = Point(230, 30)
        grp_lp.Size = Size(300, 68)
        grp_lp.Font = FNT_BOLD

        self.cmb_lp = ComboBox()
        self.cmb_lp.Location = Point(10, 28)
        self.cmb_lp.Size = Size(160, 22)
        self.cmb_lp.DropDownStyle = ComboBoxStyle.DropDownList
        self.cmb_lp.Font = FNT_DEFAULT
        for p in self.line_patterns:
            self.cmb_lp.Items.Add(p)
        if self.cmb_lp.Items.Count > 0:
            self.cmb_lp.SelectedIndex = 0

        self.btn_apply_lp = self._btn("Apply Pattern", Point(180, 26), Size(108, 26))
        self.btn_apply_lp.Click += lambda s, e: self._apply_batch(apply_weight=False, apply_pattern=True)
        self.btn_apply_lp.Enabled = False
        self._tooltip.SetToolTip(self.btn_apply_lp,
            "Apply the chosen line pattern to all selected rows")

        grp_lp.Controls.Add(self.cmb_lp)
        grp_lp.Controls.Add(self.btn_apply_lp)

        # ── Apply Both ───────────────────────────────────────────────
        self.btn_both = Button()
        self.btn_both.Text = "Apply Both"
        self.btn_both.Location = Point(545, 48)
        self.btn_both.Size = Size(120, 36)
        self.btn_both.Font = FNT_BOLD
        self.btn_both.FlatStyle = FlatStyle.Flat
        self.btn_both.BackColor = CLR_APPLY_BOTH
        self.btn_both.ForeColor = Color.White
        self.btn_both.FlatAppearance.BorderSize = 0
        self.btn_both.Enabled = False
        self.btn_both.Click += lambda s, e: self._apply_batch(apply_weight=True, apply_pattern=True)
        self._tooltip.SetToolTip(self.btn_both,
            "Apply both the chosen line weight AND pattern to all selected rows")

        panel.Controls.Add(self.lbl_batch)
        panel.Controls.Add(grp_lw)
        panel.Controls.Add(grp_lp)
        panel.Controls.Add(self.btn_both)
        return panel

    # --- Button panel ------------------------------------------------

    def _create_button_panel(self):
        panel = Panel()
        panel.BackColor = CLR_BG_BOTTOM

        btn_clear_all = self._btn("↩ Clear All Changes", Point(10, 11), Size(160, 32))
        btn_clear_all.Click += self._clear_all_changes
        self._tooltip.SetToolTip(btn_clear_all, "Remove all pending changes without applying them")

        btn_cancel = self._btn("Close", Point(560, 11), Size(100, 32))
        btn_cancel.Click += lambda s, e: self.Close()

        self.btn_apply = Button()
        self.btn_apply.Text = "Apply All Pending Changes  (0)"
        self.btn_apply.Location = Point(670, 7)
        self.btn_apply.Size = Size(360, 42)
        self.btn_apply.Font = FNT_BIG_BTN
        self.btn_apply.FlatStyle = FlatStyle.Flat
        self.btn_apply.BackColor = CLR_APPLY_DIS
        self.btn_apply.ForeColor = Color.White
        self.btn_apply.FlatAppearance.BorderSize = 0
        self.btn_apply.Enabled = False
        self.btn_apply.Click += self._apply_all_changes
        self._tooltip.SetToolTip(self.btn_apply,
            "Write all pending changes into Revit in a single transaction")

        panel.Controls.Add(btn_clear_all)
        panel.Controls.Add(btn_cancel)
        panel.Controls.Add(self.btn_apply)
        return panel

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def _lbl(self, text, loc, bold=False):
        l = Label()
        l.Text = text
        l.Location = loc
        l.AutoSize = True
        l.Font = FNT_BOLD if bold else FNT_DEFAULT
        return l

    def _btn(self, text, loc, size):
        b = Button()
        b.Text = text
        b.Location = loc
        b.Size = size
        b.Font = FNT_DEFAULT
        b.FlatStyle = FlatStyle.Flat
        b.BackColor = Color.FromArgb(220, 225, 235)
        b.FlatAppearance.BorderColor = Color.FromArgb(170, 180, 200)
        b.FlatAppearance.BorderSize = 1
        return b

    # ------------------------------------------------------------------
    # DATA / GRID
    # ------------------------------------------------------------------

    def _populate_grid(self):
        from System.Collections.Generic import List
        from System.ComponentModel import BindingList as BL

        lst = List[object]()
        for layer in self.filtered_layers:
            lst.Add(layer)
        self.grid.DataSource = BL[object](lst)
        self._update_changes_display()

    def _on_filter_changed(self, sender, e):
        cad_filter  = str(self.cmb_cad.SelectedItem)
        text_filter = self.txt_filter.Text.lower().strip()

        self.filtered_layers = []
        for layer in self.all_layers:
            if cad_filter != "All CAD Files" and layer.cad_name != cad_filter:
                continue
            if text_filter and text_filter not in layer.name.lower():
                continue
            self.filtered_layers.append(layer)

        self._populate_grid()
        self._update_info_label()

    def _clear_filters(self, sender, e):
        self.txt_filter.Text = ""
        self.cmb_cad.SelectedIndex = 0

    def _select_all_visible(self, sender, e):
        self.grid.SelectAll()

    def _on_selection_changed(self, sender, e):
        count = self.grid.SelectedRows.Count
        self.lbl_batch.Text = "BATCH EDIT  —  {} row{} selected".format(
            count, "s" if count != 1 else "")
        has_sel = count > 0
        self.btn_apply_lw.Enabled = has_sel
        self.btn_apply_lp.Enabled = has_sel
        self.btn_both.Enabled = has_sel

    # ------------------------------------------------------------------
    # PRESET & BATCH
    # ------------------------------------------------------------------

    def _apply_preset(self, sender, e):
        if self.grid.SelectedRows.Count == 0:
            forms.alert("Select at least one layer first.", title="No Selection")
            return
        pattern, weight = sender.Tag
        for row in self.grid.SelectedRows:
            layer = self.filtered_layers[row.Index]
            if weight is not None:
                layer.new_weight = weight
            if pattern is not None:
                layer.new_pattern = pattern
        self._update_changes_display()

    def _apply_batch(self, apply_weight=True, apply_pattern=True):
        """
        Directly apply selections from ComboBoxes to selected rows.
        No checkbox needed — button click is the confirmation.
        """
        if self.grid.SelectedRows.Count == 0:
            forms.alert("Select at least one layer first.", title="No Selection")
            return

        for row in self.grid.SelectedRows:
            layer = self.filtered_layers[row.Index]
            if apply_weight:
                layer.new_weight = int(self.cmb_lw.SelectedItem)
            if apply_pattern and self.cmb_lp.Items.Count > 0:
                layer.new_pattern = str(self.cmb_lp.SelectedItem)

        self._update_changes_display()

    # ------------------------------------------------------------------
    # DISPLAY UPDATES
    # ------------------------------------------------------------------

    def _update_info_label(self):
        pending = sum(1 for l in self.all_layers if l.has_changes())
        shown   = len(self.filtered_layers)
        total   = len(self.all_layers)

        if pending > 0:
            self.lbl_info.Text = (
                "Showing {}/{} layers   •   "
                "⚑ {} pending change{} — click 'Apply All Pending Changes' to commit".format(
                    shown, total, pending, "s" if pending != 1 else ""))
            self.lbl_info.ForeColor = Color.FromArgb(140, 20, 20)
            self.lbl_info.Font = FNT_BOLD
            self.lbl_info.BackColor = Color.FromArgb(255, 235, 235)
        else:
            self.lbl_info.Text = "Showing {}/{} layers   •   Select rows to batch edit".format(
                shown, total)
            self.lbl_info.ForeColor = Color.FromArgb(50, 50, 80)
            self.lbl_info.Font = FNT_DEFAULT
            self.lbl_info.BackColor = Color.FromArgb(235, 238, 245)

    def _update_changes_display(self):
        changes_count = sum(1 for l in self.all_layers if l.has_changes())

        for i, row in enumerate(self.grid.Rows):
            if i < len(self.filtered_layers):
                layer = self.filtered_layers[i]
                row.Cells["col_changes"].Value = layer.get_changes_text()

                if layer.has_changes():
                    # Blue tint — readable for colour-blind users
                    row.DefaultCellStyle.BackColor = CLR_PENDING_ROW
                    row.DefaultCellStyle.ForeColor = CLR_PENDING_TXT
                    row.DefaultCellStyle.Font = FNT_BOLD
                else:
                    row.DefaultCellStyle.BackColor = Color.White
                    row.DefaultCellStyle.ForeColor = Color.FromArgb(30, 30, 30)
                    row.DefaultCellStyle.Font = FNT_DEFAULT

        # Apply button state
        self.btn_apply.Text = "Apply All Pending Changes  ({})".format(changes_count)
        self.btn_apply.Enabled = changes_count > 0
        self.btn_apply.BackColor = CLR_APPLY_BG if changes_count > 0 else CLR_APPLY_DIS

        self._update_info_label()
        self.grid.Refresh()

    # ------------------------------------------------------------------
    # CLEAR & APPLY
    # ------------------------------------------------------------------

    def _clear_all_changes(self, sender, e):
        for layer in self.all_layers:
            layer.clear_changes()
        self._update_changes_display()

    def _apply_all_changes(self, sender, e):
        layers_with_changes = [l for l in self.all_layers if l.has_changes()]
        if not layers_with_changes:
            return

        result = forms.alert(
            "Apply {} pending change{}?".format(
                len(layers_with_changes),
                "s" if len(layers_with_changes) != 1 else ""),
            title="Confirm",
            ok=False, yes=True, no=True
        )
        if not result:
            return

        success_count = 0
        with revit.Transaction("Apply CAD Layer Changes"):
            for layer in layers_with_changes:
                if layer.apply_changes():
                    success_count += 1
                layer.clear_changes()

        self._update_changes_display()

        forms.alert(
            "Applied {} of {} change{} successfully.".format(
                success_count,
                len(layers_with_changes),
                "s" if len(layers_with_changes) != 1 else ""),
            title="Done"
        )
        # ✅ Form stays open — user can continue editing without reopening the tool


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    cad_data = get_cad_files()
    if not cad_data:
        forms.alert("No linked CAD files found in the document.", title="No CAD Files")
        return
    form = CADLayerManagerForm(cad_data)
    form.ShowDialog()


if __name__ == '__main__':
    main()