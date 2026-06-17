# -*- coding: utf-8 -*-
__title__ = "Override Button-1"
__author__ = "PrasKaa"
__version__ = "Version: 2.1"
__doc__ = """
xx.xx.2026
_____________________________________________________________________
Description:
Apply View-Specific Element Graphics Override to selected elements.
Controls (each sub-field independently toggleable):
  - Projection Lines : Pattern, Color, Weight
  - Cut Lines        : Pattern, Color, Weight
  - Surface Patterns : Foreground Pattern+Color, Background Pattern+Color

Shift+Click  -> Open XAML configuration dialog.
Click        -> Apply saved configuration directly to selection.
_____________________________________________________________________
Last update:
- [xx.xx.2026] - 2.1 Per-field "No Override" toggles (Pattern/Color/Weight)
- [xx.xx.2026] - 2.0 Added Projection/Cut line overrides + config persistence
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
    LinePatternElement,
    Color, ElementId,
    FilteredElementCollector
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
    # ── Projection Lines ─────────────────────
    "use_proj_override":    True,
    "proj_override_pattern": True,
    "proj_pattern_name":    "<Solid>",
    "proj_override_weight": True,
    "proj_weight":          1,
    "proj_override_color":  True,
    "proj_color_r": 0, "proj_color_g": 0, "proj_color_b": 0,

    # ── Cut Lines ────────────────────────────
    "use_cut_override":     True,
    "cut_override_pattern": True,
    "cut_pattern_name":     "<Solid>",
    "cut_override_weight":  True,
    "cut_weight":           1,
    "cut_override_color":   True,
    "cut_color_r": 0, "cut_color_g": 0, "cut_color_b": 0,

    # ── Surface FG ───────────────────────────
    "use_surf_fg":              True,
    "surf_fg_override_pattern": True,
    "surf_fg_pattern_name":     "<Solid fill>",
    "surf_fg_override_color":   True,
    "surf_fg_r": 128, "surf_fg_g": 128, "surf_fg_b": 128,

    # ── Surface BG ───────────────────────────
    "use_surf_bg":              True,
    "surf_bg_override_pattern": True,
    "surf_bg_pattern_name":     "<Solid fill>",
    "surf_bg_override_color":   True,
    "surf_bg_r": 180, "surf_bg_g": 180, "surf_bg_b": 180,
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


def open_color_dialog(init_r, init_g, init_b):
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
# Revit pattern collectors
# ─────────────────────────────────────────────
def get_drafting_fill_patterns(doc):
    patterns = {}
    for fp in FilteredElementCollector(doc).OfClass(FillPatternElement):
        pat = fp.GetFillPattern()
        if pat and pat.Target == FillPatternTarget.Drafting:
            patterns[fp.Name] = fp
    return patterns


def get_line_patterns(doc):
    patterns = {"<Solid>": LinePatternElement.GetSolidPatternId()}
    for lp in FilteredElementCollector(doc).OfClass(LinePatternElement):
        patterns[lp.Name] = lp.Id
    return patterns


def find_fill_pattern_id(doc, name):
    for fp in FilteredElementCollector(doc).OfClass(FillPatternElement):
        if fp.Name == name:
            pat = fp.GetFillPattern()
            if pat and pat.Target == FillPatternTarget.Drafting:
                return fp.Id
    return ElementId.InvalidElementId


def find_line_pattern_id(doc, name):
    if name == "<Solid>":
        return LinePatternElement.GetSolidPatternId()
    for lp in FilteredElementCollector(doc).OfClass(LinePatternElement):
        if lp.Name == name:
            return lp.Id
    return ElementId.InvalidElementId


# ─────────────────────────────────────────────
# Config Dialog
# ─────────────────────────────────────────────
class ConfigDialog(object):

    def __init__(self, doc):
        self._doc = doc
        self._cfg = load_config()
        self._win = load_xaml_window(MAIN_XAML_PATH)

        # ── Shared fill pattern ───────────────
        self._pattern_cb        = self._win.FindName("PatternComboBox")

        # ── Projection ───────────────────────
        self._proj_enabled          = self._win.FindName("ProjEnabled")
        self._proj_controls         = self._win.FindName("ProjControls")
        self._proj_override_pattern = self._win.FindName("ProjOverridePattern")
        self._proj_pattern_row      = self._win.FindName("ProjPatternRow")
        self._proj_pat_cb           = self._win.FindName("ProjPatternComboBox")
        self._proj_override_weight  = self._win.FindName("ProjOverrideWeight")
        self._proj_weight_row       = self._win.FindName("ProjWeightRow")
        self._proj_weight           = self._win.FindName("ProjWeight")
        self._proj_override_color   = self._win.FindName("ProjOverrideColor")
        self._proj_color_row        = self._win.FindName("ProjColorRow")
        self._proj_r                = self._win.FindName("ProjR")
        self._proj_g                = self._win.FindName("ProjG")
        self._proj_b                = self._win.FindName("ProjB")
        self._proj_r_val            = self._win.FindName("ProjRVal")
        self._proj_g_val            = self._win.FindName("ProjGVal")
        self._proj_b_val            = self._win.FindName("ProjBVal")
        self._proj_preview          = self._win.FindName("ProjPreview")
        self._proj_palette          = self._win.FindName("ProjPaletteButton")

        # ── Cut ──────────────────────────────
        self._cut_enabled           = self._win.FindName("CutEnabled")
        self._cut_controls          = self._win.FindName("CutControls")
        self._cut_override_pattern  = self._win.FindName("CutOverridePattern")
        self._cut_pattern_row       = self._win.FindName("CutPatternRow")
        self._cut_pat_cb            = self._win.FindName("CutPatternComboBox")
        self._cut_override_weight   = self._win.FindName("CutOverrideWeight")
        self._cut_weight_row        = self._win.FindName("CutWeightRow")
        self._cut_weight            = self._win.FindName("CutWeight")
        self._cut_override_color    = self._win.FindName("CutOverrideColor")
        self._cut_color_row         = self._win.FindName("CutColorRow")
        self._cut_r                 = self._win.FindName("CutR")
        self._cut_g                 = self._win.FindName("CutG")
        self._cut_b                 = self._win.FindName("CutB")
        self._cut_r_val             = self._win.FindName("CutRVal")
        self._cut_g_val             = self._win.FindName("CutGVal")
        self._cut_b_val             = self._win.FindName("CutBVal")
        self._cut_preview           = self._win.FindName("CutPreview")
        self._cut_palette           = self._win.FindName("CutPaletteButton")

        # ── Surface FG ───────────────────────
        self._surf_fg_enabled           = self._win.FindName("SurfFgEnabled")
        self._surf_fg_controls          = self._win.FindName("SurfFgControls")
        self._surf_fg_override_pattern  = self._win.FindName("SurfFgOverridePattern")
        self._surf_fg_pattern_dimmer    = self._win.FindName("SurfFgPatternDimmer")
        self._surf_fg_override_color    = self._win.FindName("SurfFgOverrideColor")
        self._surf_fg_color_row         = self._win.FindName("SurfFgColorRow")
        self._surf_fg_r                 = self._win.FindName("SurfFgR")
        self._surf_fg_g                 = self._win.FindName("SurfFgG")
        self._surf_fg_b                 = self._win.FindName("SurfFgB")
        self._surf_fg_r_val             = self._win.FindName("SurfFgRVal")
        self._surf_fg_g_val             = self._win.FindName("SurfFgGVal")
        self._surf_fg_b_val             = self._win.FindName("SurfFgBVal")
        self._surf_fg_preview           = self._win.FindName("SurfFgPreview")
        self._surf_fg_palette           = self._win.FindName("SurfFgPaletteButton")

        # ── Surface BG ───────────────────────
        self._surf_bg_enabled           = self._win.FindName("SurfBgEnabled")
        self._surf_bg_controls          = self._win.FindName("SurfBgControls")
        self._surf_bg_override_pattern  = self._win.FindName("SurfBgOverridePattern")
        self._surf_bg_pattern_dimmer    = self._win.FindName("SurfBgPatternDimmer")
        self._surf_bg_override_color    = self._win.FindName("SurfBgOverrideColor")
        self._surf_bg_color_row         = self._win.FindName("SurfBgColorRow")
        self._surf_bg_r                 = self._win.FindName("SurfBgR")
        self._surf_bg_g                 = self._win.FindName("SurfBgG")
        self._surf_bg_b                 = self._win.FindName("SurfBgB")
        self._surf_bg_r_val             = self._win.FindName("SurfBgRVal")
        self._surf_bg_g_val             = self._win.FindName("SurfBgGVal")
        self._surf_bg_b_val             = self._win.FindName("SurfBgBVal")
        self._surf_bg_preview           = self._win.FindName("SurfBgPreview")
        self._surf_bg_palette           = self._win.FindName("SurfBgPaletteButton")

        # ── Buttons ──────────────────────────
        self._ok_btn     = self._win.FindName("OkButton")
        self._cancel_btn = self._win.FindName("CancelButton")

        self._line_patterns = get_line_patterns(doc)
        self._fill_patterns = get_drafting_fill_patterns(doc)

        self._populate()
        self._wire_events()

    # ── Dim helper ───────────────────────────
    def _set_dim(self, element, enabled):
        element.IsEnabled = enabled
        element.Opacity   = 1.0 if enabled else 0.35

    # ── Combobox fillers ─────────────────────
    def _fill_line_cb(self, cb, saved):
        for name in sorted(self._line_patterns.keys()):
            cb.Items.Add(name)
        items = [cb.Items[i] for i in range(cb.Items.Count)]
        cb.SelectedItem = saved if saved in items else (cb.Items[0] if cb.Items.Count else None)

    def _fill_fill_cb(self, cb, saved):
        for name in sorted(self._fill_patterns.keys()):
            cb.Items.Add(name)
        items = [cb.Items[i] for i in range(cb.Items.Count)]
        cb.SelectedItem = saved if saved in items else (cb.Items[0] if cb.Items.Count else None)

    def _fill_weight_cb(self, cb, saved):
        for w in range(1, 17):
            cb.Items.Add(str(w))
        target = str(int(saved))
        items = [cb.Items[i] for i in range(cb.Items.Count)]
        cb.SelectedItem = target if target in items else "1"

    # ── Populate ─────────────────────────────
    def _populate(self):
        cfg = self._cfg

        # Shared fill pattern
        self._fill_fill_cb(self._pattern_cb, cfg["surf_fg_pattern_name"])

        # ── Projection ───
        self._proj_enabled.IsChecked         = bool(cfg["use_proj_override"])
        self._set_dim(self._proj_controls,     bool(cfg["use_proj_override"]))

        self._proj_override_pattern.IsChecked = bool(cfg["proj_override_pattern"])
        self._fill_line_cb(self._proj_pat_cb,  cfg["proj_pattern_name"])
        self._set_dim(self._proj_pattern_row,  bool(cfg["proj_override_pattern"]))

        self._proj_override_weight.IsChecked  = bool(cfg["proj_override_weight"])
        self._fill_weight_cb(self._proj_weight, cfg["proj_weight"])
        self._set_dim(self._proj_weight_row,   bool(cfg["proj_override_weight"]))

        self._proj_override_color.IsChecked   = bool(cfg["proj_override_color"])
        self._proj_r.Value = cfg["proj_color_r"]
        self._proj_g.Value = cfg["proj_color_g"]
        self._proj_b.Value = cfg["proj_color_b"]
        self._set_dim(self._proj_color_row,    bool(cfg["proj_override_color"]))
        self._sync_proj_preview()

        # ── Cut ──────────
        self._cut_enabled.IsChecked          = bool(cfg["use_cut_override"])
        self._set_dim(self._cut_controls,      bool(cfg["use_cut_override"]))

        self._cut_override_pattern.IsChecked  = bool(cfg["cut_override_pattern"])
        self._fill_line_cb(self._cut_pat_cb,   cfg["cut_pattern_name"])
        self._set_dim(self._cut_pattern_row,   bool(cfg["cut_override_pattern"]))

        self._cut_override_weight.IsChecked   = bool(cfg["cut_override_weight"])
        self._fill_weight_cb(self._cut_weight, cfg["cut_weight"])
        self._set_dim(self._cut_weight_row,    bool(cfg["cut_override_weight"]))

        self._cut_override_color.IsChecked    = bool(cfg["cut_override_color"])
        self._cut_r.Value = cfg["cut_color_r"]
        self._cut_g.Value = cfg["cut_color_g"]
        self._cut_b.Value = cfg["cut_color_b"]
        self._set_dim(self._cut_color_row,     bool(cfg["cut_override_color"]))
        self._sync_cut_preview()

        # ── Surface FG ───
        self._surf_fg_enabled.IsChecked            = bool(cfg["use_surf_fg"])
        self._set_dim(self._surf_fg_controls,       bool(cfg["use_surf_fg"]))

        self._surf_fg_override_pattern.IsChecked   = bool(cfg["surf_fg_override_pattern"])
        self._set_dim(self._surf_fg_pattern_dimmer, bool(cfg["surf_fg_override_pattern"]))

        self._surf_fg_override_color.IsChecked     = bool(cfg["surf_fg_override_color"])
        self._surf_fg_r.Value = cfg["surf_fg_r"]
        self._surf_fg_g.Value = cfg["surf_fg_g"]
        self._surf_fg_b.Value = cfg["surf_fg_b"]
        self._set_dim(self._surf_fg_color_row,      bool(cfg["surf_fg_override_color"]))
        self._sync_surf_fg_preview()

        # ── Surface BG ───
        self._surf_bg_enabled.IsChecked            = bool(cfg["use_surf_bg"])
        self._set_dim(self._surf_bg_controls,       bool(cfg["use_surf_bg"]))

        self._surf_bg_override_pattern.IsChecked   = bool(cfg["surf_bg_override_pattern"])
        self._set_dim(self._surf_bg_pattern_dimmer, bool(cfg["surf_bg_override_pattern"]))

        self._surf_bg_override_color.IsChecked     = bool(cfg["surf_bg_override_color"])
        self._surf_bg_r.Value = cfg["surf_bg_r"]
        self._surf_bg_g.Value = cfg["surf_bg_g"]
        self._surf_bg_b.Value = cfg["surf_bg_b"]
        self._set_dim(self._surf_bg_color_row,      bool(cfg["surf_bg_override_color"]))
        self._sync_surf_bg_preview()

    # ── Wire events ──────────────────────────
    def _wire_events(self):
        # Proj master
        self._proj_enabled.Checked   += lambda s, e: self._set_dim(self._proj_controls, True)
        self._proj_enabled.Unchecked += lambda s, e: self._set_dim(self._proj_controls, False)
        # Proj sub-toggles
        self._proj_override_pattern.Checked   += lambda s, e: self._set_dim(self._proj_pattern_row, True)
        self._proj_override_pattern.Unchecked += lambda s, e: self._set_dim(self._proj_pattern_row, False)
        self._proj_override_weight.Checked    += lambda s, e: self._set_dim(self._proj_weight_row, True)
        self._proj_override_weight.Unchecked  += lambda s, e: self._set_dim(self._proj_weight_row, False)
        self._proj_override_color.Checked     += lambda s, e: self._set_dim(self._proj_color_row, True)
        self._proj_override_color.Unchecked   += lambda s, e: self._set_dim(self._proj_color_row, False)
        # Proj sliders
        self._proj_r.ValueChanged += lambda s, e: self._sync_proj_preview()
        self._proj_g.ValueChanged += lambda s, e: self._sync_proj_preview()
        self._proj_b.ValueChanged += lambda s, e: self._sync_proj_preview()
        self._proj_palette.Click  += self._on_proj_palette

        # Cut master
        self._cut_enabled.Checked   += lambda s, e: self._set_dim(self._cut_controls, True)
        self._cut_enabled.Unchecked += lambda s, e: self._set_dim(self._cut_controls, False)
        # Cut sub-toggles
        self._cut_override_pattern.Checked   += lambda s, e: self._set_dim(self._cut_pattern_row, True)
        self._cut_override_pattern.Unchecked += lambda s, e: self._set_dim(self._cut_pattern_row, False)
        self._cut_override_weight.Checked    += lambda s, e: self._set_dim(self._cut_weight_row, True)
        self._cut_override_weight.Unchecked  += lambda s, e: self._set_dim(self._cut_weight_row, False)
        self._cut_override_color.Checked     += lambda s, e: self._set_dim(self._cut_color_row, True)
        self._cut_override_color.Unchecked   += lambda s, e: self._set_dim(self._cut_color_row, False)
        # Cut sliders
        self._cut_r.ValueChanged += lambda s, e: self._sync_cut_preview()
        self._cut_g.ValueChanged += lambda s, e: self._sync_cut_preview()
        self._cut_b.ValueChanged += lambda s, e: self._sync_cut_preview()
        self._cut_palette.Click  += self._on_cut_palette

        # Surf FG master
        self._surf_fg_enabled.Checked   += lambda s, e: self._set_dim(self._surf_fg_controls, True)
        self._surf_fg_enabled.Unchecked += lambda s, e: self._set_dim(self._surf_fg_controls, False)
        # Surf FG sub-toggles
        self._surf_fg_override_pattern.Checked   += lambda s, e: self._set_dim(self._surf_fg_pattern_dimmer, True)
        self._surf_fg_override_pattern.Unchecked += lambda s, e: self._set_dim(self._surf_fg_pattern_dimmer, False)
        self._surf_fg_override_color.Checked     += lambda s, e: self._set_dim(self._surf_fg_color_row, True)
        self._surf_fg_override_color.Unchecked   += lambda s, e: self._set_dim(self._surf_fg_color_row, False)
        # Surf FG sliders
        self._surf_fg_r.ValueChanged += lambda s, e: self._sync_surf_fg_preview()
        self._surf_fg_g.ValueChanged += lambda s, e: self._sync_surf_fg_preview()
        self._surf_fg_b.ValueChanged += lambda s, e: self._sync_surf_fg_preview()
        self._surf_fg_palette.Click  += self._on_surf_fg_palette

        # Surf BG master
        self._surf_bg_enabled.Checked   += lambda s, e: self._set_dim(self._surf_bg_controls, True)
        self._surf_bg_enabled.Unchecked += lambda s, e: self._set_dim(self._surf_bg_controls, False)
        # Surf BG sub-toggles
        self._surf_bg_override_pattern.Checked   += lambda s, e: self._set_dim(self._surf_bg_pattern_dimmer, True)
        self._surf_bg_override_pattern.Unchecked += lambda s, e: self._set_dim(self._surf_bg_pattern_dimmer, False)
        self._surf_bg_override_color.Checked     += lambda s, e: self._set_dim(self._surf_bg_color_row, True)
        self._surf_bg_override_color.Unchecked   += lambda s, e: self._set_dim(self._surf_bg_color_row, False)
        # Surf BG sliders
        self._surf_bg_r.ValueChanged += lambda s, e: self._sync_surf_bg_preview()
        self._surf_bg_g.ValueChanged += lambda s, e: self._sync_surf_bg_preview()
        self._surf_bg_b.ValueChanged += lambda s, e: self._sync_surf_bg_preview()
        self._surf_bg_palette.Click  += self._on_surf_bg_palette

        self._ok_btn.Click     += self._on_ok
        self._cancel_btn.Click += self._on_cancel

    # ── Preview syncs ────────────────────────
    def _sync_proj_preview(self):
        r, g, b = int(self._proj_r.Value), int(self._proj_g.Value), int(self._proj_b.Value)
        self._proj_r_val.Text = str(r)
        self._proj_g_val.Text = str(g)
        self._proj_b_val.Text = str(b)
        self._proj_preview.Background = make_wpf_brush(r, g, b)

    def _sync_cut_preview(self):
        r, g, b = int(self._cut_r.Value), int(self._cut_g.Value), int(self._cut_b.Value)
        self._cut_r_val.Text = str(r)
        self._cut_g_val.Text = str(g)
        self._cut_b_val.Text = str(b)
        self._cut_preview.Background = make_wpf_brush(r, g, b)

    def _sync_surf_fg_preview(self):
        r, g, b = int(self._surf_fg_r.Value), int(self._surf_fg_g.Value), int(self._surf_fg_b.Value)
        self._surf_fg_r_val.Text = str(r)
        self._surf_fg_g_val.Text = str(g)
        self._surf_fg_b_val.Text = str(b)
        self._surf_fg_preview.Background = make_wpf_brush(r, g, b)

    def _sync_surf_bg_preview(self):
        r, g, b = int(self._surf_bg_r.Value), int(self._surf_bg_g.Value), int(self._surf_bg_b.Value)
        self._surf_bg_r_val.Text = str(r)
        self._surf_bg_g_val.Text = str(g)
        self._surf_bg_b_val.Text = str(b)
        self._surf_bg_preview.Background = make_wpf_brush(r, g, b)

    # ── Palette buttons ──────────────────────
    def _on_proj_palette(self, sender, e):
        res = open_color_dialog(int(self._proj_r.Value), int(self._proj_g.Value), int(self._proj_b.Value))
        if res: self._proj_r.Value, self._proj_g.Value, self._proj_b.Value = res

    def _on_cut_palette(self, sender, e):
        res = open_color_dialog(int(self._cut_r.Value), int(self._cut_g.Value), int(self._cut_b.Value))
        if res: self._cut_r.Value, self._cut_g.Value, self._cut_b.Value = res

    def _on_surf_fg_palette(self, sender, e):
        res = open_color_dialog(int(self._surf_fg_r.Value), int(self._surf_fg_g.Value), int(self._surf_fg_b.Value))
        if res: self._surf_fg_r.Value, self._surf_fg_g.Value, self._surf_fg_b.Value = res

    def _on_surf_bg_palette(self, sender, e):
        res = open_color_dialog(int(self._surf_bg_r.Value), int(self._surf_bg_g.Value), int(self._surf_bg_b.Value))
        if res: self._surf_bg_r.Value, self._surf_bg_g.Value, self._surf_bg_b.Value = res

    # ── OK / Cancel ──────────────────────────
    def _on_ok(self, sender, e):
        cfg = self._cfg

        # Projection
        cfg["use_proj_override"]    = bool(self._proj_enabled.IsChecked)
        cfg["proj_override_pattern"]= bool(self._proj_override_pattern.IsChecked)
        cfg["proj_pattern_name"]    = str(self._proj_pat_cb.SelectedItem) if self._proj_pat_cb.SelectedItem else cfg["proj_pattern_name"]
        cfg["proj_override_weight"] = bool(self._proj_override_weight.IsChecked)
        cfg["proj_weight"]          = int(self._proj_weight.SelectedItem) if self._proj_weight.SelectedItem else 1
        cfg["proj_override_color"]  = bool(self._proj_override_color.IsChecked)
        cfg["proj_color_r"]         = int(self._proj_r.Value)
        cfg["proj_color_g"]         = int(self._proj_g.Value)
        cfg["proj_color_b"]         = int(self._proj_b.Value)

        # Cut
        cfg["use_cut_override"]     = bool(self._cut_enabled.IsChecked)
        cfg["cut_override_pattern"] = bool(self._cut_override_pattern.IsChecked)
        cfg["cut_pattern_name"]     = str(self._cut_pat_cb.SelectedItem) if self._cut_pat_cb.SelectedItem else cfg["cut_pattern_name"]
        cfg["cut_override_weight"]  = bool(self._cut_override_weight.IsChecked)
        cfg["cut_weight"]           = int(self._cut_weight.SelectedItem) if self._cut_weight.SelectedItem else 1
        cfg["cut_override_color"]   = bool(self._cut_override_color.IsChecked)
        cfg["cut_color_r"]          = int(self._cut_r.Value)
        cfg["cut_color_g"]          = int(self._cut_g.Value)
        cfg["cut_color_b"]          = int(self._cut_b.Value)

        # Surf FG
        shared_pattern = str(self._pattern_cb.SelectedItem) if self._pattern_cb.SelectedItem else cfg["surf_fg_pattern_name"]
        cfg["use_surf_fg"]               = bool(self._surf_fg_enabled.IsChecked)
        cfg["surf_fg_override_pattern"]  = bool(self._surf_fg_override_pattern.IsChecked)
        cfg["surf_fg_pattern_name"]      = shared_pattern
        cfg["surf_fg_override_color"]    = bool(self._surf_fg_override_color.IsChecked)
        cfg["surf_fg_r"]                 = int(self._surf_fg_r.Value)
        cfg["surf_fg_g"]                 = int(self._surf_fg_g.Value)
        cfg["surf_fg_b"]                 = int(self._surf_fg_b.Value)

        # Surf BG — shares pattern picker
        cfg["use_surf_bg"]               = bool(self._surf_bg_enabled.IsChecked)
        cfg["surf_bg_override_pattern"]  = bool(self._surf_bg_override_pattern.IsChecked)
        cfg["surf_bg_pattern_name"]      = shared_pattern
        cfg["surf_bg_override_color"]    = bool(self._surf_bg_override_color.IsChecked)
        cfg["surf_bg_r"]                 = int(self._surf_bg_r.Value)
        cfg["surf_bg_g"]                 = int(self._surf_bg_g.Value)
        cfg["surf_bg_b"]                 = int(self._surf_bg_b.Value)

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

    ogs = OverrideGraphicSettings()

    # ── Projection Lines ─────────────────────
    if cfg.get("use_proj_override", True):
        if cfg.get("proj_override_pattern", True):
            pat_id = find_line_pattern_id(doc, cfg["proj_pattern_name"])
            if pat_id != ElementId.InvalidElementId:
                ogs.SetProjectionLinePatternId(pat_id)
        if cfg.get("proj_override_weight", True):
            ogs.SetProjectionLineWeight(int(cfg.get("proj_weight", 1)))
        if cfg.get("proj_override_color", True):
            ogs.SetProjectionLineColor(make_revit_color(cfg["proj_color_r"], cfg["proj_color_g"], cfg["proj_color_b"]))

    # ── Cut Lines ────────────────────────────
    if cfg.get("use_cut_override", True):
        if cfg.get("cut_override_pattern", True):
            pat_id = find_line_pattern_id(doc, cfg["cut_pattern_name"])
            if pat_id != ElementId.InvalidElementId:
                ogs.SetCutLinePatternId(pat_id)
        if cfg.get("cut_override_weight", True):
            ogs.SetCutLineWeight(int(cfg.get("cut_weight", 1)))
        if cfg.get("cut_override_color", True):
            ogs.SetCutLineColor(make_revit_color(cfg["cut_color_r"], cfg["cut_color_g"], cfg["cut_color_b"]))

    # ── Surface FG ───────────────────────────
    if cfg.get("use_surf_fg", True):
        if cfg.get("surf_fg_override_pattern", True):
            fp_id = find_fill_pattern_id(doc, cfg["surf_fg_pattern_name"])
            if fp_id != ElementId.InvalidElementId:
                ogs.SetSurfaceForegroundPatternId(fp_id)
        if cfg.get("surf_fg_override_color", True):
            ogs.SetSurfaceForegroundPatternColor(
                make_revit_color(cfg["surf_fg_r"], cfg["surf_fg_g"], cfg["surf_fg_b"])
            )

    # ── Surface BG ───────────────────────────
    if cfg.get("use_surf_bg", True):
        if cfg.get("surf_bg_override_pattern", True):
            fp_id = find_fill_pattern_id(doc, cfg["surf_bg_pattern_name"])
            if fp_id != ElementId.InvalidElementId:
                ogs.SetSurfaceBackgroundPatternId(fp_id)
        if cfg.get("surf_bg_override_color", True):
            ogs.SetSurfaceBackgroundPatternColor(
                make_revit_color(cfg["surf_bg_r"], cfg["surf_bg_g"], cfg["surf_bg_b"])
            )

    selection = revit.get_selection()
    if not selection:
        forms.alert("No elements selected.", exitscript=True)

    active_view = uidoc.ActiveView

    t = Transaction(doc, "PrasKaa - Set Element Override")
    t.Start()
    try:
        count = 0
        for el in selection:
            try:
                active_view.SetElementOverrides(el.Id, ogs)
                count += 1
            except Exception:
                pass
        t.Commit()
    except Exception as ex:
        t.RollbackIfPending()
        forms.alert("Override failed: {}".format(str(ex)), exitscript=True)

    forms.toast(
        "Applied to {} element(s)".format(count),
        title="Set Element Override",
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