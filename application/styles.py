"""
Modern dark theme styles for the Renderware Modding Suite
Inspired by VS Code and other modern development environments
"""

class ModernDarkTheme:
    """Color palette for the modern dark theme"""
    
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
    def get_main_stylesheet():
        """Main application stylesheet"""
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
            padding: 4px;
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 6px 12px;
            border-radius: 4px;
            margin: 2px;
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
            padding: 4px;
        }}
        
        QMenu::item {{
            padding: 6px 12px;
            border-radius: 4px;
        }}
        
        QMenu::item:selected {{
            background-color: {ModernDarkTheme.HOVER_COLOR};
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {ModernDarkTheme.BORDER_SECONDARY};
            margin: 4px 8px;
        }}
        
        /* Toolbar Styles */
        QToolBar {{
            background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
            border: none;
            spacing: 4px;
            padding: 6px;
        }}
        
        QToolBar::separator {{
            background-color: {ModernDarkTheme.BORDER_SECONDARY};
            width: 1px;
            margin: 4px 8px;
        }}
        
        /* Button Styles */
        QPushButton {{
            background-color: {ModernDarkTheme.BUTTON_PRIMARY};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: 500;
            min-width: 80px;
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
            font-size: 13px;
        }}
        
        QTreeWidget::item {{
            padding: 6px 4px;
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
            padding: 10px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            min-width: 100px;
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
            margin: 4px;
            padding: 2px;
            width: 16px;
            height: 16px;
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
            font-family: 'Consolas', 'Monaco', 'Cascadia Code', monospace;
            font-size: 14px;
            line-height: 1.4;
            padding: 8px;
        }}
        
        QTextEdit:focus {{
            border-color: {ModernDarkTheme.BORDER_ACCENT};
        }}
        
        /* Scrollbar Styles */
        QScrollBar:vertical {{
            background-color: {ModernDarkTheme.BACKGROUND_SECONDARY};
            width: 12px;
            border: none;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {ModernDarkTheme.BORDER_SECONDARY};
            border-radius: 6px;
            min-height: 20px;
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
            height: 12px;
            border: none;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {ModernDarkTheme.BORDER_SECONDARY};
            border-radius: 6px;
            min-width: 20px;
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
            font-size: 12px;
            padding: 4px;
        }}
        
        /* ComboBox Styles */
        QComboBox {{
            background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
            color: {ModernDarkTheme.TEXT_PRIMARY};
            border: 1px solid {ModernDarkTheme.BORDER_SECONDARY};
            padding: 6px 12px;
            border-radius: 4px;
            min-width: 120px;
        }}
        
        QComboBox:hover {{
            border-color: {ModernDarkTheme.BORDER_ACCENT};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQgNkw4IDEwTDEyIDZINFoiIGZpbGw9IiNjY2NjY2MiLz4KPC9zdmc+);
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
            color: {ModernDarkTheme.TEXT_PRIMARY};
            border: 1px solid {ModernDarkTheme.BORDER_SECONDARY};
            selection-background-color: {ModernDarkTheme.TEXT_ACCENT};
        }}
        
        /* Progress Bar Styles */
        QProgressBar {{
            background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
            border: 1px solid {ModernDarkTheme.BORDER_SECONDARY};
            border-radius: 4px;
            text-align: center;
            color: {ModernDarkTheme.TEXT_PRIMARY};
            height: 20px;
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
            width: 4px;
        }}
        
        QSplitter::handle:vertical {{
            height: 4px;
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
        }}
        
        QLabel#titleLabel {{
            color: {ModernDarkTheme.TEXT_ACCENT};
            font-weight: bold;
            font-size: 14px;
        }}
        
        QLabel#sectionLabel {{
            color: {ModernDarkTheme.TEXT_SUCCESS};
            font-weight: bold;
            font-size: 12px;
            margin: 10px 0 5px 0;
        }}
        """
    
    @staticmethod
    def get_welcome_html():
        """HTML content for the welcome tab"""
        return f"""
        <div style="color: {ModernDarkTheme.TEXT_PRIMARY}; font-size: 14px; padding: 30px; font-family: 'Segoe UI', Arial, sans-serif;">
            <div style="text-align: center; margin-bottom: 40px;">
                <h1 style="color: {ModernDarkTheme.TEXT_ACCENT}; font-size: 32px; margin-bottom: 10px;">
                    ⚡ Renderware Modding Suite
                </h1>
                <p style="color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 16px;">
                    Professional modding tools for 3D era Grand Theft Auto games
                </p>
            </div>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 30px;">
                <div style="flex: 1; margin-right: 20px;">
                    <h3 style="color: {ModernDarkTheme.TEXT_SUCCESS}; margin-bottom: 15px;">🎮 Supported Games</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li style="margin-bottom: 8px; padding: 8px; background-color: {ModernDarkTheme.BACKGROUND_SECONDARY}; border-radius: 4px;">
                            <strong style="color: {ModernDarkTheme.TEXT_ACCENT};">GTA III (2001)</strong><br>
                            <span style="color: {ModernDarkTheme.TEXT_SECONDARY};">Liberty City - Where it all began</span>
                        </li>
                        <li style="margin-bottom: 8px; padding: 8px; background-color: {ModernDarkTheme.BACKGROUND_SECONDARY}; border-radius: 4px;">
                            <strong style="color: {ModernDarkTheme.TEXT_ACCENT};">GTA Vice City (2002)</strong><br>
                            <span style="color: {ModernDarkTheme.TEXT_SECONDARY};">80s Miami nostalgia and neon lights</span>
                        </li>
                        <li style="padding: 8px; background-color: {ModernDarkTheme.BACKGROUND_SECONDARY}; border-radius: 4px;">
                            <strong style="color: {ModernDarkTheme.TEXT_ACCENT};">GTA San Andreas (2004)</strong><br>
                            <span style="color: {ModernDarkTheme.TEXT_SECONDARY};">The biggest adventure across three cities</span>
                        </li>
                    </ul>
                </div>
                
                <div style="flex: 1;">
                    <h3 style="color: {ModernDarkTheme.TEXT_SUCCESS}; margin-bottom: 15px;">📁 Supported Formats</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li style="margin-bottom: 6px; padding: 6px 12px; background-color: {ModernDarkTheme.BACKGROUND_TERTIARY}; border-radius: 4px; border-left: 3px solid {ModernDarkTheme.TEXT_ACCENT};">
                            <strong>DFF</strong> - 3D Models and meshes
                        </li>
                        <li style="margin-bottom: 6px; padding: 6px 12px; background-color: {ModernDarkTheme.BACKGROUND_TERTIARY}; border-radius: 4px; border-left: 3px solid {ModernDarkTheme.TEXT_SUCCESS};">
                            <strong>TXD</strong> - Texture dictionaries
                        </li>
                        <li style="margin-bottom: 6px; padding: 6px 12px; background-color: {ModernDarkTheme.BACKGROUND_TERTIARY}; border-radius: 4px; border-left: 3px solid {ModernDarkTheme.TEXT_WARNING};">
                            <strong>COL</strong> - Collision data
                        </li>
                        <li style="margin-bottom: 6px; padding: 6px 12px; background-color: {ModernDarkTheme.BACKGROUND_TERTIARY}; border-radius: 4px; border-left: 3px solid {ModernDarkTheme.TEXT_ERROR};">
                            <strong>IFP</strong> - Animation files
                        </li>
                        <li style="margin-bottom: 6px; padding: 6px 12px; background-color: {ModernDarkTheme.BACKGROUND_TERTIARY}; border-radius: 4px; border-left: 3px solid {ModernDarkTheme.TEXT_ACCENT};">
                            <strong>IDE</strong> - Item definition files
                        </li>
                        <li style="padding: 6px 12px; background-color: {ModernDarkTheme.BACKGROUND_TERTIARY}; border-radius: 4px; border-left: 3px solid {ModernDarkTheme.TEXT_SUCCESS};">
                            <strong>IPL</strong> - Item placement files
                        </li>
                    </ul>
                </div>
            </div>
            
            <div style="background-color: {ModernDarkTheme.BACKGROUND_SECONDARY}; padding: 20px; border-radius: 8px; border-left: 4px solid {ModernDarkTheme.TEXT_ACCENT}; margin-bottom: 30px;">
                <h3 style="color: {ModernDarkTheme.TEXT_SUCCESS}; margin-bottom: 15px;">🚀 Getting Started</h3>
                <ol style="color: {ModernDarkTheme.TEXT_SECONDARY}; line-height: 1.6;">
                    <li><strong>Select your target game</strong> from the tools panel on the left</li>
                    <li><strong>Choose the appropriate tool</strong> for your modding task</li>
                    <li><strong>Load your game files</strong> and start creating amazing mods!</li>
                </ol>
            </div>
            
            <div style="text-align: center; margin-top: 40px;">
                <p style="color: {ModernDarkTheme.TEXT_ACCENT}; font-size: 18px; font-style: italic;">
                    🌟 Ready to bring your creative vision to the streets of Liberty City, Vice City, and San Andreas! 🌟
                </p>
                <div style="margin-top: 20px; padding: 15px; background-color: {ModernDarkTheme.BACKGROUND_TERTIARY}; border-radius: 8px;">
                    <p style="color: {ModernDarkTheme.TEXT_WARNING}; font-size: 12px; margin: 0;">
                        ⚠️ Development Status: Frontend Complete | Backend Placeholder | File Parsers In Progress
                    </p>
                </div>
            </div>
        </div>
        """
