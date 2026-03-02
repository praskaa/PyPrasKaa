# -*- coding: utf-8 -*-
import os
import sys
lib_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from pyrevit import forms, revit, DB
from pyrevit.framework import Windows, Drawing, ObjectModel, Forms, List
from pyrevit import script

from expUtils import (
    debug_print,
    expUtils_getAvailablePrinters,
    expUtils_getSavedPrinter,
    expUtils_savePrinter,
    expUtils_getDwgExportSetups,
    expUtils_getSavedDwgSettings,
    expUtils_saveDwgSettings,
)

logger = script.get_logger()
config = script.get_config(section='shared_naming')

NamingFormatter = forms.namedtuple('NamingFormatter', ['template', 'desc'])

class NamingFormat(forms.Reactive):
    def __init__(self, name, template, builtin=False):
        self._name = name
        self._template = self.verify_template(template)
        self.builtin = builtin
        self._is_active = False

    @staticmethod
    def verify_template(value):
        if value.lower().endswith('.pdf'): value = value[:-4]
        elif value.lower().endswith('.dwg'): value = value[:-4]
        return value

    @forms.reactive
    def name(self): return self._name
    @name.setter
    def name(self, value): self._name = value

    @forms.reactive
    def template(self): return self._template
    @template.setter
    def template(self, value): self._template = self.verify_template(value)

    @forms.reactive
    def is_active(self): return self._is_active
    @is_active.setter
    def is_active(self, value): self._is_active = value


