# -*- coding: utf-8 -*-
'''
Version: 2.0
Date    = 21.06.2026
_____________________________________________________________________
Description:
Generate family types by duplicating from a preselected family instance, then
set type parameters from a CSV file. Works directly in project documents — no
need to open the family editor.

The tool supports two naming modes: single column (type name from one CSV field)
or combined format string (e.g., "{Width}x{Height}" from multiple columns).
Numeric values are assumed to be MILLIMETERS and converted automatically.
_____________________________________________________________________
How-to:
1. Preselect a family instance in the project
2. Click the button and select a CSV file
3. Choose naming method: Single Column or Combined (Format String)
   - Single Column: select which CSV column contains the type name
   - Combined: build a format string like "{Size} - {b}x{h}"
4. Map CSV columns to family type parameters (or skip columns)
5. Review the mapping summary and confirm
6. Types are created and parameters set — existing types are skipped
_____________________________________________________
Last update:
- 21.06.2026 - 2.0 Full rewrite with WPF UI, combined name builder, manual parameter matching
- Previous versions: legacy single-column only approach
_____________________________________________________________________
Author:  PrasKaa
'''

__title__ = "Family Type Generator\n(Project Mode)"

import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')
clr.AddReference('PresentationCore')
clr.AddReference('PresentationFramework')
clr.AddReference('WindowsBase')
clr.AddReference('System')

# ── WPF Imports ───────────────────────────────────────────────────────────────
from System.Windows.Forms import OpenFileDialog, DialogResult
from System.Windows import (
    ResizeMode, Window, WindowStartupLocation,
    HorizontalAlignment, VerticalAlignment,
    Thickness, GridLength, GridUnitType, FontWeights,
)
from System.Windows.Controls import (
    StackPanel, Grid, ColumnDefinition, RowDefinition,
    Label, ComboBox, ComboBoxItem, Button, ScrollViewer,
    TextBlock, TextBox, DockPanel, Dock, Separator,
    Orientation, ScrollBarVisibility, ListBox, ListBoxItem,
    Border, GroupBox,
)
from System.Windows import TextWrapping, TextAlignment
from System.Windows.Media import SolidColorBrush, Color as WpfColor

import os
import csv
import math

# ── pyRevit ───────────────────────────────────────────────────────────────────
from pyrevit import forms, script
from pyrevit.revit import doc, uidoc

# ── Revit API ─────────────────────────────────────────────────────────────────
from Autodesk.Revit.DB import (
    Transaction,
    StorageType,
    TransactionStatus,
    BuiltInParameter,
    FamilySymbol,
)


# =============================================================================
# UNIT CONVERSION  (mm → Revit internal feet)
# =============================================================================

MM_TO_FEET = 1.0 / 304.8


def mm_to_internal(value_mm):
    return float(value_mm) * MM_TO_FEET


def deg_to_rad(value_deg):
    return float(value_deg) * (math.pi / 180.0)


def get_spec_category(param):
    """
    Returns: 'length' | 'angle' | 'area' | 'volume' | 'number' | 'integer' | 'string'
    Works on both FamilyParameter (family doc) and Parameter (project doc).
    """
    st = param.StorageType
    if st == StorageType.String:
        return 'string'
    if st == StorageType.Integer:
        return 'integer'
    try:
        spec_id = param.Definition.GetDataType().TypeId.lower()
        if 'length' in spec_id:
            return 'length'
        if 'angle' in spec_id:
            return 'angle'
        if 'area' in spec_id:
            return 'area'
        if 'volume' in spec_id:
            return 'volume'
    except Exception:
        pass
    # Safest default for Double in structural families
    return 'length'


def convert_csv_value(raw_str, spec_category):
    """Convert CSV string → Python value ready for Revit internal unit."""
    raw_str = raw_str.strip()
    if spec_category == 'string':
        return raw_str
    if spec_category == 'integer':
        return int(float(raw_str))
    numeric = float(raw_str)
    if spec_category == 'length':
        return mm_to_internal(numeric)
    if spec_category == 'angle':
        return deg_to_rad(numeric)
    if spec_category == 'area':
        return numeric * (MM_TO_FEET ** 2)
    if spec_category == 'volume':
        return numeric * (MM_TO_FEET ** 3)
    return numeric


# =============================================================================
# PROJECT-DOC TYPE PARAMETER READER
# =============================================================================

