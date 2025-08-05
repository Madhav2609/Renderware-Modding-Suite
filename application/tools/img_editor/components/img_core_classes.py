#this belongs in components/img_core_classes.py - Version: 8
# X-Seti - July20 2025 - IMG Factory 1.5 - IMG Core Classes with Fixed RW Version Detection

"""
IMG Core Classes
"""

import os
import struct
import json
import shutil
from enum import Enum
from typing import List, Dict, Optional, Any, Union, BinaryIO
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox)
from PyQt6.QtCore import pyqtSignal, Qt

# Import message box
from application.common.message_box import message_box

# Import existing RW version functions - KEPT ALL ORIGINAL IMPORTS
from application.tools.img_editor.core.rw_versions import get_rw_version_name, parse_rw_version, get_model_format_version
# CIRCULAR IMPORT REMOVED: from core.img_platform_detection import detect_img_platform, get_platform_specific_specs, IMGPlatform

# REMOVED CIRCULAR IMPORT: Don't import GUI components from img_editor.py

##Methods list -
# create_entries_table_panel
# create_img_file
# detect_img_version
# format_file_size
# integrate_filtering
# populate_table_with_sample_data

##Classes -
# CompressionType
# FileType
# IMGEntry
# IMGFile
# IMGPlatform
# IMGVersion
# Platform
# RecentFilesManager
# ValidationResult

class IMGVersion(Enum):
    """IMG Archive Version Types"""
    VERSION_1 = 1    # DIR/IMG pair (GTA3, VC)
    VERSION_2 = 2    # Single IMG file (SA)
    UNKNOWN = 0

class IMGPlatform(Enum):
    """Platform types for IMG files - MOVED HERE TO ELIMINATE CIRCULAR IMPORT"""
    PC = "pc"
    PS2 = "ps2" 
    XBOX = "xbox"
    PSP = "psp"
    ANDROID = "android"
    IOS = "ios"
    UNKNOWN = "unknown"

class FileType(Enum):
    """File types found in IMG archives"""
    DFF = "dff"         # 3D Models
    TXD = "txd"         # Texture Dictionary
    COL = "col"         # Collision Data
    IFP = "ifp"         # Animation Data
    IPL = "ipl"         # Item Placement
    DAT = "dat"         # Data files
    WAV = "wav"         # Audio files
    UNKNOWN = "unknown"
        # Aliases for backwards compatibility
    dff = DFF           # Lowercase alias
    txd = TXD           # Lowercase alias
    col = COL           # Lowercase alias
    ifp = IFP           # Lowercase alias
    ipl = IPL           # Lowercase alias
    dat = DAT           # Lowercase alias
    wav = WAV           # Lowercase alias
    unknown = UNKNOWN   # Lowercase alias

    # Legacy alias
    MODEL = DFF         # Old name alias

class Platform(Enum):
    """Platform types for IMG files"""
    PC = 0
    XBOX = 1
    PS2 = 2
    MOBILE = 3

class CompressionType(Enum):
    """Compression types"""
    NONE = "none"
    ZLIB = "zlib"
    LZO = "lzo"
    UNKNOWN = "unknown"