class EditNamingFormatsWindow(forms.WPFWindow):
    def __init__(self, xaml_file_name, start_with=None, caller_script=None):
        forms.WPFWindow.__init__(self, xaml_file_name)
        self._drop_pos = 0
        self._starting_item = start_with
        self._saved = False
        self._caller_script = caller_script
        self._dwg_suppress_save = False

        if caller_script:
            debug_print("Editor opened from {} script".format(caller_script))

        self.reset_naming_formats()
        self.reset_formatters()
        self.reset_printer_list()
        self.reset_dwg_settings()

    # ── PRINTER ─────────────────────────────────

    def reset_printer_list(self):
        try:
            printers = expUtils_getAvailablePrinters()
            if not printers:
                self.printer_cb.ItemsSource = ['(No printers found)']
                self.printer_cb.SelectedIndex = 0
                self.printer_cb.IsEnabled = False
                return
            self.printer_cb.ItemsSource = printers
            self.printer_cb.IsEnabled = True
            saved_printer = expUtils_getSavedPrinter()
            if saved_printer and saved_printer in printers:
                self.printer_cb.SelectedItem = saved_printer
            else:
                pdf_printers = [p for p in printers if 'pdf' in p.lower()]
                self.printer_cb.SelectedItem = pdf_printers[0] if pdf_printers else None
                if not pdf_printers:
                    self.printer_cb.SelectedIndex = 0
        except Exception as e:
            debug_print("Error loading printer list:", str(e))

    def printer_selection_changed(self, sender, args):
        selected = self.printer_cb.SelectedItem
        if selected and selected != '(No printers found)':
            expUtils_savePrinter(selected)
            self.printer_status_tb.Text = u"\u2713 Saved: {}".format(selected)
            self.printer_status_tb.Visibility = Windows.Visibility.Visible
        else:
            self.printer_status_tb.Visibility = Windows.Visibility.Collapsed

    # ── DWG SETTINGS ────────────────────────────

    def reset_dwg_settings(self):
        self._dwg_suppress_save = True
        try:
            saved = expUtils_getSavedDwgSettings()
            debug_print("Saved DWG settings:", saved)
            self._load_dwg_export_setups(saved.get('export_setup', None))

            merged = saved.get('merged_views', True)
            self.dwg_mergedviews_cb.SelectedIndex = 0 if merged else 1

            fmt_map = {'R2018':0,'R2013':1,'R2010':2,'R2007':3}
            self.dwg_fileformat_cb.SelectedIndex = fmt_map.get(saved.get('file_format','R2018'), 0)
        except Exception as e:
            debug_print("Error loading DWG settings:", str(e))
        finally:
            self._dwg_suppress_save = False

    def _load_dwg_export_setups(self, saved_setup_name=None):
        try:
            setups = expUtils_getDwgExportSetups(revit.doc)
            setup_names = ['<In-Session (Default)>'] + (setups if setups else [])
            self.dwg_exportsetup_cb.ItemsSource = setup_names
            self.dwg_exportsetup_cb.IsEnabled = bool(setups)
            if saved_setup_name and saved_setup_name in setup_names:
                self.dwg_exportsetup_cb.SelectedItem = saved_setup_name
            else:
                self.dwg_exportsetup_cb.SelectedIndex = 0
        except Exception as e:
            debug_print("Error loading DWG export setups:", str(e))
            self.dwg_exportsetup_cb.ItemsSource = ['(Error loading setups)']
            self.dwg_exportsetup_cb.SelectedIndex = 0

    def dwg_refresh_setups(self, sender, args):
        self._dwg_suppress_save = True
        saved = expUtils_getSavedDwgSettings()
        self._load_dwg_export_setups(saved.get('export_setup', None))
        self._dwg_suppress_save = False

    def dwg_setting_changed(self, sender, args):
        if self._dwg_suppress_save:
            return
        self._save_dwg_settings()

    def _save_dwg_settings(self):
        try:
            setup = self.dwg_exportsetup_cb.SelectedItem
            if setup == '<In-Session (Default)>' or setup is None:
                setup = None

            merged_item = self.dwg_mergedviews_cb.SelectedItem
            merged = True
            if merged_item:
                try: merged = merged_item.Tag == 'True'
                except: merged = True

            fmt_item = self.dwg_fileformat_cb.SelectedItem
            file_format = 'R2018'
            if fmt_item:
                try: file_format = fmt_item.Tag
                except: file_format = 'R2018'

            settings = {'export_setup': setup, 'merged_views': merged, 'file_format': file_format}
            expUtils_saveDwgSettings(settings)
            debug_print("DWG settings saved:", settings)

            parts = [setup if setup else 'In-Session', 'Merged' if merged else 'Separate', file_format]
            self.dwg_status_tb.Text = u"\u2713 Saved: {}".format(' | '.join(parts))
            self.dwg_status_tb.Visibility = Windows.Visibility.Visible
        except Exception as e:
            debug_print("Error saving DWG settings:", str(e))

    # ── NAMING FORMAT ────────────────────────────

    @staticmethod
    def get_default_formatters():
        return [
            NamingFormatter(template='{number}',         desc='Sheet Number e.g. "A1.00"'),
            NamingFormatter(template='{name}',           desc='Sheet Name e.g. "1ST FLOOR PLAN"'),
            NamingFormatter(template='{name_dash}',      desc='Sheet Name (with - for space)'),
            NamingFormatter(template='{name_underline}', desc='Sheet Name (with _ for space)'),
            NamingFormatter(template='{rev_number}',     desc='Revision Number e.g. "01"'),
            NamingFormatter(template='{rev_desc}',       desc='Revision Description e.g. "ASI01"'),
            NamingFormatter(template='{rev_date}',       desc='Revision Date e.g. "2019-10-12"'),
            NamingFormatter(template='{current_date}',   desc="Today's Date e.g. \"2019-10-12\""),
            NamingFormatter(template='{proj_name}',      desc='Project Name'),
            NamingFormatter(template='{proj_number}',    desc='Project Number'),
            NamingFormatter(template='{sheet_param:PARAM_NAME}',  desc='Value of Given Sheet Parameter'),
            NamingFormatter(template='{tblock_param:PARAM_NAME}', desc='Value of Given TitleBlock Parameter'),
            NamingFormatter(template='{proj_param:PARAM_NAME}',   desc='Value of Given Project Information Parameter'),
            NamingFormatter(template='{glob_param:PARAM_NAME}',   desc='Value of Given Global Parameter'),
        ]

    @staticmethod
    def get_default_naming_formats():
        return [
            NamingFormat(name='Default Format',  template='{number} {name}',              builtin=True),
            NamingFormat(name='Compact Format',  template='{number}_{name}',               builtin=True),
            NamingFormat(name='Detailed Format', template='{number} {name} R{rev_number}', builtin=True),
        ]

    @staticmethod
    def get_naming_formats():
        naming_formats = EditNamingFormatsWindow.get_default_naming_formats()
        naming_formats_dict = config.get_option('namingformats', {})
        cleaned = {}
        for name, template in naming_formats_dict.items():
            t = template
            if t.lower().endswith('.pdf'): t = t[:-4]
            elif t.lower().endswith('.dwg'): t = t[:-4]
            cleaned[name] = t
        if cleaned != naming_formats_dict:
            config.namingformats = cleaned
            script.save_config()
        for name, template in cleaned.items():
            naming_formats.append(NamingFormat(name=name, template=template))
        return naming_formats

    @staticmethod
    def set_naming_formats(naming_formats):
        config.namingformats = {x.name: x.template for x in naming_formats if not x.builtin}
        script.save_config()

    @property
    def naming_formats(self): return self.formats_lb.ItemsSource

    @property
    def selected_naming_format(self): return self.formats_lb.SelectedItem

    @selected_naming_format.setter
    def selected_naming_format(self, value):
        self.formats_lb.SelectedItem = value
        self.namingformat_edit.DataContext = value

    def reset_formatters(self):
        self.formatters_wp.ItemsSource = EditNamingFormatsWindow.get_default_formatters()

    def reset_naming_formats(self):
        formats = EditNamingFormatsWindow.get_naming_formats()
        try: active_format_name = config.get_option('selected_export_format', None)
        except: active_format_name = None
        for fmt in formats:
            fmt.is_active = (fmt.name == active_format_name)
        self.formats_lb.ItemsSource = ObjectModel.ObservableCollection[object](formats)

        selected_item = None
        if isinstance(self._starting_item, NamingFormat):
            for item in self.formats_lb.ItemsSource:
                if item.name == self._starting_item.name:
                    selected_item = item; break
        if not selected_item and active_format_name:
            for item in self.formats_lb.ItemsSource:
                if item.name == active_format_name:
                    selected_item = item; break
        if not selected_item and self.formats_lb.ItemsSource:
            selected_item = self.formats_lb.ItemsSource[0]
        if selected_item:
            self.selected_naming_format = selected_item

    def start_drag(self, sender, args):
        Windows.DragDrop.DoDragDrop(
            self.formatters_wp,
            Windows.DataObject("name_formatter", args.OriginalSource.DataContext),
            Windows.DragDropEffects.Copy)

    def preview_drag(self, sender, args):
        mouse_pos = Forms.Cursor.Position
        self._drop_pos = self.template_tb.GetCharacterIndexFromPoint(
            point=self.template_tb.PointFromScreen(Windows.Point(mouse_pos.X, mouse_pos.Y)),
            snapToText=True)
        self.template_tb.SelectionStart = self._drop_pos
        self.template_tb.SelectionLength = 0
        self.template_tb.Focus()
        args.Effects = Windows.DragDropEffects.Copy
        args.Handled = True

    def stop_drag(self, sender, args):
        name_formatter = args.Data.GetData("name_formatter")
        if name_formatter:
            self.template_tb.Text = \
                str(self.template_tb.Text)[:self._drop_pos] \
                + name_formatter.template \
                + str(self.template_tb.Text)[self._drop_pos:]
            self.template_tb.Focus()

    def namingformat_changed(self, sender, args):
        self.namingformat_edit.DataContext = self.selected_naming_format

    def duplicate_namingformat(self, sender, args):
        nf = self.selected_naming_format
        new_nf = NamingFormat(name='<unnamed>', template=nf.template)
        self.naming_formats.Add(new_nf)
        self.selected_naming_format = new_nf

    def delete_namingformat(self, sender, args):
        nf = self.selected_naming_format
        if nf.builtin: return
        idx = self.naming_formats.IndexOf(nf)
        self.naming_formats.Remove(nf)
        self.selected_naming_format = self.naming_formats[min(idx, self.naming_formats.Count-1)]

    def set_active_format(self, sender, args):
        selected_format = self.selected_naming_format
        if selected_format and not selected_format.builtin:
            config.selected_export_format = selected_format.name
            script.save_config()
            self.reset_naming_formats()

    def save_formats(self, sender, args):
        EditNamingFormatsWindow.set_naming_formats(self.naming_formats)
        cur = self.selected_naming_format
        if cur:
            config.selected_export_format = cur.name
        else:
            try: sf = config.get_option('selected_export_format', None)
            except: sf = None
            if not sf and self.naming_formats:
                config.selected_export_format = self.naming_formats[0].name
        script.save_config()
        self._saved = True
        self.Close()

    def cancelled(self, sender, args):
        if not self._saved:
            self.reset_naming_formats()

    def show_dialog(self):
        self.ShowDialog()


if __name__ == "__main__":
    EditNamingFormatsWindow('EditNamingFormats.xaml').show_dialog()