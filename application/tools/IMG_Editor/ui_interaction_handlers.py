"""
UI interaction handlers for the IMG Editor.
These methods implement the direct UI interactions that connect the ImgEditorTool class to the controller.
"""

from PyQt6.QtWidgets import QFileDialog, QDialog, QRadioButton, QDialogButtonBox, QVBoxLayout, QMessageBox, QCheckBox, QComboBox, QLabel, QHBoxLayout, QPushButton
from application.common.message_box import message_box
from application.tools.IMG_Editor.archive_tab import IMGArchiveTab

def _open_img_file(self):
    """Open a single IMG file"""
    file_dialog = QFileDialog()
    file_path, _ = file_dialog.getOpenFileName(
        self, 
        "Open IMG Archive", 
        "", 
        "IMG Archives (*.img);;All Files (*.*)"
    )
    
    if file_path:
        # Start progress panel for opening archive
        self.progress_panel.start_operation(f"Opening {file_path.split('/')[-1]}")
        success, message = self.open_archive(file_path)
        # Progress updates and completion are handled by signals
    else:
        return



def _open_multiple_img_files(self):
        """Open multiple IMG files"""
        file_dialog = QFileDialog()
        file_paths, _ = file_dialog.getOpenFileNames(
            self, 
            "Open Multiple IMG Archives", 
            "", 
            "IMG Archives (*.img);;All Files (*.*)"
        )
        
        if file_paths:
            # Start progress panel for opening multiple archives
            self.progress_panel.start_operation(f"Opening {len(file_paths)} archives")
            success, message = self.open_multiple_archives(file_paths)
            # Progress updates and completion are handled by signals




def _create_new_img(self):
    """Create a new IMG file"""
    file_path, _ = QFileDialog.getSaveFileName(
        self, "Create New IMG File", "", "IMG Files (*.img);;All Files (*.*)"
    )
    
    if not file_path:
        return
        
    # Ask for version
    dialog = QDialog(self)
    dialog.setWindowTitle("Select IMG Version")
    
    layout = QVBoxLayout()
    v1_radio = QRadioButton("Version 1 (GTA III & Vice City - separate .dir file)")
    v2_radio = QRadioButton("Version 2 (GTA San Andreas - single file)")
    v2_radio.setChecked(True)  # Default to V2
    
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    
    layout.addWidget(v1_radio)
    layout.addWidget(v2_radio)
    layout.addWidget(buttons)
    dialog.setLayout(layout)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        version = 'V1' if v1_radio.isChecked() else 'V2'
        success, message = self.img_editor.create_new_img(file_path, version)
        
        if not success:
            message_box.error(message, "Error Creating IMG", self)


def _close_current_img(self):
    """Close current IMG archive"""
    current_index = self.archive_tabs.currentIndex()
    if current_index >= 0 and isinstance(self.archive_tabs.widget(current_index), IMGArchiveTab):
        self._close_archive_tab(current_index)
    else:
        message_box.warning("No archive is currently open.", "No Archive", self)

def _close_all_imgs(self):
    """Close all IMG archives"""
    while self.archive_tabs.count() > 0:
        widget = self.archive_tabs.widget(0)
        if isinstance(widget, IMGArchiveTab):
            self._close_archive_tab(0)
        else:
            break
    self.show_empty_state()


def _extract_selected(self):
    """Extract selected entries"""
    if not self.img_editor.is_img_open():
        message_box.info("No IMG file is currently open.", "No IMG Open", self)
        return
        
    if not self.img_editor.selected_entries:
        message_box.info("No entries selected to extract.", "No Selection", self)
        return
        
    output_dir = QFileDialog.getExistingDirectory(
        self, "Select Directory for Extracted Files"
    )
    
    if not output_dir:
        return
    
    # Start progress panel for extraction
    self.progress_panel.start_operation(f"Extracting {len(self.img_editor.selected_entries)} files")
        
    success, message = self.img_editor.extract_selected(output_dir)
    # Progress updates and completion are handled by signals

