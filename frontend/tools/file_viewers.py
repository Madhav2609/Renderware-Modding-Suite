"""
File Viewers for Renderware Modding Suite
Modular file content viewers for different Renderware formats
"""

import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from PyQt6.QtCore import pyqtSignal


class BaseFileViewer(QWidget):
    """Base class for file viewers"""
    
    file_action = pyqtSignal(str, str)  # action_type, action_data
    
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setup_ui()
    
    def setup_ui(self):
        """Override in subclasses"""
        pass


class DffViewer(BaseFileViewer):
    """DFF Model file viewer"""
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # File info
        info_label = QLabel(f"📦 DFF Model: {os.path.basename(self.file_path)}")
        info_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        layout.addWidget(info_label)
        
        # Placeholder content
        content = QTextEdit()
        content.setPlainText(f"""DFF Model File: {self.file_path}
        
This is a placeholder for DFF model content.
In a complete implementation, this would show:
- 3D model preview/renderer
- Geometry information
- Material assignments
- Bone structure (if rigged)
- LOD levels
- Animation compatibility

File analysis will be performed by the C++ backend.""")
        content.setReadOnly(True)
        layout.addWidget(content)
        
        self.setLayout(layout)


class TxdViewer(BaseFileViewer):
    """TXD Texture Dictionary viewer"""
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        info_label = QLabel(f"🖼️ TXD Texture Dictionary: {os.path.basename(self.file_path)}")
        info_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        layout.addWidget(info_label)
        
        content = QTextEdit()
        content.setPlainText(f"""TXD Texture Dictionary: {self.file_path}
        
This is a placeholder for TXD texture content.
In a complete implementation, this would show:
- Texture thumbnail grid
- Texture properties (format, size, compression)
- Alpha channels
- Mipmaps
- Export/import tools

File analysis will be performed by the C++ backend.""")
        content.setReadOnly(True)
        layout.addWidget(content)
        
        self.setLayout(layout)


class ColViewer(BaseFileViewer):
    """COL Collision file viewer"""
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        info_label = QLabel(f"💥 COL Collision: {os.path.basename(self.file_path)}")
        info_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        layout.addWidget(info_label)
        
        content = QTextEdit()
        content.setPlainText(f"""COL Collision File: {self.file_path}
        
This is a placeholder for COL collision content.
In a complete implementation, this would show:
- Collision mesh visualization
- Surface properties
- Collision flags
- Bounding boxes
- Physics materials

File analysis will be performed by the C++ backend.""")
        content.setReadOnly(True)
        layout.addWidget(content)
        
        self.setLayout(layout)


class IfpViewer(BaseFileViewer):
    """IFP Animation file viewer"""
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        info_label = QLabel(f"🏃 IFP Animation: {os.path.basename(self.file_path)}")
        info_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        layout.addWidget(info_label)
        
        content = QTextEdit()
        content.setPlainText(f"""IFP Animation File: {self.file_path}
        
This is a placeholder for IFP animation content.
In a complete implementation, this would show:
- Animation timeline
- Keyframe editor
- Bone hierarchy
- Animation properties (duration, loop, etc.)
- Preview player

File analysis will be performed by the C++ backend.""")
        content.setReadOnly(True)
        layout.addWidget(content)
        
        self.setLayout(layout)


class IdeViewer(BaseFileViewer):
    """IDE Definition file viewer"""
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        info_label = QLabel(f"📋 IDE Definition: {os.path.basename(self.file_path)}")
        info_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        layout.addWidget(info_label)
        
        content = QTextEdit()
        content.setPlainText(f"""IDE Item Definition: {self.file_path}
        
This is a placeholder for IDE definition content.
In a complete implementation, this would show:
- Object definitions table
- Model references
- Texture references
- Object properties
- Search and filter tools

File analysis will be performed by the C++ backend.""")
        content.setReadOnly(True)
        layout.addWidget(content)
        
        self.setLayout(layout)


class IplViewer(BaseFileViewer):
    """IPL Placement file viewer"""
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        info_label = QLabel(f"📍 IPL Placement: {os.path.basename(self.file_path)}")
        info_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        layout.addWidget(info_label)
        
        content = QTextEdit()
        content.setPlainText(f"""IPL Item Placement: {self.file_path}
        
This is a placeholder for IPL placement content.
In a complete implementation, this would show:
- Object placement list
- 3D world position viewer
- Object instances
- Position/rotation/scale tools
- Map integration

File analysis will be performed by the C++ backend.""")
        content.setReadOnly(True)
        layout.addWidget(content)
        
        self.setLayout(layout)


class GenericViewer(BaseFileViewer):
    """Generic file viewer for unknown file types"""
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        info_label = QLabel(f"📄 File: {os.path.basename(self.file_path)}")
        info_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        layout.addWidget(info_label)
        
        content = QTextEdit()
        content.setPlainText(f"""File: {self.file_path}
        
This file type is not specifically supported by the modding suite.
You can still view the raw content or use general tools.

File size: {os.path.getsize(self.file_path)} bytes""")
        content.setReadOnly(True)
        layout.addWidget(content)
        
        self.setLayout(layout)


# File viewer registry
FILE_VIEWERS = {
    '.dff': DffViewer,
    '.txd': TxdViewer,
    '.col': ColViewer,
    '.ifp': IfpViewer,
    '.ide': IdeViewer,
    '.ipl': IplViewer,
}


def create_file_viewer(file_path):
    """Create appropriate file viewer for the given file"""
    file_ext = os.path.splitext(file_path)[1].lower()
    viewer_class = FILE_VIEWERS.get(file_ext, GenericViewer)
    return viewer_class(file_path)


def get_file_icon(file_path):
    """Get appropriate icon for file type"""
    file_ext = os.path.splitext(file_path)[1].lower()
    icons = {
        '.dff': '📦',
        '.txd': '🖼️',
        '.col': '💥',
        '.ifp': '🏃',
        '.ide': '📋',
        '.ipl': '📍',
    }
    return icons.get(file_ext, '📄')