class RecentFilesManager:
    """Manage recently opened files"""
    def __init__(self, max_files: int = 10): #vers 1
        self.max_files = max_files
        self.recent_files: List[str] = []
        self.settings_file = "recent_files.json"
        self._load_recent_files()
    
    def _load_recent_files(self): #vers 1
        """Load recent files from settings"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    self.recent_files = data.get('recent_files', [])
        except Exception:
            self.recent_files = []
    
    def _save_recent_files(self): #vers 1
        """Save recent files to settings"""
        try:
            data = {'recent_files': self.recent_files}
            with open(self.settings_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    
    def add_file(self, file_path): #vers 2
        """Add file to recent files list"""
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        
        self.recent_files.insert(0, file_path)
        
        # Keep only max_files entries
        if len(self.recent_files) > self.max_files:
            self.recent_files = self.recent_files[:self.max_files]
        
        self._save_recent_files()
    
    def get_recent_files(self): #vers 1
        """Get list of recent files"""
        # Filter out files that no longer exist
        existing_files = [f for f in self.recent_files if os.path.exists(f)]
        if len(existing_files) != len(self.recent_files):
            self.recent_files = existing_files
            self._save_recent_files()
        return self.recent_files

class ValidationResult:
    """Results from entry validation"""
    def __init__(self): #vers 1
        self.is_valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def add_error(self, message: str): #vers 1
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str): #vers 1
        self.warnings.append(message)

class IMGEntry:
    """Represents a single file entry within an IMG archive - FIXED WITH RW VERSION DETECTION"""
    
    def __init__(self): #vers 4
        self.name: str = ""
        self.extension: str = ""
        self.offset: int = 0          # Offset in bytes
        self.size: int = 0            # Size in bytes
        self.uncompressed_size: int = 0
        self.file_type: FileType = FileType.UNKNOWN
        self.compression_type: CompressionType = CompressionType.NONE
        self.rw_version: int = 0      # RenderWare version
        self.rw_version_name: str = "" # ADDED: Human readable version name
        self.is_encrypted: bool = False
        self.is_new_entry: bool = False
        self.is_replaced: bool = False
        self.flags: int = 0
        self.compression_level = 0

        # Internal data cache
        self._cached_data: Optional[bytes] = None
        self._img_file: Optional['IMGFile'] = None
        self._version_detected: bool = False # ADDED: Track if version was detected
    
    def set_img_file(self, img_file: 'IMGFile'): #vers 1
        """Set reference to parent IMG file"""
        self._img_file = img_file

    def detect_file_type_and_version(self): #vers 2
        """ADDED: Detect file type and RW version from file data"""
        try:
            # Extract extension from name
            if '.' in self.name:
                self.extension = self.name.split('.')[-1].lower()
                self.file_type = self._get_file_type_from_extension()

            # For RenderWare files, detect version from data
            if self.is_renderware_file() and self._img_file and not self._version_detected:
                try:
                    data = self.get_data()
                    if len(data) >= 12:  # Minimum RW header size
                        # Use existing RW version detection function
                        version_info = parse_rw_version(data)
                        if version_info and 'version' in version_info:
                            self.rw_version = version_info['version']
                            self.rw_version_name = get_rw_version_name(self.rw_version)
                            self._version_detected = True

                except Exception as e:
                    message_box.warning(f"Could not detect RW version for {self.name}", 
                                       details=str(e))

        except Exception as e:
            message_box.error(f"Error detecting file type/version for {self.name}", 
                             details=str(e))


    def detect_file_type_and_version(self): #vers 1
        """ADDED: Detect file type and RW version from file data"""
        try:
            # Extract extension from name
            if '.' in self.name:
                self.extension = self.name.split('.')[-1].upper()
                self.extension = ''.join(c for c in self.extension if c.isalpha())
            else:
                self.extension = "NO_EXT"
            
            # Set file type based on extension
            ext_lower = self.extension.lower()
            if ext_lower == 'dff':
                self.file_type = FileType.DFF
            elif ext_lower == 'txd':
                self.file_type = FileType.TXD
            elif ext_lower == 'col':
                self.file_type = FileType.COL
            elif ext_lower == 'ifp':
                self.file_type = FileType.IFP
            elif ext_lower == 'ipl':
                self.file_type = FileType.IPL
            elif ext_lower == 'dat':
                self.file_type = FileType.DAT
            elif ext_lower == 'wav':
                self.file_type = FileType.WAV
            else:
                self.file_type = FileType.UNKNOWN

            # Detect RW version for RenderWare files
            if self.extension in ['DFF', 'TXD'] and not self._version_detected:
                self._detect_rw_version()
                
        except Exception as e:
            message_box.error(f"Error detecting file type for {self.name}", details=str(e))

    def _detect_rw_version(self): #vers 1
        """ADDED: Detect RenderWare version from file header"""
        try:
            if not self._img_file or not self._img_file.file_path:
                return

            # Read file header (first 12 bytes contain RW version info)
            file_data = self._read_header_data(12)
            if not file_data or len(file_data) < 12:
                return

            # Use existing parse_rw_version function
            version_value, version_name = parse_rw_version(file_data[8:12])
            
            if version_value > 0:
                self.rw_version = version_value
                self.rw_version_name = version_name
                self._version_detected = True
                message_box.success(f"Detected RW version {version_name} (0x{version_value:X}) for {self.name}")
            else:
                # Fallback: try reading from different offset
                if len(file_data) >= 8:
                    try:
                        alt_version = struct.unpack('<I', file_data[4:8])[0]
                        if 0x30000 <= alt_version <= 0x40000:  # Valid RW version range
                            self.rw_version = alt_version
                            self.rw_version_name = get_rw_version_name(alt_version)
                            self._version_detected = True
                            message_box.success(f"Detected RW version {self.rw_version_name} (alt method) for {self.name}")
                    except:
                        pass

        except Exception as e:
            message_box.error(f"Error detecting RW version for {self.name}", details=str(e))

    def _read_header_data(self, bytes_to_read: int) -> Optional[bytes]: #vers 1
        """ADDED: Read file header data from IMG file"""
        try:
            if not self._img_file or not self._img_file.file_path:
                return None

            # Determine which file to read from based on IMG version
            if self._img_file.version == IMGVersion.VERSION_1:
                # Read from .img file (companion to .dir)
                img_path = self._img_file.file_path.replace('.dir', '.img')
                if not os.path.exists(img_path):
                    return None
                file_path = img_path
            else:
                # Read from single .img file
                file_path = self._img_file.file_path

            with open(file_path, 'rb') as f:
                f.seek(self.offset)
                return f.read(min(self.size, bytes_to_read))

        except Exception as e:
            message_box.error(f"Error reading header data for {self.name}", details=str(e))
            return None

    def _get_file_type_from_extension(self) -> FileType: #vers 1
        """Get file type from extension"""
        ext_lower = self.extension.lower()
        try:
            return FileType(ext_lower)
        except ValueError:
            return FileType.UNKNOWN

    def get_version_text(self) -> str: #vers 2
        """FIXED: Get human-readable version text"""
        try:
            if self.extension in ['DFF', 'TXD']:
                if self.rw_version > 0 and self.rw_version_name:
                    return f"RW {self.rw_version_name}"
                elif self.rw_version > 0:
                    return f"RW 0x{self.rw_version:X}"
                else:
                    return "RW Unknown"
            elif self.extension == 'COL':
                return "COL"
            elif self.extension == 'IFP':
                return "IFP"
            elif self.extension == 'IPL':
                return "IPL"
            elif self.extension in ['WAV', 'MP3']:
                return "Audio"
            else:
                return "Unknown"
        except:
            return "Unknown"
    
    def get_offset_in_sectors(self) -> int: #vers 1
        """Get offset in 2048-byte sectors"""
        return self.offset // 2048
    
    def get_size_in_sectors(self) -> int: #vers 1
        """Get size in 2048-byte sectors (rounded up)"""
        return (self.size + 2047) // 2048
    
    def get_file_type(self) -> FileType: #vers 1
        """Get file type based on extension"""
        if not self.extension:
            return FileType.UNKNOWN
        
        ext_lower = self.extension.lower().lstrip('.')
        try:
            return FileType(ext_lower)
        except ValueError:
            return FileType.UNKNOWN
    
    def is_renderware_file(self) -> bool: #vers 1
        """Check if file is a RenderWare format"""
        return self.extension.upper() in ['DFF', 'TXD']
    
    def validate(self) -> ValidationResult: #vers 1
        """Validate entry data"""
        result = ValidationResult()
        
        try:
            # Check basic attributes
            if not self.name:
                result.add_error("Entry has no name")
            
            if self.size < 0:
                result.add_error("Entry has negative size")
            
            if self.offset < 0:
                result.add_error("Entry has negative offset")
            
            # Check name validity
            if len(self.name) > 24:
                result.add_warning("Entry name longer than 24 characters")
            
            invalid_chars = set('\x00\xff\xcd')
            if any(char in self.name for char in invalid_chars):
                result.add_error("Entry name contains invalid characters")
            
            # Validate data if available
            if self._img_file:
                try:
                    data = self.get_data()
                    if len(data) != self.size:
                        result.add_warning(f"Entry {self.name} actual size differs from header")
                except Exception as e:
                    result.add_error(f"Cannot read data for {self.name}: {str(e)}")

        except Exception as e:
            result.add_error(f"Validation error for {self.name}: {str(e)}")

        return result
    
    def get_data(self) -> bytes: #vers 1
        """Read entry data from IMG file"""
        if not self._img_file:
            raise ValueError("No IMG file reference set")
        
        return self._img_file.read_entry_data(self)
    
    def set_data(self, data: bytes): #vers 1
        """Write entry data to IMG file"""
        if not self._img_file:
            raise ValueError("No IMG file reference set")
        
        self._img_file.write_entry_data(self, data)

# INLINE PLATFORM DETECTION FUNCTIONS - to replace the circular import
def detect_img_platform(file_path: str): #vers 1
    """INLINE: Simple platform detection to avoid circular import"""
    try:
        filename = os.path.basename(file_path).lower()
        
        # Simple platform detection based on filename/path
        if any(keyword in filename for keyword in ['ps2', 'playstation']):
            return IMGPlatform.PS2, {'confidence': 70, 'indicators': ['ps2_filename']}
        elif any(keyword in filename for keyword in ['xbox']):
            return IMGPlatform.XBOX, {'confidence': 70, 'indicators': ['xbox_filename']}
        elif any(keyword in filename for keyword in ['android', 'mobile']):
            return IMGPlatform.ANDROID, {'confidence': 70, 'indicators': ['android_filename']}
        elif any(keyword in filename for keyword in ['psp', 'stories']):
            return IMGPlatform.PSP, {'confidence': 70, 'indicators': ['psp_filename']}
        else:
            return IMGPlatform.PC, {'confidence': 50, 'indicators': ['default_pc']}
            
    except Exception:
        return IMGPlatform.UNKNOWN, {'confidence': 0, 'indicators': ['error']}

def detect_img_platform_inline(file_path: str) -> IMGPlatform: #vers 1
    """MOVED: Simple platform detection to avoid circular import"""
    try:
        filename = os.path.basename(file_path).lower()

        # Simple platform detection based on filename/path
        if any(keyword in filename for keyword in ['ps2', 'playstation']):
            return IMGPlatform.PS2
        elif any(keyword in filename for keyword in ['xbox']):
            return IMGPlatform.XBOX
        elif any(keyword in filename for keyword in ['android', 'mobile']):
            return IMGPlatform.ANDROID
        elif any(keyword in filename for keyword in ['psp', 'stories']):
            return IMGPlatform.PSP
        else:
            return IMGPlatform.PC

    except Exception:
        return IMGPlatform.UNKNOWN


def get_platform_specific_specs(platform: IMGPlatform) -> Dict[str, Any]: #vers 1
    """INLINE: Get platform-specific specifications"""
    specs = {
        IMGPlatform.PC: {
            'sector_size': 2048,
            'entry_size': 32,
            'name_length': 24,
            'endianness': 'little',
            'supports_compression': True,
            'max_entries': 65535
        },
        IMGPlatform.PS2: {
            'sector_size': 2048,
            'entry_size': 32,
            'name_length': 24,
            'endianness': 'little',
            'supports_compression': False,
            'max_entries': 16000,
            'special_alignment': True
        },
        IMGPlatform.ANDROID: {
            'sector_size': 2048,
            'entry_size': 32,
            'name_length': 24,
            'endianness': 'little',
            'supports_compression': True,
            'max_entries': 32000,
            'mobile_optimized': True
        },
        IMGPlatform.PSP: {
            'sector_size': 2048,
            'entry_size': 32,
            'name_length': 24,
            'endianness': 'little',
            'supports_compression': False,
            'max_entries': 8000,
            'stories_format': True
        }
    }
    return specs.get(platform, specs[IMGPlatform.PC])

def get_img_platform_info(file_path: str) -> Dict[str, Any]: #vers 1
    """Get platform information for IMG file"""
    platform, detection_info = detect_img_platform(file_path)
    return {
        'platform': platform.value,
        'detected_from': 'filename_analysis',
        'supported_features': {
            'compression': platform in [IMGPlatform.PC, IMGPlatform.ANDROID],
            'encryption': False,
            'large_files': platform != IMGPlatform.PSP
        }
    }

class IMGFile:
    """Main IMG archive file handler - FIXED WITH PLATFORM SUPPORT"""
    
    def __init__(self, file_path: str = ""): #vers 5
        self.file_path: str = file_path
        self.version: IMGVersion = IMGVersion.UNKNOWN
        self.platform: IMGPlatform = IMGPlatform.UNKNOWN  # ADDED: Platform detection
        self.platform_specs: Dict[str, Any] = {}  # ADDED: Platform-specific specs
        self.entries: List[IMGEntry] = []
        self.is_open: bool = False
        self.total_size: int = 0
        self.creation_time: Optional[float] = None
        self.modification_time: Optional[float] = None

        # File handles
        self._img_handle: Optional[BinaryIO] = None
        self._dir_handle: Optional[BinaryIO] = None
    
    def create_new(self, output_path: str, version: IMGVersion, **options) -> bool: #vers 2
        """Create new IMG file with specified parameters"""
        try:
            self.file_path = output_path
            self.version = version
            self.entries = []

            # Extract creation options
            initial_size_mb = options.get('initial_size_mb', 50)
            compression_enabled = options.get('compression_enabled', False)
            game_preset = options.get('game_preset', None)

            if version == IMGVersion.VERSION_1:
                # Use Version 1 creator
                from core.img_version1 import IMGVersion1Creator
                creator = IMGVersion1Creator()
                success = creator.create_version_1(output_path, initial_size_mb)
                if success:
                    self.entries = creator.entries
                    self.file_path = creator.dir_path  # Store DIR file path for Version 1
                return success
                
            elif version == IMGVersion.VERSION_2:
                # Use Version 2 creator
                from core.img_version2 import IMGVersion2Creator
                creator = IMGVersion2Creator()
                success = creator.create_version_2(output_path, initial_size_mb, compression_enabled)
                if success:
                    self.entries = creator.entries
                    self.file_path = creator.file_path
                return success
                
            else:
                message_box.error(f"Unsupported IMG version: {version}")
                return False

        except Exception as e:
            message_box.error("Error creating IMG file", details=str(e))
            return False

    def save_img_file(self) -> bool: #vers 1
        """Save IMG file with current entries"""
        try:
            if not self.file_path or not self.entries:
                message_box.warning("Cannot save IMG file: No file path or entries")
                return False

            # Create backup first
            import shutil
            backup_path = self.file_path + '.backup'
            shutil.copy2(self.file_path, backup_path)

            # Rebuild the IMG file
            return self.rebuild_img_file()

        except Exception as e:
            message_box.error("Failed to save IMG file", details=str(e))
            return False

    def rebuild_img_file(self) -> bool: #vers 1
        """Rebuild IMG file with current entries"""
        try:
            import struct
            import os
            
            if self.version == IMGVersion.VERSION_1:
                return self._rebuild_version1()
            else:
                return self._rebuild_version2()

        except Exception as e:
            message_box.error("Failed to rebuild IMG file", details=str(e))
            return False
            
    def _rebuild_version2(self) -> bool: #vers 1
        """Rebuild Version 2 IMG file (SA format)"""
        try:
            import struct
            import os

            # Calculate sizes
            entry_count = len(self.entries)
            directory_size = entry_count * 32  # 32 bytes per entry
            data_start = directory_size

            # Collect entry data
            entry_data_list = []
            current_offset = data_start

            for entry in self.entries:
                # Get entry data
                if hasattr(entry, '_cached_data') and entry._cached_data:
                    data = entry._cached_data
                else:
                    data = self.read_entry_data(entry)

                entry_data_list.append(data)

                # Update entry with new offset/size
                entry.offset = current_offset
                entry.size = len(data)

                # Align to sector boundary (2048 bytes)
                aligned_size = ((len(data) + 2047) // 2048) * 2048
                current_offset += aligned_size

            # Write new IMG file
            with open(self.file_path, 'wb') as f:
                # Write directory
                for i, entry in enumerate(self.entries):
                    # Convert to sectors
                    offset_sectors = entry.offset // 2048
                    size_sectors = ((entry.size + 2047) // 2048)

                    # Pack entry: offset(4), size(4), name(24)
                    entry_data = struct.pack('<II', offset_sectors, size_sectors)
                    name_bytes = entry.name.encode('ascii')[:24].ljust(24, b'\x00')
                    entry_data += name_bytes

                    f.write(entry_data)

                # Write file data
                for i, data in enumerate(entry_data_list):
                    f.seek(self.entries[i].offset)
                    f.write(data)

                    # Pad to sector boundary
                    current_pos = f.tell()
                    sector_end = ((current_pos + 2047) // 2048) * 2048
                    if current_pos < sector_end:
                        f.write(b'\x00' * (sector_end - current_pos))

            message_box.success(f"Successfully rebuilt IMG file with {entry_count} entries")
            return True

        except Exception as e:
            message_box.error("Failed to rebuild Version 2 IMG", details=str(e))
            return False

    def _rebuild_version1(self) -> bool: #vers 1
        """Rebuild Version 1 IMG file (DIR/IMG pair)"""
        try:
            import struct
            import os

            # Get DIR and IMG paths
            dir_path = self.file_path
            img_path = self.file_path.replace('.dir', '.img')

            entry_count = len(self.entries)

            # Collect entry data and calculate offsets
            entry_data_list = []
            current_offset = 0

            for entry in self.entries:
                # Get entry data
                if hasattr(entry, '_cached_data') and entry._cached_data:
                    data = entry._cached_data
                else:
                    data = self.read_entry_data(entry)

                entry_data_list.append(data)

                # Update entry with new offset/size
                entry.offset = current_offset
                entry.size = len(data)

                # Align to sector boundary
                aligned_size = ((len(data) + 2047) // 2048) * 2048
                current_offset += aligned_size

            # Write DIR file
            with open(dir_path, 'wb') as f:
                for entry in self.entries:
                    # Convert to sectors
                    offset_sectors = entry.offset // 2048
                    size_sectors = ((entry.size + 2047) // 2048)

                    # Pack entry: offset(4), size(4), name(24)
                    entry_data = struct.pack('<II', offset_sectors, size_sectors)
                    name_bytes = entry.name.encode('ascii')[:24].ljust(24, b'\x00')
                    entry_data += name_bytes

                    f.write(entry_data)

            # Write IMG file
            with open(img_path, 'wb') as f:
                for i, data in enumerate(entry_data_list):
                    f.seek(self.entries[i].offset)
                    f.write(data)

                    # Pad to sector boundary
                    current_pos = f.tell()
                    sector_end = ((current_pos + 2047) // 2048) * 2048
                    if current_pos < sector_end:
                        f.write(b'\x00' * (sector_end - current_pos))

            message_box.success(f"Successfully rebuilt DIR/IMG pair with {entry_count} entries")
            return True

        except Exception as e:
            message_box.error("Failed to rebuild Version 1 IMG", details=str(e))
            return False

    def import_file(self, file_path: str) -> bool: #vers 1
        """Import file into IMG"""
        try:
            import os
            filename = os.path.basename(file_path)

            # Read file data
            with open(file_path, 'rb') as f:
                data = f.read()

            # Use add_entry method
            return self.add_entry(filename, data)

        except Exception as e:
            message_box.error(f"Failed to import file {file_path}", details=str(e))
            return False

    def add_entry(self, filename: str, data: bytes, auto_save: bool = True) -> bool: #vers 1
        """Add new entry to IMG file"""
        try:
            # Create new IMGEntry
            new_entry = IMGEntry()
            new_entry.name = filename
            new_entry.size = len(data)
            new_entry.set_img_file(self)
            new_entry._cached_data = data

            # Add to entries list
            self.entries.append(new_entry)
            
            # Only save if requested (for batch operations)
            if auto_save:
                return self.save_img_file()

            return True

        except Exception as e:
            message_box.error(f"Failed to add entry {filename}", details=str(e))
            return False

    def detect_version(self) -> IMGVersion: #vers 4
        """Detect IMG version and platform from file"""
        try:
            if not os.path.exists(self.file_path):
                return IMGVersion.UNKNOWN

            # ADDED: Platform detection first
            detected_platform, detection_info = detect_img_platform(self.file_path)
            self.platform = detected_platform
            self.platform_specs = get_platform_specific_specs(detected_platform)

            # Check if it's a .dir file (Version 1)
            if self.file_path.lower().endswith('.dir'):
                img_path = self.file_path[:-4] + '.img'
                if os.path.exists(img_path):
                    self.version = IMGVersion.VERSION_1
                    return IMGVersion.VERSION_1

            # Check if it's a single .img file (Version 2)
            if self.file_path.lower().endswith('.img'):
                try:
                    with open(self.file_path, 'rb') as f:
                        header = f.read(4)
                        if header == b'VER2':
                            self.version = IMGVersion.VERSION_2
                            return IMGVersion.VERSION_2
                        # Could be Version 1 IMG file without DIR
                        self.version = IMGVersion.VERSION_1
                        return IMGVersion.VERSION_1
                except:
                    pass

        except Exception as e:
            message_box.error("Error detecting IMG version", details=str(e))

        self.version = IMGVersion.UNKNOWN
        return IMGVersion.UNKNOWN

    def open(self) -> bool: #vers 5
        """Open and parse IMG file - FIXED WITH PROPER ENTRY PARSING"""
        try:
            if self.is_open:
                return True

            # Detect version first
            if self.version == IMGVersion.UNKNOWN:
                self.detect_version()

            # Clear existing entries
            self.entries.clear()

            # Open based on version
            success = False
            if self.version == IMGVersion.VERSION_1:
                success = self._open_version_1()
            elif self.version == IMGVersion.VERSION_2:
                success = self._open_version_2()

            if success:
                self.is_open = True
                # FIXED: Parse file types and versions for all entries
                self._parse_all_entries()
                message_box.success(f"Successfully opened IMG file with {len(self.entries)} entries")
            
            return success

        except Exception as e:
            message_box.error("Error opening IMG file", details=str(e))
            return False

    def _parse_all_entries(self): #vers 2
        """ADDED: Parse file types and versions for all entries + UNKNOWN RW DETECTION"""
        try:
            for i, entry in enumerate(self.entries):
                try:
                    # Detect file type and RW version
                    entry.detect_file_type_and_version()
                except Exception as e:
                    message_box.warning(f"Error parsing entry {entry.name}", details=str(e))
                    
            # ADDED: Trigger unknown RW file detection after parsing
            self._trigger_unknown_rw_detection()
            
        except Exception as e:
            message_box.error("Error parsing all entries", details=str(e))

    def _trigger_unknown_rw_detection(self): #vers 1
        """ADDED: Trigger unknown RW file detection and snapshotting"""
        try:
            # Try to find main window reference for unknown RW detection
            # This will be set by the integration function
            if hasattr(self, '_main_window_ref') and self._main_window_ref:
                main_window = self._main_window_ref
                if hasattr(main_window, 'rw_snapshot_manager'):
                    unknown_files = main_window.rw_snapshot_manager.capture_unknown_rw_files(self)
                    if unknown_files:
                        message_box.info(f"Captured {len(unknown_files)} unknown RW files for analysis")
                else:
                    message_box.info("RW snapshot manager not available - skipping unknown detection")
            else:
                message_box.info("Main window reference not available - skipping unknown detection")
            
        except Exception as e:
            message_box.warning("Error in unknown RW detection", details=str(e))

    def set_main_window_reference(self, main_window): #vers 1
        """ADDED: Set main window reference for unknown RW detection"""
        self._main_window_ref = main_window

    def _open_version_2(self) -> bool: #vers 5
        """Open IMG version 2 (single file) - ENHANCED WITH PLATFORM SUPPORT"""
        try:
            # Use platform-specific specifications
            sector_size = self.platform_specs.get('sector_size', 2048)
            
            with open(self.file_path, 'rb') as f:
                # Skip VER2 header (4 bytes)
                f.seek(4)
                # Read entry count
                entry_count = struct.unpack('<I', f.read(4))[0]
                
                # Platform-specific entry count validation
                max_entries = self.platform_specs.get('max_entries', 65535)
                if entry_count > max_entries:
                    message_box.warning(f"Entry count {entry_count} exceeds platform limit {max_entries}")

                for i in range(entry_count):
                    # Read entry: offset(4), size(4), name(24)
                    entry_data = f.read(32)
                    if len(entry_data) < 32:
                        break

                    entry_offset, entry_size = struct.unpack('<II', entry_data[:8])
                    entry_name = entry_data[8:32].rstrip(b'\x00').decode('ascii', errors='ignore')

                    if entry_name:
                        entry = IMGEntry()
                        entry.name = entry_name
                        entry.offset = entry_offset * 2048  # Convert sectors to bytes
                        entry.size = entry_size * 2048
                        entry.set_img_file(self)
                        self.entries.append(entry)

            return True
        except Exception as e:
            message_box.error("Error opening Version 2 IMG", details=str(e))
            return False

    def _open_version_1(self) -> bool: #vers 4
        """Open IMG version 1 (DIR/IMG pair)"""
        dir_path = self.file_path[:-4] + '.dir'
        if not os.path.exists(dir_path):
            return False

        try:
            with open(dir_path, 'rb') as dir_file:
                dir_data = dir_file.read()

            # Parse directory entries (32 bytes each)
            entry_count = len(dir_data) // 32
            for i in range(entry_count):
                offset = i * 32
                entry_data = dir_data[offset:offset+32]

                if len(entry_data) < 32:
                    break

                # Parse entry: offset(4), size(4), name(24)
                entry_offset, entry_size = struct.unpack('<II', entry_data[:8])
                entry_name = entry_data[8:32].rstrip(b'\x00').decode('ascii', errors='ignore')

                if entry_name:
                    entry = IMGEntry()
                    entry.name = entry_name
                    entry.offset = entry_offset * 2048  # Convert sectors to bytes
                    entry.size = entry_size * 2048
                    entry.set_img_file(self)
                    self.entries.append(entry)

            return True
        except Exception as e:
            message_box.error("Error opening Version 1 IMG", details=str(e))
            return False

    def read_entry_data(self, entry: IMGEntry) -> bytes: #vers 1
        """Read data for a specific entry"""
        try:
            if self.version == IMGVersion.VERSION_1:
                # Read from .img file
                img_path = self.file_path.replace('.dir', '.img')
                with open(img_path, 'rb') as f:
                    f.seek(entry.offset)
                    return f.read(entry.size)
            else:
                # Read from single .img file
                with open(self.file_path, 'rb') as f:
                    f.seek(entry.offset)
                    return f.read(entry.size)
        except Exception as e:
            raise RuntimeError(f"Failed to write entry data: {e}")

    def write_entry_data(self, entry: IMGEntry, data: bytes): #vers 1
        """Write data for a specific entry"""
        try:
            if self.version == IMGVersion.VERSION_1:
                # Write to .img file
                img_path = self.file_path.replace('.dir', '.img')
                with open(img_path, 'r+b') as f:
                    f.seek(entry.offset)
                    f.write(data)
            else:
                # Write to single .img file
                with open(self.file_path, 'r+b') as f:
                    f.seek(entry.offset)
                    f.write(data)
        except Exception as e:
            raise RuntimeError(f"Failed to write entry data: {e}")

    def close(self): #vers 1
        """Close IMG file"""
        self.is_open = False
        self.entries.clear()

    def get_creation_info(self) -> Dict[str, Any]: #vers 1
        """Get information about the IMG file"""
        if not self.file_path or not os.path.exists(self.file_path):
            return {}
        
        try:
            file_size = os.path.getsize(self.file_path)
            return {
                'path': self.file_path,
                'size_bytes': file_size,
                'size_mb': file_size / (1024 * 1024),
                'entries_count': len(self.entries),
                'version': self.version.name,
                'format': f'IMG Version {self.version.value}'
            }
        except Exception:
            return {}

def format_file_size(size_bytes: int) -> str: #vers 1
    """Format file size in human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

