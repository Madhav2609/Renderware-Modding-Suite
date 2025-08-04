"""
IMG Editor Tool for Renderware Modding Suite
Handles IMG archive file operations and management
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QGroupBox, QPushButton, QSplitter, QTreeWidget,
                            QTreeWidgetItem, QLineEdit, QComboBox, QProgressBar,
                            QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction


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


class ImgEditorTool(QWidget):
    """IMG Editor tool interface"""
    
    # Signals for tool actions
    tool_action = pyqtSignal(str, str)  # action_name, parameters
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.collapsible_groups = []
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
        splitter.setSizes([400, 400])  # Set balanced initial sizes
        splitter.setStretchFactor(0, 1)  # Left panel can stretch
        splitter.setStretchFactor(1, 1)  # Right panel can stretch equally
        
        main_layout.addWidget(splitter)
        
        # Make sure the widget stretches to fill available space
        self.setMinimumHeight(700)  # Increased minimum height for stability
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.setLayout(main_layout)
    
    def create_left_panel(self):
        """Create the left panel with file tree"""
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # Search/filter
        search_layout = QHBoxLayout()
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("🔍 Search entries...")
        search_layout.addWidget(search_edit)
        
        filter_combo = QComboBox()
        filter_combo.addItems(["All Files", "DFF Models", "TXD Textures", "COL Collision", "Other"])
        search_layout.addWidget(filter_combo)
        
        left_layout.addLayout(search_layout)
        
        # IMG file tree
        img_tree = QTreeWidget()
        img_tree.setHeaderLabels(["Name", "Type", "Size"])
        img_tree.header().resizeSection(0, 200)
        
        # Sample entries
        root = QTreeWidgetItem(img_tree, ["No IMG file loaded", "", ""])
        sample_folder = QTreeWidgetItem(root, ["Sample Folder", "Folder", ""])
        QTreeWidgetItem(sample_folder, ["sample.dff", "DFF Model", "256 KB"])
        QTreeWidgetItem(sample_folder, ["sample.txd", "TXD Texture", "128 KB"])
        img_tree.expandAll()
        
        left_layout.addWidget(img_tree)
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
        
        # Entry info
        info_group = QGroupBox("📄 Entry Information")
        info_layout = QVBoxLayout()
        
        entry_info = QLabel("Select an entry to view details...")
        entry_info.setWordWrap(True)
        info_layout.addWidget(entry_info)
        
        info_group.setLayout(info_layout)
        right_layout.addWidget(info_group)
        
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
        
        # Progress bar
        progress_group = QGroupBox("📊 Progress")
        progress_layout = QVBoxLayout()
        
        progress_bar = QProgressBar()
        progress_label = QLabel("Ready")
        
        progress_layout.addWidget(progress_bar)
        progress_layout.addWidget(progress_label)
        
        progress_group.setLayout(progress_layout)
        right_layout.addWidget(progress_group)
        
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
        """Create the collapsible tools section"""
        tools_group = QGroupBox("🔧 IMG Tools")
        tools_layout = QVBoxLayout()
        
        # Set fixed height to prevent resizing when sections expand/collapse
        tools_group.setMinimumHeight(500)  # Ensure minimum height
        tools_group.setMaximumHeight(9999)  # Allow unlimited height expansion
        tools_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Create collapsible tool groups
        self.create_file_operations_group(tools_layout)
        self.create_img_operations_group(tools_layout)
        self.create_import_export_group(tools_layout)
        self.create_entry_management_group(tools_layout)
        self.create_selection_tools_group(tools_layout)
        
        tools_group.setLayout(tools_layout)
        return tools_group
    
    def create_file_operations_group(self, parent_layout):
        """Create File Operations tool group"""
        file_ops_group = CollapsibleGroupBox("📁 File Operations")
        file_ops_group.set_accordion_parent(self)
        self.collapsible_groups.append(file_ops_group)
        
        file_row1 = QHBoxLayout()
        create_new_btn = QPushButton("📄 Create New")
        create_new_btn.clicked.connect(lambda: self.handle_img_tool("Create New IMG"))
        open_img_btn = QPushButton("📂 Open IMG")
        open_img_btn.clicked.connect(lambda: self.handle_img_tool("Open IMG"))
        open_multiple_btn = QPushButton("📂 Open Multiple")
        open_multiple_btn.clicked.connect(lambda: self.handle_img_tool("Open Multiple Files"))
        file_row1.addWidget(create_new_btn)
        file_row1.addWidget(open_img_btn)
        file_row1.addWidget(open_multiple_btn)
        
        file_row2 = QHBoxLayout()
        close_img_btn = QPushButton("❌ Close IMG")
        close_img_btn.clicked.connect(lambda: self.handle_img_tool("Close IMG"))
        close_all_btn = QPushButton("❌ Close All")
        close_all_btn.clicked.connect(lambda: self.handle_img_tool("Close All"))
        recent_files_btn = QPushButton("🕒 Recent Files")
        recent_files_btn.clicked.connect(lambda: self.handle_img_tool("Recent Files"))
        file_row2.addWidget(close_img_btn)
        file_row2.addWidget(close_all_btn)
        file_row2.addWidget(recent_files_btn)
        
        file_row3 = QHBoxLayout()
        save_img_btn = QPushButton("💾 Save IMG")
        save_img_btn.clicked.connect(lambda: self.handle_img_tool("Save IMG"))
        save_as_btn = QPushButton("💾 Save As")
        save_as_btn.clicked.connect(lambda: self.handle_img_tool("Save As"))
        reload_btn = QPushButton("🔄 Reload")
        reload_btn.clicked.connect(lambda: self.handle_img_tool("Reload/Refresh"))
        file_row3.addWidget(save_img_btn)
        file_row3.addWidget(save_as_btn)
        file_row3.addWidget(reload_btn)
        
        file_ops_group.add_layout(file_row1)
        file_ops_group.add_layout(file_row2)
        file_ops_group.add_layout(file_row3)
        parent_layout.addWidget(file_ops_group)
    
    def create_img_operations_group(self, parent_layout):
        """Create IMG Operations tool group"""
        img_ops_group = CollapsibleGroupBox("⚙️ IMG Operations")
        img_ops_group.set_accordion_parent(self)
        self.collapsible_groups.append(img_ops_group)
        
        img_row1 = QHBoxLayout()
        rebuild_btn = QPushButton("🔨 Rebuild")
        rebuild_btn.clicked.connect(lambda: self.handle_img_tool("Rebuild IMG"))
        rebuild_all_btn = QPushButton("🔨 Rebuild All")
        rebuild_all_btn.clicked.connect(lambda: self.handle_img_tool("Rebuild All"))
        rebuild_as_btn = QPushButton("🔨 Rebuild As")
        rebuild_as_btn.clicked.connect(lambda: self.handle_img_tool("Rebuild As"))
        img_row1.addWidget(rebuild_btn)
        img_row1.addWidget(rebuild_all_btn)
        img_row1.addWidget(rebuild_as_btn)
        
        img_row2 = QHBoxLayout()
        merge_btn = QPushButton("🔗 Merge IMG")
        merge_btn.clicked.connect(lambda: self.handle_img_tool("Merge IMG"))
        split_btn = QPushButton("✂️ Split IMG")
        split_btn.clicked.connect(lambda: self.handle_img_tool("Split IMG"))
        convert_btn = QPushButton("🔄 Convert Format")
        convert_btn.clicked.connect(lambda: self.handle_img_tool("Convert Format"))
        img_row2.addWidget(merge_btn)
        img_row2.addWidget(split_btn)
        img_row2.addWidget(convert_btn)
        
        img_row3 = QHBoxLayout()
        optimize_btn = QPushButton("⚡ Optimize")
        optimize_btn.clicked.connect(lambda: self.handle_img_tool("Optimize IMG"))
        defrag_btn = QPushButton("🧹 Defragment")
        defrag_btn.clicked.connect(lambda: self.handle_img_tool("Defragment IMG"))
        compress_btn = QPushButton("🗜️ Compress")
        compress_btn.clicked.connect(lambda: self.handle_img_tool("Compress IMG"))
        img_row3.addWidget(optimize_btn)
        img_row3.addWidget(defrag_btn)
        img_row3.addWidget(compress_btn)
        
        img_row4 = QHBoxLayout()
        backup_btn = QPushButton("📋 Backup")
        backup_btn.clicked.connect(lambda: self.handle_img_tool("Backup IMG"))
        compare_btn = QPushButton("⚖️ Compare")
        compare_btn.clicked.connect(lambda: self.handle_img_tool("Compare IMG Files"))
        img_row4.addWidget(backup_btn)
        img_row4.addWidget(compare_btn)
        img_row4.addStretch()
        
        img_ops_group.add_layout(img_row1)
        img_ops_group.add_layout(img_row2)
        img_ops_group.add_layout(img_row3)
        img_ops_group.add_layout(img_row4)
        parent_layout.addWidget(img_ops_group)
    
    def create_import_export_group(self, parent_layout):
        """Create Import/Export tool group"""
        import_export_group = CollapsibleGroupBox("📤 Import/Export")
        import_export_group.set_accordion_parent(self)
        self.collapsible_groups.append(import_export_group)
        
        import_row1 = QHBoxLayout()
        import_files_btn = QPushButton("📥 Import Files")
        import_files_btn.clicked.connect(lambda: self.handle_img_tool("Import Files"))
        import_ide_btn = QPushButton("📥 Import via IDE")
        import_ide_btn.clicked.connect(lambda: self.handle_img_tool("Import via IDE"))
        export_selected_btn = QPushButton("📤 Export Selected")
        export_selected_btn.clicked.connect(lambda: self.handle_img_tool("Export Selected"))
        import_row1.addWidget(import_files_btn)
        import_row1.addWidget(import_ide_btn)
        import_row1.addWidget(export_selected_btn)
        
        import_row2 = QHBoxLayout()
        export_ide_btn = QPushButton("📤 Export via IDE")
        export_ide_btn.clicked.connect(lambda: self.handle_img_tool("Export via IDE"))
        export_all_btn = QPushButton("📤 Export All")
        export_all_btn.clicked.connect(lambda: self.handle_img_tool("Export All"))
        quick_export_btn = QPushButton("⚡ Quick Export")
        quick_export_btn.clicked.connect(lambda: self.handle_img_tool("Quick Export"))
        import_row2.addWidget(export_ide_btn)
        import_row2.addWidget(export_all_btn)
        import_row2.addWidget(quick_export_btn)
        
        import_row3 = QHBoxLayout()
        dump_all_btn = QPushButton("💾 Dump All")
        dump_all_btn.clicked.connect(lambda: self.handle_img_tool("Dump All"))
        import_row3.addWidget(dump_all_btn)
        import_row3.addStretch()
        import_row3.addStretch()
        
        import_export_group.add_layout(import_row1)
        import_export_group.add_layout(import_row2)
        import_export_group.add_layout(import_row3)
        parent_layout.addWidget(import_export_group)
    
    def create_entry_management_group(self, parent_layout):
        """Create Entry Management tool group"""
        entry_group = CollapsibleGroupBox("📝 Entry Management")
        entry_group.set_accordion_parent(self)
        self.collapsible_groups.append(entry_group)
        
        entry_row1 = QHBoxLayout()
        remove_selected_btn = QPushButton("🗑️ Remove Selected")
        remove_selected_btn.clicked.connect(lambda: self.handle_img_tool("Remove Selected"))
        remove_ide_btn = QPushButton("🗑️ Remove via IDE")
        remove_ide_btn.clicked.connect(lambda: self.handle_img_tool("Remove via IDE"))
        rename_btn = QPushButton("✏️ Rename Entry")
        rename_btn.clicked.connect(lambda: self.handle_img_tool("Rename Entry"))
        entry_row1.addWidget(remove_selected_btn)
        entry_row1.addWidget(remove_ide_btn)
        entry_row1.addWidget(rename_btn)
        
        entry_row2 = QHBoxLayout()
        replace_btn = QPushButton("🔄 Replace Entry")
        replace_btn.clicked.connect(lambda: self.handle_img_tool("Replace Entry"))
        duplicate_btn = QPushButton("📋 Duplicate Entry")
        duplicate_btn.clicked.connect(lambda: self.handle_img_tool("Duplicate Entry"))
        save_entry_btn = QPushButton("💾 Save Entry")
        save_entry_btn.clicked.connect(lambda: self.handle_img_tool("Save Entry"))
        entry_row2.addWidget(replace_btn)
        entry_row2.addWidget(duplicate_btn)
        entry_row2.addWidget(save_entry_btn)
        
        entry_group.add_layout(entry_row1)
        entry_group.add_layout(entry_row2)
        parent_layout.addWidget(entry_group)
    
    def create_selection_tools_group(self, parent_layout):
        """Create Selection Tools group"""
        selection_group = CollapsibleGroupBox("✅ Selection Tools")
        selection_group.set_accordion_parent(self)
        self.collapsible_groups.append(selection_group)
        
        selection_row1 = QHBoxLayout()
        select_all_btn = QPushButton("✅ Select All")
        select_all_btn.clicked.connect(lambda: self.handle_img_tool("Select All"))
        select_inverse_btn = QPushButton("🔄 Select Inverse")
        select_inverse_btn.clicked.connect(lambda: self.handle_img_tool("Select Inverse"))
        select_none_btn = QPushButton("❌ Select None")
        select_none_btn.clicked.connect(lambda: self.handle_img_tool("Select None"))
        selection_row1.addWidget(select_all_btn)
        selection_row1.addWidget(select_inverse_btn)
        selection_row1.addWidget(select_none_btn)
        
        selection_row2 = QHBoxLayout()
        sort_btn = QPushButton("📊 Sort Entries")
        sort_btn.clicked.connect(lambda: self.handle_img_tool("Sort Entries"))
        pin_btn = QPushButton("📌 Pin Selected")
        pin_btn.clicked.connect(lambda: self.handle_img_tool("Pin Selected"))
        selection_row2.addWidget(sort_btn)
        selection_row2.addWidget(pin_btn)
        selection_row2.addStretch()
        
        selection_group.add_layout(selection_row1)
        selection_group.add_layout(selection_row2)
        parent_layout.addWidget(selection_group)
    
    def collapse_other_groups(self, expanded_group):
        """Collapse all other collapsible groups when one is expanded (accordion behavior)"""
        for group in self.collapsible_groups:
            if group != expanded_group and group.isChecked():
                group.setChecked(False)
    
    def handle_img_tool(self, tool_name):
        """Handle IMG tool action"""
        # Emit signal with tool action
        self.tool_action.emit("img_tool", tool_name)
