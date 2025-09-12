"""
UI components for the IMG Editor, re-exported from the legacy module.
This interim shim allows us to refactor imports before moving implementations.
"""
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFileDialog,
    QAbstractItemView,
    QApplication,
    QComboBox,
    QLineEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QUrl
from PyQt6.QtGui import QDrag
import os

from application.responsive_utils import get_responsive_manager
from application.styles import ModernDarkTheme
from application.debug_system import get_debug_logger, LogCategory
from .drag_drop_handler import DragDropMixin

debug_logger = get_debug_logger()


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


class IMGEntriesTable(QTableWidget, DragDropMixin):
    """Enhanced table widget for IMG entries with drag and drop support"""
    entry_double_clicked = pyqtSignal(object)
    entry_selected = pyqtSignal(object)
    entry_renamed = pyqtSignal(object, str)  # Signal when entry is renamed
    files_dropped = pyqtSignal(list)  # Signal for dropped files
    entries_dropped = pyqtSignal(list, object)  # Signal for dropped entries

    def __init__(self, parent=None):
        """Initialize the table with responsive styling"""
        QTableWidget.__init__(self, parent)
        DragDropMixin.__init__(self)

        rm = get_responsive_manager()
        fonts = rm.get_font_config()
        spacing = rm.get_spacing_config()

        self.setColumnCount(7)
        self.setHorizontalHeaderLabels(['Name', 'Type', 'Size', 'Offset', 'RW Version', 'Streaming', 'Compression'])

        # Setup table properties
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        # Prevent user-initiated editing (e.g., double-click). Programmatic edits still allowed.
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Enable drag and drop
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.setDragDropOverwriteMode(False)

        # Auto-resize columns to fill the available space
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Initialize drag and drop properties
        self.current_archive = None
        self.img_controller = None

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
        self.itemChanged.connect(self._on_item_changed)

        # Track editing state
        self._is_editing = False
        self._editing_item = None
        self._old_name = None

        # Initialize context menu handler (will be set by parent)
        self.context_menu_handler = None

        # Enable context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def setup_drag_drop_support(self, drag_drop_handler, archive, controller):
        """Setup drag and drop support for this table"""
        self.current_archive = archive
        self.img_controller = controller
        self.setup_drag_drop(drag_drop_handler, accept_files=True, accept_entries=True, enable_dragging=True)

        # Connect drag and drop signals
        if drag_drop_handler:
            drag_drop_handler.files_dropped.connect(self.files_dropped.emit)
            drag_drop_handler.entries_dropped.connect(self.entries_dropped.emit)

    def set_context_menu_handler(self, handler):
        """Set the context menu handler"""
        self.context_menu_handler = handler

    def _show_context_menu(self, position):
        """Show context menu if handler is set"""
        if self.context_menu_handler:
            self.context_menu_handler.show_context_menu(position)

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
            name_item.setFlags(name_item.flags() | Qt.ItemFlag.ItemIsEditable)  # Make name editable

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

    def _on_item_changed(self, item):
        """Handle item changes (mainly for renaming)"""
        if not self._is_editing:
            return

        # Check if this is the name column
        if item.column() == 0 and self._editing_item == item:
            entry = item.data(Qt.ItemDataRole.UserRole)
            new_name = item.text().strip()

            if entry and new_name and new_name != self._old_name:
                # Emit rename signal
                self.entry_renamed.emit(entry, new_name)
            elif not new_name or new_name == "":
                # Restore old name if empty
                item.setText(self._old_name)

            # Reset editing state
            self._is_editing = False
            self._editing_item = None
            self._old_name = None

    def editItem(self, item):
        """Override to track when editing starts"""
        if item.column() == 0:  # Only allow editing of name column
            entry = item.data(Qt.ItemDataRole.UserRole)
            if entry:
                self._is_editing = True
                self._editing_item = item
                self._old_name = item.text()
        super().editItem(item)

    def apply_filter(self, filter_text=None, filter_type=None, filter_rw_version=None):
        """Apply filter to table entries"""
        for row in range(self.rowCount()):
            show_row = True

            name_item = self.item(row, 0)
            type_item = self.item(row, 1)
            rw_version_item = self.item(row, 4)  # RW Version column

            # Get the entry object to check RenderWare properties
            entry = name_item.data(Qt.ItemDataRole.UserRole) if name_item else None

            if not entry:
                continue

            # Text filter
            if filter_text and filter_text.lower() not in name_item.text().lower():
                show_row = False

            # File type filter - use entry.type property
            if filter_type and filter_type != "All":
                if entry.type != filter_type:
                    show_row = False

            # RenderWare version filter
            if filter_rw_version and filter_rw_version != "All Versions":
                if filter_rw_version == "RenderWare Only":
                    if not entry.is_renderware_file():
                        show_row = False
                else:
                    # For specific version names, check the entry's rw_version_name
                    if entry.rw_version_name != filter_rw_version:
                        show_row = False

            self.setRowHidden(row, not show_row)

    def _get_selected_entries_for_drag(self):
        """Get selected entries for drag operation"""
        selected_entries = []
        for index in self.selectedIndexes():
            if index.column() == 0:  # Only count each row once
                entry = self.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)
                if entry:
                    selected_entries.append(entry)
        return selected_entries

    def keyPressEvent(self, event):
        """Handle key press events for shortcuts"""
        # Handle Ctrl+E for export selected entries
        if (event.key() == Qt.Key.Key_E and 
            event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            selected_entries = self._get_selected_entries_for_drag()
            if selected_entries:
                export_dir = QFileDialog.getExistingDirectory(
                    self, 
                    "Export Selected Entries", 
                    "", 
                    QFileDialog.Option.ShowDirsOnly
                )

                if export_dir and self.drag_drop_handler:
                    self.drag_drop_handler.entries_exported.emit(selected_entries, export_dir)
            return

        super().keyPressEvent(event)

    def _handle_entry_drop(self, entries_data):
        """Handle dropping of IMG entries on this table"""
        if not self.drag_drop_handler or not self.current_archive:
            return

        success = self.drag_drop_handler.handle_entry_drop(entries_data, self.current_archive, self.img_controller)
        if success:
            debug_logger.info(LogCategory.UI, "Entry drop handled successfully")

    def mousePressEvent(self, event):
        """Handle mouse press for drag initiation"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mimeTypes(self):
        """Return supported MIME types for drag operations"""
        return ["application/x-img-entries", "text/plain"]

    def mimeData(self, indexes):
        """Create MIME data for drag operation"""
        selected_entries = self._get_selected_entries_for_drag()
        if not selected_entries or not self.drag_drop_handler:
            return QMimeData()

        mime_data = QMimeData()

        # Add IMG entries data for internal transfers
        entries_data = self.drag_drop_handler._serialize_entries(selected_entries, self.current_archive)
        mime_data.setData("application/x-img-entries", entries_data)

        # For external drops, create temporary files and add as URLs
        try:
            import tempfile
            from .core.Import_Export import Import_Export

            # Create temporary directory for exported files
            temp_dir = tempfile.mkdtemp(prefix="img_drag_")
            urls = []

            for entry in selected_entries:
                try:
                    # Export entry to temporary file
                    temp_file_path = Import_Export.export_entry(self.current_archive, entry, output_dir=temp_dir)
                    urls.append(QUrl.fromLocalFile(temp_file_path))
                except Exception as e:
                    debug_logger.log_exception(LogCategory.UI, f"Failed to create temp file for {entry.name}", e)

            if urls:
                mime_data.setUrls(urls)
                # Store temp directory for cleanup
                mime_data.setData("application/x-temp-dir", temp_dir.encode('utf-8'))

        except Exception as e:
            debug_logger.log_exception(LogCategory.UI, "Failed to create temporary files for external drag", e)

        # Set text representation
        entry_names = [entry.name for entry in selected_entries]
        mime_data.setText(f"IMG Entries: {', '.join(entry_names)}")

        return mime_data

    def startDrag(self, supportedActions):
        """Start drag operation for selected entries"""
        selected_entries = self._get_selected_entries_for_drag()
        if not selected_entries:
            return

        # Check if Ctrl key is pressed for export mode
        modifiers = QApplication.keyboardModifiers()
        export_mode = modifiers & Qt.KeyboardModifier.ControlModifier

        if export_mode:
            # Export mode - ask user for export directory
            export_dir = QFileDialog.getExistingDirectory(
                self, 
                "Select Export Directory", 
                "", 
                QFileDialog.Option.ShowDirsOnly
            )

            if export_dir and self.drag_drop_handler:
                # Trigger export operation
                self.drag_drop_handler.entries_exported.emit(selected_entries, export_dir)
            return

        # Use Qt's built-in drag system with our custom MIME data
        drag = QDrag(self)
        mime_data = self.mimeData(self.selectedIndexes())

        if mime_data and self.drag_drop_handler:
            drag.setMimeData(mime_data)

            # Create drag pixmap
            pixmap = self.drag_drop_handler.create_drag_pixmap(selected_entries)
            drag.setPixmap(pixmap)
            drag.setHotSpot(pixmap.rect().center())

            # Execute drag
            result = drag.exec(supportedActions)

            # Clean up temporary files after drag operation
            self._cleanup_temp_files(mime_data)

            # Log result
            result_str = "CopyAction" if result == Qt.DropAction.CopyAction else \
                        "MoveAction" if result == Qt.DropAction.MoveAction else \
                        "IgnoreAction" if result == Qt.DropAction.IgnoreAction else str(result)

            debug_logger.info(LogCategory.UI, "Table drag operation completed", 
                            {"entries_count": len(selected_entries), "result": result_str})

    def _cleanup_temp_files(self, mime_data):
        """Clean up temporary files created for external drag operations"""
        try:
            if mime_data.hasFormat("application/x-temp-dir"):
                temp_dir_data = mime_data.data("application/x-temp-dir")
                temp_dir = temp_dir_data.data().decode('utf-8')

                if temp_dir and os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    debug_logger.debug(LogCategory.UI, "Cleaned up temporary drag files", 
                                     {"temp_dir": temp_dir})
        except Exception as e:
            debug_logger.log_exception(LogCategory.UI, "Failed to cleanup temporary drag files", e)

    def mouseMoveEvent(self, event):
        """Handle mouse move for drag initiation"""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            super().mouseMoveEvent(event)
            return

        if not hasattr(self, 'drag_start_position'):
            super().mouseMoveEvent(event)
            return

        # Check if we've moved far enough to start a drag
        if ((event.pos() - self.drag_start_position).manhattanLength() < 
            QApplication.startDragDistance()):
            super().mouseMoveEvent(event)
            return

        # Start drag operation if we have selected entries
        selected_entries = self._get_selected_entries_for_drag()
        if selected_entries and self.drag_drop_handler:
            self.startDrag(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction)

        super().mouseMoveEvent(event)

    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if not self.drag_drop_handler:
            event.ignore()
            return

        mime_data = event.mimeData()

        # Check for file drops
        if mime_data.hasUrls():
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if (os.path.isfile(file_path) and 
                        self.drag_drop_handler.is_supported_file(file_path)) or os.path.isdir(file_path):
                        event.acceptProposedAction()
                        return

        # Check for entry drops
        if mime_data.hasFormat("application/x-img-entries"):
            event.acceptProposedAction()
            return

        event.ignore()

    def dragMoveEvent(self, event):
        """Handle drag move event"""
        if self.drag_drop_handler:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Handle drop event"""
        if not self.drag_drop_handler:
            event.ignore()
            return

        mime_data = event.mimeData()

        # Handle file drops
        if mime_data.hasUrls():
            file_paths = []
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    file_paths.append(file_path)

            if file_paths:
                # Emit signal instead of calling handler directly to avoid duplicate imports
                self.files_dropped.emit(file_paths)
                event.acceptProposedAction()
                return

        # Handle entry drops
        if mime_data.hasFormat("application/x-img-entries"):
            entries_data = mime_data.data("application/x-img-entries")
            self._handle_entry_drop(entries_data)
            event.acceptProposedAction()
            return

        event.ignore()


class FilterPanel(QWidget):
    """Filter panel for IMG entries"""
    filter_changed = pyqtSignal(str, str, str)  # text_filter, type_filter, rw_version_filter

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

    def update_file_type_options(self, file_types):
        """Update file type filter options based on available types in the archive"""
        current_selection = self.type_combo.currentText()
        
        # Clear and add 'All' first
        self.type_combo.clear()
        self.type_combo.addItem('All')
        
        # Add only the file types that are actually present
        for file_type in sorted(file_types):
            if file_type:  # Skip empty types
                self.type_combo.addItem(file_type)
        
        # Try to restore previous selection if it still exists
        index = self.type_combo.findText(current_selection)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)
        else:
            self.type_combo.setCurrentIndex(0)  # Default to 'All'

    def update_rw_version_options(self, rw_versions):
        """Update RenderWare version filter options based on available versions in the archive"""
        current_selection = self.rw_version_combo.currentText()
        
        # Clear and add standard options first
        self.rw_version_combo.clear()
        self.rw_version_combo.addItem('All Versions')
        self.rw_version_combo.addItem('RenderWare Only')
    
        
        # Add only the versions that are actually present 
        for version_value, version_name in rw_versions:
            if version_name and version_name not in ['All Versions', 'RenderWare Only']:
                self.rw_version_combo.addItem(version_name)
        
        # Try to restore previous selection if it still exists
        index = self.rw_version_combo.findText(current_selection)
        if index >= 0:
            self.rw_version_combo.setCurrentIndex(index)
        else:
            self.rw_version_combo.setCurrentIndex(0)  # Default to 'All Versions'

    def update_filter_options(self, img_archive):
        """Update both file type and RW version options based on the archive content"""
        if img_archive and hasattr(img_archive, 'entries'):
            # Get unique file types and RW versions from the archive
            file_types = img_archive.get_unique_file_types()
            rw_versions = img_archive.get_unique_rw_versions()
            
            # Update the comboboxes
            self.update_file_type_options(file_types)
            self.update_rw_version_options(rw_versions)
        else:
            # Reset to default options if no archive
            self.reset_filter_options()

    def reset_filter_options(self):
        """Reset filter options to default (empty archive state)"""
        self.type_combo.clear()
        self.type_combo.addItem('All')
        
        self.rw_version_combo.clear()
        self.rw_version_combo.addItem('All Versions')
        self.rw_version_combo.addItem('RenderWare Only')


__all__ = [
    "IMGFileInfoPanel",
    "IMGEntriesTable",
    "FilterPanel",
]
