# -*- coding: utf-8 -*-
__title__ = "Remove Revsion\nby PrintSet"
__author__ = "PrasKaa"
__doc__ = """
Version: 1.0
Date    = 10.03.2026
_____________________________________________________________________
Description:
Remove all revision clouds and manual revision assignments from sheets in selected Print Set(s).
This tool deletes Revision Cloud annotations and clears Additional Revision IDs from sheets
that are members of the chosen Print Sets.

Useful for cleaning up revision markups before issuing new revision cycles.
_____________________________________________________________________
How-to:
1. Run the tool from pyRevit toolbar
2. Select one or more Print Sets containing sheets to clean
3. Confirm the deletion when prompted
4. Review the summary showing deleted clouds and cleared revisions

Warning: Ensure revisions are unissued before running this tool.
_____________________________________________________
Last update:
- 10.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa
"""


import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSheet, ViewSheetSet,
    RevisionCloud,
    Transaction, ElementId,
)
from System.Collections.Generic import List as CsList
from System.Windows.Forms import (
    Form, Button, CheckedListBox, Label,
    DialogResult, FlatStyle,
    FormStartPosition, FormBorderStyle,
    MessageBox, MessageBoxButtons, MessageBoxIcon,
    BorderStyle,
)
from System.Drawing import Size, Point, Font, FontStyle, Color

doc = __revit__.ActiveUIDocument.Document


# ═════════════════════════════════════════════════════════════════════════════
#  PRE-BUILD: index semua cloud di dokumen by OwnerViewId
# ═════════════════════════════════════════════════════════════════════════════
def build_cloud_index():
    """
    Return dict: { ElementId(viewId) -> [ElementId(cloudId), ...] }
    Mengambil SEMUA cloud di dokumen tanpa filter view,
    sehingga cloud Show=None pun ikut tertangkap.
    """
    index = {}
    all_clouds = (
        FilteredElementCollector(doc)
        .OfClass(RevisionCloud)
        .ToElements()
    )
    for cloud in all_clouds:
        owner_id = cloud.OwnerViewId
        if owner_id not in index:
            index[owner_id] = []
        index[owner_id].append(cloud.Id)
    return index


# ═════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═════════════════════════════════════════════════════════════════════════════
def get_all_print_sets():
    sets = list(FilteredElementCollector(doc).OfClass(ViewSheetSet))
    sets.sort(key=lambda s: s.Name)
    return sets

def get_sheets_in_print_set(ps):
    sheets = []
    it = ps.Views.GetEnumerator()
    while it.MoveNext():
        v = it.Current
        if isinstance(v, ViewSheet):
            sheets.append(v)
    return sheets

def get_cloud_ids_for_sheet(sheet, cloud_index):
    """
    Kumpulkan semua cloud ID yang berkontribusi ke sheet ini:
      1. Cloud yang OwnerViewId = sheet (langsung di sheet)
      2. Cloud yang OwnerViewId = view di viewport sheet
    """
    cloud_ids = []

    # 1. Cloud langsung di sheet
    if sheet.Id in cloud_index:
        cloud_ids.extend(cloud_index[sheet.Id])

    # 2. Cloud di view-view yang di-place sebagai viewport
    try:
        for vp_id in sheet.GetAllViewports():
            vp = doc.GetElement(vp_id)
            if vp is None:
                continue
            view_id = vp.ViewId
            if view_id in cloud_index:
                cloud_ids.extend(cloud_index[view_id])
    except Exception:
        pass

    return cloud_ids


# ═════════════════════════════════════════════════════════════════════════════
#  DIALOG
# ═════════════════════════════════════════════════════════════════════════════
class PrintSetPickerForm(Form):
    def __init__(self, print_sets):
        self.Text = "Remove Revisions by Print Set"
        self.Size = Size(440, 500)
        self.StartPosition = FormStartPosition.CenterScreen
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        self.BackColor = Color.FromArgb(245, 245, 245)

        lbl_title = Label()
        lbl_title.Text = "Pilih satu atau lebih Print Set:"
        lbl_title.Font = Font("Segoe UI", 10, FontStyle.Bold)
        lbl_title.Location = Point(16, 16)
        lbl_title.Size = Size(400, 24)
        self.Controls.Add(lbl_title)

        lbl_sub = Label()
        lbl_sub.Text = (
            "Semua Revision Cloud (termasuk Show = None)\n"
            "pada sheet-sheet di Print Set yang dipilih akan dihapus."
        )
        lbl_sub.Font = Font("Segoe UI", 9)
        lbl_sub.ForeColor = Color.FromArgb(60, 60, 60)
        lbl_sub.Location = Point(16, 44)
        lbl_sub.Size = Size(400, 40)
        self.Controls.Add(lbl_sub)

        lbl_warn = Label()
        lbl_warn.Text = "⚠  Pastikan Revision sudah di-unissued sebelum menjalankan."
        lbl_warn.Font = Font("Segoe UI", 8, FontStyle.Italic)
        lbl_warn.ForeColor = Color.FromArgb(180, 80, 0)
        lbl_warn.Location = Point(16, 88)
        lbl_warn.Size = Size(400, 18)
        self.Controls.Add(lbl_warn)

        self.clb = CheckedListBox()
        self.clb.Location = Point(16, 114)
        self.clb.Size = Size(400, 300)
        self.clb.Font = Font("Segoe UI", 9)
        self.clb.CheckOnClick = True
        self.clb.BorderStyle = BorderStyle.FixedSingle
        for ps in print_sets:
            self.clb.Items.Add(ps.Name)
        self.Controls.Add(self.clb)

        btn_all = Button()
        btn_all.Text = "Pilih Semua"
        btn_all.Location = Point(16, 428)
        btn_all.Size = Size(90, 28)
        btn_all.FlatStyle = FlatStyle.Flat
        btn_all.Click += self._select_all
        self.Controls.Add(btn_all)

        btn_none = Button()
        btn_none.Text = "Kosongkan"
        btn_none.Location = Point(114, 428)
        btn_none.Size = Size(90, 28)
        btn_none.FlatStyle = FlatStyle.Flat
        btn_none.Click += self._select_none
        self.Controls.Add(btn_none)

        btn_ok = Button()
        btn_ok.Text = "Hapus Revisi"
        btn_ok.Location = Point(224, 428)
        btn_ok.Size = Size(96, 28)
        btn_ok.BackColor = Color.FromArgb(196, 43, 28)
        btn_ok.ForeColor = Color.White
        btn_ok.FlatStyle = FlatStyle.Flat
        btn_ok.DialogResult = DialogResult.OK
        self.Controls.Add(btn_ok)
        self.AcceptButton = btn_ok

        btn_cancel = Button()
        btn_cancel.Text = "Batal"
        btn_cancel.Location = Point(328, 428)
        btn_cancel.Size = Size(80, 28)
        btn_cancel.FlatStyle = FlatStyle.Flat
        btn_cancel.DialogResult = DialogResult.Cancel
        self.Controls.Add(btn_cancel)
        self.CancelButton = btn_cancel

        self._print_sets = print_sets

    def _select_all(self, sender, e):
        for i in range(self.clb.Items.Count):
            self.clb.SetItemChecked(i, True)

    def _select_none(self, sender, e):
        for i in range(self.clb.Items.Count):
            self.clb.SetItemChecked(i, False)

    @property
    def selected_print_sets(self):
        checked = list(self.clb.CheckedItems)
        return [ps for ps in self._print_sets if ps.Name in checked]