# Built-in type parameters injected manually because they don't appear in
# the normal Parameters iteration or are otherwise tricky to detect.
# We store BIP here and resolve the actual Parameter object per-type at write time.
BUILTIN_TYPE_PARAMS = {
    "Type Mark": BuiltInParameter.ALL_MODEL_TYPE_MARK,
    # Add more BIPs here if needed:
    # "Description": BuiltInParameter.ALL_MODEL_DESCRIPTION,
    # "Keynote":     BuiltInParameter.KEYNOTE_PARAM,
}


def get_writable_type_parameters(family_symbol):
    """
    Read writable type parameters from a FamilySymbol (project doc).

    Returns dict:
        { param_name: { 'storage_type': ST, 'spec_category': str, 'source': str,
                        'bip': BIP or None } }

    source values:
        'element'  — accessed via family_symbol.LookupParameter(name)
        'builtin'  — accessed via family_symbol.get_Parameter(bip)
    """
    result = {}

    # Pass 1 — iterate the FamilySymbol's own Parameters collection
    for p in family_symbol.Parameters:
        if p.IsReadOnly:
            continue
        defn = p.Definition
        if defn is None:
            continue
        name = defn.Name
        if not name:
            continue
        result[name] = {
            'storage_type': p.StorageType,
            'spec_category': get_spec_category(p),
            'source': 'element',
            'bip': None,
        }

    # Pass 2 — inject known built-in type parameters
    for name, bip in BUILTIN_TYPE_PARAMS.items():
        if name not in result:
            # Probe whether this BIP exists on the symbol
            probe = family_symbol.get_Parameter(bip)
            if probe is not None:
                result[name] = {
                    'storage_type': probe.StorageType,
                    'spec_category': get_spec_category(probe),
                    'source': 'builtin',
                    'bip': bip,
                }

    return result


def set_type_parameter(family_symbol, param_name, pinfo, value):
    """
    Write a value to a type parameter on a FamilySymbol.
    Returns (True, '') or (False, error_msg).
    """
    st = pinfo['storage_type']
    source = pinfo['source']

    try:
        if source == 'builtin':
            p = family_symbol.get_Parameter(pinfo['bip'])
        else:
            p = family_symbol.LookupParameter(param_name)

        if p is None:
            return False, "Parameter not found on new type"
        if p.IsReadOnly:
            return False, "Parameter is read-only"

        if st == StorageType.Double:
            p.Set(float(value))
        elif st == StorageType.Integer:
            p.Set(int(value))
        elif st == StorageType.String:
            p.Set(str(value))
        else:
            return False, "Unsupported StorageType: {}".format(st)

        return True, ''

    except Exception as e:
        return False, str(e)


# =============================================================================
# SHARED WPF HELPERS  (unchanged from v1)
# =============================================================================

def _lbl(text, bold=False, size=12, wrap=False):
    lbl = Label()
    lbl.Content = text
    lbl.FontSize = size
    lbl.VerticalAlignment = VerticalAlignment.Center
    if bold:
        lbl.FontWeight = FontWeights.Bold
    return lbl


def _tb(text, bold=False, size=12, wrap=False):
    tb = TextBlock()
    tb.Text = text
    tb.FontSize = size
    tb.VerticalAlignment = VerticalAlignment.Center
    if bold:
        tb.FontWeight = FontWeights.Bold
    if wrap:
        tb.TextWrapping = TextWrapping.Wrap
    return tb


def _col(grid, index, element):
    Grid.SetColumn(element, index)
    grid.Children.Add(element)


def _row_grid(*widths):
    g = Grid()
    g.Margin = Thickness(0, 1, 0, 1)
    for w in widths:
        cd = ColumnDefinition()
        if w == '*':
            cd.Width = GridLength(1, GridUnitType.Star)
        elif w == 'auto':
            cd.Width = GridLength.Auto
        else:
            cd.Width = GridLength(w)
        g.ColumnDefinitions.Add(cd)
    return g


# =============================================================================
# COMBINED NAME BUILDER WINDOW  (unchanged from v1)
# =============================================================================