def _delete_selected(self):
    """Delete selected entries from the current archive (in memory only)"""
    if not self.img_editor.is_img_open():
        message_box.info("No IMG file is currently open.", "No IMG Open", self)
        return
        
    if not self.img_editor.selected_entries:
        message_box.info("No entries selected to delete.", "No Selection", self)
        return
    
    # Get entry count and names for confirmation
    selected_count = len(self.img_editor.selected_entries)
    entry_names = [entry.name for entry in self.img_editor.selected_entries[:5]]  # Show first 5 names
    
    # Create confirmation message
    if selected_count <= 5:
        files_text = ", ".join(entry_names)
    else:
        files_text = ", ".join(entry_names) + f" and {selected_count - 5} more"
    
    # Confirm deletion
    reply = QMessageBox.question(
        self, "Confirm Delete",
        f"Are you sure you want to delete {selected_count} selected entries?\n\n"
        f"Files: {files_text}\n\n"
        "Note: This will only remove entries from memory. "
        "The actual IMG file will not be modified until you save or rebuild the archive.",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
    )
    
    if reply == QMessageBox.StandardButton.Yes:
        # Start progress panel for deletion
        self.progress_panel.start_operation(f"Deleting {selected_count} entries")
        
        success, message = self.img_editor.delete_selected()
        # Progress updates and completion are handled by signals
            
