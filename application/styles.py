"""
Modern dark theme styles for the Renderware Modding Suite
Inspired by VS Code and other modern development environments
"""

import sys
import os
from .responsive_utils import get_responsive_manager


def initialize_qt_resources():
    """Initialize Qt resources for compiled applications"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        try:
            # Ensure Qt plugins can be found
            executable_dir = os.path.dirname(sys.executable)
            qt_plugin_path = os.path.join(executable_dir, "PySide6", "plugins")
            
            if os.path.exists(qt_plugin_path):
                os.environ['QT_PLUGIN_PATH'] = qt_plugin_path
                print(f"✅ Qt plugin path set to: {qt_plugin_path}")
            
            # Set other Qt environment variables for stability
            os.environ.setdefault('QT_FONT_DPI', '96')
            os.environ.setdefault('QT_SCALE_FACTOR', '1')
            
        except Exception as e:
            print(f"⚠️ Warning initializing Qt resources: {e}")


class ModernDarkTheme:
    """Color palette for the modern dark theme"""
    
    def __init__(self):
        """Initialize the theme and Qt resources"""
        initialize_qt_resources()
    
    # Base colors
    BACKGROUND_PRIMARY = "#1e1e1e"
    BACKGROUND_SECONDARY = "#252526" 
    BACKGROUND_TERTIARY = "#2d2d30"
    
    # Text colors
    TEXT_PRIMARY = "#cccccc"
    TEXT_SECONDARY = "#969696"
    TEXT_ACCENT = "#007acc"
    TEXT_SUCCESS = "#4ec9b0"
    TEXT_WARNING = "#dcdcaa"
    TEXT_ERROR = "#f44747"
    
    # Border colors
    BORDER_PRIMARY = "#2d2d30"
    BORDER_SECONDARY = "#464647"
    BORDER_ACCENT = "#007acc"
    
    # Interactive colors
    HOVER_COLOR = "#3e3e42"
    SELECTION_COLOR = "#37373d"
    BUTTON_PRIMARY = "#0e639c"
    BUTTON_HOVER = "#1177bb"
    BUTTON_PRESSED = "#005a9e"
    
    @staticmethod
    def apply_dark_palette(app):
        """Apply dark palette to the application to override system theme"""
        from PySide6.QtGui import QPalette, QColor
        
        dark_palette = QPalette()
        # Background colors
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(ModernDarkTheme.BACKGROUND_PRIMARY))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(ModernDarkTheme.TEXT_PRIMARY))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(ModernDarkTheme.BACKGROUND_SECONDARY))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(ModernDarkTheme.BACKGROUND_TERTIARY))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(ModernDarkTheme.BACKGROUND_TERTIARY))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(ModernDarkTheme.TEXT_PRIMARY))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(ModernDarkTheme.TEXT_PRIMARY))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(ModernDarkTheme.BUTTON_PRIMARY))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(ModernDarkTheme.TEXT_PRIMARY))
        dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(ModernDarkTheme.TEXT_ACCENT))
        # Selection colors
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(ModernDarkTheme.TEXT_ACCENT))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(ModernDarkTheme.TEXT_ACCENT))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        # Disabled colors
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(ModernDarkTheme.TEXT_SECONDARY))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(ModernDarkTheme.TEXT_SECONDARY))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(ModernDarkTheme.TEXT_SECONDARY))
        
        app.setPalette(dark_palette)
    
    @staticmethod
    def get_main_stylesheet():
        """Main application stylesheet with responsive sizing"""
        rm = get_responsive_manager()
        fonts = rm.get_font_config()
        spacing = rm.get_spacing_config()
        button_size = rm.get_button_size()
        
        return f"""
        QMainWindow {{
            background-color: {ModernDarkTheme.BACKGROUND_PRIMARY};
            color: {ModernDarkTheme.TEXT_PRIMARY};
        }}
        
        /* Menu Bar Styles */
        QMenuBar {{
            background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
            color: {ModernDarkTheme.TEXT_PRIMARY};
            border: none;
            padding: {spacing['small']}px;
            font-size: {fonts['menu']['size']}px;
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: {spacing['small']}px {spacing['medium']}px;
            border-radius: 4px;
            margin: {spacing['small']//2}px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {ModernDarkTheme.HOVER_COLOR};
        }}
        
        QMenuBar::item:pressed {{
            background-color: {ModernDarkTheme.TEXT_ACCENT};
        }}
        
        QMenu {{
            background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
            color: {ModernDarkTheme.TEXT_PRIMARY};
            border: 1px solid {ModernDarkTheme.BORDER_SECONDARY};
            padding: {spacing['small']}px;
            font-size: {fonts['menu']['size']}px;
        }}
        
        QMenu::item {{
            padding: {spacing['small']}px {spacing['medium']}px;
            border-radius: 4px;
        }}
        
        QMenu::item:selected {{
            background-color: {ModernDarkTheme.HOVER_COLOR};
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {ModernDarkTheme.BORDER_SECONDARY};
            margin: {spacing['small']}px {spacing['medium']}px;
        }}
        
        /* Toolbar Styles */
        QToolBar {{
            background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
            border: none;
            spacing: {spacing['small']}px;
            padding: {spacing['small']}px;
        }}
        
        QToolBar::separator {{
            background-color: {ModernDarkTheme.BORDER_SECONDARY};
            width: 1px;
            margin: {spacing['small']}px {spacing['medium']}px;
        }}
        
        /* Button Styles */
        QPushButton {{
            background-color: {ModernDarkTheme.BUTTON_PRIMARY};
            color: white;
            border: none;
            padding: {spacing['small']}px {spacing['small'] + 2}px;
            border-radius: 4px;
            font-weight: 500;
            font-size: {fonts['body']['size']}px;
            min-width: {button_size[0]}px;
            min-height: {button_size[1]}px;
            max-height: {button_size[1] + 4}px;
        }}
        
        QPushButton:hover {{
            background-color: {ModernDarkTheme.BUTTON_HOVER};
        }}
        
        QPushButton:pressed {{
            background-color: {ModernDarkTheme.BUTTON_PRESSED};
        }}
        
        QPushButton:disabled {{
            background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
            color: {ModernDarkTheme.TEXT_SECONDARY};
        }}
        
        /* Tree Widget Styles */
        QTreeWidget {{
            background-color: {ModernDarkTheme.BACKGROUND_SECONDARY};
            color: {ModernDarkTheme.TEXT_PRIMARY};
            border: none;
            outline: none;
            font-size: {fonts['body']['size']}px;
        }}
        
        QTreeWidget::item {{
            padding: {spacing['small']}px;
            border-bottom: 1px solid {ModernDarkTheme.BACKGROUND_TERTIARY};
        }}
        
        QTreeWidget::item:selected {{
            background-color: {ModernDarkTheme.SELECTION_COLOR};
        }}
        
        QTreeWidget::item:hover {{
            background-color: {ModernDarkTheme.HOVER_COLOR};
        }}
        
        QTreeWidget::branch:closed:has-children {{
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTYgNEwxMCA4TDYgMTJWNFoiIGZpbGw9IiNjY2NjY2MiLz4KPC9zdmc+);
        }}
        
        QTreeWidget::branch:open:has-children {{
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQgNkw4IDEwTDEyIDZINFoiIGZpbGw9IiNjY2NjY2MiLz4KPC9zdmc+);
        }}
        
        /* Tab Widget Styles */
        QTabWidget::pane {{
            background-color: {ModernDarkTheme.BACKGROUND_PRIMARY};
            border: 1px solid {ModernDarkTheme.BORDER_PRIMARY};
        }}
        
        QTabBar::tab {{
            background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
            color: {ModernDarkTheme.TEXT_PRIMARY};
            padding: {spacing['small']}px {spacing['medium']}px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            min-width: {rm.get_scaled_size(80)}px;
            font-size: {fonts['body']['size']}px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {ModernDarkTheme.BACKGROUND_PRIMARY};
            color: {ModernDarkTheme.TEXT_ACCENT};
            border-bottom: 2px solid {ModernDarkTheme.TEXT_ACCENT};
        }}
        
        QTabBar::tab:hover {{
            background-color: {ModernDarkTheme.HOVER_COLOR};
        }}
        
        QTabBar::close-button {{
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDRMNCA5NU00IDRMMTIgMTIiIHN0cm9rZT0iI2NjY2NjYyIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8L3N2Zz4K);
            subcontrol-position: right;
            subcontrol-origin: padding;
            margin: {spacing['small']}px;
            padding: 2px;
            width: {rm.get_icon_size()}px;
            height: {rm.get_icon_size()}px;
            background-color: transparent;
            border-radius: 2px;
        }}
        
        QTabBar::close-button:hover {{
            background-color: {ModernDarkTheme.TEXT_ERROR};
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDRMNCA5NU00IDRMMTIgMTIiIHN0cm9rZT0iI2ZmZmZmZiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz4KPC9zdmc+);
        }}
        
        QTabBar::close-button:pressed {{
            background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
        }}
        
        /* Text Edit Styles */
        QTextEdit {{
            background-color: {ModernDarkTheme.BACKGROUND_PRIMARY};
            color: {ModernDarkTheme.TEXT_PRIMARY};
            border: 1px solid {ModernDarkTheme.BORDER_PRIMARY};
            font-family: {fonts['code']['family']};
            font-size: {fonts['code']['size']}px;
            line-height: 1.4;
            padding: {spacing['medium']}px;
        }}
        
        QTextEdit:focus {{
            border-color: {ModernDarkTheme.BORDER_ACCENT};
        }}
        
        /* Scrollbar Styles */
        QScrollBar:vertical {{
            background-color: {ModernDarkTheme.BACKGROUND_SECONDARY};
            width: {rm.get_scaled_size(12)}px;
            border: none;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {ModernDarkTheme.BORDER_SECONDARY};
            border-radius: {rm.get_scaled_size(6)}px;
            min-height: {rm.get_scaled_size(20)}px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {ModernDarkTheme.TEXT_SECONDARY};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background-color: {ModernDarkTheme.BACKGROUND_SECONDARY};
            height: {rm.get_scaled_size(12)}px;
            border: none;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {ModernDarkTheme.BORDER_SECONDARY};
            border-radius: {rm.get_scaled_size(6)}px;
            min-width: {rm.get_scaled_size(20)}px;
            margin: 2px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {ModernDarkTheme.TEXT_SECONDARY};
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        
        /* Status Bar Styles */
        QStatusBar {{
            background-color: {ModernDarkTheme.TEXT_ACCENT};
            color: white;
            border: none;
            font-size: {fonts['status']['size']}px;
            padding: {spacing['small']}px;
        }}
        
        /* ComboBox Styles */
        QComboBox {{
            background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
            color: {ModernDarkTheme.TEXT_PRIMARY};
            border: 1px solid {ModernDarkTheme.BORDER_SECONDARY};
            padding: {spacing['small']}px {spacing['medium']}px;
            border-radius: 4px;
            min-width: {rm.get_scaled_size(120)}px;
            font-size: {fonts['body']['size']}px;
        }}
        
        QComboBox:hover {{
            border-color: {ModernDarkTheme.BORDER_ACCENT};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: {rm.get_scaled_size(20)}px;
        }}
        
        QComboBox::down-arrow {{
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQgNkw4IDEwTDEyIDZINFoiIGZpbGw9IiNjY2NjY2MiLz4KPC9zdmc+);
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
            color: {ModernDarkTheme.TEXT_PRIMARY};
            border: 1px solid {ModernDarkTheme.BORDER_SECONDARY};
            selection-background-color: {ModernDarkTheme.TEXT_ACCENT};
            font-size: {fonts['body']['size']}px;
        }}
        
        /* Progress Bar Styles */
        QProgressBar {{
            background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
            border: 1px solid {ModernDarkTheme.BORDER_SECONDARY};
            border-radius: 4px;
            text-align: center;
            color: {ModernDarkTheme.TEXT_PRIMARY};
            height: {rm.get_scaled_size(20)}px;
            font-size: {fonts['small']['size']}px;
        }}
        
        QProgressBar::chunk {{
            background-color: {ModernDarkTheme.TEXT_ACCENT};
            border-radius: 3px;
        }}
        
        /* Splitter Styles */
        QSplitter::handle {{
            background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
        }}
        
        QSplitter::handle:horizontal {{
            width: {spacing['small']}px;
        }}
        
        QSplitter::handle:vertical {{
            height: {spacing['small']}px;
        }}
        
        QSplitter::handle:hover {{
            background-color: {ModernDarkTheme.BORDER_ACCENT};
        }}
        
        /* Frame Styles */
        QFrame#sidebarFrame {{
            background-color: {ModernDarkTheme.BACKGROUND_SECONDARY};
            border-right: 1px solid {ModernDarkTheme.BORDER_PRIMARY};
        }}
        
        /* Label Styles */
        QLabel {{
            color: {ModernDarkTheme.TEXT_PRIMARY};
            font-size: {fonts['body']['size']}px;
        }}
        
        QLabel#titleLabel {{
            color: {ModernDarkTheme.TEXT_ACCENT};
            font-weight: bold;
            font-size: {fonts['header']['size']}px;
        }}
        
        QLabel#sectionLabel {{
            color: {ModernDarkTheme.TEXT_SUCCESS};
            font-weight: bold;
            font-size: {fonts['subheader']['size']}px;
            margin: {spacing['medium']}px 0 {spacing['small']}px 0;
        }}
        
        /* List Widget Styles */
        QListWidget {{
            background-color: {ModernDarkTheme.BACKGROUND_SECONDARY};
            color: {ModernDarkTheme.TEXT_PRIMARY};
            border: 1px solid {ModernDarkTheme.BORDER_PRIMARY};
            outline: none;
            font-size: {fonts['body']['size']}px;
        }}
        
        QListWidget::item {{
            padding: {spacing['small']}px;
            border-bottom: 1px solid {ModernDarkTheme.BACKGROUND_TERTIARY};
        }}
        
        QListWidget::item:selected {{
            background-color: {ModernDarkTheme.SELECTION_COLOR};
        }}
        
        QListWidget::item:hover {{
            background-color: {ModernDarkTheme.HOVER_COLOR};
        }}
        
        /* Group Box Styles */
        QGroupBox {{
            color: {ModernDarkTheme.TEXT_PRIMARY};
            border: 1px solid {ModernDarkTheme.BORDER_SECONDARY};
            border-radius: 4px;
            margin-top: {spacing['medium']}px;
            font-size: {fonts['subheader']['size']}px;
            font-weight: bold;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: {spacing['medium']}px;
            padding: 0 {spacing['small']}px 0 {spacing['small']}px;
        }}
        
        /* Table Widget Styles */
        QTableWidget {{
            background-color: {ModernDarkTheme.BACKGROUND_SECONDARY};
            color: {ModernDarkTheme.TEXT_PRIMARY};
            gridline-color: {ModernDarkTheme.BORDER_SECONDARY};
            border: 1px solid {ModernDarkTheme.BORDER_PRIMARY};
            outline: none;
            font-size: {fonts['body']['size']}px;
        }}
        
        QTableWidget::item {{
            padding: {spacing['small']}px;
        }}
        
        QTableWidget::item:selected {{
            background-color: {ModernDarkTheme.SELECTION_COLOR};
        }}
        
        QTableWidget::item:hover {{
            background-color: {ModernDarkTheme.HOVER_COLOR};
        }}
        
        QHeaderView::section {{
            background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
            color: {ModernDarkTheme.TEXT_PRIMARY};
            padding: {spacing['medium']}px;
            border: 1px solid {ModernDarkTheme.BORDER_SECONDARY};
            font-size: {fonts['body']['size']}px;
            font-weight: bold;
        }}
        """
    
    @staticmethod
    def get_welcome_html():
        """HTML content for the welcome tab with responsive sizing"""
        rm = get_responsive_manager()
        fonts = rm.get_font_config()
        spacing = rm.get_spacing_config()
        
        # Adjust layout based on screen size
        if rm.breakpoint == "small":
            container_padding = spacing['medium']
            title_size = fonts['header']['size'] + 4
            subtitle_size = fonts['subheader']['size']
            body_size = fonts['body']['size']
            flex_direction = "column"  # Stack vertically on small screens
            section_margin = spacing['small']
        else:
            container_padding = spacing['large']
            title_size = fonts['header']['size'] + 6
            subtitle_size = fonts['subheader']['size'] + 1
            body_size = fonts['body']['size']
            flex_direction = "row"  # Side by side on larger screens
            section_margin = spacing['medium']
        
        return f"""
        <div style="color: {ModernDarkTheme.TEXT_PRIMARY}; font-size: {body_size}px; padding: {container_padding}px; font-family: 'Segoe UI', Arial, sans-serif;">
            <div style="text-align: center; margin-bottom: {spacing['xlarge'] * 2}px;">
                <h1 style="color: {ModernDarkTheme.TEXT_ACCENT}; font-size: {title_size}px; margin-bottom: {spacing['medium']}px;">
                    ⚡ Renderware Modding Suite
                </h1>
                <p style="color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: {subtitle_size}px;">
                    Professional modding tools for 3D era Grand Theft Auto games
                </p>
            </div>
            
            <div style="display: flex; flex-direction: {flex_direction}; justify-content: space-between; margin-bottom: {spacing['xlarge']}px; gap: {spacing['large']}px;">
                <div style="flex: 1;">
                    <h3 style="color: {ModernDarkTheme.TEXT_SUCCESS}; margin-bottom: {spacing['medium']}px; font-size: {fonts['subheader']['size']}px;">🎮 Supported Games</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li style="margin-bottom: {spacing['medium']}px; padding: {spacing['medium']}px; background-color: {ModernDarkTheme.BACKGROUND_SECONDARY}; border-radius: 4px;">
                            <strong style="color: {ModernDarkTheme.TEXT_ACCENT}; font-size: {body_size}px;">GTA III (2001)</strong><br>
                            <span style="color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: {fonts['small']['size']}px;">Liberty City - Where it all began</span>
                        </li>
                        <li style="margin-bottom: {spacing['medium']}px; padding: {spacing['medium']}px; background-color: {ModernDarkTheme.BACKGROUND_SECONDARY}; border-radius: 4px;">
                            <strong style="color: {ModernDarkTheme.TEXT_ACCENT}; font-size: {body_size}px;">GTA Vice City (2002)</strong><br>
                            <span style="color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: {fonts['small']['size']}px;">80s Miami nostalgia and neon lights</span>
                        </li>
                        <li style="padding: {spacing['medium']}px; background-color: {ModernDarkTheme.BACKGROUND_SECONDARY}; border-radius: 4px;">
                            <strong style="color: {ModernDarkTheme.TEXT_ACCENT}; font-size: {body_size}px;">GTA San Andreas (2004)</strong><br>
                            <span style="color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: {fonts['small']['size']}px;">The biggest adventure across three cities</span>
                        </li>
                    </ul>
                </div>
                
                <div style="flex: 1;">
                    <h3 style="color: {ModernDarkTheme.TEXT_SUCCESS}; margin-bottom: {spacing['medium']}px; font-size: {fonts['subheader']['size']}px;">📁 Supported Formats</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li style="margin-bottom: {spacing['small']}px; padding: {spacing['small']}px {spacing['medium']}px; background-color: {ModernDarkTheme.BACKGROUND_TERTIARY}; border-radius: 4px; border-left: 3px solid {ModernDarkTheme.TEXT_ACCENT}; font-size: {fonts['small']['size']}px;">
                            <strong>DFF</strong> - 3D Models and meshes
                        </li>
                        <li style="margin-bottom: {spacing['small']}px; padding: {spacing['small']}px {spacing['medium']}px; background-color: {ModernDarkTheme.BACKGROUND_TERTIARY}; border-radius: 4px; border-left: 3px solid {ModernDarkTheme.TEXT_SUCCESS}; font-size: {fonts['small']['size']}px;">
                            <strong>TXD</strong> - Texture dictionaries
                        </li>
                        <li style="margin-bottom: {spacing['small']}px; padding: {spacing['small']}px {spacing['medium']}px; background-color: {ModernDarkTheme.BACKGROUND_TERTIARY}; border-radius: 4px; border-left: 3px solid {ModernDarkTheme.TEXT_WARNING}; font-size: {fonts['small']['size']}px;">
                            <strong>COL</strong> - Collision data
                        </li>
                        <li style="margin-bottom: {spacing['small']}px; padding: {spacing['small']}px {spacing['medium']}px; background-color: {ModernDarkTheme.BACKGROUND_TERTIARY}; border-radius: 4px; border-left: 3px solid {ModernDarkTheme.TEXT_ERROR}; font-size: {fonts['small']['size']}px;">
                            <strong>IFP</strong> - Animation files
                        </li>
                        <li style="margin-bottom: {spacing['small']}px; padding: {spacing['small']}px {spacing['medium']}px; background-color: {ModernDarkTheme.BACKGROUND_TERTIARY}; border-radius: 4px; border-left: 3px solid {ModernDarkTheme.TEXT_ACCENT}; font-size: {fonts['small']['size']}px;">
                            <strong>IDE</strong> - Item definition files
                        </li>
                        <li style="padding: {spacing['small']}px {spacing['medium']}px; background-color: {ModernDarkTheme.BACKGROUND_TERTIARY}; border-radius: 4px; border-left: 3px solid {ModernDarkTheme.TEXT_SUCCESS}; font-size: {fonts['small']['size']}px;">
                            <strong>IPL</strong> - Item placement files
                        </li>
                    </ul>
                </div>
            </div>
            
            <div style="background-color: {ModernDarkTheme.BACKGROUND_SECONDARY}; padding: {spacing['large']}px; border-radius: 8px; border-left: 4px solid {ModernDarkTheme.TEXT_ACCENT}; margin-bottom: {spacing['xlarge']}px;">
                <h3 style="color: {ModernDarkTheme.TEXT_SUCCESS}; margin-bottom: {spacing['medium']}px; font-size: {fonts['subheader']['size']}px;">🚀 Getting Started</h3>
                <ol style="color: {ModernDarkTheme.TEXT_SECONDARY}; line-height: 1.6; font-size: {body_size}px;">
                    <li><strong>Select your target game</strong> from the tools panel on the left</li>
                    <li><strong>Choose the appropriate tool</strong> for your modding task</li>
                    <li><strong>Load your game files</strong> and start creating amazing mods!</li>
                </ol>
            </div>
            
            <div style="text-align: center; margin-top: {spacing['xlarge'] * 2}px;">
                <p style="color: {ModernDarkTheme.TEXT_ACCENT}; font-size: {subtitle_size}px; font-style: italic;">
                    🌟 Ready to bring your creative vision to the streets of Liberty City, Vice City, and San Andreas! 🌟
                </p>
                <div style="margin-top: {spacing['large']}px; padding: {spacing['medium']}px; background-color: {ModernDarkTheme.BACKGROUND_TERTIARY}; border-radius: 8px;">
                    <p style="color: {ModernDarkTheme.TEXT_WARNING}; font-size: {fonts['small']['size']}px; margin: 0;">
                        ⚠️ Development Status: Frontend Complete | Backend Placeholder | File Parsers In Progress
                    </p>
                </div>
            </div>
        </div>
        """
