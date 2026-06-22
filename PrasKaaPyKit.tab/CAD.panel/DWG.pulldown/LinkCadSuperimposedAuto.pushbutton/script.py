# -*- coding: utf-8 -*-
"""
Link CAD Batch - PrasKaaPyKitv2
Batch link DWG/DXF files to floor plan views with WPF UI.
Author: PrasKaa
Version: 2.0
"""

__title__ = "Link CAD\nSuperimposed Batch"
__doc__ = """2025.01.01 - v2.0
Batch link DWG/DXF files to floor plan views.
Scan folder -> pair CAD to views -> set X/Y offset -> link all at once."""

import os
import System
import traceback

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("WindowsBase")
clr.AddReference("PresentationCore")
clr.AddReference("PresentationFramework")
from System.Windows.Forms import FolderBrowserDialog, DialogResult
from System.Collections.ObjectModel import ObservableCollection

from pyrevit import HOST_APP, DB, forms, script
from pyrevit import output as pyoutput

logger = script.get_logger()
op     = pyoutput.get_output()

doc = HOST_APP.doc

# unit conversion — Revit 2024+ uses UnitTypeId
try:
    def mm_to_ft(mm):
        return DB.UnitUtils.ConvertToInternalUnits(mm, DB.UnitTypeId.Millimeters)
    mm_to_ft(1.0)
except Exception:
    def mm_to_ft(mm):
        return DB.UnitUtils.ConvertToInternalUnits(mm, DB.DisplayUnitType.DUT_MILLIMETERS)


# =============================================================================
# HELPERS
# =============================================================================

def get_floor_plan_views():
    PLAN_TYPES = (DB.ViewType.FloorPlan, DB.ViewType.EngineeringPlan)
    views = []
    for v in DB.FilteredElementCollector(doc).OfClass(DB.View).ToElements():
        if not v.IsTemplate and v.ViewType in PLAN_TYPES:
            views.append(v)
    views.sort(key=lambda v: v.Name)
    return views


def scan_cad_files(folder):
    files = []
    for fname in sorted(os.listdir(folder)):
        ext = os.path.splitext(fname)[1].lower()
        if ext in (".dwg", ".dxf"):
            files.append({"name": fname, "path": os.path.join(folder, fname), "ext": ext})
    return files


def get_already_linked_names(view_id):
    names = []
    try:
        for inst in DB.FilteredElementCollector(doc, view_id).OfClass(DB.ImportInstance).ToElements():
            lt = doc.GetElement(inst.GetTypeId())
            if lt:
                try:
                    names.append(os.path.basename(
                        lt.GetExternalFileReference().GetAbsolutePath()).lower())
                except Exception:
                    pass
                try:
                    names.append(lt.Name.lower())
                except Exception:
                    pass
    except Exception:
        pass
    return names


def auto_match_views(cad_files, views):
    """Score CAD filename vs view name by shared words."""
    result = {}
    for cf in cad_files:
        base = os.path.splitext(cf["name"])[0].lower()
        base = base.replace("_", " ").replace("-", " ").replace(".", " ")
        words_cad = set(w for w in base.split() if len(w) > 1)
        best_view, best_score = None, 0
        for v in views:
            vlow = v.Name.lower().replace("_", " ").replace("-", " ").replace(".", " ")
            words_v = set(w for w in vlow.split() if len(w) > 1)
            score = len(words_cad & words_v)
            if score > best_score:
                best_view, best_score = v, score
        result[cf["name"]] = best_view if best_score > 0 else None
    return result


def _safe_float(s, default=0.0):
    try:
        return float(str(s).replace(",", "."))
    except Exception:
        return default


# =============================================================================
# ROW VIEW MODEL  (bound to DataGrid)
# =============================================================================

class PairRow(object):
    """One row in the DataGrid — holds all editable fields."""
    def __init__(self, cad_file, view=None):
        self.Enabled  = True
        self.CadName  = cad_file["name"]
        self.CadExt   = cad_file["ext"].upper().lstrip(".")
        self.CadPath  = cad_file["path"]
        self.ViewName = view.Name if view else ""
        self._view    = view        # resolved Revit View object
        self.OffsetX  = "0"
        self.OffsetY  = "0"
        self.Status   = "⏳ pending"


# =============================================================================
# WPF DIALOG
# =============================================================================

