"""
IMG Controller - Main controller for the IMG Editor.
This module acts as a bridge between the UI components and the core backend classes,
implementing the controller in the MVC pattern.
"""

from pathlib import Path
import os

from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal

# Import core modules
from .core import (
    IMGEntry, 
    IMGArchive,
    File_Operations, 
    IMG_Operations,
    Import_Export,
    Entries_and_Selection
)

class IMGController(QObject):
    """
    Main controller class that connects the IMG Editor UI with backend functionality.
    Acts as a controller between the UI (View) and the data model (Model).
    """
    # Define signals for UI updates
    img_loaded = pyqtSignal(object)  # Signal emitted when an IMG file is loaded
    img_closed = pyqtSignal()  # Signal emitted when an IMG file is closed
    entries_updated = pyqtSignal(list)  # Signal emitted when entries are updated
    operation_progress = pyqtSignal(int, str)  # Signal for long operations: progress, message
    operation_completed = pyqtSignal(bool, str)  # Signal for operation completion: success, message
    
    def __init__(self):
        super().__init__()
        self.current_img = None  # Current IMG archive being edited
        self.selected_entries = []  # List of currently selected entries
        self.recent_files = []  # List of recently opened files
        self.max_recent_files = 10  # Maximum number of recent files to track
    
    # File Operations
    
    def open_img(self, file_path):
        """Opens an IMG archive from the specified path."""
        try:
            self.current_img = File_Operations.open_archive(file_path)
            
            # Add to recent files
            if file_path in self.recent_files:
                self.recent_files.remove(file_path)
            self.recent_files.insert(0, file_path)
            if len(self.recent_files) > self.max_recent_files:
                self.recent_files = self.recent_files[:self.max_recent_files]
            
            # Emit signal with the loaded archive
            self.img_loaded.emit(self.current_img)
            
            # Emit signal with entries for the UI
            self.entries_updated.emit(self.current_img.entries)
            
            return True, f"Successfully opened {Path(file_path).name}"
        except Exception as e:
            return False, f"Error opening IMG file: {str(e)}"
    
    def open_multiple(self, file_paths):
        """Opens multiple IMG archives (only the first one is active)."""
        if not file_paths:
            return False, "No files selected"
        
        # Open the first file
        success, message = self.open_img(file_paths[0])
        
        # TODO: Handle multiple files - implement this feature later
        
        return success, message
    
    def create_new_img(self, file_path, version='V2'):
        """Creates a new empty IMG archive."""
        try:
            self.current_img = File_Operations.create_new_archive(file_path, version)
            self.img_loaded.emit(self.current_img)
            self.entries_updated.emit([])  # No entries in a new file
            return True, f"Created new IMG archive: {Path(file_path).name}"
        except Exception as e:
            return False, f"Error creating IMG file: {str(e)}"
    
    def save_img(self):
        """Saves the current IMG archive."""
        if not self.current_img:
            return False, "No IMG file is currently open"
        
        try:
            File_Operations.save_archive(self.current_img)
            return True, f"Saved {Path(self.current_img.file_path).name}"
        except Exception as e:
            return False, f"Error saving IMG file: {str(e)}"
    
    def save_img_as(self, file_path):
        """Saves the current IMG archive to a new path."""
        if not self.current_img:
            return False, "No IMG file is currently open"
        
        try:
            File_Operations.save_archive(self.current_img, file_path)
            self.current_img.file_path = file_path
            return True, f"Saved as {Path(file_path).name}"
        except Exception as e:
            return False, f"Error saving IMG file: {str(e)}"
    
    def close_img(self):
        """Closes the current IMG archive."""
        if not self.current_img:
            return False, "No IMG file is currently open"
        
        self.current_img = None
        self.selected_entries = []
        self.img_closed.emit()
        return True, "IMG file closed"
    
    def reload_img(self):
        """Reloads the current IMG archive from disk."""
        if not self.current_img or not self.current_img.file_path:
            return False, "No IMG file is currently open"
        
        file_path = self.current_img.file_path
        return self.open_img(file_path)
    
    # Entry Management
    
    def get_entries(self, filter_text=None, filter_type=None):
        """Gets entries from the current archive, optionally filtered."""
        if not self.current_img:
            return []
        
        if filter_text or filter_type:
            return Entries_and_Selection.filter_entries(self.current_img, filter_text, filter_type)
        
        return self.current_img.entries
    
    def set_selected_entries(self, entries):
        """Sets the currently selected entries."""
        self.selected_entries = entries
    
    def add_files(self, file_paths):
        """Adds files to the current IMG archive."""
        if not self.current_img:
            return False, "No IMG file is currently open"
        
        try:
            added_entries = []
            for file_path in file_paths:
                entry = Import_Export.import_file(self.current_img, file_path)
                added_entries.append(entry)
            
            self.entries_updated.emit(self.current_img.entries)
            return True, f"Added {len(added_entries)} file(s) to the archive"
        except Exception as e:
            return False, f"Error adding files: {str(e)}"
    
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
        """Deletes selected entries from the current IMG archive."""
        if not self.current_img:
            return False, "No IMG file is currently open"
        
        if not self.selected_entries:
            return False, "No entries selected"
        
        try:
            for entry in self.selected_entries.copy():
                Entries_and_Selection.remove_entry(self.current_img, entry)
                self.selected_entries.remove(entry)
            
            self.entries_updated.emit(self.current_img.entries)
            return True, f"Deleted {len(self.selected_entries)} entries"
        except Exception as e:
            return False, f"Error deleting entries: {str(e)}"
    
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
