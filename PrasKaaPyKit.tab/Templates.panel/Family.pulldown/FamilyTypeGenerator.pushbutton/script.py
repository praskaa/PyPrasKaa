# -*- coding: utf-8 -*-
"""
Family Type Generator from CSV
- Single column OR combined (format string) type naming
- Manual parameter matching UI (no assumptions)
- MM → Revit internal feet conversion
- StorageType-aware parameter handling
- No output after Transaction.Commit()
"""

__title__ = "Family Type Generator"
__author__ = "PrasKaa Team"
__doc__ = """Generate family types from CSV with manual parameter matching UI"""

import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')
clr.AddReference('PresentationCore')
clr.AddReference('PresentationFramework')
clr.AddReference('WindowsBase')
clr.AddReference('System')

# ── WPF Imports ───────────────────────────────────────────────────────────────
# IronPython: GridLength, GridUnitType, FontWeights, ResizeMode → System.Windows
#             NOT System.Windows.Controls
# ─────────────────────────────────────────────────────────────────────────────
from System.Windows.Forms import OpenFileDialog, DialogResult
from System.Windows import (
    ResizeMode,
    Window,
    WindowStartupLocation,
    HorizontalAlignment,
    VerticalAlignment,
    Thickness,
    GridLength,
    GridUnitType,
    FontWeights,
)
from System.Windows.Controls import (
    StackPanel,
    Grid,
    ColumnDefinition,
    RowDefinition,
    Label,
    ComboBox,
    ComboBoxItem,
    Button,
    ScrollViewer,
    TextBlock,
    TextBox,
    DockPanel,
    Dock,
    Separator,
    Orientation,
    ScrollBarVisibility,
    ListBox,
    ListBoxItem,
    Border,
    GroupBox,
)
from System.Windows import TextWrapping, TextAlignment
from System.Windows.Media import SolidColorBrush, Color as WpfColor

import os
import csv
import math
import re

# ── pyRevit ───────────────────────────────────────────────────────────────────
from pyrevit import forms, script
from pyrevit.revit import doc

