#this belongs in components/ img_formats.py - version 9
# X-Seti - July06 2025 - Img Factory 1.5  
# Credit MexUK 2007 Img Factory 1.2

#!/usr/bin/env python3
"""
Enhanced IMG Formats - Complete Format System
Game-specific handling for different IMG format variations
"""

import os
import struct
import json
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox, QCheckBox,
    QGroupBox, QFileDialog, QMessageBox, QTextEdit, QProgressBar,
    QButtonGroup, QRadioButton, QTabWidget, QWidget, QSlider,
    QTreeWidget, QTreeWidgetItem, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap

# Import from consolidated img_core_classes
from components.img_core_classes import IMGFile, IMGEntry, IMGVersion, CompressionType


class GameType(Enum):
    """Supported game types with specific configurations"""
    GTA3 = "gta3"
    GTAVC = "gtavc" 
    GTASA = "gtasa"
    BULLY = "bully"
    MANHUNT = "manhunt"
    MANHUNT2 = "manhunt2"


class PlatformType(Enum):
    """Platform-specific configurations for games"""
    PC = "pc"
    XBOX = "xbox"
    PS2 = "ps2"
    PSP = "psp"
    ANDROID = "android"
    IOS = "ios"


@dataclass
class GameConfiguration:
    """Game-specific IMG configuration"""
    name: str
    code: str
    img_version: IMGVersion
    platform: PlatformType
    default_size_mb: int
    max_size_mb: int
    max_entries: int
    supports_compression: bool
    supports_encryption: bool
    common_files: List[str]
    file_extensions: List[str]
    sector_size: int = 2048
    alignment_required: bool = True
    description: str = ""
    
    def get_format_specific_options(self) -> Dict[str, Any]:
        """Get format-specific options"""
        return {
            'sector_size': self.sector_size,
            'alignment_required': self.alignment_required,
            'max_entries': self.max_entries,
            'max_size_mb': self.max_size_mb
        }


class GameConfigurations:
    """Game configuration database"""
    
    CONFIGURATIONS = {
        GameType.GTA3: GameConfiguration(
            name="Grand Theft Auto III",
            code="gta3",
            img_version=IMGVersion.VERSION_1,
            platform=PlatformType.PC,
            default_size_mb=50,
            max_size_mb=500,
            max_entries=8000,
            supports_compression=False,
            supports_encryption=False,
            common_files=['gta3.img'],
            file_extensions=['.dff', '.txd', '.col', '.ifp'],
            description="Original RenderWare format with DIR+IMG files"
        ),
        
        GameType.GTAVC: GameConfiguration(
            name="Grand Theft Auto Vice City",
            code="gtavc",
            img_version=IMGVersion.VERSION_1,
            platform=PlatformType.PC,
            default_size_mb=75,
            max_size_mb=750,
            max_entries=10000,
            supports_compression=False,
            supports_encryption=False,
            common_files=['gta3.img', 'cuts.img'],
            file_extensions=['.dff', '.txd', '.col', '.ifp'],
            description="Enhanced V1 format with improved DIR handling"
        ),
        
        GameType.GTASA: GameConfiguration(
            name="Grand Theft Auto San Andreas",
            code="gtasa",
            img_version=IMGVersion.VERSION_2,
            platform=PlatformType.PC,
            default_size_mb=150,
            max_size_mb=2048,
            max_entries=16000,
            supports_compression=True,
            supports_encryption=False,
            common_files=['gta3.img', 'player.img', 'gta_int.img'],
            file_extensions=['.dff', '.txd', '.col', '.ifp', '.wav'],
            description="V2 format with integrated header and compression support"
        ),
        
        GameType.BULLY: GameConfiguration(
            name="Bully",
            code="bully",
            img_version=IMGVersion.VERSION_2,
            platform=PlatformType.PC,
            default_size_mb=100,
            max_size_mb=1024,
            max_entries=12000,
            supports_compression=True,
            supports_encryption=False,
            common_files=['world.img', 'chars.img'],
            file_extensions=['.dff', '.txd', '.col', '.ifp'],
            description="Modified V2 format for Bully game engine"
        ),
        
        GameType.MANHUNT: GameConfiguration(
            name="Manhunt",
            code="manhunt",
            img_version=IMGVersion.VERSION_1,
            platform=PlatformType.PC,
            default_size_mb=80,
            max_size_mb=800,
            max_entries=9000,
            supports_compression=False,
            supports_encryption=False,
            common_files=['manhunt.img'],
            file_extensions=['.dff', '.txd', '.col'],
            description="Manhunt-specific V1 format"
        ),
        
        GameType.MANHUNT2: GameConfiguration(
            name="Manhunt 2",
            code="manhunt2",
            img_version=IMGVersion.VERSION_2,
            platform=PlatformType.PC,
            default_size_mb=120,
            max_size_mb=1200,
            max_entries=14000,
            supports_compression=True,
            supports_encryption=False,
            common_files=['manhunt2.img'],
            file_extensions=['.dff', '.txd', '.col', '.wav'],
            description="Manhunt 2 enhanced V2 format"
        )
    }
    
    @classmethod
    def get_configuration(cls, game_type: GameType) -> Optional[GameConfiguration]:
        """Get configuration for specific game type"""
        return cls.CONFIGURATIONS.get(game_type)
    
    @classmethod
    def get_all_games(cls) -> List[GameType]:
        """Get list of all supported games"""
        return list(cls.CONFIGURATIONS.keys())


