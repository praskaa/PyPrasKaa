# -*- coding: utf-8 -*-
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System')
clr.AddReference('System.Collections')
clr.AddReference('PresentationFramework')
clr.AddReference('PresentationCore')
clr.AddReference('WindowsBase')
from Autodesk.Revit.DB import *
from System.Collections.Generic import List
from System.Collections.ObjectModel import ObservableCollection
from System.Windows import (Window, Thickness, GridLength, ResizeMode,
                             WindowStartupLocation, HorizontalAlignment,
                             TextWrapping, GridUnitType)
from System.Windows.Controls import (ListBox, ListBoxItem, Button, StackPanel,
                                      TextBlock, Grid, ColumnDefinition,
                                      RowDefinition, Orientation)
from System.Windows.Media import Brushes
from pyrevit import forms, script, revit
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'lib'))
from Snippets._selection import get_selected_elements, pick_by_category
from Snippets._context_manager import ef_Transaction

# UPDATED IMPORT: Now pulling CAT_MAP and DEFAULT_ORDER from the manager
from join_order_manager import (
    join_with_order, 
    get_intersecting_structural,
    ALL_CATEGORIES, 
    JOIN_PRIORITY,
    DEFAULT_ORDER,
    CAT_MAP
)

doc = revit.doc
uidoc = revit.uidoc

# Config keys
CFG_SECTION = 'join_order_manager'
CFG_KEY = 'priority_order'

def load_priority_order():
    """Load saved priority order from pyRevit config, fallback to default."""
    # ... [rest of the file remains exactly the same] ...

def load_priority_order():
    """Load saved priority order from pyRevit config, fallback to default."""
    try:
        cfg = script.get_config(CFG_SECTION)
        saved = cfg.get_option(CFG_KEY, None)
        if saved:
            order = saved.split(',')
            # Validate all keys exist
            if all(k in CAT_MAP for k in order):
                return order
    except:
        pass
    return list(DEFAULT_ORDER)


def save_priority_order(order):
    """Save priority order to pyRevit config."""
    try:
        cfg = script.get_config(CFG_SECTION)
        cfg.set_option(CFG_KEY, ','.join(order))
        script.save_config()
    except:
        pass


def build_priority_from_order(order):
    """Build {BuiltInCategory: priority_int} dict from ordered list."""
    priority = {}
    for i, key in enumerate(order):
        if key in CAT_MAP:
            bic, _ = CAT_MAP[key]
            priority[bic] = i + 1
    return priority


