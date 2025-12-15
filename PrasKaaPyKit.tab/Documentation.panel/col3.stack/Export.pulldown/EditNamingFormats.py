import os
import sys
# Add lib directory to path for imports
lib_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

# import pyrevit libraries
from pyrevit import forms
from pyrevit.framework import Windows, Drawing, ObjectModel, Forms, List
from pyrevit import script

# import expUtils for debug functionality
from expUtils import debug_print

logger = script.get_logger()
config = script.get_config(section='shared_naming')

NamingFormatter = forms.namedtuple('NamingFormatter', ['template', 'desc'])

class NamingFormat(forms.Reactive):
    """Export File Naming Format"""
    def __init__(self, name, template, builtin=False):
        self._name = name
        self._template = self.verify_template(template)
        self.builtin = builtin
        self._is_active = False

    @staticmethod
    def verify_template(value):
        """Verify template is valid - extensions are added automatically based on export type"""
        # Strip any existing extensions since they're added automatically
        if value.lower().endswith('.pdf'):
            value = value[:-4]
        elif value.lower().endswith('.dwg'):
            value = value[:-4]
        return value

    @forms.reactive
    def name(self):
        """Format name"""
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @forms.reactive
    def template(self):
        """Format template string"""
        return self._template

    @template.setter
    def template(self, value):
        self._template = self.verify_template(value)

    @forms.reactive
    def is_active(self):
        """Is this the currently active format"""
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = value


