"""
TXD Editor Tool module for the GTA Renderware Modding Suite
Provides the TXDEditorTool UI for managing TXD texture dictionaries with tabs.
"""

from pathlib import Path
import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QSizePolicy,
    QTabWidget,
    QFrame,
    QScrollArea,
    QGroupBox,
    QGridLayout,
    QPushButton,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLineEdit,
    QComboBox,
    QFileDialog,
    QDialog,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
)

from application.common.message_box import message_box
from application.responsive_utils import get_responsive_manager
from application.styles import ModernDarkTheme
from application.debug_system import get_debug_logger, LogCategory

# Import TXD parser
from application.common.txd import txd

# Module-level debug logger
debug_logger = get_debug_logger()


class TXDEditorTool(QWidget):
    """TXD Editor tool interface with multi-TXD tab support"""

    # Signals for tool actions
    tool_action = pyqtSignal(str, str)  # action_name, parameters
    txd_switched = pyqtSignal(object)  # Signal when active TXD changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_txd_tab = None
        self.txd_files = {}  # Dictionary to store loaded TXD files

        self.setup_ui()

    def setup_ui(self):
        """Setup the main UI layout"""
        rm = get_responsive_manager()
        spacing = rm.get_spacing_config()

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(spacing['medium'])

        # Create toolbar
        self.create_toolbar()
        main_layout.addWidget(self.toolbar)

        # Create main splitter (remove the info panel, just use tabs area)
        self.tabs_widget = QTabWidget()
        self.tabs_widget.setTabsClosable(True)
        self.tabs_widget.tabCloseRequested.connect(self.close_txd_tab)
        self.tabs_widget.currentChanged.connect(self.on_tab_changed)
        
        main_layout.addWidget(self.tabs_widget)

        # Apply styling
        self.apply_styling()

    def create_toolbar(self):
        """Create the toolbar with basic actions"""
        self.toolbar = QFrame()
        self.toolbar.setFixedHeight(40)  # Set fixed height to keep it compact
        self.toolbar.setFrameStyle(QFrame.Shape.StyledPanel)
        
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(8, 4, 8, 4)  # Reduced margins
        toolbar_layout.setSpacing(8)  # Reduced spacing between buttons

        # Open TXD button
        self.open_btn = QPushButton("📁 Open TXD")
        self.open_btn.setFixedHeight(28)  # Fixed button height
        self.open_btn.setMinimumWidth(100)
        self.open_btn.clicked.connect(self.open_txd_file)
        toolbar_layout.addWidget(self.open_btn)

        # Close TXD button
        self.close_btn = QPushButton("❌ Close TXD")
        self.close_btn.setFixedHeight(28)  # Fixed button height
        self.close_btn.setMinimumWidth(100)
        self.close_btn.clicked.connect(self.close_current_txd)
        self.close_btn.setEnabled(False)
        toolbar_layout.addWidget(self.close_btn)

        # TXD Info button
        self.info_btn = QPushButton("📋 TXD Info")
        self.info_btn.setFixedHeight(28)  # Fixed button height
        self.info_btn.setMinimumWidth(100)
        self.info_btn.clicked.connect(self.show_txd_info_dialog)
        self.info_btn.setEnabled(False)
        toolbar_layout.addWidget(self.info_btn)

        # Add stretch to push buttons to the left
        toolbar_layout.addStretch()

    def create_tabs_area(self):
        """Create the tabs area for TXD files"""
        self.tabs_widget = QTabWidget()
        self.tabs_widget.setTabsClosable(True)
        self.tabs_widget.tabCloseRequested.connect(self.close_txd_tab)
        self.tabs_widget.currentChanged.connect(self.on_tab_changed)

    def show_txd_info_dialog(self):
        """Show TXD file information in a popup dialog"""
        if not self.current_txd_tab:
            message_box.warning("No TXD file is currently open.", "No TXD Open", self)
            return

        # Get TXD info from current tab
        txd_info = self.current_txd_tab.get_txd_info()
        if not txd_info:
            message_box.error("Unable to retrieve TXD information.", "Error", self)
            return

        # Create and show info dialog
        dialog = TXDInfoDialog(txd_info, self.current_txd_tab.file_path, self)
        dialog.exec()

    def apply_styling(self):
        """Apply modern dark theme styling"""
        theme = ModernDarkTheme()
        self.setStyleSheet(theme.get_main_stylesheet())

    def open_txd_file(self):
        """Open a TXD file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open TXD File",
            "",
            "TXD Files (*.txd);;All Files (*)"
        )

        if file_path:
            self.load_txd_file(file_path)

    def load_txd_file(self, file_path):
        """Load a TXD file and create a new tab"""
        try:
            # Check if file is already open
            if file_path in self.txd_files:
                # Switch to existing tab
                for i in range(self.tabs_widget.count()):
                    tab = self.tabs_widget.widget(i)
                    if hasattr(tab, 'file_path') and tab.file_path == file_path:
                        self.tabs_widget.setCurrentIndex(i)
                        return

            # Load the TXD file
            txd_parser = txd()
            txd_parser.load_file(file_path)

            # Debug: Log TXD info after loading
            debug_logger.info(LogCategory.UI, f"TXD loaded - RW Version: {getattr(txd_parser, 'rw_version', 'None')}, Device ID: {getattr(txd_parser, 'device_id', 'None')}")

            # Create a new tab for this TXD
            tab = TXDArchiveTab(txd_parser, file_path, self)
            tab_name = os.path.basename(file_path)

            # Add tab to widget
            tab_index = self.tabs_widget.addTab(tab, tab_name)
            self.tabs_widget.setCurrentIndex(tab_index)

            # Store reference
            self.txd_files[file_path] = txd_parser
            self.current_txd_tab = tab

            # Update UI state
            self.close_btn.setEnabled(True)
            self.info_btn.setEnabled(True)

            debug_logger.info(LogCategory.UI, f"Loaded TXD file: {file_path}")

        except Exception as e:
            debug_logger.log_exception(LogCategory.UI, f"Failed to load TXD file: {file_path}", e)
            message_box.error(f"Failed to load TXD file:\n{str(e)}", "Error", self)

    def close_current_txd(self):
        """Close the currently active TXD"""
        current_index = self.tabs_widget.currentIndex()
        if current_index >= 0:
            self.close_txd_tab(current_index)

    def close_txd_tab(self, index):
        """Close a specific TXD tab"""
        if index < 0 or index >= self.tabs_widget.count():
            return

        tab = self.tabs_widget.widget(index)
        if hasattr(tab, 'file_path'):
            # Remove from our tracking
            if tab.file_path in self.txd_files:
                del self.txd_files[tab.file_path]

        # Remove the tab
        self.tabs_widget.removeTab(index)

        # Update current tab reference
        if self.tabs_widget.count() > 0:
            current_tab = self.tabs_widget.currentWidget()
            self.current_txd_tab = current_tab
        else:
            self.current_txd_tab = None
            self.close_btn.setEnabled(False)
            self.info_btn.setEnabled(False)

    def on_tab_changed(self, index):
        """Handle tab change"""
        if index >= 0:
            self.current_txd_tab = self.tabs_widget.widget(index)
        else:
            self.current_txd_tab = None

        self.txd_switched.emit(self.current_txd_tab)

    def update_info_panel(self):
        """Update the information panel with current TXD info"""
        if self.current_txd_tab and hasattr(self.current_txd_tab, 'get_txd_info'):
            info = self.current_txd_tab.get_txd_info()
            self.info_panel.update_info(info)
        else:
            self.info_panel.update_info(None)


class TXDInfoDialog(QDialog):
    """Dialog showing detailed TXD file information with save option"""

    def __init__(self, txd_info, file_path, parent=None):
        super().__init__(parent)
        self.txd_info = txd_info
        self.file_path = file_path
        self.setWindowTitle(f"TXD Information - {os.path.basename(file_path)}")
        self.setModal(True)
        self.resize(500, 600)
        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel(f"📋 TXD File Information")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px; padding: 10px;")
        layout.addWidget(title_label)

        # Scrollable text area for information
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.populate_info_text()
        layout.addWidget(self.info_text)

        # Buttons
        button_layout = QHBoxLayout()
        
        # Save button
        save_btn = QPushButton("💾 Save Info")
        save_btn.clicked.connect(self.save_info)
        button_layout.addWidget(save_btn)
        
        # Close button
        close_btn = QPushButton("❌ Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Apply styling
        self.setStyleSheet(ModernDarkTheme.get_main_stylesheet())

    def populate_info_text(self):
        """Populate the text area with TXD information"""
        info_text = f"""<h2>TXD File Information</h2>
        
