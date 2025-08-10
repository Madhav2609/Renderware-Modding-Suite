"""
IMG Editor Tool for Renderware Modding Suite
Handles IMG archive file operations and management
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QGroupBox, QPushButton, QSplitter, QTreeWidget,
                            QTreeWidgetItem, QLineEdit, QComboBox, QProgressBar,
                            QScrollArea, QSizePolicy, QTableWidget, QTableWidgetItem,
                            QHeaderView, QFileDialog, QGridLayout, QTabWidget,
                            QToolButton, QMenu, QFrame)
from PySide6.QtCore import Qt, Signal
from pathlib import Path

from application.common.message_box import message_box
from application.responsive_utils import get_responsive_manager
from application.styles import ModernDarkTheme
from .img_controller import IMGController


class IMGFileInfoPanel(QGroupBox):
    """Panel showing IMG file information"""
    
    def __init__(self, parent=None):
        super().__init__("IMG File Information", parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the UI with responsive sizing"""
        rm = get_responsive_manager()
        fonts = rm.get_font_config()
        spacing = rm.get_spacing_config()
        
        layout = QVBoxLayout(self)
        
        # File info labels
        self.file_path_label = QLabel("Path: Not loaded")
        self.version_label = QLabel("Version: -")
        self.entry_count_label = QLabel("Entries: 0")
        self.total_size_label = QLabel("Total Size: 0 bytes")
        self.modified_label = QLabel("Modified: No")
        
        # RenderWare version summary labels
        self.rw_files_label = QLabel("RenderWare Files: 0")
        self.rw_versions_label = QLabel("RW Versions: None")
        
        # Modification status labels
        self.new_entries_label = QLabel("New Entries: 0")
        self.deleted_entries_label = QLabel("Deleted Entries: 0")
        self.needs_save_label = QLabel("Needs Save: No")
        
        # Add labels to layout
        layout.addWidget(self.file_path_label)
        layout.addWidget(self.version_label)
        layout.addWidget(self.entry_count_label)
        layout.addWidget(self.total_size_label)
        layout.addWidget(self.modified_label)
        layout.addWidget(self.rw_files_label)
        layout.addWidget(self.rw_versions_label)
        layout.addWidget(self.new_entries_label)
        layout.addWidget(self.deleted_entries_label)
        layout.addWidget(self.needs_save_label)
        
        # Apply responsive styling
        self.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {fonts['body']['size']}px;
                padding: {spacing['small']}px;
            }}
        """)
    
    def update_info(self, img_info=None, rw_summary=None, mod_summary=None):
        """Update panel with IMG file information"""
        if not img_info:
            # Reset to default state
            self.file_path_label.setText("Path: Not loaded")
            self.version_label.setText("Version: -")
            self.entry_count_label.setText("Entries: 0")
            self.total_size_label.setText("Total Size: 0 bytes")
            self.modified_label.setText("Modified: No")
            self.rw_files_label.setText("RenderWare Files: 0")
            self.rw_versions_label.setText("RW Versions: None")
            self.new_entries_label.setText("New Entries: 0")
            self.deleted_entries_label.setText("Deleted Entries: 0")
            self.needs_save_label.setText("Needs Save: No")
            return
            
        # Update with provided information
        self.file_path_label.setText(f"Path: {img_info['path']}")
        self.version_label.setText(f"Version: {img_info['version']}")
        self.entry_count_label.setText(f"Entries: {img_info['entry_count']}")
        self.total_size_label.setText(f"Total Size: {img_info['total_size']}")
        self.modified_label.setText(f"Modified: {img_info['modified']}")
        
        # Update RenderWare version summary
        if rw_summary:
            self.rw_files_label.setText(f"RenderWare Files: {rw_summary['renderware_files']}/{rw_summary['total_files']}")
            
            # Show most common RW versions
            version_breakdown = rw_summary.get('version_breakdown', {})
            if version_breakdown:
                # Get top 3 most common versions
                sorted_versions = sorted(version_breakdown.items(), key=lambda x: x[1], reverse=True)[:3]
                versions_text = ", ".join([f"{name} ({count})" for name, count in sorted_versions])
                self.rw_versions_label.setText(f"RW Versions: {versions_text}")
                
                # Set tooltip with full breakdown
                full_breakdown = "\n".join([f"{name}: {count} files" for name, count in sorted_versions])
                self.rw_versions_label.setToolTip(f"RenderWare Version Breakdown:\n{full_breakdown}")
            else:
                self.rw_versions_label.setText("RW Versions: None detected")
        else:
            self.rw_files_label.setText("RenderWare Files: Analyzing...")
            self.rw_versions_label.setText("RW Versions: Analyzing...")
        
        # Update modification status
        if mod_summary:
            self.new_entries_label.setText(f"New Entries: {mod_summary.get('new_entries_count', 0)}")
            self.deleted_entries_label.setText(f"Deleted Entries: {mod_summary.get('deleted_entries_count', 0)}")
            needs_save = "Yes" if mod_summary.get('needs_save', False) else "No"
            self.needs_save_label.setText(f"Needs Save: {needs_save}")
            
            # Color code the needs save label
            if mod_summary.get('needs_save', False):
                self.needs_save_label.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.needs_save_label.setStyleSheet("color: white;")
            
            # Set tooltips for deleted entries
            if mod_summary.get('deleted_entry_names'):
                deleted_names = mod_summary['deleted_entry_names'][:10]  # Show first 10
                tooltip_text = "Deleted entries:\n" + "\n".join(deleted_names)
                if len(mod_summary['deleted_entry_names']) > 10:
                    tooltip_text += f"\n... and {len(mod_summary['deleted_entry_names']) - 10} more"
                self.deleted_entries_label.setToolTip(tooltip_text)
            else:
                self.deleted_entries_label.setToolTip("")
        else:
            self.new_entries_label.setText("New Entries: 0")
            self.deleted_entries_label.setText("Deleted Entries: 0")
            self.needs_save_label.setText("Needs Save: No")
            self.needs_save_label.setStyleSheet("color: white;")



class IMGEntriesTable(QTableWidget):
    """Enhanced table widget for IMG entries"""
    entry_double_clicked = Signal(object)
    entry_selected = Signal(object)
    
    def __init__(self, parent=None):
        """Initialize the table with responsive styling"""
        super().__init__(parent)
        rm = get_responsive_manager()
        fonts = rm.get_font_config()
        spacing = rm.get_spacing_config()
        
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels(['Name', 'Type', 'Size', 'Offset', 'RW Version', 'Streaming', 'Compression'])
        
        # Setup table properties
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        
        # Auto-resize columns to fill the available space
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            
        # Add responsive styling
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {ModernDarkTheme.BACKGROUND_SECONDARY};
                gridline-color: {ModernDarkTheme.BORDER_SECONDARY};
                border: 1px solid {ModernDarkTheme.BORDER_PRIMARY};
                border-radius: 4px;
                font-size: {fonts['body']['size']}px;
            }}
            QTableWidget::item {{
                padding: {spacing['small']}px;
                border-bottom: 1px solid {ModernDarkTheme.BORDER_SECONDARY};
            }}
            QTableWidget::item:selected {{
                background-color: {ModernDarkTheme.TEXT_ACCENT};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
                color: white;
                padding: {spacing['small']}px;
                border: 1px solid {ModernDarkTheme.BORDER_PRIMARY};
                font-weight: bold;
                font-size: {fonts['body']['size']}px;
            }}
        """)
        
        # Connect signals
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.itemSelectionChanged.connect(self._on_selection_changed)
    
    def _on_item_double_clicked(self, item):
        """Handle double-click on entry"""
        row = item.row()
        # Get the entry from the table's row data
        entry = self.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if entry:
            self.entry_double_clicked.emit(entry)
    
    def _on_selection_changed(self):
        """Handle selection change"""
        selected_entries = []
        
        # Get all selected rows
        for index in self.selectedIndexes():
            if index.column() == 0:  # Only count each row once
                entry = self.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)
                if entry:
                    selected_entries.append(entry)
        
        if selected_entries:
            self.entry_selected.emit(selected_entries)
    
    def populate_entries(self, entries):
        """Populate table with entries"""
        self.setRowCount(0)  # Clear the table
        
        if not entries:
            return
            
        # Disable sorting temporarily for better performance
        self.setSortingEnabled(False)
        
        for entry in entries:
            row = self.rowCount()
            self.insertRow(row)
            
            # Set entry data
            name_item = QTableWidgetItem(entry.name)
            name_item.setData(Qt.ItemDataRole.UserRole, entry)  # Store entry object in the item
            
            type_item = QTableWidgetItem(entry.type)
            size_item = QTableWidgetItem(f"{entry.actual_size:,}")
            offset_item = QTableWidgetItem(f"{entry.offset}")
            
            # RenderWare version information
            if hasattr(entry, 'rw_version_name') and entry.rw_version_name:
                rw_version_item = QTableWidgetItem(entry.rw_version_name)
                # Color code based on version type
                if entry.is_renderware_file() and entry.rw_version is not None:
                    rw_version_item.setToolTip(f"RW Version: 0x{entry.rw_version:X}")
                elif entry.rw_version_name and "COL" in entry.rw_version_name:
                    rw_version_item.setToolTip(f"Collision file: {entry.rw_version_name}")
                else:
                    rw_version_item.setToolTip("Not a standard RenderWare file")
            else:
                rw_version_item = QTableWidgetItem("Unknown")
                rw_version_item.setToolTip("Version not analyzed")
            
            # For V2 archives, show streaming size, otherwise show dash
            if hasattr(entry, 'streaming_size') and entry.streaming_size > 0:
                streaming_item = QTableWidgetItem(f"{entry.streaming_size}")
            else:
                streaming_item = QTableWidgetItem("-")
                
            # Compression status
            comp_item = QTableWidgetItem("Yes" if entry.is_compressed else "No")
            
            # Add items to the row
            self.setItem(row, 0, name_item)
            self.setItem(row, 1, type_item)
            self.setItem(row, 2, size_item)
            self.setItem(row, 3, offset_item)
            self.setItem(row, 4, rw_version_item)
            self.setItem(row, 5, streaming_item)
            self.setItem(row, 6, comp_item)
        
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.SortOrder.AscendingOrder)  # Sort by name initially
    
    def apply_filter(self, filter_text=None, filter_type=None, filter_rw_version=None):
        """Apply filter to table entries"""
        for row in range(self.rowCount()):
            show_row = True
            
            name_item = self.item(row, 0)
            type_item = self.item(row, 1)
            rw_version_item = self.item(row, 4)  # RW Version column
            
            # Get the entry object to check RenderWare properties
            entry = name_item.data(Qt.ItemDataRole.UserRole) if name_item else None
            
            # Text filter
            if filter_text and filter_text.lower() not in name_item.text().lower():
                show_row = False
                
            # File type filter
            if filter_type and filter_type != "All" and type_item.text() != filter_type:
                show_row = False
                
            # RenderWare version filter
            if filter_rw_version and entry:
                rw_text = rw_version_item.text() if rw_version_item else ""
                
                if filter_rw_version == "RenderWare Only":
                    if not entry.is_renderware_file():
                        show_row = False
                elif filter_rw_version == "Non-RenderWare":
                    if entry.is_renderware_file():
                        show_row = False
                elif filter_rw_version == "GTA III (3.1.0.1)":
                    if not ("3.1.0.1" in rw_text or "GTA3" in rw_text):
                        show_row = False
                elif filter_rw_version == "Vice City (3.3.0.2)":
                    if not ("3.3.0.2" in rw_text or "Vice City" in rw_text):
                        show_row = False
                elif filter_rw_version == "San Andreas (3.6.0.3)":
                    if not ("3.6.0.3" in rw_text):
                        show_row = False
                elif filter_rw_version == "San Andreas (3.4.0.3)":
                    if not ("3.4.0.3" in rw_text):
                        show_row = False
                elif filter_rw_version == "Liberty City Stories (3.5.0.0)":
                    if not ("3.5.0.0" in rw_text or "Liberty City Stories" in rw_text):
                        show_row = False
                elif filter_rw_version == "Vice City Stories (3.5.0.2)":
                    if not ("3.5.0.2" in rw_text or "Vice City Stories" in rw_text):
                        show_row = False
                elif filter_rw_version == "COL1 (GTA III/VC)":
                    if not ("COL1" in rw_text):
                        show_row = False
                elif filter_rw_version == "COL2 (GTA SA)":
                    if not ("COL2" in rw_text):
                        show_row = False
                elif filter_rw_version == "COL3 (GTA SA Advanced)":
                    if not ("COL3" in rw_text):
                        show_row = False
                elif filter_rw_version == "COL4 (Extended)":
                    if not ("COL4" in rw_text):
                        show_row = False
                
            self.setRowHidden(row, not show_row)


