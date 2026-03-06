# -*- coding: utf-8 -*-
__title__ = "Load Plan Manager"
__author__ = "PrasKaa"
__version__ = 'Version: 1.0'
__doc__ = '''Version: 1.0
Date    = 06.03.2026
_____________________________________________________________________
Description:
Comprehensive tool to manage Load Plan Areas with a WPF interface.
Features include area overview, CSV import/export, load value editing,
and color randomization using CIELAB color space.
_____________________________________________________________________
How-to:
1. Ensure "Load Plan by Area" Color Fill Scheme exists
2. Run the tool to open the WPF interface
3. Use the navigation tabs:
   - Areas: View all areas with their colors and loads
   - Create: Create new areas from CSV
   - Set Loads: Update SDL/LL values from CSV
   - Export: Export area data to CSV
   - Randomize: Generate new CIELAB-based colors

____________________________________
Last update:
- [06.03.2026] - 1.0 Initial release
_____________________________________________________________________
Author: PrasKaa'''

import os
import csv
import random
import math

import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('PresentationFramework')
clr.AddReference('PresentationCore')
clr.AddReference('WindowsBase')

from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, BuiltInParameter, Category,
    ColorFillScheme, Transaction, StorageType, UnitUtils, UnitTypeId,
    ViewPlan, ViewType, UV
)
from Autodesk.Revit.DB import Color as RvtColor
from System.Windows import Visibility
from System.Windows.Media import SolidColorBrush, Colors
from System.Windows.Media import Color as WpfColor
from System.Collections.ObjectModel import ObservableCollection
from pyrevit import forms

doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

TARGET_SCHEME_NAME = "Load Plan by Area"

def color_to_hex(r, g, b):
    def to_hex(n):
        h = hex(int(n)).replace('0x', '').replace('L', '').upper()
        return h if len(h) == 2 else '0' + h
    return "#{}{}{}".format(to_hex(r), to_hex(g), to_hex(b))

def get_area_scheme():
    all_schemes = FilteredElementCollector(doc).OfClass(ColorFillScheme).ToElements()
    area_cat_id = Category.GetCategory(doc, BuiltInCategory.OST_Areas).Id
    return next(
        (s for s in all_schemes if s.CategoryId == area_cat_id and s.Name == TARGET_SCHEME_NAME),
        None
    )

def get_param_knm2(area, param_name):
    param = area.LookupParameter(param_name)
    if not param or param.StorageType != StorageType.Double:
        return ''
    val = param.AsDouble()
    if val == 0:
        return '0'
    converted = UnitUtils.ConvertFromInternalUnits(val, UnitTypeId.KilonewtonsPerSquareMeter)
    return str(round(converted, 4))

def set_param_value(element, param_name, new_value_str, is_load_knm2=False):
    param = element.LookupParameter(param_name)
    if not param or param.IsReadOnly:
        return False
    updated = False
    if param.StorageType == StorageType.String:
        if param.AsString() != new_value_str:
            param.Set(new_value_str)
            updated = True
    elif param.StorageType == StorageType.Double:
        try:
            val_double = float(new_value_str)
            val_to_set = UnitUtils.ConvertToInternalUnits(
                val_double, UnitTypeId.KilonewtonsPerSquareMeter) if is_load_knm2 else val_double
            if abs(param.AsDouble() - val_to_set) > 0.0001:
                param.Set(val_to_set)
                updated = True
        except ValueError:
            pass
    elif param.StorageType == StorageType.Integer:
        try:
            new_int = int(new_value_str)
            if param.AsInteger() != new_int:
                param.Set(new_int)
                updated = True
        except ValueError:
            pass
    return updated