<h3>📁 File Details</h3>
<table width="100%" cellpadding="3">
<tr><td><b>File Path:</b></td><td>{self.file_path}</td></tr>
<tr><td><b>File Name:</b></td><td>{self.txd_info.get('file_path', 'Unknown')}</td></tr>
<tr><td><b>File Size:</b></td><td>{self.txd_info.get('file_size', 'Unknown')}</td></tr>
</table>

<h3>🏗️ RenderWare Information</h3>
<table width="100%" cellpadding="3">
<tr><td><b>RW Version:</b></td><td>{self.txd_info.get('rw_version', 'Unknown')}</td></tr>
<tr><td><b>Device ID:</b></td><td>{self.txd_info.get('device_id', 'Unknown')}</td></tr>
<tr><td><b>Platform:</b></td><td>{self.txd_info.get('platform_info', 'Unknown')}</td></tr>
</table>

<h3>🖼️ Texture Statistics</h3>
<table width="100%" cellpadding="3">
<tr><td><b>Total Textures:</b></td><td>{self.txd_info.get('texture_count', 0)} regular + {self.txd_info.get('native_count', 0)} native = {self.txd_info.get('texture_count', 0) + self.txd_info.get('native_count', 0)} total</td></tr>
<tr><td><b>Total Pixels:</b></td><td>{self.txd_info.get('total_pixels', 0):,}</td></tr>
<tr><td><b>Estimated Memory:</b></td><td>{self.txd_info.get('memory_usage', 0)} KB</td></tr>
<tr><td><b>Mipmapped Textures:</b></td><td>{self.txd_info.get('mipmapped_count', 0)}</td></tr>
<tr><td><b>Alpha Textures:</b></td><td>{self.txd_info.get('alpha_count', 0)}</td></tr>
</table>

