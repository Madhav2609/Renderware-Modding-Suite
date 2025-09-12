"""
Archive tab widget for the IMG Editor, re-exported from the legacy module.
This interim shim allows us to refactor imports before moving implementations.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal

from application.common.message_box import message_box
from application.styles import ModernDarkTheme
from application.responsive_utils import get_responsive_manager
from application.debug_system import get_debug_logger, LogCategory

from .ui_components import FilterPanel, IMGEntriesTable
from .context_menu import IMGTableContextMenu


debug_logger = get_debug_logger()


class IMGArchiveTab(QWidget):
    """Individual tab for an IMG archive"""

    # Signals
    archive_modified = pyqtSignal(str)  # Signal when archive is modified
    entries_selected = pyqtSignal(list)  # Signal when entries are selected
    action_requested = pyqtSignal(str, object)  # Signal for requesting actions from parent

    def __init__(self, img_archive, parent=None):
        super().__init__(parent)
        self.img_archive = img_archive
        self.parent_tool = parent  # Reference to parent ImgEditorTool
        self.setup_ui()
        self.update_display()

    def setup_ui(self):
        """Setup UI for individual archive tab"""
        layout = QVBoxLayout(self)
        # Filter panel
        self.filter_panel = FilterPanel()
        self.filter_panel.filter_changed.connect(self._on_filter_changed)
        layout.addWidget(self.filter_panel)

        # Entries table
        self.entries_table = IMGEntriesTable()
        self.entries_table.entry_double_clicked.connect(self._on_entry_double_clicked)
        self.entries_table.entry_selected.connect(self._on_entry_selected)
        self.entries_table.entry_renamed.connect(self._on_entry_renamed)

        # Setup drag and drop for the table
        if hasattr(self.parent_tool, 'drag_drop_handler'):
            self.entries_table.setup_drag_drop_support(
                self.parent_tool.drag_drop_handler,
                self.img_archive,
                self.parent_tool.img_controller
            )

            # Connect drag and drop signals
            self.entries_table.files_dropped.connect(self._on_files_dropped)
            self.entries_table.entries_dropped.connect(self._on_entries_dropped)

        # Initialize context menu handler with controller
        context_menu_handler = IMGTableContextMenu(self.entries_table, self.parent_tool.img_controller)
        self.entries_table.set_context_menu_handler(context_menu_handler)

        # Connect integration signals if available
        if hasattr(context_menu_handler, 'integration') and context_menu_handler.integration:
            context_menu_handler.integration.tool_open_requested.connect(self.parent_tool._on_tool_open_requested)
        layout.addWidget(self.entries_table)

    def update_display(self):
        """Update the display with current archive data"""
        if not self.img_archive or not self.parent_tool:
            return

        # Get entries through controller instead of direct access
        file_path = self.parent_tool.img_controller.get_archive_file_path(self.img_archive)
        entries = self.parent_tool.img_controller.get_archive_entries(file_path)

        # Update filter options based on the archive content
        self.filter_panel.update_filter_options(self.img_archive)

        # Populate table with entries
        if entries:
            self.entries_table.populate_entries(entries)

    def get_archive_info(self):
        """Get archive information for display"""
        if not self.img_archive or not self.parent_tool:
            return None

        # Get information through controller instead of direct access
        file_path = self.parent_tool.img_controller.get_archive_file_path(self.img_archive)
        return self.parent_tool.img_controller.get_archive_info_by_path(file_path)

    def get_selected_entries(self):
        """Get currently selected entries"""
        selected_entries = []

        # Get all selected rows
        for index in self.entries_table.selectedIndexes():
            if index.column() == 0:  # Only count each row once
                entry = self.entries_table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)
                if entry:
                    selected_entries.append(entry)

        return selected_entries

    def _on_filter_changed(self, filter_text, filter_type, filter_rw_version):
        """Handle filter changes"""
        self.entries_table.apply_filter(filter_text, filter_type, filter_rw_version)

    def _on_entry_double_clicked(self, entry):
        """Handle entry double-click"""
        # Implementation for entry preview/edit
        entry_info = f"Name: {entry.name}\n"
        entry_info += f"Size: {entry.actual_size:,} bytes\n"
        entry_info += f"Offset: Sector {entry.offset}"
        message_box.info(entry_info, "Entry Details", self)

    def _on_entry_selected(self, entries):
        """Handle entry selection"""
        self.entries_selected.emit(entries)

    def _on_entry_renamed(self, entry, new_name):
        """Handle entry rename request"""
        if self.parent_tool and self.parent_tool.img_controller:
            self.parent_tool.img_controller.handle_entry_rename(entry, new_name)
            # Update the display after rename
            self.update_display()

    def _on_files_dropped(self, file_paths):
        """Handle files dropped on this archive tab"""
        if not self.parent_tool or not self.parent_tool.img_controller:
            return

        try:
            debug_logger.info(LogCategory.UI, "Files dropped on archive tab",
                              {"file_count": len(file_paths), "archive": self.img_archive.file_path})

            # Use the IMG controller's import method with progress
            # Start progress panel for import
            if hasattr(self.parent_tool, 'progress_panel'):
                self.parent_tool.progress_panel.start_operation(f"Importing {len(file_paths)} files")

            success, message = self.parent_tool.img_controller.import_multiple_files(file_paths)

            if success:
                message_box.info("Files imported successfully!", "Import Complete", self)
                self.update_display()  # Refresh the display
                self.archive_modified.emit(self.img_archive.file_path)
            else:
                message_box.error(f"Import failed: {message}", "Import Error", self)

        except Exception as e:
            debug_logger.log_exception(LogCategory.UI, "Error handling file drop", e)
            message_box.error(f"Error importing files: {str(e)}", "Import Error", self)

    def _on_entries_dropped(self, entries, target_archive):
        """Handle entries dropped from another archive"""
        if not self.parent_tool or not self.parent_tool.img_controller:
            return

        if target_archive != self.img_archive:
            debug_logger.warning(LogCategory.UI, "Entry drop target mismatch")
            return

        try:
            debug_logger.info(LogCategory.UI, "Entries dropped between archives",
                              {"entry_count": len(entries), "target": target_archive.file_path})

            # Use a more efficient approach: export entries to temp directory then import
            import tempfile
            import shutil

            with tempfile.TemporaryDirectory() as temp_dir:
                # Export entries from source archive
                exported_files = []
                failed_exports = []

                for entry in entries:
                    try:
                        # Find source archive
                        source_archive = None
                        for archive in self.parent_tool.img_controller.archives:
                            if archive.get_entry_by_name(entry.name) == entry:
                                source_archive = archive
                                break

                        if source_archive:
                            from .core.Import_Export import Import_Export
                            exported_path = Import_Export.export_entry(source_archive, entry, output_dir=temp_dir)
                            exported_files.append(exported_path)
                        else:
                            failed_exports.append(entry.name)

                    except Exception as e:
                        debug_logger.log_exception(LogCategory.UI, f"Error exporting entry {entry.name}", e)
                        failed_exports.append(entry.name)

                # Import exported files to target archive
                if exported_files:
                    success, message = self.parent_tool.img_controller.import_multiple_files(exported_files)

                    if success:
                        message_box.info(f"Successfully transferred {len(exported_files)} entries.",
                                         "Transfer Complete", self)
                        self.update_display()
                        self.archive_modified.emit(target_archive.file_path)
                    else:
                        message_box.error(f"Failed to import transferred entries: {message}",
                                          "Transfer Error", self)

                if failed_exports:
                    message_box.warning(f"Failed to export {len(failed_exports)} entries: {', '.join(failed_exports[:5])}{'...' if len(failed_exports) > 5 else ''}",
                                        "Transfer Warning", self)

        except Exception as e:
            debug_logger.log_exception(LogCategory.UI, "Error handling entry drop", e)
            message_box.error(f"Error transferring entries: {str(e)}", "Transfer Error", self)

    def cleanup(self):
        """Clean up resources when the archive tab is closed"""
        try:
            # Clear references
            self.img_archive = None
            self.parent_tool = None

            # Clear table data
            if hasattr(self, 'entries_table'):
                self.entries_table.setRowCount(0)

            debug_logger.info(LogCategory.UI, "IMGArchiveTab cleanup completed")

        except Exception as e:
            debug_logger.log_exception(LogCategory.UI, "Error during IMGArchiveTab cleanup", e)

    def closeEvent(self, event):
        """Handle close event for the archive tab widget"""
        self.cleanup()
        super().closeEvent(event)