class IMGCreator:
    """IMG creation with advanced options - CONSOLIDATED VERSION"""
    
    @staticmethod
    def create_from_template(template_data: Dict[str, Any]) -> bool:
        """Create IMG from template data - FIXED SIGNATURE"""
        try:
            # Extract required data from template
            output_path = template_data.get('output_path')
            if not output_path:
                print("❌ No output path in template data")
                return False
            
            game_type_str = template_data.get('game_type', 'gtasa')
            
            # Convert string to GameType enum
            try:
                game_type = GameType(game_type_str)
            except ValueError:
                print(f"❌ Unknown game type: {game_type_str}")
                return False
            
            config = GameConfigurations.get_configuration(game_type)
            if not config:
                print(f"❌ No configuration for game type: {game_type}")
                return False
            
            # Extract settings
            settings = template_data.get('settings', {})
            
            img = IMGFile()
            creation_options = {
                'initial_size_mb': settings.get('initial_size_mb', config.default_size_mb),
                'compression_enabled': settings.get('compression_enabled', False),
                'encryption_enabled': settings.get('encryption_enabled', False)
            }
            
            if img.create_new(output_path, config.img_version, **creation_options):
                # Add template entries if specified
                entries = template_data.get('entries', [])
                for entry_info in entries:
                    # Create placeholder entries
                    entry_name = entry_info.get('name', '')
                    if entry_name:
                        img.add_entry(entry_name, b'')
                
                success = img.rebuild() if entries else True
                print(f"✅ Template applied: {template_data.get('name', 'Unknown')}")
                return success
            else:
                print("❌ Failed to create IMG file")
                return False
            
        except Exception as e:
            print(f"❌ Error creating from template: {e}")
            return False
    
    @staticmethod
    def create_game_specific(output_path: str, game_type: GameType, **options) -> bool:
        """Create game-specific IMG file"""
        try:
            config = GameConfigurations.get_configuration(game_type)
            if not config:
                return False
            
            img = IMGFile()
            
            creation_options = {
                'initial_size_mb': options.get('initial_size_mb', config.default_size_mb),
                'compression_enabled': options.get('compression_enabled', config.supports_compression),
                'encryption_enabled': options.get('encryption_enabled', config.supports_encryption),
                'sector_size': config.sector_size,
                'alignment_required': config.alignment_required
            }
            
            return img.create_new(output_path, config.img_version, **creation_options)
            
        except Exception as e:
            print(f"❌ Error creating game-specific IMG: {e}")
            return False
    
    @staticmethod
    def validate_game_compatibility(img_path: str, target_game: GameType) -> Dict[str, Any]:
        """Validate IMG compatibility with target game"""
        result = {
            'compatible': False,
            'issues': [],
            'recommendations': []
        }
        
        try:
            img = IMGFile(img_path)
            if img.open():
                config = GameConfigurations.get_configuration(target_game)
                if not config:
                    result['issues'].append("Unknown target game type")
                    return result
                
                # Check version compatibility
                if img.version != config.img_version:
                    result['issues'].append(f"Version mismatch: IMG is {img.version.name}, game expects {config.img_version.name}")
                
                # Check file count
                if len(img.entries) > config.max_entries:
                    result['issues'].append(f"Too many entries: {len(img.entries)} > {config.max_entries}")
                
                # Check file types
                unsupported_extensions = []
                for entry in img.entries:
                    if hasattr(entry, 'extension') and entry.extension:
                        if entry.extension.lower() not in [ext.lower() for ext in config.file_extensions]:
                            unsupported_extensions.append(entry.extension)
                
                if unsupported_extensions:
                    result['issues'].append(f"Unsupported file types: {', '.join(set(unsupported_extensions))}")
                
                result['compatible'] = len(result['issues']) == 0
                img.close()
        
        except Exception as e:
            result['issues'].append(f"Error analyzing file: {str(e)}")
        
        return result
    
    @staticmethod
    def get_creation_templates() -> List[Dict[str, Any]]:
        """Get available creation templates"""
        templates = []
        
        for game_type in GameConfigurations.get_all_games():
            config = GameConfigurations.get_configuration(game_type)
            if config:
                template = {
                    'name': f"{config.name} - Standard",
                    'game_type': game_type.value,
                    'description': config.description,
                    'settings': {
                        'initial_size_mb': config.default_size_mb,
                        'compression_enabled': config.supports_compression,
                        'encryption_enabled': False
                    }
                }
                templates.append(template)
        
        return templates