<h3>🎨 Format Information</h3>
<table width="100%" cellpadding="3">
<tr><td><b>Formats Used:</b></td><td>{self.txd_info.get('formats_used', 'None')}</td></tr>
<tr><td><b>Compression:</b></td><td>{self.txd_info.get('compression_info', 'None')}</td></tr>
</table>
"""
        
        self.info_text.setHtml(info_text)

    def save_info(self):
        """Save TXD information to a text file"""
        try:
            # Generate filename
            base_name = os.path.splitext(os.path.basename(self.file_path))[0]
            default_name = f"{base_name}_info.txt"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save TXD Information",
                default_name,
                "Text Files (*.txt);;All Files (*)"
            )

            if file_path:
                # Generate plain text version
                info_text = f"""TXD File Information
Generated by GTA Renderware Modding Suite

FILE DETAILS
============
File Path: {self.file_path}
File Name: {self.txd_info.get('file_path', 'Unknown')}
File Size: {self.txd_info.get('file_size', 'Unknown')}

RENDERWARE INFORMATION
======================
RW Version: {self.txd_info.get('rw_version', 'Unknown')}
Device ID: {self.txd_info.get('device_id', 'Unknown')}
Platform: {self.txd_info.get('platform_info', 'Unknown')}

TEXTURE STATISTICS
==================
Regular Textures: {self.txd_info.get('texture_count', 0)}
Native Textures: {self.txd_info.get('native_count', 0)}
Total Textures: {self.txd_info.get('texture_count', 0) + self.txd_info.get('native_count', 0)}
Total Pixels: {self.txd_info.get('total_pixels', 0):,}
Estimated Memory Usage: {self.txd_info.get('memory_usage', 0)} KB
Mipmapped Textures: {self.txd_info.get('mipmapped_count', 0)}
Alpha Textures: {self.txd_info.get('alpha_count', 0)}

