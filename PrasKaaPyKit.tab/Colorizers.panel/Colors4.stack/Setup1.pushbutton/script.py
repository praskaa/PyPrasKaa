# -*- coding: utf-8 -*-
__title__ = "Override Button-1"
__author__ = "PrasKaa"
__version__ = "Version: 1.0"
__doc__ = """
xx.xx.2026
_____________________________________________________________________
Description:
Apply Projection/Surface Graphic Override to selected elements.
Pattern, foreground color, and background color are configurable.

Shift+Click  -> Open XAML configuration dialog.
Click        -> Apply saved configuration directly to selection.
_____________________________________________________________________
Last update:
- [xx.xx.2026] - 1.0 RELEASE
_____________________________________________________________________
Author: PrasKaa"""

import os
import json
import clr

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")
clr.AddReference("WindowsBase")
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from Autodesk.Revit.DB import (
    Transaction, OverrideGraphicSettings,
    FillPatternElement, FillPatternTarget,
    Color, ElementId
)
from System.Windows.Media import SolidColorBrush, Color as WpfColor
from System.Windows.Markup import XamlReader
from System.Windows.Forms import ColorDialog, DialogResult
import System.Drawing as Drawing
from pyrevit import revit, forms, script

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────
SCRIPT_DIR     = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH    = os.path.join(SCRIPT_DIR, "config.json")
MAIN_XAML_PATH = os.path.join(SCRIPT_DIR, "ConfigDialog.xaml")

# ─────────────────────────────────────────────
# Defaults
# ─────────────────────────────────────────────
DEFAULT_CONFIG = {
    "pattern_name": "<Solid fill>",
    "fg_r": 128, "fg_g": 128, "fg_b": 128,
    "bg_r": 180, "bg_g": 180, "bg_b": 180,
    "use_bg": True
}

# ─────────────────────────────────────────────
# Config helpers
# ─────────────────────────────────────────────
def load_config():
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                data.setdefault(k, v)
            return data
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=4)


# ─────────────────────────────────────────────
# Color helpers
# ─────────────────────────────────────────────
def make_revit_color(r, g, b):
    return Color(int(r), int(g), int(b))


def make_wpf_brush(r, g, b):
    return SolidColorBrush(WpfColor.FromRgb(int(r), int(g), int(b)))


def open_color_dialog(owner_win, init_r, init_g, init_b):
    """
    Open Windows native ColorDialog pre-filled with init_r/g/b.
    Returns (r, g, b) on OK, or None on cancel.
    owner_win is the WPF Window — used only to bring dialog to front.
    """
    dlg = ColorDialog()
    dlg.Color = Drawing.Color.FromArgb(int(init_r), int(init_g), int(init_b))
    dlg.FullOpen = True
    res = dlg.ShowDialog()
    if res == DialogResult.OK:
        c = dlg.Color
        return int(c.R), int(c.G), int(c.B)
    return None


# ─────────────────────────────────────────────
# XAML loader
# ─────────────────────────────────────────────
def load_xaml_window(xaml_path):
    with open(xaml_path, "r") as f:
        xaml_str = f.read()
    return XamlReader.Parse(xaml_str)


# ─────────────────────────────────────────────
# Revit helpers
# ─────────────────────────────────────────────
def get_drafting_patterns(doc):
    from Autodesk.Revit.DB import FilteredElementCollector
    patterns = {}
    for fp in FilteredElementCollector(doc).OfClass(FillPatternElement):
        pat = fp.GetFillPattern()
        if pat and pat.Target == FillPatternTarget.Drafting:
            patterns[fp.Name] = fp
    return patterns


def find_pattern_by_name(doc, name):
    from Autodesk.Revit.DB import FilteredElementCollector
    for fp in FilteredElementCollector(doc).OfClass(FillPatternElement):
        if fp.Name == name:
            pat = fp.GetFillPattern()
            if pat and pat.Target == FillPatternTarget.Drafting:
                return fp.Id
    return ElementId.InvalidElementId