def rgb_to_lab(rgb):
    r, g, b = [x / 255.0 for x in rgb]
    def pivot(n):
        return ((n + 0.055) / 1.055) ** 2.4 if n > 0.04045 else n / 12.92
    r, g, b = map(pivot, [r, g, b])
    x = r * 0.4124 + g * 0.3576 + b * 0.1805
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = r * 0.0193 + g * 0.1192 + b * 0.9505
    def f(t):
        return t ** (1.0/3.0) if t > 0.008856 else (7.787 * t) + (16.0/116.0)
    l     = 116.0 * f(y)          - 16.0
    a     = 500.0 * (f(x/0.95047) - f(y))
    b_lab = 200.0 * (f(y)         - f(z/1.08883))
    return (l, a, b_lab)

def perceptual_distance(lab1, lab2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2)))

def generate_cielab_palette(n_colors, k_candidates=200):
    first_rgb = [random.randint(0, 255) for _ in range(3)]
    palette   = [(first_rgb, rgb_to_lab(first_rgb))]
    for _ in range(n_colors - 1):
        best_rgb, max_min_dist = None, -1
        for _ in range(k_candidates):
            cand_rgb = [random.randint(0, 255) for _ in range(3)]
            cand_lab = rgb_to_lab(cand_rgb)
            min_dist = min(perceptual_distance(cand_lab, p[1]) for p in palette)
            if min_dist > max_min_dist:
                max_min_dist = min_dist
                best_rgb = cand_rgb
        palette.append((best_rgb, rgb_to_lab(best_rgb)))
    return [p[0] for p in palette]

class AreaRow(object):
    def __init__(self, name, color_hex, sdl, ll):
        self.Name     = name
        self.ColorHex = color_hex
        self.SDL      = sdl
        self.LL       = ll