class FilterPanel(QWidget):
    """Filter panel for IMG entries"""
    filter_changed = Signal(str, str, str)  # text_filter, type_filter, rw_version_filter
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(15)

        # File type filter
        type_group = QGroupBox("File Type Filter")
        type_layout = QHBoxLayout(type_group)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(['All', 'DFF', 'TXD', 'COL', 'IFP', 'IPL', 'DAT', 'WAV'])
        self.type_combo.currentTextChanged.connect(self._filter_changed)
        type_layout.addWidget(self.type_combo)
        
        # RenderWare version filter
        rw_group = QGroupBox("RenderWare Version Filter")
        rw_layout = QHBoxLayout(rw_group)
        
        self.rw_version_combo = QComboBox()
        self.rw_version_combo.addItems(['All Versions', 'RenderWare Only', 'Non-RenderWare', 'GTA III (3.1.0.1)', 'Vice City (3.3.0.2)', 'San Andreas (3.6.0.3)', 'San Andreas (3.4.0.3)', 'Liberty City Stories (3.5.0.0)', 'Vice City Stories (3.5.0.2)', 'COL1 (GTA III/VC)', 'COL2 (GTA SA)', 'COL3 (GTA SA Advanced)', 'COL4 (Extended)'])
        self.rw_version_combo.currentTextChanged.connect(self._filter_changed)
        rw_layout.addWidget(self.rw_version_combo)
        
        # Search filter
        search_group = QGroupBox("Search")
        search_layout = QHBoxLayout(search_group)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Search entries...")
        self.search_edit.textChanged.connect(self._filter_changed)
        search_layout.addWidget(self.search_edit)
        
        # Apply responsive styling
        rm = get_responsive_manager()
        fonts = rm.get_font_config()
        spacing = rm.get_spacing_config()
        button_size = rm.get_button_size()
        
        combo_style = f"""
            QComboBox {{
                background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
                color: white;
                border: 1px solid {ModernDarkTheme.BORDER_PRIMARY};
                border-radius: 3px;
                padding: {spacing['small']}px;
                min-width: {button_size[0] - 20}px;
                font-size: {fonts['body']['size']}px;
            }}
            QComboBox:hover {{
                border: 1px solid {ModernDarkTheme.TEXT_ACCENT};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: {spacing['medium'] + 5}px;
                border-left: 1px solid {ModernDarkTheme.BORDER_PRIMARY};
            }}
        """
        self.type_combo.setStyleSheet(combo_style)
        self.rw_version_combo.setStyleSheet(combo_style)
        
        self.search_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
                color: white;
                border: 1px solid {ModernDarkTheme.BORDER_PRIMARY};
                border-radius: 3px;
                padding: {spacing['small']}px;
                font-size: {fonts['body']['size']}px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ModernDarkTheme.TEXT_ACCENT};
            }}
        """)
        
        layout.addWidget(type_group)
        layout.addWidget(rw_group)
        layout.addWidget(search_group)
    
    def _filter_changed(self):
        """Emit signal when filter is changed"""
        filter_text = self.search_edit.text()
        filter_type = self.type_combo.currentText() if self.type_combo.currentText() != "All" else None
        filter_rw_version = self.rw_version_combo.currentText() if self.rw_version_combo.currentText() != "All Versions" else None
        self.filter_changed.emit(filter_text, filter_type, filter_rw_version)


class IMGArchiveTab(QWidget):
    """Individual tab for an IMG archive"""
    
    # Signals
    archive_modified = Signal(str)  # Signal when archive is modified
    entries_selected = Signal(list)  # Signal when entries are selected
    action_requested = Signal(str, object)  # Signal for requesting actions from parent
    
    def __init__(self, img_archive, parent=None):
        super().__init__(parent)
        self.img_archive = img_archive
        self.parent_tool = parent  # Reference to parent ImgEditorTool
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self):
        """Setup UI for individual archive tab"""
        layout = QVBoxLayout(self)
        
        # Filter panel
        self.filter_panel = FilterPanel()
        self.filter_panel.filter_changed.connect(self._on_filter_changed)
        layout.addWidget(self.filter_panel)
        
        # Entries table
        self.entries_table = IMGEntriesTable()
        self.entries_table.entry_double_clicked.connect(self._on_entry_double_clicked)
        self.entries_table.entry_selected.connect(self._on_entry_selected)
        layout.addWidget(self.entries_table)
        
    
    def update_display(self):
        """Update the display with current archive data"""
        if not self.img_archive:
            return
        
        # Populate table with entries
        if hasattr(self.img_archive, 'entries') and self.img_archive.entries:
            self.entries_table.populate_entries(self.img_archive.entries)
    
    def get_archive_info(self):
        """Get archive information for display"""
        if not self.img_archive:
            return None
        
        total_size = sum(entry.actual_size for entry in self.img_archive.entries) if hasattr(self.img_archive, 'entries') else 0
        
        return {
            'path': self.img_archive.file_path or 'Unknown',
            'version': getattr(self.img_archive, 'version', 'Unknown'),
            'entry_count': len(self.img_archive.entries) if hasattr(self.img_archive, 'entries') else 0,
            'total_size': f"{total_size:,} bytes",
            'modified': "Yes" if getattr(self.img_archive, 'modified', False) else "No"
        }
    
    def get_selected_entries(self):
        """Get currently selected entries"""
        selected_entries = []
        
        # Get all selected rows
        for index in self.entries_table.selectedIndexes():
            if index.column() == 0:  # Only count each row once
                entry = self.entries_table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)
                if entry:
                    selected_entries.append(entry)
        
        return selected_entries
    
    def _on_filter_changed(self, filter_text, filter_type, filter_rw_version):
        """Handle filter changes"""
        self.entries_table.apply_filter(filter_text, filter_type, filter_rw_version)
    
    def _on_entry_double_clicked(self, entry):
        """Handle entry double-click"""
        # Implementation for entry preview/edit
        entry_info = f"Name: {entry.name}\n"
        entry_info += f"Size: {entry.actual_size:,} bytes\n"
        entry_info += f"Offset: Sector {entry.offset}"
        message_box.info(entry_info, "Entry Details", self)
    
    def _on_entry_selected(self, entries):
        """Handle entry selection"""
        self.entries_selected.emit(entries)
    
    


class ImgEditorTool(QWidget):
    """IMG Editor tool interface with multi-archive tab support"""
    
    # Signals for tool actions
    tool_action = Signal(str, str)  # action_name, parameters
    archive_switched = Signal(object)  # Signal when active archive changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.img_controller = IMGController()
        self.current_archive_tab = None
        
        # Create compatibility layer for UI interaction handlers
        self.img_editor = self._create_img_editor_adapter()
        
        # Import UI interaction handlers
        self._import_ui_handlers()
        
        # Connect controller signals
        self.img_controller.img_loaded.connect(self._on_img_loaded)
        self.img_controller.img_closed.connect(self._on_img_closed)
        self.img_controller.archive_switched.connect(self._on_archive_switched)
        self.img_controller.entries_updated.connect(self._on_entries_updated_for_tabs)
        
        self.setup_ui()
    
    def _create_img_editor_adapter(self):
        """Create an adapter object that provides the interface expected by UI handlers"""
        class IMGEditorAdapter:
            def __init__(self, tool):
                self.tool = tool
            
            def open_img(self, file_path):
                return self.tool.open_archive(file_path)
            
            def create_new_img(self, file_path, version):
                return self.tool.img_controller.create_new_img(file_path, version)
            
            def is_img_open(self):
                return self.tool.img_controller.get_archive_count() > 0
            
            def close_img(self):
                return self.tool.img_controller.close_all_archives()
            
            def extract_selected(self, output_dir):
                # Delegate to controller implementation
                return self.tool.img_controller.extract_selected(output_dir)

            def delete_selected(self):
                return self.tool.img_controller.delete_selected()
            
            # Import methods
            def import_file(self, file_path, entry_name=None):
                return self.tool.img_controller.import_file(file_path, entry_name)
            
            def import_multiple_files(self, file_paths, entry_names=None):
                return self.tool.img_controller.import_multiple_files(file_paths, entry_names)
            
            def import_folder(self, folder_path, recursive=False, filter_extensions=None):
                return self.tool.img_controller.import_folder(folder_path, recursive, filter_extensions)
            
            def get_import_preview(self, file_paths):
                return self.tool.img_controller.get_import_preview(file_paths)
            
            # Modification tracking methods
            def get_detailed_modification_status(self):
                return self.tool.img_controller.get_detailed_modification_status()
            
            def restore_deleted_entry(self, entry_name):
                return self.tool.img_controller.restore_deleted_entry(entry_name)
            
            def restore_all_deleted_entries(self):
                return self.tool.img_controller.restore_all_deleted_entries()
            
            def get_img_info(self):
                archive = self.tool.get_current_archive()
                if archive and self.tool.current_archive_tab:
                    return self.tool.current_archive_tab.get_archive_info()
                return None
            
            def get_rw_version_summary(self):
                # Get the read/write version summary for the current archive
                archive = self.tool.get_current_archive()
                if archive:
                    return archive.get_rw_version_summary()
                return None
            
            @property
            def selected_entries(self):
                return self.tool.get_selected_entries()
        
        return IMGEditorAdapter(self)
    
    # Import UI interaction handlers - make them methods of this class
    def _import_ui_handlers(self):
        """Import and bind UI interaction handlers"""
        try:
            from .ui_interaction_handlers import (
                _open_img_file,
                _create_new_img,
                _close_img,
                _extract_selected,
                _delete_selected,
                _import_Via_IDE,
                _import_multiple_files,
                _import_folder,
                _get_import_preview,
                _show_modification_status,
                _proceed_with_import,
                _proceed_with_ide_import,
                _on_img_loaded,
                _on_img_closed,
                _on_entries_updated,
            )
            
            # Bind imported functions as methods of this class
            self._open_img_file = _open_img_file.__get__(self, self.__class__)
            self._create_new_img = _create_new_img.__get__(self, self.__class__)
            self._close_img = _close_img.__get__(self, self.__class__)
            self._extract_selected = _extract_selected.__get__(self, self.__class__)
            self._delete_selected = _delete_selected.__get__(self, self.__class__)
            self._import_Via_IDE = _import_Via_IDE.__get__(self, self.__class__)
            self._import_multiple_files = _import_multiple_files.__get__(self, self.__class__)
            self._import_folder = _import_folder.__get__(self, self.__class__)
            self._get_import_preview = _get_import_preview.__get__(self, self.__class__)
            self._show_modification_status = _show_modification_status.__get__(self, self.__class__)
            self._proceed_with_import = _proceed_with_import.__get__(self, self.__class__)
            self._proceed_with_ide_import = _proceed_with_ide_import.__get__(self, self.__class__)
            self._on_img_loaded_handler = _on_img_loaded.__get__(self, self.__class__)
            self._on_img_closed_handler = _on_img_closed.__get__(self, self.__class__)
            self._on_entries_updated_handler = _on_entries_updated.__get__(self, self.__class__)
            
        except ImportError:
            # If ui_interaction_handlers doesn't exist, use fallback methods
            self._open_img_file = self._fallback_open_img_file
            self._create_new_img = self._fallback_create_new_img
            self._close_img = self._fallback_close_img
            self._extract_selected = self._fallback_extract_selected
            self._delete_selected = self._fallback_delete_selected
            self._import_Via_IDE = self._fallback_import_Via_IDE
            self._import_multiple_files = self._fallback_import_multiple_files
            self._import_folder = self._fallback_import_folder
            self._get_import_preview = self._fallback_get_import_preview
            self._show_modification_status = self._fallback_show_modification_status
            self._proceed_with_import = self._fallback_proceed_with_import
            self._proceed_with_ide_import = self._fallback_proceed_with_ide_import
    
    
    def _fallback_extract_selected(self):
        """Fallback method for extracting selected entries"""
        selected_entries = self.get_selected_entries()
        if not selected_entries:
            message_box.warning("Please select entries to extract.", "No Selection", self)
            return
        message_box.info(f"Extract feature is not implemented yet. {len(selected_entries)} entries selected.", "Feature Not Implemented", self)
    
    def _fallback_delete_selected(self):
        """Fallback method for deleting selected entries"""
        selected_entries = self.get_selected_entries()
        if not selected_entries:
            message_box.warning("Please select entries to delete.", "No Selection", self)
            return
        message_box.info(f"Delete feature is not implemented yet. {len(selected_entries)} entries selected.", "Feature Not Implemented", self)
    
    def _fallback_create_new_img(self):
        """Fallback method for creating new IMG"""
        message_box.info("Create new IMG feature is not implemented yet.", "Feature Not Implemented", self)
    
    def _fallback_open_img_file(self):
        """Fallback method for opening IMG file"""
        message_box.info("Open IMG file feature is not implemented yet.", "Feature Not Implemented", self)
    
    def _fallback_close_img(self):
        """Fallback method for closing IMG file"""
        message_box.info("Close IMG file feature is not implemented yet.", "Feature Not Implemented", self)
    
    def _fallback_import_multiple_files(self):
        """Fallback method for importing multiple files"""
        message_box.info("Import multiple files feature is not implemented yet.", "Feature Not Implemented", self)
    
    def _fallback_import_folder(self):
        """Fallback method for importing folder"""
        message_box.info("Import folder feature is not implemented yet.", "Feature Not Implemented", self)
    
    def _fallback_get_import_preview(self):
        """Fallback method for import preview"""
        message_box.info("Import preview feature is not implemented yet.", "Feature Not Implemented", self)
    
    def _fallback_show_modification_status(self):
        """Fallback method for showing modification status"""
        message_box.info("Modification status feature is not implemented yet.", "Feature Not Implemented", self)
    
    def _fallback_proceed_with_import(self, dialog, file_paths):
        """Fallback method for proceeding with import"""
        message_box.info("Import feature is not implemented yet.", "Feature Not Implemented", self)
    
    def _fallback_import_Via_IDE(self):
        """Fallback method for IDE import"""
        message_box.info("IDE import feature is not implemented yet.", "Feature Not Implemented", self)
    
    def _fallback_proceed_with_ide_import(self, dialog, ide_file, models_dir):
        """Fallback method for proceeding with IDE import"""
        message_box.info("IDE import feature is not implemented yet.", "Feature Not Implemented", self)
    
    def setup_ui(self):
        """Setup the IMG Editor interface with tabbed archives"""
        rm = get_responsive_manager()
        fonts = rm.get_font_config()
        spacing = rm.get_spacing_config()
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # IMG Editor header with responsive sizing
        header_label = QLabel("📁 IMG Editor")
        header_label.setStyleSheet(f"font-weight: bold; font-size: {fonts['header']['size']}px; padding: {spacing['medium']}px;")
        main_layout.addWidget(header_label)
        
        # Main splitter for IMG content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Tabbed archives
        left_panel = self.create_left_panel()
        
        # Right panel: Tools and information
        right_panel = self.create_right_panel()
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # Set initial sizes
        splitter.setSizes([500, 450])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        
        main_layout.addWidget(splitter, 1)
        
        # Status info
        self.create_status_info(main_layout)
        
        self.setLayout(main_layout)
        self.setMinimumHeight(400)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    def create_left_panel(self):
        """Create the left panel with tabbed archives"""
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Archive tabs
        self.archive_tabs = QTabWidget()
        self.archive_tabs.setTabsClosable(True)
        self.archive_tabs.setMovable(True)
        self.archive_tabs.tabCloseRequested.connect(self._close_archive_tab)
        self.archive_tabs.currentChanged.connect(self._on_tab_changed)
        
        # Set responsive tab styling
        rm = get_responsive_manager()
        fonts = rm.get_font_config()
        spacing = rm.get_spacing_config()
        min_tab_width = rm.get_scaled_size(80)
        max_tab_width = rm.get_scaled_size(180)
        
        self.archive_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {ModernDarkTheme.BORDER_SECONDARY};
                border-radius: 4px;
                background-color: {ModernDarkTheme.BACKGROUND_SECONDARY};
            }}
            QTabBar::tab {{
                background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
                color: {ModernDarkTheme.TEXT_PRIMARY};
                min-width: {min_tab_width}px;
                max-width: {max_tab_width}px;
                padding: {spacing['small']}px {spacing['medium']}px;
                margin-right: 2px;
                border: 1px solid {ModernDarkTheme.BORDER_SECONDARY};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: {fonts['body']['size']}px;
            }}
            QTabBar::tab:selected {{
                background-color: {ModernDarkTheme.BACKGROUND_SECONDARY};
                color: white;
                border-bottom: 2px solid {ModernDarkTheme.TEXT_ACCENT};
            }}
            QTabBar::tab:hover {{
                background-color: {ModernDarkTheme.HOVER_COLOR};
            }}
        """)
        
        # Empty state widget
        self.empty_state = self.create_empty_state()
        
        # Add tabs to layout
        left_layout.addWidget(self.archive_tabs)
        
        # Initially show empty state
        self.show_empty_state()
        
        return left_panel
    
    def create_empty_state(self):
        """Create empty state widget when no archives are open"""
        rm = get_responsive_manager()
        fonts = rm.get_font_config()
        spacing = rm.get_spacing_config()
        
        empty_widget = QFrame()
        empty_widget.setFrameStyle(QFrame.Shape.StyledPanel)
        empty_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {ModernDarkTheme.BACKGROUND_SECONDARY};
                border: 2px dashed {ModernDarkTheme.BORDER_PRIMARY};
                border-radius: 8px;
            }}
            QLabel {{
                color: {ModernDarkTheme.TEXT_SECONDARY};
                font-size: {fonts['body']['size']}px;
            }}
        """)
        
        layout = QVBoxLayout(empty_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel("📁")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_size = fonts['header']['size'] * 3  # Scale icon with header font
        icon_label.setStyleSheet(f"font-size: {icon_size}px; color: {ModernDarkTheme.BORDER_PRIMARY};")
        
        text_label = QLabel("No IMG archives open")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setStyleSheet(f"font-size: {fonts['subheader']['size']}px; color: {ModernDarkTheme.TEXT_SECONDARY}; margin: {spacing['medium']}px;")
        
        hint_label = QLabel("Use 'Open IMG' or 'Open Multiple' to load archives")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_label.setStyleSheet(f"font-size: {fonts['small']['size']}px; color: {ModernDarkTheme.TEXT_SECONDARY}; margin: {spacing['small']}px;")
        
        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.addWidget(hint_label)
        
        return empty_widget
    
    def show_empty_state(self):
        """Show empty state when no archives are open"""
        if self.archive_tabs.count() == 0:
            # Clear the tab widget and add empty state
            self.archive_tabs.clear()
            self.archive_tabs.addTab(self.empty_state, "No Archives")
            self.archive_tabs.setTabsClosable(False)
    
    def hide_empty_state(self):
        """Hide empty state when archives are opened"""
        if self.archive_tabs.count() == 1 and self.archive_tabs.widget(0) == self.empty_state:
            self.archive_tabs.clear()
            self.archive_tabs.setTabsClosable(True)
    
    def create_status_info(self, parent_layout):
        """Create status information at bottom"""
        self.status_label = QLabel("Ready | No archives open")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
                color: {ModernDarkTheme.TEXT_PRIMARY};
                padding: 5px 10px;
                border-top: 1px solid {ModernDarkTheme.BORDER_PRIMARY};
                font-size: 11px;
            }}
        """)
        parent_layout.addWidget(self.status_label)
    
    def update_status(self):
        """Update status information"""
        archive_count = self.img_controller.get_archive_count()
        if archive_count == 0:
            self.status_label.setText("Ready | No archives open")
        else:
            active_archive = self.img_controller.get_active_archive()
            if active_archive:
                archive_name = Path(active_archive.file_path).name if active_archive.file_path else "Unknown"
                entry_count = len(active_archive.entries) if hasattr(active_archive, 'entries') else 0
                self.status_label.setText(f"Active: {archive_name} | {entry_count} entries | {archive_count} archive(s) open")
            else:
                self.status_label.setText(f"Ready | {archive_count} archive(s) open")
    
    def add_archive_tab(self, img_archive):
        """Add a new archive tab"""
        if not img_archive or not img_archive.file_path:
            return
        
        # Hide empty state if it's showing
        self.hide_empty_state()
        
        # Create tab with parent reference
        archive_tab = IMGArchiveTab(img_archive, parent=self)
        archive_tab.entries_selected.connect(self._on_entries_selected)
        archive_tab.archive_modified.connect(self._on_archive_modified)
        archive_tab.action_requested.connect(self._on_tab_action_requested)
        
        # Get tab title
        tab_title = Path(img_archive.file_path).name
        
        # Add tab
        tab_index = self.archive_tabs.addTab(archive_tab, tab_title)
        
        # Set as current tab
        self.archive_tabs.setCurrentIndex(tab_index)
        self.current_archive_tab = archive_tab
        
        # Update archive manager
        self.img_controller.switch_active_archive(img_archive.file_path)
        
        # Update status and info panel
        self.update_status()
        self.update_info_panel()
        
        return archive_tab
    
    def open_archive(self, file_path):
        """Open a single archive"""
        return self.img_controller.open_archive(file_path)
    
    def open_multiple_archives(self, file_paths):
        """Open multiple archives"""
        return self.img_controller.open_multiple_archives(file_paths)
    
    def switch_to_archive(self, file_path):
        """Switch to a specific archive tab"""
        if not file_path:
            return False
            
        for i in range(self.archive_tabs.count()):
            widget = self.archive_tabs.widget(i)
            if isinstance(widget, IMGArchiveTab) and widget.img_archive.file_path == file_path:
                self.archive_tabs.setCurrentIndex(i)
                return True
        return False
    
    def _close_archive_tab(self, index):
        """Close an archive tab"""
        widget = self.archive_tabs.widget(index)
        if isinstance(widget, IMGArchiveTab):
            # Remove from controller
            file_path = widget.img_archive.file_path
            if file_path:  # Only try to close if file_path is not None
                self.img_controller.close_archive(file_path)
            
            # Remove tab
            self.archive_tabs.removeTab(index)
            
            # Show empty state if no tabs left
            if self.archive_tabs.count() == 0:
                self.show_empty_state()
            
            # Update status
            self.update_status()
            self.update_info_panel()
    
    def _on_tab_changed(self, index):
        """Handle tab change"""
        widget = self.archive_tabs.widget(index)
        if isinstance(widget, IMGArchiveTab):
            self.current_archive_tab = widget
            # Only switch if file_path is not None
            if widget.img_archive.file_path:
                self.img_controller.switch_active_archive(widget.img_archive.file_path)
            self.update_status()
            self.update_info_panel()
    
    def _on_img_loaded(self, img_archive):
        """Handle when an archive is loaded by the controller"""
        self.add_archive_tab(img_archive)
    
    def _on_img_closed(self, file_path):
        """Handle when an archive is closed by the controller"""
        if not file_path:  # All archives closed
            while self.archive_tabs.count() > 0:
                self.archive_tabs.removeTab(0)
            self.show_empty_state()
        else:
            # Find and remove specific tab
            for i in range(self.archive_tabs.count()):
                widget = self.archive_tabs.widget(i)
                if isinstance(widget, IMGArchiveTab) and widget.img_archive.file_path == file_path:
                    self.archive_tabs.removeTab(i)
                    break
            
            if self.archive_tabs.count() == 0:
                self.show_empty_state()
        
        self.update_status()
        self.update_info_panel()
    
    def _on_archive_switched(self, img_archive):
        """Handle when active archive is switched"""
        if img_archive and img_archive.file_path:
            self.switch_to_archive(img_archive.file_path)
        self.update_status()
        self.update_info_panel()
        self.archive_switched.emit(img_archive)
    
    def _on_entries_updated_for_tabs(self, entries):
        """Refresh the current tab's table and info when controller entries change"""
        if self.current_archive_tab:
            self.current_archive_tab.entries_table.populate_entries(entries or [])
            self.update_info_panel()
            self.update_status()

    def _on_entries_selected(self, entries):
        """Handle entry selection in current tab by updating controller selection"""
        # Keep controller in sync with UI-selected entries
        self.img_controller.set_selected_entries(entries or [])
        # Optional: update status/info
        self.update_status()

    
    def _on_archive_modified(self, file_path):
        """Handle archive modification"""
        if not file_path:
            return
            
        # Update tab title to show modified state
        for i in range(self.archive_tabs.count()):
            widget = self.archive_tabs.widget(i)
            if isinstance(widget, IMGArchiveTab) and widget.img_archive.file_path == file_path:
                current_title = self.archive_tabs.tabText(i)
                if not current_title.endswith("*"):
                    self.archive_tabs.setTabText(i, current_title + "*")
                break
    
    def _on_tab_action_requested(self, action_name, data):
        """Handle action requests from tabs"""
        # Switch context to the requesting tab's archive if needed
        if isinstance(data, dict) and 'archive' in data:
            archive = data['archive']
            current_archive = self.get_current_archive()
            if (archive and archive.file_path and 
                current_archive and current_archive.file_path and
                archive.file_path != current_archive.file_path):
                self.switch_to_archive(archive.file_path)
        
        # Handle the action
        self.handle_img_tool(action_name)
    
    def get_current_archive(self):
        """Get currently active archive"""
        return self.img_controller.get_active_archive()
    
    def get_selected_entries(self):
        """Get selected entries from current tab"""
        if self.current_archive_tab:
            return self.current_archive_tab.get_selected_entries()
        return []
    
    def update_info_panel(self):
        """Update the information panel with current archive data"""
        if self.current_archive_tab:
            archive_info = self.current_archive_tab.get_archive_info()
            
            # Get RW summary from current archive
            rw_summary = None
            if self.current_archive_tab.img_archive:
                rw_summary = self.current_archive_tab.img_archive.get_rw_version_summary()
            
            # Get modification summary from controller
            mod_summary = self.img_controller.get_modification_info()
            
            self.file_info_panel.update_info(archive_info, rw_summary, mod_summary)
        else:
            self.file_info_panel.update_info()
    
    def create_right_panel(self):
        """Create the right panel with tools and information"""
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Set size policy and fixed dimensions
        right_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        right_panel.setMinimumWidth(350)
        
        # File info panel
        self.file_info_panel = IMGFileInfoPanel()
        right_layout.addWidget(self.file_info_panel)
        
        # Quick actions
        actions_group = QGroupBox("⚡ Quick Actions")
        actions_layout = QGridLayout()

        extract_btn = QPushButton("📤 Extract")
        extract_btn.clicked.connect(lambda: self.handle_img_tool("Extract Selected"))
        replace_btn = QPushButton("🔄 Replace")
        replace_btn.clicked.connect(lambda: self.handle_img_tool("Replace Selected"))
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.clicked.connect(lambda: self.handle_img_tool("Delete Selected"))
        rebuild_btn = QPushButton("🔄 Rebuild")
        rebuild_btn.clicked.connect(lambda: self.handle_img_tool("Rebuild"))
        import_btn = QPushButton("📥 Import")
        import_btn.clicked.connect(lambda: self.handle_img_tool("Import Files"))
        select_all_btn = QPushButton("✔️ Select All")
        select_all_btn.clicked.connect(lambda: self.handle_img_tool("Select All"))

        # Add buttons to grid layout
        actions_layout.addWidget(extract_btn, 0, 0)
        actions_layout.addWidget(replace_btn, 0, 1)
        actions_layout.addWidget(delete_btn, 0, 2)
        actions_layout.addWidget(rebuild_btn, 1, 0)
        actions_layout.addWidget(import_btn, 1, 1)
        actions_layout.addWidget(select_all_btn, 1, 2)

        actions_group.setLayout(actions_layout)
        right_layout.addWidget(actions_group)
        
        # IMG Tools Section
        tools_group = self.create_tools_section()
        
        # Wrap tools in a scroll area
        tools_scroll = QScrollArea()
        tools_scroll.setWidget(tools_group)
        tools_scroll.setWidgetResizable(True)
        tools_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        right_layout.addWidget(tools_scroll, 1)
        
        right_panel.setLayout(right_layout)
        return right_panel
    
    def create_tools_section(self):
        """Create the tools section with a tabbed interface for better space management"""
        tools_group = QGroupBox("🔧 IMG Tools")
        tools_layout = QVBoxLayout()
        
        # Create a tab widget to organize tools
        tab_widget = QTabWidget()
        tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # Set style for modern tabs
        tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {ModernDarkTheme.BORDER_SECONDARY};
                border-radius: 3px;
                background-color: {ModernDarkTheme.BACKGROUND_SECONDARY};
            }}
            QTabBar::tab {{
                background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
                color: {ModernDarkTheme.TEXT_PRIMARY};
                min-width: 80px;
                padding: 5px 10px;
                margin-right: 1px;
                border: 1px solid {ModernDarkTheme.BORDER_SECONDARY};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {ModernDarkTheme.BACKGROUND_SECONDARY};
                color: white;
                border-bottom: 2px solid {ModernDarkTheme.TEXT_ACCENT};
            }}
            QTabBar::tab:hover {{
                background-color: {ModernDarkTheme.HOVER_COLOR};
            }}
        """)
        
        # File Operations Tab
        file_tab = QWidget()
        file_layout = QVBoxLayout(file_tab)
        self.create_file_operations_group(file_layout)
        tab_widget.addTab(file_tab, "📁 File")
        
        # IMG Operations Tab
        img_tab = QWidget()
        img_layout = QVBoxLayout(img_tab)
        self.create_img_operations_group(img_layout)
        tab_widget.addTab(img_tab, "⚙️ IMG")
        
        # Import/Export Tab
        import_tab = QWidget()
        import_layout = QVBoxLayout(import_tab)
        self.create_import_export_group(import_layout)
        tab_widget.addTab(import_tab, "📤 Import/Export")
        
        tools_layout.addWidget(tab_widget)
        tools_group.setLayout(tools_layout)
        
        # Set size policies
        tools_group.setMinimumHeight(250)  # Reduced minimum height
        tools_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        return tools_group
    
    def create_file_operations_group(self, parent_layout):
        """Create File Operations tool group"""
        file_ops_group = QGroupBox("File Operations")
        
        # Main grid layout for buttons
        file_grid = QGridLayout()
        # Set horizontal spacing between columns
        file_grid.setHorizontalSpacing(15)
        # Set vertical spacing between rows
        
        # Create buttons
        create_new_btn = QPushButton("📄 Create New")
        create_new_btn.clicked.connect(lambda: self.handle_img_tool("Create New IMG"))
        
        open_img_btn = QPushButton("📂 Open IMG")
        open_img_btn.clicked.connect(lambda: self.handle_img_tool("Open IMG"))
        
        open_multiple_btn = QPushButton("📂 Open Multiple")
        open_multiple_btn.clicked.connect(lambda: self.handle_img_tool("Open Multiple Files"))
        
        close_img_btn = QPushButton("❌ Close IMG")
        close_img_btn.clicked.connect(lambda: self.handle_img_tool("Close IMG"))
        
        close_all_btn = QPushButton("❌ Close All")
        close_all_btn.clicked.connect(lambda: self.handle_img_tool("Close All"))
        
                
        
        # Add buttons to grid - using a 3x3 grid for better organization
        file_grid.addWidget(create_new_btn, 0, 0)
        file_grid.addWidget(open_img_btn, 0, 1)
        
        file_grid.addWidget(open_multiple_btn, 1, 0)
        file_grid.addWidget(close_img_btn, 1, 1)
        
        file_grid.addWidget(close_all_btn, 2, 0)
        
        file_ops_group.setLayout(file_grid)
        
        # Add to parent layout
        parent_layout.addWidget(file_ops_group)
    
    def create_img_operations_group(self, parent_layout):
        """Create IMG Operations tool group"""
        img_ops_group = QGroupBox("IMG Operations")
        
        img_grid = QGridLayout()
        # Set horizontal spacing between columns
        img_grid.setHorizontalSpacing(15)
        # Set vertical spacing between rows
        
        rebuild_btn = QPushButton("🔨 Rebuild")
        rebuild_btn.clicked.connect(lambda: self.handle_img_tool("Rebuild IMG"))
        
        rebuild_all_btn = QPushButton("🔨 Rebuild All")
        rebuild_all_btn.clicked.connect(lambda: self.handle_img_tool("Rebuild All"))
        
        
        merge_btn = QPushButton("🔗 Merge IMG")
        merge_btn.clicked.connect(lambda: self.handle_img_tool("Merge IMG"))
        
        split_btn = QPushButton("✂️ Split IMG")
        split_btn.clicked.connect(lambda: self.handle_img_tool("Split IMG"))
        
        convert_btn = QPushButton("🔄 Convert Format")
        convert_btn.clicked.connect(lambda: self.handle_img_tool("Convert Format"))
        
        
        
        compress_btn = QPushButton("🗜️ Compress")
        compress_btn.clicked.connect(lambda: self.handle_img_tool("Compress IMG"))
        
        
        
        # Add buttons to grid
        img_grid.addWidget(rebuild_btn, 0, 0)
        img_grid.addWidget(rebuild_all_btn, 0, 1)
        img_grid.addWidget(merge_btn, 1, 0)
        img_grid.addWidget(split_btn, 1, 1)
        img_grid.addWidget(convert_btn, 2, 0)
        img_grid.addWidget(compress_btn, 2, 1)
        
        img_ops_group.setLayout(img_grid)
        
        # Add to parent layout
        parent_layout.addWidget(img_ops_group)
    
    def create_import_export_group(self, parent_layout):
        """Create Import/Export tool group"""
        import_export_group = QGroupBox("Import/Export")
        
        import_grid = QGridLayout()
        # Set horizontal spacing between columns
        import_grid.setHorizontalSpacing(10)
        # Set vertical spacing between rows
        import_grid.setVerticalSpacing(5)
        
        # Import buttons
        import_file_btn = QPushButton("📥 Import Via IDE")
        import_file_btn.clicked.connect(lambda: self.handle_img_tool("Import Via IDE"))
        
        import_files_btn = QPushButton("📥 Import Files")
        import_files_btn.clicked.connect(lambda: self.handle_img_tool("Import Files"))
        
        import_folder_btn = QPushButton("📁 Import Folder")
        import_folder_btn.clicked.connect(lambda: self.handle_img_tool("Import Folder"))
        
        import_preview_btn = QPushButton("👁️ Import Preview")
        import_preview_btn.clicked.connect(lambda: self.handle_img_tool("Import Preview"))
        
        # Export buttons
        export_all_btn = QPushButton("📤 Export All")
        export_all_btn.clicked.connect(lambda: self.handle_img_tool("Export All"))
        
        export_selected_btn = QPushButton("📤 Export Selected")
        export_selected_btn.clicked.connect(lambda: self.handle_img_tool("Export Selected"))
        
        export_by_type_btn = QPushButton("📤 Export by Type")
        export_by_type_btn.clicked.connect(lambda: self.handle_img_tool("Export by Type"))
        
        # Modification status button
        mod_status_btn = QPushButton("📊 Mod Status")
        mod_status_btn.clicked.connect(lambda: self.handle_img_tool("Show Modification Status"))
        
        # Add buttons to grid (3 columns now)
        import_grid.addWidget(import_file_btn, 0, 0)
        import_grid.addWidget(import_files_btn, 1, 0)
        import_grid.addWidget(import_folder_btn, 2, 0)
        import_grid.addWidget(import_preview_btn, 3, 0)
        
        import_grid.addWidget(export_all_btn, 0, 1)
        import_grid.addWidget(export_selected_btn, 1, 1)
        import_grid.addWidget(export_by_type_btn, 2, 1)
        import_grid.addWidget(mod_status_btn, 3, 1)
        
        import_export_group.setLayout(import_grid)
        
        # Add to parent layout
        parent_layout.addWidget(import_export_group)
    
    def handle_img_tool(self, tool_name):
        """Handle IMG tool action"""
        # Handle different tool actions using imported handlers
        if tool_name == "Open IMG":
            self._open_single_img()
        elif tool_name == "Open Multiple Files":
            self._open_multiple_imgs()
        elif tool_name == "Close IMG":
            self._close_current_img()
        elif tool_name == "Close All":
            self._close_all_imgs()
        elif tool_name == "Create New IMG":
            self._create_new_img()
        elif tool_name == "Extract Selected":
            self._extract_selected()
        elif tool_name == "Delete Selected":
            self._delete_selected()
        # Import actions
        elif tool_name == "Import Via IDE":
            self._import_Via_IDE()
        elif tool_name == "Import Files":
            self._import_multiple_files()
        elif tool_name == "Import Folder":
            self._import_folder()
        elif tool_name == "Import Preview":
            self._get_import_preview()
        elif tool_name == "Show Modification Status":
            self._show_modification_status()
        else:
            # For other tools not yet implemented
            message_box.info(f"The '{tool_name}' feature is not implemented yet.", "Feature Not Implemented", self)
    
    def _open_single_img(self):
        """Open a single IMG file"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, 
            "Open IMG Archive", 
            "", 
            "IMG Archives (*.img);;All Files (*.*)"
        )
        
        if file_path:
            success, message = self.open_archive(file_path)
            if success:
                message_box.info(message, "Success", self)
            else:
                message_box.error(message, "Error", self)

    def _open_multiple_imgs(self):
        """Open multiple IMG files"""
        file_dialog = QFileDialog()
        file_paths, _ = file_dialog.getOpenFileNames(
            self, 
            "Open Multiple IMG Archives", 
            "", 
            "IMG Archives (*.img);;All Files (*.*)"
        )
        
        if file_paths:
            success, message = self.open_multiple_archives(file_paths)
            if success:
                message_box.info(message, "Success", self)
            else:
                message_box.error(message, "Error", self)

    def _close_current_img(self):
        """Close current IMG archive"""
        current_index = self.archive_tabs.currentIndex()
        if current_index >= 0 and isinstance(self.archive_tabs.widget(current_index), IMGArchiveTab):
            self._close_archive_tab(current_index)
        else:
            message_box.warning("No archive is currently open.", "No Archive", self)

    def _close_all_imgs(self):
        """Close all IMG archives"""
        while self.archive_tabs.count() > 0:
            widget = self.archive_tabs.widget(0)
            if isinstance(widget, IMGArchiveTab):
                self._close_archive_tab(0)
            else:
                break
        self.show_empty_state()
    
    def load_img_file(self, file_path):
        """Load an IMG file into the editor (public interface)"""
        success, message = self.open_archive(file_path)
        if not success:
            message_box.error(message, "Error Loading IMG", self)
        return success