# --- WPF Config Dialog ---
class JoinOrderDialog(Window):
    def __init__(self, current_order):
        self.result_order = None
        self._order = list(current_order)
        self.Title = 'Join Order'
        self.Width = 320
        self.Height = 380
        self.ResizeMode = ResizeMode.NoResize
        self.WindowStartupLocation = WindowStartupLocation.CenterScreen

        # Root grid
        root = Grid()
        root.Margin = Thickness(12)

        # Row definitions
        rd0 = RowDefinition(); rd0.Height = GridLength(32)
        rd1 = RowDefinition(); rd1.Height = GridLength(1, GridUnitType.Star)
        rd2 = RowDefinition(); rd2.Height = GridLength(40)
        rd3 = RowDefinition(); rd3.Height = GridLength(44)
        root.RowDefinitions.Add(rd0)
        root.RowDefinitions.Add(rd1)
        root.RowDefinitions.Add(rd2)
        root.RowDefinitions.Add(rd3)

        # Label
        lbl = TextBlock()
        lbl.Text = 'Each category will cut categories below it.'
        lbl.TextWrapping = TextWrapping.Wrap
        lbl.Margin = Thickness(0, 0, 0, 6)
        Grid.SetRow(lbl, 0)
        root.Children.Add(lbl)

        # ListBox
        self.listbox = ListBox()
        self.listbox.Margin = Thickness(0, 0, 0, 6)
        Grid.SetRow(self.listbox, 1)
        root.Children.Add(self.listbox)
        self._refresh_list()

        # Up/Down buttons
        ud_panel = StackPanel()
        ud_panel.Orientation = Orientation.Horizontal
        ud_panel.Margin = Thickness(0, 0, 0, 6)
        Grid.SetRow(ud_panel, 2)

        btn_up = Button()
        btn_up.Content = u'\u2191 Up'
        btn_up.Width = 80
        btn_up.Margin = Thickness(0, 0, 8, 0)
        btn_up.Click += self._move_up

        btn_down = Button()
        btn_down.Content = u'\u2193 Down'
        btn_down.Width = 80
        btn_down.Click += self._move_down

        ud_panel.Children.Add(btn_up)
        ud_panel.Children.Add(btn_down)
        root.Children.Add(ud_panel)

        # Action buttons
        btn_panel = StackPanel()
        btn_panel.Orientation = Orientation.Horizontal
        btn_panel.HorizontalAlignment = HorizontalAlignment.Right
        Grid.SetRow(btn_panel, 3)

        btn_cancel = Button()
        btn_cancel.Content = 'Cancel'
        btn_cancel.Width = 75
        btn_cancel.Margin = Thickness(0, 0, 8, 0)
        btn_cancel.Click += self._cancel

        btn_default = Button()
        btn_default.Content = 'Default'
        btn_default.Width = 75
        btn_default.Margin = Thickness(0, 0, 8, 0)
        btn_default.Click += self._reset_default

        btn_save = Button()
        btn_save.Content = 'Save Settings'
        btn_save.Width = 95
        btn_save.Click += self._save

        btn_panel.Children.Add(btn_cancel)
        btn_panel.Children.Add(btn_default)
        btn_panel.Children.Add(btn_save)
        root.Children.Add(btn_panel)

        self.Content = root

    def _refresh_list(self, select_index=None):
        self.listbox.Items.Clear()
        for key in self._order:
            _, display = CAT_MAP.get(key, (None, key))
            item = ListBoxItem()
            item.Content = display
            item.Tag = key
            self.listbox.Items.Add(item)
        if select_index is not None:
            count = self.listbox.Items.Count
            idx = max(0, min(select_index, count - 1))
            self.listbox.SelectedIndex = idx

    def _get_selected_index(self):
        return self.listbox.SelectedIndex

    def _move_up(self, sender, args):
        idx = self._get_selected_index()
        if idx <= 0:
            return
        self._order[idx], self._order[idx - 1] = self._order[idx - 1], self._order[idx]
        self._refresh_list(idx - 1)

    def _move_down(self, sender, args):
        idx = self._get_selected_index()
        if idx < 0 or idx >= len(self._order) - 1:
            return
        self._order[idx], self._order[idx + 1] = self._order[idx + 1], self._order[idx]
        self._refresh_list(idx + 1)

    def _reset_default(self, sender, args):
        self._order = list(DEFAULT_ORDER)
        self._refresh_list(0)

    def _cancel(self, sender, args):
        self.result_order = None
        self.Close()

    def _save(self, sender, args):
        self.result_order = list(self._order)
        self.Close()


# --- Shift+Click: show config dialog ---
if __shiftclick__:
    current_order = load_priority_order()
    dlg = JoinOrderDialog(current_order)
    dlg.ShowDialog()
    if dlg.result_order:
        save_priority_order(dlg.result_order)
        forms.alert('Join order saved.', title='Join with Order')
    script.exit()


# --- Normal click: run join logic ---
priority_order = load_priority_order()
active_priority = build_priority_from_order(priority_order)


def get_priority_live(element):
    """Get priority from active (possibly user-configured) priority map."""
    if not element or not element.Category:
        return 99
    return active_priority.get(element.Category.BuiltInCategory, 99)


def get_cutting_live(elem_a, elem_b):
    """Return (cutting, cut) based on live priority config."""
    if get_priority_live(elem_a) <= get_priority_live(elem_b):
        return elem_a, elem_b
    return elem_b, elem_a


def join_with_live_order(elem_a, elem_b):
    """Join two elements and apply correct order per live config."""
    try:
        cutting, cut = get_cutting_live(elem_a, elem_b)
        if not JoinGeometryUtils.AreElementsJoined(doc, cutting, cut):
            try:
                JoinGeometryUtils.JoinGeometry(doc, cutting, cut)
            except:
                return
        # Apply correct join order
        try:
            is_cutting = JoinGeometryUtils.IsCuttingElementInJoin(doc, cutting, cut)
            if not is_cutting:
                JoinGeometryUtils.SwitchJoinOrder(doc, cutting, cut)
        except:
            try:
                JoinGeometryUtils.SwitchJoinOrder(doc, cutting, cut)
            except:
                pass
    except:
        pass


def process_element(element):
    """Join element with all intersecting structural elements."""
    intersecting = get_intersecting_structural(element, doc)
    for other in intersecting:
        join_with_live_order(element, other)


# Get selection
selected_elements = get_selected_elements(uidoc, exitscript=False)
selected = []
if selected_elements:
    for elem in selected_elements:
        if elem and elem.Category:
            if elem.Category.BuiltInCategory in list(active_priority.keys()):
                selected.append(elem)

if not selected:
    selected = pick_by_category(list(active_priority.keys()), exit_if_none=True)

# Process
if selected:
    with ef_Transaction(doc, "Join with Order", debug=False, exitscript=False):
        for elem in selected:
            try:
                process_element(elem)
            except:
                continue