"""
Main Application Class for Renderware Modding Suite
Coordinates all components and manages application state
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QSplitter, QMenuBar, QMenu, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon, QFont, QPalette, QColor

# Import modular components
from application.styles import ModernDarkTheme
from application.file_explorer import FileExplorer
from application.tools_panel import ToolsPanel
from application.content_area import ContentArea
from application.status_bar import StatusBarWidget
from application.responsive_utils import get_responsive_manager
from application.debug_system import get_debug_logger, LogLevel, LogCategory, debug_function


class RenderwareModdingSuite(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize debug logger
        self.debug_logger = get_debug_logger()
        self.debug_logger.info(LogCategory.SYSTEM, "Initializing Renderware Modding Suite")
        
        # Start application setup timer
        setup_timer = self.debug_logger.start_performance_timer("Application Initialization")
        
        self.setup_ui()
        self.setup_connections()
        
        # End setup timer
        self.debug_logger.end_performance_timer(setup_timer)
        
        # Memory monitoring timer
        self.memory_timer = QTimer()
        self.memory_timer.timeout.connect(self.update_memory_usage)
        self.memory_timer.start(5000)  # Update every 5 seconds
        
        self.debug_logger.info(LogCategory.SYSTEM, "Application initialization completed")
    
    
    def setup_ui(self):
        """Setup the user interface with responsive sizing"""
        self.debug_logger.debug(LogCategory.UI, "Setting up main UI")
        
        rm = get_responsive_manager()
        
        # Set responsive window size and title
        window_size = rm.get_window_size()
        self.setWindowTitle("Renderware Modding Suite - GTA 3D Era Tool")
        self.setGeometry(100, 100, window_size[0], window_size[1])
        
        self.debug_logger.info(LogCategory.UI, "Window configured", {
            "size": f"{window_size[0]}x{window_size[1]}",
            "breakpoint": rm.breakpoint
        })
        
        # Print debug info for development
        rm.print_debug_info()
        
        # Set application icon
        self.set_window_icon()
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Get responsive margins
        margins = rm.get_content_margins()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(margins[0], margins[1], margins[2], margins[3])
        
        # Create horizontal splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Get panel widths
        panel_min, panel_max = rm.get_panel_width()
        
        # Left panel (File Explorer)
        self.debug_logger.debug(LogCategory.UI, "Creating File Explorer panel")
        self.file_explorer = FileExplorer()
        self.file_explorer.setMaximumWidth(panel_max)
        self.file_explorer.setMinimumWidth(panel_min)
        
        # Center area (Content)
        self.debug_logger.debug(LogCategory.UI, "Creating Content Area")
        self.content_area = ContentArea()
        
        # Right panel (Tools)
        self.debug_logger.debug(LogCategory.UI, "Creating Tools panel")
        self.tools_panel = ToolsPanel()
        self.tools_panel.setMaximumWidth(panel_max)
        self.tools_panel.setMinimumWidth(panel_min)
        
        # Add panels to splitter
        splitter.addWidget(self.file_explorer)
        splitter.addWidget(self.content_area)
        splitter.addWidget(self.tools_panel)
        
        # Set responsive splitter proportions based on screen size
        if rm.breakpoint == "small":
            # On small screens, give more space to content
            splitter.setSizes([panel_min, window_size[0] - (2 * panel_min), panel_min])
        else:
            # On larger screens, use balanced proportions
            content_width = window_size[0] - (2 * panel_max)
            splitter.setSizes([panel_max, content_width, panel_max])
        
        # Status bar
        self.status_bar = StatusBarWidget()
        
        # Add to main layout
        main_layout.addWidget(splitter)
        main_layout.addWidget(self.status_bar)
        
        # Create menu bar after all components are initialized
        self.create_menu_bar()
    
    def set_window_icon(self):
        """Set the application window icon"""
        try:
            # Try to find icon in different possible locations
            possible_paths = [
                # When running as executable
                os.path.join(os.path.dirname(sys.executable), "icon.ico"),
                # When running from source
                os.path.join(os.path.dirname(__file__), "..", "icon.ico"),
                # Alternative source location
                os.path.join(os.path.dirname(__file__), "..", "..", "icon.ico"),
                # Current working directory
                "icon.ico"
            ]
            
            icon_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    icon_path = path
                    break
            
            if icon_path:
                icon = QIcon(icon_path)
                if not icon.isNull():
                    self.setWindowIcon(icon)
                    self.debug_logger.info(LogCategory.UI, f"Application icon loaded", {"icon_path": icon_path})
                else:
                    self.debug_logger.warning(LogCategory.UI, "Icon file found but couldn't be loaded", {"icon_path": icon_path})
            else:
                self.debug_logger.warning(LogCategory.UI, "Icon file not found in any expected location")
                
        except Exception as e:
            self.debug_logger.error(LogCategory.UI, f"Error setting window icon: {e}")
    
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
        
        window_menu.addSeparator()
        
        # UI Scale options
        zoom_in_action = QAction('Zoom &In', self)
        zoom_in_action.setShortcut('Ctrl++')
        zoom_in_action.triggered.connect(self.zoom_in)
        window_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction('Zoom &Out', self)
        zoom_out_action.setShortcut('Ctrl+-')
        zoom_out_action.triggered.connect(self.zoom_out)
        window_menu.addAction(zoom_out_action)
        
        reset_zoom_action = QAction('&Reset Zoom', self)
        reset_zoom_action.setShortcut('Ctrl+0')
        reset_zoom_action.triggered.connect(self.reset_zoom)
        window_menu.addAction(reset_zoom_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_connections(self):
        """Setup signal connections between components"""
        # File Explorer signals
        self.file_explorer.fileSelected.connect(self.load_file)
        self.file_explorer.openInTool.connect(self.handle_tool_request)
        
        # Tools Panel signals
        self.tools_panel.toolRequested.connect(self.handle_tool_request)
    
    def load_file(self, file_path):
        """Load file in content area"""
        self.debug_logger.log_user_action("Load File", {"file_path": file_path})
        
        load_timer = self.debug_logger.start_performance_timer(f"Load File: {os.path.basename(file_path)}")
        
        self.status_bar.set_status(f"Loading {os.path.basename(file_path)}...")
        self.status_bar.set_file_info(file_path)
        
        try:
            # Load file in content area
            self.content_area.load_file(file_path)
            self.status_bar.show_success(f"Loaded {os.path.basename(file_path)}")
            
            self.debug_logger.log_file_operation("load", file_path, True, {
                "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
            })
                
        except Exception as e:
            self.debug_logger.log_exception(LogCategory.FILE_IO, f"Failed to load file: {file_path}", e)
            self.status_bar.show_error(f"Error loading file: {str(e)}")
            
            # Still try to show file in UI
            self.content_area.load_file(file_path)
        
        finally:
            self.debug_logger.end_performance_timer(load_timer)
    
    def handle_tool_request(self, tool_name, params):
        """Handle tool request from tools panel"""
        self.debug_logger.log_user_action("Open Tool", {"tool_name": tool_name, "params": params})
        
        tool_timer = self.debug_logger.start_performance_timer(f"Open Tool: {tool_name}")
        
        self.status_bar.set_status(f"Opening {tool_name.replace('_', ' ').title()}...")
        
        try:
            # Show tool interface
            self.content_area.show_tool_interface(tool_name, params)
            self.status_bar.show_success(f"Opened {tool_name.replace('_', ' ').title()}")
            
            self.debug_logger.log_tool_operation(tool_name, "opened", params)
        
        except Exception as e:
            self.debug_logger.log_exception(LogCategory.TOOL, f"Failed to open tool: {tool_name}", e)
            self.status_bar.show_error(f"Error opening tool: {str(e)}")
        
        finally:
            self.debug_logger.end_performance_timer(tool_timer)
    
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
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            # Log memory usage to debug system
            self.debug_logger.log_memory_usage("Main Application", memory_mb)
            
            # Update status bar with memory usage - pass the float value directly
            if hasattr(self, 'status_bar'):
                self.status_bar.set_memory_usage(memory_mb)
                
        except ImportError:
            # psutil not available, skip memory monitoring
            pass
        except Exception as e:
            self.debug_logger.error(LogCategory.MEMORY, f"Error updating memory usage: {e}")
    def closeEvent(self, event):
        """Handle application close event to ensure proper cleanup"""
        try:
            self.debug_logger.info(LogCategory.SYSTEM, "Application shutting down - cleaning up resources")
            
            # Clean up content area (which includes all tool tabs)
            if hasattr(self, 'content_area'):
                self.content_area.cleanup_all_tools()
            
            # Stop memory monitoring timer
            if hasattr(self, 'memory_timer'):
                self.memory_timer.stop()
            
            self.debug_logger.info(LogCategory.SYSTEM, "Application cleanup completed")
            
        except Exception as e:
            self.debug_logger.log_exception(LogCategory.SYSTEM, "Error during application cleanup", e)
        
        # Accept the close event
        event.accept()
    
    def aboutToQuit(self):
        """Handle application quit event"""
        try:
            self.debug_logger.info(LogCategory.SYSTEM, "Application about to quit - final cleanup...")
            
            # Force cleanup of all resources
            if hasattr(self, 'content_area'):
                self.content_area.cleanup_all_tools()
            
            self.debug_logger.info(LogCategory.SYSTEM, "Final cleanup completed")
            
        except Exception as e:
            self.debug_logger.error(LogCategory.SYSTEM, f"Error during final cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup when the application is destroyed"""
        try:
            # Using logger may not always be safe during interpreter shutdown, but attempt it
            if hasattr(self, 'debug_logger'):
                self.debug_logger.info(LogCategory.SYSTEM, "Main application destructor called - cleaning up...")
            
            # Force cleanup of all resources
            if hasattr(self, 'content_area'):
                self.content_area.cleanup_all_tools()
            
            if hasattr(self, 'debug_logger'):
                self.debug_logger.info(LogCategory.SYSTEM, "Main application cleanup completed")
            
        except Exception as e:
            if hasattr(self, 'debug_logger'):
                self.debug_logger.error(LogCategory.SYSTEM, f"Error in main application destructor: {e}")
    
    def zoom_in(self):
        """Increase UI scale"""
        rm = get_responsive_manager()
        rm.scale_factor = min(2.0, rm.scale_factor * 1.1)
        self.refresh_ui_scaling()
        self.status_bar.show_success(f"Zoom increased to {rm.scale_factor:.1f}x")
    
    def zoom_out(self):
        """Decrease UI scale"""
        rm = get_responsive_manager()
        rm.scale_factor = max(0.5, rm.scale_factor * 0.9)
        self.refresh_ui_scaling()
        self.status_bar.show_success(f"Zoom decreased to {rm.scale_factor:.1f}x")
    
    def reset_zoom(self):
        """Reset UI scale to default"""
        rm = get_responsive_manager()
        rm.scale_factor = rm._calculate_scale_factor()  # Reset to calculated default
        self.refresh_ui_scaling()
        self.status_bar.show_success(f"Zoom reset to {rm.scale_factor:.1f}x")
    
    def refresh_ui_scaling(self):
        """Refresh the UI with new scaling"""
        try:
            # Reapply the stylesheet with new scaling
            theme = ModernDarkTheme()
            QApplication.instance().setStyleSheet(theme.get_main_stylesheet())
            
            # Reapply dark palette to ensure theme consistency
            theme.apply_dark_palette(QApplication.instance())
            
            # Update font
            rm = get_responsive_manager()
            font_config = rm.get_font_config()
            new_font = QFont("Fira Code", font_config['body']['size'])
            QApplication.instance().setFont(new_font)
            
            self.debug_logger.info(LogCategory.UI, "UI refreshed", {"scale_factor": f"{rm.scale_factor:.2f}"})
        except Exception as e:
            self.debug_logger.error(LogCategory.UI, f"Error refreshing UI scaling: {e}")