FORMAT INFORMATION
==================
Formats Used: {self.txd_info.get('formats_used', 'None')}
Compression: {self.txd_info.get('compression_info', 'None')}
"""

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(info_text)
                
                message_box.info(f"TXD information saved successfully to:\n{file_path}", "Save Success", self)

        except Exception as e:
            debug_logger.log_exception(LogCategory.UI, "Failed to save TXD info", e)
            message_box.error(f"Failed to save TXD information:\n{str(e)}", "Save Error", self)


class TXDArchiveTab(QWidget):
    """Individual tab for a TXD archive"""

    # Signals
    texture_selected = pyqtSignal(object)  # Signal when texture is selected

    def __init__(self, txd_parser, file_path, parent=None):
        super().__init__(parent)
        self.txd_parser = txd_parser
        self.file_path = file_path
        self.parent_tool = parent
        self.setup_ui()
        self.update_display()

    def setup_ui(self):
        """Setup UI for individual TXD tab"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)  # Minimal margins
        layout.setSpacing(8)

        # Left side - Texture list with filter
        left_panel = QWidget()
        left_panel.setMinimumWidth(200)  # Reduced width for texture list
        left_panel.setMaximumWidth(250)  # Cap maximum width
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Filter/search area
        self.filter_panel = TXDFilterPanel()
        self.filter_panel.filter_changed.connect(self._on_filter_changed)
        left_layout.addWidget(self.filter_panel)

        # Texture list (simple list instead of table)
        self.texture_list = TXDTextureList()
        self.texture_list.texture_selected.connect(self._on_texture_selected)
        left_layout.addWidget(self.texture_list)

        layout.addWidget(left_panel)

        # Right side - Texture preview
        self.preview_panel = TXDTexturePreview()
        self.preview_panel.setMinimumWidth(500)  # Increased minimum width for preview
        layout.addWidget(self.preview_panel)

        # Set proportions - give much more space to preview
        layout.setStretch(0, 20)  # Texture list gets 20% 
        layout.setStretch(1, 80)  # Preview panel gets 80%

    def update_display(self):
        """Update the display with current TXD data"""
        if not self.txd_parser:
            return

        # Get textures from the parser
        textures = []
        
        # Add native textures
        if hasattr(self.txd_parser, 'native_textures'):
            textures.extend(self.txd_parser.native_textures)
        
        # Add regular textures
        if hasattr(self.txd_parser, 'textures'):
            textures.extend(self.txd_parser.textures)

        # Populate list with textures
        self.texture_list.populate_textures(textures)

    def get_txd_info(self):
        """Get TXD information for display"""
        if not self.txd_parser:
            return None

        # Get file size
        file_size = "Unknown"
        try:
            import os
            if os.path.exists(self.file_path):
                size_bytes = os.path.getsize(self.file_path)
                if size_bytes < 1024:
                    file_size = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    file_size = f"{size_bytes / 1024:.1f} KB"
                else:
                    file_size = f"{size_bytes / (1024 * 1024):.1f} MB"
        except:
            pass

        # Get texture collections
        native_textures = getattr(self.txd_parser, 'native_textures', [])
        regular_textures = getattr(self.txd_parser, 'textures', [])
        all_textures = native_textures + regular_textures

        # Calculate statistics
        total_pixels = 0
        total_memory = 0
        formats_used = set()
        mipmapped_count = 0
        alpha_count = 0
        platform_ids = set()
        compression_types = set()

        for texture in native_textures:
            try:
                # Size calculations - use direct property access
                width = texture.width if hasattr(texture, 'width') else 0
                height = texture.height if hasattr(texture, 'height') else 0
                depth = texture.depth if hasattr(texture, 'depth') else 0
                num_levels = texture.num_levels if hasattr(texture, 'num_levels') else 1
                
                total_pixels += width * height
                
                # Memory estimation (rough calculation)
                bytes_per_pixel = max(depth / 8, 1)
                texture_memory = width * height * bytes_per_pixel
                
                # Add mipmap memory (roughly 1/3 additional)
                if num_levels > 1:
                    texture_memory *= 1.33
                    mipmapped_count += 1
                
                total_memory += texture_memory
                
                # Format information - use parser properties directly
                d3d_format = texture.d3d_format if hasattr(texture, 'd3d_format') else 0
                raster_format = texture.raster_format_flags if hasattr(texture, 'raster_format_flags') else 0
                platform_id = texture.platform_id if hasattr(texture, 'platform_id') else 0
                
                if d3d_format:
                    formats_used.add(f"D3D:{d3d_format}")
                if raster_format:
                    formats_used.add(f"Raster:{raster_format}")
                    
                platform_ids.add(platform_id)
                
                # Check for alpha using parser method
                if hasattr(texture, 'has_alpha') and texture.has_alpha():
                    alpha_count += 1
                
                # Check compression using parser enums
                from application.common.txd import D3DFormat
                try:
                    if d3d_format and D3DFormat(d3d_format) in [D3DFormat.D3D_DXT1, D3DFormat.D3D_DXT2, 
                                                                D3DFormat.D3D_DXT3, D3DFormat.D3D_DXT4, D3DFormat.D3D_DXT5]:
                        compression_types.add("DXT")
                except ValueError:
                    pass
                        
            except Exception as e:
                debug_logger.warning(LogCategory.UI, f"Error analyzing texture: {e}")

        # Platform information
        platform_info = "Unknown"
        if platform_ids:
            from application.common.txd import DeviceType
            platform_names = []
            for pid in platform_ids:
                try:
                    device_type = DeviceType(pid)
                    platform_names.append(device_type.name.replace('DEVICE_', ''))
                except ValueError:
                    platform_names.append(f"Unknown({pid})")
            platform_info = ", ".join(set(platform_names))

        # Compression info
        compression_info = "None"
        if compression_types:
            compression_info = ", ".join(compression_types)

        # Format summary
        formats_summary = "-"
        if formats_used:
            formats_list = list(formats_used)[:3]  # Show first 3 formats
            formats_summary = ", ".join(formats_list)
            if len(formats_used) > 3:
                formats_summary += f" (+{len(formats_used) - 3} more)"

        return {
            'file_path': os.path.basename(self.file_path),
            'file_size': file_size,
            'texture_count': len(regular_textures),
            'native_count': len(native_textures),
            'rw_version': self._format_rw_version(),
            'device_id': self._format_device_id(),
            'total_pixels': total_pixels,
            'memory_usage': int(total_memory / 1024),  # Convert to KB
            'formats_used': formats_summary,
            'mipmapped_count': mipmapped_count,
            'alpha_count': alpha_count,
            'platform_info': platform_info,
            'compression_info': compression_info
        }

    def _format_rw_version(self):
        """Format RW version properly"""
        try:
            rw_version = getattr(self.txd_parser, 'rw_version', None)
            
            # Handle different possible types
            if rw_version is None or rw_version == "":
                return "Unknown"
            elif isinstance(rw_version, str):
                # Try to parse if it's already a string
                if rw_version.startswith('0x'):
                    return rw_version
                try:
                    # Try to convert to int and format
                    version_int = int(rw_version, 16) if 'x' in rw_version else int(rw_version)
                    return f"0x{version_int:X}"
                except:
                    return rw_version
            elif isinstance(rw_version, (int, float)):
                # Format as hex
                version_int = int(rw_version)
                if version_int == 0:
                    return "Unknown"
                return f"0x{version_int:X}"
            else:
                return str(rw_version)
        except Exception as e:
            debug_logger.warning(LogCategory.UI, f"Error formatting RW version: {e}")
            return "Error"

    def _format_device_id(self):
        """Format device ID with descriptive name using TXD parser enums"""
        try:
            from application.common.txd import DeviceType
            device_id = getattr(self.txd_parser, 'device_id', None)
            
            if device_id is None:
                return "Unknown"
            
            try:
                device_type = DeviceType(device_id)
                device_name = device_type.name.replace('DEVICE_', '')
                return f"{device_id} ({device_name})"
            except ValueError:
                return f"{device_id} (Unknown)"
            
        except Exception as e:
            debug_logger.warning(LogCategory.UI, f"Error formatting device ID: {e}")
            return "Error"

    def _on_filter_changed(self, filter_text):
        """Handle filter changes"""
        # TODO: Implement texture filtering
        pass

    def _on_texture_selected(self, texture):
        """Handle texture selection"""
        self.preview_panel.show_texture(texture)
        self.texture_selected.emit(texture)


