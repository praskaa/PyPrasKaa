# -*- coding: utf-8 -*-
"""
UI Utility Functions

Helper functions untuk membuat dan mengelola UI components.

Author: PrasKaa
"""

# ╦ ╦╔═╗╔╦╗╔═╗╔╦╗╔═╗
# ║║║║╣  ║ ║ ║ ║║╚═╗
# ╚╩╝╚═╝ ╩ ╚═╝═╩╝╚═╝ IMPORTS
# ====================================================================================================
from ui.ui_styles import DARK_BLUE_THEME, BUTTON_SIZES, FONT_SIZES

# ╔╗ ╦  ╔═╗╔═╗╦╔═  ╔═╗╦ ╦╔═╗╔═╗╔╦╗
# ╠╩╗║  ║ ║║ ║╠╩╗  ╚═╗╠═╣║╣ ║╣  ║
# ╚═╝╩═╝╚═╝╚═╝╩ ╩  ╚═╝╩ ╩╚═╝╚═╝ ╩  BUTTON FACTORIES
# ====================================================================================================

def create_modern_button(content, click_handler=None, height=None, width=None, style_name="ModernButton"):
    """
    Factory function untuk membuat button dengan styling konsisten.

    Args:
        content (str): Button text
        click_handler (callable): Click event handler
        height (int, optional): Button height
        width (int, optional): Button width
        style_name (str): Style resource name

    Returns:
        Button: Configured WPF Button
    """
    from System.Windows.Controls import Button

    button = Button()
    button.Content = content
    button.Height = height or BUTTON_SIZES['default'][0]
    button.Width = width or BUTTON_SIZES['default'][1]

    # Set font properties
    button.FontFamily = "Roboto, Segoe UI"
    button.FontSize = FONT_SIZES['body']

    # Set styling
    if hasattr(button, 'Style'):
        # Style akan diset oleh XAML atau parent container
        pass

    # Set click handler
    if click_handler:
        button.Click += click_handler

    return button

def create_icon_button(icon_text, click_handler=None, tooltip=None):
    """
    Factory function untuk membuat icon button.

    Args:
        icon_text (str): Icon unicode character (e.g., "✕", "✓", "⚠")
        click_handler (callable): Click event handler
        tooltip (str): Button tooltip

    Returns:
        Button: Configured icon button
    """
    from System.Windows.Controls import Button

    button = Button()
    button.Content = icon_text
    button.FontSize = FONT_SIZES['header']
    button.Width = 30
    button.Height = 30
    button.FontFamily = "Segoe UI Symbol, Segoe UI"

    if tooltip:
        from System.Windows.Controls import ToolTip
        button.ToolTip = ToolTip(Content=tooltip)

    if click_handler:
        button.Click += click_handler

    return button

# ╔═╗╦  ╦╔═╗╔╗╔╔╦╗  ╦ ╦╔═╗╔╗╔╔╦╗╦  ╔═╗╦═╗╔═╗
# ║╣ ╚╗╔╝║╣ ║║║ ║   ╠═╣╠═╣║║║ ║║║  ║╣ ╠╦╝╚═╗
# ╚═╝ ╚╝ ╚═╝╝╚╝ ╩   ╩ ╩╩ ╩╝╚╝═╩╝╩═╝╚═╝╩╚═╚═╝ TEXTBOX FACTORIES
# ====================================================================================================

def create_modern_textbox(text="", watermark=None, max_length=None):
    """
    Factory function untuk membuat textbox dengan styling konsisten.

    Args:
        text (str): Initial text
        watermark (str): Placeholder text
        max_length (int): Maximum character length

    Returns:
        TextBox: Configured WPF TextBox
    """
    from System.Windows.Controls import TextBox

    textbox = TextBox()
    textbox.Text = text or ""
    textbox.FontFamily = "Roboto, Segoe UI"
    textbox.FontSize = FONT_SIZES['body']

    if max_length:
        textbox.MaxLength = max_length

    # Watermark functionality would require additional controls
    # For now, just set placeholder in tag
    if watermark:
        textbox.Tag = watermark

    return textbox

def create_filter_textbox(placeholder="Filter items...", change_handler=None):
    """
    Factory function untuk membuat filter textbox.

    Args:
        placeholder (str): Placeholder text
        change_handler (callable): Text changed event handler

    Returns:
        TextBox: Configured filter textbox
    """
    textbox = create_modern_textbox(watermark=placeholder)

    if change_handler:
        textbox.TextChanged += change_handler

    return textbox

# ╔═╗╦═╗╔═╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ╠═╝╠╦╝║ ║╠═╝║╣ ╠╦╝ ║ ╚═╗
# ╩  ╩╚═╚═╝╩  ╚═╝╩╚═ ╩ ╚═╝ CHECKBOX FACTORIES
# ====================================================================================================

def create_modern_checkbox(content, is_checked=False, click_handler=None):
    """
    Factory function untuk membuat checkbox dengan styling konsisten.

    Args:
        content (str): Checkbox label
        is_checked (bool): Initial checked state
        click_handler (callable): Click event handler

    Returns:
        CheckBox: Configured WPF CheckBox
    """
    from System.Windows.Controls import CheckBox

    checkbox = CheckBox()
    checkbox.Content = content
    checkbox.IsChecked = is_checked
    checkbox.FontFamily = "Roboto, Segoe UI"
    checkbox.FontSize = FONT_SIZES['body']

    if click_handler:
        checkbox.Click += click_handler

    return checkbox

