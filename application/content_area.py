"""
Content Area Widget for Renderware Modding Suite
Main area for displaying file content and tool interfaces
"""

import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTextEdit, QTabWidget, QScrollArea, QGroupBox,
                            QPushButton, QMenu, QTabBar, QToolButton, QTableWidget,
                            QTableWidgetItem, QHeaderView, QSplitter, QTreeWidget,
                            QTreeWidgetItem, QLineEdit, QComboBox, QProgressBar,
                            QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QAction, QIcon
from application.debug_system import get_debug_logger, LogCategory
from application.tools import ToolRegistry


class ContentArea(QWidget):
    """Main content area for displaying files and tools"""
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.debug_logger = get_debug_logger()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Tab widget for multiple content views
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(False)  # Disable built-in close buttons
        self.tab_widget.setMovable(True)  # Allow tab reordering
        self.tab_widget.setUsesScrollButtons(True)  # Show scroll buttons when many tabs
        self.tab_widget.setElideMode(Qt.TextElideMode.ElideRight)  # Elide long tab names
        
        # Ensure close buttons are visible with explicit styling
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                background-color: #1e1e1e;
                border: 1px solid #2d2d30;
            }
            QTabBar::tab {
                background-color: #2d2d30;
                color: #cccccc;
                padding: 10px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #007acc;
                border-bottom: 2px solid #007acc;
            }
            QTabBar::tab:hover {
                background-color: #3e3e42;
            }
            QTabBar::close-button {
                background-color: #666666;
                border: 1px solid #888888;
                border-radius: 8px;
                width: 16px;
                height: 16px;
                margin: 2px;
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                text-align: center;
                subcontrol-position: right;
                subcontrol-origin: padding;
            }
            QTabBar::close-button:hover {
                background-color: #f44747;
                border-color: #f44747;
                color: #ffffff;
            }
            QTabBar::close-button:pressed {
                background-color: #d73a49;
                border-color: #d73a49;
            }
        """)
        
        # Set tooltip for tab widget
        self.tab_widget.setToolTip("Right-click on tabs for more options • Ctrl+W to close • Ctrl+Tab to switch")
        
        # Enable context menu for tabs
        self.tab_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_widget.customContextMenuRequested.connect(self.show_tab_context_menu)
        
        # Welcome tab (default)
        self.welcome_tab = self.create_welcome_tab()
        welcome_tab_index = self.tab_widget.addTab(self.welcome_tab, "🏠 Welcome")
        self.tab_widget.setTabToolTip(welcome_tab_index, "Welcome page - Overview of Renderware Modding Suite")
        
        # Disable close button for Welcome tab specifically
        tab_bar = self.tab_widget.tabBar()
        tab_bar.setTabButton(welcome_tab_index, QTabBar.ButtonPosition.RightSide, None)
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
    
    def create_welcome_tab(self):
        """Create welcome/home tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Welcome message
        welcome_label = QLabel("🎮 Renderware Modding Suite")
        welcome_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #61dafb;
                margin: 20px;
                text-align: center;
            }
        """)
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Subtitle
        subtitle = QLabel("Professional modding tools for GTA 3D era games")
        subtitle.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #888;
                margin-bottom: 30px;
                text-align: center;
            }
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Quick start section
        quick_start = self.create_quick_start_section()
        
        # Supported formats section
        formats_section = self.create_formats_section()
        
        layout.addWidget(welcome_label)
        layout.addWidget(subtitle)
        layout.addWidget(quick_start)
        layout.addWidget(formats_section)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_quick_start_section(self):
        """Create quick start guide section"""
        group = QGroupBox("🚀 Quick Start")
        layout = QVBoxLayout()
        
        steps = [
            "1. Use the File Browser to open a Renderware file (DFF, TXD, COL, etc.)",
            "2. The file will be analyzed and displayed in a new tab",
            "3. Use the Tools Panel to perform modding operations",
            "4. Save your changes or export to different formats"
        ]
        
        for step in steps:
            step_label = QLabel(step)
            step_label.setWordWrap(True)
            step_label.setStyleSheet("margin: 5px; padding: 5px;")
            layout.addWidget(step_label)
        
        group.setLayout(layout)
        return group
    
    def create_formats_section(self):
        """Create supported formats section"""
        group = QGroupBox("📁 Supported File Formats")
        layout = QVBoxLayout()
        
        formats = [
            ("📦 DFF", "3D Models - Game objects, vehicles, characters"),
            ("🖼️ TXD", "Texture Dictionaries - Game textures and materials"),
            ("💥 COL", "Collision Files - Physics collision meshes"),
            ("🏃 IFP", "Animation Files - Character and object animations"),
            ("📋 IDE", "Item Definition - Object properties and metadata"),
            ("📍 IPL", "Item Placement - Object positions in game world")
        ]
        
        for format_name, description in formats:
            format_label = QLabel(f"{format_name}: {description}")
            format_label.setWordWrap(True)
            format_label.setStyleSheet("margin: 3px; padding: 3px;")
            layout.addWidget(format_label)
        
        group.setLayout(layout)
        return group
    
    def add_custom_close_button(self, tab_index):
        """Add a custom close button to a tab"""
        close_button = QToolButton()
        close_button.setText("×")
        close_button.setFixedSize(20, 20)
        close_button.setStyleSheet("""
            QToolButton {
                background-color: transparent;
                border: none;
                color: #cccccc;
                font-size: 16px;
                font-weight: bold;
                border-radius: 10px;
            }
            QToolButton:hover {
                background-color: #f44747;
                color: #ffffff;
            }
            QToolButton:pressed {
                background-color: #d73a49;
            }
        """)
        close_button.setToolTip("Close tab")
        
        # Use QTimer.singleShot to defer the close operation and avoid crashes
        def safe_close():
            QTimer.singleShot(0, lambda: self.close_tab(tab_index))
        
        close_button.clicked.connect(safe_close)
        
        # Set the custom close button
        tab_bar = self.tab_widget.tabBar()
        tab_bar.setTabButton(tab_index, QTabBar.ButtonPosition.RightSide, close_button)
        
        return close_button
    
    def load_file(self, file_path):
        """Load and display a file in a new tab"""
        if not os.path.exists(file_path):
            self.show_error(f"File not found: {file_path}")
            return

        file_name = os.path.basename(file_path)
        
        # Check if file is already open in a tab
        for i in range(self.tab_widget.count()):
            tab_tooltip = self.tab_widget.tabToolTip(i)
            if tab_tooltip.startswith(file_path):
                # File already open, just switch to it
                self.tab_widget.setCurrentIndex(i)
                return

        # Create a simple file viewer widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # Add file info
        file_info_label = QLabel(f"File: {file_path}")
        file_info_label.setWordWrap(True)
        layout.addWidget(file_info_label)
        
        # Add text editor for viewing file content
        text_editor = QTextEdit()
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            text_editor.setPlainText(content)
        except Exception as e:
            text_editor.setPlainText(f"Cannot display file content: {str(e)}\nBinary file or encoding not supported.")
        text_editor.setReadOnly(True)
        layout.addWidget(text_editor)
        
        # Use a generic file icon
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext in ['.dff', '.txd', '.col', '.ifp', '.ide', '.ipl']:
            icon_text = "📄"  # Document icon for known formats
        else:
            icon_text = "📄"  # Generic file icon
            
        tab_title = f"{icon_text} {file_name}"

        # Add tab with tooltip and custom close button
        tab_index = self.tab_widget.addTab(content_widget, tab_title)
        self.tab_widget.setTabToolTip(tab_index, f"{file_path}\nRight-click for options • Ctrl+W to close")
        
        # Add custom close button to make it visible
        self.add_custom_close_button(tab_index)
        
        self.tab_widget.setCurrentIndex(tab_index)

        self.current_file = file_path
    
    def show_tool_interface(self, tool_name, params=None):
        """Show interface for a specific tool"""
        if params is None:
            params = {}
        
        tab_title = f"🔧 {tool_name.replace('_', ' ').title()}"
        
        # Check if tool tab already exists
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == tab_title:
                # Tool tab already exists, switch to it and load new file if specified
                self.tab_widget.setCurrentIndex(i)
                
                # If we have a file to load, load it in the existing tool
                if params.get('file_path') and params.get('auto_load'):
                    existing_widget = self.tab_widget.widget(i)
                    if hasattr(existing_widget, 'load_file'):
                        existing_widget.load_file(params['file_path'])
                
                return
        
        # Create new tool interface widget
        tool_widget = self.create_tool_interface(tool_name, params)
        
        # Add tab and switch to it
        tab_index = self.tab_widget.addTab(tool_widget, tab_title)
        self.tab_widget.setTabToolTip(tab_index, f"{tool_name.replace('_', ' ').title()} Tool\nRight-click for options • Ctrl+W to close")
        
        # Add custom close button to make it visible
        self.add_custom_close_button(tab_index)
        
        self.tab_widget.setCurrentIndex(tab_index)
    
    def create_tool_interface(self, tool_name, params):
        """Create interface for specific tool using modular system"""
        # Check if tool is available in registry
        if ToolRegistry.is_tool_available(tool_name):
            tool_widget = ToolRegistry.create_tool(tool_name, self)
            if tool_widget:
                # Connect tool signals to handle actions
                if hasattr(tool_widget, 'tool_action'):
                    tool_widget.tool_action.connect(self.handle_tool_action)
                
                # Handle auto-loading files if specified in params
                if params.get('file_path') and params.get('auto_load'):
                    if hasattr(tool_widget, 'load_file'):
                        tool_widget.load_file(params['file_path'])
                
                return tool_widget
        
        # Fallback for tools not yet implemented
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Tool header
        tool_info = ToolRegistry.get_tool_info(tool_name)
        if tool_info:
            header_text = f"{tool_info['icon']} {tool_info['name']}"
            description = tool_info['description']
        else:
            header_text = f"🔧 {tool_name.replace('_', ' ').title()}"
            description = "Tool implementation not found"
        
        header_label = QLabel(header_text)
        header_label.setStyleSheet("font-weight: bold; font-size: 16px; padding: 10px;")
        layout.addWidget(header_label)
        
        # Tool content (placeholder)
        content = QTextEdit()
        content.setPlainText(f"""Tool: {tool_name}
