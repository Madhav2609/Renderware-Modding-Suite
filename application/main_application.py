"""
Main Application Class for Renderware Modding Suite
Coordinates all components and manages application state
"""

import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QSplitter, QMenuBar, QMenu, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon

# Import modular components
from styles import ModernDarkTheme
from file_explorer import FileExplorer
from tools_panel import ToolsPanel
from content_area import ContentArea
from status_bar import StatusBarWidget


class RenderwareModdingSuite(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_connections()
        
        # Memory monitoring timer
        self.memory_timer = QTimer()
        self.memory_timer.timeout.connect(self.update_memory_usage)
        self.memory_timer.start(5000)  # Update every 5 seconds
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Renderware Modding Suite - GTA 3D Era Tool")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create horizontal splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel (File Explorer)
        self.file_explorer = FileExplorer()
        self.file_explorer.setMaximumWidth(300)
        self.file_explorer.setMinimumWidth(200)
        
        # Center area (Content)
        self.content_area = ContentArea()
        
        # Right panel (Tools)
        self.tools_panel = ToolsPanel()
        self.tools_panel.setMaximumWidth(300)
        self.tools_panel.setMinimumWidth(200)
        
        # Add panels to splitter
        splitter.addWidget(self.file_explorer)
        splitter.addWidget(self.content_area)
        splitter.addWidget(self.tools_panel)
        
        # Set splitter proportions
        splitter.setSizes([250, 900, 250])
        
        # Status bar
        self.status_bar = StatusBarWidget()
        
        # Add to main layout
        main_layout.addWidget(splitter)
        main_layout.addWidget(self.status_bar)
        
        # Create menu bar after all components are initialized
        self.create_menu_bar()
    
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        open_action = QAction('&Open File...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.file_explorer.browse_files)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('&Tools')
        
        batch_action = QAction('&Batch Converter', self)
        batch_action.triggered.connect(lambda: self.tools_panel.toolRequested.emit("batch_converter", {}))
        tools_menu.addAction(batch_action)
        
        validate_action = QAction('&Validate Files', self)
        validate_action.triggered.connect(lambda: self.tools_panel.toolRequested.emit("file_validator", {}))
        tools_menu.addAction(validate_action)
        
        # Window menu for tab management
        window_menu = menubar.addMenu('&Window')
        
        close_tab_action = QAction('&Close Tab', self)
        close_tab_action.setShortcut('Ctrl+W')
        close_tab_action.triggered.connect(self.content_area.close_current_tab)
        window_menu.addAction(close_tab_action)
        
        close_all_action = QAction('Close &All Tabs', self)
        close_all_action.setShortcut('Ctrl+Shift+W')
        close_all_action.triggered.connect(self.content_area.close_all_tabs_except_welcome)
        window_menu.addAction(close_all_action)
        
        window_menu.addSeparator()
        
        next_tab_action = QAction('&Next Tab', self)
        next_tab_action.setShortcut('Ctrl+Tab')
        next_tab_action.triggered.connect(self.switch_to_next_tab)
        window_menu.addAction(next_tab_action)
        
        prev_tab_action = QAction('&Previous Tab', self)
        prev_tab_action.setShortcut('Ctrl+Shift+Tab')
        prev_tab_action.triggered.connect(self.switch_to_previous_tab)
        window_menu.addAction(prev_tab_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_connections(self):
        """Setup signal connections between components"""
        # File Explorer signals
        self.file_explorer.fileSelected.connect(self.load_file)
        
        # Tools Panel signals
        self.tools_panel.toolRequested.connect(self.handle_tool_request)
    
    def load_file(self, file_path):
        """Load file in content area"""
        self.status_bar.set_status(f"Loading {os.path.basename(file_path)}...")
        self.status_bar.set_file_info(file_path)
        
        try:
            # Load file in content area
            self.content_area.load_file(file_path)
            self.status_bar.show_success(f"Loaded {os.path.basename(file_path)}")
                
        except Exception as e:
            self.status_bar.show_error(f"Error loading file: {str(e)}")
            
            # Still try to show file in UI
            self.content_area.load_file(file_path)
    
    def handle_tool_request(self, tool_name, params):
        """Handle tool request from tools panel"""
        self.status_bar.set_status(f"Opening {tool_name.replace('_', ' ').title()}...")
        
        try:
            # Show tool interface
            self.content_area.show_tool_interface(tool_name, params)
            self.status_bar.show_success(f"Opened {tool_name.replace('_', ' ').title()}")
        
        except Exception as e:
            self.status_bar.show_error(f"Error opening tool: {str(e)}")
    
    def switch_to_next_tab(self):
        """Switch to the next tab"""
        current_index = self.content_area.tab_widget.currentIndex()
        tab_count = self.content_area.tab_widget.count()
        
        if tab_count > 1:  # Only switch if there are multiple tabs
            next_index = (current_index + 1) % tab_count
            self.content_area.tab_widget.setCurrentIndex(next_index)
    
    def switch_to_previous_tab(self):
        """Switch to the previous tab"""
        current_index = self.content_area.tab_widget.currentIndex()
        tab_count = self.content_area.tab_widget.count()
        
        if tab_count > 1:  # Only switch if there are multiple tabs
            prev_index = (current_index - 1) % tab_count
            self.content_area.tab_widget.setCurrentIndex(prev_index)
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Renderware Modding Suite",
            """<h3>Renderware Modding Suite</h3>
            <p>Professional modding tools for GTA 3D era games</p>
            <p><b>Supported Games:</b><br>
            • Grand Theft Auto III<br>
            • Grand Theft Auto: Vice City<br>
            • Grand Theft Auto: San Andreas</p>
            
            <p><b>Supported Formats:</b><br>
            • DFF (3D Models)<br>
            • TXD (Textures)<br>
            • COL (Collision)<br>
            • IFP (Animations)<br>
            • IDE (Definitions)<br>
            • IPL (Placements)</p>
            
            <p><b>Version:</b> 1.0<br>
            <b>Frontend:</b> PyQt6</p>"""
        )
    
    def update_memory_usage(self):
        """Update memory usage display"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.status_bar.set_memory_usage(memory_mb)
        except ImportError:
            # psutil not available
            print("Warning: psutil module not available. Memory usage monitoring disabled.")
            self.memory_timer.stop()  # Stop the timer to avoid repeated import attempts
        except Exception as e:
            # Any other error
            print(f"Error in memory monitoring: {str(e)}")
            self.memory_timer.stop()  # Stop the timer to prevent repeated errors
    
    def closeEvent(self, event):
        """Handle application close event"""
        self.status_bar.set_status("Shutting down...")
        event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Apply modern dark theme
    theme = ModernDarkTheme()
    app.setStyleSheet(theme.get_main_stylesheet())
    
    # Create and show main window
    window = RenderwareModdingSuite()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