class CombinedNameWindow(Window):
    """Build a format string like '{Size} - {b}x{h}' using CSV column placeholders."""

    def __init__(self, csv_headers, csv_rows):
        self.csv_headers = csv_headers
        self.preview_rows = csv_rows[:8]
        self.format_string = None
        self._setup_window()
        self._build_ui()

    def _setup_window(self):
        self.Title = "Combined Type Name Builder"
        self.Width = 680
        self.Height = 520
        self.MinWidth = 520
        self.MinHeight = 380
        self.WindowStartupLocation = WindowStartupLocation.CenterScreen
        self.ResizeMode = ResizeMode.CanResizeWithGrip

    def _build_ui(self):
        root = DockPanel()
        root.Margin = Thickness(12)
        self.Content = root

        hdr = StackPanel()
        hdr.Margin = Thickness(0, 0, 0, 10)
        DockPanel.SetDock(hdr, Dock.Top)
        root.Children.Add(hdr)
        hdr.Children.Add(_tb("Combined Type Name Builder", bold=True, size=15))
        how_to = _tb(
            "1. Double-click a column name to insert its placeholder.\n"
            "2. Type separators or text between placeholders.\n"
            "   Example:  {Size} - {b}x{h}  or  L{b}x{t1}",
            size=11, wrap=True
        )
        how_to.Foreground = SolidColorBrush(WpfColor.FromRgb(80, 80, 80))
        how_to.Margin = Thickness(0, 4, 0, 0)
        hdr.Children.Add(how_to)

        fmt_row = _row_grid('auto', '*')
        fmt_row.Margin = Thickness(0, 6, 0, 4)
        DockPanel.SetDock(fmt_row, Dock.Top)
        root.Children.Add(fmt_row)
        _col(fmt_row, 0, _lbl("Format:", bold=True, size=12))
        self._fmt_tb = TextBox()
        self._fmt_tb.FontSize = 12
        self._fmt_tb.Height = 26
        self._fmt_tb.Margin = Thickness(6, 0, 0, 0)
        self._fmt_tb.VerticalContentAlignment = VerticalAlignment.Center
        self._fmt_tb.TextChanged += self._on_format_changed
        _col(fmt_row, 1, self._fmt_tb)

        self._val_tb = TextBlock()
        self._val_tb.FontSize = 11
        self._val_tb.Margin = Thickness(0, 2, 0, 6)
        self._val_tb.Text = "Enter a format string above."
        self._val_tb.Foreground = SolidColorBrush(WpfColor.FromRgb(120, 120, 120))
        DockPanel.SetDock(self._val_tb, Dock.Top)
        root.Children.Add(self._val_tb)

        btn_row = StackPanel()
        btn_row.Orientation = Orientation.Horizontal
        btn_row.HorizontalAlignment = HorizontalAlignment.Right
        btn_row.Margin = Thickness(0, 8, 0, 0)
        DockPanel.SetDock(btn_row, Dock.Bottom)
        root.Children.Add(btn_row)
        cancel_btn = Button()
        cancel_btn.Content = "  Cancel  "
        cancel_btn.Height = 28
        cancel_btn.Margin = Thickness(0, 0, 8, 0)
        cancel_btn.Click += self._on_cancel
        btn_row.Children.Add(cancel_btn)
        apply_btn = Button()
        apply_btn.Content = "  Apply Format  "
        apply_btn.Height = 28
        apply_btn.Click += self._on_apply
        btn_row.Children.Add(apply_btn)

        body = Grid()
        body.ColumnDefinitions.Add(ColumnDefinition())
        body.ColumnDefinitions[0].Width = GridLength(190)
        body.ColumnDefinitions.Add(ColumnDefinition())
        body.ColumnDefinitions[1].Width = GridLength(1, GridUnitType.Star)
        root.Children.Add(body)

        left = GroupBox()
        left.Header = "Available Columns (double-click)"
        left.Margin = Thickness(0, 0, 6, 0)
        Grid.SetColumn(left, 0)
        body.Children.Add(left)
        self._col_lb = ListBox()
        self._col_lb.FontSize = 11
        self._col_lb.MouseDoubleClick += self._on_col_dblclick
        for h in self.csv_headers:
            item = ListBoxItem()
            item.Content = "{" + h + "}"
            self._col_lb.Items.Add(item)
        left.Content = self._col_lb

        right = GroupBox()
        right.Header = "Preview (first 8 rows)"
        Grid.SetColumn(right, 1)
        body.Children.Add(right)
        self._preview_panel = StackPanel()
        self._preview_panel.Margin = Thickness(4)
        scroll = ScrollViewer()
        scroll.VerticalScrollBarVisibility = ScrollBarVisibility.Auto
        scroll.Content = self._preview_panel
        right.Content = scroll
        self._refresh_preview()

    def _generate_name(self, fmt, row):
        result = fmt
        for h in self.csv_headers:
            result = result.replace("{" + h + "}", str(row.get(h, "")).strip())
        return result

    def _validate(self, fmt):
        if not fmt.strip():
            return False, "Format string is empty."
        has_placeholder = any(("{" + h + "}") in fmt for h in self.csv_headers)
        if not has_placeholder:
            return False, "No valid placeholder found. Use {ColumnName} syntax."
        return True, "OK"

    def _refresh_preview(self):
        self._preview_panel.Children.Clear()
        fmt = self._fmt_tb.Text if hasattr(self, '_fmt_tb') else ""
        for row in self.preview_rows:
            name = self._generate_name(fmt, row) if fmt.strip() else "(enter format above)"
            tb = TextBlock()
            tb.Text = name
            tb.FontSize = 11
            tb.Margin = Thickness(0, 1, 0, 1)
            self._preview_panel.Children.Add(tb)

    def _on_col_dblclick(self, sender, args):
        sel = self._col_lb.SelectedItem
        if sel is None:
            return
        placeholder = str(sel.Content)
        pos = self._fmt_tb.SelectionStart
        current = self._fmt_tb.Text or ""
        self._fmt_tb.Text = current[:pos] + placeholder + current[pos:]
        self._fmt_tb.SelectionStart = pos + len(placeholder)
        self._fmt_tb.Focus()

    def _on_format_changed(self, sender, args):
        fmt = self._fmt_tb.Text or ""
        valid, msg = self._validate(fmt)
        if valid:
            self._val_tb.Text = u"\u2705 " + msg
            self._val_tb.Foreground = SolidColorBrush(WpfColor.FromRgb(0, 128, 0))
        else:
            self._val_tb.Text = u"\u274C " + msg
            self._val_tb.Foreground = SolidColorBrush(WpfColor.FromRgb(180, 0, 0))
        self._refresh_preview()

    def _on_apply(self, sender, args):
        fmt = self._fmt_tb.Text or ""
        valid, msg = self._validate(fmt)
        if not valid:
            forms.alert(msg, title="Invalid Format")
            return
        self.format_string = fmt
        self.Close()

    def _on_cancel(self, sender, args):
        self.format_string = None
        self.Close()

    def show_dialog(self):
        self.ShowDialog()
        return self.format_string


