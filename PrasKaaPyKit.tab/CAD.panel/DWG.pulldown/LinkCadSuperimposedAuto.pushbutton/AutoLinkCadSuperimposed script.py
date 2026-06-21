# -*- coding: utf-8 -*-
"""
Link CAD Batch - PrasKaaPyKitv2
Batch link DWG/DXF files to floor plan views with WPF UI.
Author: PrasKaa
Version: 2.4
"""

__title__ = "Link CAD\nSuperimposed Batch"
__doc__ = """2025.06.01 - v2.1
Batch link DWG/DXF files to floor plan views.
Scan folder -> pair CAD to views -> set X/Y offset -> link all at once.

Fix v2.1:
- Use doc.Import() instead of ImportInstance.Create() to correctly
  bind CAD link to the target view (ThisViewOnly = True).
- Added opts.Placement = ImportPlacement.Origin for predictable placement.
- clr.Reference[ElementId] used to capture resulting instance ID.

Fix v2.2:
- Set IMPORT_BACKGROUND parameter to 0 (Foreground) after linking.
  Revit defaults new CAD links to Background; this forces Foreground
  automatically so no manual change is needed per view.

Fix v2.3:
- Replace legacy FolderBrowserDialog with forms.pick_folder().
  Now shows modern Windows Explorer folder picker instead of old tree dialog.

Fix v2.4:
- Replace non-existent op.print_html_table() with manual HTML table via op.print_html().
  print_html_table does not exist in pyRevit 5.1."""

import os
import clr
import System
import traceback

clr.AddReference("WindowsBase")
clr.AddReference("PresentationCore")
clr.AddReference("PresentationFramework")
from System.Collections.ObjectModel import ObservableCollection

from pyrevit import HOST_APP, DB, forms, script
from pyrevit import output as pyoutput

logger = script.get_logger()
op     = pyoutput.get_output()

doc = HOST_APP.doc


# =============================================================================
# UNIT CONVERSION
# =============================================================================

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
    """Return lowercased basenames/names of CAD instances already linked in a view."""
    names = []
    try:
        for inst in DB.FilteredElementCollector(doc, view_id)\
                      .OfClass(DB.ImportInstance)\
                      .WhereElementIsNotElementType()\
                      .ToElements():
            lt = doc.GetElement(inst.GetTypeId())
            if lt is None:
                continue
            # try external file reference path
            try:
                ref = lt.GetExternalFileReference()
                if ref is not None:
                    names.append(os.path.basename(ref.GetAbsolutePath()).lower())
            except Exception:
                pass
            # try element name
            try:
                names.append(lt.Name.lower())
            except Exception:
                try:
                    names.append(DB.Element.Name.GetValue(lt).lower())
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
# CORE LINK FUNCTION  (fixed — uses doc.Import with clr.Reference)
# =============================================================================