class TXDFilterPanel(QWidget):
    """Filter panel for TXD textures"""

    filter_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup filter UI"""
        layout = QHBoxLayout(self)

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search textures...")
        self.search_box.textChanged.connect(self.filter_changed.emit)
        layout.addWidget(QLabel("Filter:"))
        layout.addWidget(self.search_box)

        # Filter type combo
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Native", "Regular"])
        layout.addWidget(self.filter_combo)


class TXDTextureList(QWidget):
    """Simple list widget to display TXD texture names"""

    texture_selected = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.textures = []
        self.setup_ui()

    def setup_ui(self):
        """Setup texture list UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Simple label for the list
        self.list_label = QLabel("Textures")
        self.list_label.setStyleSheet(f"""
            QLabel {{
                font-weight: bold;
                color: {ModernDarkTheme.TEXT_PRIMARY};
                padding: 4px;
                background-color: {ModernDarkTheme.BACKGROUND_SECONDARY};
                border: 1px solid {ModernDarkTheme.BORDER_SECONDARY};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(self.list_label)

        # List widget for texture names
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.list_widget.currentRowChanged.connect(self._on_selection_changed)
        
        # Apply styling to match the suite theme
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {ModernDarkTheme.BACKGROUND_PRIMARY};
                color: {ModernDarkTheme.TEXT_PRIMARY};
                border: 1px solid {ModernDarkTheme.BORDER_PRIMARY};
                border-radius: 4px;
                selection-background-color: {ModernDarkTheme.TEXT_ACCENT};
                alternate-background-color: {ModernDarkTheme.BACKGROUND_SECONDARY};
            }}
            QListWidget::item {{
                padding: 6px 8px;
                border-bottom: 1px solid {ModernDarkTheme.BORDER_SECONDARY};
            }}
            QListWidget::item:selected {{
                background-color: {ModernDarkTheme.TEXT_ACCENT};
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: {ModernDarkTheme.HOVER_COLOR};
            }}
        """)

        layout.addWidget(self.list_widget)

    def populate_textures(self, textures):
        """Populate list with texture data"""
        self.textures = textures
        self.list_widget.clear()

        for i, texture in enumerate(textures):
            # Get texture name
            name = getattr(texture, 'name', f'Texture_{i}')
            
            # Create list item
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, texture)
            
            # Add tooltip with additional info
            width = getattr(texture, 'width', 0)
            height = getattr(texture, 'height', 0)
            format_info = self._get_format_info(texture)
            item.setToolTip(f"Name: {name}\nSize: {width}x{height}\nFormat: {format_info}")
            
            self.list_widget.addItem(item)

        # Update label with count
        self.list_label.setText(f"Textures ({len(textures)})")

    def _get_format_info(self, texture):
        """Get format information for texture"""
        if hasattr(texture, 'd3d_format'):
            return f"D3D:{texture.d3d_format}"
        elif hasattr(texture, 'raster_format_flags'):
            return f"Raster:{texture.raster_format_flags}"
        else:
            return "Unknown"

    def _on_selection_changed(self, current_row):
        """Handle selection changes"""
        if current_row >= 0 and current_row < len(self.textures):
            texture = self.textures[current_row]
            self.texture_selected.emit(texture)


