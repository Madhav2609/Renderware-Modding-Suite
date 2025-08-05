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
# Import the core classes directly instead of their GUI components
from application.tools.img_editor.components.img_core_classes import IMGFile, IMGEntry, IMGVersion, FileType, format_file_size


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
        
        # Add labels to layout
        layout.addWidget(self.file_path_label)
        layout.addWidget(self.version_label)
        layout.addWidget(self.entry_count_label)
        layout.addWidget(self.total_size_label)
        layout.addWidget(self.modified_label)
        
        # Apply modern styling
        self.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                padding: 2px;
            }
        """)
    
    def update_info(self, img_file):
        """Update panel with IMG file information"""
        if not img_file:
            self.file_path_label.setText("Path: Not loaded")
            self.version_label.setText("Version: -")
            self.entry_count_label.setText("Entries: 0")
            self.total_size_label.setText("Total Size: 0 bytes")
            self.modified_label.setText("Modified: No")
            return
        
        # Update labels with IMG file info
        self.file_path_label.setText(f"Path: {img_file.filepath}")
        self.version_label.setText(f"Version: {img_file.version.name}")
        self.entry_count_label.setText(f"Entries: {len(img_file.entries)}")
        
        # Calculate total size
        total_size = sum(entry.size for entry in img_file.entries if hasattr(entry, 'size'))
        self.total_size_label.setText(f"Total Size: {format_file_size(total_size)}")
        
        # Check if modified
        is_modified = any(getattr(entry, 'is_new_entry', False) or 
                          getattr(entry, 'is_replaced', False) 
                          for entry in img_file.entries)
        self.modified_label.setText(f"Modified: {'Yes' if is_modified else 'No'}")


    def update_info(self, entry):
        """Update panel with entry information"""
        if not entry:
            self.name_label.setText("Name: -")
            self.type_label.setText("Type: -")
            self.size_label.setText("Size: -")
            self.offset_label.setText("Offset: -")
            self.version_label.setText("Version: -")
            self.status_label.setText("Status: -")
            return
        
        # Update labels with entry info
        self.name_label.setText(f"Name: {entry.name}")
        
        type_text = entry.extension.upper() if hasattr(entry, 'extension') else "Unknown"
        self.type_label.setText(f"Type: {type_text}")
        
        size_text = format_file_size(entry.size) if hasattr(entry, 'size') else "Unknown"
        self.size_label.setText(f"Size: {size_text}")
        
        offset_text = f"0x{entry.offset:X}" if hasattr(entry, 'offset') else "Unknown"
        self.offset_label.setText(f"Offset: {offset_text}")
        
        version_text = entry.get_version_text() if hasattr(entry, 'get_version_text') else "Unknown"
        self.version_label.setText(f"Version: {version_text}")
        
        status_text = "New" if hasattr(entry, 'is_new_entry') and entry.is_new_entry else \
                      "Modified" if hasattr(entry, 'is_replaced') and entry.is_replaced else \
                      "Original"
        self.status_label.setText(f"Status: {status_text}")


class CollapsibleGroupBox(QGroupBox):
    """Custom collapsible group box with accordion-style behavior using radio button style"""
    
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(False)  # Start collapsed
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.accordion_parent = None  # Will be set later
        
        # Style as radio button instead of checkbox
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QGroupBox::indicator {
                width: 13px;
                height: 13px;
                border-radius: 7px;
                border: 2px solid #555;
                background-color: #2b2b2b;
            }
            QGroupBox::indicator:checked {
                background-color: #007acc;
                border: 2px solid #007acc;
            }
            QGroupBox::indicator:unchecked {
                background-color: #2b2b2b;
                border: 2px solid #555;
            }
            QGroupBox::indicator:hover {
                border: 2px solid #007acc;
            }
        """)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.content_widget)
        
        # Connect toggle
        self.toggled.connect(self.on_toggled)
        
        # Initially hide content
        self.content_widget.setVisible(False)
    
    def set_accordion_parent(self, parent):
        """Set the parent that manages accordion behavior"""
        self.accordion_parent = parent
    
    def on_toggled(self, checked):
        """Handle expand/collapse"""
        self.content_widget.setVisible(checked)
        
        # If this is being expanded, collapse all other collapsible groups
        if checked and self.accordion_parent:
            self.accordion_parent.collapse_other_groups(self)
    
    def add_widget(self, widget):
        """Add widget to content area"""
        self.content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        """Add layout to content area"""
        self.content_layout.addLayout(layout)