def _import_Via_IDE(self):
    """Import DFF models and TXD textures from an IDE file"""
    if not self.img_editor.is_img_open():
        message_box.warning("Please open an IMG file first.", "No IMG File Open", self)
        return
    
    from PyQt6.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QGroupBox, QGridLayout
    
    # Select IDE file
    ide_file, _ = QFileDialog.getOpenFileName(
        self,
        "Select IDE File",
        "",
        "IDE Files (*.ide);;All Files (*.*)"
    )
    
    if not ide_file:
        return
    
    # Select models directory
    models_dir = QFileDialog.getExistingDirectory(
        self,
        "Select Models Directory (containing DFF and TXD files)",
        ""
    )
    
    if not models_dir:
        return
    
    # Show progress/preview dialog
    dialog = QDialog(self)
    dialog.setWindowTitle("IDE Import Preview")
    dialog.setMinimumSize(600, 500)
    
    layout = QVBoxLayout(dialog)
    
    # Info label
    info_label = QLabel(f"IDE File: {ide_file}\nModels Directory: {models_dir}")
    layout.addWidget(info_label)
    
    # Get preview info from controller instead of parsing in UI
    try:
        success, preview_info = self.img_controller.get_ide_import_preview(ide_file, models_dir)
        if not success:
            message_box.error(preview_info, "IDE Analysis Error", self)
            return

        # Create preview content
        preview_text = QTextEdit()
        preview_text.setReadOnly(True)

        parsed_info = preview_info
        preview_content = f"""IDE File Analysis:

Sections Found:
• objs entries: {parsed_info['objs_count']}
• tobj entries: {parsed_info['tobj_count']}

Files to Import:
• Models (DFF): {len(parsed_info['found_models'])} found, {len(parsed_info['missing_models'])} missing
• Textures (TXD): {len(parsed_info['found_textures'])} found, {len(parsed_info['missing_textures'])} missing

Found Models ({len(parsed_info['found_models'])}):
{chr(10).join(f"  ✓ {model}.dff" for model in parsed_info['found_models'][:20])}
{f"  ... and {len(parsed_info['found_models']) - 20} more" if len(parsed_info['found_models']) > 20 else ""}

Found Textures ({len(parsed_info['found_textures'])}):
{chr(10).join(f"  ✓ {texture}.txd" for texture in parsed_info['found_textures'][:20])}
{f"  ... and {len(parsed_info['found_textures']) - 20} more" if len(parsed_info['found_textures']) > 20 else ""}

Missing Models ({len(parsed_info['missing_models'])}):
{chr(10).join(f"  ✗ {model}.dff" for model in parsed_info['missing_models'][:10])}
{f"  ... and {len(parsed_info['missing_models']) - 10} more" if len(parsed_info['missing_models']) > 10 else ""}

Missing Textures ({len(parsed_info['missing_textures'])}):
{chr(10).join(f"  ✗ {texture}.txd" for texture in parsed_info['missing_textures'][:10])}
{f"  ... and {len(parsed_info['missing_textures']) - 10} more" if len(parsed_info['missing_textures']) > 10 else ""}
"""

        preview_text.setPlainText(preview_content)
        layout.addWidget(preview_text)

        # Buttons
        button_layout = QHBoxLayout()

        import_btn = QPushButton("Import Found Files")
        import_btn.setEnabled(len(parsed_info['found_models']) > 0 or len(parsed_info['found_textures']) > 0)

        cancel_btn = QPushButton("Cancel")

        button_layout.addWidget(import_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        # Connect buttons
        import_btn.clicked.connect(lambda: self._proceed_with_ide_import(dialog, ide_file, models_dir))
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()

    except Exception as e:
        message_box.error(f"Error analyzing IDE file: {str(e)}", "IDE Analysis Error", self)

def _proceed_with_ide_import(self, dialog, ide_file, models_dir):
    """Proceed with the IDE import after user confirmation"""
    dialog.accept()
    
    # Start progress panel for IDE import
    self.progress_panel.start_operation(f"Importing via IDE: {ide_file.split('/')[-1]}")
    
    try:
        success, message, parsed_info = self.img_controller.import_via_ide(ide_file, models_dir)
        # Progress updates and completion are handled by signals
            
    except Exception as e:
        message_box.error(f"Error during IDE import: {str(e)}", "IDE Import Error", self)

def _import_multiple_files(self):
    """Import multiple files into the current archive"""
    if not self.img_editor.is_img_open():
        message_box.info("No IMG file is currently open.", "No IMG Open", self)
        return
    
    file_paths, _ = QFileDialog.getOpenFileNames(
        self, "Import Multiple Files", "", "All Files (*.*)"
    )
    
    if not file_paths:
        return
    
    # Start progress panel for import
    self.progress_panel.start_operation(f"Importing {len(file_paths)} files")
    
    success, message = self.img_editor.import_multiple_files(file_paths)
    # Progress updates and completion are handled by signals

def _import_folder(self):
    """Import folder contents into the current archive"""
    if not self.img_editor.is_img_open():
        message_box.info("No IMG file is currently open.", "No IMG Open", self)
        return
    
    folder_path = QFileDialog.getExistingDirectory(
        self, "Import Folder"
    )
    
    if not folder_path:
        return
    
    # Show folder import options dialog
    dialog = QDialog(self)
    dialog.setWindowTitle("Folder Import Options")
    dialog.setMinimumWidth(400)
    
    layout = QVBoxLayout()
    
    # Recursive option
    recursive_check = QCheckBox("Include subdirectories (recursive)")
    recursive_check.setChecked(False)
    layout.addWidget(recursive_check)
    
    # File filter option
    filter_layout = QHBoxLayout()
    filter_label = QLabel("File Extensions Filter:")
    filter_combo = QComboBox()
    filter_combo.setEditable(True)
    filter_combo.addItems([
        "All files", 
        "dff,txd", 
        "dff,txd,col", 
        "dff", 
        "txd", 
        "col", 
        "ifp", 
        "ipl,dat",
        "wav,mp3"
    ])
    filter_layout.addWidget(filter_label)
    filter_layout.addWidget(filter_combo)
    layout.addLayout(filter_layout)
    
    # Buttons
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    
    dialog.setLayout(layout)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        recursive = recursive_check.isChecked()
        
        # Parse filter extensions
        filter_text = filter_combo.currentText().strip()
        if filter_text and filter_text != "All files":
            filter_extensions = [ext.strip() for ext in filter_text.split(',')]
        else:
            filter_extensions = None
        
        # Start progress panel for folder import
        self.progress_panel.start_operation(f"Importing folder: {folder_path.split('/')[-1]}")
        
        success, message = self.img_editor.import_folder(folder_path, recursive, filter_extensions)
        # Progress updates and completion are handled by signals

def _get_import_preview(self):
    """Show import preview for selected files"""
    if not self.img_editor.is_img_open():
        message_box.info("No IMG file is currently open.", "No IMG Open", self)
        return
    
    file_paths, _ = QFileDialog.getOpenFileNames(
        self, "Preview Import", "", "All Files (*.*)"
    )
    
    if not file_paths:
        return
    
    success, preview_data = self.img_editor.get_import_preview(file_paths)
    
    if not success:
        message_box.error(preview_data, "Error Generating Preview", self)
        return
    
    # Create preview dialog
    dialog = QDialog(self)
    dialog.setWindowTitle("Import Preview")
    dialog.setMinimumSize(500, 400)
    
    layout = QVBoxLayout()
    
    # Summary
    summary_text = f"Total files: {preview_data['total_files']}\n"
    summary_text += f"Valid files: {len(preview_data['valid_files'])}\n"
    summary_text += f"Invalid files: {len(preview_data['invalid_files'])}\n"
    summary_text += f"Would add: {len(preview_data['would_add'])}\n"
    summary_text += f"Would replace: {len(preview_data['would_replace'])}\n"
    summary_text += f"Total size: {preview_data['total_size_bytes']:,} bytes ({preview_data['total_size_sectors']} sectors)"
    
    summary_label = QLabel(summary_text)
    layout.addWidget(summary_label)
    
    # Show invalid files if any
    if preview_data['invalid_files']:
        invalid_text = "Invalid files:\n"
        for invalid in preview_data['invalid_files'][:10]:  # Show first 10
            invalid_text += f"• {invalid['file_path']}: {invalid['error']}\n"
        if len(preview_data['invalid_files']) > 10:
            invalid_text += f"... and {len(preview_data['invalid_files']) - 10} more"
        
        invalid_label = QLabel(invalid_text)
        invalid_label.setStyleSheet("color: orange;")
        layout.addWidget(invalid_label)
    
    # Show files that would be replaced
    if preview_data['would_replace']:
        replace_text = "Files that would be replaced:\n"
        for replace in preview_data['would_replace'][:10]:  # Show first 10
            replace_text += f"• {replace['entry_name']}\n"
        if len(preview_data['would_replace']) > 10:
            replace_text += f"... and {len(preview_data['would_replace']) - 10} more"
        
        replace_label = QLabel(replace_text)
        replace_label.setStyleSheet("color: yellow;")
        layout.addWidget(replace_label)
    
    # Buttons
    button_layout = QHBoxLayout()
    
    proceed_btn = QPushButton("Proceed with Import")
    proceed_btn.clicked.connect(lambda: self._proceed_with_import(dialog, file_paths))
    
    cancel_btn = QPushButton("Cancel")
    cancel_btn.clicked.connect(dialog.reject)
    
    button_layout.addWidget(proceed_btn)
    button_layout.addWidget(cancel_btn)
    layout.addLayout(button_layout)
    
    dialog.setLayout(layout)
    dialog.exec()

def _proceed_with_import(self, dialog, file_paths):
    """Proceed with import after preview"""
    dialog.accept()
    success, message = self.img_editor.import_multiple_files(file_paths)
    
    if not success:
        message_box.error(message, "Error Importing Files", self)
    else:
        message_box.info(message, "Files Imported", self)

# Export UI Interaction Handlers

def _export_selected(self):
    """Export selected entries to a directory"""
    if not self.img_editor.is_img_open():
        message_box.warning("No IMG file is currently open.", "No IMG Open", self)
        return
    
    selected_entries = self.get_selected_entries()
    if not selected_entries:
        message_box.warning("No entries are selected for export.", "No Selection", self)
        return
    
    # Get export directory
    export_dir = QFileDialog.getExistingDirectory(
        self, 
        "Select Export Directory", 
        "",
        QFileDialog.Option.ShowDirsOnly
    )
    
    if export_dir:
        # Start progress panel for export
        self.progress_panel.start_operation(f"Exporting {len(selected_entries)} entries")
        success, message = self.img_editor.export_selected(export_dir)
        # Progress updates and completion are handled by signals

def _export_all(self):
    """Export all entries to a directory"""
    if not self.img_editor.is_img_open():
        message_box.warning("No IMG file is currently open.", "No IMG Open", self)
        return
    
    # Get export directory
    export_dir = QFileDialog.getExistingDirectory(
        self, 
        "Select Export Directory", 
        "",
        QFileDialog.Option.ShowDirsOnly
    )
    
    if export_dir:
        # Start progress panel for export
        self.progress_panel.start_operation("Exporting all entries")
        success, message = self.img_editor.export_all(export_dir)
        # Progress updates and completion are handled by signals

def _export_by_type(self):
    """Export entries by type to a directory"""
    if not self.img_editor.is_img_open():
        message_box.warning("No IMG file is currently open.", "No IMG Open", self)
        return
    
    # Get available types from current archive
    archive = self.img_editor.get_active_archive()
    if not archive:
        message_box.warning("No active archive available.", "No Archive", self)
        return
    
    # Get unique types from entries
    types = list(set(entry.type for entry in archive.entries))
    types.sort()
    
    if not types:
        message_box.warning("No entries found in archive.", "No Entries", self)
        return
    
    # Create type selection dialog
    dialog = QDialog(self)
    dialog.setWindowTitle("Select Types to Export")
    dialog.setMinimumSize(300, 200)
    
    layout = QVBoxLayout()
    
    # Instructions
    instruction_label = QLabel("Select the file types you want to export:")
    layout.addWidget(instruction_label)
    
    # Type checkboxes
    type_checkboxes = {}
    for file_type in types:
        checkbox = QCheckBox(f"{file_type} ({len([e for e in archive.entries if e.type == file_type])} files)")
        checkbox.setChecked(True)  # Default to all selected
        type_checkboxes[file_type] = checkbox
        layout.addWidget(checkbox)
    
    # Buttons
    button_layout = QHBoxLayout()
    
    select_all_btn = QPushButton("Select All")
    select_all_btn.clicked.connect(lambda: [cb.setChecked(True) for cb in type_checkboxes.values()])
    
    deselect_all_btn = QPushButton("Deselect All")
    deselect_all_btn.clicked.connect(lambda: [cb.setChecked(False) for cb in type_checkboxes.values()])
    
    export_btn = QPushButton("Export")
    export_btn.clicked.connect(dialog.accept)
    
    cancel_btn = QPushButton("Cancel")
    cancel_btn.clicked.connect(dialog.reject)
    
    button_layout.addWidget(select_all_btn)
    button_layout.addWidget(deselect_all_btn)
    button_layout.addStretch()
    button_layout.addWidget(export_btn)
    button_layout.addWidget(cancel_btn)
    
    layout.addLayout(button_layout)
    dialog.setLayout(layout)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        # Get selected types
        selected_types = [t for t, cb in type_checkboxes.items() if cb.isChecked()]
        
        if not selected_types:
            message_box.warning("No types selected for export.", "No Types Selected", self)
            return
        
        # Get export directory
        export_dir = QFileDialog.getExistingDirectory(
            self, 
            "Select Export Directory", 
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if export_dir:
            # Start progress panel for export
            self.progress_panel.start_operation(f"Exporting {', '.join(selected_types)} files")
            success, message = self.img_editor.export_by_type(export_dir, selected_types)
            # Progress updates and completion are handled by signals

def _get_export_preview(self):
    """Get a preview of what would be exported"""
    if not self.img_editor.is_img_open():
        message_box.warning("No IMG file is currently open.", "No IMG Open", self)
        return
    
    # Get preview data
    preview = self.img_editor.get_export_preview()
    if not preview:
        message_box.warning("Could not generate export preview.", "Preview Error", self)
        return
    
    # Create preview dialog
    dialog = QDialog(self)
    dialog.setWindowTitle("Export Preview")
    dialog.setMinimumSize(500, 400)
    
    layout = QVBoxLayout()
    
    # Summary
    summary_text = f"Total Entries: {preview['total_entries']}\n"
    summary_text += f"Total Size: {preview['total_size_bytes'] / (1024*1024):.2f} MB\n\n"
    
    summary_label = QLabel(summary_text)
    layout.addWidget(summary_label)
    
    # Type breakdown
    type_text = "Breakdown by Type:\n"
    for file_type, entries in preview['by_type'].items():
        type_size = sum(e['size'] for e in entries)
        type_text += f"• {file_type}: {len(entries)} files ({type_size / (1024*1024):.2f} MB)\n"
    
    type_label = QLabel(type_text)
    layout.addWidget(type_label)
    
    # Close button
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dialog.accept)
    layout.addWidget(close_btn)
    
    dialog.setLayout(layout)
    dialog.exec()

def _show_modification_status(self):
    """Show detailed modification status"""
    if not self.img_editor.is_img_open():
        message_box.info("No IMG file is currently open.", "No IMG Open", self)
        return
    
    status = self.img_editor.get_detailed_modification_status()
    
    if not status['has_archive']:
        message_box.info("No archive information available.", "No Archive", self)
        return
    
    details = status['details']
    
    # Create status dialog
    dialog = QDialog(self)
    dialog.setWindowTitle("Archive Modification Status")
    dialog.setMinimumSize(400, 300)
    
    layout = QVBoxLayout()
    
    # Main status
    main_status = f"Archive: {status['summary']}\n"
    main_status += f"Modified: {'Yes' if status['is_modified'] else 'No'}\n"
    main_status += f"Needs Save: {'Yes' if status['needs_save'] else 'No'}\n\n"
    
    # Detailed breakdown
    main_status += f"Total Entries: {details['total_entries']}\n"
    
    if details['has_new_entries']:
        main_status += f"New Entries: {details['new_entries_count']}\n"
    
    if details['has_deleted_entries']:
        main_status += f"Deleted Entries: {details['deleted_entries_count']}\n"
        main_status += f"Original Entry Count: {details['original_entries_count']}\n"
    
    # Show deleted entry names if any
    if details['deleted_entry_names']:
        main_status += f"\nDeleted entries:\n"
        for name in details['deleted_entry_names'][:10]:  # Show first 10
            main_status += f"• {name}\n"
        if len(details['deleted_entry_names']) > 10:
            main_status += f"... and {len(details['deleted_entry_names']) - 10} more"
    
    status_label = QLabel(main_status)
    layout.addWidget(status_label)
    
    # Restore buttons if there are deleted entries
    if details['has_deleted_entries']:
        button_layout = QHBoxLayout()
        
        restore_all_btn = QPushButton("Restore All Deleted")
        restore_all_btn.clicked.connect(lambda: self._restore_all_deleted(dialog))
        
        button_layout.addWidget(restore_all_btn)
        layout.addLayout(button_layout)
    
    # Close button
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dialog.accept)
    layout.addWidget(close_btn)
    
    dialog.setLayout(layout)
    dialog.exec()