def link_cad_to_view(doc, view, cad_path, offset_x_mm=0.0, offset_y_mm=0.0):
    """
    Link a DWG/DXF file superimposed into a specific view only.

    Uses doc.Import() with ThisViewOnly=True and an explicit view argument,
    which is the correct API to guarantee placement in the target view.
    ImportInstance.Create() does NOT reliably honour ThisViewOnly.

    Returns (ElementId, error_message).
    error_message is None on success.
    """
    try:
        opts = DB.DWGImportOptions()
        opts.ColorMode    = DB.ImportColorMode.Preserved
        opts.ThisViewOnly = True
        opts.Unit         = DB.ImportUnit.Millimeter
        opts.Placement    = DB.ImportPlacement.Origin  # predictable origin placement

        # clr.Reference used to receive the output ElementId from doc.Import()
        result_id_ref = clr.Reference[DB.ElementId]()
        doc.Import(cad_path, opts, view, result_id_ref)
        link_id = result_id_ref.Value

        if link_id is None or link_id == DB.ElementId.InvalidElementId:
            return DB.ElementId.InvalidElementId, "doc.Import returned invalid ElementId"

        elem = doc.GetElement(link_id)

        # Set to Foreground (IMPORT_BACKGROUND = 0 means Foreground, 1 means Background)
        # Revit defaults new CAD links to Background — override it here.
        if elem is not None:
            bg_param = elem.get_Parameter(DB.BuiltInParameter.IMPORT_BACKGROUND)
            if bg_param is not None and not bg_param.IsReadOnly:
                bg_param.Set(0)  # 0 = Foreground

        # Apply X/Y offset if non-zero
        ox = offset_x_mm
        oy = offset_y_mm
        if abs(ox) > 1e-9 or abs(oy) > 1e-9:
            if elem is not None:
                was_pinned = elem.Pinned
                if was_pinned:
                    elem.Pinned = False
                DB.ElementTransformUtils.MoveElement(
                    doc, link_id,
                    DB.XYZ(mm_to_ft(ox), mm_to_ft(oy), 0.0)
                )
                if was_pinned:
                    elem.Pinned = True

        return link_id, None

    except Exception as ex:
        return DB.ElementId.InvalidElementId, str(ex)


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
        # forms.pick_folder() uses modern IFileOpenDialog — proper Explorer window
        selected = forms.pick_folder(title="Pilih folder yang berisi file DWG/DXF")
        if not selected:
            return
        self._folder = selected
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
        for vname, v in self._view_map.items():
            if vname.lower() == low:
                return v
        for vname, v in self._view_map.items():
            if low in vname.lower() or vname.lower() in low:
                return v
        return None

    # ------------------------------------------------------------------
    # LINK  (fixed — uses link_cad_to_view with doc.Import)
    # ------------------------------------------------------------------
    def _on_link(self, sender, args):
        # Validate / resolve views first
        active = []
        for row in self._rows:
            if not row.Enabled:
                continue
            if not row._view:
                v = self._resolve_view(row.ViewName)
                if v:
                    row._view    = v
                    row.ViewName = v.Name
                    row.Status   = "✅ ready"
                else:
                    row.Status   = "❌ view not found"
                    continue
            active.append(row)

        self._refresh_grid()

        if not active:
            forms.alert(
                "Tidak ada pair valid untuk diproses.\nPastikan View Name sudah benar.",
                title="Link CAD Batch"
            )
            return

        skip_existing = self.ChkSkipExisting.IsChecked

        success, skipped, failed = 0, 0, 0
        # log entries: (cad_name, view_name, offset_str, status_key, status_label)
        log = []

        t = DB.Transaction(doc, "PrasKaa - Link CAD Batch v2.2")
        t.Start()
        try:
            for row in active:
                view = row._view

                # --- Skip if already linked in this view ---
                if skip_existing:
                    existing = get_already_linked_names(view.Id)
                    cad_lower = row.CadName.lower()
                    if any(cad_lower in e for e in existing):
                        row.Status = "⏭ already linked"
                        skipped += 1
                        log.append((row.CadName, view.Name, "-", "SKIP", "⏭ already linked"))
                        continue

                ox = _safe_float(row.OffsetX, 0.0)
                oy = _safe_float(row.OffsetY, 0.0)
                offset_str = "({},{})".format(ox, oy) if (abs(ox) > 1e-9 or abs(oy) > 1e-9) else "-"

                # --- Link using corrected doc.Import() approach ---
                link_id, err = link_cad_to_view(doc, view, row.CadPath, ox, oy)

                if err is None and link_id != DB.ElementId.InvalidElementId:
                    row.Status = "✅ linked"
                    success += 1
                    log.append((row.CadName, view.Name, offset_str, "OK", "✅ linked"))
                else:
                    msg = err if err else "invalid ElementId"
                    row.Status = "❌ {}".format(msg[:50])
                    failed += 1
                    log.append((row.CadName, view.Name, offset_str, "FAIL",
                                "❌ {}".format(msg[:60])))

            t.Commit()

        except Exception as outer:
            try:
                t.RollbackIfPending()
            except Exception:
                pass
            forms.alert("Transaction error:\n{}".format(str(outer)), title="Error")
            self._refresh_grid()
            return

        self._refresh_grid()
        self._update_status()

        self.TxtStatus.Text = "Done. Linked: {} | Skipped: {} | Failed: {}".format(
            success, skipped, failed)

        # --- Output panel report ---
        op.set_title("Link CAD Batch — {}".format(doc.Title))
        op.print_md("## Link CAD Batch v2.4")
        op.print_md("**Linked: {}** | **Skipped: {}** | **Failed: {}**".format(
            success, skipped, failed))

        if log:
            STATUS_COLORS = {
                "OK":   "#A6E3A1",
                "SKIP": "#FAB387",
                "FAIL": "#F38BA8",
            }
            # Build HTML table manually — print_html_table does not exist in pyRevit 5.1
            rows_html = ""
            for cad_name, view_name, offset_str, key, label in log:
                color = STATUS_COLORS.get(key, "#CDD6F4")
                rows_html += (
                    "<tr>"
                    "<td style='padding:3px 8px;width:250px;'>{}</td>"
                    "<td style='padding:3px 8px;width:200px;'>{}</td>"
                    "<td style='padding:3px 8px;width:120px;text-align:center;'>{}</td>"
                    "<td style='padding:3px 8px;width:120px;text-align:center;"
                    "font-weight:bold;color:{};'>{}</td>"
                    "</tr>"
                ).format(cad_name, view_name, offset_str, color, label)

            op.print_html(
                "<table style='border-collapse:collapse;font-size:12px;'>"
                "<thead><tr style='border-bottom:1px solid #555;'>"
                "<th style='padding:4px 8px;text-align:left;width:250px;'>CAD File</th>"
                "<th style='padding:4px 8px;text-align:left;width:200px;'>View</th>"
                "<th style='padding:4px 8px;text-align:center;width:120px;'>Offset (mm)</th>"
                "<th style='padding:4px 8px;text-align:center;width:120px;'>Status</th>"
                "</tr></thead>"
                "<tbody>{}</tbody>"
                "</table>".format(rows_html)
            )

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    def _refresh_grid(self):
        """Force DataGrid to re-read rows by toggling ItemsSource."""
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
        forms.alert(
            "Tidak ada Floor Plan / Engineering Plan view di project ini.",
            title="Link CAD Batch"
        )
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