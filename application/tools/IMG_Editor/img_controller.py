"""
IMG Controller - Main controller for the IMG Editor.
This module acts as a bridge between the UI components and the core backend classes,
implementing the controller in the MVC pattern.
"""

from pathlib import Path
import os

from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QMutex, QMutexLocker

# Import core modules
from .core import (
    IMGEntry, 
    IMGArchive,
    File_Operations, 
    IMG_Operations,
    Import_Export
)
from .core.File_Operations import ArchiveManager
from application.debug_system import get_debug_logger, LogCategory

# Module-level debug logger
debug_logger = get_debug_logger()


class IMGWorkerThread(QThread):
    """
    Worker thread for handling heavy IMG operations without blocking the UI.
    """
    # Progress signals
    progress_updated = pyqtSignal(int, str)  # progress_percentage, message
    operation_completed = pyqtSignal(bool, str, object)  # success, message, result_data

    def __init__(self, operation_type, operation_data, parent=None):
        super().__init__(parent)
        self.operation_type = operation_type
        self.operation_data = operation_data
        self.mutex = QMutex()
        self._cancelled = False
        # Track whether we've already emitted completion for a cancel to avoid duplicates
        self._cancelled_emitted = False
        
    def run(self):
        """Execute the operation based on type."""
        try:
            if self.operation_type == "open_archive":
                self._open_archive_operation()
            elif self.operation_type == "open_multiple_archives":
                self._open_multiple_archives_operation()
            elif self.operation_type == "import_multiple_files":
                self._import_multiple_files_operation()
            elif self.operation_type == "import_folder":
                self._import_folder_operation()
            elif self.operation_type == "import_via_ide":
                self._import_via_ide_operation()
            elif self.operation_type == "extract_selected":
                self._extract_selected_operation()
            elif self.operation_type == "delete_selected":
                self._delete_selected_operation()
            elif self.operation_type == "export_selected":
                self._export_selected_operation()
            elif self.operation_type == "export_all":
                self._export_all_operation()
            elif self.operation_type == "export_by_type":
                self._export_by_type_operation()
            elif self.operation_type == "rebuild_img":
                self._rebuild_img_operation()
            else:
                self.operation_completed.emit(False, f"Unknown operation type: {self.operation_type}", None)
                
        except Exception as e:
            self.operation_completed.emit(False, f"Operation failed: {str(e)}", None)
    
    def cancel(self):
        """Cancel the current operation."""
        with QMutexLocker(self.mutex):
            self._cancelled = True
    
    def _check_cancelled(self):
        """Check if operation was cancelled and emit completion once.

        Returns True if cancelled (and ensures a single completion signal is emitted),
        otherwise False.
        """
        with QMutexLocker(self.mutex):
            if self._cancelled:
                # Emit completion only once on cancellation to unblock UI
                if not self._cancelled_emitted:
                    try:
                        # Best-effort progress update to reflect cancellation
                        self.progress_updated.emit(100, "Operation cancelled")
                    except Exception:
                        pass
                    self.operation_completed.emit(False, "Operation cancelled", None)
                    self._cancelled_emitted = True
                return True
            return False
    
    def _open_archive_operation(self):
        """Open a single IMG archive."""
        file_path = self.operation_data['file_path']
        archive_manager = self.operation_data['archive_manager']
        
        self.progress_updated.emit(10, f"Opening archive: {Path(file_path).name}")
        
        try:
            img_archive = File_Operations.open_archive(file_path, archive_manager)
            
            if self._check_cancelled():
                return
            
            self.progress_updated.emit(50, "Analyzing RenderWare versions...")
            
            # Analyze RenderWare versions for all entries
            if img_archive and hasattr(img_archive, 'entries') and img_archive.entries:
                total_entries = len(img_archive.entries)
                for i, entry in enumerate(img_archive.entries):
                    if self._check_cancelled():
                        return
                    
                    img_archive.analyze_entry_rw_version(entry)
                    progress = 50 + int((i / total_entries) * 40)
                    self.progress_updated.emit(progress, f"Analyzing entry {i+1}/{total_entries}")
            
            self.progress_updated.emit(100, "Archive opened successfully")
            self.operation_completed.emit(True, f"Successfully opened {Path(file_path).name}", img_archive)
            
        except Exception as e:
            self.operation_completed.emit(False, f"Error opening IMG file: {str(e)}", None)
    
    def _open_multiple_archives_operation(self):
        """Open multiple IMG archives."""
        file_paths = self.operation_data['file_paths']
        archive_manager = self.operation_data['archive_manager']
        
        total_files = len(file_paths)
        success_count = 0
        failed_files = []
        error_messages = []
        
        for i, file_path in enumerate(file_paths):
            if self._check_cancelled():
                return
            
            progress = int((i / total_files) * 80)
            self.progress_updated.emit(progress, f"Opening archive {i+1}/{total_files}: {Path(file_path).name}")
            
            try:
                img_archive = File_Operations.open_archive(file_path, archive_manager)
                
                if self._check_cancelled():
                    return
                
                # Analyze RenderWare versions
                if img_archive and hasattr(img_archive, 'entries') and img_archive.entries:
                    img_archive.analyze_all_entries_rw_versions()
                
                success_count += 1
                
            except Exception as e:
                failed_files.append(file_path)
                error_messages.append(str(e))
        
        if self._check_cancelled():
            return
        
        self.progress_updated.emit(100, "All archives processed")
        
        # Prepare result message
        if success_count == total_files:
            message = f"Successfully opened {success_count} archive(s)"
        elif success_count > 0:
            failed_names = [Path(f).name for f in failed_files]
            message = f"Opened {success_count}/{total_files} archives. Failed: {', '.join(failed_names)}"
        else:
            message = f"Failed to open any archives: {'; '.join(error_messages)}"
        
        result_data = {
            'success_count': success_count,
            'failed_files': failed_files,
            'error_messages': error_messages
        }
        
        self.operation_completed.emit(success_count > 0, message, result_data)
    
    def _import_multiple_files_operation(self):
        """Import multiple files into an archive."""
        archive = self.operation_data['archive']
        file_paths = self.operation_data['file_paths']
        entry_names = self.operation_data.get('entry_names')
        
        total_files = len(file_paths)
        imported_entries = []
        failed_files = []
        
        for i, file_path in enumerate(file_paths):
            if self._check_cancelled():
                return
            
            progress = int((i / total_files) * 90)
            self.progress_updated.emit(progress, f"Importing file {i+1}/{total_files}: {Path(file_path).name}")
            
            try:
                entry_name = entry_names[i] if entry_names and i < len(entry_names) else None
                entry = Import_Export.import_file(archive, file_path, entry_name)
                
                if entry:
                    imported_entries.append(entry)
                else:
                    failed_files.append(file_path)
                    
            except Exception as e:
                failed_files.append(file_path)
        
        if self._check_cancelled():
            return
        
        self.progress_updated.emit(100, "Import completed")
        
        result_data = {
            'imported_entries': imported_entries,
            'failed_files': failed_files
        }
        
        success_count = len(imported_entries)
        total_count = len(file_paths)
        
        if success_count == total_count:
            message = f"Successfully imported {success_count} file(s)"
        elif success_count > 0:
            message = f"Imported {success_count} of {total_count} files. {len(failed_files)} files failed."
        else:
            message = f"Failed to import any files. {len(failed_files)} files failed."
        
        self.operation_completed.emit(success_count > 0, message, result_data)
    
    def _import_folder_operation(self):
        """Import all files from a folder."""
        archive = self.operation_data['archive']
        folder_path = self.operation_data['folder_path']
        recursive = self.operation_data.get('recursive', False)
        filter_extensions = self.operation_data.get('filter_extensions')
        
        self.progress_updated.emit(10, f"Scanning folder: {Path(folder_path).name}")
        
        try:
            imported_entries, failed_files = Import_Export.import_folder(
                archive, folder_path, recursive, filter_extensions
            )
            
            if self._check_cancelled():
                return
            
            self.progress_updated.emit(100, "Folder import completed")
            
            result_data = {
                'imported_entries': imported_entries,
                'failed_files': failed_files
            }
            
            success_count = len(imported_entries)
            failed_count = len(failed_files)
            
            if success_count > 0:
                message = f"Successfully imported {success_count} file(s) from folder"
                if failed_count > 0:
                    message += f". {failed_count} files failed."
            else:
                message = f"No files were imported. {failed_count} files failed or no matching files found."
            
            self.operation_completed.emit(success_count > 0, message, result_data)
            
        except Exception as e:
            self.operation_completed.emit(False, f"Error importing folder: {str(e)}", None)
    
    def _import_via_ide_operation(self):
        """Import files via IDE file."""
        archive = self.operation_data['archive']
        ide_file_path = self.operation_data['ide_file_path']
        models_directory = self.operation_data.get('models_directory')
        
        self.progress_updated.emit(10, "Parsing IDE file...")
        
        try:
            imported_entries, failed_files, parsed_info = Import_Export.import_via_ide(
                archive, ide_file_path, models_directory
            )
            
            if self._check_cancelled():
                return
            
            self.progress_updated.emit(100, "IDE import completed")
            
            result_data = {
                'imported_entries': imported_entries,
                'failed_files': failed_files,
                'parsed_info': parsed_info
            }
            
            success_count = len(imported_entries)
            
            if success_count > 0:
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
                if len(failed_files) > 0:
                    message_parts.append(f"• Failed imports: {len(failed_files)}")
                
                message = "\n".join(message_parts)
            else:
                message = "No files were imported from the IDE file"
                if parsed_info:
                    if parsed_info['missing_models'] or parsed_info['missing_textures']:
                        message += f"\nMissing files: {len(parsed_info['missing_models'])} models, {len(parsed_info['missing_textures'])} textures"
            
            self.operation_completed.emit(success_count > 0, message, result_data)
            
        except Exception as e:
            self.operation_completed.emit(False, f"Error importing from IDE file: {str(e)}", None)
    
    def _extract_selected_operation(self):
        """Extract selected entries."""
        archive = self.operation_data['archive']
        selected_entries = self.operation_data['selected_entries']
        output_dir = self.operation_data['output_dir']
        
        total_entries = len(selected_entries)
        extracted_files = []
        
        for i, entry in enumerate(selected_entries):
            if self._check_cancelled():
                return
            
            progress = int((i / total_entries) * 90)
            self.progress_updated.emit(progress, f"Extracting {i+1}/{total_entries}: {entry.name}")
            
            try:
                output_path = Import_Export.export_entry(archive, entry, output_dir=output_dir)
                extracted_files.append(output_path)
            except Exception as e:
                # Continue with other files even if one fails
                pass
        
        if self._check_cancelled():
            return
        
        self.progress_updated.emit(100, "Extraction completed")
        
        result_data = {
            'extracted_files': extracted_files
        }
        
        message = f"Extracted {len(extracted_files)} file(s) to {output_dir}"
        self.operation_completed.emit(True, message, result_data)
    
    def _delete_selected_operation(self):
        """Delete selected entries."""
        archive = self.operation_data['archive']
        selected_entries = self.operation_data['selected_entries']
        
        total_entries = len(selected_entries)
        success_count = 0
        failed_entries = []
        
        for i, entry in enumerate(selected_entries):
            if self._check_cancelled():
                return
            
            progress = int((i / total_entries) * 90)
            self.progress_updated.emit(progress, f"Deleting {i+1}/{total_entries}: {entry.name}")
            
            try:
                # Use the batch delete method for better performance
                success, failed = archive.delete_entries([entry])
                if success > 0:
                    success_count += 1
                else:
                    failed_entries.append(entry)
            except Exception as e:
                failed_entries.append(entry)
        
        if self._check_cancelled():
            return
        
        self.progress_updated.emit(100, "Deletion completed")
        
        result_data = {
            'success_count': success_count,
            'failed_entries': failed_entries
        }
        
        if success_count == total_entries:
            message = f"Successfully deleted {success_count} entries"
        elif success_count > 0:
            message = f"Deleted {success_count} of {total_entries} entries. {len(failed_entries)} entries could not be deleted."
        else:
            message = "No entries could be deleted"
        
        self.operation_completed.emit(success_count > 0, message, result_data)
    
    def _export_selected_operation(self):
        """Export selected entries from the active archive."""
        output_dir = self.operation_data['output_dir']
        selected_entries = self.operation_data['selected_entries']
        img_archive = self.operation_data['img_archive']
        
        total_entries = len(selected_entries)
        if total_entries == 0:
            self.operation_completed.emit(False, "No entries selected for export", None)
            return
        
        self.progress_updated.emit(0, f"Starting export of {total_entries} entries")
        
        exported_files = []
        failed_entries = []
        
        for i, entry in enumerate(selected_entries):
            if self._check_cancelled():
                return
            
            progress = int((i / total_entries) * 90)
            self.progress_updated.emit(progress, f"Exporting {entry.name} ({i+1}/{total_entries})")
            
            try:
                exported_path = Import_Export.export_entry(img_archive, entry, output_dir=output_dir)
                exported_files.append(exported_path)
            except Exception as e:
                failed_entries.append(entry)
                debug_logger.error(LogCategory.TOOL, f"Failed to export {entry.name}: {str(e)}")
        
        if self._check_cancelled():
            return
        
        self.progress_updated.emit(100, "Export completed")
        
        result_data = {
            'exported_files': exported_files,
            'failed_entries': failed_entries
        }
        
        if failed_entries:
            message = f"Exported {len(exported_files)} files, failed to export {len(failed_entries)} entries"
        else:
            message = f"Successfully exported {len(exported_files)} files to {output_dir}"
        
        self.operation_completed.emit(len(failed_entries) == 0, message, result_data)
    
    def _export_all_operation(self):
        """Export all entries from the active archive."""
        output_dir = self.operation_data['output_dir']
        filter_type = self.operation_data.get('filter_type')
        img_archive = self.operation_data['img_archive']
        
        total_entries = len(img_archive.entries)
        if total_entries == 0:
            self.operation_completed.emit(False, "No entries to export", None)
            return
        
        self.progress_updated.emit(0, f"Starting export of all entries ({total_entries} total)")
        
        try:
            exported_files, failed_entries = Import_Export.export_all(img_archive, output_dir, filter_type)
            
            if self._check_cancelled():
                return
            
            self.progress_updated.emit(100, "Export completed")
            
            result_data = {
                'exported_files': exported_files,
                'failed_entries': failed_entries
            }
            
            if failed_entries:
                message = f"Exported {len(exported_files)} files, failed to export {len(failed_entries)} entries"
            else:
                message = f"Successfully exported {len(exported_files)} files to {output_dir}"
            
            self.operation_completed.emit(len(failed_entries) == 0, message, result_data)
            
        except Exception as e:
            self.operation_completed.emit(False, f"Export failed: {str(e)}", None)
    
    def _export_by_type_operation(self):
        """Export entries of specific types from the active archive."""
        output_dir = self.operation_data['output_dir']
        types = self.operation_data['types']
        img_archive = self.operation_data['img_archive']
        
        total_entries = len(img_archive.entries)
        if total_entries == 0:
            self.operation_completed.emit(False, "No entries to export", None)
            return
        
        self.progress_updated.emit(0, f"Starting export by type: {', '.join(types)}")
        
        try:
            results = Import_Export.export_by_type(img_archive, output_dir, types)
            
            if self._check_cancelled():
                return
            
            self.progress_updated.emit(100, "Export by type completed")
            
            total_exported = sum(len(files) for files, _ in results.values())
            total_failed = sum(len(failed) for _, failed in results.values())
            
            result_data = {
                'results': results,
                'total_exported': total_exported,
                'total_failed': total_failed
            }
            
            if total_failed > 0:
                message = f"Exported {total_exported} files by type, failed to export {total_failed} entries"
            else:
                message = f"Successfully exported {total_exported} files by type to {output_dir}"
            
            self.operation_completed.emit(total_failed == 0, message, result_data)
            
        except Exception as e:
            self.operation_completed.emit(False, f"Export by type failed: {str(e)}", None)
    
    def _rebuild_img_operation(self):
        """Rebuild the current IMG archive (write changes to disk)."""
        from .core.IMG_Operations import IMG_Operations
        archive = self.operation_data['archive']
        output_path = self.operation_data.get('output_path')
        target_version = self.operation_data.get('target_version')
        try:
            # Kick off with a small progress update
            self.progress_updated.emit(0, "Starting rebuild...")
            new_archive = IMG_Operations.rebuild_archive(
                archive,
                output_path=output_path,
                version=target_version,
                progress_callback=lambda pct, msg: self.progress_updated.emit(pct, msg)
            )
            self.progress_updated.emit(100, "Rebuild finished")
            result_data = {
                'new_archive': new_archive,
                'output_path': output_path
            }
            self.operation_completed.emit(True, f"Rebuilt archive successfully", result_data)
        except Exception as e:
            self.operation_completed.emit(False, f"Rebuild failed: {str(e)}", None)