# ── Revit API ─────────────────────────────────────────────────────────────────
from Autodesk.Revit.DB import (
    Transaction,
    StorageType,
    TransactionStatus,
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
    return 'length'   # safest default for Double in structural families


def convert_csv_value(raw_str, spec_category):
    """Convert CSV string to proper Python value for Revit internal unit."""
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
# FAMILY PARAMETER READER
# =============================================================================

def get_writable_type_parameters(family_doc):
    result = {}
    for p in family_doc.FamilyManager.Parameters:
        if p.IsReadOnly or p.IsDeterminedByFormula:
            continue
        name = p.Definition.Name
        result[name] = {
            'param': p,
            'storage_type': p.StorageType,
            'spec_category': get_spec_category(p),
        }
    return result


# =============================================================================
# SHARED WPF HELPERS
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
    """Create a Grid with given column widths (int=px, '*'=star, 'auto'=auto)."""
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
# COMBINED NAME BUILDER WINDOW
# =============================================================================

class CombinedNameWindow(Window):
    """
    Lets the user build a format string like "{Size} - {b}x{h}" using
    CSV column placeholders. Shows a live preview against first 8 rows.
    """

    def __init__(self, csv_headers, csv_rows):
        self.csv_headers = csv_headers
        self.preview_rows = csv_rows[:8]
        self.format_string = None      # set on Apply
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

        # ── Header ────────────────────────────────────────────────────────────
        hdr = StackPanel()
        hdr.Margin = Thickness(0, 0, 0, 10)
        DockPanel.SetDock(hdr, Dock.Top)
        root.Children.Add(hdr)

        hdr.Children.Add(_tb("Combined Type Name Builder", bold=True, size=15))

        how_to = _tb(
            "1. Double-click a column name to insert its placeholder into the format string.\n"
            "2. Type separators, spaces, or text between placeholders.\n"
            "   Example:  {Size} - {b}x{h}  or  L{b}x{t1}",
            size=11, wrap=True
        )
        how_to.Foreground = SolidColorBrush(WpfColor.FromRgb(80, 80, 80))
        how_to.Margin = Thickness(0, 4, 0, 0)
        hdr.Children.Add(how_to)

        # ── Format string input ────────────────────────────────────────────────
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

        # ── Validation label ───────────────────────────────────────────────────
        self._val_tb = TextBlock()
        self._val_tb.FontSize = 11
        self._val_tb.Margin = Thickness(0, 2, 0, 6)
        self._val_tb.Text = "Enter a format string above."
        self._val_tb.Foreground = SolidColorBrush(WpfColor.FromRgb(120, 120, 120))
        DockPanel.SetDock(self._val_tb, Dock.Top)
        root.Children.Add(self._val_tb)

        # ── Buttons ────────────────────────────────────────────────────────────
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

        # ── Body: columns list + preview ───────────────────────────────────────
        body = Grid()
        body.ColumnDefinitions.Add(ColumnDefinition())
        body.ColumnDefinitions[0].Width = GridLength(190)
        body.ColumnDefinitions.Add(ColumnDefinition())
        body.ColumnDefinitions[1].Width = GridLength(1, GridUnitType.Star)
        root.Children.Add(body)

        # Left: column list
        left = GroupBox()
        left.Header = "Available Columns (double-click to insert)"
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

        # Right: preview
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

    # ── helpers ───────────────────────────────────────────────────────────────

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

    # ── events ────────────────────────────────────────────────────────────────

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
# MANUAL PARAMETER MATCHING WINDOW
# =============================================================================

class ParameterMatchingWindow(Window):
    """
    One row per CSV column (name column excluded).
    Each row has a ComboBox with all writable family parameters.
    Default is always '-- Skip --' — no assumptions made.
    """

    SKIP = "-- Skip --"

    def __init__(self, csv_headers, name_column, family_params, sample_row):
        # name_column may be None when combined naming is used
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

        # Header
        hdr = StackPanel()
        hdr.Margin = Thickness(0, 0, 0, 8)
        DockPanel.SetDock(hdr, Dock.Top)
        root.Children.Add(hdr)

        hdr.Children.Add(_tb("Manual Parameter Matching", bold=True, size=15))

        hint = _tb(
            "Assign each CSV column to a family parameter.\n"
            "Leave '-- Skip --' to ignore that column.\n"
            "Numeric values are assumed to be MILLIMETERS "
            "and will be converted to Revit internal feet.",
            size=11, wrap=True
        )
        hint.Foreground = SolidColorBrush(WpfColor.FromRgb(90, 90, 90))
        hint.Margin = Thickness(0, 4, 0, 0)
        hdr.Children.Add(hint)

        # Buttons
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

        # Scrollable rows
        scroll = ScrollViewer()
        scroll.VerticalScrollBarVisibility = ScrollBarVisibility.Auto
        root.Children.Add(scroll)

        inner = StackPanel()
        inner.Margin = Thickness(0, 2, 4, 2)
        scroll.Content = inner

        # Column header row
        h_row = _row_grid(220, 24, '*', 180)
        _col(h_row, 0, _lbl("CSV Column", bold=True, size=11))
        _col(h_row, 2, _lbl("Family Parameter", bold=True, size=11))
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
# MAIN GENERATOR
# =============================================================================

class FamilyTypeGenerator:

    def __init__(self, family_doc):
        self.family_doc = family_doc
        self.fm = family_doc.FamilyManager
        self.output = script.get_output()

    # ── public entry point ────────────────────────────────────────────────────

    def run(self, csv_path):
        out = self.output
        out.print_md("# 📄 Reading CSV")

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

        out.print_md("✅ {} columns, {} rows".format(len(headers), len(rows)))

        # ── Step 1: Choose naming method ──────────────────────────────────────
        out.print_md("\n# 🏷️ Type Naming Method")
        naming_choice = forms.CommandSwitchWindow.show(
            ["Single Column", "Combined (Format String)"],
            message="How should type names be generated?",
            title="Type Naming Method",
        )
        if not naming_choice:
            out.print_md("❌ Cancelled.")
            return

        name_col = None        # used by single column mode
        format_string = None   # used by combined mode

        if naming_choice == "Single Column":
            # User picks which column holds the type name
            name_col = forms.CommandSwitchWindow.show(
                headers,
                message="Which column contains the TYPE NAME?",
                title="Select Name Column",
            )
            if not name_col:
                out.print_md("❌ Cancelled.")
                return
            out.print_md("✅ Name column: **{}**".format(name_col))

        else:  # Combined
            win = CombinedNameWindow(headers, rows)
            format_string = win.show_dialog()
            if format_string is None:
                out.print_md("❌ Cancelled.")
                return
            out.print_md("✅ Format string: `{}`".format(format_string))

        # ── Step 2: Get family parameters ─────────────────────────────────────
        family_params = get_writable_type_parameters(self.family_doc)
        if not family_params:
            forms.alert("No writable type parameters found.", title="No Parameters")
            return
        out.print_md("✅ **{}** writable type parameters found".format(len(family_params)))

        # ── Step 3: Manual matching UI ────────────────────────────────────────
        out.print_md("\n# 🔗 Manual Parameter Matching")
        sample_row = rows[0]

        win = ParameterMatchingWindow(
            csv_headers=headers,
            name_column=name_col,   # None is fine for combined mode
            family_params=family_params,
            sample_row=sample_row,
        )
        mapping = win.show_dialog()

        if mapping is None:
            out.print_md("❌ Cancelled by user.")
            return

        active = {k: v for k, v in mapping.items() if v is not None}
        skipped = [k for k, v in mapping.items() if v is None]

        out.print_md("## ✅ Active mappings ({})".format(len(active)))
        for csv_h, param_n in active.items():
            cat = family_params[param_n]['spec_category']
            out.print_md("  **{}** → `{}` *[{}]*".format(csv_h, param_n, cat))

        if skipped:
            out.print_md("## ⏭️ Skipped: {}".format(", ".join(skipped)))

        if not active:
            forms.alert("No columns mapped. Nothing to do.", title="No Mapping")
            return

        # ── Step 4: Create types ──────────────────────────────────────────────
        out.print_md("\n# ⚙️ Creating Family Types")
        self._process_types(rows, name_col, format_string, headers, active, family_params)

    # ─────────────────────────────────────────────────────────────────────────

    def _resolve_name(self, row, name_col, format_string, headers):
        """Return the type name for a CSV row depending on naming mode."""
        if format_string:
            result = format_string
            for h in headers:
                result = result.replace("{" + h + "}", str(row.get(h, "")).strip())
            return result.strip()
        else:
            return str(row.get(name_col, "")).strip()

    def _process_types(self, rows, name_col, format_string, headers, mapping, family_params):
        out = self.output
        counts = {'ok': 0, 'fail': 0, 'skip': 0}
        existing = set(ft.Name for ft in self.fm.Types)

        with Transaction(self.family_doc, "Generate Family Types from CSV") as t:
            t.Start()

            with forms.ProgressBar(title="Creating family types...", cancellable=True) as pb:
                total = len(rows)
                for i, row in enumerate(rows):
                    if pb.cancelled:
                        t.RollBack()
                        forms.alert("Cancelled.", title="Cancelled")
                        return

                    type_name = self._resolve_name(row, name_col, format_string, headers)

                    if not type_name:
                        out.print_md("  ⚠️ Row {}: empty name — skipped".format(i + 1))
                        counts['skip'] += 1
                        pb.update_progress(i + 1, total)
                        continue

                    if type_name in existing:
                        out.print_md("  ⏭️ **{}** already exists — skipped".format(type_name))
                        counts['skip'] += 1
                        pb.update_progress(i + 1, total)
                        continue

                    ok, msg = self._create_type(row, type_name, mapping, family_params)
                    existing.add(type_name)

                    if ok:
                        counts['ok'] += 1
                        out.print_md("  ✅ **{}**: {}".format(type_name, msg))
                    else:
                        counts['fail'] += 1
                        out.print_md("  ❌ **{}**: {}".format(type_name, msg))

                    pb.update_progress(i + 1, total)

            # Summary BEFORE commit — prevents console splitting
            done = counts['ok'] + counts['fail'] + counts['skip']
            rate = int(counts['ok'] / done * 100) if done else 0
            out.print_md("\n## 📊 Results")
            out.print_md("✅ Created : **{}**".format(counts['ok']))
            out.print_md("⏭️ Skipped : **{}**".format(counts['skip']))
            out.print_md("❌ Failed  : **{}**".format(counts['fail']))
            out.print_md("🎯 Success : **{}%**".format(rate))
            out.print_md("\n💾 Saving…")

            status = t.Commit()

        if status != TransactionStatus.Committed:
            forms.alert("Transaction failed! Changes NOT saved.", title="Error")
            return

        forms.alert(
            "Done!\n\nCreated : {}\nSkipped : {}\nFailed  : {}\nSuccess : {}%".format(
                counts['ok'], counts['skip'], counts['fail'], rate
            ),
            title="Family Type Generator",
        )

    def _create_type(self, row, type_name, mapping, family_params):
        try:
            new_type = self.fm.NewType(type_name)
            self.fm.CurrentType = new_type

            ok_n = 0
            errors = []

            for csv_h, param_n in mapping.items():
                raw = str(row.get(csv_h, "")).strip()
                if not raw:
                    continue   # empty cell → keep parameter default

                pinfo = family_params[param_n]
                param = pinfo['param']
                spec_cat = pinfo['spec_category']
                st = pinfo['storage_type']

                try:
                    value = convert_csv_value(raw, spec_cat)
                    if st == StorageType.Double:
                        self.fm.Set(param, float(value))
                    elif st == StorageType.Integer:
                        self.fm.Set(param, int(value))
                    elif st == StorageType.String:
                        self.fm.Set(param, str(value))
                    else:
                        errors.append("{}: unsupported StorageType".format(csv_h))
                        continue
                    ok_n += 1
                except ValueError as e:
                    errors.append("{}: bad value '{}' ({})".format(csv_h, raw, e))
                except Exception as e:
                    errors.append("{}: {}".format(csv_h, e))

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
    output.print_md("# 🚀 FAMILY TYPE GENERATOR")
    output.print_md("---")

    try:
        if not doc.IsFamilyDocument:
            forms.alert("Please open a Family (.rfa) document first.", title="Not a Family")
            return

        output.print_md("✅ Family: **{}**".format(doc.Title))

        dlg = OpenFileDialog()
        dlg.Filter = "CSV files (*.csv)|*.csv|All files (*.*)|*.*"
        dlg.Title = "Select CSV file"

        if dlg.ShowDialog() != DialogResult.OK:
            output.print_md("❌ No file selected.")
            return

        csv_path = dlg.FileName
        output.print_md("✅ CSV: **{}**".format(os.path.basename(csv_path)))

        FamilyTypeGenerator(doc).run(csv_path)

    except Exception as e:
        output.print_md("❌ **Error:** {}".format(str(e)))
        import traceback
        traceback.print_exc()
        forms.alert("Error:\n{}".format(str(e)), title="Script Error")


if __name__ == '__main__':
    main()