class GameSpecificIMGDialog(QDialog):
    """Dialog for creating game-specific IMG files"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Game-Specific IMG Archive")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        
        self.selected_config = None
        self.output_path = ""
        
        self._create_ui()
        self._connect_signals()
    
    def _create_ui(self):
        """Create the user interface"""
        layout = QVBoxLayout(self)
        
        # Game selection
        game_group = QGroupBox("Select Game & Platform")
        game_layout = QVBoxLayout(game_group)
        
        # Game type combo
        self.game_combo = QComboBox()
        for game_type in GameConfigurations.get_all_games():
            config = GameConfigurations.get_configuration(game_type)
            if config:
                self.game_combo.addItem(config.name, game_type)
        game_layout.addWidget(QLabel("Game:"))
        game_layout.addWidget(self.game_combo)
        
        # Platform combo
        self.platform_combo = QComboBox()
        for platform in PlatformType:
            self.platform_combo.addItem(platform.value.upper(), platform)
        game_layout.addWidget(QLabel("Platform:"))
        game_layout.addWidget(self.platform_combo)
        
        layout.addWidget(game_group)
        
        # Configuration display
        config_group = QGroupBox("Configuration Details")
        config_layout = QFormLayout(config_group)
        
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        config_layout.addRow("Description:", self.desc_label)
        
        self.version_label = QLabel()
        config_layout.addRow("IMG Version:", self.version_label)
        
        self.size_limits_label = QLabel()
        config_layout.addRow("Size Limits:", self.size_limits_label)
        
        self.features_label = QLabel()
        config_layout.addRow("Features:", self.features_label)
        
        layout.addWidget(config_group)
        
        # Creation options
        options_group = QGroupBox("Creation Options")
        options_layout = QFormLayout(options_group)
        
        # Size
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 4096)
        self.size_spin.setSuffix(" MB")
        options_layout.addRow("Initial Size:", self.size_spin)
        
        # Compression
        self.compression_check = QCheckBox("Enable compression")
        options_layout.addRow("Compression:", self.compression_check)
        
        # Encryption
        self.encryption_check = QCheckBox("Enable encryption")
        options_layout.addRow("Encryption:", self.encryption_check)
        
        layout.addWidget(options_group)
        
        # Output path
        path_group = QGroupBox("Output Path")
        path_layout = QHBoxLayout(path_group)
        
        self.path_edit = QLineEdit()
        path_layout.addWidget(self.path_edit)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_output_path)
        path_layout.addWidget(self.browse_btn)
        
        layout.addWidget(path_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.create_btn = QPushButton("Create IMG")
        self.create_btn.clicked.connect(self._create_img)
        button_layout.addWidget(self.create_btn)
        
        layout.addLayout(button_layout)
        
        # Initialize with first game
        self._update_configuration()
    
    def _connect_signals(self):
        """Connect UI signals"""
        self.game_combo.currentIndexChanged.connect(self._update_configuration)
        self.platform_combo.currentIndexChanged.connect(self._update_configuration)
    
    def _update_configuration(self):
        """Update configuration display"""
        game_type = self.game_combo.currentData()
        if not game_type:
            return
        
        config = GameConfigurations.get_configuration(game_type)
        if not config:
            return
        
        self.selected_config = config
        
        # Update display
        self.desc_label.setText(config.description)
        self.version_label.setText(config.img_version.name)
        self.size_limits_label.setText(f"{config.default_size_mb} MB (max: {config.max_size_mb} MB)")
        
        features = []
        if config.supports_compression:
            features.append("Compression")
        if config.supports_encryption:
            features.append("Encryption")
        self.features_label.setText(", ".join(features) if features else "None")
        
        # Update controls
        self.size_spin.setValue(config.default_size_mb)
        self.size_spin.setMaximum(config.max_size_mb)
        
        self.compression_check.setEnabled(config.supports_compression)
        self.compression_check.setChecked(config.supports_compression)
        
        self.encryption_check.setEnabled(config.supports_encryption)
        self.encryption_check.setChecked(False)
    
    def _browse_output_path(self):
        """Browse for output file path"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save IMG Archive",
            "",
            "IMG Archives (*.img);;All Files (*)"
        )
        
        if file_path:
            self.path_edit.setText(file_path)
            self.output_path = file_path
    
    def _create_img(self):
        """Create the new IMG file"""
        if not self.output_path:
            QMessageBox.warning(self, "Warning", "Please select an output path.")
            return
        
        if not self.selected_config:
            QMessageBox.warning(self, "Warning", "No configuration selected.")
            return
        
        try:
            creation_options = {
                'initial_size_mb': self.size_spin.value(),
                'compression_enabled': self.compression_check.isChecked(),
                'encryption_enabled': self.encryption_check.isChecked()
            }
            
            game_type = self.game_combo.currentData()
            if IMGCreator.create_game_specific(self.output_path, game_type, **creation_options):
                QMessageBox.information(
                    self,
                    "Success",
                    f"Game-specific IMG archive created!\n\n"
                    f"Game: {self.selected_config.name}\n"
                    f"File: {self.output_path}\n"
                    f"Version: {self.selected_config.img_version.name}"
                )
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to create IMG archive.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creating IMG archive:\n{str(e)}")


# Factory functions
def create_game_specific_dialog(parent=None):
    """Create game-specific IMG dialog"""
    return GameSpecificIMGDialog(parent)


def get_supported_games():
    """Get list of supported games"""
    return GameConfigurations.get_all_games()


def get_game_configuration(game_type: GameType):
    """Get configuration for specific game"""
    return GameConfigurations.get_configuration(game_type)