class LoadPlanManager(forms.WPFWindow):

    def __init__(self):
        xaml_path = os.path.join(os.path.dirname(__file__), 'ui.xaml')
        forms.WPFWindow.__init__(self, xaml_path)

        def e(name): return self.FindName(name)

        self.PageAreas     = e('PageAreas')
        self.PageCreate    = e('PageCreate')
        self.PageSetLoads  = e('PageSetLoads')
        self.PageExport    = e('PageExport')
        self.PageRandomize = e('PageRandomize')
        self.GridAreas     = e('GridAreas')
        self.TxtAreaCount  = e('TxtAreaCount')
        self.TxtCreateCsv     = e('TxtCreateCsv')
        self.CmbViewCreate    = e('CmbViewCreate')
        self.TxtCreatePreview = e('TxtCreatePreview')
        self.TxtLoadsCsv      = e('TxtLoadsCsv')
        self.RbNewCsv         = e('RbNewCsv')
        self.RbUpdateCsv      = e('RbUpdateCsv')
        self.PanelExistingCsv = e('PanelExistingCsv')
        self.TxtExistingCsv   = e('TxtExistingCsv')
        self.SliderCandidates = e('SliderCandidates')
        self.TxtCandidateVal  = e('TxtCandidateVal')
        self.TxtStatus        = e('TxtStatus')
        self.StatusDot        = e('StatusDot')

        e('NavAreas').Checked              += self.NavAreas_Checked
        e('NavCreate').Checked             += self.NavCreate_Checked
        e('NavSetLoads').Checked           += self.NavSetLoads_Checked
        e('NavExport').Checked             += self.NavExport_Checked
        e('NavRandomize').Checked          += self.NavRandomize_Checked
        e('BtnRefresh').Click              += self.BtnRefresh_Click
        e('BtnSyncNumbers').Click          += self.BtnSyncNumbers_Click
        e('BtnBrowseCreate').Click         += self.BtnBrowseCreate_Click
        e('BtnCreateAreas').Click          += self.BtnCreateAreas_Click
        e('BtnBrowseLoads').Click          += self.BtnBrowseLoads_Click
        e('BtnSetLoads').Click             += self.BtnSetLoads_Click
        e('BtnExport').Click               += self.BtnExport_Click
        e('BtnBrowseExisting').Click       += self.BtnBrowseExisting_Click
        e('BtnRandomize').Click            += self.BtnRandomize_Click
        self.RbNewCsv.Checked              += self.ExportMode_Changed
        self.RbUpdateCsv.Checked           += self.ExportMode_Changed
        self.SliderCandidates.ValueChanged += self.SliderCandidates_Changed

        self._load_views()
        self._refresh_areas()
        self.ShowDialog()

    # ── NAVIGATION ──────────────────────────────

    def _show_page(self, page):
        for p in [self.PageAreas, self.PageCreate,
                  self.PageSetLoads, self.PageExport, self.PageRandomize]:
            p.Visibility = Visibility.Collapsed
        page.Visibility = Visibility.Visible

    def NavAreas_Checked(self, s, e):     self._show_page(self.PageAreas)
    def NavCreate_Checked(self, s, e):    self._show_page(self.PageCreate)
    def NavSetLoads_Checked(self, s, e):  self._show_page(self.PageSetLoads)
    def NavExport_Checked(self, s, e):    self._show_page(self.PageExport)
    def NavRandomize_Checked(self, s, e): self._show_page(self.PageRandomize)

    # ── STATUS ──────────────────────────────────

    def _set_status(self, msg, ok=True):
        self.TxtStatus.Text = msg
        self.StatusDot.Fill = SolidColorBrush(Colors.LimeGreen if ok else Colors.OrangeRed)

    # ── AREA OVERVIEW ────────────────────────────

    def _refresh_areas(self):
        scheme = get_area_scheme()
        if not scheme:
            self._set_status("Scheme '{}' not found.".format(TARGET_SCHEME_NAME), ok=False)
            return

        color_map = {}
        for entry in scheme.GetEntries():
            name = entry.GetStringValue()
            if name:
                color_map[name] = (entry.Color.Red, entry.Color.Green, entry.Color.Blue)

        areas = FilteredElementCollector(doc)\
            .OfCategory(BuiltInCategory.OST_Areas)\
            .WhereElementIsNotElementType().ToElements()

        area_data = {}
        for area in areas:
            p = area.LookupParameter("Name")
            if p:
                n = p.AsString()
                if n:
                    area_data[n] = {
                        'sdl': get_param_knm2(area, 'SDL'),
                        'll' : get_param_knm2(area, 'LL')
                    }

        rows = ObservableCollection[object]()
        for name, (r, g, b) in color_map.items():
            hex_code = color_to_hex(r, g, b)
            data     = area_data.get(name, {'sdl': '-', 'll': '-'})
            rows.Add(AreaRow(name, hex_code, data['sdl'], data['ll']))

        self.GridAreas.ItemsSource = rows
        self.TxtAreaCount.Text = "{} areas loaded".format(len(rows))
        self._set_status("Loaded {} areas from '{}'.".format(len(rows), TARGET_SCHEME_NAME))

    def BtnRefresh_Click(self, s, e):
        self._refresh_areas()

    # ── SYNC NUMBERS ─────────────────────────────

    def _sync_area_numbers(self):
        areas = FilteredElementCollector(doc)\
            .OfCategory(BuiltInCategory.OST_Areas)\
            .WhereElementIsNotElementType().ToElements()

        # Build Name -> Number mapping, sorted alphabetically
        unique_names = sorted(set(
            area.LookupParameter("Name").AsString()
            for area in areas
            if area.LookupParameter("Name") and area.LookupParameter("Name").AsString()
        ))
        name_to_number = {name: str(i + 1) for i, name in enumerate(unique_names)}

        updated = 0
        t = Transaction(doc, "Sync Area Numbers")
        t.Start()
        for area in areas:
            p_name   = area.LookupParameter("Name")
            p_number = area.get_Parameter(BuiltInParameter.ROOM_NUMBER)
            if not p_name or not p_number or p_number.IsReadOnly:
                continue
            name = p_name.AsString()
            if name and name in name_to_number:
                expected = name_to_number[name]
                if p_number.AsString() != expected:
                    try:
                        p_number.Set(expected)
                        updated += 1
                    except:
                        pass
        t.Commit()

        self._set_status("Numbers synced. {} areas updated.".format(updated))
        self._refresh_areas()

    def BtnSyncNumbers_Click(self, s, e):
        self._sync_area_numbers()

    # ── CREATE AREAS ─────────────────────────────

    def _load_views(self):
        views = [v for v in FilteredElementCollector(doc)
                 .OfClass(ViewPlan).ToElements()
                 if v.ViewType == ViewType.AreaPlan and not v.IsTemplate]
        self.CmbViewCreate.Items.Clear()
        for v in sorted(views, key=lambda x: x.Name):
            self.CmbViewCreate.Items.Add(v.Name)
        if self.CmbViewCreate.Items.Count > 0:
            self.CmbViewCreate.SelectedIndex = 0
        self._view_map = {v.Name: v for v in views}

    def BtnBrowseCreate_Click(self, s, e):
        path = forms.pick_file(file_ext='csv', title='Pilih CSV')
        if not path:
            return
        self.TxtCreateCsv.Text       = path
        self.TxtCreateCsv.Foreground = SolidColorBrush(WpfColor.FromRgb(232, 234, 240))
        try:
            names = []
            with open(path, 'r') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if row and row[0].strip():
                        names.append(row[0].strip())
            preview = ", ".join(names[:5]) + ("..." if len(names) > 5 else "")
            self.TxtCreatePreview.Text = "Preview: {} areas - {}".format(len(names), preview)
        except Exception as ex:
            self.TxtCreatePreview.Text = "Error: {}".format(str(ex))

    def BtnCreateAreas_Click(self, s, e):
        path = self.TxtCreateCsv.Text
        if not path or not os.path.exists(path):
            self._set_status("Please select a valid CSV file.", ok=False)
            return
        view_name = self.CmbViewCreate.SelectedItem
        if not view_name or view_name not in self._view_map:
            self._set_status("Please select an Area Plan View.", ok=False)
            return
        target_view = self._view_map[view_name]
        names = []
        with open(path, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if row and row[0].strip():
                    names.append(row[0].strip())

        created, failed = [], []
        t = Transaction(doc, "Create Areas from CSV")
        t.Start()
        for i, name in enumerate(names):
            try:
                uv   = UV(i * 0.1, 0)
                area = doc.Create.NewArea(target_view, uv)
                area.LookupParameter("Name").Set(name)
                created.append(name)
            except Exception as ex:
                failed.append((name, str(ex)))
        t.Commit()

        self._set_status("Created {}. Failed: {}.".format(len(created), len(failed)),
                         ok=len(failed) == 0)
        self._refresh_areas()

    # ── SET SDL & LL ─────────────────────────────

    def BtnBrowseLoads_Click(self, s, e):
        path = forms.pick_file(file_ext='csv', title='Pilih CSV')
        if path:
            self.TxtLoadsCsv.Text       = path
            self.TxtLoadsCsv.Foreground = SolidColorBrush(WpfColor.FromRgb(232, 234, 240))

    def BtnSetLoads_Click(self, s, e):
        path = self.TxtLoadsCsv.Text
        if not path or not os.path.exists(path):
            self._set_status("Please select a valid CSV file.", ok=False)
            return
        mapping = {}
        with open(path, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if len(row) >= 3 and row[0].strip():
                    mapping[row[0].strip()] = {'sdl': row[1].strip(), 'll': row[2].strip()}

        areas = FilteredElementCollector(doc)\
            .OfCategory(BuiltInCategory.OST_Areas)\
            .WhereElementIsNotElementType().ToElements()

        count = 0
        t = Transaction(doc, "Update Area Loads")
        t.Start()
        for area in areas:
            p = area.LookupParameter("Name")
            if not p: continue
            name = p.AsString()
            if name in mapping:
                data = mapping[name]
                if set_param_value(area, 'SDL', data['sdl'], is_load_knm2=True): count += 1
                if set_param_value(area, 'LL',  data['ll'],  is_load_knm2=True): count += 1
        t.Commit()

        self._set_status("Updated {} parameters.".format(count))
        self._refresh_areas()

    # ── EXPORT COLORS ────────────────────────────

    def ExportMode_Changed(self, s, e):
        self.PanelExistingCsv.Visibility = \
            Visibility.Visible if self.RbUpdateCsv.IsChecked else Visibility.Collapsed

    def BtnBrowseExisting_Click(self, s, e):
        path = forms.pick_file(file_ext='csv', title='Pilih CSV')
        if path:
            self.TxtExistingCsv.Text       = path
            self.TxtExistingCsv.Foreground = SolidColorBrush(WpfColor.FromRgb(232, 234, 240))

    def BtnExport_Click(self, s, e):
        scheme = get_area_scheme()
        if not scheme:
            self._set_status("Scheme not found.", ok=False)
            return

        color_map = {}
        for entry in scheme.GetEntries():
            name = entry.GetStringValue()
            if name:
                color_map[name] = color_to_hex(
                    entry.Color.Red, entry.Color.Green, entry.Color.Blue)

        areas = FilteredElementCollector(doc)\
            .OfCategory(BuiltInCategory.OST_Areas)\
            .WhereElementIsNotElementType().ToElements()
        area_data = {}
        for area in areas:
            p = area.LookupParameter("Name")
            if p:
                n = p.AsString()
                if n:
                    area_data[n] = {
                        'sdl': get_param_knm2(area, 'SDL'),
                        'll' : get_param_knm2(area, 'LL')
                    }

        if self.RbNewCsv.IsChecked:
            save_path = forms.save_file(file_ext='csv', title='Simpan CSV Baru')
            if not save_path: return
            with open(save_path, 'wb') as f:
                writer = csv.writer(f)
                writer.writerow(['Name', 'SDL', 'LL', 'Color'])
                for name, hex_code in sorted(color_map.items()):
                    d = area_data.get(name, {'sdl': '', 'll': ''})
                    writer.writerow([name, d['sdl'], d['ll'], hex_code])
            self._set_status("Exported {} rows to new CSV.".format(len(color_map)))
        else:
            path = self.TxtExistingCsv.Text
            if not path or not os.path.exists(path):
                self._set_status("Please select an existing CSV file.", ok=False)
                return
            rows = []
            with open(path, 'rb') as f:
                reader = csv.reader(f)
                header = next(reader)
                for row in reader:
                    rows.append(row)
            if 'Color' not in header:
                header.append('Color')
            color_col = header.index('Color')
            updated = 0
            for row in rows:
                while len(row) <= color_col:
                    row.append('')
                name = row[0].strip()
                if name in color_map:
                    row[color_col] = color_map[name]
                    updated += 1
            with open(path, 'wb') as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerows(rows)
            self._set_status("Updated {} rows in existing CSV.".format(updated))

    # ── RANDOMIZE ────────────────────────────────

    def SliderCandidates_Changed(self, s, e):
        self.TxtCandidateVal.Text = str(int(self.SliderCandidates.Value))

    def BtnRandomize_Click(self, s, e):
        scheme = get_area_scheme()
        if not scheme:
            self._set_status("Scheme not found.", ok=False)
            return
        entries = scheme.GetEntries()
        n = len(entries)
        k = int(self.SliderCandidates.Value)
        self._set_status("Generating {} colors (k={})...".format(n, k))
        palette = generate_cielab_palette(n_colors=n, k_candidates=k)
        t = Transaction(doc, "Randomize Area Colors CIELAB")
        t.Start()
        for i, entry in enumerate(entries):
            rgb = palette[i]
            entry.Color = RvtColor(rgb[0], rgb[1], rgb[2])
            scheme.UpdateEntry(entry)
        t.Commit()
        self._set_status("Applied {} new CIELAB colors.".format(n))
        self._refresh_areas()


LoadPlanManager()