# ╔═╗╦  ╦╔═╗╔╗╔  ╦ ╦╔═╗╔╗╔╔╦╗╦  ╔═╗╦═╗╔═╗
# ║╣ ╚╗╔╝║╣ ║║║  ╠═╣╠═╣║║║ ║║║  ║╣ ╠╦╝╚═╗
# ╚═╝ ╚╝ ╚═╝╝╚╝  ╩ ╩╩ ╩╝╚╝═╩╝╩═╝╚═╝╩╚═╚═╝ LABEL/TEXT FACTORIES
# ====================================================================================================

def create_header_text(text, font_size=None):
    """
    Factory function untuk membuat header text.

    Args:
        text (str): Header text
        font_size (int, optional): Font size

    Returns:
        TextBlock: Configured header text
    """
    from System.Windows.Controls import TextBlock

    textblock = TextBlock()
    textblock.Text = text
    textblock.FontFamily = "Roboto, Segoe UI"
    textblock.FontSize = font_size or FONT_SIZES['header']
    textblock.FontWeight = "SemiBold"

    return textblock

def create_body_text(text, foreground=None):
    """
    Factory function untuk membuat body text.

    Args:
        text (str): Body text
        foreground (str): Text color

    Returns:
        TextBlock: Configured body text
    """
    from System.Windows.Controls import TextBlock

    textblock = TextBlock()
    textblock.Text = text
    textblock.FontFamily = "Roboto, Segoe UI"
    textblock.FontSize = FONT_SIZES['body']

    if foreground:
        from System.Windows.Media import SolidColorBrush
        textblock.Foreground = SolidColorBrush(foreground)

    return textblock

# ╔═╗╦ ╦╔═╗╔═╗╔╦╗  ╔═╗╦ ╦╔═╗╔═╗╔╦╗
# ╚═╗╠═╣║╣ ║╣  ║   ╚═╗╠═╣║╣ ║╣  ║
# ╚═╝╩ ╩╚═╝╚═╝ ╩   ╚═╝╩ ╩╚═╝╚═╝ ╩  WINDOW UTILITIES
# ====================================================================================================

def setup_window_properties(window, title, width=None, height=None):
    """
    Setup common window properties.

    Args:
        window: WPF Window object
        title (str): Window title
        width (int, optional): Window width
        height (int, optional): Window height
    """
    from ui.ui_styles import WINDOW_SIZES

    window.Title = title
    window.Width = width or WINDOW_SIZES['default'][0]
    window.Height = height or WINDOW_SIZES['default'][1]
    window.WindowStartupLocation = "CenterScreen"
    window.ShowInTaskbar = False
    window.ResizeMode = "NoResize"
    window.WindowStyle = "None"

    # Set background color
    from System.Windows.Media import SolidColorBrush
    window.Background = SolidColorBrush(DARK_BLUE_THEME['background_dark'])

def center_window_on_screen(window):
    """
    Center window on screen.

    Args:
        window: WPF Window object
    """
    from System.Windows import SystemParameters

    screen_width = SystemParameters.PrimaryScreenWidth
    screen_height = SystemParameters.PrimaryScreenHeight

    window.Left = (screen_width - window.Width) / 2
    window.Top = (screen_height - window.Height) / 2

# ╔═╗╦═╗╔═╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ╠═╝╠╦╝║ ║╠═╝║╣ ╠╦╝ ║ ╚═╗
# ╩  ╩╚═╚═╝╩  ╚═╝╩╚═ ╩ ╚═╝ VALIDATION UTILITIES
# ==================================================

def validate_text_input(text, min_length=0, max_length=None, allow_empty=False):
    """
    Validate text input.

    Args:
        text (str): Text to validate
        min_length (int): Minimum length
        max_length (int): Maximum length
        allow_empty (bool): Allow empty text

    Returns:
        tuple: (is_valid, error_message)
    """
    if not allow_empty and not text:
        return False, "Text cannot be empty"

    if len(text) < min_length:
        return False, "Text must be at least {} characters".format(min_length)

    if max_length and len(text) > max_length:
        return False, "Text cannot exceed {} characters".format(max_length)

    return True, ""

def validate_numeric_input(value, min_value=None, max_value=None):
    """
    Validate numeric input.

    Args:
        value: Value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value

    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        num_value = float(value)
    except (ValueError, TypeError):
        return False, "Value must be numeric"

    if min_value is not None and num_value < min_value:
        return False, "Value must be at least {}".format(min_value)

    if max_value is not None and num_value > max_value:
        return False, "Value cannot exceed {}".format(max_value)

    return True, ""

# ╔═╗╦═╗╔═╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ╠═╝╠╦╝║ ║╠═╝║╣ ╠╦╝ ║ ╚═╗
# ╩  ╩╚═╚═╝╩  ╚═╝╩╚═ ╩ ╚═╝ LOGGING UTILITIES
# ==================================================

def log_ui_action(action, details=None):
    """
    Log UI action untuk debugging.

    Args:
        action (str): Action name
        details (dict, optional): Additional details
    """
    import datetime

    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    detail_str = " - {}".format(details) if details else ""
    print("[{}] UI Action: {}{}".format(timestamp, action, detail_str))

def safe_ui_operation(operation_func, error_message="UI operation failed"):
    """
    Execute UI operation dengan error handling.

    Args:
        operation_func (callable): Function to execute
        error_message (str): Error message if operation fails

    Returns:
        tuple: (success, result)
    """
    try:
        result = operation_func()
        return True, result
    except Exception as ex:
        print("{}: {}".format(error_message, str(ex)))
        return False, None
