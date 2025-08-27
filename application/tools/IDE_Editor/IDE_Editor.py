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
    QGroupBox, QToolButton, QMenu, QDialog, QComboBox, QSpinBox, QCheckBox, QTabWidget,
    QMessageBox
)
from PyQt6.QtGui import QAction, QKeySequence, QFont, QFontDatabase
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QEvent

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
        """Create a categorized toolbar with dropdown menus: File, Save, Tools, Raw."""
        rm = get_responsive_manager()
        spacing = rm.get_spacing_config()
        button_size = rm.get_button_size()

        self.toolbar = QGroupBox("IDE Operations")
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setSpacing(spacing['small'])
        toolbar_layout.setContentsMargins(spacing['medium'], spacing['small'], spacing['medium'], spacing['small'])

        # Keep an internal raw toggle button for logic; not added to layout
        self.view_toggle_btn = QPushButton("Raw")
        self.view_toggle_btn.setCheckable(True)

        # Category buttons as QToolButtons with menus
        self.file_menu_btn = QToolButton()
        self.file_menu_btn.setText("File ▾")
        self.file_menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.file_menu_btn.installEventFilter(self)

        self.save_menu_btn = QToolButton()
        self.save_menu_btn.setText("Save ▾")
        self.save_menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.save_menu_btn.installEventFilter(self)

        self.tools_menu_btn = QToolButton()
        self.tools_menu_btn.setText("Tools ▾")
        self.tools_menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.tools_menu_btn.installEventFilter(self)

        self.raw_menu_btn = QToolButton()
        self.raw_menu_btn.setText("Raw ▾")
        self.raw_menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.raw_menu_btn.installEventFilter(self)

        # Enable hover tracking and apply category styling for menu buttons
        for btn in (self.file_menu_btn, self.save_menu_btn, self.tools_menu_btn, self.raw_menu_btn):
            btn.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self._apply_category_button_styling([
            self.file_menu_btn,
            self.save_menu_btn,
            self.tools_menu_btn,
            self.raw_menu_btn,
        ])

        # Build menus
        file_menu = QMenu(self)
        file_menu.addAction("Open Files…", self.open_files)
        file_menu.addAction("Open Folder…", self.open_folder)
        file_menu.addSeparator()
        file_menu.addAction("Close Current", self.close_current_file)
        file_menu.addAction("Close All", self.close_all_files)
        self.file_menu_btn.setMenu(file_menu)

        save_menu = QMenu(self)
        save_menu.addAction("Save Current", self.save_current_file)
        save_menu.addAction("Save All", self.save_all_files)
        self.save_menu_btn.setMenu(save_menu)

        tools_menu = QMenu(self)
        tools_menu.addAction("Validate Current", self.validate_current_file)
        tools_menu.addAction("Validate All", self.validate_all_files)
        tools_menu.addSeparator()
        tools_menu.addAction("ID Manager", self.open_id_manager)
        tools_menu.addAction("Statistics", self.show_statistics)
        self.tools_menu_btn.setMenu(tools_menu)

        raw_menu = QMenu(self)
        raw_action = raw_menu.addAction("Raw View")
        raw_action.setCheckable(True)
        raw_action.setChecked(False)
        # Sync QAction with internal toggle button/state
        def _on_raw_toggled(checked):
            self.view_toggle_btn.setChecked(checked)
            self.toggle_view_mode()
        raw_action.toggled.connect(_on_raw_toggled)
        self.raw_menu_btn.setMenu(raw_menu)

        # Layout with subtle separators between groups
        toolbar_layout.addWidget(self.file_menu_btn)
        toolbar_layout.addWidget(self._create_separator())
        toolbar_layout.addWidget(self.save_menu_btn)
        toolbar_layout.addWidget(self._create_separator())
        toolbar_layout.addWidget(self.tools_menu_btn)
        toolbar_layout.addWidget(self._create_separator())
        toolbar_layout.addWidget(self.raw_menu_btn)
        toolbar_layout.addStretch()

        # Compact height
        self.toolbar.setMaximumHeight(button_size[1] + spacing['medium'] * 2)
    
    def _create_button_group(self, title):
        """Create a labeled button group"""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 10px;
                color: {ModernDarkTheme.TEXT_SECONDARY};
                border: 1px solid {ModernDarkTheme.BORDER_SECONDARY};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 8px;
                min-height: 50px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
            }}
        """)
        layout = QHBoxLayout(group)
        layout.setSpacing(4)
        layout.setContentsMargins(6, 12, 6, 6)
        group.setLayout(layout)
        return group
    
    def _create_separator(self):
        """Create an elegant vertical separator"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet(f"""
            QFrame {{
                color: {ModernDarkTheme.BORDER_SECONDARY};
                margin: 4px 0px;
            }}
        """)
        return separator
    
    def _apply_main_button_styling(self, buttons):
        """Apply styling to main action buttons"""
        rm = get_responsive_manager()
        spacing = rm.get_spacing_config()
        button_size = rm.get_button_size()
        
        button_style = f"""
            QPushButton {{
                background-color: {ModernDarkTheme.BUTTON_PRIMARY};
                color: white;
                border: none;
                padding: {spacing['small']}px {spacing['medium']}px;
                border-radius: 5px;
                font-weight: 500;
                font-size: {rm.get_font_config()['body']['size']}px;
                min-width: {button_size[0] - 20}px;
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
                border: 2px solid {ModernDarkTheme.BORDER_ACCENT};
            }}
        """
        
        for btn in buttons:
            btn.setStyleSheet(button_style)
            btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
    
    def _apply_dropdown_styling(self, dropdown_buttons):
        """Apply styling to small dropdown buttons"""
        rm = get_responsive_manager()
        spacing = rm.get_spacing_config()
        
        dropdown_style = f"""
            QToolButton {{
                background-color: {ModernDarkTheme.BACKGROUND_SECONDARY};
                color: {ModernDarkTheme.TEXT_PRIMARY};
                border: 1px solid {ModernDarkTheme.BORDER_SECONDARY};
                border-radius: 4px;
                padding: {spacing['small']}px;
                font-weight: bold;
                font-size: 10px;
                min-width: 18px;
                max-width: 18px;
                min-height: 24px;
                max-height: 24px;
            }}
            QToolButton:hover {{
                background-color: {ModernDarkTheme.HOVER_COLOR};
                border-color: {ModernDarkTheme.BORDER_PRIMARY};
            }}
            QToolButton:pressed {{
                background-color: {ModernDarkTheme.BUTTON_PRESSED};
            }}
        """
        
        for btn in dropdown_buttons:
            btn.setStyleSheet(dropdown_style)
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    
    def _apply_category_button_styling(self, buttons):
        """Apply styling to the main category QToolButtons (File, Save, Tools, Raw)."""
        rm = get_responsive_manager()
        spacing = rm.get_spacing_config()
        button_size = rm.get_button_size()
        style = f"""
            QToolButton {{
                background-color: {ModernDarkTheme.BUTTON_PRIMARY};
                color: white;
                border: none;
                padding: {spacing['small']}px {spacing['medium']}px;
                border-radius: 5px;
                font-weight: 500;
                font-size: {rm.get_font_config()['body']['size']}px;
                min-height: {button_size[1]}px;
                max-height: {button_size[1]}px;
            }}
            QToolButton:hover {{
                background-color: {ModernDarkTheme.BUTTON_HOVER};
            }}
            QToolButton:pressed {{
                background-color: {ModernDarkTheme.BUTTON_PRESSED};
            }}
        """
        for btn in buttons:
            btn.setStyleSheet(style)
            btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def eventFilter(self, obj, event):
        """Open category menus on hover; fall back to default handling otherwise."""
        try:
            if isinstance(obj, QToolButton) and obj.menu() is not None:
                if event.type() in (QEvent.Type.Enter, QEvent.Type.HoverEnter):
                    # Show menu on hover
                    obj.showMenu()
        except Exception:
            pass
        return super().eventFilter(obj, event)
    
    def close_current_file(self):
        """Close the currently selected file"""
        current_row = self.sidebar.currentRow()
        if current_row >= 0:
            file_path = list(self.opened_files.keys())[current_row]
            self._close_file(file_path)
    
    def close_all_files(self):
        """Close all opened files"""
        if not self.opened_files:
            return
            
        reply = QMessageBox.question(
            self,
            "Close all files?",
            f"Are you sure you want to close all {len(self.opened_files)} files?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Close files in reverse order to avoid index issues
            for file_path in list(self.opened_files.keys()):
                self._close_file(file_path)
    
    def _close_file(self, file_path):
        """Internal method to close a specific file"""
        if file_path not in self.opened_files:
            return
            
        # Remove from tracking
        row_index = self.opened_files[file_path]
        del self.opened_files[file_path]
        del self.file_data_models[file_path]
        
        # Remove from sidebar
        self.sidebar.takeItem(row_index)
        
        # Update indices for remaining files
        for fp, idx in self.opened_files.items():
            if idx > row_index:
                self.opened_files[fp] = idx - 1
        
        # Remove content widget if exists
        if file_path in self.file_content_widgets:
            widget = self.file_content_widgets[file_path]
            widget.setParent(None)
            del self.file_content_widgets[file_path]
        
        # Show placeholder if no files remain
        if not self.opened_files:
            self.main_pane_layout.addWidget(self.main_pane_placeholder)
            self.main_pane_placeholder.show()
        
        debug_logger.info(LogCategory.TOOL, f"Closed IDE file: {os.path.basename(file_path)}")
    
    def show_statistics(self):
        """Show comprehensive statistics for all opened files"""
        if not self.file_data_models:
            message_box.info("No files are currently opened.", "No Data", self)
            return
        
        stats = self._calculate_statistics()
        self._show_statistics_dialog(stats)
    
    def _calculate_statistics(self):
        """Calculate comprehensive statistics for all files"""
        stats = {
            'total_files': len(self.file_data_models),
            'total_entries': 0,
            'sections': {},
            'id_ranges': {'min': float('inf'), 'max': 0},
            'file_details': {}
        }
        
        for file_path, data_model in self.file_data_models.items():
            filename = os.path.basename(file_path)
            file_stats = {'entries': 0, 'sections': {}}
            
            for section_name, entries in data_model.items():
                if isinstance(entries, list):
                    entry_count = len(entries)
                    file_stats['entries'] += entry_count
                    file_stats['sections'][section_name] = entry_count
                    
                    # Update global section stats
                    if section_name not in stats['sections']:
                        stats['sections'][section_name] = 0
                    stats['sections'][section_name] += entry_count
                    
                    # Track ID ranges
                    for entry in entries:
                        if isinstance(entry, dict) and 'id' in entry:
                            try:
                                entry_id = int(entry['id'])
                                stats['id_ranges']['min'] = min(stats['id_ranges']['min'], entry_id)
                                stats['id_ranges']['max'] = max(stats['id_ranges']['max'], entry_id)
                            except (ValueError, TypeError):
                                pass
            
            stats['total_entries'] += file_stats['entries']
            stats['file_details'][filename] = file_stats
        
        # Handle case where no IDs were found
        if stats['id_ranges']['min'] == float('inf'):
            stats['id_ranges']['min'] = 0
        
        return stats
    
    def _show_statistics_dialog(self, stats):
        """Display statistics in a professional dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("📊 IDE Files Statistics")
        dialog.setModal(True)
        dialog.resize(600, 500)
        
        layout = QVBoxLayout(dialog)
        
        # Create tabbed view
        tab_widget = QTabWidget()
        
        # Overview tab
        overview_tab = QWidget()
        overview_layout = QVBoxLayout(overview_tab)
        
        overview_text = f"""
<h3>📋 Overview</h3>
<p><b>Total Files:</b> {stats['total_files']}</p>
<p><b>Total Entries:</b> {stats['total_entries']:,}</p>
<p><b>ID Range:</b> {stats['id_ranges']['min']:,} - {stats['id_ranges']['max']:,}</p>
<p><b>ID Span:</b> {stats['id_ranges']['max'] - stats['id_ranges']['min']:,}</p>

<h3>📂 Sections Summary</h3>
"""
        
        for section, count in sorted(stats['sections'].items()):
            percentage = (count / stats['total_entries']) * 100 if stats['total_entries'] > 0 else 0
            overview_text += f"<p><b>{section}:</b> {count:,} entries ({percentage:.1f}%)</p>"
        
        overview_label = QLabel(overview_text)
        overview_label.setWordWrap(True)
        overview_layout.addWidget(overview_label)
        
        tab_widget.addTab(overview_tab, "Overview")
        
        # File details tab
        details_tab = QWidget()
        details_layout = QVBoxLayout(details_tab)
        
        details_text = "<h3>📁 File Details</h3>"
        for filename, file_stats in stats['file_details'].items():
            details_text += f"<h4>{filename}</h4>"
            details_text += f"<p><b>Total Entries:</b> {file_stats['entries']:,}</p>"
            for section, count in file_stats['sections'].items():
                details_text += f"<p>&nbsp;&nbsp;<b>{section}:</b> {count:,}</p>"
            details_text += "<hr>"
        
        details_label = QLabel(details_text)
        details_label.setWordWrap(True)
        details_scroll = QScrollArea()
        details_scroll.setWidget(details_label)
        details_scroll.setWidgetResizable(True)
        details_layout.addWidget(details_scroll)
        
        tab_widget.addTab(details_tab, "File Details")
        
        layout.addWidget(tab_widget)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
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

        # Create raw text widget with editing capability
        raw_widget = QTextEdit()
        raw_widget.setReadOnly(False)  # Allow editing
        raw_widget.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        raw_widget.textChanged.connect(partial(self.on_raw_text_changed, abs_path))
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
        """Handle cell edits, validate data, and update the model and raw text."""
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
        self.update_raw_text_from_model(file_path)
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
        self.update_raw_text_from_model(file_path)
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
        self.update_raw_text_from_model(file_path)
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
    
    def on_raw_text_changed(self, file_path):
        """Handle raw text changes and update the data model and tables."""
        if file_path not in self.file_raw_widgets:
            return
            
        try:
            raw_widget = self.file_raw_widgets[file_path]
            new_content = raw_widget.toPlainText()
            
            # Parse the new content
            parsed_data = self.parser.parse(new_content)
            self.file_data_models[file_path] = parsed_data
            self.file_raw_contents[file_path] = new_content
            
            # Update all tables for this file
            self.refresh_tables_from_model(file_path)
            self.mark_file_as_dirty(file_path)
            
        except Exception as e:
            debug_logger.log_exception(LogCategory.TOOL, f"Error parsing raw text for {file_path}", e)

    def update_raw_text_from_model(self, file_path):
        """Update raw text widget from the current data model."""
        if file_path not in self.file_raw_widgets or file_path not in self.file_data_models:
            return
            
        try:
            # Serialize the current model back to IDE format
            serialized_content = self.parser.serialize(self.file_data_models[file_path])
            
            # Update the raw text widget without triggering change events
            raw_widget = self.file_raw_widgets[file_path]
            raw_widget.blockSignals(True)
            raw_widget.setPlainText(serialized_content)
            raw_widget.blockSignals(False)
            
            # Update stored content
            self.file_raw_contents[file_path] = serialized_content
            
        except Exception as e:
            debug_logger.log_exception(LogCategory.TOOL, f"Error updating raw text for {file_path}", e)

    def refresh_tables_from_model(self, file_path):
        """Refresh all table widgets for a file from the current data model."""
        if file_path not in self.file_content_widgets or file_path not in self.file_data_models:
            return
            
        try:
            content_widget = self.file_content_widgets[file_path]
            parsed_data = self.file_data_models[file_path]
            
            # Find all tables in the content widget and refresh them
            for table in content_widget.findChildren(QTableWidget):
                object_name = table.objectName()
                if '|' in object_name:
                    _, section_key = object_name.split('|')
                    section_data = parsed_data.get(section_key, {"rows": [], "errors": []})
                    self.populate_table(table, section_key, section_data["rows"])
                    
        except Exception as e:
            debug_logger.log_exception(LogCategory.TOOL, f"Error refreshing tables for {file_path}", e)

    def _save_file(self, file_path):
        """Save a specific file with all changes."""
        try:
            if file_path not in self.file_data_models:
                debug_logger.warning(LogCategory.TOOL, f"No data model found for {file_path}")
                return False
                
            # Serialize the current data model to IDE format
            serialized_content = self.parser.serialize(self.file_data_models[file_path])
            
            # Write to file
            with open(file_path, 'w', encoding='ascii', errors='ignore') as f:
                f.write(serialized_content)
            
            # Update stored content and mark as clean
            self.file_raw_contents[file_path] = serialized_content
            
            # Update raw text widget if it exists
            if file_path in self.file_raw_widgets:
                raw_widget = self.file_raw_widgets[file_path]
                raw_widget.blockSignals(True)
                raw_widget.setPlainText(serialized_content)
                raw_widget.blockSignals(False)
            
            self.mark_file_as_clean(file_path)
            debug_logger.info(LogCategory.TOOL, f"Saved IDE file: {os.path.basename(file_path)}")
            return True
            
        except Exception as e:
            message_box.error(f"Failed to save file: {e}", "Save Error", self)
            debug_logger.log_exception(LogCategory.TOOL, f"Error saving file: {file_path}", e)
            return False

    def validate_current_file(self):
        """Validate the currently selected file for duplicate IDs and objects."""
        current_row = self.sidebar.currentRow()
        if current_row < 0:
            message_box.info("No file selected to validate.", "No File Selected", self)
            return
        
        item = self.sidebar.item(current_row)
        if not item:
            return
            
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path and file_path in self.file_data_models:
            self._show_validation_results(self._validate_single_file(file_path))

    def validate_all_files(self):
        """Validate all opened IDE files for cross-file duplicates."""
        if not self.file_data_models:
            message_box.info("No files are currently opened.", "No Files", self)
            return
            
        results = self.parser.validate_multiple_files(self.file_data_models)
        self._show_validation_results(results, is_multi_file=True)

    def _validate_single_file(self, file_path):
        """Validate a single file and return results."""
        return self.parser.validate_single_file(self.file_data_models[file_path], file_path)

    def _show_validation_results(self, results, is_multi_file=False):
        """Display validation results in a dialog with option to save as log."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle("IDE Validation Results")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Summary
        if is_multi_file:
            summary_text = f"""