def main():
    """Main application entry point"""
    # Initialize debug logger early
    debug_logger = get_debug_logger()
    debug_logger.info(LogCategory.SYSTEM, "Starting Renderware Modding Suite")
    
    # Set critical Qt attributes before creating QApplication to force dark theme
    os.environ['QT_FONT_DPI'] = '96'  # Force consistent DPI
    os.environ['QT_SCALE_FACTOR'] = '1'  # Prevent auto-scaling issues
    
    # Force dark theme independent of system theme
    os.environ['QT_QPA_PLATFORM_THEME'] = ''  # Disable system theme integration
    os.environ['QT_STYLE_OVERRIDE'] = 'Fusion'  # Use Fusion as base style
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '0'  # Disable auto-scaling
    
    debug_logger.debug(LogCategory.SYSTEM, "Qt environment variables configured")
    
    # Additional environment variables to prevent system theme interference
    os.environ.pop('QT_QPA_PLATFORMTHEME', None)  # Remove any existing platform theme
    os.environ.pop('QT_QUICK_CONTROLS_STYLE', None)  # Remove quick controls style
    os.environ.pop('QT_QUICK_CONTROLS_MATERIAL_THEME', None)  # Remove material theme
    
    app = QApplication(sys.argv)
    debug_logger.debug(LogCategory.SYSTEM, "QApplication created")
    
    # Set application properties
    app.setApplicationName("Renderware Modding Suite")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("GTA Modding Community")
    debug_logger.info(LogCategory.SYSTEM, "Application properties set")
    
    # Set application icon globally
    try:
        # Try to find icon in different possible locations
        possible_paths = [
            os.path.join(os.path.dirname(sys.executable), "icon.ico") if getattr(sys, 'frozen', False) else None,
            os.path.join(os.path.dirname(__file__), "..", "icon.ico"),
            "icon.ico"
        ]
        
        for path in possible_paths:
            if path and os.path.exists(path):
                app_icon = QIcon(path)
                if not app_icon.isNull():
                    app.setWindowIcon(app_icon)
                    debug_logger.info(LogCategory.UI, "Global application icon set", {"icon_path": path})
                    break
    except Exception as e:
        debug_logger.error(LogCategory.UI, f"Error setting global application icon: {e}")
    
    # Apply modern dark theme
    theme = ModernDarkTheme()
    app.setStyleSheet(theme.get_main_stylesheet())
    
    # Force dark palette to override any system theme interference
    theme.apply_dark_palette(app)
    debug_logger.info(LogCategory.UI, "Dark theme applied successfully")
    
    # Set responsive font with fallbacks
    try:
        rm = get_responsive_manager()
        font_config = rm.get_font_config()
        
        font_families = ["Fira Code", "Consolas", "Courier New", "monospace"]
        for font_family in font_families:
            professional_font = QFont(font_family, font_config['body']['size'])
            if professional_font.exactMatch():
                app.setFont(professional_font)
                debug_logger.info(LogCategory.UI, "Font set", {"font_family": font_family})
                break
        else:
            professional_font = QFont("monospace", font_config['body']['size'])
            app.setFont(professional_font)
            debug_logger.warning(LogCategory.UI, "Using system default monospace font")
            
    except Exception as e:
        debug_logger.error(LogCategory.UI, f"Error setting font: {e}")
    
    # Create and show main window
    window = RenderwareModdingSuite()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
