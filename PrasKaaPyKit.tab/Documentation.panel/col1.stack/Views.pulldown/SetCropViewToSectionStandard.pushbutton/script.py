# -*- coding: utf-8 -*-

"""
Crop View Override Script for Revit

This script allows users to apply or reset graphic overrides to crop boxes
in section and detail views placed on sheets.
"""

import os
from pyrevit import revit, DB, UI, forms


class DummyProgressBar:
    """Dummy progress bar implementation for when progress bar is disabled."""

    def __init__(self, title=None, total=0, cancellable=False, indeterminate=False):
        self._title = title or ""
        self._cancelled = False
        self._is_active = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._is_active = False

    def update_progress(self, current_step, max_steps=None):
        """Update progress (no-op for dummy implementation)."""
        pass

    def update_message(self, message):
        """Update progress message (no-op for dummy implementation)."""
        pass

    @property
    def cancelled(self):
        """Check if operation was cancelled."""
        return self._cancelled

    @property
    def title(self):
        """Get progress bar title."""
        return self._title

    @title.setter
    def title(self, value):
        """Set progress bar title."""
        self._title = value


def load_configuration():
    """Load configuration from config.py file or use defaults."""
    script_dir = os.path.dirname(__file__)
    config_path = os.path.join(script_dir, 'config.py')

    # Default configuration
    config = {
        'line_weight': 6,
        'line_pattern_name': 'Dash dot',
        'allowed_view_types': ['Section', 'Detail'],
        'show_progress_bar': True,
        'show_detailed_results': True
    }

    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config_content = f.read()
            # Execute config in local scope to avoid namespace pollution
            local_config = {}
            exec(config_content, {}, local_config)
            config.update(local_config)
    except Exception as e:
        print("Could not load config file, using defaults: {}".format(e))

    return config


def get_views_on_sheets(doc, allowed_view_types=None):
    """Get all views that are placed on sheets and match allowed types."""
    views = DB.FilteredElementCollector(doc)\
             .OfCategory(DB.BuiltInCategory.OST_Views)\
             .WhereElementIsNotElementType()\
             .ToElements()

    views_on_sheet = []
    for view in views:
        try:
            # Check if view is on sheet
            sheet_number = view.get_Parameter(DB.BuiltInParameter.VIEWER_SHEET_NUMBER)
            if sheet_number and sheet_number.AsString():
                # Filter by view type if specified
                if allowed_view_types:
                    view_type_name = view.ViewType.ToString()
                    if view_type_name in allowed_view_types:
                        views_on_sheet.append(view)
                else:
                    views_on_sheet.append(view)
        except AttributeError:
            # Skip views that don't have the required parameters
            continue

    return views_on_sheet


def create_override_settings(doc, config, action):
    """Create override graphic settings based on action and configuration."""
    override = DB.OverrideGraphicSettings()

    if action == 'Apply Standard Overrides':
        # Set line weight
        override.SetProjectionLineWeight(config['line_weight'])

        # Find and set line pattern
        line_patterns = DB.FilteredElementCollector(doc)\
                         .OfClass(DB.LinePatternElement)\
                         .ToElements()

        target_pattern = None
        for pattern in line_patterns:
            if pattern.Name == config['line_pattern_name']:
                target_pattern = pattern
                break

        if not target_pattern:
            forms.alert(
                'Could not find "{}" line pattern in the project. Please check the config file or make sure the pattern exists.'.format(config['line_pattern_name']),
                exitscript=True
            )

        override.SetProjectionLinePatternId(target_pattern.Id)
        transaction_name = 'Apply Viewport Lineweight'
        success_message_verb = "applied to"

    elif action == 'Reset Overrides to Default':
        # Empty settings to reset to default
        transaction_name = 'Reset Viewport Lineweight'
        success_message_verb = "reset for"

    return override, transaction_name, success_message_verb


def find_crop_box_element(doc, view):
    """Find the crop box element for a given view."""
    try:
        # Temporarily hide crop box to find elements
        with revit.Transaction('TEMP crop box to false', doc=doc):
            view.CropBoxVisible = False

        collector = DB.FilteredElementCollector(doc, view.Id)
        shown_elements = collector.ToElementIds()

        # Show crop box again
        with revit.Transaction('TEMP crop box to true', doc=doc):
            view.CropBoxVisible = True

        # Find crop box element (difference between shown and hidden elements)
        collector = DB.FilteredElementCollector(doc, view.Id)
        collector.Excluding(shown_elements)
        crop_box_element = collector.FirstElement()

        return crop_box_element

    except Exception as e:
        print("Error finding crop box for view {}: {}".format(view.Name, e))
        return None