# GUI classes have been removed and moved to img_editor.py

def integrate_filtering(main_window): #vers 2
    """Integrate filtering functionality into main window - NOTE: Now a stub function to avoid circular imports"""
    # We'll use the FilterPanel from img_editor.py directly in the main application
    return None

def create_entries_table_panel(main_window): #vers 4
    """Create the complete entries table panel - NOTE: Now a stub function to avoid circular imports"""
    # We'll use the GUI components from img_editor.py directly in the main application
    panel = QWidget()
    return panel

def create_img_file(output_path: str, version: IMGVersion, **options) -> bool: #vers 2
    """Create IMG file using appropriate version creator"""
    img = IMGFile()
    return img.create_new(output_path, version, **options)

def detect_img_version(file_path: str) -> IMGVersion: #vers 2
    """Detect IMG version without fully opening the file"""
    img = IMGFile(file_path)
    return img.detect_version()

def populate_table_with_sample_data(table): #vers 3
    """Populate table with sample data for testing - NOTE: Updated to work with any table object"""
    sample_entries = [
        {"name": "player.dff", "extension": "DFF", "size": 250880, "offset": 0x2000, "version": "RW 3.6"},
        {"name": "player.txd", "extension": "TXD", "size": 524288, "offset": 0x42000, "version": "RW 3.6"},
        {"name": "vehicle.col", "extension": "COL", "size": 131072, "offset": 0x84000, "version": "COL 2"},
        {"name": "dance.ifp", "extension": "IFP", "size": 1258291, "offset": 0xA4000, "version": "IFP 1"},
    ]

    # Convert to mock entry objects
    class MockEntry:
        def __init__(self, data): #vers 1
            self.name = data["name"]
            self.extension = data["extension"]
            self.size = data["size"]
            self.offset = data["offset"]
            self._version = data["version"]
            self.is_new_entry = False
            self.is_replaced = False
            self.compression_type = CompressionType.NONE

        def get_version_text(self): #vers 1
            return self._version

    mock_entries = [MockEntry(data) for data in sample_entries]
    # Check if table has a populate_entries method before calling it
    if hasattr(table, 'populate_entries'):
        table.populate_entries(mock_entries)

# Export classes and functions - GUI components now imported from img_editor.py
__all__ = [
    'IMGVersion',
    'FileType', 
    'CompressionType',
    'Platform',
    'IMGEntry',
    'IMGFile',
    'ValidationResult',
    'RecentFilesManager',
    'create_img_file',
    'format_file_size',
    'integrate_filtering',
    'create_entries_table_panel',
    'detect_img_version',
    'populate_table_with_sample_data',
    'get_img_platform_info',  # ADDED: Platform info function
    'IMGPlatform'  # ADDED: Now exported since moved here
]