class IMGController(QObject):
    """
    Main controller class that connects the IMG Editor UI with backend functionality.
    Acts as a controller between the UI (View) and the data model (Model).
    Supports multiple IMG archives with tab-based management.
    """
    # Define signals for UI updates
    img_loaded = pyqtSignal(object)  # Signal emitted when an IMG file is loaded
    img_closed = pyqtSignal(str)  # Signal emitted when an IMG file is closed (file_path)
    entries_updated = pyqtSignal(list)  # Signal emitted when entries are updated
    operation_progress = pyqtSignal(int, str)  # Signal for long operations: progress, message
    operation_completed = pyqtSignal(bool, str)  # Signal for operation completion: success, message
    archive_switched = pyqtSignal(object)  # Signal when active archive changes
    archive_modified = pyqtSignal(str)  # Signal when archive is modified (file_path)
    
    def __init__(self):
        super().__init__()
        self.archive_manager = ArchiveManager()
        self.selected_entries = []  # List of currently selected entries
        self.recent_files = []  # List of recently opened files
        self.max_recent_files = 10  # Maximum number of recent files to track
        
        # Threading support
        self.worker_thread = None
        self.current_operation = None
    
    def _start_worker_operation(self, operation_type, operation_data):
        """Start a worker thread for heavy operations."""
        # Cancel any existing operation
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.cancel()
            self.worker_thread.wait()
        
        # Create and start new worker thread
        self.worker_thread = IMGWorkerThread(operation_type, operation_data, self)
        self.current_operation = operation_type
        
        # Connect signals
        self.worker_thread.progress_updated.connect(self.operation_progress.emit)
        self.worker_thread.operation_completed.connect(self._on_worker_completed)
        
        # Start the thread
        self.worker_thread.start()
    
    def _on_worker_completed(self, success, message, result_data):
        """Handle completion of worker thread operations."""
        operation_type = self.current_operation
        self.current_operation = None
        
        # Handle specific operation results
        if operation_type == "open_archive" and success:
            img_archive = result_data
            self.img_loaded.emit(img_archive)
        elif operation_type == "open_multiple_archives" and success:
            # Emit signals for successfully opened archives
            for file_path in self.archive_manager.get_archive_paths():
                img_archive = self.archive_manager.get_archive(file_path)
                if img_archive:
                    self.img_loaded.emit(img_archive)
        elif operation_type in ["import_multiple_files", "import_folder", "import_via_ide"] and success:
            # Update UI with new entries
            active_archive = self.get_active_archive()
            if active_archive:
                self.entries_updated.emit(active_archive.entries)
        elif operation_type == "rebuild_img":
            if success and result_data and result_data.get('new_archive'):
                new_archive = result_data['new_archive']
                # Replace the archive in the manager
                if new_archive.file_path:
                    self.archive_manager.open_archives[new_archive.file_path] = new_archive
                    self.archive_manager.active_archive = new_archive
                # Notify UI of new entries/state
                self.entries_updated.emit(new_archive.entries)
        elif operation_type == "delete_selected" and success:
            # Clear selection and update UI
            self.selected_entries.clear()
            active_archive = self.get_active_archive()
            if active_archive:
                self.entries_updated.emit(active_archive.entries)
        
        # Emit completion signal
        self.operation_completed.emit(success, message)
    
    def cancel_current_operation(self):
        """Cancel the currently running operation."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.cancel()
            self.worker_thread.wait(1000)  # Wait up to 1 second for cancellation
            if self.worker_thread.isRunning():
                self.worker_thread.terminate()
                self.worker_thread.wait(1000)
    
    def cleanup(self):
        """Clean up all resources when the controller is being destroyed"""
        try:
            # Cancel any running operations
            self.cancel_current_operation()
            
            # Close all archives
            if self.get_archive_count() > 0:
                self.close_all_archives()
            
            # Clear references
            self.worker_thread = None
            self.selected_entries = []
            
            # Disconnect all signals
            try:
                self.img_loaded.disconnect()
                self.img_closed.disconnect()
                self.archive_switched.disconnect()
                self.entries_updated.disconnect()
                self.operation_progress.disconnect()
                self.operation_completed.disconnect()
            except (TypeError, RuntimeError):
                # Signals might already be disconnected
                pass
            
            debug_logger.info(LogCategory.TOOL, "IMGController cleanup completed")
        except Exception as e:
            debug_logger.log_exception(LogCategory.IMG, "Error during entry deletion", e)
    def handle_entry_rename(self, entry, new_name):
        """Handle entry rename in IMG archive"""
        try:
            archive = self.get_active_archive()
            if not archive:
                return
                
            # Validate new name
            new_name = new_name.strip()
            if not new_name:
                from application.common.message_box import message_box
                message_box.warning("Entry name cannot be empty", "Invalid Name")
                return
            
            # Check for duplicate names
            existing_names = [e.name.lower() for e in archive.entries if e != entry]
            if new_name.lower() in existing_names:
                from application.common.message_box import message_box
                message_box.warning(f"An entry with the name '{new_name}' already exists", "Duplicate Name")
                return
            
            # Update the entry's name and mark as modified
            old_name = entry.name
            entry.name = new_name  # Actually update the name!
            entry.is_new_entry = True  # Mark as modified for rebuild
            archive.modified = True
            
            # Emit signals to update UI
            self.entries_updated.emit(archive.entries)
            self.archive_modified.emit(archive.file_path)
            
            debug_logger.info(LogCategory.TOOL, f"Entry renamed from '{old_name}' to '{new_name}'")
                
        except Exception as e:
            debug_logger.error(LogCategory.TOOL, f"Error during entry rename: {e}")

    def __del__(self):
        """Destructor to ensure cleanup when the controller is destroyed"""
        try:
            self.cleanup()
        
        except Exception as e:
            debug_logger.error(LogCategory.TOOL, f"Error in IMGController destructor: {e}")
    
    def is_operation_running(self):
        """Check if a heavy operation is currently running."""
        return self.worker_thread is not None and self.worker_thread.isRunning()
    
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
            
            # Start worker thread for opening archive
            operation_data = {
                'file_path': file_path,
                'archive_manager': self.archive_manager
            }
            self._start_worker_operation("open_archive", operation_data)
            
            # Add to recent files
            self._add_to_recent_files(file_path)
            
            return True, "Opening archive..."  # Return immediately, actual result comes via signal
            
        except Exception as e:
            return False, f"Error opening IMG file: {str(e)}"
    
    def open_multiple_archives(self, file_paths):
        """Opens multiple IMG archives."""
        if not file_paths:
            return False, "No files selected"
        
        try:
            # Start worker thread for opening multiple archives
            operation_data = {
                'file_paths': file_paths,
                'archive_manager': self.archive_manager
            }
            self._start_worker_operation("open_multiple_archives", operation_data)
            
            # Add successful files to recent files
            for file_path in file_paths:
                self._add_to_recent_files(file_path)
            
            return True, "Opening archives..."  # Return immediately, actual result comes via signal
                
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
        try:
            closed_count = len(self.archive_manager.open_archives)
            
            # Get all archive paths before closing
            archive_paths = list(self.archive_manager.open_archives.keys())
            
            # Close each archive individually to ensure proper cleanup
            for file_path in archive_paths:
                try:
                    img_archive = self.archive_manager.get_archive(file_path)
                    if img_archive:
                        # Close the archive using the core function
                        File_Operations.close_archive(img_archive, self.archive_manager)
                except Exception as e:
                    debug_logger.error(LogCategory.FILE_IO, f"Error closing archive {file_path}: {e}")
            
            # Clear the archive manager
            self.archive_manager.close_all_archives()
            
            # Clear any cached data
            self.selected_entries = []
            
            # Emit signal that all archives are closed
            self.img_closed.emit("")  # Empty string indicates all closed
            
            debug_logger.info(LogCategory.FILE_IO, f"Successfully closed {closed_count} archive(s)")
            return True, f"Closed {closed_count} archive(s)"
            
        except Exception as e:
            debug_logger.error(LogCategory.FILE_IO, f"Error in close_all_archives: {e}")
            return False, f"Error closing archives: {str(e)}"
    
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
        active_archive = self.get_active_archive()
        if not active_archive:
            return False, "No IMG file is currently open"
        
        if not self.selected_entries:
            return False, "No entries selected"
        
        try:
            # Start worker thread for extraction
            operation_data = {
                'archive': active_archive,
                'selected_entries': self.selected_entries,
                'output_dir': output_dir
            }
            self._start_worker_operation("extract_selected", operation_data)
            
            return True, "Extracting files..."  # Return immediately, actual result comes via signal
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
            # Start worker thread for deletion
            operation_data = {
                'archive': active_archive,
                'selected_entries': self.selected_entries.copy()
            }
            self._start_worker_operation("delete_selected", operation_data)
            
            return True, "Deleting entries..."  # Return immediately, actual result comes via signal
                
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
            # Start worker thread for IDE import
            operation_data = {
                'archive': active_archive,
                'ide_file_path': ide_file_path,
                'models_directory': models_directory
            }
            self._start_worker_operation("import_via_ide", operation_data)
            
            return True, "Importing via IDE file...", None  # Return immediately, actual result comes via signal
                
        except Exception as e:
            error_msg = f"Error importing from IDE file: {str(e)}"
            return False, error_msg, None

    def get_ide_import_preview(self, ide_file_path, models_directory=None):
        """
        Parse IDE file and check for existence of DFF and TXD files in the given directory.
        Returns (success, preview_info or error_message)
        """
        if not ide_file_path or not os.path.exists(ide_file_path):
            return False, "Invalid IDE file path"
        if not models_directory or not os.path.isdir(models_directory):
            return False, "Invalid models directory"
        try:
            from .core.Import_Export import Import_Export
            parsed_info = {
                'objs_count': 0,
                'tobj_count': 0,
                'unique_models': set(),
                'unique_textures': set(),
                'found_models': [],
                'found_textures': [],
                'missing_models': [],
                'missing_textures': []
            }
            models, textures = Import_Export._parse_ide_file(ide_file_path, parsed_info)
            for model_name in models:
                dff_path = Import_Export._find_file_in_directory(models_directory, f"{model_name}.dff")
                if dff_path:
                    parsed_info['found_models'].append(model_name)
                else:
                    parsed_info['missing_models'].append(model_name)
            for texture_name in textures:
                txd_path = Import_Export._find_file_in_directory(models_directory, f"{texture_name}.txd")
                if txd_path:
                    parsed_info['found_textures'].append(texture_name)
                else:
                    parsed_info['missing_textures'].append(texture_name)
            return True, parsed_info
        except Exception as e:
            return False, f"Error analyzing IDE file: {str(e)}"




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
            # Start worker thread for import
            operation_data = {
                'archive': active_archive,
                'file_paths': file_paths,
                'entry_names': entry_names
            }
            self._start_worker_operation("import_multiple_files", operation_data)
            
            return True, "Importing files..."  # Return immediately, actual result comes via signal
                
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
            # Start worker thread for folder import
            operation_data = {
                'archive': active_archive,
                'folder_path': folder_path,
                'recursive': recursive,
                'filter_extensions': filter_extensions
            }
            self._start_worker_operation("import_folder", operation_data)
            
            return True, "Importing folder..."  # Return immediately, actual result comes via signal
                
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
    
    # Export Methods
    
    def export_entry(self, entry, output_path=None, output_dir=None):
        """Export a single entry from the active archive."""
        active_archive = self.get_active_archive()
        if not active_archive:
            return False, "No active archive"
        
        try:
            exported_path = Import_Export.export_entry(active_archive, entry, output_path, output_dir)
            return True, f"Exported {entry.name} to {exported_path}"
        except Exception as e:
            return False, f"Failed to export {entry.name}: {str(e)}"
    
    def export_selected(self, output_dir):
        """Export all selected entries to the specified directory."""
        if not self.selected_entries:
            return False, "No entries selected"
        
        active_archive = self.get_active_archive()
        if not active_archive:
            return False, "No active archive"
        
        # Start worker thread for export operation
        operation_data = {
            'output_dir': output_dir,
            'selected_entries': self.selected_entries,
            'img_archive': active_archive
        }
        self._start_worker_operation("export_selected", operation_data)
        return True, "Export operation started"
    
    def export_all(self, output_dir, filter_type=None):
        """Export all entries from the active archive."""
        active_archive = self.get_active_archive()
        if not active_archive:
            return False, "No active archive"
        
        # Start worker thread for export operation
        operation_data = {
            'output_dir': output_dir,
            'filter_type': filter_type,
            'img_archive': active_archive
        }
        self._start_worker_operation("export_all", operation_data)
        return True, "Export operation started"
    
    def export_by_type(self, output_dir, types):
        """Export entries of specific types from the active archive."""
        active_archive = self.get_active_archive()
        if not active_archive:
            return False, "No active archive"
        
        # Start worker thread for export operation
        operation_data = {
            'output_dir': output_dir,
            'types': types,
            'img_archive': active_archive
        }
        self._start_worker_operation("export_by_type", operation_data)
        return True, "Export operation started"
    
    def get_export_preview(self, entries=None, filter_type=None):
        """Get a preview of what would be exported."""
        active_archive = self.get_active_archive()
        if not active_archive:
            return None
        
        if entries is None:
            entries = active_archive.entries
        
        preview = {
            'total_entries': len(entries),
            'entries': [],
            'total_size_bytes': 0,
            'by_type': {}
        }
        
        for entry in entries:
            # Apply type filter if provided
            if filter_type and entry.type != filter_type:
                continue
            
            entry_info = {
                'name': entry.name,
                'type': entry.type,
                'size': entry.actual_size,
                'offset': entry.actual_offset
            }
            preview['entries'].append(entry_info)
            preview['total_size_bytes'] += entry.actual_size
            
            # Group by type
            if entry.type not in preview['by_type']:
                preview['by_type'][entry.type] = []
            preview['by_type'][entry.type].append(entry_info)
        
        return preview
    
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
        try:
            operation_data = {
                'archive': self.current_img,
                'output_path': output_path,
                'target_version': None,
            }
            self._start_worker_operation("rebuild_img", operation_data)
            return True, "Rebuilding archive..."
        except Exception as e:
            return False, f"Error starting rebuild: {str(e)}"
    
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