class LinkCADBatchDialog(forms.WPFWindow):

    def __init__(self, views):
        forms.WPFWindow.__init__(self, "ui.xaml")
        self._all_views = views
        self._view_map  = {v.Name: v for v in views}   # name -> View
        self._rows      = ObservableCollection[object]()
        self._folder    = None

        # Wire events
        self.BtnBrowse.Click      += self._on_browse
        self.BtnAutoMatch.Click   += self._on_auto_match
        self.BtnApplyOffset.Click += self._on_apply_offset
        self.BtnLink.Click        += self._on_link

        # Event delegation — intercept BtnPickView clicks at DataGrid level
        self.PairingGrid.PreviewMouseLeftButtonUp += self._on_grid_mouse_up

        self._update_status()

    # ------------------------------------------------------------------
    # BROWSE
    # ------------------------------------------------------------------
    def _on_browse(self, sender, args):
        dlg = FolderBrowserDialog()
        dlg.Description = "Pilih folder yang berisi file DWG/DXF"
        if dlg.ShowDialog() != DialogResult.OK:
            return
        self._folder = dlg.SelectedPath
        self.TxtFolder.Text       = self._folder
        self.TxtFolder.Foreground = self._brush("#CDD6F4")

        cad_files = scan_cad_files(self._folder)
        if not cad_files:
            forms.alert("Tidak ada file DWG/DXF di folder tersebut.", title="Link CAD Batch")
            return

        self._rows.Clear()
        for cf in cad_files:
            self._rows.Add(PairRow(cf))
        self.PairingGrid.ItemsSource = self._rows
        self._update_status()

    # ------------------------------------------------------------------
    # AUTO MATCH
    # ------------------------------------------------------------------
    def _on_auto_match(self, sender, args):
        if not self._rows:
            forms.alert("Browse folder dulu.", title="Link CAD Batch")
            return

        cad_files = [{"name": r.CadName, "path": r.CadPath, "ext": r.CadExt}
                     for r in self._rows]
        matched = auto_match_views(cad_files, self._all_views)

        for row in self._rows:
            v = matched.get(row.CadName)
            if v:
                row.ViewName = v.Name
                row._view    = v
                row.Status   = "✅ matched"
            else:
                row.Status   = "⚠ no match"

        self._refresh_grid()
        self._update_status()

    # ------------------------------------------------------------------
    # APPLY OFFSET TO ALL
    # ------------------------------------------------------------------
    def _on_apply_offset(self, sender, args):
        gx = _safe_float(self.TxtOffsetX.Text, 0.0)
        gy = _safe_float(self.TxtOffsetY.Text, 0.0)
        for row in self._rows:
            row.OffsetX = str(gx)
            row.OffsetY = str(gy)
        self._refresh_grid()

    # ------------------------------------------------------------------
    # EVENT DELEGATION — catch BtnPickView clicks at DataGrid level
    # ------------------------------------------------------------------
    def _on_grid_mouse_up(self, sender, args):
        """Intercept clicks on any BtnPickView button via event delegation."""
        try:
            from System.Windows.Media import VisualTreeHelper
            from System.Windows.Controls import Button

            # Walk up visual tree from clicked element to find Button named BtnPickView
            el = args.OriginalSource
            while el is not None:
                try:
                    if isinstance(el, Button) and getattr(el, 'Name', '') == 'BtnPickView':
                        row = el.Tag
                        if isinstance(row, PairRow):
                            self._pick_view_for_row(row)
                        return
                    el = VisualTreeHelper.GetParent(el)
                except Exception:
                    break
        except Exception:
            pass

    def _pick_view_for_row(self, row):
        """Open pyRevit SelectFromList for choosing a view."""
        view_names = sorted(self._view_map.keys())
        chosen = forms.SelectFromList.show(
            view_names,
            title="Pilih View untuk: {}".format(row.CadName),
            multiselect=False,
            button_name="Pilih"
        )
        if chosen:
            row.ViewName = chosen
            row._view    = self._view_map.get(chosen)
            row.Status   = "✅ ready"
            self._refresh_grid()
            self._update_status()



    def _resolve_view(self, name):
        """Exact match first, then partial."""
        low = name.lower()
        # exact
        for vname, v in self._view_map.items():
            if vname.lower() == low:
                return v
        # partial
        for vname, v in self._view_map.items():
            if low in vname.lower() or vname.lower() in low:
                return v
        return None

    # ------------------------------------------------------------------
    # LINK
    # ------------------------------------------------------------------
    def _on_link(self, sender, args):
        # Validate first
        active = []
        for row in self._rows:
            if not row.Enabled:
                continue
            if not row._view:
                v = self._resolve_view(row.ViewName)
                if v:
                    row._view   = v
                    row.ViewName = v.Name
                    row.Status  = "✅ ready"
                else:
                    row.Status  = "❌ view not found"
                    continue
            active.append(row)

        self._refresh_grid()

        if not active:
            forms.alert("Tidak ada pair valid untuk diproses.\nPastikan View Name sudah benar.",
                        title="Link CAD Batch")
            return

        skip_existing = self.ChkSkipExisting.IsChecked

        success, skipped, failed = 0, 0, 0
        log = []

        t = DB.Transaction(doc, "PrasKaa - Link CAD Batch v2")
        t.Start()
        try:
            from Autodesk.Revit.DB import ImportInstance as ImpInst

            for row in active:
                view = row._view

                # Skip existing
                if skip_existing:
                    existing = get_already_linked_names(view.Id)
                    cad_lower = row.CadName.lower()
                    if any(cad_lower in e for e in existing):
                        row.Status = "⏭ already linked"
                        skipped += 1
                        log.append("SKIP  | {} -> {}".format(row.CadName, view.Name))
                        continue

                try:
                    opts = DB.DWGImportOptions()
                    opts.ColorMode    = DB.ImportColorMode.Preserved
                    opts.ThisViewOnly = True
                    opts.Unit         = DB.ImportUnit.Millimeter

                    import_inst, _llr = ImpInst.Create(doc, view, row.CadPath, opts)
                    link_id = import_inst.Id if import_inst else DB.ElementId.InvalidElementId

                    if link_id != DB.ElementId.InvalidElementId:
                        ox = _safe_float(row.OffsetX, 0.0)
                        oy = _safe_float(row.OffsetY, 0.0)
                        if abs(ox) > 1e-9 or abs(oy) > 1e-9:
                            elem = doc.GetElement(link_id)
                            was_pinned = elem.Pinned
                            if was_pinned:
                                elem.Pinned = False
                            DB.ElementTransformUtils.MoveElement(
                                doc, link_id,
                                DB.XYZ(mm_to_ft(ox), mm_to_ft(oy), 0.0)
                            )
                            if was_pinned:
                                elem.Pinned = True
                        row.Status = "✅ linked"
                        success += 1
                        log.append("OK    | {} -> {}  ({},{})mm".format(
                            row.CadName, view.Name, ox, oy))
                    else:
                        row.Status = "❌ failed"
                        failed += 1
                        log.append("FAIL  | {} -> {}".format(row.CadName, view.Name))

                except Exception as ex:
                    row.Status = "❌ {}".format(str(ex)[:50])
                    failed += 1
                    log.append("ERR   | {} -> {}  {}".format(row.CadName, view.Name, str(ex)))

            t.Commit()

        except Exception as outer:
            try:
                t.RollBack()
            except Exception:
                pass
            forms.alert("Transaction error:\n{}".format(str(outer)), title="Error")
            self._refresh_grid()
            return

        self._refresh_grid()
        self._update_status()

        # Output report
        summary = "✅ Linked: {}  |  ⏭ Skipped: {}  |  ❌ Failed: {}".format(
            success, skipped, failed)
        self.TxtStatus.Text = summary

        op.print_md("## Link CAD Batch — Hasil")
        op.print_md("**{}**".format(summary))
        op.print_md("---")
        op.print_md("```\n{}\n```".format("\n".join(log)))

        forms.alert(
            "Selesai!\n\n{}".format(summary),
            title="Link CAD Batch"
        )

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    def _refresh_grid(self):
        """Force DataGrid to re-read rows."""
        src = self.PairingGrid.ItemsSource
        self.PairingGrid.ItemsSource = None
        self.PairingGrid.ItemsSource = src

    def _update_status(self):
        total   = len(self._rows)
        matched = sum(1 for r in self._rows if r._view is not None)
        self.TxtStatus.Text = "Matched {} / {} files".format(matched, total)

    @staticmethod
    def _brush(hex_color):
        from System.Windows.Media import SolidColorBrush, ColorConverter
        return SolidColorBrush(ColorConverter.ConvertFromString(hex_color))


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    views = get_floor_plan_views()
    if not views:
        forms.alert("Tidak ada Floor Plan / Engineering Plan view di project ini.",
                    title="Link CAD Batch")
        return
    try:
        dlg = LinkCADBatchDialog(views)
        dlg.ShowDialog()
    except Exception as e:
        forms.alert(
            "Dialog error:\n{}\n\n{}".format(str(e), traceback.format_exc()),
            title="Link CAD Batch"
        )


if __name__ == "__main__":
    main()