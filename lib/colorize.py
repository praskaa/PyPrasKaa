# -*- coding: utf-8 -*-
"""
colorize.py - PrasKaaPyKitv2
Author : PrasKaa
Updated: CIELAB-based perceptually-uniform color generation

Public API (unchanged):
    get_colours(n)
    override_options
    default_override_options
    OVERRIDES_CONFIG_OPTION_NAME
    CATEGORIES_CONFIG_OPTION_NAME
    COLORIZE_ONLY_CATEGORIES
    COLORIZE_ONLY_CONFIG_OPTION_NAME
    ChosenItem
    get_config / save_config / load_configs
    get_categories_config / get_colorize_only_categories_config
    config_overrides / config_category_overrides
    set_colour_overrides_by_option
"""

import math
import random
from collections import defaultdict

from pyrevit import forms
from pyrevit import revit, DB
from pyrevit import script

from database import (
    frequent_category_labels,
    model_categories_dict,
    category_labels_to_bic,
    get_solid_fill_pat,
)


# ─────────────────────────────────────────────────────────────────────────────
# CIELAB color space utilities
# ─────────────────────────────────────────────────────────────────────────────

def _lab_to_xyz(L, a, b):
    """Convert CIELAB → XYZ (D65 illuminant)."""
    Xn, Yn, Zn = 0.95047, 1.00000, 1.08883

    fy = (L + 16.0) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b / 200.0

    def _f_inv(t):
        return t ** 3 if t > 0.20689303 else (t - 16.0 / 116.0) * 3.0 * (6.0 / 29.0) ** 2

    return Xn * _f_inv(fx), Yn * _f_inv(fy), Zn * _f_inv(fz)


def _xyz_to_linear_rgb(X, Y, Z):
    """Convert XYZ → linear sRGB (values may be outside [0, 1])."""
    r =  3.2404542 * X - 1.5371385 * Y - 0.4985314 * Z
    g = -0.9692660 * X + 1.8760108 * Y + 0.0415560 * Z
    b =  0.0556434 * X - 0.2040259 * Y + 1.0572252 * Z
    return r, g, b


def _linear_to_srgb(c):
    """Apply sRGB gamma to a single linear channel, clamped to [0, 1]."""
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1.0 / 2.4)) - 0.055


def _lab_to_rgb255(L, a, b):
    """Convert LAB → XYZ → linear RGB → sRGB → (R, G, B) uint8 tuple."""
    X, Y, Z = _lab_to_xyz(L, a, b)
    r, g, bl = _xyz_to_linear_rgb(X, Y, Z)
    return (
        int(round(_linear_to_srgb(r)  * 255)),
        int(round(_linear_to_srgb(g)  * 255)),
        int(round(_linear_to_srgb(bl) * 255)),
    )


def _is_in_srgb_gamut(L, a, b, tol=0.01):
    """Return True if the LAB point is within the sRGB gamut."""
    X, Y, Z = _lab_to_xyz(L, a, b)
    r, g, bl = _xyz_to_linear_rgb(X, Y, Z)
    return all(-tol <= c <= 1.0 + tol for c in (r, g, bl))


def _clip_chroma_to_gamut(L, a, b, steps=16):
    """
    Reduce chroma (a*, b*) via binary search until the point is inside sRGB.
    Hue angle and L* are preserved; only the chroma magnitude is reduced.
    """
    if _is_in_srgb_gamut(L, a, b):
        return L, a, b

    lo, hi = 0.0, 1.0
    for _ in range(steps):
        mid = (lo + hi) / 2.0
        if _is_in_srgb_gamut(L, a * mid, b * mid):
            lo = mid
        else:
            hi = mid
    return L, a * lo, b * lo


def _delta_e(lab1, lab2):
    """CIE76 Delta E between two LAB points."""
    return math.sqrt(
        (lab1[0] - lab2[0]) ** 2 +
        (lab1[1] - lab2[1]) ** 2 +
        (lab1[2] - lab2[2]) ** 2
    )


