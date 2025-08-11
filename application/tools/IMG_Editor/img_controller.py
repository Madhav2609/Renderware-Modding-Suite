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
    
    @property
    def current_img(self):
        """Legacy property for backward compatibility."""
        return self.get_active_archive()
    
    @current_img.setter 
    def current_img(self, value):
        """Legacy setter for backward compatibility."""
        # This is mainly for compatibility with old code
        # New code should use the archive_manager methods
        pass
    
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
    
    # Import Methods
    def import_via_ide(self, ide_file_path, models_directory=None):
        """
        Import DFF models and TXD textures from an IDE file into the current archive.
        
        Args:
            ide_file_path: Path to the IDE file to parse
            models_directory: Directory containing the DFF and TXD files
            
        Returns:
            Tuple of (success, message, parsed_info)
        """
        active_archive = self.get_active_archive()
        if not active_archive:
            return False, "No IMG file is currently open", None
        
        if not ide_file_path or not os.path.exists(ide_file_path):
            return False, "Invalid IDE file path", None
        
        try:
            imported_entries, failed_files, parsed_info = Import_Export.import_via_ide(
                active_archive, ide_file_path, models_directory
            )
            
            # Update UI
            if imported_entries:
                self.entries_updated.emit(active_archive.entries)
                active_archive.modified = True
                
                success_count = len(imported_entries)
                failed_count = len(failed_files)
                
                # Create detailed message
                message_parts = [
                    f"IDE Import completed:",
                    f"• Successfully imported: {success_count} files",
                    f"• Models found: {len(parsed_info['found_models'])}",
                    f"• Textures found: {len(parsed_info['found_textures'])}",
                ]
                
                if parsed_info['missing_models']:
                    message_parts.append(f"• Missing models: {len(parsed_info['missing_models'])}")
                if parsed_info['missing_textures']:
                    message_parts.append(f"• Missing textures: {len(parsed_info['missing_textures'])}")
                if failed_count > 0:
                    message_parts.append(f"• Failed imports: {failed_count}")
                
                message = "\n".join(message_parts)
                
                self.operation_completed.emit(True, message)
                return True, message, parsed_info
            else:
                message = "No files were imported from the IDE file"
                if parsed_info:
                    if parsed_info['missing_models'] or parsed_info['missing_textures']:
                        message += f"\nMissing files: {len(parsed_info['missing_models'])} models, {len(parsed_info['missing_textures'])} textures"
                
                return False, message, parsed_info
                
        except Exception as e:
            error_msg = f"Error importing from IDE file: {str(e)}"
            self.operation_completed.emit(False, error_msg)
            return False, error_msg, None
    
    def import_multiple_files(self, file_paths, entry_names=None):
        """
        Import multiple files into the current archive (memory only operation).
        
        Args:
            file_paths: List of file paths to import
            entry_names: Optional list of custom names for the entries
            
        Returns:
            Tuple of (success, message)
        """
        active_archive = self.get_active_archive()
        if not active_archive:
            return False, "No IMG file is currently open"
        
        if not file_paths:
            return False, "No files provided for import"
        
        try:
            # Import files
            imported_entries, failed_files = Import_Export.import_multiple_files(
                active_archive, file_paths, entry_names
            )
            
            if imported_entries:
                # Emit signal to update UI
                self.entries_updated.emit(active_archive.entries)
            
            # Prepare result message
            success_count = len(imported_entries)
            failed_count = len(failed_files)
            total_count = len(file_paths)
            
            if success_count == total_count:
                return True, f"Successfully imported {success_count} file(s)"
            elif success_count > 0:
                return True, f"Imported {success_count} of {total_count} files. {failed_count} files failed."
            else:
                return False, f"Failed to import any files. {failed_count} files failed."
                
        except Exception as e:
            return False, f"Error importing files: {str(e)}"
    
    def import_folder(self, folder_path, recursive=False, filter_extensions=None):
        """
        Import all files from a folder into the current archive (memory only operation).
        
        Args:
            folder_path: Path to the folder to import
            recursive: Whether to include subdirectories
            filter_extensions: Optional list of file extensions to filter by
            
        Returns:
            Tuple of (success, message)
        """
        active_archive = self.get_active_archive()
        if not active_archive:
            return False, "No IMG file is currently open"
        
        try:
            # Import folder
            imported_entries, failed_files = Import_Export.import_folder(
                active_archive, folder_path, recursive, filter_extensions
            )
            
            if imported_entries:
                # Emit signal to update UI
                self.entries_updated.emit(active_archive.entries)
            
            # Prepare result message
            success_count = len(imported_entries)
            failed_count = len(failed_files)
            
            if success_count > 0:
                message = f"Successfully imported {success_count} file(s) from folder"
                if failed_count > 0:
                    message += f". {failed_count} files failed."
                return True, message
            else:
                return False, f"No files were imported. {failed_count} files failed or no matching files found."
                
        except Exception as e:
            return False, f"Error importing folder: {str(e)}"
    
    def get_import_preview(self, file_paths):
        """
        Get a preview of what would happen if files were imported.
        
        Args:
            file_paths: List of file paths to preview
            
        Returns:
            Tuple of (success, preview_data or error_message)
        """
        active_archive = self.get_active_archive()
        if not active_archive:
            return False, "No IMG file is currently open"
        
        try:
            preview = Import_Export.get_import_preview(active_archive, file_paths)
            return True, preview
        except Exception as e:
            return False, f"Error generating import preview: {str(e)}"
    
    # Deleted Entry Management
    
    def get_deleted_entries(self):
        """
        Get list of deleted entries.
        
        Returns:
            List of deleted IMGEntry objects
        """
        active_archive = self.get_active_archive()
        if not active_archive:
            return []
        return active_archive.deleted_entries
    
    def get_deleted_entry_names(self):
        """
        Get list of deleted entry names.
        
        Returns:
            List of deleted entry names
        """
        active_archive = self.get_active_archive()
        if not active_archive:
            return []
        return active_archive.get_deleted_entry_names()
    
    def restore_deleted_entry(self, entry_name):
        """
        Restore a deleted entry.
        
        Args:
            entry_name: Name of the entry to restore
            
        Returns:
            Tuple of (success, message)
        """
        active_archive = self.get_active_archive()
        if not active_archive:
            return False, "No IMG file is currently open"
        
        try:
            success = active_archive.restore_deleted_entry(entry_name)
            
            if success:
                # Emit signal to update UI
                self.entries_updated.emit(active_archive.entries)
                return True, f"Successfully restored {entry_name}"
            else:
                return False, f"Could not find deleted entry: {entry_name}"
                
        except Exception as e:
            return False, f"Error restoring entry: {str(e)}"
    
    def restore_all_deleted_entries(self):
        """
        Restore all deleted entries.
        
        Returns:
            Tuple of (success, message)
        """
        active_archive = self.get_active_archive()
        if not active_archive:
            return False, "No IMG file is currently open"
        
        try:
            count = active_archive.restore_all_deleted_entries()
            
            if count > 0:
                # Emit signal to update UI
                self.entries_updated.emit(active_archive.entries)
                return True, f"Successfully restored {count} deleted entries"
            else:
                return False, "No deleted entries to restore"
                
        except Exception as e:
            return False, f"Error restoring entries: {str(e)}"
    
    
    def has_unsaved_changes(self):
        """Check if the current archive has unsaved changes."""
        active_archive = self.get_active_archive()
        if not active_archive:
            return False
        return active_archive.modified
    
    def get_modification_info(self):
        """Get information about modifications to the current archive."""
        active_archive = self.get_active_archive()
        if not active_archive:
            return {"modified": False, "has_deletions": False, "has_new_entries": False}
        
        # Use the new modification summary method
        if hasattr(active_archive, 'get_modification_summary'):
            return active_archive.get_modification_summary()
        else:
            # Fallback for backwards compatibility
            return active_archive.get_deleted_entries_count()
    
    def get_detailed_modification_status(self):
        """
        Get detailed information about all modifications to the current archive.
        
        Returns:
            Detailed modification information dictionary
        """
        active_archive = self.get_active_archive()
        if not active_archive:
            return {
                "has_archive": False,
                "is_modified": False,
                "summary": "No archive open"
            }
        
        mod_summary = active_archive.get_modification_summary()
        
        # Add additional details
        status_messages = []
        if mod_summary['has_new_entries']:
            status_messages.append(f"{mod_summary['new_entries_count']} new entries")
        if mod_summary['has_deleted_entries']:
            status_messages.append(f"{mod_summary['deleted_entries_count']} deleted entries")
        
        if not status_messages:
            summary = "No changes"
        else:
            summary = ", ".join(status_messages)
        
        return {
            "has_archive": True,
            "is_modified": mod_summary['is_modified'],
            "needs_save": mod_summary['needs_save'],
            "summary": summary,
            "details": mod_summary
        }
    
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
    
    def get_img_info(self, file_path=None):
        """Gets information about the specified or current IMG archive."""
        archive = None
        if file_path:
            archive = self.archive_manager.get_archive(file_path)
        else:
            archive = self.get_active_archive()
            
        if not archive:
            return {
                "path": "Not loaded",
                "version": "-",
                "entry_count": 0,
                "total_size": "0 bytes",
                "modified": "No"
            }
        
        return {
            "path": archive.file_path or "Unknown",
            "version": getattr(archive, 'version', 'Unknown'),
            "entry_count": len(archive.entries) if hasattr(archive, 'entries') else 0,
            "total_size": f"{sum(entry.actual_size for entry in archive.entries) if hasattr(archive, 'entries') and archive.entries else 0:,} bytes",
            "modified": "Yes" if getattr(archive, 'modified', False) else "No"
        }
    
    def get_archive_info_by_path(self, file_path):
        """Get archive information for a specific file path."""
        return self.get_img_info(file_path)
    
    def get_rw_version_summary(self, file_path=None):
        """Get RenderWare version summary for the specified or current archive."""
        archive = None
        if file_path:
            archive = self.archive_manager.get_archive(file_path)
        else:
            archive = self.get_active_archive()
            
        if not archive:
            return None
            
        if hasattr(archive, 'get_rw_version_summary'):
            return archive.get_rw_version_summary()
        return None
    
    def is_img_open(self):
        """Checks if an IMG file is currently open."""
        return self.current_img is not None
    
    def get_archive_file_path(self, archive=None):
        """Get the file path of the specified or current archive."""
        if archive is None:
            archive = self.get_active_archive()
        return getattr(archive, 'file_path', None) if archive else None
    
    def get_archive_entries(self, file_path=None):
        """Get entries for the specified or current archive."""
        archive = None
        if file_path:
            archive = self.archive_manager.get_archive(file_path)
        else:
            archive = self.get_active_archive()
            
        if not archive:
            return []
            
        return getattr(archive, 'entries', [])
    
    def get_archive_by_path(self, file_path):
        """Get archive object by file path."""
        return self.archive_manager.get_archive(file_path)
    
    def has_archive_path(self, file_path):
        """Check if an archive with the given path exists."""
        return file_path in self.archive_manager.open_archives if file_path else False
