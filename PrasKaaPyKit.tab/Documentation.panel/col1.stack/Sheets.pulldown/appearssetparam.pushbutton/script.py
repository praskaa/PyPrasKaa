# -*- coding: utf-8 -*-
__title__ = "Set 'Appears\nin Sheet List' by PrintSet"
__author__ = "PrasKaa"
__doc__ = """
Version: 1.0
Date    = 10.03.2026
_____________________________________________________________________
Description:
Set the "Appears in Sheet List" parameter for sheets based on Print Set membership.
Sheets included in selected Print Set(s) will be set to True, while all other sheets
will be set to False.

This tool helps synchronize sheet scheduling with Print Sets for consistent documentation.
_____________________________________________________________________
How-to:
1. Run the tool from pyRevit toolbar
2. Select one or more Print Sets from the dialog
3. Click OK to apply changes
4. Review the summary showing sheets updated to True/False

Note: Sheets with read-only "Sheet Scheduled" parameter will be skipped.
_____________________________________________________
Last update:
- 10.03.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa
"""


# ── Imports ──────────────────────────────────────────────────────────────────
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSheet,
    ViewSheetSet,
    BuiltInParameter,
    Transaction,
)
from System.Windows.Forms import (
    Form, Button, CheckedListBox, Label,
    DialogResult, CheckState,
    FormStartPosition, FormBorderStyle,
    AnchorStyles, DockStyle, ScrollBars,
    MessageBox, MessageBoxButtons, MessageBoxIcon,
    Panel, FlowLayoutPanel, FlowDirection,
    Padding, BorderStyle, FlatStyle,
)
from System.Drawing import Size, Point, Font, FontStyle, Color

# ── Revit doc / uidoc ─────────────────────────────────────────────────────────
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument


# ═════════════════════════════════════════════════════════════════════════════
#  HELPER – kumpulkan semua Print Set dari dokumen
# ═════════════════════════════════════════════════════════════════════════════
def get_all_print_sets():
    """Return list of ViewSheetSet elements (Print Sets) sorted by name."""
    collector = FilteredElementCollector(doc).OfClass(ViewSheetSet)
    sets = list(collector)
    sets.sort(key=lambda s: s.Name)
    return sets


def get_sheets_in_print_set(print_set):
    """Return a set of ElementIds of ViewSheets in the given print_set."""
    sheet_ids = set()
    views = print_set.Views          # ViewSet
    view_iter = views.GetEnumerator()
    while view_iter.MoveNext():
        v = view_iter.Current
        if isinstance(v, ViewSheet):
            sheet_ids.add(v.Id)
    return sheet_ids


def get_all_sheets():
    """Return list of all ViewSheet elements in the document."""
    return list(
        FilteredElementCollector(doc)
        .OfClass(ViewSheet)
        .WhereElementIsNotElementType()
        .ToElements()
    )


# ═════════════════════════════════════════════════════════════════════════════
#  DIALOG – pilih Print Set
# ═════════════════════════════════════════════════════════════════════════════
class PrintSetPickerForm(Form):
    def __init__(self, print_sets):
        self.Text = "Select Print Set"
        self.Size = Size(420, 460)
        self.MinimumSize = Size(360, 360)
        self.StartPosition = FormStartPosition.CenterScreen
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        self.BackColor = Color.FromArgb(245, 245, 245)

        # ── Title label ──────────────────────────────────────────────────────
        lbl_title = Label()
        lbl_title.Text = "Pilih satu atau lebih Print Set:"
        lbl_title.Font = Font("Segoe UI", 10, FontStyle.Bold)
        lbl_title.Location = Point(16, 16)
        lbl_title.Size = Size(380, 24)
        self.Controls.Add(lbl_title)

        lbl_sub = Label()
        lbl_sub.Text = (
            "Sheet yang ada di Print Set yang dipilih\n"
            "akan di-set 'Appears in Sheet List' = True.\n"
            "Sheet lainnya akan di-set False."
        )
        lbl_sub.Font = Font("Segoe UI", 9)
        lbl_sub.ForeColor = Color.FromArgb(80, 80, 80)
        lbl_sub.Location = Point(16, 44)
        lbl_sub.Size = Size(380, 52)
        self.Controls.Add(lbl_sub)

        # ── CheckedListBox ────────────────────────────────────────────────────
        self.clb = CheckedListBox()
        self.clb.Location = Point(16, 104)
        self.clb.Size = Size(378, 270)
        self.clb.Font = Font("Segoe UI", 9)
        self.clb.CheckOnClick = True
        self.clb.ScrollAlwaysVisible = False
        self.clb.BorderStyle = BorderStyle.FixedSingle

        for ps in print_sets:
            self.clb.Items.Add(ps.Name)

        self.Controls.Add(self.clb)

        # ── Tombol Select All / None ──────────────────────────────────────────
        btn_all = Button()
        btn_all.Text = "Select All"
        btn_all.Location = Point(16, 384)
        btn_all.Size = Size(90, 28)
        btn_all.FlatStyle = FlatStyle.Flat
        btn_all.Click += self._select_all
        self.Controls.Add(btn_all)

        btn_none = Button()
        btn_none.Text = "Uncheck"
        btn_none.Location = Point(114, 384)
        btn_none.Size = Size(90, 28)
        btn_none.FlatStyle = FlatStyle.Flat
        btn_none.Click += self._select_none
        self.Controls.Add(btn_none)

        # ── Tombol OK / Cancel ────────────────────────────────────────────────
        btn_ok = Button()
        btn_ok.Text = "OK"
        btn_ok.Location = Point(220, 384)
        btn_ok.Size = Size(82, 28)
        btn_ok.BackColor = Color.FromArgb(0, 120, 212)
        btn_ok.ForeColor = Color.White
        btn_ok.FlatStyle = FlatStyle.Flat
        btn_ok.DialogResult = DialogResult.OK
        self.Controls.Add(btn_ok)
        self.AcceptButton = btn_ok

        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.Location = Point(310, 384)
        btn_cancel.Size = Size(82, 28)
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
        """Return list of ViewSheetSet that were checked."""
        checked = list(self.clb.CheckedItems)
        return [ps for ps in self._print_sets if ps.Name in checked]