# =============================================================================
# MANUAL PARAMETER MATCHING WINDOW  (adapted for project-doc param dict)
# =============================================================================

class ParameterMatchingWindow(Window):
    """
    One row per CSV column (name column excluded).
    Each row has a ComboBox listing all writable type parameters of the source type.
    Default is always '-- Skip --'.
    """

    SKIP = "-- Skip --"

    def __init__(self, csv_headers, name_column, family_params, sample_row):
        exclude = [name_column] if name_column else []
        self.data_headers = [h for h in csv_headers if h not in exclude]
        self.family_params = family_params
        self.sample_row = sample_row
        self.result_mapping = None
        self._combos = {}
        self._setup_window()
        self._build_ui()

    def _setup_window(self):
        self.Title = "Parameter Matching — Manual Assignment"
        self.Width = 740
        self.MinWidth = 580
        self.MinHeight = 260
        self.WindowStartupLocation = WindowStartupLocation.CenterScreen
        self.ResizeMode = ResizeMode.CanResizeWithGrip

    def _build_ui(self):
        root = DockPanel()
        root.Margin = Thickness(12)
        self.Content = root

        hdr = StackPanel()
        hdr.Margin = Thickness(0, 0, 0, 8)
        DockPanel.SetDock(hdr, Dock.Top)
        root.Children.Add(hdr)
        hdr.Children.Add(_tb("Manual Parameter Matching", bold=True, size=15))
        hint = _tb(
            "Assign each CSV column to a type parameter of the source family.\n"
            "Leave '-- Skip --' to ignore that column.\n"
            "Numeric values are assumed to be MILLIMETERS and will be converted to Revit internal feet.",
            size=11, wrap=True
        )
        hint.Foreground = SolidColorBrush(WpfColor.FromRgb(90, 90, 90))
        hint.Margin = Thickness(0, 4, 0, 0)
        hdr.Children.Add(hint)

        btn_row = StackPanel()
        btn_row.Orientation = Orientation.Horizontal
        btn_row.HorizontalAlignment = HorizontalAlignment.Right
        btn_row.Margin = Thickness(0, 10, 0, 0)
        DockPanel.SetDock(btn_row, Dock.Bottom)
        root.Children.Add(btn_row)
        cancel_btn = Button()
        cancel_btn.Content = "  Cancel  "
        cancel_btn.Height = 28
        cancel_btn.Margin = Thickness(0, 0, 8, 0)
        cancel_btn.Click += self._on_cancel
        btn_row.Children.Add(cancel_btn)
        ok_btn = Button()
        ok_btn.Content = "  Apply Matching  "
        ok_btn.Height = 28
        ok_btn.Click += self._on_apply
        btn_row.Children.Add(ok_btn)

        scroll = ScrollViewer()
        scroll.VerticalScrollBarVisibility = ScrollBarVisibility.Auto
        root.Children.Add(scroll)

        inner = StackPanel()
        inner.Margin = Thickness(0, 2, 4, 2)
        scroll.Content = inner

        h_row = _row_grid(220, 24, '*', 180)
        _col(h_row, 0, _lbl("CSV Column", bold=True, size=11))
        _col(h_row, 2, _lbl("Type Parameter", bold=True, size=11))
        _col(h_row, 3, _lbl("Sample Value", bold=True, size=11))
        inner.Children.Add(h_row)

        sep = Separator()
        sep.Margin = Thickness(0, 2, 0, 6)
        inner.Children.Add(sep)

        param_choices = [self.SKIP] + sorted(self.family_params.keys())

        for csv_h in self.data_headers:
            row = _row_grid(220, 24, '*', 180)
            _col(row, 0, _lbl(csv_h, size=12))
            arr = _lbl(u"\u2192", size=12)
            arr.HorizontalAlignment = HorizontalAlignment.Center
            _col(row, 1, arr)

            combo = ComboBox()
            combo.FontSize = 11
            combo.Height = 24
            combo.Margin = Thickness(4, 0, 4, 0)
            combo.VerticalAlignment = VerticalAlignment.Center
            for pname in param_choices:
                item = ComboBoxItem()
                item.Content = pname
                combo.Items.Add(item)
            combo.SelectedIndex = 0
            _col(row, 2, combo)
            self._combos[csv_h] = combo

            raw = str(self.sample_row.get(csv_h, "")).strip()
            display = (raw[:35] + u"\u2026") if len(raw) > 35 else raw
            s_lbl = _lbl(display, size=10)
            s_lbl.Foreground = SolidColorBrush(WpfColor.FromRgb(110, 110, 110))
            _col(row, 3, s_lbl)

            inner.Children.Add(row)

        self.Height = min(180 + len(self.data_headers) * 34 + 80, 720)

    def _on_apply(self, sender, args):
        mapping = {}
        for csv_h, combo in self._combos.items():
            sel = combo.SelectedItem
            if sel is None or str(sel.Content) == self.SKIP:
                mapping[csv_h] = None
            else:
                mapping[csv_h] = str(sel.Content)
        self.result_mapping = mapping
        self.Close()

    def _on_cancel(self, sender, args):
        self.result_mapping = None
        self.Close()

    def show_dialog(self):
        self.ShowDialog()
        return self.result_mapping