# ─────────────────────────────────────────────
# Main Config Dialog
# ─────────────────────────────────────────────
class ConfigDialog(object):
    """
    Wraps ConfigDialog.xaml.
    Palette buttons open Windows ColorDialog directly — no sub-dialog.
    """

    def __init__(self, doc):
        self._doc = doc
        self._cfg = load_config()
        self._win = load_xaml_window(MAIN_XAML_PATH)

        # Named elements
        self._pattern_cb  = self._win.FindName("PatternComboBox")
        self._fg_r        = self._win.FindName("FgR")
        self._fg_g        = self._win.FindName("FgG")
        self._fg_b        = self._win.FindName("FgB")
        self._fg_r_val    = self._win.FindName("FgRVal")
        self._fg_g_val    = self._win.FindName("FgGVal")
        self._fg_b_val    = self._win.FindName("FgBVal")
        self._fg_preview  = self._win.FindName("FgPreview")
        self._fg_palette  = self._win.FindName("FgPaletteButton")

        self._bg_enabled  = self._win.FindName("BgEnabled")
        self._bg_controls = self._win.FindName("BgControls")
        self._bg_r        = self._win.FindName("BgR")
        self._bg_g        = self._win.FindName("BgG")
        self._bg_b        = self._win.FindName("BgB")
        self._bg_r_val    = self._win.FindName("BgRVal")
        self._bg_g_val    = self._win.FindName("BgGVal")
        self._bg_b_val    = self._win.FindName("BgBVal")
        self._bg_preview  = self._win.FindName("BgPreview")
        self._bg_palette  = self._win.FindName("BgPaletteButton")

        self._ok_btn      = self._win.FindName("OkButton")
        self._cancel_btn  = self._win.FindName("CancelButton")

        self._populate()
        self._wire_events()

    # ── Populate from config ─────────────────
    def _populate(self):
        cfg = self._cfg

        # Pattern list
        patterns = get_drafting_patterns(self._doc)
        for name in sorted(patterns.keys()):
            self._pattern_cb.Items.Add(name)
        saved = cfg.get("pattern_name", "")
        items = [self._pattern_cb.Items[i] for i in range(self._pattern_cb.Items.Count)]
        if saved in items:
            self._pattern_cb.SelectedItem = saved
        else:
            self._pattern_cb.SelectedIndex = 0

        # Sliders
        self._fg_r.Value = cfg["fg_r"]
        self._fg_g.Value = cfg["fg_g"]
        self._fg_b.Value = cfg["fg_b"]
        self._bg_r.Value = cfg["bg_r"]
        self._bg_g.Value = cfg["bg_g"]
        self._bg_b.Value = cfg["bg_b"]

        # BgEnabled
        self._bg_enabled.IsChecked = bool(cfg.get("use_bg", True))
        self._set_bg_controls_enabled(bool(cfg.get("use_bg", True)))

        self._sync_labels_fg()
        self._sync_labels_bg()

    # ── Event wiring ─────────────────────────
    def _wire_events(self):
        self._fg_r.ValueChanged += lambda s, e: self._sync_labels_fg()
        self._fg_g.ValueChanged += lambda s, e: self._sync_labels_fg()
        self._fg_b.ValueChanged += lambda s, e: self._sync_labels_fg()

        self._bg_r.ValueChanged += lambda s, e: self._sync_labels_bg()
        self._bg_g.ValueChanged += lambda s, e: self._sync_labels_bg()
        self._bg_b.ValueChanged += lambda s, e: self._sync_labels_bg()

        self._bg_enabled.Checked   += lambda s, e: self._set_bg_controls_enabled(True)
        self._bg_enabled.Unchecked += lambda s, e: self._set_bg_controls_enabled(False)

        # Palette buttons → directly open ColorDialog
        self._fg_palette.Click += self._on_fg_palette
        self._bg_palette.Click += self._on_bg_palette

        self._ok_btn.Click     += self._on_ok
        self._cancel_btn.Click += self._on_cancel

    # ── Sync helpers ─────────────────────────
    def _sync_labels_fg(self):
        r = int(self._fg_r.Value)
        g = int(self._fg_g.Value)
        b = int(self._fg_b.Value)
        self._fg_r_val.Text         = str(r)
        self._fg_g_val.Text         = str(g)
        self._fg_b_val.Text         = str(b)
        self._fg_preview.Background = make_wpf_brush(r, g, b)

    def _sync_labels_bg(self):
        r = int(self._bg_r.Value)
        g = int(self._bg_g.Value)
        b = int(self._bg_b.Value)
        self._bg_r_val.Text         = str(r)
        self._bg_g_val.Text         = str(g)
        self._bg_b_val.Text         = str(b)
        self._bg_preview.Background = make_wpf_brush(r, g, b)

    def _set_bg_controls_enabled(self, enabled):
        self._bg_controls.IsEnabled = enabled
        self._bg_controls.Opacity   = 1.0 if enabled else 0.4

    # ── Palette buttons → ColorDialog directly ──
    def _on_fg_palette(self, sender, e):
        result = open_color_dialog(
            self._win,
            int(self._fg_r.Value),
            int(self._fg_g.Value),
            int(self._fg_b.Value)
        )
        if result:
            r, g, b = result
            self._fg_r.Value = r
            self._fg_g.Value = g
            self._fg_b.Value = b

    def _on_bg_palette(self, sender, e):
        result = open_color_dialog(
            self._win,
            int(self._bg_r.Value),
            int(self._bg_g.Value),
            int(self._bg_b.Value)
        )
        if result:
            r, g, b = result
            self._bg_r.Value = r
            self._bg_g.Value = g
            self._bg_b.Value = b

    # ── OK / Cancel ──────────────────────────
    def _on_ok(self, sender, e):
        cfg = self._cfg
        cfg["pattern_name"] = str(self._pattern_cb.SelectedItem) if self._pattern_cb.SelectedItem else cfg["pattern_name"]
        cfg["fg_r"] = int(self._fg_r.Value)
        cfg["fg_g"] = int(self._fg_g.Value)
        cfg["fg_b"] = int(self._fg_b.Value)
        cfg["use_bg"] = bool(self._bg_enabled.IsChecked)
        cfg["bg_r"] = int(self._bg_r.Value)
        cfg["bg_g"] = int(self._bg_g.Value)
        cfg["bg_b"] = int(self._bg_b.Value)
        save_config(cfg)
        self._win.DialogResult = True
        self._win.Close()

    def _on_cancel(self, sender, e):
        self._win.DialogResult = False
        self._win.Close()

    def show(self):
        self._win.ShowDialog()


