"""
Drag and Drop Handler for IMG Editor
Provides comprehensive drag and drop functionality for importing files and transferring entries between IMG archives.
"""

import os
from pathlib import Path
from PyQt6.QtCore import Qt, QMimeData, QUrl, pyqtSignal, QObject
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QDrag, QPainter, QPixmap, QFont, QColor

from application.debug_system import get_debug_logger, LogCategory
from application.common.message_box import message_box

# Module-level logger
debug_logger = get_debug_logger()


class DragDropHandler(QObject):
    """Handles drag and drop operations for IMG Editor"""
    
    # Signals
    files_dropped = pyqtSignal(list)  # List of file paths
    entries_dropped = pyqtSignal(list, object)  # List of entries, target archive
    entries_exported = pyqtSignal(list, str)  # List of entries, export directory
    drag_started = pyqtSignal()
    drag_finished = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.supported_extensions = {
            '.dff', '.txd', '.col', '.ifp', '.ipl', '.dat', '.wav', 
            '.img', '.ide', '.cfg', '.rrr', '.scm', '.fxt', '.gxt'
        }
        self.drag_in_progress = False
        
    def is_supported_file(self, file_path):
        """Check if file extension is supported for import"""
        ext = Path(file_path).suffix.lower()
        return ext in self.supported_extensions
    
    def validate_drop_data(self, mime_data):
        """Validate dropped data and return file paths or entries"""
        if not mime_data:
            return None, "No data provided"
        
        # Check for file URLs (external files)
        if mime_data.hasUrls():
            file_paths = []
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if os.path.isfile(file_path):
                        if self.is_supported_file(file_path):
                            file_paths.append(file_path)
                        else:
                            debug_logger.warning(LogCategory.UI, 
                                               f"Unsupported file type: {Path(file_path).suffix}")
                    elif os.path.isdir(file_path):
                        # Handle directory drops - find supported files
                        dir_files = self._get_supported_files_from_directory(file_path)
                        file_paths.extend(dir_files)
            
            if file_paths:
                return file_paths, None
            else:
                return None, "No supported files found in drop"
        
        # Check for IMG entries (internal drag and drop)
        if mime_data.hasFormat("application/x-img-entries"):
            try:
                entries_data = mime_data.data("application/x-img-entries")
                # This would contain serialized entry information
                return entries_data, None
            except Exception as e:
                debug_logger.log_exception(LogCategory.UI, "Failed to parse IMG entries data", e)
                return None, "Invalid IMG entries data"
        
        return None, "Unsupported data format"
    
    def _get_supported_files_from_directory(self, directory_path, recursive=False):
        """Get all supported files from a directory"""
        supported_files = []
        
        try:
            if recursive:
                for root, dirs, files in os.walk(directory_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if self.is_supported_file(file_path):
                            supported_files.append(file_path)
            else:
                for item in os.listdir(directory_path):
                    item_path = os.path.join(directory_path, item)
                    if os.path.isfile(item_path) and self.is_supported_file(item_path):
                        supported_files.append(item_path)
        except Exception as e:
            debug_logger.log_exception(LogCategory.FILE_IO, 
                                     f"Error scanning directory {directory_path}", e)
        
        return supported_files
    
    def create_drag_pixmap(self, entries, drag_text=""):
        """Create a visual representation for drag operations"""
        try:
            # Create a pixmap for the drag operation
            pixmap = QPixmap(200, 60)
            pixmap.fill(QColor(50, 50, 50, 180))
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Set font
            font = QFont("Arial", 10, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))
            
            # Draw text
            if not drag_text:
                if len(entries) == 1:
                    drag_text = f"Moving: {entries[0].name}"
                else:
                    drag_text = f"Moving: {len(entries)} entries"
            
            # Truncate text if too long
            if len(drag_text) > 25:
                drag_text = drag_text[:22] + "..."
            
            painter.drawText(10, 20, drag_text)
            painter.drawText(10, 40, f"Count: {len(entries)}")
            
            painter.end()
            return pixmap
            
        except Exception as e:
            debug_logger.log_exception(LogCategory.UI, "Failed to create drag pixmap", e)
            # Return a simple default pixmap
            pixmap = QPixmap(100, 30)
            pixmap.fill(QColor(100, 100, 100))
            return pixmap
    
    def start_entry_drag(self, source_widget, entries, source_archive=None):
        """Start a drag operation for IMG entries"""
        if not entries:
            return
        
        try:
            self.drag_in_progress = True
            self.drag_started.emit()
            
            drag = QDrag(source_widget)
            mime_data = QMimeData()
            
            # Create custom MIME data for IMG entries
            entries_data = self._serialize_entries(entries, source_archive)
            if entries_data:
                mime_data.setData("application/x-img-entries", entries_data)
            
            # Also set text representation for debugging
            entry_names = [entry.name for entry in entries]
            mime_data.setText(f"IMG Entries: {', '.join(entry_names)}")
            
            # Set the MIME data on the drag object BEFORE creating pixmap
            drag.setMimeData(mime_data)
            
            # Create drag pixmap
            pixmap = self.create_drag_pixmap(entries)
            drag.setPixmap(pixmap)
            drag.setHotSpot(pixmap.rect().center())
            
            # Execute drag
            result = drag.exec(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction)
            
            # Convert DropAction to string for logging
            result_str = "CopyAction" if result == Qt.DropAction.CopyAction else \
                        "MoveAction" if result == Qt.DropAction.MoveAction else \
                        "IgnoreAction" if result == Qt.DropAction.IgnoreAction else str(result)
            
            debug_logger.info(LogCategory.UI, "Drag operation completed", 
                            {"entries_count": len(entries), "result": result_str})
            
        except Exception as e:
            debug_logger.log_exception(LogCategory.UI, "Failed to start entry drag", e)
        finally:
            self.drag_in_progress = False
            self.drag_finished.emit()
    
    def _serialize_entries(self, entries, source_archive):
        """Serialize entries for drag and drop transfer"""
        try:
            import json
            
            serialized_data = {
                "entries": [],
                "source_archive_path": source_archive.file_path if source_archive else None,
                "timestamp": str(QApplication.instance().applicationPid())  # Simple unique identifier
            }
            
            for entry in entries:
                entry_data = {
                    "name": entry.name,
                    "type": entry.type,
                    "size": entry.actual_size,
                    "offset": entry.offset,
                    "is_compressed": entry.is_compressed,
                    # Add other relevant entry properties
                }
                serialized_data["entries"].append(entry_data)
            
            return json.dumps(serialized_data).encode('utf-8')
            
        except Exception as e:
            debug_logger.log_exception(LogCategory.UI, "Failed to serialize entries", e)
            return b""
    
    def deserialize_entries(self, entries_data, controller):
        """Deserialize entries from drag and drop data"""
        try:
            import json
            
            data = json.loads(entries_data.decode('utf-8'))
            source_archive_path = data.get("source_archive_path")
            entry_info_list = data.get("entries", [])
            
            if not source_archive_path or not entry_info_list:
                return None, None
            
            # Get the source archive from controller
            source_archive = controller.get_archive_by_path(source_archive_path)
            if not source_archive:
                debug_logger.error(LogCategory.UI, "Source archive not found", 
                                 {"path": source_archive_path})
                return None, None
            
            # Get actual entry objects
            entries = []
            for entry_info in entry_info_list:
                entry = source_archive.get_entry_by_name(entry_info["name"])
                if entry:
                    entries.append(entry)
                else:
                    debug_logger.warning(LogCategory.UI, "Entry not found in source archive", 
                                       {"entry_name": entry_info["name"]})
            
            return entries, source_archive
            
        except Exception as e:
            debug_logger.log_exception(LogCategory.UI, "Failed to deserialize entries", e)
            return None, None
    
    def handle_file_drop(self, file_paths, target_widget, controller):
        """Handle dropping of external files"""
        if not file_paths:
            return
        
        try:
            debug_logger.info(LogCategory.UI, "Handling file drop", 
                            {"file_count": len(file_paths), "target": type(target_widget).__name__})
            
            # Validate files
            valid_files = []
            invalid_files = []
            
            for file_path in file_paths:
                if os.path.isfile(file_path) and self.is_supported_file(file_path):
                    valid_files.append(file_path)
                else:
                    invalid_files.append(file_path)
            
            if invalid_files:
                debug_logger.warning(LogCategory.UI, "Some files are not supported", 
                                   {"invalid_count": len(invalid_files)})
            
            if not valid_files:
                message_box.warning("No supported files found in the dropped items.", 
                                  "Drag and Drop", target_widget)
                return
            
            # Emit signal for files to be imported
            self.files_dropped.emit(valid_files)
            
        except Exception as e:
            debug_logger.log_exception(LogCategory.UI, "Failed to handle file drop", e)
            message_box.error(f"Error handling dropped files: {str(e)}", 
                            "Drag and Drop Error", target_widget)
    
    def handle_entry_drop(self, entries_data, target_archive, controller):
        """Handle dropping of IMG entries between archives"""
        try:
            entries, source_archive = self.deserialize_entries(entries_data, controller)
            
            if not entries or not source_archive:
                debug_logger.error(LogCategory.UI, "Failed to deserialize dropped entries")
                return False
            
            if source_archive == target_archive:
                debug_logger.info(LogCategory.UI, "Dropping entries on same archive - no action needed")
                return True
            
            debug_logger.info(LogCategory.UI, "Handling entry drop between archives", 
                            {"entries_count": len(entries), 
                             "source": source_archive.file_path,
                             "target": target_archive.file_path})
            
            # Emit signal for entries to be transferred
            self.entries_dropped.emit(entries, target_archive)
            return True
            
        except Exception as e:
            debug_logger.log_exception(LogCategory.UI, "Failed to handle entry drop", e)
            return False
    
    def handle_entry_export(self, entries_data, export_directory, controller):
        """Handle dropping of IMG entries to external directory for export"""
        try:
            entries, source_archive = self.deserialize_entries(entries_data, controller)
            
            if not entries or not source_archive:
                debug_logger.error(LogCategory.UI, "Failed to deserialize dropped entries for export")
                return False
            
            debug_logger.info(LogCategory.UI, "Handling entry export to directory", 
                            {"entries_count": len(entries), 
                             "source": source_archive.file_path,
                             "export_dir": export_directory})
            
            # Emit signal for entries to be exported
            self.entries_exported.emit(entries, export_directory)
            return True
            
        except Exception as e:
            debug_logger.log_exception(LogCategory.UI, "Failed to handle entry export", e)
            return False