# =============================================================================
# CSV READER
# =============================================================================

def read_csv(csv_path):
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        rows = list(reader)
    return headers, rows


# =============================================================================
# MAIN GENERATOR — PROJECT MODE
# =============================================================================

class FamilyTypeGenerator:

    def __init__(self, source_symbol):
        """
        source_symbol : FamilySymbol — the type of the preselected instance.
        All new types are duplicated from this symbol.
        """
        self.source_symbol = source_symbol
        self.output = script.get_output()

    # ── public entry point ────────────────────────────────────────────────────

    # ── public entry point ────────────────────────────────────────────────────────────────────────────

    def run(self, csv_path):
        out = self.output

        # ── Read CSV ────────────────────────────────────────────────────────────────────
        try:
            headers, rows = read_csv(csv_path)
        except Exception as e:
            forms.alert("Error reading CSV:\n{}".format(e), title="CSV Error")
            return
        if not headers:
            forms.alert("CSV has no headers.", title="CSV Error")
            return
        if not rows:
            forms.alert("CSV has no data rows.", title="CSV Error")
            return

        # ── Step 1: Naming method ─────────────────────────────────────────────────────
        naming_choice = forms.CommandSwitchWindow.show(
            ["Single Column", "Combined (Format String)"],
            message="How should type names be generated?",
            title="Type Naming Method",
        )
        if not naming_choice:
            out.print_md("\u274c Cancelled.")
            return

        name_col = None
        format_string = None

        if naming_choice == "Single Column":
            name_col = forms.CommandSwitchWindow.show(
                headers,
                message="Which column contains the TYPE NAME?",
                title="Select Name Column",
            )
            if not name_col:
                out.print_md("\u274c Cancelled.")
                return
        else:
            win = CombinedNameWindow(headers, rows)
            format_string = win.show_dialog()
            if format_string is None:
                out.print_md("\u274c Cancelled.")
                return

        # ── Step 2: Read type parameters ──────────────────────────────────────────────────────────────────────
        from Autodesk.Revit.DB import Element as _Element
        sym_name = _Element.Name.GetValue(self.source_symbol)

        family_params = get_writable_type_parameters(self.source_symbol)
        if not family_params:
            forms.alert("No writable type parameters found on source type.", title="No Parameters")
            return

        # ── Step 3: Manual matching UI ─────────────────────────────────────────────────────────────────
        win = ParameterMatchingWindow(
            csv_headers=headers,
            name_column=name_col,
            family_params=family_params,
            sample_row=rows[0],
        )
        mapping = win.show_dialog()
        if mapping is None:
            out.print_md("\u274c Cancelled by user.")
            return

        active = {k: v for k, v in mapping.items() if v is not None}
        if not active:
            forms.alert("No columns mapped. Nothing to do.", title="No Mapping")
            return

        # ── Setup summary: compact one-shot print ─────────────────────────────────────────────
        name_desc = (
            "Column: <b>{}</b>".format(name_col) if name_col
            else "Format: <code>{}</code>".format(format_string)
        )
        mapping_rows_html = "".join(
            "<tr>"
            "<td style='padding:1px 8px 1px 0'>{}</td>"
            "<td style='padding:1px 4px;color:#999'>→</td>"
            "<td style='padding:1px 8px'><b>{}</b></td>"
            "<td style='padding:1px 8px;color:#888;font-style:italic'>{}</td>"
            "</tr>".format(csv_h, param_n, family_params[param_n]["spec_category"])
            for csv_h, param_n in active.items()
        )
        out.print_html(
            "<div style='font-size:12px;line-height:1.6;margin-bottom:4px'>"
            "<b>Source:</b> {sym}"
            " &nbsp;·&nbsp; <b>CSV:</b> {nr} rows, {nc} cols"
            " &nbsp;·&nbsp; <b>Naming:</b> {name}"
            "</div>"
            "<details open>"
            "<summary style='font-size:11px;cursor:pointer;color:#555'>"
            "Mappings ({n} active)</summary>"
            "<table style='font-size:11px;border-collapse:collapse;margin:3px 0 6px 12px'>"
            "{mrows}</table>"
            "</details>"
            "<hr style='margin:6px 0'>".format(
                sym=sym_name,
                nr=len(rows),
                nc=len(headers),
                name=name_desc,
                n=len(active),
                mrows=mapping_rows_html,
            )
        )

        # ── Step 4: Duplicate types and set parameters ────────────────────────────────────────────
        self._process_types(rows, name_col, format_string, headers, active, family_params)

    def _resolve_name(self, row, name_col, format_string, headers):
        if format_string:
            result = format_string
            for h in headers:
                result = result.replace("{" + h + "}", str(row.get(h, "")).strip())
            return result.strip()
        return str(row.get(name_col, "")).strip()

    def _process_types(self, rows, name_col, format_string, headers, mapping, family_params):
        out = self.output
        counts = {"ok": 0, "fail": 0, "skip": 0}
        # rows_log collects (type_name, status, detail) for the final HTML table
        rows_log = []

        # Collect existing type names from the same family
        from Autodesk.Revit.DB import Element as _Element
        family_id = self.source_symbol.Family.Id
        existing_names = set()
        for sym in doc.GetElement(family_id).GetFamilySymbolIds():
            s = doc.GetElement(sym)
            if s:
                existing_names.add(_Element.Name.GetValue(s))

        with Transaction(doc, "Generate Family Types from CSV") as t:
            t.Start()

            with forms.ProgressBar(title="Creating family types...", cancellable=True) as pb:
                total = len(rows)
                for i, row in enumerate(rows):
                    if pb.cancelled:
                        t.RollBack()
                        forms.alert("Cancelled. No changes saved.", title="Cancelled")
                        return

                    type_name = self._resolve_name(row, name_col, format_string, headers)

                    if not type_name:
                        counts["skip"] += 1
                        rows_log.append(("(row {})".format(i + 1), "skip", "empty name"))
                        pb.update_progress(i + 1, total)
                        continue

                    if type_name in existing_names:
                        counts["skip"] += 1
                        rows_log.append((type_name, "skip", "already exists"))
                        pb.update_progress(i + 1, total)
                        continue

                    ok, msg = self._duplicate_and_set(row, type_name, mapping, family_params)
                    existing_names.add(type_name)

                    if ok:
                        counts["ok"] += 1
                        rows_log.append((type_name, "ok", msg))
                    else:
                        counts["fail"] += 1
                        rows_log.append((type_name, "fail", msg))

                    pb.update_progress(i + 1, total)

            # ── Results table ─────────────────────────────────────────────────────
            done = counts["ok"] + counts["fail"] + counts["skip"]
            rate = int(counts["ok"] / done * 100) if done else 0

            STATUS_STYLE = {
                "ok":   "color:#1a7a1a",
                "fail": "color:#b00000;font-weight:bold",
                "skip": "color:#888",
            }
            STATUS_ICON = {"ok": "✅", "fail": "❌", "skip": "⏭️"}

            detail_rows_html = "".join(
                "<tr>"
                "<td style='padding:2px 10px 2px 0;{st}'>{icon} {name}</td>"
                "<td style='padding:2px 8px;font-size:10px;color:#666'>{detail}</td>"
                "</tr>".format(
                    st=STATUS_STYLE.get(st, ""),
                    icon=STATUS_ICON.get(st, ""),
                    name=nm,
                    detail=det,
                )
                for nm, st, det in rows_log
            )

            # Separate section for failures only (if any)
            fail_rows = [(nm, det) for nm, st, det in rows_log if st == "fail"]
            fail_html = ""
            if fail_rows:
                fail_html = (
                    "<details style='margin-top:6px'>"
                    "<summary style='font-size:11px;cursor:pointer;color:#b00000'>"
                    "⚠️ {} failure(s) — click to expand</summary>"
                    "<ul style='font-size:11px;margin:4px 0 0 16px;color:#b00000'>{}</ul>"
                    "</details>"
                ).format(
                    len(fail_rows),
                    "".join("<li><b>{}</b>: {}</li>".format(nm, det) for nm, det in fail_rows),
                )

            out.print_html(
                "<div style='font-size:13px;font-weight:bold;margin-bottom:4px'>"
                "✅ {ok} created &nbsp; ⏭️ {skip} skipped &nbsp; ❌ {fail} failed"
                " &nbsp;&nbsp; <span style='color:#555;font-size:11px;font-weight:normal'>"
                "({rate}% success)</span>"
                "</div>"
                "<details>"
                "<summary style='font-size:11px;cursor:pointer;color:#555'>"
                "All types ({total})</summary>"
                "<table style='font-size:11px;border-collapse:collapse;margin:4px 0 0 12px'>"
                "{det}</table>"
                "</details>"
                "{fail_html}"
                "<hr style='margin:8px 0'>".format(
                    ok=counts["ok"],
                    skip=counts["skip"],
                    fail=counts["fail"],
                    rate=rate,
                    total=done,
                    det=detail_rows_html,
                    fail_html=fail_html,
                )
            )
            out.print_md("💾 Saving…")

            status = t.Commit()

        if status != TransactionStatus.Committed:
            forms.alert("Transaction failed! Changes NOT saved.", title="Error")
            return

        forms.alert(
            "Done!\n\nCreated : {}\nSkipped : {}\nFailed  : {}\nSuccess : {}%".format(
                counts["ok"], counts["skip"], counts["fail"], rate
            ),
            title="Family Type Generator",
        )

    def _duplicate_and_set(self, row, type_name, mapping, family_params):
        """
        Duplicate source_symbol with type_name, then set all mapped parameters.
        Returns (True, summary_msg) or (False, error_msg).
        """
        try:
            # Duplicate creates a new FamilySymbol in the project
            new_symbol = self.source_symbol.Duplicate(type_name)

            if new_symbol is None:
                return False, "Duplicate() returned None"

            # Cast to FamilySymbol to access parameter API
            if not isinstance(new_symbol, FamilySymbol):
                return False, "Duplicate() did not return a FamilySymbol"

            ok_n = 0
            errors = []

            for csv_h, param_n in mapping.items():
                raw = str(row.get(csv_h, "")).strip()
                if not raw:
                    continue  # empty cell → keep inherited default from source type

                pinfo = family_params[param_n]
                spec_cat = pinfo['spec_category']

                try:
                    value = convert_csv_value(raw, spec_cat)
                except ValueError as e:
                    errors.append("{}: bad value '{}' ({})".format(csv_h, raw, e))
                    continue

                wrote, err = set_type_parameter(new_symbol, param_n, pinfo, value)
                if wrote:
                    ok_n += 1
                else:
                    errors.append("{}: {}".format(csv_h, err))

            msg = "{} params set".format(ok_n)
            if errors:
                msg += " | " + "; ".join(errors)
            return True, msg

        except Exception as e:
            return False, "Exception: {}".format(e)


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    output = script.get_output()
    output.print_md("# 🚀 FAMILY TYPE GENERATOR — PROJECT MODE")
    output.print_md("---")

    try:
        # Guard: must be a project document
        if doc.IsFamilyDocument:
            forms.alert(
                "This script runs in a PROJECT document.\n"
                "Please run it from a .rvt file with a family instance pre-selected.",
                title="Not a Project"
            )
            return

        # ── Step 0: Validate preselection ─────────────────────────────────────
        sel_ids = list(uidoc.Selection.GetElementIds())
        if not sel_ids:
            forms.alert(
                "Nothing selected.\n"
                "Please select one family instance before running this script.",
                title="No Selection"
            )
            return

        if len(sel_ids) > 1:
            forms.alert(
                "Multiple elements selected. Please select exactly ONE family instance.",
                title="Too Many Selected"
            )
            return

        instance = doc.GetElement(sel_ids[0])
        if instance is None:
            forms.alert("Selected element could not be retrieved.", title="Error")
            return

        # Get the type (FamilySymbol) from the instance
        type_id = instance.GetTypeId()
        if type_id is None:
            forms.alert("Selected element has no type.", title="Error")
            return

        source_symbol = doc.GetElement(type_id)
        if not isinstance(source_symbol, FamilySymbol):
            forms.alert(
                "Selected element is not a loadable family instance.\n"
                "System families (walls, floors, etc.) are not supported.",
                title="Not a Family Instance"
            )
            return

        # IronPython: .Name on Family/FamilySymbol requires Element.Name.GetValue()
        from Autodesk.Revit.DB import Element as _Element
        family_name = _Element.Name.GetValue(source_symbol.Family)
        type_name = _Element.Name.GetValue(source_symbol)
        output.print_md("✅ Source: **{}** — Type: **{}**".format(family_name, type_name))

        # ── Step 1: Pick CSV ───────────────────────────────────────────────────
        dlg = OpenFileDialog()
        dlg.Filter = "CSV files (*.csv)|*.csv|All files (*.*)|*.*"
        dlg.Title = "Select CSV file"

        if dlg.ShowDialog() != DialogResult.OK:
            output.print_md("❌ No file selected.")
            return

        csv_path = dlg.FileName
        output.print_md("✅ CSV: **{}**".format(os.path.basename(csv_path)))

        # ── Step 2: Run generator ──────────────────────────────────────────────
        FamilyTypeGenerator(source_symbol).run(csv_path)

    except Exception as e:
        output.print_md("❌ **Error:** {}".format(str(e)))
        import traceback
        traceback.print_exc()
        forms.alert("Error:\n{}".format(str(e)), title="Script Error")


if __name__ == '__main__':
    main()