"""
File Explorer Widget for Renderware Modding Suite
Handles file browsing and recent files management
"""

import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGroupBox, 
                            QPushButton, QListWidget, QListWidgetItem, 
                            QFileDialog)
from PySide6.QtCore import Qt, Signal
from .responsive_utils import get_responsive_manager


class FileExplorer(QWidget):
    """Simple file browser for opening modding files"""
    
    fileSelected = Signal(str)  # Signal when file is selected
    
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
        
        # Quick open buttons
        quick_open_group = QGroupBox("⚡ Quick Open")
        quick_layout = QVBoxLayout()
        quick_layout.setSpacing(spacing['small'])
        
        self.create_quick_open_buttons(quick_layout)
        quick_open_group.setLayout(quick_layout)
        
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
        
        layout.addWidget(quick_open_group)
        layout.addWidget(recent_group)
        layout.addWidget(browse_btn)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def create_quick_open_buttons(self, layout):
        """Create quick open buttons for each file type"""
        file_types = [
            ("📦 Open DFF Model", "DFF Models (*.dff)"),
            ("🖼️ Open TXD Texture", "TXD Textures (*.txd)"),
            ("💥 Open COL Collision", "COL Collision (*.col)"),
            ("🏃 Open IFP Animation", "IFP Animations (*.ifp)"),
            ("📋 Open IDE Definition", "IDE Definitions (*.ide)"),
            ("📍 Open IPL Placement", "IPL Placements (*.ipl)")
        ]
        
        for button_text, file_filter in file_types:
            btn = QPushButton(button_text)
            btn.clicked.connect(lambda checked, f=file_filter: self.open_file_dialog(f))
            layout.addWidget(btn)
    
    def open_file_dialog(self, file_filter):
        """Open file dialog for specific file type"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Open {file_filter.split('(')[0].strip()}",
            "",
            f"{file_filter};;All Files (*.*)"
        )
        if file_path:
            self.fileSelected.emit(file_path)
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
            self.fileSelected.emit(file_path)
            self.add_to_recent(file_path)
    
    def add_to_recent(self, file_path):
        """Add file to recent files list"""
        # Remove "No recent files" placeholder
        if self.recent_files_list.count() == 1:
            item = self.recent_files_list.item(0)
            if item and item.text() == "🔄 No recent files":
                self.recent_files_list.takeItem(0)
        
        # Add new file (limit to 10 recent files)
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
        
        # Limit to 10 items
        while self.recent_files_list.count() > 10:
            self.recent_files_list.takeItem(self.recent_files_list.count() - 1)
    
    def on_recent_file_selected(self, item):
        """Handle recent file selection"""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self.fileSelected.emit(file_path)
