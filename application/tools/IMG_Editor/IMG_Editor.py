"""
IMG Editor Tool for Renderware Modding Suite
Handles IMG archive file operations and management
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QGroupBox, QPushButton, QSplitter, QTreeWidget,
                            QTreeWidgetItem, QLineEdit, QComboBox, QProgressBar,
                            QScrollArea, QSizePolicy, QTableWidget, QTableWidgetItem,
                            QHeaderView, QFileDialog, QGridLayout, QTabWidget,
                            QToolButton, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal

from application.common.message_box import message_box


class IMGFileInfoPanel(QGroupBox):
    """Panel showing IMG file information"""
    
    def __init__(self, parent=None):
        super().__init__("IMG File Information", parent)
        self._setup_ui()
        
    def _setup_ui(self):
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
        
        # Add labels to layout
        layout.addWidget(self.file_path_label)
        layout.addWidget(self.version_label)
        layout.addWidget(self.entry_count_label)
        layout.addWidget(self.total_size_label)
        layout.addWidget(self.modified_label)
        layout.addWidget(self.rw_files_label)
        layout.addWidget(self.rw_versions_label)
        
        # Apply modern styling
        self.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                padding: 2px;
            }
        """)
    
    def update_info(self, img_info=None, rw_summary=None):
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



class IMGEntriesTable(QTableWidget):
    """Enhanced table widget for IMG entries"""
    entry_double_clicked = pyqtSignal(object)
    entry_selected = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels(['Name', 'Type', 'Size', 'Offset', 'RW Version', 'Streaming', 'Compression'])
        
        # Setup table properties
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        
        # Auto-resize columns to fill the available space
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            
        # Add style for modern look
        self.setStyleSheet("""
            QTableWidget {
                background-color: #2d2d2d;
                gridline-color: #444;
                border: 1px solid #555;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 4px;
                border-bottom: 1px solid #444;
            }
            QTableWidget::item:selected {
                background-color: #007acc;
                color: white;
            }
            QHeaderView::section {
                background-color: #333;
                color: white;
                padding: 4px;
                border: 1px solid #555;
                font-weight: bold;
            }
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
    filter_changed = pyqtSignal(str, str, str)  # text_filter, type_filter, rw_version_filter
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
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
        
        # Apply modern styling
        combo_style = """
            QComboBox {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
                min-width: 6em;
            }
            QComboBox:hover {
                border: 1px solid #007acc;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left: 1px solid #555;
            }
        """
        self.type_combo.setStyleSheet(combo_style)
        self.rw_version_combo.setStyleSheet(combo_style)
        
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
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


class ImgEditorTool(QWidget):
    """IMG Editor tool interface"""
    
    # Signals for tool actions
    tool_action = pyqtSignal(str, str)  # action_name, parameters
    
    # Import UI interaction handlers
    from .ui_interaction_handlers import (_open_img_file, _create_new_img, _save_img, 
                                  _save_img_as, _close_img, _add_files, 
                                  _extract_selected, _delete_selected,
                                  _on_img_loaded, _on_img_closed, _on_entries_updated)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.img_file = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the IMG Editor interface"""
        main_layout = QVBoxLayout()
        
        # IMG Editor header
        header_label = QLabel("📁 IMG Editor")
        header_label.setStyleSheet("font-weight: bold; font-size: 16px; padding: 10px;")
        main_layout.addWidget(header_label)
        
        # Main splitter for IMG content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: IMG file tree
        left_panel = self.create_left_panel()
        
        # Right panel: Entry details/preview and tools
        right_panel = self.create_right_panel()
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([500, 100])  # Set balanced initial sizes
        splitter.setStretchFactor(0, 1)  # Left panel can stretch
        splitter.setStretchFactor(1, 1)  # Right panel can stretch equally
        
        main_layout.addWidget(splitter)
        
        # Make sure the widget stretches to fill available space
        self.setMinimumHeight(400)  # Increased minimum height for stability
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.setLayout(main_layout)
    
    def create_left_panel(self):
        """Create the left panel with file table"""
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # Add filter panel at top
        self.filter_panel = FilterPanel()
        self.filter_panel.filter_changed.connect(self._on_filter_changed)
        left_layout.addWidget(self.filter_panel)
        
        # Add IMG entries table
        self.entries_table = IMGEntriesTable()
        self.entries_table.entry_double_clicked.connect(self._on_entry_double_clicked)
        self.entries_table.entry_selected.connect(self._on_entry_selected)
        left_layout.addWidget(self.entries_table)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Add")
        add_btn.clicked.connect(lambda: self.handle_img_tool("Add Files"))
        extract_btn = QPushButton("📤 Extract")
        extract_btn.clicked.connect(lambda: self.handle_img_tool("Extract Selected"))
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.clicked.connect(lambda: self.handle_img_tool("Delete Selected"))
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(extract_btn)
        btn_layout.addWidget(delete_btn)
        
        left_layout.addLayout(btn_layout)
        left_panel.setLayout(left_layout)
        
        return left_panel
    
    def create_right_panel(self):
        """Create the right panel with tools and actions"""
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Set size policy and fixed dimensions to prevent resizing
        right_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_panel.setMinimumWidth(350)  # Minimum width for right panel
        right_panel.setMinimumHeight(600)  # Minimum height to prevent collapse
        
        self.file_info_panel = IMGFileInfoPanel()
        right_layout.addWidget(self.file_info_panel)
                
        # Quick actions
        actions_group = QGroupBox("⚡ Quick Actions")
        actions_layout = QVBoxLayout()
        
        extract_btn = QPushButton("📤 Extract Selected")
        extract_btn.clicked.connect(lambda: self.handle_img_tool("Extract Selected"))
        replace_btn = QPushButton("🔄 Replace Selected")
        replace_btn.clicked.connect(lambda: self.handle_img_tool("Replace Selected"))
        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.clicked.connect(lambda: self.handle_img_tool("Delete Selected"))
        
        actions_layout.addWidget(extract_btn)
        actions_layout.addWidget(replace_btn)
        actions_layout.addWidget(delete_btn)
        
        actions_group.setLayout(actions_layout)
        right_layout.addWidget(actions_group)
        
        # IMG Tools Section
        tools_group = self.create_tools_section()
        
        # Wrap tools in a scroll area to handle overflow while maintaining size
        tools_scroll = QScrollArea()
        tools_scroll.setWidget(tools_group)
        tools_scroll.setWidgetResizable(True)
        tools_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        tools_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        tools_scroll.setMinimumHeight(500)  # Maintain minimum height
        
        right_layout.addWidget(tools_scroll)
        
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
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444;
                border-radius: 3px;
                background-color: #2d2d2d;
            }
            QTabBar::tab {
                background-color: #333;
                color: #ccc;
                min-width: 80px;
                padding: 5px 10px;
                margin-right: 1px;
                border: 1px solid #444;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #2d2d2d;
                color: white;
                border-bottom: 2px solid #007acc;
            }
            QTabBar::tab:hover {
                background-color: #3a3a3a;
            }
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
        
        # Entry Management Tab
        entry_tab = QWidget()
        entry_layout = QVBoxLayout(entry_tab)
        self.create_entry_management_group(entry_layout)
        tab_widget.addTab(entry_tab, "📝 Entries")
        
        # Selection Tools Tab
        selection_tab = QWidget()
        selection_layout = QVBoxLayout(selection_tab)
        self.create_selection_tools_group(selection_layout)
        tab_widget.addTab(selection_tab, "✅ Selection")
        
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
        file_grid.setHorizontalSpacing(10)
        # Set vertical spacing between rows
        file_grid.setVerticalSpacing(5)
        
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
        
        recent_files_btn = QPushButton("📋 Recent Files")
        recent_files_btn.clicked.connect(lambda: self.handle_img_tool("Recent Files"))
        
        save_img_btn = QPushButton("💾 Save IMG")
        save_img_btn.clicked.connect(lambda: self.handle_img_tool("Save IMG"))
        
        save_as_btn = QPushButton("📋 Save As...")
        save_as_btn.clicked.connect(lambda: self.handle_img_tool("Save IMG As"))
        
        reload_btn = QPushButton("🔄 Reload IMG")
        reload_btn.clicked.connect(lambda: self.handle_img_tool("Reload IMG"))
        
        # Add buttons to grid - using a 3x3 grid for better organization
        file_grid.addWidget(create_new_btn, 0, 0)
        file_grid.addWidget(open_img_btn, 0, 1)
        file_grid.addWidget(save_img_btn, 0, 2)
        
        file_grid.addWidget(open_multiple_btn, 1, 0)
        file_grid.addWidget(close_img_btn, 1, 1)
        file_grid.addWidget(save_as_btn, 1, 2)
        
        file_grid.addWidget(close_all_btn, 2, 0)
        file_grid.addWidget(recent_files_btn, 2, 1)
        file_grid.addWidget(reload_btn, 2, 2)
        
        file_ops_group.setLayout(file_grid)
        
        # Add to parent layout
        parent_layout.addWidget(file_ops_group)
        
        save_img_btn = QPushButton("💾 Save IMG")
        save_img_btn.clicked.connect(lambda: self.handle_img_tool("Save IMG"))
        
        save_as_btn = QPushButton("💾 Save As")
        save_as_btn.clicked.connect(lambda: self.handle_img_tool("Save As"))
        
        reload_btn = QPushButton("🔄 Reload")
        reload_btn.clicked.connect(lambda: self.handle_img_tool("Reload/Refresh"))
        
        # Add buttons to grid (vertical arrangement)
        file_grid.addWidget(create_new_btn, 0, 0)
        file_grid.addWidget(open_img_btn, 1, 0)
        file_grid.addWidget(open_multiple_btn, 2, 0)
        file_grid.addWidget(close_img_btn, 0, 1)
        file_grid.addWidget(close_all_btn, 1, 1)
        file_grid.addWidget(recent_files_btn, 2, 1)
        file_grid.addWidget(save_img_btn, 0, 2)
        file_grid.addWidget(save_as_btn, 1, 2)
        file_grid.addWidget(reload_btn, 2, 2)
        
        file_ops_group.setLayout(file_grid)
        
        # Add to parent layout
        parent_layout.addWidget(file_ops_group)
    
    def create_img_operations_group(self, parent_layout):
        """Create IMG Operations tool group"""
        img_ops_group = QGroupBox("IMG Operations")
        
        img_grid = QGridLayout()
        # Set horizontal spacing between columns
        img_grid.setHorizontalSpacing(10)
        # Set vertical spacing between rows
        img_grid.setVerticalSpacing(5)
        
        rebuild_btn = QPushButton("🔨 Rebuild")
        rebuild_btn.clicked.connect(lambda: self.handle_img_tool("Rebuild IMG"))
        
        rebuild_all_btn = QPushButton("🔨 Rebuild All")
        rebuild_all_btn.clicked.connect(lambda: self.handle_img_tool("Rebuild All"))
        
        rebuild_as_btn = QPushButton("🔨 Rebuild As")
        rebuild_as_btn.clicked.connect(lambda: self.handle_img_tool("Rebuild As"))
        
        merge_btn = QPushButton("🔗 Merge IMG")
        merge_btn.clicked.connect(lambda: self.handle_img_tool("Merge IMG"))
        
        split_btn = QPushButton("✂️ Split IMG")
        split_btn.clicked.connect(lambda: self.handle_img_tool("Split IMG"))
        
        convert_btn = QPushButton("🔄 Convert Format")
        convert_btn.clicked.connect(lambda: self.handle_img_tool("Convert Format"))
        
        optimize_btn = QPushButton("⚡ Optimize")
        optimize_btn.clicked.connect(lambda: self.handle_img_tool("Optimize IMG"))
        
        defrag_btn = QPushButton("🧹 Defragment")
        defrag_btn.clicked.connect(lambda: self.handle_img_tool("Defragment IMG"))
        
        compress_btn = QPushButton("🗜️ Compress")
        compress_btn.clicked.connect(lambda: self.handle_img_tool("Compress IMG"))
        
        backup_btn = QPushButton("📋 Backup")
        backup_btn.clicked.connect(lambda: self.handle_img_tool("Backup IMG"))
        
        compare_btn = QPushButton("⚖️ Compare")
        compare_btn.clicked.connect(lambda: self.handle_img_tool("Compare IMG Files"))
        
        # Add buttons to grid
        img_grid.addWidget(rebuild_btn, 0, 0)
        img_grid.addWidget(rebuild_all_btn, 1, 0)
        img_grid.addWidget(rebuild_as_btn, 2, 0)
        img_grid.addWidget(merge_btn, 0, 1)
        img_grid.addWidget(split_btn, 1, 1)
        img_grid.addWidget(convert_btn, 2, 1)
        img_grid.addWidget(optimize_btn, 0, 2)
        img_grid.addWidget(defrag_btn, 1, 2)
        img_grid.addWidget(compress_btn, 2, 2)
        img_grid.addWidget(backup_btn, 3, 0)
        img_grid.addWidget(compare_btn, 3, 1)
        
        img_ops_group.setLayout(img_grid)
        
        # Add to parent layout
        parent_layout.addWidget(img_ops_group)
        img_grid.addWidget(optimize_btn, 0, 2)
        img_grid.addWidget(defrag_btn, 1, 2)
        img_grid.addWidget(compress_btn, 2, 2)
        img_grid.addWidget(backup_btn, 3, 0)
        img_grid.addWidget(compare_btn, 3, 1)
        
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
        
        import_files_btn = QPushButton("📥 Import Files")
        import_files_btn.clicked.connect(lambda: self.handle_img_tool("Import Files"))
        
        import_ide_btn = QPushButton("📥 Import via IDE")
        import_ide_btn.clicked.connect(lambda: self.handle_img_tool("Import via IDE"))
        
        import_folder_btn = QPushButton("� Import Folder")
        import_folder_btn.clicked.connect(lambda: self.handle_img_tool("Import Folder"))
        
        export_all_btn = QPushButton("📤 Export All")
        export_all_btn.clicked.connect(lambda: self.handle_img_tool("Export All"))
        
        export_selected_btn = QPushButton("📤 Export Selected")
        export_selected_btn.clicked.connect(lambda: self.handle_img_tool("Export Selected"))
        
        export_by_type_btn = QPushButton("📤 Export by Type")
        export_by_type_btn.clicked.connect(lambda: self.handle_img_tool("Export by Type"))
        
        # Add buttons to grid
        import_grid.addWidget(import_files_btn, 0, 0)
        import_grid.addWidget(import_ide_btn, 1, 0)
        import_grid.addWidget(import_folder_btn, 2, 0)
        import_grid.addWidget(export_all_btn, 0, 1)
        import_grid.addWidget(export_selected_btn, 1, 1)
        import_grid.addWidget(export_by_type_btn, 2, 1)
        
        import_export_group.setLayout(import_grid)
        
        # Add to parent layout
        parent_layout.addWidget(import_export_group)
    
    def create_entry_management_group(self, parent_layout):
        """Create Entry Management tool group"""
        entry_group = QGroupBox("📝 Entry Management")
        
        entry_grid = QGridLayout()
        # Set horizontal spacing between columns
        entry_grid.setHorizontalSpacing(10)
        # Set vertical spacing between rows
        entry_grid.setVerticalSpacing(5)
        
        extract_btn = QPushButton("📦 Extract Entry")
        extract_btn.clicked.connect(lambda: self.handle_img_tool("Extract Entry"))
        extract_all_btn = QPushButton("📦 Extract All")
        extract_all_btn.clicked.connect(lambda: self.handle_img_tool("Extract All"))
        batch_extract_btn = QPushButton("📦 Batch Extract")
        batch_extract_btn.clicked.connect(lambda: self.handle_img_tool("Batch Extract"))
        
        replace_btn = QPushButton("🔄 Replace Entry")
        replace_btn.clicked.connect(lambda: self.handle_img_tool("Replace Entry"))
        
        rename_btn = QPushButton("✏️ Rename Entry")
        rename_btn.clicked.connect(lambda: self.handle_img_tool("Rename Entry"))
        
        delete_btn = QPushButton("🗑️ Delete Entry")
        delete_btn.clicked.connect(lambda: self.handle_img_tool("Delete Entry"))
        copy_btn = QPushButton("📋 Copy Entry")
        copy_btn.clicked.connect(lambda: self.handle_img_tool("Copy Entry"))
        
        move_btn = QPushButton("↪️ Move Entry")
        move_btn.clicked.connect(lambda: self.handle_img_tool("Move Entry"))
        view_btn = QPushButton("👁️ View Entry")
        view_btn.clicked.connect(lambda: self.handle_img_tool("View Entry"))
        
        # Add buttons to grid
        entry_grid.addWidget(extract_btn, 0, 0)
        entry_grid.addWidget(extract_all_btn, 1, 0)
        entry_grid.addWidget(batch_extract_btn, 2, 0)
        entry_grid.addWidget(replace_btn, 0, 1)
        entry_grid.addWidget(rename_btn, 1, 1)
        entry_grid.addWidget(delete_btn, 2, 1)
        entry_grid.addWidget(copy_btn, 0, 2)
        entry_grid.addWidget(move_btn, 1, 2)
        entry_grid.addWidget(view_btn, 2, 2)
        
        entry_group.setLayout(entry_grid)
        
        # Add to parent layout
        parent_layout.addWidget(entry_group)
    
    def create_selection_tools_group(self, parent_layout):
        """Create Selection Tools group"""
        selection_group = QGroupBox("✅ Selection Tools")
        
        selection_grid = QGridLayout()
        # Set horizontal spacing between columns
        selection_grid.setHorizontalSpacing(10)
        # Set vertical spacing between rows
        selection_grid.setVerticalSpacing(5)
        
        select_all_btn = QPushButton("✅ Select All")
        select_all_btn.clicked.connect(lambda: self.handle_img_tool("Select All"))
        
        select_inverse_btn = QPushButton("🔄 Select Inverse")
        select_inverse_btn.clicked.connect(lambda: self.handle_img_tool("Select Inverse"))
        
        select_none_btn = QPushButton("❌ Select None")
        select_none_btn.clicked.connect(lambda: self.handle_img_tool("Select None"))
        
        sort_btn = QPushButton("📊 Sort Entries")
        sort_btn.clicked.connect(lambda: self.handle_img_tool("Sort Entries"))
        
        pin_btn = QPushButton("📌 Pin Selected")
        pin_btn.clicked.connect(lambda: self.handle_img_tool("Pin Selected"))
        
        # Add buttons to grid
        selection_grid.addWidget(select_all_btn, 0, 0)
        selection_grid.addWidget(select_inverse_btn, 1, 0)
        selection_grid.addWidget(select_none_btn, 2, 0)
        selection_grid.addWidget(sort_btn, 0, 1)
        selection_grid.addWidget(pin_btn, 1, 1)
        
        selection_group.setLayout(selection_grid)
        
        # Add to parent layout
        parent_layout.addWidget(selection_group)
    
    def handle_img_tool(self, tool_name):
        """Handle IMG tool action"""
        # Initialize backend if not already done
        if not hasattr(self, 'img_editor'):
            from .img_controller import IMGController
            self.img_editor = IMGController()
            
            # Connect signals
            self.img_editor.img_loaded.connect(self._on_img_loaded)
            self.img_editor.img_closed.connect(self._on_img_closed)
            self.img_editor.entries_updated.connect(self._on_entries_updated)
        
        # Handle different tool actions
        if tool_name == "Open IMG":
            self._open_img_file()
        elif tool_name == "Create New IMG":
            self._create_new_img()
        elif tool_name == "Save IMG":
            self._save_img()
        elif tool_name == "Save IMG As":
            self._save_img_as()
        elif tool_name == "Close IMG":
            self._close_img()
        elif tool_name == "Add Files":
            self._add_files()
        elif tool_name == "Extract Selected":
            self._extract_selected()
        elif tool_name == "Delete Selected":
            self._delete_selected()
        else:
            # For other tools not yet implemented
            from application.common.message_box import message_box
            message_box.info(f"The '{tool_name}' feature is not implemented yet.", "Feature Not Implemented")
    
    def _on_filter_changed(self, filter_text, filter_type, filter_rw_version):
        """Apply filters to the entries table"""
        self.entries_table.apply_filter(filter_text, filter_type, filter_rw_version)
    
    def _on_entry_double_clicked(self, entry):
        """Handle double-click on an entry"""
        # In a real implementation, this might show a preview or allow editing
        # For now, show entry details
        entry_info = f"Name: {entry.name}\n"
        entry_info += f"Type: {entry.type}\n"
        entry_info += f"Size: {entry.actual_size:,} bytes\n"
        entry_info += f"Offset: Sector {entry.offset}"
        
        message_box("Entry Details", entry_info, "info")
    
    def _on_entry_selected(self, entries):
        """Handle entry selection - update info panel"""
        # Store selected entries in the main editor
        if hasattr(self, 'img_editor'):
            self.img_editor.set_selected_entries(entries)
    
    def load_img_file(self, file_path):
        """Load an IMG file into the editor"""
        # Initialize backend if not already done
        if not hasattr(self, 'img_editor'):
            from .img_controller import IMGController
            self.img_editor = IMGController()
            
            # Connect signals
            self.img_editor.img_loaded.connect(self._on_img_loaded)
            self.img_editor.img_closed.connect(self._on_img_closed)
            self.img_editor.entries_updated.connect(self._on_entries_updated)
            
        # Load the file
        success, message = self.img_editor.open_img(file_path)
        
        if not success:
            message_box.error("Error Loading IMG", message, "error")
            
        return success
