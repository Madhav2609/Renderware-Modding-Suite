"""
File Explorer Widget for Renderware Modding Suite
Handles file browsing and recent files management
"""

import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGroupBox, 
                            QPushButton, QListWidget, QListWidgetItem, 
                            QFileDialog, QDialog, QDialogButtonBox, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from .responsive_utils import get_responsive_manager


class FileExplorer(QWidget):
    """Simple file browser for opening modding files"""

    fileSelected = pyqtSignal(str)  # Signal when file is selected
    openInTool = pyqtSignal(str, dict)  # Signal for opening a specific tool (tool_name, params)

    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the file explorer UI with responsive sizing"""
        rm = get_responsive_manager()
        fonts = rm.get_font_config()
        spacing = rm.get_spacing_config()
        
        layout = QVBoxLayout()
        layout.setSpacing(spacing['medium'])
        
        # Header with responsive font
        header_label = QLabel("📁 File Browser")
        header_label.setObjectName("titleLabel")
        header_label.setStyleSheet(f"font-weight: bold; font-size: {fonts['header']['size']}px; padding: {spacing['small']}px;")
        layout.addWidget(header_label)
        
        
        # Recent files list
        recent_group = QGroupBox("📄 Recent Files")
        recent_layout = QVBoxLayout()
        recent_layout.setSpacing(spacing['small'])
        
        self.recent_files_list = QListWidget()
        self.recent_files_list.addItem("🔄 No recent files")
        self.recent_files_list.itemClicked.connect(self.on_recent_file_selected)
        
        recent_layout.addWidget(self.recent_files_list)
        recent_group.setLayout(recent_layout)
        
        # Browse button with responsive sizing
        browse_btn = QPushButton("🗂️ Browse for Files...")
        browse_btn.clicked.connect(self.browse_files)
        
        layout.addWidget(recent_group)
        layout.addWidget(browse_btn)
        layout.addStretch()
        
        self.setLayout(layout)
    
    
    def open_file_dialog(self, file_filter):
        """Open file dialog for specific file type"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Open {file_filter.split('(')[0].strip()}",
            "",
            f"{file_filter};;All Files (*.*)"
        )
        if file_path:
            self.handle_file_selection(file_path)
            self.add_to_recent(file_path)
    
    def browse_files(self):
        """Open general file browser"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Renderware File",
            "",
            "All Renderware Files (*.dff *.txd *.col *.ifp *.ide *.ipl);;DFF Models (*.dff);;TXD Textures (*.txd);;COL Collision (*.col);;IFP Animations (*.ifp);;IDE Definitions (*.ide);;IPL Placements (*.ipl);;All Files (*.*)"
        )
        if file_path:
            self.handle_file_selection(file_path)
            self.add_to_recent(file_path)
    
    def add_to_recent(self, file_path):
        """Add file to recent files list"""
        # Remove "No recent files" placeholder
        if self.recent_files_list.count() == 1:
            item = self.recent_files_list.item(0)
            if item and item.text() == "🔄 No recent files":
                self.recent_files_list.takeItem(0)
        
    # Add new file (limit to scaled recent files)
        from application.responsive_utils import get_responsive_manager
        rm = get_responsive_manager()
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].upper()
        
        # Add icon based on file type
        icon_map = {
            '.DFF': '📦',
            '.TXD': '🖼️',
            '.COL': '💥',
            '.IFP': '🏃',
            '.IDE': '📋',
            '.IPL': '📍'
        }
        icon = icon_map.get(file_ext, '📄')
        
        item = QListWidgetItem(f"{icon} {file_name}")
        item.setData(Qt.ItemDataRole.UserRole, file_path)
        self.recent_files_list.insertItem(0, item)
        
        # Limit to scaled number of items
        max_items = max(5, rm.get_scaled_size(10))
        while self.recent_files_list.count() > max_items:
            self.recent_files_list.takeItem(self.recent_files_list.count() - 1)
    
    def on_recent_file_selected(self, item):
        """Handle recent file selection"""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self.handle_file_selection(file_path)
    
    def handle_file_selection(self, file_path):
        """Handle file selection with appropriate tool routing"""
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "File Not Found", f"The file '{file_path}' could not be found.")
            return
            
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.dff':
            self.handle_dff_file(file_path)
        elif file_ext == '.img':
            self.openInTool.emit('IMG_Editor', {'file_path': file_path, 'auto_load': True})
        elif file_ext == '.ide':
            self.openInTool.emit('ide_editor', {'file_path': file_path, 'auto_load': True})
        else:
            # For other file types, emit the original signal
            self.fileSelected.emit(file_path)
    
    def handle_dff_file(self, file_path):
        """Handle DFF file selection with choice dialog"""
        dialog = DFFActionDialog(self)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            action = dialog.get_selected_action()
            if action == 'view':
                self.openInTool.emit('dff_viewer', {'file_path': file_path, 'auto_load': True})
            elif action == 'analyze':
                self.openInTool.emit('rw_analyze', {'file_path': file_path, 'auto_load': True})


class DFFActionDialog(QDialog):
    """Dialog for choosing action when opening DFF files"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Open DFF File")
        self.setModal(True)
        self.selected_action = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("📦 How would you like to open this DFF file?")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        layout.addWidget(header_label)
        
        # Action buttons
        view_btn = QPushButton("🔍 View in DFF Viewer")
        view_btn.setToolTip("Open the DFF file in the 3D model viewer")
        view_btn.clicked.connect(lambda: self.select_action('view'))
        
        analyze_btn = QPushButton("📊 Analyze Structure")
        analyze_btn.setToolTip("Analyze the DFF file structure and properties")
        analyze_btn.clicked.connect(lambda: self.select_action('analyze'))
        
        # Style the buttons
        button_style = """
            QPushButton {
                padding: 12px;
                font-size: 12px;
                border: 1px solid #555;
                border-radius: 6px;
                background-color: #2b2b2b;
                color: white;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
                border-color: #777;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
        """
        
        view_btn.setStyleSheet(button_style)
        analyze_btn.setStyleSheet(button_style)
        
        layout.addWidget(view_btn)
        layout.addWidget(analyze_btn)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setFixedSize(350, 200)
    
    def select_action(self, action):
        """Select an action and close dialog"""
        self.selected_action = action
        self.accept()
    
    def get_selected_action(self):
        """Get the selected action"""
        return self.selected_action