def _build_candidate_pool(n_candidates=512, seed=42):
    """
    Sample candidate colors in LAB space within perceptually safe bounds:
      L* ∈ [35, 85]   – avoid near-black and near-white
      C* ∈ [30, 110]  – vivid, not pastel
    Only candidates that survive gamut clipping with C* ≥ 25 are kept.
    """
    rng = random.Random(seed)
    candidates = []

    while len(candidates) < n_candidates:
        L = rng.uniform(35.0, 85.0)
        chroma  = rng.uniform(30.0, 110.0)
        hue_rad = rng.uniform(0.0, 2.0 * math.pi)
        a_raw = chroma * math.cos(hue_rad)
        b_raw = chroma * math.sin(hue_rad)

        L_c, a_c, b_c = _clip_chroma_to_gamut(L, a_raw, b_raw)
        if math.sqrt(a_c ** 2 + b_c ** 2) >= 25.0:
            candidates.append((L_c, a_c, b_c))

    return candidates


def get_colours(n, seed=42):
    """
    Generate n DB.Color values that are perceptually distinct from each other,
    using CIELAB color space and farthest-point (maximin) selection.

    Algorithm:
      1. Build a pool of 512+ candidates in LAB space (L* 35-85, C* 30-110).
      2. First color: candidate whose L* is closest to 60 (mid-tone anchor).
      3. Each subsequent color: candidate that maximises min(ΔE) to all
         already-selected colors  ← the "farthest point" / maximin rule.
      4. Convert LAB → sRGB → DB.Color.

    Args:
        n    : number of colors required
        seed : random seed for reproducibility (pass doc.Title.__hash__()
               to vary per project)

    Returns:
        list[DB.Color]
    """
    if n == 0:
        return []

    candidates = _build_candidate_pool(
        n_candidates=max(512, n * 20),
        seed=seed,
    )

    # Anchor: L* closest to 60 (mid-perceptual-brightness)
    first = min(candidates, key=lambda c: abs(c[0] - 60.0))
    selected = [first]
    remaining = [c for c in candidates if c != first]

    # min_dist[i] = current minimum ΔE from remaining[i] to any selected color
    min_dist = [_delta_e(c, first) for c in remaining]

    for _ in range(n - 1):
        if not remaining:
            break
        best_idx = max(range(len(remaining)), key=lambda i: min_dist[i])
        chosen = remaining[best_idx]
        selected.append(chosen)

        # Update running min-distances incrementally (O(remaining) per step)
        del remaining[best_idx]
        del min_dist[best_idx]
        for i, c in enumerate(remaining):
            d = _delta_e(c, chosen)
            if d < min_dist[i]:
                min_dist[i] = d

    return [DB.Color(*_lab_to_rgb255(*lab)) for lab in selected]


# ─────────────────────────────────────────────────────────────────────────────
# Override / config constants
# ─────────────────────────────────────────────────────────────────────────────

override_options = [
    "Projection Line Colour",
    "Projection Surface Colour",
    "Cut Line Colour",
    "Cut Pattern Colour",
]
default_override_options = ["Projection Surface Colour", "Cut Pattern Colour"]

OVERRIDES_CONFIG_OPTION_NAME      = "overrides"
CATEGORIES_CONFIG_OPTION_NAME     = "colorize_categories"
COLORIZE_ONLY_CONFIG_OPTION_NAME  = "colorize_only_categories"

# Categories that support element overrides but NOT parameter filters
COLORIZE_ONLY_CATEGORIES = [
    DB.BuiltInCategory.OST_GenericAnnotation,
]


# ─────────────────────────────────────────────────────────────────────────────
# UI helpers
# ─────────────────────────────────────────────────────────────────────────────

class ChosenItem(forms.TemplateListItem):
    """Simple wrapper for SelectFromList items."""
    @property
    def name(self):
        return str(self.item)