def _restore_all_deleted(self, parent_dialog):
    """Restore all deleted entries"""
    success, message = self.img_editor.restore_all_deleted_entries()
    
    if success:
        message_box.info(message, "Entries Restored", parent_dialog)
        parent_dialog.accept()  # Close the status dialog to refresh
    else:
        message_box.error(message, "Error Restoring Entries", parent_dialog)

# Signal handlers for backend events

def _on_img_loaded(self, img_archive):
    """Handle IMG loaded event"""
    # Update file info panel
    info = self.img_editor.get_img_info()
    rw_summary = self.img_editor.get_rw_version_summary()
    self.file_info_panel.update_info(info, rw_summary)
    
    # Populate table with entries
    self.entries_table.populate_entries(img_archive.entries)

def _on_img_closed(self):
    """Handle IMG closed event"""
    # Reset file info panel
    self.file_info_panel.update_info(None)
    
    # Clear entries table
    self.entries_table.setRowCount(0)

def _on_entries_updated(self, entries):
    """Handle entries updated event"""
    # Update file info panel
    info = self.img_editor.get_img_info()
    rw_summary = self.img_editor.get_rw_version_summary()
    self.file_info_panel.update_info(info, rw_summary)
    
    # Refresh entries table
    self.entries_table.populate_entries(entries)