# ─────────────────────────────────────────────
# Apply override  (Click)
# ─────────────────────────────────────────────
def run_apply(doc, uidoc):
    cfg = load_config()

    pat_id = find_pattern_by_name(doc, cfg["pattern_name"])
    if pat_id == ElementId.InvalidElementId:
        forms.alert(
            "Pattern '{}' not found in this document.\n"
            "Shift+Click to reconfigure.".format(cfg["pattern_name"]),
            exitscript=True
        )

    fg_color = make_revit_color(cfg["fg_r"], cfg["fg_g"], cfg["fg_b"])
    use_bg   = cfg.get("use_bg", True)
    bg_color = make_revit_color(cfg["bg_r"], cfg["bg_g"], cfg["bg_b"]) if use_bg else None

    ogs = OverrideGraphicSettings()
    ogs.SetSurfaceForegroundPatternId(pat_id)
    ogs.SetSurfaceForegroundPatternColor(fg_color)
    ogs.SetCutForegroundPatternId(pat_id)
    ogs.SetCutForegroundPatternColor(fg_color)
    if use_bg and bg_color:
        ogs.SetSurfaceBackgroundPatternId(pat_id)
        ogs.SetSurfaceBackgroundPatternColor(bg_color)
        ogs.SetCutBackgroundPatternId(pat_id)
        ogs.SetCutBackgroundPatternColor(bg_color)

    selection = revit.get_selection()
    if not selection:
        forms.alert("No elements selected.", exitscript=True)

    active_view = uidoc.ActiveView

    with Transaction(doc, "PrasKaa - Set Projection Override") as t:
        t.Start()
        count = 0
        for el in selection:
            try:
                active_view.SetElementOverrides(el.Id, ogs)
                count += 1
            except Exception:
                pass
        t.Commit()

    forms.toast(
        "Applied to {} element(s)".format(count),
        title="Set Projection Override",
        appid="PrasKaaPyKit"
    )


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
doc   = revit.doc
uidoc = revit.uidoc

if __shiftclick__:
    dlg = ConfigDialog(doc)
    dlg.show()
else:
    run_apply(doc, uidoc)