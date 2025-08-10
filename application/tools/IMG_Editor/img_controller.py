"""
IMG Controller - Main controller for the IMG Editor.
This module acts as a bridge between the UI components and the core backend classes,
implementing the controller in the MVC pattern.
"""

from pathlib import Path
import os

from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QObject, Signal

# Import core modules
from .core import (
    IMGEntry, 
    IMGArchive,
    File_Operations, 
    IMG_Operations,
    Import_Export
)
from .core.File_Operations import ArchiveManager

class IMGController(QObject):
    """
    Main controller class that connects the IMG Editor UI with backend functionality.
    Acts as a controller between the UI (View) and the data model (Model).
    Supports multiple IMG archives with tab-based management.
    """
    # Define signals for UI updates
    img_loaded = Signal(object)  # Signal emitted when an IMG file is loaded
    img_closed = Signal(str)  # Signal emitted when an IMG file is closed (file_path)
    entries_updated = Signal(list)  # Signal emitted when entries are updated
    operation_progress = Signal(int, str)  # Signal for long operations: progress, message
    operation_completed = Signal(bool, str)  # Signal for operation completion: success, message
    archive_switched = Signal(object)  # Signal when active archive changes
    
    def __init__(self):
        super().__init__()
        self.archive_manager = ArchiveManager()
        self.selected_entries = []  # List of currently selected entries
        self.recent_files = []  # List of recently opened files
        self.max_recent_files = 10  # Maximum number of recent files to track
    
    # Archive Management Methods
    
    def open_archive(self, file_path):
        """Opens a single IMG archive from the specified path."""
        try:
            # Check if already open
            if file_path in self.archive_manager.open_archives:
                # Switch to existing archive
                self.archive_manager.set_active_archive(file_path)
                active_archive = self.archive_manager.get_active_archive()
                self.archive_switched.emit(active_archive)
                return True, f"Switched to already open archive: {Path(file_path).name}"
            
            # Open new archive
            img_archive = File_Operations.open_archive(file_path, self.archive_manager)
            
            # Add to recent files
            self._add_to_recent_files(file_path)
            
            # Analyze RenderWare versions for all entries
            if img_archive and hasattr(img_archive, 'entries') and img_archive.entries:
                img_archive.analyze_all_entries_rw_versions()
            
            # Emit signal with the loaded archive
            self.img_loaded.emit(img_archive)
            
            return True, f"Successfully opened {Path(file_path).name}"
            
        except Exception as e:
            return False, f"Error opening IMG file: {str(e)}"
    
    def open_multiple_archives(self, file_paths):
        """Opens multiple IMG archives."""
        if not file_paths:
            return False, "No files selected"
        
        try:
            success_count, failed_files, error_messages = File_Operations.open_multiple_archives(
                file_paths, self.archive_manager
            )
            
            # Add successful files to recent files
            for file_path in file_paths:
                if file_path not in failed_files:
                    self._add_to_recent_files(file_path)
            
            # Analyze RenderWare versions for all successfully opened archives
            for file_path in self.archive_manager.get_archive_paths():
                img_archive = self.archive_manager.get_archive(file_path)
                if img_archive and hasattr(img_archive, 'entries') and img_archive.entries:
                    if not hasattr(img_archive, '_rw_analyzed'):
                        img_archive.analyze_all_entries_rw_versions()
                        img_archive._rw_analyzed = True
            
            # Emit signals for successfully opened archives
            for file_path in file_paths:
                if file_path not in failed_files:
                    img_archive = self.archive_manager.get_archive(file_path)
                    if img_archive:
                        self.img_loaded.emit(img_archive)
            
            # Prepare result message
            if success_count == len(file_paths):
                return True, f"Successfully opened {success_count} archive(s)"
            elif success_count > 0:
                failed_names = [Path(f).name for f in failed_files]
                return True, f"Opened {success_count}/{len(file_paths)} archives. Failed: {', '.join(failed_names)}"
            else:
                return False, f"Failed to open any archives: {'; '.join(error_messages)}"
                
        except Exception as e:
            return False, f"Error opening archives: {str(e)}"
    
    def close_archive(self, file_path):
        """Closes a specific IMG archive."""
        if not file_path:
            return False, "Invalid file path: None"
            
        if file_path in self.archive_manager.open_archives:
            img_archive = self.archive_manager.get_archive(file_path)
            
            # Close the archive
            File_Operations.close_archive(img_archive, self.archive_manager)
            
            # Emit signal
            self.img_closed.emit(file_path)
            
            return True, f"Closed {Path(file_path).name}"
        else:
            return False, f"Archive not found: {Path(file_path).name}"
    
    def close_all_archives(self):
        """Closes all open IMG archives."""
        closed_count = len(self.archive_manager.open_archives)
        self.archive_manager.close_all_archives()
        self.img_closed.emit("")  # Empty string indicates all closed
        return True, f"Closed {closed_count} archive(s)"
    
    def switch_active_archive(self, file_path):
        """Switches the active archive."""
        if self.archive_manager.set_active_archive(file_path):
            active_archive = self.archive_manager.get_active_archive()
            self.archive_switched.emit(active_archive)
            return True
        return False
    
    def get_active_archive(self):
        """Get the currently active archive."""
        return self.archive_manager.get_active_archive()
    
    def get_open_archives(self):
        """Get list of all open archive paths."""
        return self.archive_manager.get_archive_paths()
    
    def get_archive_count(self):
        """Get the number of open archives."""
        return self.archive_manager.get_archive_count()
    
    def _add_to_recent_files(self, file_path):
        """Add a file to recent files list."""
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        if len(self.recent_files) > self.max_recent_files:
            self.recent_files = self.recent_files[:self.max_recent_files]
    
    # Legacy methods for backward compatibility
    
    def open_img(self, file_path):
        """Legacy method - opens an IMG archive from the specified path."""
        return self.open_archive(file_path)
    
    def get_rw_version_summary(self):
        """Get RenderWare version summary for the current archive."""
        if not self.current_img:
            return None
        return self.current_img.get_rw_version_summary()
    
    def analyze_entry_rw_version(self, entry):
        """Analyze RenderWare version for a specific entry."""
        if not self.current_img:
            return
        self.current_img.analyze_entry_rw_version(entry)
    
    def get_entries_by_rw_version(self, version_value):
        """Get entries filtered by RenderWare version."""
        if not self.current_img:
            return []
        return self.current_img.get_entries_by_rw_version(version_value)
    
    def get_entries_by_format(self, format_type):
        """Get entries filtered by format type."""
        if not self.current_img:
            return []
        return self.current_img.get_entries_by_format(format_type)
    
    
    def create_new_img(self, file_path, version='V2'):
        """Creates a new empty IMG archive."""
        try:
            self.current_img = File_Operations.create_new_archive(file_path, version)
            self.img_loaded.emit(self.current_img)
            self.entries_updated.emit([])  # No entries in a new file
            return True, f"Created new IMG archive: {Path(file_path).name}"
        except Exception as e:
            return False, f"Error creating IMG file: {str(e)}"
    
    
    def close_img(self):
        """Closes the current IMG archive."""
        if not self.current_img:
            return False, "No IMG file is currently open"
        
        self.current_img = None
        self.selected_entries = []
        self.img_closed.emit()
        return True, "IMG file closed"
        
    # Entry Management
    
    def get_entries(self, filter_text=None, filter_type=None):
        """Gets entries from the current archive, optionally filtered."""
        if not self.current_img:
            return []
        
        if filter_text or filter_type:
            return self.current_img.filter_entries(filter_text, filter_type)
        
        return self.current_img.entries
    
    def set_selected_entries(self, entries):
        """Sets the currently selected entries."""
        self.selected_entries = entries
    
    
    def extract_selected(self, output_dir):
        """Extracts selected entries to the specified directory."""
        if not self.current_img:
            return False, "No IMG file is currently open"
        
        if not self.selected_entries:
            return False, "No entries selected"
        
        try:
            extracted_files = []
            for entry in self.selected_entries:
                output_path = Import_Export.export_entry(self.current_img, entry, output_dir=output_dir)
                extracted_files.append(output_path)
            
            return True, f"Extracted {len(extracted_files)} file(s) to {output_dir}"
        except Exception as e:
            return False, f"Error extracting files: {str(e)}"
    
    def delete_selected(self):
        """Deletes selected entries from the current IMG archive in memory only."""
        active_archive = self.get_active_archive()
        if not active_archive:
            return False, "No IMG file is currently open"
        
        if not self.selected_entries:
            return False, "No entries selected"
        
        try:
            # Store count before deletion
            selected_count = len(self.selected_entries)
            entries_to_delete = self.selected_entries.copy()
            
            # Use the batch delete method for better performance
            success_count, failed_entries = active_archive.delete_entries(entries_to_delete)
            
            # Clear the selection since entries are deleted
            self.selected_entries.clear()
            
            # Emit signal to update UI
            self.entries_updated.emit(active_archive.entries)
            
            if success_count == selected_count:
                return True, f"Successfully deleted {success_count} entries"
            elif success_count > 0:
                return True, f"Deleted {success_count} of {selected_count} entries. {len(failed_entries)} entries could not be deleted."
            else:
                return False, "No entries could be deleted"
                
        except Exception as e:
            return False, f"Error deleting entries: {str(e)}"
    
    
    def has_unsaved_changes(self):
        """Check if the current archive has unsaved changes."""
        if not self.current_img:
            return False
        return self.current_img.modified
    
    def get_modification_info(self):
        """Get information about modifications to the current archive."""
        if not self.current_img:
            return {"modified": False, "has_deletions": False}
        return self.current_img.get_deleted_entries_count()
    
    def validate_entries_exist(self, entry_names):
        """Validate that entries with given names exist in the current archive."""
        if not self.current_img:
            return False, "No IMG file is currently open"
        
        existing_names = self.current_img.get_entry_names()
        missing_names = [name for name in entry_names if name not in existing_names]
        
        if missing_names:
            return False, f"Entries not found: {', '.join(missing_names)}"
        
        return True, "All entries exist"
    
    # IMG Operations
    
    def rebuild_img(self, output_path=None):
        """Rebuilds the current IMG archive."""
        if not self.current_img:
            return False, "No IMG file is currently open"
        
        # This would be implemented later
        # Placeholder for now
        return False, "Rebuild feature not implemented yet"
    
    def merge_img(self, img_paths, output_path):
        """Merges multiple IMG archives into one."""
        # This would be implemented later
        # Placeholder for now
        return False, "Merge feature not implemented yet"
    
    def split_img(self, output_dir, max_size=None, by_type=False):
        """Splits the current IMG archive into multiple smaller archives."""
        if not self.current_img:
            return False, "No IMG file is currently open"
        
        # This would be implemented later
        # Placeholder for now
        return False, "Split feature not implemented yet"
    
    # Helper Methods
    
    def get_img_info(self):
        """Gets information about the current IMG archive."""
        if not self.current_img:
            return {
                "path": "Not loaded",
                "version": "-",
                "entry_count": 0,
                "total_size": "0 bytes",
                "modified": "No"
            }
        
        return {
            "path": self.current_img.file_path,
            "version": self.current_img.get_version_string(),
            "entry_count": self.current_img.get_file_count(),
            "total_size": f"{self.current_img.get_total_size():,} bytes",
            "modified": "Yes" if self.current_img.modified else "No"
        }
    
    def is_img_open(self):
        """Checks if an IMG file is currently open."""
        return self.current_img is not None
