"""
UI interaction handlers for the IMG Editor.
These methods implement the direct UI interactions that connect the ImgEditorTool class to the controller.
"""

from PySide6.QtWidgets import QFileDialog, QDialog, QRadioButton, QDialogButtonBox, QVBoxLayout, QMessageBox

def _open_img_file(self):
    """Open an IMG file"""
    file_path, _ = QFileDialog.getOpenFileName(
        self, "Open IMG File", "", "IMG Files (*.img);;All Files (*.*)"
    )
    
    if not file_path:
        return
        
    success, message = self.img_editor.open_img(file_path)
    if not success:
        from application.common.message_box import message_box
        message_box.error(message, "Error Opening IMG", self)

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
            from application.common.message_box import message_box
            message_box.error(message, "Error Creating IMG", self)


def _close_img(self):
    """Close the current IMG file"""
    if not self.img_editor.is_img_open():
        from application.common.message_box import message_box
        message_box.info("No IMG file is currently open to close.", "No IMG Open", self)
        return
        
    success, message = self.img_editor.close_img()

def _add_files(self):
    """Add files to the current IMG archive"""
    if not self.img_editor.is_img_open():
        from application.common.message_box import message_box
        message_box.info("No IMG file is currently open.", "No IMG Open", self)
        return
        
    file_paths, _ = QFileDialog.getOpenFileNames(
        self, "Select Files to Add", "", "All Files (*.*)"
    )
    
    if not file_paths:
        return
        
    success, message = self.img_editor.add_files(file_paths)
    
    from application.common.message_box import message_box
    if not success:
        message_box.error(message, "Error Adding Files", self)
    else:
        message_box.info(message, "Files Added", self)

def _extract_selected(self):
    """Extract selected entries"""
    if not self.img_editor.is_img_open():
        from application.common.message_box import message_box
        message_box.info("No IMG file is currently open.", "No IMG Open", self)
        return
        
    if not self.img_editor.selected_entries:
        from application.common.message_box import message_box
        message_box.info("No entries selected to extract.", "No Selection", self)
        return
        
    output_dir = QFileDialog.getExistingDirectory(
        self, "Select Directory for Extracted Files"
    )
    
    if not output_dir:
        return
        
    success, message = self.img_editor.extract_selected(output_dir)
    
    from application.common.message_box import message_box
    if not success:
        message_box.error(message, "Error Extracting Files", self)
    else:
        message_box.info(message, "Files Extracted", self)

def _delete_selected(self):
    """Delete selected entries"""
    if not self.img_editor.is_img_open():
        from application.common.message_box import message_box
        message_box.info("No IMG file is currently open.", "No IMG Open", self)
        return
        
    if not self.img_editor.selected_entries:
        from application.common.message_box import message_box
        message_box.info("No entries selected to delete.", "No Selection", self)
        return
        
    # Confirm deletion
    reply = QMessageBox.question(
        self, "Confirm Delete",
        f"Are you sure you want to delete {len(self.img_editor.selected_entries)} selected entries?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
    )
    
    if reply == QMessageBox.StandardButton.Yes:
        success, message = self.img_editor.delete_selected()
        from application.common.message_box import message_box
        if not success:
            message_box.error(message, "Error Deleting Entries", self)
        else:
            message_box.info(message, "Entries Deleted", self)

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
