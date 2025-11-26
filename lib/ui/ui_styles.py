# -*- coding: utf-8 -*-
"""
UI Styles and Theme Constants

Centralized styling definitions untuk konsistensi visual di semua dialog.

Author: PrasKaa
"""

# ╦ ╦╔═╗╔╦╗╔═╗╔╦╗╔═╗
# ║║║║╣  ║ ║ ║ ║║╚═╗
# ╚╩╝╚═╝ ╩ ╚═╝═╩╝╚═╝ THEME CONSTANTS
# ====================================================================================================

# Dark Blue Theme - Main color scheme
DARK_BLUE_THEME = {
    "header_background": "#1E2A3B",
    "text_white": "#FFFFFF",
    "text_gray": "#A3B4CC",
    "accent_color": "#2B5797",
    "accent_light": "#3B6DB0",
    "warning_color": "#FF6B6B",
    "list_hover": "#202D40",
    "background": "#151E2B",
    "background_dark": "#101F33",
    "border_color": "#2B4766",
    "border_light": "#3D3E4D",
    "success_color": "#90EE90",
    "error_color": "#FF6B6B"
}

# ScrollBar Colors
SCROLLBAR_THEME = {
    "track_brush": "#1A2635",
    "thumb_brush": "#2B4766",
    "thumb_hover_brush": "#3B6DB0"
}

# ╔═╗╔═╗╔═╗╔═╗╔═╗╔╗ ╔═╗═╗ ╦
# ║ ║║  ║ ║╠═╝║╣ ╠╩╗║ ║╔╩╦╝
# ╚═╝╚═╝╚═╝╩  ╚═╝╚═╝╚═╝╩ ╚═ COMMON DIMENSIONS
# ==================================================

WINDOW_SIZES = {
    "default": (600, 700),
    "large": (800, 700),
    "small": (500, 600)
}

BUTTON_SIZES = {
    "default": (32, None),  # Height, Width (None = auto)
    "large": (40, None),
    "small": (28, None)
}

FONT_SIZES = {
    "header": 16,
    "title": 14,
    "body": 13,
    "small": 12
}

# ╔═╗╔═╗╔═╗╔═╗╔═╗╔╗ ╔═╗═╗ ╦
# ║ ║║  ║ ║╠═╝║╣ ╠╩╗║ ║╔╩╦╝
# ╚═╝╚═╝╚═╝╩  ╚═╝╚═╝╚═╝╩ ╚═ COMMON STYLES
# ==================================================