class EditNamingFormatsWindow(forms.WPFWindow):
    def __init__(self, xaml_file_name, start_with=None, caller_script=None):
        forms.WPFWindow.__init__(self, xaml_file_name)

        self._drop_pos = 0
        self._starting_item = start_with
        self._saved = False
        self._caller_script = caller_script

        # Debug: Show which script called this
        if caller_script:
            debug_print("Editor opened from {} script".format(caller_script))
        else:
            debug_print("Editor opened from unknown script")

        # Debug: Show config state
        try:
            active_format_name = config.get_option('selected_export_format', None)
            debug_print("Current active format in config: {}".format(active_format_name))
            naming_formats_dict = config.get_option('namingformats', {})
            debug_print("Custom naming formats in config: {}".format(naming_formats_dict))
        except Exception as e:
            debug_print("Error reading config: {}".format(str(e)))

        self.reset_naming_formats()
        self.reset_formatters()

    @staticmethod
    def get_default_formatters():
        return [
            NamingFormatter(
                template='{number}',
                desc='Sheet Number e.g. "A1.00"'
            ),
            NamingFormatter(
                template='{name}',
                desc='Sheet Name e.g. "1ST FLOOR PLAN"'
            ),
            NamingFormatter(
                template='{name_dash}',
                desc='Sheet Name (with - for space) e.g. "1ST-FLOOR-PLAN"'
            ),
            NamingFormatter(
                template='{name_underline}',
                desc='Sheet Name (with _ for space) e.g. "1ST_FLOOR_PLAN"'
            ),
            NamingFormatter(
                template='{rev_number}',
                desc='Revision Number e.g. "01"'
            ),
            NamingFormatter(
                template='{rev_desc}',
                desc='Revision Description e.g. "ASI01"'
            ),
            NamingFormatter(
                template='{rev_date}',
                desc='Revision Date e.g. "2019-10-12"'
            ),
            NamingFormatter(
                template='{current_date}',
                desc='Today\'s Date e.g. "2019-10-12"'
            ),
            NamingFormatter(
                template='{proj_name}',
                desc='Project Name e.g. "MY_PROJECT"'
            ),
            NamingFormatter(
                template='{proj_number}',
                desc='Project Number e.g. "PR2019.12"'
            ),
            NamingFormatter(
                template='{sheet_param:PARAM_NAME}',
                desc='Value of Given Sheet Parameter e.g. Replace PARAM_NAME with target parameter name'
            ),
            NamingFormatter(
                template='{tblock_param:PARAM_NAME}',
                desc='Value of Given TitleBlock Parameter e.g. Replace PARAM_NAME with target parameter name'
            ),
            NamingFormatter(
                template='{proj_param:PARAM_NAME}',
                desc='Value of Given Project Information Parameter e.g. Replace PARAM_NAME with target parameter name'
            ),
            NamingFormatter(
                template='{glob_param:PARAM_NAME}',
                desc='Value of Given Global Parameter e.g. Replace PARAM_NAME with target parameter name'
            ),
        ]

    @staticmethod
    def get_default_naming_formats():
        return [
            NamingFormat(
                name='Default Format',
                template='{number} {name}',
                builtin=True
            ),
            NamingFormat(
                name='Compact Format',
                template='{number}_{name}',
                builtin=True
            ),
            NamingFormat(
                name='Detailed Format',
                template='{number} {name} R{rev_number}',
                builtin=True
            ),
        ]

    @staticmethod
    def get_naming_formats():
        naming_formats = EditNamingFormatsWindow.get_default_naming_formats()
        naming_formats_dict = config.get_option('namingformats', {})

        # Clean existing templates by stripping extensions (migration from old system)
        cleaned_naming_formats_dict = {}
        for name, template in naming_formats_dict.items():
            # Strip extensions from existing templates to ensure compatibility with conditional extension system
            cleaned_template = template
            if cleaned_template.lower().endswith('.pdf'):
                cleaned_template = cleaned_template[:-4]
            elif cleaned_template.lower().endswith('.dwg'):
                cleaned_template = cleaned_template[:-4]
            cleaned_naming_formats_dict[name] = cleaned_template

        # Save cleaned config back if any templates were modified
        if cleaned_naming_formats_dict != naming_formats_dict:
            config.namingformats = cleaned_naming_formats_dict
            script.save_config()

        for name, template in cleaned_naming_formats_dict.items():
            naming_formats.append(NamingFormat(name=name, template=template))
        return naming_formats

    @staticmethod
    def set_naming_formats(naming_formats):
        naming_formats_dict = {
            x.name:x.template for x in naming_formats if not x.builtin
        }
        config.namingformats = naming_formats_dict
        script.save_config()

    @property
    def naming_formats(self):
        return self.formats_lb.ItemsSource

    @property
    def selected_naming_format(self):
        return self.formats_lb.SelectedItem

    @selected_naming_format.setter
    def selected_naming_format(self, value):
        self.formats_lb.SelectedItem = value
        self.namingformat_edit.DataContext = value

    def reset_formatters(self):
        self.formatters_wp.ItemsSource = \
            EditNamingFormatsWindow.get_default_formatters()

    def reset_naming_formats(self):
        formats = EditNamingFormatsWindow.get_naming_formats()

        # Mark the active format
        try:
            active_format_name = config.get_option('selected_export_format', None)
        except:
            active_format_name = None

        for fmt in formats:
            fmt.is_active = (fmt.name == active_format_name)

        self.formats_lb.ItemsSource = \
                ObjectModel.ObservableCollection[object](formats)

        # Select the active format or the first format
        selected_item = None
        if isinstance(self._starting_item, NamingFormat):
            for item in self.formats_lb.ItemsSource:
                if item.name == self._starting_item.name:
                    selected_item = item
                    break

        if not selected_item and active_format_name:
            for item in self.formats_lb.ItemsSource:
                if item.name == active_format_name:
                    selected_item = item
                    break

        if not selected_item and self.formats_lb.ItemsSource:
            selected_item = self.formats_lb.ItemsSource[0]

        if selected_item:
            self.selected_naming_format = selected_item

    # https://www.wpftutorial.net/DragAndDrop.html
    def start_drag(self, sender, args):
        name_formatter = args.OriginalSource.DataContext
        Windows.DragDrop.DoDragDrop(
            self.formatters_wp,
            Windows.DataObject("name_formatter", name_formatter),
            Windows.DragDropEffects.Copy
            )

    # https://social.msdn.microsoft.com/Forums/vstudio/en-US/941f6bf2-a321-459e-85c9-501ec1e13204/how-do-you-get-a-drag-and-drop-event-for-a-wpf-textbox-hosted-in-a-windows-form
    def preview_drag(self, sender, args):
        mouse_pos = Forms.Cursor.Position
        mouse_po_pt = Windows.Point(mouse_pos.X, mouse_pos.Y)
        self._drop_pos = \
            self.template_tb.GetCharacterIndexFromPoint(
                point=self.template_tb.PointFromScreen(mouse_po_pt),
                snapToText=True
                )
        self.template_tb.SelectionStart = self._drop_pos
        self.template_tb.SelectionLength = 0
        self.template_tb.Focus()
        args.Effects = Windows.DragDropEffects.Copy
        args.Handled = True

    def stop_drag(self, sender, args):
        name_formatter = args.Data.GetData("name_formatter")
        if name_formatter:
            new_template = \
                str(self.template_tb.Text)[:self._drop_pos] \
                + name_formatter.template \
                + str(self.template_tb.Text)[self._drop_pos:]
            self.template_tb.Text = new_template
            self.template_tb.Focus()

    def namingformat_changed(self, sender, args):
        naming_format = self.selected_naming_format
        self.namingformat_edit.DataContext = naming_format

    def duplicate_namingformat(self, sender, args):
        naming_format = self.selected_naming_format
        new_naming_format = NamingFormat(
            name='<unnamed>',
            template=naming_format.template
            )
        self.naming_formats.Add(new_naming_format)
        self.selected_naming_format = new_naming_format

    def delete_namingformat(self, sender, args):
        naming_format = self.selected_naming_format
        if naming_format.builtin:
            return
        item_index = self.naming_formats.IndexOf(naming_format)
        self.naming_formats.Remove(naming_format)
        next_index = min([item_index, self.naming_formats.Count-1])
        self.selected_naming_format = self.naming_formats[next_index]

    def set_active_format(self, sender, args):
        """Set the selected format as the active format"""
        selected_format = self.selected_naming_format
        if selected_format and not selected_format.builtin:
            config.selected_export_format = selected_format.name
            script.save_config()
            # Update the UI to show the active format
            self.reset_naming_formats()

    def save_formats(self, sender, args):
        EditNamingFormatsWindow.set_naming_formats(self.naming_formats)
        # Set the currently selected format as active (allow builtin formats to be selected)
        current_selected = self.selected_naming_format
        if current_selected:
            config.selected_export_format = current_selected.name
        else:
            # Fallback: set the first available format as selected
            try:
                selected_format = config.get_option('selected_export_format', None)
            except:
                selected_format = None

            if not selected_format and self.naming_formats:
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