#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyQt6-based RW Analyze tool integrated into the Renderware Modding Suite.
- Parses RW chunks generically and displays a recursive tree
- Shows selected chunk header details and basic file metadata
- Themed to match the Renderware Modding Suite style
- Implements full import/export functionality
- Integrated with the suite's custom debug_system

Uses:
- application.debug_system for logging
- application.tools.RW_Analyze.RW_Analyze_core for low-level constants/helpers
- application.common.rw_versions for version decoding
"""
from __future__ import annotations

import io
import os
from dataclasses import dataclass
from typing import List, Optional
from application.common.message_box import MessageBox


from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QTextEdit,
    QLabel,
    QMenu,
    QMessageBox,
    QSizePolicy,
)

# Suite integrations
from application.debug_system import get_debug_logger, LogCategory
from application.responsive_utils import get_responsive_manager
from application.styles import ModernDarkTheme

# RW helpers
from application.tools.RW_Analyze import RW_Analyze_core as core
from application.common.rw_versions import RWVersionManager

# Initialize RW Version Manager
rw_version_manager = RWVersionManager()


@dataclass
class ChunkHeader:
    """A dataclass to hold parsed information about a RenderWare chunk header."""
    type_raw: int
    size: int
    version: int
    offset: int

    @property
    def type_name(self) -> str:
        """Return the Enum name for the chunk type, or a hex string if unknown."""
        member = core.ChunkType._value2member_map_.get(self.type_raw)
        return member.name if member is not None else f"UNKNOWN(0x{self.type_raw:X})"

    @property
    def version_name(self) -> str:
        """Return the friendly name for the RW version."""
        try:
            version_info = rw_version_manager.get_version_info(self.version)
            if version_info.get('game_info'):
                game = version_info['game_info']['display_name']
                return f"{version_info['version_string']} ({game})"
            return version_info['version_string']
        except Exception:
            return f"0x{self.version:X}"


class RWAnalyzeTool(QWidget):
    """The main widget for the RenderWare Analyze tool."""
    tool_action = pyqtSignal(str, str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.debug = get_debug_logger()
        self.current_path: Optional[str] = None
        self.current_data: Optional[bytes] = None
        self.chunk_list: List[ChunkHeader] = []
        self._setup_ui()
        self.debug.info(LogCategory.UI, "RWAnalyzeTool initialized")

    # -------------------- UI Setup --------------------
    def _setup_ui(self):
        """Initializes the user interface and applies styling."""
        rm = get_responsive_manager()
        fonts = rm.get_font_config()
        spacing = rm.get_spacing_config()

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(spacing['medium'], spacing['medium'], spacing['medium'], spacing['medium'])
        outer_layout.setSpacing(spacing['medium'])

        header_label = QLabel("🔎 RenderWare File Analyzer")
        header_label.setStyleSheet(f"font-weight: bold; font-size: {fonts['header']['size']}px; padding-bottom: {spacing['small']}px;")
        outer_layout.addWidget(header_label)

        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(spacing['medium'])
        self.btn_open = QPushButton("📂 Open RW File…")
        self.btn_close = QPushButton("❌ Close File")
        self.lbl_path = QLabel("No file loaded.")
        self.lbl_path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lbl_path.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar_layout.addWidget(self.btn_open)
        toolbar_layout.addWidget(self.btn_close)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.lbl_path, 2)
        outer_layout.addLayout(toolbar_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Chunk", "Size", "Version", "Offset"])
        self.tree.setUniformRowHeights(True)
        self.tree.setColumnWidth(0, 280)

        self.details = QTextEdit()
        self.details.setReadOnly(True)

        splitter.addWidget(self.tree)
        splitter.addWidget(self.details)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        outer_layout.addWidget(splitter, 1)

        self._apply_styles(fonts, spacing)

        self.btn_open.clicked.connect(self._on_open)
        self.btn_close.clicked.connect(self._close_file)
        self.tree.currentItemChanged.connect(self._on_item_selected)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        
        self._close_file() # Set initial state

    def _apply_styles(self, fonts, spacing):
        """Applies consistent styling based on the suite's theme."""
        self.lbl_path.setStyleSheet(f"font-size: {fonts['body']['size']}px; color: {ModernDarkTheme.TEXT_SECONDARY};")
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {ModernDarkTheme.BACKGROUND_SECONDARY};
                border: 1px solid {ModernDarkTheme.BORDER_PRIMARY};
                font-size: {fonts['body']['size']}px;
                color: {ModernDarkTheme.TEXT_PRIMARY};
            }}
            QTreeWidget::item:selected {{
                background-color: {ModernDarkTheme.TEXT_ACCENT};
                color: #ffffff;
            }}
            QTreeWidget::item:hover {{
                background-color: {ModernDarkTheme.HOVER_COLOR};
            }}
            QHeaderView::section {{
                background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
                color: white;
                padding: {spacing['small']}px;
                border: 1px solid {ModernDarkTheme.BORDER_PRIMARY};
                font-weight: bold;
            }}
        """)
        self.details.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
                color: {ModernDarkTheme.TEXT_PRIMARY};
                border: 1px solid {ModernDarkTheme.BORDER_PRIMARY};
                border-radius: 3px;
                padding: {spacing['small']}px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: {fonts['code']['size']}px;
            }}
        """)

    # -------------------- File Operations --------------------
    def _on_open(self):
        """Handles the 'Open File' button click."""
        self.debug.log_user_action("Clicked 'Open RW File'")
        path, _ = QFileDialog.getOpenFileName(self, "Open RenderWare file", "", "RenderWare Files (*.dff *.txd *.col *.anm *.bsp);;All Files (*.*)")
        if path:
            self.load_file(path)

    def load_file(self, path: str):
        """Loads and parses a RenderWare file from the given path."""
        self.debug.info(LogCategory.FILE_IO, f"Attempting to load file: {path}")
        try:
            with open(path, 'rb') as f:
                data = f.read()
            self.debug.log_file_operation("load", path, success=True, details={"size_bytes": len(data)})
        except Exception as e:
            self.debug.log_exception(LogCategory.FILE_IO, f"Failed to read file: {path}", e)
            MessageBox.error(f"Could not open file:\n{e}", "Open Error", self)
            return

        self.current_path = path
        self.current_data = data
        self.lbl_path.setText(f"<b>{os.path.basename(path)}</b> ({len(data):,} bytes)")
        self.btn_close.setEnabled(True)
        self._populate_tree(data)
        self.tool_action.emit('rw_analyze', f'opened:{path}')

    def _close_file(self):
        """Resets the tool to its initial state."""
        if self.current_path:
            self.debug.log_user_action("Closed file", {"path": self.current_path})
        self.current_path = None
        self.current_data = None
        self.chunk_list.clear()
        self.tree.clear()
        self.details.setText("Open a RenderWare file (.dff, .txd, .col, etc) to begin analysis.")
        self.lbl_path.setText("No file loaded.")
        self.btn_close.setEnabled(False)

    # -------------------- Parsing Logic --------------------
    def _populate_tree(self, data: bytes):
        """Clears the tree and populates it by parsing the file data."""
        timer_id = self.debug.start_performance_timer("Parse RW Tree")
        self.tree.clear()
        self.chunk_list.clear()
        self.details.clear()
        buf = io.BytesIO(data)
        filesize = len(data)

        if filesize < 12:
            self.details.setPlainText("File is too small to be a valid RenderWare file.")
            self.debug.warning(LogCategory.TOOL, "File too small to be valid RW", {"size": filesize, "path": self.current_path})
            self.debug.end_performance_timer(timer_id)
            return

        fmt, fmt_str, ver = rw_version_manager.detect_file_format_version(data, self.current_path or "")
        root_title = f"{os.path.basename(self.current_path or 'File')} ({fmt_str})"
        
        # Get version name using new system
        if ver > 0:
            version_info = rw_version_manager.get_version_info(ver)
            if version_info.get('game_info'):
                game = version_info['game_info']['display_name']
                version_display = f"{version_info['version_string']} ({game})"
            else:
                version_display = version_info['version_string']
        else:
            version_display = "Unknown"
            
        root = QTreeWidgetItem([root_title, str(filesize), version_display, "0x0"])
        root.setData(0, Qt.ItemDataRole.UserRole, {"kind": "root"})
        self.tree.addTopLevelItem(root)

        try:
            self._read_children(buf, filesize, root)
        except Exception as e:
            self.debug.log_exception(LogCategory.TOOL, "Error occurred during RW parsing", e)
            MessageBox.error(f"An error occurred during parsing:\n{e}", "Parsing Error", self)
        
        self.tree.expandToDepth(0)
        self.tree.setCurrentItem(root)
        self.debug.end_performance_timer(timer_id)

    def _read_header(self, stream: io.BytesIO) -> Optional[ChunkHeader]:
        """Reads a 12-byte chunk header from the stream."""
        offset = stream.tell()
        header_bytes = stream.read(12)
        if len(header_bytes) < 12:
            return None
        return ChunkHeader(
            int.from_bytes(header_bytes[0:4], 'little'),
            int.from_bytes(header_bytes[4:8], 'little'),
            int.from_bytes(header_bytes[8:12], 'little'),
            offset
        )

    def _read_children(self, stream: io.BytesIO, limit: int, parent_item: QTreeWidgetItem):
        """Recursively reads all sibling chunks within the given limit."""
        while stream.tell() + 12 <= limit:
            start_pos = stream.tell()
            header = self._read_header(stream)
            if header is None:
                break

            display_name = header.type_name
            if header.type_name == 'ASSET':
                current_pos = stream.tell()
                try:
                    stream.seek(4, 1)
                    name_size = int.from_bytes(stream.read(4), 'little')
                    if 0 < name_size < 256:
                        name_bytes = stream.read(name_size)
                        name = name_bytes.rstrip(b'\x00\xBF').decode('utf-8', errors='ignore')
                        clean_name = ''.join(c for c in name if c.isprintable())
                        if clean_name:
                            display_name = f"ASSET: {clean_name}"
                finally:
                    stream.seek(current_pos)

            item = QTreeWidgetItem([display_name, str(header.size), header.version_name, f"0x{header.offset:X}"])
            item.setData(0, Qt.ItemDataRole.UserRole, {"kind": "chunk", "header": header})
            parent_item.addChild(item)

            payload_start = stream.tell()
            payload_end = payload_start + header.size

            if payload_end > limit:
                item.setForeground(0, QtGui.QBrush(QtGui.QColor("red")))
                item.setToolTip(0, f"Corrupt size: chunk ends at 0x{payload_end:X}, which is outside its parent's limit of 0x{limit:X}.")
                stream.seek(limit)
                continue

            if header.size >= 12:
                self._read_children(stream, payload_end, item)

            stream.seek(payload_end)

            if stream.tell() <= start_pos:
                item.setForeground(0, QtGui.QBrush(QtGui.QColor("orange")))
                item.setToolTip(0, "Zero-size or negative-size chunk detected; parsing of this branch stopped.")
                break

    # -------------------- UI Interaction & Functionality --------------------
    def _on_item_selected(self, current: Optional[QTreeWidgetItem], _prev: Optional[QTreeWidgetItem]):
        """Updates the details view when a new item is selected in the tree."""
        if current:
            self._show_properties(current)
        else:
            self.details.clear()

    def _show_context_menu(self, position):
        """Shows a context menu for the selected tree item."""
        item = self.tree.itemAt(position)
        if not item or (item.data(0, Qt.ItemDataRole.UserRole) or {}).get("kind") != "chunk":
            return
            
        menu = QMenu(self)
        menu.addAction("Export Full Chunk...").triggered.connect(lambda: self._export_full_chunk(item))
        menu.addAction("Export Payload Only...").triggered.connect(lambda: self._export_payload(item))
        menu.addSeparator()
        menu.addAction("Import and Replace Payload...").triggered.connect(lambda: self._import_and_replace_payload(item))
        menu.addSeparator()
        menu.addAction("Show Properties").triggered.connect(lambda: self._show_properties(item))
        
        menu.exec(self.tree.mapToGlobal(position))

    def _show_properties(self, item: QTreeWidgetItem):
        """Displays detailed properties for the selected item in the details view."""
        meta = item.data(0, Qt.ItemDataRole.UserRole) or {}
        if meta.get("kind") == "root":
            info = [
                f"File: {self.current_path}",
                f"Size: {len(self.current_data):,} bytes",
            ]
            self.details.setPlainText("\n".join(info))
            return
            
        header: ChunkHeader = meta.get("header")
        if header:
            props = [
                f"Chunk Type:    {header.type_name}",
                f"Raw Type ID:   0x{header.type_raw:08X}",
                "---------------------------------",
                f"Payload Size:  {header.size:,} bytes",
                f"RW Version:    {header.version_name}",
                f"Raw Version:   0x{header.version:08X}",
                "---------------------------------",
                f"File Offset:   0x{header.offset:08X} ({header.offset:,})",
                f"End of Chunk:  0x{header.offset + 12 + header.size:08X}",
            ]
            self.details.setPlainText("\n".join(props))

    def _export_full_chunk(self, item: QTreeWidgetItem):
        """Exports the full binary data of a chunk (header + payload)."""
        header: ChunkHeader = (item.data(0, Qt.ItemDataRole.UserRole) or {}).get("header")
        if not header or not self.current_data: return
        
        self.debug.log_user_action("Export Full Chunk", {"chunk_type": header.type_name, "offset": header.offset})
        data_to_export = self.current_data[header.offset : header.offset + 12 + header.size]
        filename = f"{header.type_name}_{header.offset:08X}_full.bin"
        self._save_data_to_file(data_to_export, "Export Full Chunk", filename)

    def _export_payload(self, item: QTreeWidgetItem):
        """Exports only the payload of a chunk, with special handling for ASSET types."""
        header: ChunkHeader = (item.data(0, Qt.ItemDataRole.UserRole) or {}).get("header")
        if not header or not self.current_data: return

        self.debug.log_user_action("Export Payload", {"chunk_type": header.type_name, "offset": header.offset})
        payload = self.current_data[header.offset + 12 : header.offset + 12 + header.size]
        data_to_export = payload
        
        if header.type_name == 'ASSET' and len(payload) > 8:
            try:
                asset_stream = io.BytesIO(payload)
                asset_stream.seek(4)
                sub_header_size = int.from_bytes(asset_stream.read(4), 'little')
                asset_stream.seek(sub_header_size, 1)
                asset_size = int.from_bytes(asset_stream.read(4), 'little')
                if asset_size <= len(payload) - asset_stream.tell():
                    data_to_export = asset_stream.read(asset_size)
            except Exception as e:
                self.debug.log_exception(LogCategory.TOOL, "Could not parse ASSET payload for export", e)

        filename = f"{header.type_name}_{header.offset:08X}_payload.bin"
        self._save_data_to_file(data_to_export, "Export Payload", filename)

    def _import_and_replace_payload(self, item: QTreeWidgetItem):
        """Replaces a chunk's payload with data from an external file."""
        header: ChunkHeader = (item.data(0, Qt.ItemDataRole.UserRole) or {}).get("header")
        if not header or not self.current_data: return

        self.debug.log_user_action("Initiated Payload Import", {"chunk_type": header.type_name, "offset": header.offset})
        warning_text = (
            "This will replace the content of the selected chunk and all its children. "
            "The modified result must be saved as a NEW file.\n\n"
            "This can easily corrupt the file if the imported data is not correctly formatted. "
            "Make sure you have a backup.\n\nDo you want to proceed?"
        )
        resp = QMessageBox.question(
            self,
            "Warning: Destructive Operation",
            warning_text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        path, _ = QFileDialog.getOpenFileName(self, "Select file to import as payload", "", "All Files (*.*)")
        if not path: return

        try:
            with open(path, 'rb') as f:
                imported_data = f.read()
            self.debug.log_file_operation("import_read", path, True, {"size": len(imported_data)})
        except Exception as e:
            self.debug.log_exception(LogCategory.FILE_IO, f"Failed to read import file: {path}", e)
            MessageBox.error(f"Failed to read import file:\n{e}", "Error", self)
            return

        before_data = self.current_data[0:header.offset]
        after_data = self.current_data[header.offset + 12 + header.size:]
        
        new_header_bytes = b''.join([
            header.type_raw.to_bytes(4, 'little'),
            len(imported_data).to_bytes(4, 'little'),
            header.version.to_bytes(4, 'little')
        ])
        
        new_file_data = before_data + new_header_bytes + imported_data + after_data
        
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Modified File As...", os.path.basename(self.current_path), "All Files (*.*)")
        if not save_path: return

        try:
            with open(save_path, 'wb') as f:
                f.write(new_file_data)
            self.debug.log_file_operation("import_write", save_path, True, {"size": len(new_file_data)})
            resp2 = QMessageBox.question(
                self,
                "Import Complete",
                "File saved successfully. Load the new file now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp2 == QMessageBox.StandardButton.Yes:
                self.load_file(save_path)
        except Exception as e:
            self.debug.log_exception(LogCategory.FILE_IO, f"Failed to save modified file: {save_path}", e)
            MessageBox.error(f"Failed to save modified file:\n{e}", "Error", self)

    def _save_data_to_file(self, data: bytes, title: str, filename: str):
        """Utility to show a save dialog and write data to a file."""
        path, _ = QFileDialog.getSaveFileName(self, title, filename, "Binary Files (*.bin);;All Files (*.*)")
        if path:
            try:
                with open(path, 'wb') as f:
                    f.write(data)
                self.debug.log_file_operation("export", path, True, {"size": len(data)})
                MessageBox.success(f"Data exported successfully to:\n{path}", "Export Complete", self)
            except Exception as e:
                self.debug.log_exception(LogCategory.FILE_IO, f"Failed to write exported data to: {path}", e)
                MessageBox.error(f"Failed to export data:\n{e}", "Export Error", self)