# ═════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═════════════════════════════════════════════════════════════════════════════
def main():
    # 1. Kumpulkan semua Print Set
    print_sets = get_all_print_sets()

    if not print_sets:
        MessageBox.Show(
            "Tidak ada Print Set yang ditemukan dalam dokumen ini.\n"
            "Buat Print Set terlebih dahulu melalui File → Print → Print Setup.",
            "Tidak Ada Print Set",
            MessageBoxButtons.OK,
            MessageBoxIcon.Warning,
        )
        return

    # 2. Tampilkan dialog pilih Print Set
    form = PrintSetPickerForm(print_sets)
    result = form.ShowDialog()

    if result != DialogResult.OK:
        return   # user membatalkan

    selected_sets = form.selected_print_sets

    if not selected_sets:
        MessageBox.Show(
            "Tidak ada Print Set yang dipilih. Operasi dibatalkan.",
            "Tidak Ada Pilihan",
            MessageBoxButtons.OK,
            MessageBoxIcon.Information,
        )
        return

    # 3. Kumpulkan semua sheet ID yang masuk ke salah satu Print Set terpilih
    included_ids = set()
    for ps in selected_sets:
        included_ids.update(get_sheets_in_print_set(ps))

    # 4. Kumpulkan semua sheet di dokumen
    all_sheets = get_all_sheets()

    if not all_sheets:
        MessageBox.Show(
            "Tidak ada Sheet di dokumen ini.",
            "Info",
            MessageBoxButtons.OK,
            MessageBoxIcon.Information,
        )
        return

    # 5. Terapkan perubahan dalam satu Transaction
    changed_true  = 0
    changed_false = 0
    skipped       = 0

    with Transaction(doc, "Set Sheet Scheduled by PrintSet") as t:
        t.Start()

        for sheet in all_sheets:
            param = sheet.get_Parameter(BuiltInParameter.SHEET_SCHEDULED)

            if param is None or param.IsReadOnly:
                skipped += 1
                continue

            if sheet.Id in included_ids:
                if param.AsInteger() != 1:   # belum True
                    param.Set(1)             # True = 1
                    changed_true += 1
            else:
                if param.AsInteger() != 0:   # belum False
                    param.Set(0)             # False = 0
                    changed_false += 1

        t.Commit()

    # 6. Ringkasan hasil
    set_names = "\n".join("  • " + ps.Name for ps in selected_sets)
    summary = (
        "✅ Selesai!\n\n"
        "Print Set yang dipilih:\n{names}\n\n"
        "Hasil perubahan:\n"
        "  Sheet → True  : {t} sheet\n"
        "  Sheet → False : {f} sheet\n"
        "  Dilewati      : {s} sheet (read-only / tidak ada parameter)"
    ).format(names=set_names, t=changed_true, f=changed_false, s=skipped)

    MessageBox.Show(
        summary,
        "Sheet List Updated",
        MessageBoxButtons.OK,
        MessageBoxIcon.Information,
    )


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()