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
        header_label = QLabel("🔧 Renderware Modding Tools")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(header_label)
        
        # File format editors
        self.create_file_editors(layout)
        
        # Map & world tools
        self.create_map_world_tools(layout)
        
        # Data editors
        self.create_data_editors(layout)
        
        # Utilities
        self.create_utilities(layout)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def create_file_editors(self, layout):
        """Create file format editors"""
        file_group = QGroupBox("📁 File Format Editors")
        file_layout = QVBoxLayout()
        
        # IMG Editor
        img_btn = QPushButton("📦 IMG Editor")
        img_btn.setToolTip("Edit and manage IMG archive files")
        img_btn.clicked.connect(lambda: self.toolRequested.emit("img_editor", {}))
        
        # TXD Editor
        txd_btn = QPushButton("�️ TXD Editor")
        txd_btn.setToolTip("Edit texture dictionary files")
        txd_btn.clicked.connect(lambda: self.toolRequested.emit("txd_editor", {}))
        
        # DFF Viewer
        dff_btn = QPushButton("📦 DFF Viewer")
        dff_btn.setToolTip("View and analyze 3D model files")
        dff_btn.clicked.connect(lambda: self.toolRequested.emit("dff_viewer", {}))
        
        # COL Editor
        col_btn = QPushButton("� COL Editor")
        col_btn.setToolTip("Edit collision data files")
        col_btn.clicked.connect(lambda: self.toolRequested.emit("col_editor", {}))
        
        # IFP Editor
        ifp_btn = QPushButton("🏃 IFP Editor")
        ifp_btn.setToolTip("Edit animation files")
        ifp_btn.clicked.connect(lambda: self.toolRequested.emit("ifp_editor", {}))
        
        file_layout.addWidget(img_btn)
        file_layout.addWidget(txd_btn)
        file_layout.addWidget(dff_btn)
        file_layout.addWidget(col_btn)
        file_layout.addWidget(ifp_btn)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
    
    def create_map_world_tools(self, layout):
        """Create map and world editing tools"""
        map_group = QGroupBox("�️ Map & World Tools")
        map_layout = QVBoxLayout()
        
        # IDE Editor
        ide_btn = QPushButton("� IDE Editor")
        ide_btn.setToolTip("Edit item definition files")
        ide_btn.clicked.connect(lambda: self.toolRequested.emit("ide_editor", {}))
        
        # IPL Editor
        ipl_btn = QPushButton("� IPL Editor")
        ipl_btn.setToolTip("Edit item placement files")
        ipl_btn.clicked.connect(lambda: self.toolRequested.emit("ipl_editor", {}))
        
        # Zones/Cull Editor
        zones_btn = QPushButton("🌍 Zones/Cull Editor")
        zones_btn.setToolTip("Edit zone and culling data")
        zones_btn.clicked.connect(lambda: self.toolRequested.emit("zones_editor", {}))
        
        # Traffic Path Utility
        traffic_btn = QPushButton("🛣️ Traffic Path Utility")
        traffic_btn.setToolTip("Edit path network for vehicles and pedestrians")
        traffic_btn.clicked.connect(lambda: self.toolRequested.emit("traffic_path_editor", {}))
        
        # Water dat Editor
        water_btn = QPushButton("🌊 Water dat Editor")
        water_btn.setToolTip("Edit water effects and properties")
        water_btn.clicked.connect(lambda: self.toolRequested.emit("water_editor", {}))
        
        # timecyc Editor
        timecyc_btn = QPushButton("🌤️ timecyc Editor")
        timecyc_btn.setToolTip("Edit weather system and time cycles")
        timecyc_btn.clicked.connect(lambda: self.toolRequested.emit("timecyc_editor", {}))
        
        map_layout.addWidget(ide_btn)
        map_layout.addWidget(ipl_btn)
        map_layout.addWidget(zones_btn)
        map_layout.addWidget(traffic_btn)
        map_layout.addWidget(water_btn)
        map_layout.addWidget(timecyc_btn)
        
        map_group.setLayout(map_layout)
        layout.addWidget(map_group)
    
    def create_data_editors(self, layout):
        """Create data and statistics editors"""
        data_group = QGroupBox("📊 Data Editors")
        data_layout = QVBoxLayout()
        
        # Weapons Editor
        weapons_btn = QPushButton("🔫 Weapons Editor")
        weapons_btn.setToolTip("Edit weapon statistics and properties")
        weapons_btn.clicked.connect(lambda: self.toolRequested.emit("weapons_editor", {}))
        
        # Vehicles Editor
        vehicles_btn = QPushButton("🚗 Vehicles Editor")
        vehicles_btn.setToolTip("Edit vehicle properties and data")
        vehicles_btn.clicked.connect(lambda: self.toolRequested.emit("vehicles_editor", {}))
        
        # Pedestrians Editor
        peds_btn = QPushButton("🚶 Pedestrians Editor")
        peds_btn.setToolTip("Edit pedestrian data and behavior")
        peds_btn.clicked.connect(lambda: self.toolRequested.emit("pedestrians_editor", {}))
        
        # Handling Editor
        handling_btn = QPushButton("🎛️ Handling Editor")
        handling_btn.setToolTip("Edit vehicle handling properties")
        handling_btn.clicked.connect(lambda: self.toolRequested.emit("handling_editor", {}))
        
        # GXT Editor
        gxt_btn = QPushButton("📝 GXT Editor")
        gxt_btn.setToolTip("Edit text and font files")
        gxt_btn.clicked.connect(lambda: self.toolRequested.emit("gxt_editor", {}))
        
        data_layout.addWidget(weapons_btn)
        data_layout.addWidget(vehicles_btn)
        data_layout.addWidget(peds_btn)
        data_layout.addWidget(handling_btn)
        data_layout.addWidget(gxt_btn)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
    
    def create_utilities(self, layout):
        """Create utility tools"""
        util_group = QGroupBox("� Utilities")
        util_layout = QVBoxLayout()
        
        # RW Analyze
        analyze_btn = QPushButton("🔍 RW Analyze")
        analyze_btn.setToolTip("Analyze and debug Renderware files")
        analyze_btn.clicked.connect(lambda: self.toolRequested.emit("rw_analyze", {}))
        
        # Batch Converter
        batch_btn = QPushButton("� Batch Converter")
        batch_btn.setToolTip("Convert multiple files at once")
        batch_btn.clicked.connect(lambda: self.toolRequested.emit("batch_converter", {}))
        
        # File Validator
        validate_btn = QPushButton("✅ File Validator")
        validate_btn.setToolTip("Validate file integrity and format")
        validate_btn.clicked.connect(lambda: self.toolRequested.emit("file_validator", {}))
        
        # Backup Manager
        backup_btn = QPushButton("� Backup Manager")
        backup_btn.setToolTip("Manage file backups and restore points")
        backup_btn.clicked.connect(lambda: self.toolRequested.emit("backup_manager", {}))
        
        util_layout.addWidget(analyze_btn)
        util_layout.addWidget(batch_btn)
        util_layout.addWidget(validate_btn)
        util_layout.addWidget(backup_btn)
        
        util_group.setLayout(util_layout)
        layout.addWidget(util_group)