Parameters: {params}
Description: {description}

This tool is not yet implemented.
In a complete implementation, this would provide:
- Tool-specific controls and options
- Real-time preview
- Progress indicators
- Result display

This tool will be implemented in a future update.""")
        content.setReadOnly(True)
        layout.addWidget(content)
        
        widget.setLayout(layout)
        return widget
    
    def handle_tool_action(self, action_type, action_data):
        """Handle tool action signals"""
        # Show status message for tool actions
        main_window = self.window()
        if hasattr(main_window, 'status_bar'):
            main_window.status_bar.set_status(f"Tool Action: {action_data}")
    

    def show_error(self, message):
        """Show error message in a new tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        error_label = QLabel("❌ Error")
        error_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #ff6b6b; padding: 10px;")
        layout.addWidget(error_label)
        
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("padding: 10px;")
        layout.addWidget(message_label)
        
        layout.addStretch()
        widget.setLayout(layout)
        
        tab_index = self.tab_widget.addTab(widget, "❌ Error")
        self.tab_widget.setCurrentIndex(tab_index)
    
    def show_tab_context_menu(self, position):
        """Show context menu for tab"""
        # Get the tab that was right-clicked
        tab_bar = self.tab_widget.tabBar()
        tab_index = tab_bar.tabAt(position)
        
        if tab_index < 0:
            return  # No tab at this position
        
        # Create context menu
        context_menu = QMenu(self)
        
        # Close tab action (disabled for welcome tab)
        if tab_index > 0:
            close_action = QAction("Close Tab", self)
            close_action.triggered.connect(lambda: self.close_tab(tab_index))
            context_menu.addAction(close_action)
            
            close_others_action = QAction("Close Other Tabs", self)
            close_others_action.triggered.connect(lambda: self.close_other_tabs(tab_index))
            context_menu.addAction(close_others_action)
            
            context_menu.addSeparator()
        
        # Close all tabs action
        close_all_action = QAction("Close All Tabs", self)
        close_all_action.triggered.connect(self.close_all_tabs_except_welcome)
        context_menu.addAction(close_all_action)
        
        # Reload tab action (if applicable)
        if tab_index > 0:
            context_menu.addSeparator()
            reload_action = QAction("Reload Tab", self)
            reload_action.triggered.connect(lambda: self.reload_tab(tab_index))
            context_menu.addAction(reload_action)
        
        # Show the context menu
        context_menu.exec(self.tab_widget.mapToGlobal(position))
    
    def close_other_tabs(self, keep_index):
        """Close all tabs except the specified one and welcome tab"""
        # Close tabs from right to left to maintain correct indices
        for i in range(self.tab_widget.count() - 1, 0, -1):
            if i != keep_index:
                self.tab_widget.removeTab(i)
        
        if hasattr(self.parent(), 'status_bar'):
            self.parent().status_bar.show_success("Closed other tabs")
    
    def reload_tab(self, tab_index):
        """Reload a specific tab (placeholder for future implementation)"""
        tab_title = self.tab_widget.tabText(tab_index)
        
        if hasattr(self.parent(), 'status_bar'):
            self.parent().status_bar.show_info(f"Reload functionality for '{tab_title}' will be implemented in future versions")
    
    def close_tab(self, index):
        """Close tab by index with proper cleanup"""
        if index <= 0:  # Don't close welcome/home tab
            return
        
        if index >= self.tab_widget.count():
            return
        
        # Get the widget before removing the tab
        widget = self.tab_widget.widget(index)
        
        # Clean up tool resources if it's a tool tab
        if widget and hasattr(widget, 'cleanup'):
            try:
                widget.cleanup()
            except Exception as e:
                self.debug_logger.warning(LogCategory.TOOL, "Error during widget cleanup", {"error": str(e)})
        
        # Remove the tab
        self.tab_widget.removeTab(index)
        
        # Switch to welcome tab if this was the last tab
        if self.tab_widget.count() == 1:
            self.tab_widget.setCurrentIndex(0)
    
    def close_all_tabs_except_welcome(self):
        """Close all tabs except the welcome tab"""
        # Close tabs from right to left to maintain correct indices
        for i in range(self.tab_widget.count() - 1, 0, -1):
            self.tab_widget.removeTab(i)
        
        # Switch to welcome tab
        self.tab_widget.setCurrentIndex(0)
        
        if hasattr(self.parent(), 'status_bar'):
            self.parent().status_bar.show_success("Closed all tabs")
    
    def close_current_tab(self):
        """Close the currently active tab"""
        current_index = self.tab_widget.currentIndex()
        if current_index > 0:  # Don't close welcome tab
            self.close_tab(current_index)
    
    def cleanup_all_tools(self):
        """Clean up all tool resources when the application is shutting down"""
        try:
            self.debug_logger.info(LogCategory.TOOL, "Starting cleanup of all tools in content area...")
            tool_count = 0
            
            # Clean up all tool tabs
            for i in range(self.tab_widget.count()):
                widget = self.tab_widget.widget(i)
                if widget and hasattr(widget, 'cleanup'):
                    try:
                        self.debug_logger.debug(LogCategory.TOOL, "Cleaning up tool tab", {"tab_index": i})
                        widget.cleanup()
                        tool_count += 1
                    except Exception as e:
                        self.debug_logger.warning(LogCategory.TOOL, "Error during tool cleanup", {"error": str(e), "tab_index": i})
            
            self.debug_logger.info(LogCategory.TOOL, "All tool resources cleaned up", {"processed_tools": tool_count})
            
        except Exception as e:
            self.debug_logger.error(LogCategory.TOOL, f"Error during tool cleanup: {e}")
    
    def closeEvent(self, event):
        """Handle close event for the content area"""
        self.debug_logger.info(LogCategory.UI, "Content area closeEvent triggered")
        self.cleanup_all_tools()
        super().closeEvent(event)