class IMGEntriesTable(QTableWidget):
    """Enhanced table widget for IMG entries"""
    entry_double_clicked = pyqtSignal(object)
    entry_selected = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels(['Name', 'Type', 'Size', 'Offset', 'Version', 'Compression', 'Status'])
        
        # Setup table properties
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        
        # Auto-resize columns
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(6):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            
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
        if hasattr(self, 'entries') and row < len(self.entries):
            self.entry_double_clicked.emit(self.entries[row])
    
    def _on_selection_changed(self):
        """Handle selection change"""
        selected_rows = {item.row() for item in self.selectedItems()}
        if hasattr(self, 'entries') and selected_rows:
            # Get the first selected entry
            row = min(selected_rows)
            if row < len(self.entries):
                self.entry_selected.emit(self.entries[row])
    
    def populate_entries(self, entries):
        """Populate table with entries"""
        self.entries = entries
        self.setRowCount(0)  # Clear existing rows
        
        for i, entry in enumerate(entries):
            self.insertRow(i)
            
            # Name
            self.setItem(i, 0, QTableWidgetItem(entry.name))
            
            # Type
            type_text = entry.extension.upper() if hasattr(entry, 'extension') else "Unknown"
            self.setItem(i, 1, QTableWidgetItem(type_text))
            
            # Size
            size_text = format_file_size(entry.size) if hasattr(entry, 'size') else "Unknown"
            self.setItem(i, 2, QTableWidgetItem(size_text))
            
            # Offset
            offset_text = f"0x{entry.offset:X}" if hasattr(entry, 'offset') else "Unknown"
            self.setItem(i, 3, QTableWidgetItem(offset_text))
            
            # Version
            version_text = entry.get_version_text() if hasattr(entry, 'get_version_text') else "Unknown"
            self.setItem(i, 4, QTableWidgetItem(version_text))
            
            # Compression
            compression_text = entry.compression_type.value if hasattr(entry, 'compression_type') else "None"
            self.setItem(i, 5, QTableWidgetItem(compression_text))
            
            # Status
            status_text = "New" if hasattr(entry, 'is_new_entry') and entry.is_new_entry else \
                          "Modified" if hasattr(entry, 'is_replaced') and entry.is_replaced else \
                          "Original"
            self.setItem(i, 6, QTableWidgetItem(status_text))
    
    def apply_filter(self, filter_text=None, filter_type=None):
        """Apply filter to table entries"""
        if not hasattr(self, 'entries'):
            return
            
        filter_text = filter_text.lower() if filter_text else ""
        
        for i, entry in enumerate(self.entries):
            show_row = True
            
            # Apply text filter
            if filter_text and filter_text not in entry.name.lower():
                show_row = False
                
            # Apply type filter
            if filter_type and filter_type != "All":
                entry_type = entry.extension.upper() if hasattr(entry, 'extension') else ""
                if entry_type != filter_type:
                    show_row = False
            
            # Show/hide row
            self.setRowHidden(i, not show_row)


class FilterPanel(QWidget):
    """Filter panel for IMG entries"""
    filter_changed = pyqtSignal(str, str)
    
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
        
        # Search filter
        search_group = QGroupBox("Search")
        search_layout = QHBoxLayout(search_group)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Search entries...")
        self.search_edit.textChanged.connect(self._filter_changed)
        search_layout.addWidget(self.search_edit)
        
        # Apply modern styling
        self.type_combo.setStyleSheet("""
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
        """)
        
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
        layout.addWidget(search_group)
    
    def _filter_changed(self):
        """Emit signal when filter is changed"""
        filter_text = self.search_edit.text()
        filter_type = self.type_combo.currentText()
        self.filter_changed.emit(filter_text, filter_type)


class ImgEditorTool(QWidget):
    """IMG Editor tool interface"""
    
    # Signals for tool actions
    tool_action = pyqtSignal(str, str)  # action_name, parameters
    
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
        # Emit signal with tool action
        self.tool_action.emit("img_tool", tool_name)
    
    def _on_filter_changed(self, filter_text, filter_type):
        """Apply filters to the entries table"""
        if hasattr(self, 'entries_table'):
            self.entries_table.apply_filter(filter_text, filter_type)
    
    def _on_entry_double_clicked(self, entry):
        """Handle double-click on an entry"""
        # Default action is to extract the entry
        self.tool_action.emit("extract_entry", entry.name)
    
    def _on_entry_selected(self, entry):
        """Handle entry selection - update info panel"""
        # In the future, update an entry info panel
        self.tool_action.emit("show_entry_info", entry.name)
    
    def load_img_file(self, img_file):
        """Load an IMG file into the editor"""
        self.img_file = img_file
        
        # Populate entries table
        if hasattr(self, 'entries_table') and img_file:
            self.entries_table.populate_entries(img_file.entries)
            
            # Update status bar
            msg = f"Loaded IMG file with {len(img_file.entries)} entries"
            self.tool_action.emit("status_update", msg)
