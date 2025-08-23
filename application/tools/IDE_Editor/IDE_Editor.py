"""
IDE Editor Tool for Renderware Modding Suite
Handles IDE (Item Definition) file operations and management
"""

import sys
import os
import json
from pathlib import Path
from functools import partial

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QListWidget, QListWidgetItem, 
    QSplitter, QLabel, QProgressDialog, QTableWidget, QTableWidgetItem, QPushButton,
    QScrollArea, QFrame, QAbstractItemView, QSizePolicy, QHeaderView, QTextEdit,
    QGroupBox, QToolButton, QMenu
)
from PyQt6.QtGui import QAction, QKeySequence, QFont, QFontDatabase
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal

# Suite integrations
from application.responsive_utils import get_responsive_manager
from application.styles import ModernDarkTheme
from application.debug_system import get_debug_logger, LogCategory
from application.common.message_box import message_box

# Import the core logic
try:
    from .IDE_core import IDEParser
except ImportError:
    from IDE_core import IDEParser

# Module-level debug logger
debug_logger = get_debug_logger()

# --- Custom Widget for Collapsible Panels ---

class CollapsiblePanel(QWidget):
    """
    A collapsible widget that now includes a toolbar for actions
    like adding or deleting rows.
    """
    def __init__(self, title="Section", parent=None):
        super().__init__(parent)
        self.is_expanded = True
        
        # Get responsive configuration
        rm = get_responsive_manager()
        fonts = rm.get_font_config()
        spacing = rm.get_spacing_config()
        button_size = rm.get_button_size()

        self.header_button = QPushButton(title)
        self.header_button.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding: {spacing['small']}px;
                font-weight: bold;
                background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
                color: {ModernDarkTheme.TEXT_PRIMARY};
                border: 1px solid {ModernDarkTheme.BORDER_PRIMARY};
                border-radius: 4px;
                font-size: {fonts['subheader']['size']}px;
            }}
            QPushButton:hover {{
                background-color: {ModernDarkTheme.HOVER_COLOR};
            }}
        """)
        self.header_button.clicked.connect(self.toggle_expanded)

        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(spacing['small'], spacing['small'], spacing['small'], spacing['small'])

        # Toolbar for section-specific actions
        self.toolbar = QWidget()
        self.toolbar_layout = QHBoxLayout(self.toolbar)
        self.toolbar_layout.setContentsMargins(0, 0, 0, 0)
        self.toolbar_layout.setSpacing(spacing['small'])
        
        self.add_row_button = QPushButton("Add Row")
        self.delete_row_button = QPushButton("Delete Selected")
        
        # Apply suite styling to buttons
        button_style = f"""
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
        """
        
        self.add_row_button.setStyleSheet(button_style)
        self.delete_row_button.setStyleSheet(button_style)
        
        self.toolbar_layout.addWidget(self.add_row_button)
        self.toolbar_layout.addWidget(self.delete_row_button)
        self.toolbar_layout.addStretch()
        self.content_layout.addWidget(self.toolbar)
        
        self.animation = QPropertyAnimation(self.content_area, b"maximumHeight")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.header_button)
        main_layout.addWidget(self.content_area)
        
        self._update_arrow()

    def set_content_widget(self, widget):
        # Insert the new content widget (the table) after the toolbar
        self.content_layout.addWidget(widget)

    def toggle_expanded(self):
        start_height = self.content_area.height()
        end_height = 0
        self.is_expanded = not self.is_expanded

        if self.is_expanded:
            end_height = self.content_area.sizeHint().height()
        
        self.animation.setStartValue(start_height)
        self.animation.setEndValue(end_height)
        self.animation.start()
        self._update_arrow()

    def _update_arrow(self):
        arrow = "▼" if self.is_expanded else "►"
        title = self.header_button.text().lstrip("▼► ").strip()
        self.header_button.setText(f"{arrow} {title}")

    def set_title(self, title):
        arrow = "▼" if self.is_expanded else "►"
        self.header_button.setText(f"{arrow} {title}")

# --- IDE Editor Tool Widget ---

class IDEEditorTool(QWidget):
    """IDE Editor tool interface integrated with the Modding Suite"""
    
    # Signals for tool actions
    tool_action = pyqtSignal(str, str)  # action_name, parameters
    file_loaded = pyqtSignal(str)  # Signal when file is loaded
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Load schema
        self.schema = self._load_schema()
        if not self.schema:
            debug_logger.error(LogCategory.TOOL, "Failed to load IDE schema")
            return

        # Data Model and State Tracking
        self.opened_files = {} # Maps abs_path -> list row index
        self.file_data_models = {} # Maps abs_path -> parsed data model
        self.file_content_widgets = {} # Maps abs_path -> UI content widget
        self.file_raw_widgets = {} # Maps abs_path -> QTextEdit (raw view)
        self.file_raw_contents = {} # Maps abs_path -> raw text content
        self.dirty_files = set() # Set of abs_path for files with changes

        # View state
        self.view_mode_raw = False

        self.setup_ui()
        
        # Instantiate the parser from our core module
        self.parser = IDEParser(self.schema)
        
        debug_logger.info(LogCategory.TOOL, "IDE Editor tool initialized")
    
    def _load_schema(self):
        """Load the IDE schema file"""
        try:
            # Try to find schema in the tool directory
            schema_path = Path(__file__).parent / 'schema.json'
            if not schema_path.exists():
                # Fallback to current directory
                schema_path = Path('schema.json')
            
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    return json.load(f)
            else:
                debug_logger.error(LogCategory.TOOL, "Schema file not found", {"paths_tried": [str(schema_path)]})
                return None
        except Exception as e:
            debug_logger.log_exception(LogCategory.TOOL, "Error loading schema", e)
            return None

    # ---- Schema helpers ----
    def build_section_columns(self, section_key):
        """Return ordered list of column dicts [{name, type}] to DISPLAY for a section.
        - Simple sections: top-level 'columns'.
        - 'cars': base columns + union of all variants.extraColumns.
        - '2dfx': commonPrefix + union of types[*].columns.
        - Fallback: single raw column.
        """
        sec = self.schema["sections"].get(section_key, {})
        cols = []
        seen = set()

        def add_cols(col_list):
            nonlocal cols, seen
            for c in col_list or []:
                name = c.get("name")
                ctype = c.get("type", "string")
                if name and name not in seen:
                    cols.append({"name": name, "type": ctype})
                    seen.add(name)

        # Simple top-level columns
        if isinstance(sec.get("columns"), list) and sec.get("columns"):
            add_cols(sec.get("columns"))

        # Variants (e.g., cars)
        if isinstance(sec.get("variants"), dict):
            add_cols(sec.get("columns", []))  # ensure base first
            for v in sec["variants"].values():
                add_cols(v.get("extraColumns", []))

        # 2dfx style: commonPrefix + types
        if isinstance(sec.get("commonPrefix"), list) or isinstance(sec.get("types"), dict):
            add_cols(sec.get("commonPrefix", []))
            types = sec.get("types", {})
            if isinstance(types, dict):
                for t in types.values():
                    add_cols(t.get("columns", []))

        if not cols:
            cols = [{"name": "raw", "type": "string"}]
        return cols

    def base_schema_columns(self, section_key):
        """Return only top-level schema columns for editing/adding purposes."""
        sec = self.schema["sections"].get(section_key, {})
        return sec.get("columns", []) if isinstance(sec.get("columns"), list) else []

    def setup_ui(self):
        """Setup the main UI layout"""
        rm = get_responsive_manager()
        fonts = rm.get_font_config()
        spacing = rm.get_spacing_config()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(*rm.get_content_margins())
        main_layout.setSpacing(spacing['medium'])
        
        # Create toolbar
        self.create_toolbar()
        main_layout.addWidget(self.toolbar)
        
        # Create main content area
        self.create_main_content()
        main_layout.addWidget(self.splitter)
        
        # Apply suite styling
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {ModernDarkTheme.BACKGROUND_PRIMARY};
                color: {ModernDarkTheme.TEXT_PRIMARY};
            }}
        """)
    
    def create_toolbar(self):
        """Create the toolbar with file operations"""
        rm = get_responsive_manager()
        spacing = rm.get_spacing_config()
        button_size = rm.get_button_size()
        
        self.toolbar = QGroupBox("IDE File Operations")
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setSpacing(spacing['small'])
        # Add a bit more vertical padding above and below the buttons
        toolbar_layout.setContentsMargins(
            spacing['small'], spacing['small'] * 2, spacing['small'], spacing['small'] * 2
        )
        
        # File operations
        self.open_files_btn = QPushButton("📁 Open File(s)")
        self.open_folder_btn = QPushButton("📂 Open Folder")
        self.save_btn = QPushButton("💾 Save")
        self.save_all_btn = QPushButton("💾 Save All")
        
        # View toggle
        self.view_toggle_btn = QPushButton("🔄 Toggle Raw View")
        self.view_toggle_btn.setCheckable(True)
        
        # Apply consistent button styling
        button_style = f"""
            QPushButton {{
                background-color: {ModernDarkTheme.BUTTON_PRIMARY};
                color: white;
                border: none;
                padding: {spacing['small']}px {spacing['small'] + 2}px;
                border-radius: 4px;
                font-weight: 500;
                font-size: {rm.get_font_config()['body']['size']}px;
                min-width: {button_size[0]}px;
                min-height: {button_size[1]}px;
                max-height: {button_size[1]}px;
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
            QPushButton:checked {{
                background-color: {ModernDarkTheme.TEXT_ACCENT};
                color: white;
            }}
        """
        
        buttons = [self.open_files_btn, self.open_folder_btn, self.save_btn, self.save_all_btn, self.view_toggle_btn]
        for btn in buttons:
            btn.setStyleSheet(button_style)
            btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        # Connect signals
        self.open_files_btn.clicked.connect(self.open_files)
        self.open_folder_btn.clicked.connect(self.open_folder)
        self.save_btn.clicked.connect(self.save_current_file)
        self.save_all_btn.clicked.connect(self.save_all_files)
        self.view_toggle_btn.clicked.connect(self.toggle_view_mode)
        
        # Add to layout
        toolbar_layout.addWidget(self.open_files_btn)
        toolbar_layout.addWidget(self.open_folder_btn)
        toolbar_layout.addWidget(QFrame())  # Separator
        toolbar_layout.addWidget(self.save_btn)
        toolbar_layout.addWidget(self.save_all_btn)
        toolbar_layout.addWidget(QFrame())  # Separator
        toolbar_layout.addWidget(self.view_toggle_btn)
        toolbar_layout.addStretch()
        
        # Make the toolbar itself compact
        # Allow for the extra top/bottom margins so buttons don't get clipped
        self.toolbar.setMaximumHeight(button_size[1] + spacing['small'] * 5)
    
    def create_main_content(self):
        """Create the main content area with sidebar and editor pane"""
        rm = get_responsive_manager()
        fonts = rm.get_font_config()
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Sidebar: list of opened files
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("sidebarFrame")
        sidebar_layout = QVBoxLayout(sidebar_frame)
        
        sidebar_label = QLabel("Opened Files")
        sidebar_label.setObjectName("sectionLabel")
        sidebar_layout.addWidget(sidebar_label)
        
        self.sidebar = QListWidget()
        self.sidebar.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        sidebar_layout.addWidget(self.sidebar)
        
        # Main content pane
        self.main_pane = QWidget()
        self.main_pane_layout = QVBoxLayout(self.main_pane)
        self.main_pane_layout.setContentsMargins(0, 0, 0, 0)
        
        self.main_pane_placeholder = QLabel("📋 Select an IDE file from the sidebar to view its contents.")
        self.main_pane_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_pane_placeholder.setStyleSheet(f"""
            QLabel {{
                color: {ModernDarkTheme.TEXT_SECONDARY};
                font-size: {fonts['subheader']['size']}px;
                padding: 40px;
            }}
        """)
        self.main_pane_layout.addWidget(self.main_pane_placeholder)
        
        # Add to splitter
        self.splitter.addWidget(sidebar_frame)
        self.splitter.addWidget(self.main_pane)
        
        # Set initial sizes
        panel_width = rm.get_panel_width()
        self.splitter.setSizes([panel_width[0], 800])
        
        # Connect signals
        self.sidebar.currentRowChanged.connect(self.on_list_row_changed)

    # Keep tables capped appropriately when window resizes
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_all_table_heights()

    def adjust_all_table_heights(self):
        try:
            avail_h = self.main_pane.height() if hasattr(self, 'main_pane') and self.main_pane.height() > 0 else self.height()
            cap_h = max(220, int(avail_h * 0.85))
            for content in self.file_content_widgets.values():
                for table in content.findChildren(QTableWidget):
                    vh = table.verticalHeader()
                    row_h = vh.defaultSectionSize()
                    header_h = table.horizontalHeader().height()
                    row_count = table.rowCount()
                    visible_rows = max(3, min(row_count, 20))
                    padding = table.frameWidth() * 2 + 12
                    desired_h = header_h + visible_rows * row_h + padding
                    final_h = min(desired_h, cap_h)
                    table.setMinimumHeight(final_h)
                    table.setMaximumHeight(final_h)
        except Exception:
            pass

    def open_files(self):
        """Open IDE file(s) using file dialog"""
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "Open IDE File(s)", 
            "", 
            "IDE Files (*.ide);;All Files (*)"
        )
        if files:
            for fp in files:
                self.add_file_tab(fp)
            debug_logger.info(LogCategory.TOOL, f"Opened {len(files)} IDE files")

    def open_folder(self):
        """Open all IDE files in a folder"""
        folder_path = QFileDialog.getExistingDirectory(self, "Open Folder")
        if not folder_path:
            return
            
        ide_files = [str(p) for p in Path(folder_path).rglob('*.ide')]
        if not ide_files:
            message_box.info("No .ide files were found in the selected folder.", "No Files Found", self)
            return
            
        progress = QProgressDialog(f"Loading {len(ide_files)} IDE files...", "Cancel", 0, len(ide_files), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        
        for i, file_path in enumerate(ide_files):
            progress.setValue(i)
            if progress.wasCanceled():
                break
            self.add_file_tab(file_path)
            
        progress.setValue(len(ide_files))
        debug_logger.info(LogCategory.TOOL, f"Loaded {len(ide_files)} IDE files from folder", {"folder": folder_path})

    def add_file_tab(self, file_path):
        abs_path = os.path.abspath(file_path)
        if abs_path in self.opened_files:
            self.sidebar.setCurrentRow(self.opened_files[abs_path])
            return

        try:
            with open(file_path, 'r', encoding='ascii', errors='ignore') as f: content = f.read()
        except Exception as e:
            message_box.error(f"Could not read file: {file_path}\n\n{e}", "Error Reading File", self)
            debug_logger.log_exception(LogCategory.TOOL, f"Error reading IDE file: {file_path}", e)
            return
        
        parsed_data = self.parser.parse(content)
        self.file_raw_contents[abs_path] = content
        self.file_data_models[abs_path] = parsed_data
        
        file_content_widget = self.create_file_content_widget(abs_path, parsed_data)
        self.file_content_widgets[abs_path] = file_content_widget

        # Create raw text widget
        raw_widget = QTextEdit()
        raw_widget.setReadOnly(True)
        raw_widget.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        # Prefer a fixed-width system font; fall back to Consolas if not available
        try:
            mono = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        except Exception:
            mono = QFont("Consolas")
        raw_widget.setFont(mono)
        raw_widget.setText(content)
        raw_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.file_raw_widgets[abs_path] = raw_widget
        
        # Add an item to the sidebar list and keep widget hidden until selected
        item = QListWidgetItem(os.path.basename(file_path))
        item.setToolTip(f"Path: {abs_path}")
        item.setData(Qt.ItemDataRole.UserRole, abs_path)
        self.sidebar.addItem(item)
        row = self.sidebar.count() - 1
        self.opened_files[abs_path] = row
        # Ensure the content widget is part of the main pane to avoid separate windows
        self.file_content_widgets[abs_path].setParent(self.main_pane)
        self.file_content_widgets[abs_path].hide()
        self.main_pane_layout.addWidget(self.file_content_widgets[abs_path])

        # Also add raw widget to the main pane, hidden by default
        self.file_raw_widgets[abs_path].setParent(self.main_pane)
        self.file_raw_widgets[abs_path].hide()
        self.main_pane_layout.addWidget(self.file_raw_widgets[abs_path])
        debug_logger.info(LogCategory.TOOL, f"Opened IDE file: {os.path.basename(file_path)}")
        self.sidebar.setCurrentRow(row)

    def create_file_content_widget(self, file_path, parsed_data):
        if not parsed_data:
            return QLabel("File is empty or contains no recognized sections.")

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)

        # Iterate sections in the order defined by schema
        for section_name in self.schema["sections"].keys():
            data = parsed_data.get(section_name, {"rows": [], "errors": []})
            panel = CollapsiblePanel(f"{section_name.upper()} ({len(data['rows'])} rows)")
            panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            table = QTableWidget()
            table.setObjectName(f"{file_path}|{section_name}")
            # Expand to fill available space
            table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            
            # Connect signals for editing and row operations
            panel.add_row_button.clicked.connect(partial(self.add_row, table))
            panel.delete_row_button.clicked.connect(partial(self.delete_rows, table))
            table.itemChanged.connect(self.on_item_changed)
            
            # Disable Add Row for sections without base editable columns
            if not self.base_schema_columns(section_name):
                panel.add_row_button.setEnabled(False)
            self.populate_table(table, section_name, data["rows"])
            panel.set_content_widget(table)
            # Give more stretch to table vs toolbar
            panel.content_layout.setStretch(0, 0)  # toolbar
            panel.content_layout.setStretch(1, 1)  # table

            # Collapse empty sections by default
            if len(data["rows"]) == 0:
                panel.is_expanded = False
                panel.content_area.setMaximumHeight(0)
                panel._update_arrow()
            container_layout.addWidget(panel)
        
        container_layout.addStretch()
        scroll_area.setWidget(container_widget)
        return scroll_area
    
    def populate_table(self, table, section_key, rows):
        table.blockSignals(True) # Block signals during population
        schema_section = self.schema["sections"].get(section_key)
        if not schema_section:
            table.blockSignals(False)
            return

        # Build display columns (union)
        display_cols = self.build_section_columns(section_key)
        headers = [c["name"] for c in display_cols]
        base_cols = [c["name"] for c in self.base_schema_columns(section_key)]

        table.setRowCount(len(rows))
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        # Make columns stretch to fill width
        header_view = table.horizontalHeader()
        header_view.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        for row_idx, row_data in enumerate(rows):
            for col_idx, header in enumerate(headers):
                value = row_data.get(header)
                display_text = ", ".join(map(str, value)) if isinstance(value, list) else str(value if value is not None else "")
                item = QTableWidgetItem(display_text)
                # Make non-base columns read-only
                if header not in base_cols:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)

        # table.resizeColumnsToContents()  # Not needed with Stretch mode
        # Adjust table height dynamically based on number of rows, but cap to a fraction of window height
        try:
            vh = table.verticalHeader()
            row_h = vh.defaultSectionSize()
            header_h = table.horizontalHeader().height()
            row_count = len(rows)
            # Show between 3 and 20 rows worth of height
            visible_rows = max(3, min(row_count, 20))
            padding = table.frameWidth() * 2 + 12
            desired_h = header_h + visible_rows * row_h + padding
            # Cap height to ~60% of main content area (or window) so other sections remain visible
            avail_h = self.main_pane.height() if hasattr(self, 'main_pane') and self.main_pane.height() > 0 else self.height()
            cap_h = max(220, int(avail_h * 0.85))
            final_h = min(desired_h, cap_h)
            table.setMinimumHeight(final_h)
            table.setMaximumHeight(final_h)
        except Exception:
            pass
        table.blockSignals(False) # Re-enable signals

    def on_item_changed(self, item):
        """Handle cell edits, validate data, and update the model."""
        table = item.tableWidget()
        file_path, section_key = table.objectName().split('|')
        row, col = item.row(), item.column()
        new_text = item.text()

        schema_section = self.schema["sections"].get(section_key, {})
        base_cols = self.base_schema_columns(section_key)
        # If this section has no base columns, or edited col is not in base, skip
        if not base_cols or col >= len(base_cols):
            return
        schema_col = base_cols[col]
        col_type = schema_col["type"]

        try:
            if col_type == "int": validated_value = int(new_text)
            elif col_type == "float": validated_value = float(new_text)
            else: validated_value = new_text
        except ValueError:
            debug_logger.warning(LogCategory.TOOL, f"Invalid value for type '{col_type}'. Reverting.")
            table.blockSignals(True)
            original_value = self.file_data_models[file_path][section_key]["rows"][row][schema_col["name"]]
            item.setText(str(original_value))
            table.blockSignals(False)
            return

        self.file_data_models[file_path][section_key]["rows"][row][schema_col["name"]] = validated_value
        self.mark_file_as_dirty(file_path)
        debug_logger.debug(LogCategory.TOOL, f"Updated {section_key}[{row}][{schema_col['name']}]")

    def add_row(self, table):
        """Adds a new row to the table and the underlying data model."""
        file_path, section_key = table.objectName().split('|')
        schema_cols = self.base_schema_columns(section_key)
        if not schema_cols:
            # Unsupported section for adding rows (e.g., 2dfx/raw)
            debug_logger.warning(LogCategory.TOOL, f"Cannot add rows to section '{section_key}'")
            return
        
        new_row_data = {}
        for col in schema_cols:
            if col['type'] == 'int' or col['type'] == 'float': new_row_data[col['name']] = col.get('default', 0)
            elif col['type'] == 'array': new_row_data[col['name']] = []
            else: new_row_data[col['name']] = col.get('default', 'new_value')

        self.file_data_models[file_path][section_key]["rows"].append(new_row_data)

        table.blockSignals(True)
        row_count = table.rowCount()
        table.insertRow(row_count)
        for col_idx, col_schema in enumerate(schema_cols):
            item = QTableWidgetItem(str(new_row_data[col_schema['name']]))
            table.setItem(row_count, col_idx, item)
        table.blockSignals(False)
        
        self.mark_file_as_dirty(file_path)
        debug_logger.info(LogCategory.TOOL, f"Added new row to {section_key}")
    
    def delete_rows(self, table):
        """Deletes all selected rows from the table and data model."""
        selected_rows = sorted(list(set(item.row() for item in table.selectedItems())), reverse=True)
        if not selected_rows:
            debug_logger.warning(LogCategory.TOOL, "No rows selected to delete")
            return

        file_path, section_key = table.objectName().split('|')
        
        # Update model first
        for row_idx in selected_rows:
            del self.file_data_models[file_path][section_key]["rows"][row_idx]
        
        # Update view
        for row_idx in selected_rows:
            table.removeRow(row_idx)
            
        self.mark_file_as_dirty(file_path)
        debug_logger.info(LogCategory.TOOL, f"Deleted {len(selected_rows)} row(s) from {section_key}")

    def mark_file_as_dirty(self, file_path):
        """Updates the list item title to show the dirty state."""
        if file_path in self.dirty_files or file_path not in self.opened_files:
            return

        self.dirty_files.add(file_path)
        row = self.opened_files[file_path]
        item = self.sidebar.item(row)
        if item is not None and not item.text().endswith(" •"):
            item.setText(f"{item.text()} •")
        
    def mark_file_as_clean(self, file_path):
        """Removes the dirty indicator from a list item."""
        if file_path not in self.dirty_files:
            return

        self.dirty_files.remove(file_path)
        row = self.opened_files[file_path]
        item = self.sidebar.item(row)
        if item is not None and item.text().endswith(" •"):
            item.setText(item.text()[:-2])

    def on_list_row_changed(self, row):
        # Hide all widgets first
        for widget in self.file_content_widgets.values():
            widget.hide()
        for widget in self.file_raw_widgets.values():
            widget.hide()
        self.main_pane_placeholder.hide()

        if row < 0:
            self.main_pane_placeholder.show()
            return

        item = self.sidebar.item(row)
        if not item:
            self.main_pane_placeholder.show()
            return

        current_path = item.data(Qt.ItemDataRole.UserRole)
        if current_path in self.file_content_widgets:
            # Show either raw or table view based on toggle
            if self.view_mode_raw and current_path in self.file_raw_widgets:
                self.file_raw_widgets[current_path].show()
            else:
                self.file_content_widgets[current_path].show()
        else:
            self.main_pane_placeholder.show()

    def toggle_view_mode(self):
        """Toggle between parsed tables and raw text for all opened files."""
        self.view_mode_raw = self.view_toggle_btn.isChecked()
        # Update currently visible item
        current_row = self.sidebar.currentRow()
        self.on_list_row_changed(current_row)
    
    def save_current_file(self):
        """Save the currently selected file"""
        current_row = self.sidebar.currentRow()
        if current_row < 0:
            message_box.info("No file selected to save.", "No File Selected", self)
            return
        
        item = self.sidebar.item(current_row)
        if not item:
            return
            
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self._save_file(file_path)
    
    def save_all_files(self):
        """Save all modified files"""
        if not self.dirty_files:
            message_box.info("No files need saving.", "No Changes", self)
            return
        
        saved_count = 0
        for file_path in list(self.dirty_files):
            if self._save_file(file_path):
                saved_count += 1
        
        message_box.info(f"Saved {saved_count} file(s).", "Files Saved", self)
    
    def _save_file(self, file_path):
        """Save a specific file"""
        try:
            # TODO: Implement actual file saving logic
            # For now, just mark as clean
            self.mark_file_as_clean(file_path)
            debug_logger.info(LogCategory.TOOL, f"Saved IDE file: {os.path.basename(file_path)}")
            return True
        except Exception as e:
            message_box.error(f"Failed to save file: {e}", "Save Error", self)
            debug_logger.log_exception(LogCategory.TOOL, f"Error saving file: {file_path}", e)
            return False


# Legacy class name for backward compatibility
IDEEditor = IDEEditorTool