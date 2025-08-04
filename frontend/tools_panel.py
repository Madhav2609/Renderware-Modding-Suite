"""
Tools Panel Widget for Renderware Modding Suite
Contains various modding tools and operations
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGroupBox, 
                            QPushButton, QComboBox, QMenu)
from PyQt6.QtCore import pyqtSignal, QPoint


class ToolsPanel(QWidget):
    """Panel containing modding tools and operations"""
    
    toolRequested = pyqtSignal(str, dict)  # Signal when tool is requested (tool_name, params)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header_label = QLabel("🔧 Modding Tools")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(header_label)
        
        # General tools
        self.create_general_tools(layout)
        
        # Model tools
        self.create_model_tools(layout)
        
        # Texture tools
        self.create_texture_tools(layout)
        
        # Animation tools
        self.create_animation_tools(layout)
        
        # Map tools
        self.create_map_tools(layout)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def create_general_tools(self, layout):
        """Create general modding tools"""
        general_group = QGroupBox("⚙️ General Tools")
        general_layout = QVBoxLayout()
        
        # Batch converter
        batch_btn = QPushButton("📦 Batch Converter")
        batch_btn.clicked.connect(lambda: self.toolRequested.emit("batch_converter", {}))
        
        # File validator
        validate_btn = QPushButton("✅ Validate Files")
        validate_btn.clicked.connect(lambda: self.toolRequested.emit("file_validator", {}))
        
        # Backup manager
        backup_btn = QPushButton("💾 Backup Manager")
        backup_btn.clicked.connect(lambda: self.toolRequested.emit("backup_manager", {}))
        
        # IMG Editor
        img_editor_btn = QPushButton("📁 IMG Editor")
        img_editor_btn.clicked.connect(lambda: self.toolRequested.emit("img_editor", {}))
        
        general_layout.addWidget(batch_btn)
        general_layout.addWidget(validate_btn)
        general_layout.addWidget(backup_btn)
        general_layout.addWidget(img_editor_btn)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
    
    def create_model_tools(self, layout):
        """Create DFF model tools"""
        model_group = QGroupBox("📦 Model Tools (DFF)")
        model_layout = QVBoxLayout()
        
        # Model viewer
        viewer_btn = QPushButton("👁️ Model Viewer")
        viewer_btn.clicked.connect(lambda: self.toolRequested.emit("model_viewer", {}))
        
        # Collision editor
        collision_btn = QPushButton("💥 Collision Editor")
        collision_btn.clicked.connect(lambda: self.toolRequested.emit("collision_editor", {}))
        
        # LOD manager
        lod_btn = QPushButton("🔍 LOD Manager")
        lod_btn.clicked.connect(lambda: self.toolRequested.emit("lod_manager", {}))
        
        model_layout.addWidget(viewer_btn)
        model_layout.addWidget(collision_btn)
        model_layout.addWidget(lod_btn)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
    
    def create_texture_tools(self, layout):
        """Create TXD texture tools"""
        texture_group = QGroupBox("🖼️ Texture Tools (TXD)")
        texture_layout = QVBoxLayout()
        
        # Texture viewer
        viewer_btn = QPushButton("🖼️ Texture Viewer")
        viewer_btn.clicked.connect(lambda: self.toolRequested.emit("texture_viewer", {}))
        
        # Format converter
        format_combo = QComboBox()
        format_combo.addItems(["DXT1", "DXT3", "DXT5", "RGBA8888", "RGB565"])
        
        convert_btn = QPushButton("🔄 Convert Format")
        convert_btn.clicked.connect(lambda: self.toolRequested.emit(
            "texture_converter", 
            {"format": format_combo.currentText()}
        ))
        
        # Texture replacer
        replace_btn = QPushButton("🔀 Texture Replacer")
        replace_btn.clicked.connect(lambda: self.toolRequested.emit("texture_replacer", {}))
        
        texture_layout.addWidget(viewer_btn)
        texture_layout.addWidget(QLabel("Target Format:"))
        texture_layout.addWidget(format_combo)
        texture_layout.addWidget(convert_btn)
        texture_layout.addWidget(replace_btn)
        
        texture_group.setLayout(texture_layout)
        layout.addWidget(texture_group)
    
    def create_animation_tools(self, layout):
        """Create IFP animation tools"""
        anim_group = QGroupBox("🏃 Animation Tools (IFP)")
        anim_layout = QVBoxLayout()
        
        # Animation player
        player_btn = QPushButton("▶️ Animation Player")
        player_btn.clicked.connect(lambda: self.toolRequested.emit("animation_player", {}))
        
        # Timeline editor
        timeline_btn = QPushButton("⏱️ Timeline Editor")
        timeline_btn.clicked.connect(lambda: self.toolRequested.emit("timeline_editor", {}))
        
        # Bone mapper
        bone_btn = QPushButton("🦴 Bone Mapper")
        bone_btn.clicked.connect(lambda: self.toolRequested.emit("bone_mapper", {}))
        
        anim_layout.addWidget(player_btn)
        anim_layout.addWidget(timeline_btn)
        anim_layout.addWidget(bone_btn)
        
        anim_group.setLayout(anim_layout)
        layout.addWidget(anim_group)
    
    def create_map_tools(self, layout):
        """Create IDE/IPL map tools"""
        map_group = QGroupBox("📍 Map Tools (IDE/IPL)")
        map_layout = QVBoxLayout()
        
        # Object browser
        browser_btn = QPushButton("🗺️ Object Browser")
        browser_btn.clicked.connect(lambda: self.toolRequested.emit("object_browser", {}))
        
        # Placement editor
        placement_btn = QPushButton("📍 Placement Editor")
        placement_btn.clicked.connect(lambda: self.toolRequested.emit("placement_editor", {}))
        
        # Collision viewer
        collision_btn = QPushButton("💥 Collision Viewer")
        collision_btn.clicked.connect(lambda: self.toolRequested.emit("collision_viewer", {}))
        
        map_layout.addWidget(browser_btn)
        map_layout.addWidget(placement_btn)
        map_layout.addWidget(collision_btn)
        
        map_group.setLayout(map_layout)
        layout.addWidget(map_group)