class DragDropMixin:
    """Mixin class to add drag and drop functionality to widgets"""
    
    def __init__(self):
        self.drag_drop_handler = None
        self.accept_file_drops = True
        self.accept_entry_drops = True
        self.enable_entry_dragging = True
    
    def setup_drag_drop(self, handler, accept_files=True, accept_entries=True, enable_dragging=True):
        """Setup drag and drop functionality"""
        self.drag_drop_handler = handler
        self.accept_file_drops = accept_files
        self.accept_entry_drops = accept_entries
        self.enable_entry_dragging = enable_dragging
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        if enable_dragging:
            self.setDragEnabled(True)
            self.setDragDropMode(self.DragDropMode.DragDrop)
    
    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if not self.drag_drop_handler:
            event.ignore()
            return
        
        mime_data = event.mimeData()
        
        # Check if we can accept this data
        if self.accept_file_drops and mime_data.hasUrls():
            # Check if any URLs are supported files
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if (os.path.isfile(file_path) and 
                        self.drag_drop_handler.is_supported_file(file_path)) or os.path.isdir(file_path):
                        event.acceptProposedAction()
                        return
        
        if self.accept_entry_drops and mime_data.hasFormat("application/x-img-entries"):
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
        if self.accept_file_drops and mime_data.hasUrls():
            file_paths = []
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_paths.append(url.toLocalFile())
            
            if file_paths:
                self.drag_drop_handler.handle_file_drop(file_paths, self, None)
                event.acceptProposedAction()
                return
        
        # Handle entry drops
        if self.accept_entry_drops and mime_data.hasFormat("application/x-img-entries"):
            entries_data = mime_data.data("application/x-img-entries")
            # This would need to be handled by the specific widget implementation
            self._handle_entry_drop(entries_data)
            event.acceptProposedAction()
            return
        
        event.ignore()
    
    def _handle_entry_drop(self, entries_data):
        """Override this method in implementing classes"""
        pass
    
    def startDrag(self, supportedActions):
        """Start drag operation for selected entries"""
        if not self.enable_entry_dragging or not self.drag_drop_handler:
            return
        
        # This should be overridden by implementing classes to get selected entries
        selected_entries = self._get_selected_entries_for_drag()
        if selected_entries:
            self.drag_drop_handler.start_entry_drag(self, selected_entries)
    
    def _get_selected_entries_for_drag(self):
        """Override this method in implementing classes"""
        return []