Validation Summary:
• Total Files: {results['summary']['total_files']}
• Files with Errors: {results['summary']['files_with_errors']}
• Total Errors: {results['summary']['total_errors']}
• Total Warnings: {results['summary']['total_warnings']}
"""
        else:
            error_count = len(results.get('errors', []))
            warning_count = len(results.get('warnings', []))
            summary_text = f"""
Validation Summary for: {os.path.basename(results.get('file_path', 'Unknown'))}
• Errors: {error_count}
• Warnings: {warning_count}
"""
        
        summary_label = QLabel(summary_text)
        layout.addWidget(summary_label)
        
        # Detailed results
        results_text = QTextEdit()
        results_text.setReadOnly(True)
        results_text.setFont(QFont("Consolas", 10))
        
        detailed_report = self._generate_detailed_report(results, is_multi_file)
        results_text.setPlainText(detailed_report)
        
        layout.addWidget(results_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_log_btn = QPushButton("Save as Log File")
        save_log_btn.clicked.connect(lambda: self._save_validation_log(detailed_report))
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        
        button_layout.addWidget(save_log_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()

    def _generate_detailed_report(self, results, is_multi_file=False):
        """Generate a detailed validation report."""
        from datetime import datetime
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("IDE VALIDATION REPORT")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        if is_multi_file:
            # Multi-file validation report
            report_lines.append(f"SUMMARY:")
            report_lines.append(f"  Total Files Validated: {results['summary']['total_files']}")
            report_lines.append(f"  Files with Errors: {results['summary']['files_with_errors']}")
            report_lines.append(f"  Total Errors: {results['summary']['total_errors']}")
            report_lines.append(f"  Total Warnings: {results['summary']['total_warnings']}")
            report_lines.append("")
            
            # Individual file results
            for file_path, file_results in results['files'].items():
                report_lines.append(f"FILE: {os.path.basename(file_path)}")
                report_lines.append(f"  Path: {file_path}")
                
                if file_results['errors']:
                    report_lines.append(f"  ERRORS ({len(file_results['errors'])}):")
                    for error in file_results['errors']:
                        report_lines.append(f"    • {error}")
                
                if file_results['warnings']:
                    report_lines.append(f"  WARNINGS ({len(file_results['warnings'])}):")
                    for warning in file_results['warnings']:
                        report_lines.append(f"    • {warning}")
                
                if file_results['stats']:
                    report_lines.append(f"  STATISTICS:")
                    for section, count in file_results['stats'].items():
                        if count > 0:
                            report_lines.append(f"    {section}: {count} entries")
                
                report_lines.append("")
            
            # Cross-file duplicates
            if results['cross_file_duplicates']['ids']:
                report_lines.append("CROSS-FILE DUPLICATE IDs:")
                for obj_id, locations in results['cross_file_duplicates']['ids'].items():
                    report_lines.append(f"  ID {obj_id} found in:")
                    for file_path, section, row_idx in locations:
                        report_lines.append(f"    • {os.path.basename(file_path)} - {section}[{row_idx}]")
                report_lines.append("")
            
            if results['cross_file_duplicates']['models']:
                report_lines.append("CROSS-FILE DUPLICATE MODELS:")
                for model_name, locations in results['cross_file_duplicates']['models'].items():
                    report_lines.append(f"  Model '{model_name}' found in:")
                    for file_path, section, row_idx in locations:
                        report_lines.append(f"    • {os.path.basename(file_path)} - {section}[{row_idx}]")
                report_lines.append("")
        
        else:
            # Single file validation report
            file_path = results.get('file_path', 'Unknown')
            report_lines.append(f"FILE: {os.path.basename(file_path)}")
            report_lines.append(f"Path: {file_path}")
            report_lines.append("")
            
            if results.get('errors'):
                report_lines.append(f"ERRORS ({len(results['errors'])}):")
                for error in results['errors']:
                    report_lines.append(f"  • {error}")
                report_lines.append("")
            
            if results.get('warnings'):
                report_lines.append(f"WARNINGS ({len(results['warnings'])}):")
                for warning in results['warnings']:
                    report_lines.append(f"  • {warning}")
                report_lines.append("")
            
            if results.get('stats'):
                report_lines.append("STATISTICS:")
                for section, count in results['stats'].items():
                    if count > 0:
                        report_lines.append(f"  {section}: {count} entries")
                report_lines.append("")
            
            if results.get('duplicate_ids'):
                report_lines.append("DUPLICATE IDs:")
                for obj_id, locations in results['duplicate_ids'].items():
                    report_lines.append(f"  ID {obj_id} found in sections: {', '.join([f'{sec}[{idx}]' for sec, idx in locations])}")
                report_lines.append("")
            
            if results.get('duplicate_models'):
                report_lines.append("DUPLICATE MODELS:")
                for model_name, locations in results['duplicate_models'].items():
                    report_lines.append(f"  Model '{model_name}' found in sections: {', '.join([f'{sec}[{idx}]' for sec, idx in locations])}")
                report_lines.append("")
        
        if not any([results.get('errors'), results.get('warnings'), 
                   results.get('cross_file_duplicates', {}).get('ids'), 
                   results.get('cross_file_duplicates', {}).get('models')]):
            report_lines.append("✓ NO ISSUES FOUND - All validations passed successfully!")
        
        report_lines.append("=" * 80)
        return "\n".join(report_lines)

    def _save_validation_log(self, report_content):
        """Save validation report to a log file."""
        from datetime import datetime
        
        default_filename = f"ide_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Validation Log",
            default_filename,
            "Log Files (*.log);;Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                message_box.info(f"Validation log saved to:\n{file_path}", "Log Saved", self)
                debug_logger.info(LogCategory.TOOL, f"Validation log saved: {file_path}")
            except Exception as e:
                message_box.error(f"Failed to save log file:\n{e}", "Save Error", self)
                debug_logger.log_exception(LogCategory.TOOL, f"Error saving validation log: {file_path}", e)

    def find_free_id_ranges(self):
        """Find free ID ranges in IDE files from a selected folder."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select IDE Files Folder")
        if not folder_path:
            return
            
        # Get upper limit from user
        upper_limit = self._get_id_upper_limit()
        if upper_limit is None:
            return
            
        # Find all IDE files in the folder
        ide_files = [str(p) for p in Path(folder_path).rglob('*.ide')]
        if not ide_files:
            message_box.info("No .ide files were found in the selected folder.", "No Files Found", self)
            return
        
        # Analyze ID ranges
        try:
            progress = QProgressDialog(f"Analyzing {len(ide_files)} IDE files...", "Cancel", 0, len(ide_files), self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            
            used_ids = set()
            file_id_data = {}
            
            for i, file_path in enumerate(ide_files):
                progress.setValue(i)
                if progress.wasCanceled():
                    return
                    
                file_ids = self._extract_ids_from_file(file_path)
                if file_ids:
                    file_id_data[file_path] = file_ids
                    used_ids.update(file_ids)
            
            progress.setValue(len(ide_files))
            
            # Calculate free ranges
            free_ranges = self._calculate_free_ranges(used_ids, upper_limit)
            
            # Show results
            self._show_id_ranges_results(folder_path, file_id_data, free_ranges, upper_limit)
            
        except Exception as e:
            message_box.error(f"Error analyzing ID ranges: {e}", "Analysis Error", self)
            debug_logger.log_exception(LogCategory.TOOL, f"Error in find_free_id_ranges", e)

    def _get_id_upper_limit(self):
        """Get the upper limit for ID analysis from user input."""
        from PyQt6.QtWidgets import QInputDialog
        
        limit, ok = QInputDialog.getInt(
            self,
            "Set ID Upper Limit",
            "Enter the maximum ID to analyze (default: 65535):",
            value=65535,
            min=1,
            max=999999,
            step=1
        )
        
        return limit if ok else None

    def _extract_ids_from_file(self, file_path):
        """Extract all IDs from a single IDE file."""
        try:
            with open(file_path, 'r', encoding='ascii', errors='ignore') as f:
                content = f.read()
            
            parsed_data = self.parser.parse(content)
            ids = set()
            
            for section_key, section_data in parsed_data.items():
                rows = section_data.get("rows", [])
                schema_section = self.schema["sections"].get(section_key, {})
                primary_keys = schema_section.get("primaryKeys", [])
                
                if "id" in primary_keys:
                    for row_data in rows:
                        if "id" in row_data and isinstance(row_data["id"], (int, str)):
                            try:
                                obj_id = int(row_data["id"])
                                ids.add(obj_id)
                            except (ValueError, TypeError):
                                continue
            
            return ids
            
        except Exception as e:
            debug_logger.log_exception(LogCategory.TOOL, f"Error extracting IDs from {file_path}", e)
            return set()

    def _calculate_free_ranges(self, used_ids, upper_limit):
        """Calculate free ID ranges from used IDs."""
        if not used_ids:
            return [(1, upper_limit)]
        
        # Sort used IDs and find gaps
        sorted_ids = sorted(used_ids)
        free_ranges = []
        
        # Check for range before first ID
        if sorted_ids[0] > 1:
            free_ranges.append((1, sorted_ids[0] - 1))
        
        # Check for gaps between consecutive IDs
        for i in range(len(sorted_ids) - 1):
            current_id = sorted_ids[i]
            next_id = sorted_ids[i + 1]
            
            if next_id - current_id > 1:
                free_ranges.append((current_id + 1, next_id - 1))
        
        # Check for range after last ID
        if sorted_ids[-1] < upper_limit:
            free_ranges.append((sorted_ids[-1] + 1, upper_limit))
        
        return free_ranges

    def _show_id_ranges_results(self, folder_path, file_id_data, free_ranges, upper_limit):
        """Display ID ranges analysis results."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QTabWidget
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Free ID Ranges Analysis")
        dialog.setMinimumSize(900, 700)
        
        layout = QVBoxLayout(dialog)
        
        # Summary
        total_used = sum(len(ids) for ids in file_id_data.values())
        total_free = sum(end - start + 1 for start, end in free_ranges)
        
        summary_text = f"""
ID Range Analysis Results:
• Folder: {folder_path}
• Files Analyzed: {len(file_id_data)}
• Upper Limit: {upper_limit}
• Total Used IDs: {total_used}
• Total Free IDs: {total_free}
• Free Ranges Found: {len(free_ranges)}
"""
        
        summary_label = QLabel(summary_text)
        layout.addWidget(summary_label)
        
        # Create tabs for different views
        tab_widget = QTabWidget()
        
        # Free Ranges Tab
        free_ranges_widget = QTextEdit()
        free_ranges_widget.setReadOnly(True)
        free_ranges_widget.setFont(QFont("Consolas", 10))
        
        free_ranges_report = self._generate_free_ranges_report(free_ranges, file_id_data, folder_path, upper_limit)
        free_ranges_widget.setPlainText(free_ranges_report)
        
        tab_widget.addTab(free_ranges_widget, "Free Ranges")
        
        # File Details Tab
        file_details_widget = QTextEdit()
        file_details_widget.setReadOnly(True)
        file_details_widget.setFont(QFont("Consolas", 10))
        
        file_details_report = self._generate_file_details_report(file_id_data)
        file_details_widget.setPlainText(file_details_report)
        
        tab_widget.addTab(file_details_widget, "File Details")
        
        layout.addWidget(tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("Export Report")
        export_btn.clicked.connect(lambda: self._export_id_ranges_report(free_ranges_report, file_details_report))
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        
        button_layout.addWidget(export_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()

    def _generate_free_ranges_report(self, free_ranges, file_id_data, folder_path, upper_limit):
        """Generate detailed free ranges report."""
        from datetime import datetime
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("FREE ID RANGES ANALYSIS REPORT")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        report_lines.append(f"ANALYSIS PARAMETERS:")
        report_lines.append(f"  Folder: {folder_path}")
        report_lines.append(f"  Files Analyzed: {len(file_id_data)}")
        report_lines.append(f"  ID Upper Limit: {upper_limit}")
        report_lines.append("")
        
        total_used = sum(len(ids) for ids in file_id_data.values())
        total_free = sum(end - start + 1 for start, end in free_ranges)
        
        report_lines.append(f"SUMMARY:")
        report_lines.append(f"  Total Used IDs: {total_used}")
        report_lines.append(f"  Total Free IDs: {total_free}")
        report_lines.append(f"  Free Ranges Found: {len(free_ranges)}")
        report_lines.append(f"  Usage Percentage: {(total_used / upper_limit * 100):.2f}%")
        report_lines.append("")
        
        if free_ranges:
            report_lines.append("FREE ID RANGES:")
            for i, (start, end) in enumerate(free_ranges, 1):
                range_size = end - start + 1
                if range_size == 1:
                    report_lines.append(f"  {i:2d}. ID {start} (1 ID available)")
                else:
                    report_lines.append(f"  {i:2d}. IDs {start}-{end} ({range_size} IDs available)")
            report_lines.append("")
            
            # Highlight largest ranges
            sorted_ranges = sorted(free_ranges, key=lambda x: x[1] - x[0], reverse=True)
            report_lines.append("LARGEST FREE RANGES:")
            for i, (start, end) in enumerate(sorted_ranges[:10], 1):
                range_size = end - start + 1
                report_lines.append(f"  {i:2d}. IDs {start}-{end} ({range_size} IDs)")
        else:
            report_lines.append("⚠️  NO FREE IDS AVAILABLE - All IDs up to the limit are in use!")
        
        report_lines.append("")
        report_lines.append("=" * 80)
        return "\n".join(report_lines)

    def _generate_file_details_report(self, file_id_data):
        """Generate detailed file-by-file ID usage report."""
        report_lines = []
        report_lines.append("FILE-BY-FILE ID USAGE DETAILS")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        for file_path, ids in file_id_data.items():
            filename = os.path.basename(file_path)
            report_lines.append(f"FILE: {filename}")
            report_lines.append(f"  Path: {file_path}")
            report_lines.append(f"  IDs Used: {len(ids)}")
            
            if ids:
                sorted_ids = sorted(ids)
                report_lines.append(f"  ID Range: {min(sorted_ids)} - {max(sorted_ids)}")
                
                # Show first few and last few IDs
                if len(sorted_ids) <= 10:
                    report_lines.append(f"  IDs: {', '.join(map(str, sorted_ids))}")
                else:
                    first_five = ', '.join(map(str, sorted_ids[:5]))
                    last_five = ', '.join(map(str, sorted_ids[-5:]))
                    report_lines.append(f"  IDs: {first_five} ... {last_five}")
            
            report_lines.append("")
        
        return "\n".join(report_lines)

    def _export_id_ranges_report(self, free_ranges_report, file_details_report):
        """Export ID ranges analysis to a file."""
        from datetime import datetime
        
        default_filename = f"id_ranges_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export ID Ranges Report",
            default_filename,
            "Text Files (*.txt);;Log Files (*.log);;All Files (*)"
        )
        
        if file_path:
            try:
                combined_report = free_ranges_report + "\n\n" + file_details_report
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(combined_report)
                message_box.info(f"ID ranges report exported to:\n{file_path}", "Export Complete", self)
                debug_logger.info(LogCategory.TOOL, f"ID ranges report exported: {file_path}")
            except Exception as e:
                message_box.error(f"Failed to export report:\n{e}", "Export Error", self)
                debug_logger.log_exception(LogCategory.TOOL, f"Error exporting ID ranges report: {file_path}", e)

    def open_id_manager(self):
        """Open the ID Manager dialog for renumbering operations."""
        if not self.file_data_models:
            message_box.info("No IDE files are currently opened.", "No Files", self)
            return
            
        dialog = IDManagerDialog(self, self.file_data_models, self.parser, self.schema)
        if dialog.exec() == dialog.DialogCode.Accepted:
            # Apply changes and refresh UI
            self._apply_id_manager_changes(dialog.get_changes())

    def _apply_id_manager_changes(self, changes):
        """Apply ID renumbering changes to the data models and refresh UI."""
        try:
            for file_path, file_changes in changes.items():
                if file_path in self.file_data_models:
                    # Apply changes to data model
                    for section_key, section_changes in file_changes.items():
                        if section_key in self.file_data_models[file_path]:
                            for row_idx, new_id in section_changes.items():
                                if row_idx < len(self.file_data_models[file_path][section_key]["rows"]):
                                    self.file_data_models[file_path][section_key]["rows"][row_idx]["id"] = new_id
                    
                    # Mark file as dirty and refresh UI
                    self.mark_file_as_dirty(file_path)
                    self.update_raw_text_from_model(file_path)
                    self.refresh_tables_from_model(file_path)
            
            debug_logger.info(LogCategory.TOOL, f"Applied ID renumbering changes to {len(changes)} files")
            
        except Exception as e:
            message_box.error(f"Error applying ID changes: {e}", "Apply Error", self)
            debug_logger.log_exception(LogCategory.TOOL, "Error applying ID manager changes", e)


class IDManagerDialog(QDialog):
    """Dialog for managing and renumbering IDs in IDE files."""
    
    def __init__(self, parent, file_data_models, parser, schema):
        super().__init__(parent)
        self.file_data_models = file_data_models
        self.parser = parser
        self.schema = schema
        self.changes = {}  # Store pending changes
        
        self.setWindowTitle("ID Manager")
        self.setMinimumSize(1000, 700)
        
        self.setup_ui()
        self.load_current_ids()
    
    def setup_ui(self):
        """Setup the ID Manager dialog UI."""
        from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                                   QTableWidget, QTableWidgetItem, QPushButton, QLabel, 
                                   QSpinBox, QComboBox, QCheckBox, QGroupBox, QTextEdit,
                                   QSplitter, QHeaderView)
        
        layout = QVBoxLayout(self)
        
        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Controls
        controls_frame = QGroupBox("Renumbering Options")
        controls_layout = QVBoxLayout(controls_frame)
        
        # Renumbering mode selection
        mode_group = QGroupBox("Renumbering Mode")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Single File - Custom Start ID",
            "All Files - Consecutive IDs",
            "All Files - Custom Start per File",
            "Resolve Conflicts Only"
        ])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(QLabel("Select renumbering mode:"))
        mode_layout.addWidget(self.mode_combo)
        
        controls_layout.addWidget(mode_group)
        
        # Per-file custom starts group (hidden by default, placed high for visibility)
        self.per_file_group = QGroupBox("Per-file Start IDs")
        self.per_file_group_layout = QVBoxLayout(self.per_file_group)
        # Scrollable container inside the group to handle many files
        from PyQt6.QtWidgets import QScrollArea, QWidget
        self.per_file_scroll = QScrollArea(self.per_file_group)
        self.per_file_scroll.setWidgetResizable(True)
        self.per_file_container = QWidget()
        from PyQt6.QtWidgets import QVBoxLayout as _QVBoxLayout
        self.per_file_container_layout = _QVBoxLayout(self.per_file_container)
        self.per_file_container_layout.setContentsMargins(6, 6, 6, 6)
        self.per_file_scroll.setWidget(self.per_file_container)
        self.per_file_group_layout.addWidget(self.per_file_scroll)
        self.per_file_group.setVisible(False)
        controls_layout.addWidget(self.per_file_group)

        # Parameters group
        self.params_group = QGroupBox("Parameters")
        self.params_layout = QVBoxLayout(self.params_group)
        
        # Start ID input
        start_id_layout = QHBoxLayout()
        start_id_layout.addWidget(QLabel("Start ID:"))
        self.start_id_spin = QSpinBox()
        self.start_id_spin.setRange(1, 999999)
        self.start_id_spin.setValue(1000)
        start_id_layout.addWidget(self.start_id_spin)
        start_id_layout.addStretch()
        self.params_layout.addLayout(start_id_layout)
        
        # Increment input
        increment_layout = QHBoxLayout()
        increment_layout.addWidget(QLabel("Increment:"))
        self.increment_spin = QSpinBox()
        self.increment_spin.setRange(1, 1000)
        self.increment_spin.setValue(1)
        increment_layout.addWidget(self.increment_spin)
        increment_layout.addStretch()
        self.params_layout.addLayout(increment_layout)
        
        # File selection for single file mode
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Target File:"))
        self.file_combo = QComboBox()
        file_layout.addWidget(self.file_combo)
        self.params_layout.addLayout(file_layout)
        
        # Options
        self.preserve_order_cb = QCheckBox("Preserve original order")
        self.preserve_order_cb.setChecked(True)
        self.params_layout.addWidget(self.preserve_order_cb)
        
        self.create_backup_cb = QCheckBox("Create backup before changes")
        self.create_backup_cb.setChecked(True)
        self.params_layout.addWidget(self.create_backup_cb)
        
        controls_layout.addWidget(self.params_group)

        # Action buttons
        action_layout = QVBoxLayout()
        
        self.preview_btn = QPushButton("🔍 Preview Changes")
        self.preview_btn.clicked.connect(self.preview_changes)
        action_layout.addWidget(self.preview_btn)
        
        self.apply_btn = QPushButton("✅ Apply Changes")
        self.apply_btn.clicked.connect(self.apply_changes)
        action_layout.addWidget(self.apply_btn)
        
        self.reset_btn = QPushButton("🔄 Reset")
        self.reset_btn.clicked.connect(self.reset_changes)
        action_layout.addWidget(self.reset_btn)
        
        action_layout.addStretch()
        controls_layout.addLayout(action_layout)
        
        # Right panel - Preview/Results
        preview_frame = QGroupBox("Preview & Results")
        preview_layout = QVBoxLayout(preview_frame)
        
        # Create tabs for different views
        self.tab_widget = QTabWidget()
        
        # Current IDs tab
        self.current_ids_table = QTableWidget()
        self.current_ids_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tab_widget.addTab(self.current_ids_table, "Current IDs")
        
        # Preview tab
        self.preview_table = QTableWidget()
        self.preview_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tab_widget.addTab(self.preview_table, "Preview Changes")
        
        # Conflicts tab
        self.conflicts_table = QTableWidget()
        self.conflicts_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tab_widget.addTab(self.conflicts_table, "Conflicts")
        
        preview_layout.addWidget(self.tab_widget)
        
        # Status text
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        preview_layout.addWidget(self.status_text)
        
        # Add to splitter
        splitter.addWidget(controls_frame)
        splitter.addWidget(preview_frame)
        splitter.setSizes([350, 650])
        
        layout.addWidget(splitter)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Initialize UI state
        # Prefer to open in per-file mode for discoverability
        try:
            idx = self.mode_combo.findText("All Files - Custom Start per File")
            if idx >= 0:
                self.mode_combo.setCurrentIndex(idx)
        except Exception:
            pass
        self.on_mode_changed()
        # Build per-file controls initially
        self._build_per_file_start_controls()
    
    def load_current_ids(self):
        """Load current IDs from all opened files."""
        # Populate file combo
        self.file_combo.clear()
        for file_path in self.file_data_models.keys():
            self.file_combo.addItem(os.path.basename(file_path), file_path)
        
        # Load current IDs table
        self.refresh_current_ids_table()
        self.detect_conflicts()
        # Rebuild per-file controls when files list changes
        self._build_per_file_start_controls()

    def _build_per_file_start_controls(self):
        """Create rows of Start ID spinboxes for each file."""
        # Clear existing
        self.per_file_start_spins = {}
        # Remove all widgets from the scroll container layout
        while self.per_file_container_layout.count():
            item = self.per_file_container_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        # Create a row per file
        from PyQt6.QtWidgets import QLabel, QHBoxLayout, QWidget, QSpinBox
        for file_path in sorted(self.file_data_models.keys()):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addWidget(QLabel(os.path.basename(file_path)))
            spin = QSpinBox()
            spin.setRange(1, 999999)
            spin.setValue(self.start_id_spin.value())
            row_layout.addStretch()
            row_layout.addWidget(QLabel("Start:"))
            row_layout.addWidget(spin)
            self.per_file_container_layout.addWidget(row_widget)
            self.per_file_start_spins[file_path] = spin
        self.per_file_container_layout.addStretch()
    
    def refresh_current_ids_table(self):
        """Refresh the current IDs table."""
        all_ids = []
        
        for file_path, file_data in self.file_data_models.items():
            filename = os.path.basename(file_path)
            
            for section_key, section_data in file_data.items():
                rows = section_data.get("rows", [])
                schema_section = self.schema["sections"].get(section_key, {})
                primary_keys = schema_section.get("primaryKeys", [])
                
                if "id" in primary_keys:
                    for row_idx, row_data in enumerate(rows):
                        if "id" in row_data:
                            model_name = row_data.get("modelName", row_data.get("model", ""))
                            all_ids.append({
                                "file": filename,
                                "file_path": file_path,
                                "section": section_key,
                                "row": row_idx,
                                "id": row_data["id"],
                                "model": model_name
                            })
        
        # Sort by ID
        all_ids.sort(key=lambda x: int(x["id"]) if isinstance(x["id"], (int, str)) and str(x["id"]).isdigit() else 0)
        
        # Populate table
        self.current_ids_table.setRowCount(len(all_ids))
        self.current_ids_table.setColumnCount(5)
        self.current_ids_table.setHorizontalHeaderLabels(["File", "Section", "ID", "Model", "Row"])
        
        for row_idx, id_data in enumerate(all_ids):
            self.current_ids_table.setItem(row_idx, 0, QTableWidgetItem(id_data["file"]))
            self.current_ids_table.setItem(row_idx, 1, QTableWidgetItem(id_data["section"]))
            self.current_ids_table.setItem(row_idx, 2, QTableWidgetItem(str(id_data["id"])))
            self.current_ids_table.setItem(row_idx, 3, QTableWidgetItem(id_data["model"]))
            self.current_ids_table.setItem(row_idx, 4, QTableWidgetItem(str(id_data["row"])))
        
        # Resize columns
        header = self.current_ids_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    
    def detect_conflicts(self):
        """Detect and display ID conflicts."""
        conflicts = {}
        all_ids = {}
        
        for file_path, file_data in self.file_data_models.items():
            filename = os.path.basename(file_path)
            
            for section_key, section_data in file_data.items():
                rows = section_data.get("rows", [])
                schema_section = self.schema["sections"].get(section_key, {})
                primary_keys = schema_section.get("primaryKeys", [])
                
                if "id" in primary_keys:
                    for row_idx, row_data in enumerate(rows):
                        if "id" in row_data:
                            obj_id = row_data["id"]
                            location = (filename, section_key, row_idx)
                            
                            if obj_id in all_ids:
                                if obj_id not in conflicts:
                                    conflicts[obj_id] = [all_ids[obj_id]]
                                conflicts[obj_id].append(location)
                            else:
                                all_ids[obj_id] = location
        
        # Populate conflicts table
        conflict_rows = []
        for obj_id, locations in conflicts.items():
            for location in locations:
                conflict_rows.append({
                    "id": obj_id,
                    "file": location[0],
                    "section": location[1],
                    "row": location[2],
                    "conflict_count": len(locations)
                })
        
        self.conflicts_table.setRowCount(len(conflict_rows))
        self.conflicts_table.setColumnCount(5)
        self.conflicts_table.setHorizontalHeaderLabels(["ID", "File", "Section", "Row", "Conflicts"])
        
        for row_idx, conflict in enumerate(conflict_rows):
            self.conflicts_table.setItem(row_idx, 0, QTableWidgetItem(str(conflict["id"])))
            self.conflicts_table.setItem(row_idx, 1, QTableWidgetItem(conflict["file"]))
            self.conflicts_table.setItem(row_idx, 2, QTableWidgetItem(conflict["section"]))
            self.conflicts_table.setItem(row_idx, 3, QTableWidgetItem(str(conflict["row"])))
            self.conflicts_table.setItem(row_idx, 4, QTableWidgetItem(str(conflict["conflict_count"])))
        
        # Update status
        if conflicts:
            self.status_text.setText(f"⚠️ Found {len(conflicts)} ID conflicts affecting {len(conflict_rows)} entries.")
        else:
            self.status_text.setText("✅ No ID conflicts detected.")
    
    def on_mode_changed(self):
        """Handle renumbering mode change."""
        mode = self.mode_combo.currentText()
        
        # Show/hide relevant controls
        if "Single File" in mode:
            self.file_combo.setVisible(True)
            self.file_combo.parent().setVisible(True)
        else:
            self.file_combo.setVisible(False)
            self.file_combo.parent().setVisible(False)
        
        if "Resolve Conflicts Only" in mode:
            self.start_id_spin.setEnabled(False)
            self.increment_spin.setEnabled(False)
        else:
            self.start_id_spin.setEnabled(True)
            self.increment_spin.setEnabled(True)
        # Per-file group visibility
        per_file = "All Files - Custom Start per File" in mode
        self.per_file_group.setVisible(per_file)
        if per_file:
            self._build_per_file_start_controls()
    
    def preview_changes(self):
        """Preview the renumbering changes."""
        mode = self.mode_combo.currentText()
        start_id = self.start_id_spin.value()
        increment = self.increment_spin.value()
        
        preview_data = []
        current_id = start_id
        
        try:
            if "Single File" in mode:
                # Single file renumbering
                file_path = self.file_combo.currentData()
                if file_path and file_path in self.file_data_models:
                    current_id = self._preview_single_file(file_path, start_id, increment, preview_data)
            
            elif "All Files - Consecutive" in mode:
                # Consecutive renumbering across all files
                for file_path in sorted(self.file_data_models.keys()):
                    current_id = self._preview_single_file(file_path, current_id, increment, preview_data)
            
            elif "All Files - Custom Start per File" in mode:
                # Custom start ID per file using per-file spin values
                for file_path in sorted(self.file_data_models.keys()):
                    per_file_start = start_id
                    if hasattr(self, 'per_file_start_spins') and file_path in self.per_file_start_spins:
                        per_file_start = self.per_file_start_spins[file_path].value()
                    self._preview_single_file(file_path, per_file_start, increment, preview_data)
            
            elif "Resolve Conflicts Only" in mode:
                # Only renumber conflicting IDs
                self._preview_conflict_resolution(preview_data)
            
            # Store preview data and populate table
            self._preview_data = preview_data
            self.populate_preview_table(preview_data)
            self.tab_widget.setCurrentIndex(1)  # Switch to preview tab
            
        except Exception as e:
            self.status_text.setText(f"❌ Error generating preview: {e}")
    
    def _preview_single_file(self, file_path, start_id, increment, preview_data):
        """Preview renumbering for a single file."""
        current_id = start_id
        filename = os.path.basename(file_path)
        
        file_data = self.file_data_models[file_path]
        
        for section_key, section_data in file_data.items():
            rows = section_data.get("rows", [])
            schema_section = self.schema["sections"].get(section_key, {})
            primary_keys = schema_section.get("primaryKeys", [])
            
            if "id" in primary_keys:
                for row_idx, row_data in enumerate(rows):
                    if "id" in row_data:
                        old_id = row_data["id"]
                        new_id = current_id
                        model_name = row_data.get("modelName", row_data.get("model", ""))
                        
                        preview_data.append({
                            "file": filename,
                            "section": section_key,
                            "row": row_idx,
                            "old_id": old_id,
                            "new_id": new_id,
                            "model": model_name,
                            "change": "Modified" if old_id != new_id else "No Change"
                        })
                        
                        current_id += increment
        
        return current_id
    
    def _preview_conflict_resolution(self, preview_data):
        """Preview conflict resolution renumbering."""
        # Find conflicts and assign new IDs only to conflicting entries
        conflicts = self._find_conflicts()
        
        # Find the highest existing ID to start from
        max_id = 0
        for file_data in self.file_data_models.values():
            for section_data in file_data.values():
                for row_data in section_data.get("rows", []):
                    if "id" in row_data:
                        try:
                            max_id = max(max_id, int(row_data["id"]))
                        except (ValueError, TypeError):
                            pass
        
        next_available_id = max_id + 1
        
        for obj_id, locations in conflicts.items():
            # Keep first occurrence, renumber the rest
            for i, (file_path, section_key, row_idx) in enumerate(locations[1:], 1):
                filename = os.path.basename(file_path)
                row_data = self.file_data_models[file_path][section_key]["rows"][row_idx]
                model_name = row_data.get("modelName", row_data.get("model", ""))
                
                preview_data.append({
                    "file": filename,
                    "section": section_key,
                    "row": row_idx,
                    "old_id": obj_id,
                    "new_id": next_available_id,
                    "model": model_name,
                    "change": "Conflict Resolved"
                })
                
                next_available_id += 1
    
    def _find_conflicts(self):
        """Find ID conflicts across all files."""
        conflicts = {}
        all_ids = {}
        
        for file_path, file_data in self.file_data_models.items():
            for section_key, section_data in file_data.items():
                rows = section_data.get("rows", [])
                schema_section = self.schema["sections"].get(section_key, {})
                primary_keys = schema_section.get("primaryKeys", [])
                
                if "id" in primary_keys:
                    for row_idx, row_data in enumerate(rows):
                        if "id" in row_data:
                            obj_id = row_data["id"]
                            location = (file_path, section_key, row_idx)
                            
                            if obj_id in all_ids:
                                if obj_id not in conflicts:
                                    conflicts[obj_id] = [all_ids[obj_id]]
                                conflicts[obj_id].append(location)
                            else:
                                all_ids[obj_id] = location
        
        return conflicts
    
    def populate_preview_table(self, preview_data):
        """Populate the preview table with change data."""
        self.preview_table.setRowCount(len(preview_data))
        self.preview_table.setColumnCount(7)
        self.preview_table.setHorizontalHeaderLabels([
            "File", "Section", "Model", "Old ID", "New ID", "Change", "Row"
        ])
        
        for row_idx, data in enumerate(preview_data):
            self.preview_table.setItem(row_idx, 0, QTableWidgetItem(data["file"]))
            self.preview_table.setItem(row_idx, 1, QTableWidgetItem(data["section"]))
            self.preview_table.setItem(row_idx, 2, QTableWidgetItem(data["model"]))
            self.preview_table.setItem(row_idx, 3, QTableWidgetItem(str(data["old_id"])))
            self.preview_table.setItem(row_idx, 4, QTableWidgetItem(str(data["new_id"])))
            self.preview_table.setItem(row_idx, 5, QTableWidgetItem(data["change"]))
            self.preview_table.setItem(row_idx, 6, QTableWidgetItem(str(data["row"])))
        
        # Resize columns
        header = self.preview_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        # Update status
        changes = len([d for d in preview_data if d["change"] != "No Change"])
        self.status_text.setText(f"📋 Preview ready: {changes} changes planned out of {len(preview_data)} entries.")
    
    def apply_changes(self):
        """Apply the renumbering changes."""
        if not hasattr(self, '_preview_data') or not self._preview_data:
            self.preview_changes()
            if not hasattr(self, '_preview_data'):
                return
        
        # Create backup if requested
        if self.create_backup_cb.isChecked():
            self._create_backup()
        
        # Apply changes to data models
        self.changes = {}
        
        for data in self._preview_data:
            if data["change"] != "No Change":
                file_path = None
                # Find file path by filename
                for fp in self.file_data_models.keys():
                    if os.path.basename(fp) == data["file"]:
                        file_path = fp
                        break
                
                if file_path:
                    if file_path not in self.changes:
                        self.changes[file_path] = {}
                    if data["section"] not in self.changes[file_path]:
                        self.changes[file_path][data["section"]] = {}
                    
                    self.changes[file_path][data["section"]][data["row"]] = data["new_id"]
        
        self.ok_btn.setEnabled(True)
        self.status_text.setText(f"✅ Changes applied! {len(self.changes)} files will be modified.")
    
    def reset_changes(self):
        """Reset all changes and refresh the dialog."""
        self.changes = {}
        self.ok_btn.setEnabled(False)
        self.load_current_ids()
        self.status_text.setText("🔄 Reset complete. Ready for new operations.")
    
    def _create_backup(self):
        """Create backup of files before applying changes."""
        try:
            from datetime import datetime
            backup_suffix = f"_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            for file_path in self.file_data_models.keys():
                backup_path = file_path + backup_suffix
                import shutil
                shutil.copy2(file_path, backup_path)
            
            self.status_text.append(f"📁 Backup created with suffix: {backup_suffix}")
            
        except Exception as e:
            self.status_text.append(f"⚠️ Backup failed: {e}")
    
    def get_changes(self):
        """Get the changes to apply."""
        return self.changes


# Legacy class name for backward compatibility
IDEEditor = IDEEditorTool