# ═════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═════════════════════════════════════════════════════════════════════════════
def main():
    print_sets = get_all_print_sets()
    if not print_sets:
        MessageBox.Show(
            "Tidak ada Print Set di dokumen ini.",
            "Tidak Ada Print Set",
            MessageBoxButtons.OK,
            MessageBoxIcon.Warning,
        )
        return

    form = PrintSetPickerForm(print_sets)
    if form.ShowDialog() != DialogResult.OK:
        return

    selected_sets = form.selected_print_sets
    if not selected_sets:
        MessageBox.Show(
            "Tidak ada Print Set yang dipilih.",
            "Batal",
            MessageBoxButtons.OK,
            MessageBoxIcon.Information,
        )
        return

    # Kumpulkan sheet unik
    seen_ids      = set()
    target_sheets = []
    for ps in selected_sets:
        for sht in get_sheets_in_print_set(ps):
            if sht.Id not in seen_ids:
                seen_ids.add(sht.Id)
                target_sheets.append(sht)

    if not target_sheets:
        MessageBox.Show(
            "Print Set yang dipilih tidak mengandung Sheet.",
            "Sheet Tidak Ditemukan",
            MessageBoxButtons.OK,
            MessageBoxIcon.Information,
        )
        return

    # Konfirmasi
    set_names = ", ".join(ps.Name for ps in selected_sets)
    if MessageBox.Show(
        "Hapus SEMUA revision cloud dari {} sheet\ndi Print Set: {}\n\nLanjutkan?".format(
            len(target_sheets), set_names),
        "Konfirmasi",
        MessageBoxButtons.YesNo,
        MessageBoxIcon.Warning,
    ) != DialogResult.Yes:
        return

    # ── Build cloud index SEKALI di luar transaction ──────────────────────────
    cloud_index = build_cloud_index()

    # ── Eksekusi ──────────────────────────────────────────────────────────────
    total_clouds_deleted = 0
    total_manual_cleared = 0
    total_failed         = 0
    sheets_clean         = 0

    with Transaction(doc, "Remove All Revisions by PrintSet") as t:
        t.Start()

        for sht in target_sheets:
            all_rev_ids = sht.GetAllRevisionIds()
            additional  = sht.GetAdditionalRevisionIds()
            cloud_ids   = get_cloud_ids_for_sheet(sht, cloud_index)

            # Lewati jika memang tidak ada apa-apa
            if all_rev_ids.Count == 0 and additional.Count == 0 and not cloud_ids:
                sheets_clean += 1
                continue

            # A. Hapus AdditionalRevisionIds (revision manual)
            if additional.Count > 0:
                try:
                    empty = CsList[ElementId]()
                    sht.SetAdditionalRevisionIds(empty)
                    total_manual_cleared += additional.Count
                except Exception:
                    total_failed += 1

            # B. Hapus semua RevisionCloud berdasarkan index
            for cid in cloud_ids:
                try:
                    doc.Delete(cid)
                    total_clouds_deleted += 1
                except Exception:
                    total_failed += 1

        t.Commit()

    # ── Ringkasan ─────────────────────────────────────────────────────────────
    set_display = "\n".join("  • " + ps.Name for ps in selected_sets)
    summary = (
        "Selesai!\n\n"
        "Print Set:\n{sets}\n\n"
        "Total sheet diproses     : {total}\n"
        "Revision cloud dihapus   : {clouds}\n"
        "Revision manual dihapus  : {manual}\n"
        "Sheet sudah bersih       : {clean}\n"
        "Gagal                    : {fail}"
    ).format(
        sets=set_display,
        total=len(target_sheets),
        clouds=total_clouds_deleted,
        manual=total_manual_cleared,
        clean=sheets_clean,
        fail=total_failed,
    )

    MessageBox.Show(
        summary,
        "Remove Revisions Selesai",
        MessageBoxButtons.OK,
        MessageBoxIcon.Information,
    )


if __name__ == "__main__":
    main()