def process_single_view(doc, view, override, transaction_name, config):
    """Process a single view to apply or reset overrides."""
    view_type_name = view.ViewType.ToString()

    # Check if view type is allowed
    if config.get('allowed_view_types') and view_type_name not in config['allowed_view_types']:
        return False, "Type '{}' not in allowed types".format(view_type_name)

    # Find crop box
    crop_box_element = find_crop_box_element(doc, view)
    if not crop_box_element:
        return False, "No crop box found"

    try:
        # Apply override settings
        with revit.Transaction('{} for {}'.format(transaction_name, view.Name), doc=doc):
            view.SetElementOverrides(crop_box_element.Id, override)
        return True, None
    except Exception as e:
        return False, str(e)


def display_results(transaction_name, stats, failed_details, config, action, success_message_verb):
    """Display processing results to the user using toast notifications."""

    if stats['cancelled']:
        forms.alert("Operation was cancelled by the user.", title='Operation Cancelled')
        return

    if stats['processed'] > 0:
        message = 'Successfully {} overrides for {} view(s)!'.format(success_message_verb, stats['processed'])

        if action == 'Apply Standard Overrides':
            message += '\n\nApplied settings:\n- Line weight: {}\n- Line pattern: {}'.format(config['line_weight'], config['line_pattern_name'])

        if failed_details and config.get('show_detailed_results', True):
            message += '\n\nFailed views/errors (max 5 shown):\n- ' + '\n- '.join(failed_details[:5])
            if len(failed_details) > 5:
                message += '\n- ... and {} more. Check output window for all details.'.format(len(failed_details) - 5)

        forms.alert(message, title='Operation Complete')

    else:
        if not failed_details:
            forms.alert(
                'No views were modified. This might be because no crop boxes were found or no applicable views were selected.',
                title='Operation Note'
            )
        else:
            message = 'No views were successfully modified.'
            if config.get('show_detailed_results', True):
                message += '\n\nFailed views/errors (max 5 shown):\n- ' + '\n- '.join(failed_details[:5])
                if len(failed_details) > 5:
                    message += '\n- ... and {} more. Check output window for all details.'.format(len(failed_details) - 5)
            forms.alert(message, title='Operation Failed')


def main():
    """Main function to execute the crop view override script."""
    # Initialize document (no console output needed)
    doc = revit.doc

    # Load configuration
    config = load_configuration()

    # Get views on sheets
    views_on_sheet = get_views_on_sheets(doc, config.get('allowed_view_types'))

    if not views_on_sheet:
        view_types_str = ', '.join(config.get('allowed_view_types', ['All']))
        forms.alert(
            'No {} views found on sheets. Please make sure you have views of the specified type placed on sheets.'.format(view_types_str),
            exitscript=True
        )

    # Let user select views
    selected_views = forms.SelectFromList.show(
        views_on_sheet,
        button_name='Select Views',
        multiselect=True,
        name_attr='Name'
    )

    if not selected_views:
        forms.alert('No views were selected. Please select at least one view.', exitscript=True)

    # Ask user for action
    action = forms.CommandSwitchWindow.show(
        ['Apply Standard Overrides', 'Reset Overrides to Default'],
        message='What action would you like to perform on the selected views?'
    )

    if not action:
        forms.alert("No action selected. Exiting.", exitscript=True)

    # Create override settings
    override, transaction_name, success_message_verb = create_override_settings(doc, config, action)

    # Process views
    # Console output removed - using toast notifications only

    stats = {
        'processed': 0,
        'skipped': 0,
        'errors': 0,
        'cancelled': False
    }
    failed_details = []

    # Setup progress bar
    total_views = len(selected_views)
    if config.get('show_progress_bar', True):
        progress_bar = forms.ProgressBar(title=transaction_name, total=total_views, cancellable=True)
    else:
        progress_bar = DummyProgressBar(title=transaction_name, total=total_views, cancellable=True)

    with progress_bar as pb:
        for i, view in enumerate(selected_views):
            if pb.cancelled:
                stats['cancelled'] = True
                break

            success, error_message = process_single_view(doc, view, override, transaction_name, config)

            if success:
                stats['processed'] += 1
                # View processed successfully - no console output needed
            elif error_message == "No crop box found":
                stats['errors'] += 1
                failed_details.append("{} ({})".format(view.Name, error_message))
                # Failed to find crop box - details will be shown in final toast
            elif "not in allowed types" in error_message:
                stats['skipped'] += 1
                # View type not allowed - will be summarized in final toast
            else:
                stats['errors'] += 1
                failed_details.append("{} ({})".format(view.Name, error_message))
                # Processing error - details will be shown in final toast

            # Safely update progress bar, handling potential UI threading issues
            try:
                if not pb.cancelled:
                    pb.update_progress(i + 1, total_views)
            except (AttributeError, Exception):
                # Progress bar might be disposed or have threading issues
                # Continue processing without progress updates
                pass

    # Display results using toast notifications
    display_results(transaction_name, stats, failed_details, config, action, success_message_verb)


if __name__ == "__main__":
    main()