class TXDTexturePreview(QWidget):
    """Preview panel for selected texture"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_texture = None
        self.setup_ui()

    def setup_ui(self):
        """Setup preview UI"""
        layout = QVBoxLayout(self)

        # Texture info - compact layout with side-by-side properties
        self.info_group = QGroupBox("Texture Information")
        self.info_group.setMaximumHeight(180)  # Limit height to give more space to preview
        info_layout = QVBoxLayout(self.info_group)

        # Create labels
        self.name_label = QLabel("Name: -")
        self.size_label = QLabel("Size: -")
        self.format_label = QLabel("Format: -")
        self.depth_label = QLabel("Depth: -")
        self.platform_label = QLabel("Platform: -")
        self.mipmaps_label = QLabel("Mip Levels: -")
        self.filter_label = QLabel("Filter Mode: -")
        self.addressing_label = QLabel("UV Addressing: -")
        self.raster_type_label = QLabel("Raster Type: -")
        self.compression_label = QLabel("Compression: -")
        self.alpha_label = QLabel("Has Alpha: -")
        self.palette_label = QLabel("Palette: -")
        self.memory_label = QLabel("Memory Usage: -")
        self.mask_label = QLabel("Mask: -")

        # Grid layout for compact display - 2 columns
        grid_layout = QGridLayout()
        grid_layout.setSpacing(4)  # Compact spacing
        
        # Row 0: Basic info
        grid_layout.addWidget(self.name_label, 0, 0)
        grid_layout.addWidget(self.size_label, 0, 1)
        
        # Row 1: Format and depth
        grid_layout.addWidget(self.format_label, 1, 0)
        grid_layout.addWidget(self.depth_label, 1, 1)
        
        # Row 2: Platform and mipmaps
        grid_layout.addWidget(self.platform_label, 2, 0)
        grid_layout.addWidget(self.mipmaps_label, 2, 1)
        
        # Row 3: Filter and addressing
        grid_layout.addWidget(self.filter_label, 3, 0)
        grid_layout.addWidget(self.addressing_label, 3, 1)
        
        # Row 4: Raster type and compression
        grid_layout.addWidget(self.raster_type_label, 4, 0)
        grid_layout.addWidget(self.compression_label, 4, 1)
        
        # Row 5: Alpha and palette
        grid_layout.addWidget(self.alpha_label, 5, 0)
        grid_layout.addWidget(self.palette_label, 5, 1)
        
        # Row 6: Memory and mask
        grid_layout.addWidget(self.memory_label, 6, 0)
        grid_layout.addWidget(self.mask_label, 6, 1)

        info_layout.addLayout(grid_layout)
        layout.addWidget(self.info_group)

        # Image preview - takes up much more space now
        self.preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(self.preview_group)

        self.image_label = QLabel("No texture selected")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(400)  # Increased from 200 to 400
        self.image_label.setStyleSheet("border: 1px solid gray; background-color: #2b2b2b;")

        preview_layout.addWidget(self.image_label)
        layout.addWidget(self.preview_group)

        # Export button
        self.export_btn = QPushButton("Export Texture")
        self.export_btn.clicked.connect(self.export_texture)
        self.export_btn.setEnabled(False)
        layout.addWidget(self.export_btn)

        # Give much more space to the preview
        layout.setStretch(0, 0)  # Info group - no stretch (fixed height)
        layout.setStretch(1, 1)  # Preview group - takes all available space
        layout.setStretch(2, 0)  # Export button - no stretch

    def show_texture(self, texture):
        """Show texture information and preview"""
        self.current_texture = texture
        
        if not texture:
            self.clear_preview()
            return

        # Update info labels with detailed information - TXD parser guarantees these properties
        name = texture.name
        width = texture.width
        height = texture.height
        depth = texture.depth
        platform_id = texture.platform_id
        num_levels = texture.num_levels
        filter_mode = texture.filter_mode
        uv_addressing = texture.uv_addressing
        raster_type = texture.raster_type
        mask = texture.mask

        self.name_label.setText(f"Name: {name}")
        self.size_label.setText(f"Size: {width} x {height}")
        self.format_label.setText(f"Format: {self._get_format_string(texture)}")
        self.depth_label.setText(f"Depth: {depth} bits")
        
        # Platform information
        platform_name = self._get_platform_name(platform_id)
        self.platform_label.setText(f"Platform: {platform_name}")
        
        # Mipmap info
        mipmap_info = f"{num_levels} level(s)"
        if texture.get_raster_has_mipmaps():
            mipmap_info += " (Auto-generated)"
        self.mipmaps_label.setText(f"Mip Levels: {mipmap_info}")
        
        # Filter mode
        filter_names = {0: "None", 1: "Nearest", 2: "Linear", 3: "Mip Nearest", 
                       4: "Mip Linear", 5: "Linear Mip Nearest", 6: "Linear Mip Linear"}
        filter_name = filter_names.get(filter_mode, f"Unknown ({filter_mode})")
        self.filter_label.setText(f"Filter Mode: {filter_name}")
        
        # UV Addressing
        addressing_names = {1: "Wrap", 2: "Mirror", 3: "Clamp", 4: "Border"}
        addressing_name = addressing_names.get(uv_addressing, f"Unknown ({uv_addressing})")
        self.addressing_label.setText(f"UV Addressing: {addressing_name}")
        
        # Raster type
        raster_names = {0: "Normal", 1: "Z-Buffer", 2: "Camera", 4: "Texture", 5: "Camera Texture"}
        raster_name = raster_names.get(raster_type, f"Unknown ({raster_type})")
        self.raster_type_label.setText(f"Raster Type: {raster_name}")
        
        # Compression info
        compression_info = self._get_compression_info(texture)
        self.compression_label.setText(f"Compression: {compression_info}")
        
        # Alpha info
        has_alpha = "Yes" if texture.has_alpha() else "No"
        self.alpha_label.setText(f"Has Alpha: {has_alpha}")
        
        # Palette info
        palette_info = "None"
        if texture.palette:
            palette_size = len(texture.palette)
            palette_type = texture.get_raster_palette_type()
            palette_info = f"{palette_size} bytes (Type: {palette_type})"
        self.palette_label.setText(f"Palette: {palette_info}")
        
        # Memory usage estimation
        memory_usage = self._calculate_memory_usage(texture)
        self.memory_label.setText(f"Memory Usage: {memory_usage}")
        
        # Mask info
        mask_info = mask if mask else "None"
        self.mask_label.setText(f"Mask: {mask_info}")

        # Try to create preview image
        self._create_preview_image(texture)

        self.export_btn.setEnabled(True)

    def clear_preview(self):
        """Clear the preview"""
        self.name_label.setText("Name: -")
        self.size_label.setText("Size: -")
        self.format_label.setText("Format: -")
        self.depth_label.setText("Depth: -")
        self.platform_label.setText("Platform: -")
        self.mipmaps_label.setText("Mip Levels: -")
        self.filter_label.setText("Filter Mode: -")
        self.addressing_label.setText("UV Addressing: -")
        self.raster_type_label.setText("Raster Type: -")
        self.compression_label.setText("Compression: -")
        self.alpha_label.setText("Has Alpha: -")
        self.palette_label.setText("Palette: -")
        self.memory_label.setText("Memory Usage: -")
        self.mask_label.setText("Mask: -")
        self.image_label.setText("No texture selected")
        self.export_btn.setEnabled(False)

    def _get_format_string(self, texture):
        """Get readable format string using TXD parser enums"""
        from application.common.txd import D3DFormat
        
        format_parts = []
        
        if hasattr(texture, 'd3d_format') and texture.d3d_format:
            # Use the parser's D3DFormat enum names directly
            try:
                format_name = D3DFormat(texture.d3d_format).name
                format_parts.append(format_name)
            except ValueError:
                # Fallback for unknown D3D formats
                format_parts.append(f"D3D:{texture.d3d_format}")
            
        if hasattr(texture, 'raster_format_flags') and texture.raster_format_flags:
            raster_format = texture.raster_format_flags
            format_parts.append(f"Raster:0x{raster_format:X}")
        
        return " | ".join(format_parts) if format_parts else "Unknown"

    def _get_platform_name(self, platform_id):
        """Get platform name from ID using TXD parser enums"""
        from application.common.txd import DeviceType
        platform_names = {
            DeviceType.DEVICE_NONE: "None/Generic",
            DeviceType.DEVICE_D3D8: "D3D8", 
            DeviceType.DEVICE_D3D9: "D3D9",
            DeviceType.DEVICE_GC: "GameCube",
            DeviceType.DEVICE_PS2: "PS2",
            DeviceType.DEVICE_XBOX: "Xbox",
            DeviceType.DEVICE_PSP: "PSP"
        }
        return platform_names.get(platform_id, f"Unknown ({platform_id})")

    def _get_compression_info(self, texture):
        """Get compression information using TXD parser enums"""
        from application.common.txd import D3DFormat
        
        if hasattr(texture, 'd3d_format') and texture.d3d_format:
            try:
                d3d_format = D3DFormat(texture.d3d_format)
                if d3d_format in [D3DFormat.D3D_DXT1, D3DFormat.D3D_DXT2, D3DFormat.D3D_DXT3, 
                                 D3DFormat.D3D_DXT4, D3DFormat.D3D_DXT5]:
                    return d3d_format.name
            except ValueError:
                pass
        
        if hasattr(texture, 'raster_format_flags') and texture.raster_format_flags:
            if texture.raster_format_flags & 0x80:  # DXT compression flag
                return "DXT (Generic)"
        
        return "None"

    def _calculate_memory_usage(self, texture):
        """Calculate estimated memory usage"""
        try:
            width = texture.width
            height = texture.height
            depth = texture.depth
            num_levels = texture.num_levels
            
            if width == 0 or height == 0:
                return "Unknown"
            
            # Basic calculation
            bytes_per_pixel = max(depth / 8, 1)
            base_memory = width * height * bytes_per_pixel
            
            # Add mipmap memory (approximately 1/3 additional for full mipmap chain)
            if num_levels > 1:
                base_memory *= 1.33
            
            # Format in appropriate units
            if base_memory < 1024:
                return f"{int(base_memory)} B"
            elif base_memory < 1024 * 1024:
                return f"{base_memory / 1024:.1f} KB"
            else:
                return f"{base_memory / (1024 * 1024):.1f} MB"
                
        except Exception:
            return "Unknown"

    def _create_preview_image(self, texture):
        """Create and display preview image"""
        try:
            # Ensure texture is valid
            if not texture:
                self.image_label.setText("No texture available")
                return
                
            # Try to get RGBA data from texture using TXD parser method
            rgba_data = texture.to_rgba()
            width = texture.width
            height = texture.height

            if rgba_data and width > 0 and height > 0:
                self._display_rgba_image(rgba_data, width, height)
            else:
                self.image_label.setText("Cannot preview this texture format")

        except Exception as e:
            debug_logger.log_exception(LogCategory.UI, "Failed to create texture preview", e)
            self.image_label.setText("Preview failed")

    def _display_rgba_image(self, rgba_data, width, height):
        """Display RGBA image data"""
        try:
            from PyQt6.QtGui import QImage, QPixmap

            # Create QImage from RGBA data
            image = QImage(rgba_data, width, height, QImage.Format.Format_RGBA8888)
            
            if image.isNull():
                self.image_label.setText("Failed to create image")
                return

            # Convert to pixmap and scale to fit
            pixmap = QPixmap.fromImage(image)
            
            # Scale image to fit label while maintaining aspect ratio
            label_size = self.image_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size.width() - 10,
                label_size.height() - 10,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            self.image_label.setPixmap(scaled_pixmap)

        except Exception as e:
            debug_logger.log_exception(LogCategory.UI, "Failed to display RGBA image", e)
            self.image_label.setText("Display failed")

    def export_texture(self):
        """Export the current texture"""
        if not self.current_texture:
            return

        try:
            # Get export filename
            name = getattr(self.current_texture, 'name', 'texture')
            default_name = f"{name}.png"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Texture",
                default_name,
                "PNG Files (*.png);;All Files (*)"
            )

            if file_path:
                self._export_texture_to_file(file_path)

        except Exception as e:
            debug_logger.log_exception(LogCategory.UI, "Failed to export texture", e)
            message_box.error(f"Failed to export texture:\n{str(e)}", "Export Error", self)

    def _export_texture_to_file(self, file_path):
        """Export texture to file"""
        try:
            if not self.current_texture:
                message_box.error("No texture selected for export", "Export Error", self)
                return
                
            rgba_data = self.current_texture.to_rgba()
            width = self.current_texture.width
            height = self.current_texture.height

            if rgba_data and width > 0 and height > 0:
                from PyQt6.QtGui import QImage

                # Create QImage and save
                image = QImage(rgba_data, width, height, QImage.Format.Format_RGBA8888)
                
                if image.save(file_path):
                    message_box.info(f"Texture exported successfully to:\n{file_path}", "Export Success", self)
                else:
                    message_box.error("Failed to save image file", "Export Error", self)
            else:
                message_box.error("Cannot export this texture format", "Export Error", self)

        except Exception as e:
            debug_logger.log_exception(LogCategory.UI, "Failed to export texture to file", e)
            raise


# Make the main tool class available for import
__all__ = ["TXDEditorTool"]