# ─────────────────────────────────────────────────────────────────────────────
# Config helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_config(config_set, option_name, default_options):
    """Read a config option, writing defaults if it has never been set."""
    prev_choice = config_set.get_option(option_name, [])
    if not prev_choice:
        save_config(list(default_options), option_name, config_set)
        prev_choice = config_set.get_option(option_name, [])
    return prev_choice


def save_config(chosen, option_name, config):
    """Persist a list value to the given config."""
    config.set_option(option_name, chosen)


def load_configs(config, option_name, default_option):
    """Return saved config list, falling back to default_option."""
    ovrds = config.get_option(option_name, [])
    items = [x for x in (ovrds or default_option)]
    if not ovrds:
        items = list(default_option)
    return filter(None, items)


def get_categories_config(doc):
    """
    Return {localized_label: BuiltInCategory} for the user's saved
    frequent categories (defaults to frequent_category_labels()).
    """
    categories_config = script.get_config(CATEGORIES_CONFIG_OPTION_NAME)
    default_names     = frequent_category_labels()
    names_list        = get_config(categories_config, CATEGORIES_CONFIG_OPTION_NAME, default_names)
    return category_labels_to_bic(names_list, doc)


def get_colorize_only_categories_config(doc):
    """
    Return {localized_label: BuiltInCategory} for Colorize-by-Value, which
    includes the standard user config categories PLUS COLORIZE_ONLY_CATEGORIES
    (annotations etc. that support overrides but not filter rules).
    """
    config = get_categories_config(doc)

    for bic in COLORIZE_ONLY_CATEGORIES:
        try:
            label = DB.LabelUtils.GetLabelFor(bic)
            if label not in config:
                config[label] = bic
        except Exception:
            pass

    return config


# ─────────────────────────────────────────────────────────────────────────────
# Interactive config dialogs
# ─────────────────────────────────────────────────────────────────────────────

def config_overrides(config, option_name):
    """Show a dialog to let the user pick which override styles to apply."""
    prev_ovrds = load_configs(config, option_name, default_override_options)
    opts = [ChosenItem(x, checked=x in prev_ovrds) for x in override_options]
    overrides = forms.SelectFromList.show(
        sorted(opts),
        title="Choose Override Styles",
        button_name="Remember",
        multiselect=True,
    )
    if overrides:
        save_config([x for x in overrides if x], option_name, config)


def config_category_overrides(doc):
    """Show a dialog to let the user pick their frequent categories."""
    categories_config = script.get_config(CATEGORIES_CONFIG_OPTION_NAME)
    prev_cat = load_configs(
        categories_config,
        CATEGORIES_CONFIG_OPTION_NAME,
        frequent_category_labels(),
    )
    cat_options = [
        ChosenItem(x, checked=x in prev_cat)
        for x in model_categories_dict(doc)
    ]
    selection = forms.SelectFromList.show(
        sorted(cat_options, key=lambda x: x.name),
        title="Frequent Categories List",
        button_name="Choose Categories",
        multiselect=True,
    )
    if selection:
        save_config(
            [x for x in selection if x],
            CATEGORIES_CONFIG_OPTION_NAME,
            categories_config,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Override application
# ─────────────────────────────────────────────────────────────────────────────

def set_colour_overrides_by_option(overrides_option, colour, doc):
    """
    Build a DB.OverrideGraphicSettings object for the given colour,
    applying only the override channels listed in overrides_option.
    """
    override        = DB.OverrideGraphicSettings()
    solid_fill_id   = get_solid_fill_pat(doc).Id

    if "Projection Line Colour" in overrides_option:
        override.SetProjectionLineColor(colour)
    if "Cut Line Colour" in overrides_option:
        override.SetCutLineColor(colour)
    if "Projection Surface Colour" in overrides_option:
        override.SetSurfaceForegroundPatternColor(colour)
        override.SetSurfaceForegroundPatternId(solid_fill_id)
    if "Cut Pattern Colour" in overrides_option:
        override.SetCutForegroundPatternColor(colour)
        override.SetCutForegroundPatternId(solid_fill_id)

    return override