def get_common_resources():
    """Return common XAML ResourceDictionary sebagai string."""
    return """
<ResourceDictionary xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
                    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">

    <!-- Color Brushes -->
    <SolidColorBrush x:Key="header_background" Color="{0}"/>
    <SolidColorBrush x:Key="text_white" Color="{1}"/>
    <SolidColorBrush x:Key="text_gray" Color="{2}"/>
    <SolidColorBrush x:Key="accent_color" Color="{3}"/>
    <SolidColorBrush x:Key="accent_light" Color="{4}"/>
    <SolidColorBrush x:Key="warning_color" Color="{5}"/>
    <SolidColorBrush x:Key="list_hover" Color="{6}"/>
    <SolidColorBrush x:Key="background" Color="{7}"/>
    <SolidColorBrush x:Key="border_color" Color="{8}"/>
    <SolidColorBrush x:Key="border_light" Color="{9}"/>
    <SolidColorBrush x:Key="success_color" Color="{10}"/>
    <SolidColorBrush x:Key="error_color" Color="{11}"/>

    <!-- ScrollBar Colors -->
    <SolidColorBrush x:Key="ScrollBarTrackBrush" Color="{12}"/>
    <SolidColorBrush x:Key="ScrollBarThumbBrush" Color="{13}"/>
    <SolidColorBrush x:Key="ScrollBarThumbHoverBrush" Color="{14}"/>

    <!-- Modern Button Style -->
    <Style x:Key="ModernButton" TargetType="Button">
        <Setter Property="Background" Value="{{StaticResource accent_color}}"/>
        <Setter Property="Foreground" Value="{{StaticResource text_white}}"/>
        <Setter Property="BorderThickness" Value="0"/>
        <Setter Property="Padding" Value="15,8"/>
        <Setter Property="FontFamily" Value="Roboto, Segoe UI"/>
        <Setter Property="FontSize" Value="{15}"/>
        <Setter Property="Template">
            <Setter.Value>
                <ControlTemplate TargetType="Button">
                    <Border Background="{{TemplateBinding Background}}"
                            CornerRadius="6"
                            Padding="{{TemplateBinding Padding}}">
                        <ContentPresenter HorizontalAlignment="Center"
                                        VerticalAlignment="Center"/>
                    </Border>
                </ControlTemplate>
            </Setter.Value>
        </Setter>
        <Style.Triggers>
            <Trigger Property="IsMouseOver" Value="True">
                <Setter Property="Background" Value="{{StaticResource accent_light}}"/>
                <Setter Property="Cursor" Value="Hand"/>
            </Trigger>
            <Trigger Property="IsEnabled" Value="False">
                <Setter Property="Opacity" Value="0.6"/>
            </Trigger>
        </Style.Triggers>
    </Style>

    <!-- Modern TextBox Style -->
    <Style x:Key="ModernTextBox" TargetType="TextBox">
        <Setter Property="Background" Value="#2A2B36"/>
        <Setter Property="Foreground" Value="{{StaticResource text_white}}"/>
        <Setter Property="BorderThickness" Value="1"/>
        <Setter Property="BorderBrush" Value="{{StaticResource border_light}}"/>
        <Setter Property="Padding" Value="10,5"/>
        <Setter Property="FontFamily" Value="Roboto, Segoe UI"/>
        <Setter Property="FontSize" Value="{16}"/>
        <Setter Property="Template">
            <Setter.Value>
                <ControlTemplate TargetType="TextBox">
                    <Border Background="{{TemplateBinding Background}}"
                            BorderBrush="{{TemplateBinding BorderBrush}}"
                            BorderThickness="{{TemplateBinding BorderThickness}}"
                            CornerRadius="6">
                        <ScrollViewer x:Name="PART_ContentHost"/>
                    </Border>
                </ControlTemplate>
            </Setter.Value>
        </Setter>
    </Style>

    <!-- Modern ListView Style -->
    <Style x:Key="ModernListView" TargetType="ListView">
        <Setter Property="Background" Value="{{StaticResource background}}"/>
        <Setter Property="BorderThickness" Value="1"/>
        <Setter Property="BorderBrush" Value="{{StaticResource border_color}}"/>
        <Setter Property="ScrollViewer.HorizontalScrollBarVisibility" Value="Auto"/>
        <Setter Property="ScrollViewer.VerticalScrollBarVisibility" Value="Auto"/>
        <Setter Property="FontFamily" Value="Roboto, Segoe UI"/>
        <Setter Property="VirtualizingStackPanel.IsVirtualizing" Value="True"/>
        <Setter Property="VirtualizingStackPanel.VirtualizationMode" Value="Recycling"/>
        <Setter Property="Template">
            <Setter.Value>
                <ControlTemplate TargetType="ListView">
                    <Border Background="{{TemplateBinding Background}}"
                            BorderBrush="{{TemplateBinding BorderBrush}}"
                            BorderThickness="{{TemplateBinding BorderThickness}}"
                            CornerRadius="6">
                        <ScrollViewer Focusable="False">
                            <ItemsPresenter/>
                        </ScrollViewer>
                    </Border>
                </ControlTemplate>
            </Setter.Value>
        </Setter>
    </Style>

    <!-- ListView Item Style -->
    <Style TargetType="ListViewItem">
        <Setter Property="Padding" Value="8,6"/>
        <Setter Property="Background" Value="Transparent"/>
        <Setter Property="Template">
            <Setter.Value>
                <ControlTemplate TargetType="ListViewItem">
                    <Border Background="{{TemplateBinding Background}}"
                            BorderThickness="0"
                            Padding="{{TemplateBinding Padding}}">
                        <GridViewRowPresenter />
                    </Border>
                    <ControlTemplate.Triggers>
                        <Trigger Property="IsMouseOver" Value="True">
                            <Setter Property="Background" Value="{{StaticResource list_hover}}"/>
                        </Trigger>
                        <Trigger Property="IsSelected" Value="True">
                            <Setter Property="Background" Value="{{StaticResource accent_color}}"/>
                        </Trigger>
                    </ControlTemplate.Triggers>
                </ControlTemplate>
            </Setter.Value>
        </Setter>
    </Style>

    <!-- Modern CheckBox Style -->
    <Style x:Key="ModernCheckBox" TargetType="CheckBox">
        <Setter Property="Foreground" Value="{{StaticResource text_white}}"/>
        <Setter Property="Background" Value="#2A3847"/>
        <Setter Property="BorderBrush" Value="{{StaticResource text_white}}"/>
        <Setter Property="FontFamily" Value="Roboto, Segoe UI"/>
        <Setter Property="FontSize" Value="{17}"/>
        <Setter Property="Template">
            <Setter.Value>
                <ControlTemplate TargetType="CheckBox">
                    <Grid>
                        <Border x:Name="Border"
                                HorizontalAlignment="Left"
                                Width="16" Height="16"
                                Background="{{TemplateBinding Background}}"
                                BorderBrush="{{TemplateBinding BorderBrush}}"
                                BorderThickness="1"
                                CornerRadius="2">
                            <Path x:Name="Checkmark"
                                  Stroke="{{StaticResource text_white}}"
                                  StrokeThickness="2"
                                  Data="M 3,8 L 7,12 L 13,4"
                                  Visibility="Collapsed"/>
                        </Border>
                        <ContentPresenter Margin="18,0,0,0"
                                          VerticalAlignment="Center"/>
                    </Grid>
                    <ControlTemplate.Triggers>
                        <Trigger Property="IsChecked" Value="True">
                            <Setter TargetName="Checkmark" Property="Visibility" Value="Visible"/>
                            <Setter TargetName="Border" Property="Background" Value="{{StaticResource accent_color}}"/>
                        </Trigger>
                        <Trigger Property="IsMouseOver" Value="True">
                            <Setter TargetName="Border" Property="BorderBrush" Value="{{StaticResource accent_light}}"/>
                        </Trigger>
                    </ControlTemplate.Triggers>
                </ControlTemplate>
            </Setter.Value>
        </Setter>
    </Style>

    <!-- Text Block Style -->
    <Style TargetType="TextBlock">
        <Setter Property="FontFamily" Value="Roboto, Segoe UI"/>
        <Setter Property="FontSize" Value="{18}"/>
        <Setter Property="TextOptions.TextFormattingMode" Value="Ideal"/>
        <Setter Property="TextOptions.TextRenderingMode" Value="ClearType"/>
    </Style>

    <!-- Status Badge Style -->
    <Style x:Key="StatusBadge" TargetType="Border">
        <Setter Property="CornerRadius" Value="4"/>
        <Setter Property="Padding" Value="8,4"/>
        <Setter Property="HorizontalAlignment" Value="Center"/>
    </Style>

</ResourceDictionary>
""".format(
        DARK_BLUE_THEME['header_background'],
        DARK_BLUE_THEME['text_white'],
        DARK_BLUE_THEME['text_gray'],
        DARK_BLUE_THEME['accent_color'],
        DARK_BLUE_THEME['accent_light'],
        DARK_BLUE_THEME['warning_color'],
        DARK_BLUE_THEME['list_hover'],
        DARK_BLUE_THEME['background'],
        DARK_BLUE_THEME['border_color'],
        DARK_BLUE_THEME['border_light'],
        DARK_BLUE_THEME['success_color'],
        DARK_BLUE_THEME['error_color'],
        SCROLLBAR_THEME['track_brush'],
        SCROLLBAR_THEME['thumb_brush'],
        SCROLLBAR_THEME['thumb_hover_brush'],
        FONT_SIZES['body'],
        FONT_SIZES['body'],
        FONT_SIZES['body'],
        FONT_SIZES['body']
    )

def get_theme_color(color_name):
    """Get color value dari theme by name."""
    return DARK_BLUE_THEME.get(color_name, DARK_BLUE_THEME['text_white'])

def create_color_brush(color_name):
    """Create SolidColorBrush dari theme color."""
    from System.Windows.Media import SolidColorBrush
    color_value = get_theme_color(color_name)
    return SolidColorBrush(color_value)
