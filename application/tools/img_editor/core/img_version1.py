#this belongs in components/ img_version1.py - Version: 1
# X-Seti - July16 2025 - Img Factory 1.5

"""
IMG Version 1 Creator - DIR+IMG file format
Handles creation of Version 1 IMG files (separate .dir and .img files)
"""

import os
import struct
from typing import Optional, List, Dict, Any
from pathlib import Path


class IMGVersion1Creator:
    """Creates IMG Version 1 files (separate .dir and .img files)"""
    
    def __init__(self):
        self.entries = []
        self.dir_path = ""
        self.img_path = ""
        
    def create_version_1(self, output_path: str, initial_size_mb: int) -> bool:
        """Create IMG version 1 (DIR+IMG pair) - FIXED METHOD SIGNATURE"""
        try:
            # Determine file paths
            if output_path.lower().endswith('.img'):
                self.img_path = output_path
                self.dir_path = output_path[:-4] + '.dir'
            elif output_path.lower().endswith('.dir'):
                self.dir_path = output_path
                self.img_path = output_path[:-4] + '.img'
            else:
                self.img_path = output_path + '.img'
                self.dir_path = output_path + '.dir'

            # Create dummy DFF file content
            dummy_dff = self._create_dummy_dff()
            
            # Calculate initial size in bytes
            initial_size = initial_size_mb * 1024 * 1024

            # Create .dir file
            with open(self.dir_path, 'wb') as dir_file:
                # Write entry count (1 entry)
                dir_file.write(struct.pack('<I', 1))
                
                # Write entry: offset(4), size(4), name(24)
                entry_size_sectors = (len(dummy_dff) + 2047) // 2048
                dir_file.write(struct.pack('<I', 0))  # offset: 0 sectors
                dir_file.write(struct.pack('<I', entry_size_sectors))  # size in sectors
                dir_file.write(b'replaceme.dff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')  # name (24 bytes)

            # Create .img file
            with open(self.img_path, 'wb') as img_file:
                # Write dummy file data
                img_file.write(dummy_dff)
                
                # Pad to sector boundary (2048 bytes)
                padding = 2048 - (len(dummy_dff) % 2048)
                if padding < 2048:
                    img_file.write(b'\x00' * padding)

                # Pad to initial size
                current_size = img_file.tell()
                if initial_size > current_size:
                    img_file.write(b'\x00' * (initial_size - current_size))

            # Add dummy entry to our entries list
            self._add_dummy_entry(len(dummy_dff))
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating Version 1 IMG: {e}")
            return False
    
    def _create_dummy_dff(self) -> bytes:
        """Create minimal valid DFF file for initial structure"""
        # Minimal RenderWare DFF structure for GTA3/VC
        dff_header = struct.pack('<III', 0x10, 0x1001FFFF, 0x0800)  # DFF header (older version)
        clump_header = struct.pack('<III', 0x10, 0x1001FFFF, 0x0800)  # Clump header
        
        return dff_header + clump_header + b'\x00' * 400  # Minimal DFF content
    
    def _add_dummy_entry(self, size: int):
        """Add dummy entry to entries list"""
        from components.img_core_classes import IMGEntry, FileType
        
        dummy_entry = IMGEntry()
        dummy_entry.name = "replaceme.dff"
        dummy_entry.extension = "dff"
        dummy_entry.offset = 0  # First entry at offset 0
        dummy_entry.size = size
        dummy_entry.file_type = FileType.dff
        dummy_entry.is_new_entry = True
        
        self.entries.append(dummy_entry)
    
    def create_gta3_version_1(self, output_path: str, initial_size_mb: int, game_preset: Dict[str, Any]) -> bool:
        """Create GTA3-specific Version 1 IMG"""
        try:
            success = self.create_version_1(output_path, initial_size_mb)
            
            if success:
                print(f"✅ GTA3 Version 1 IMG created: {self.img_path}")
                print(f"   DIR file: {self.dir_path}")
                print(f"   Size: {initial_size_mb}MB")
            
            return success
            
        except Exception as e:
            print(f"❌ Error creating GTA3 Version 1 IMG: {e}")
            return False
    
    def create_vc_version_1(self, output_path: str, initial_size_mb: int, game_preset: Dict[str, Any]) -> bool:
        """Create Vice City-specific Version 1 IMG"""
        try:
            success = self.create_version_1(output_path, initial_size_mb)
            
            if success:
                print(f"✅ Vice City Version 1 IMG created: {self.img_path}")
                print(f"   DIR file: {self.dir_path}")
                print(f"   Size: {initial_size_mb}MB")
            
            return success
            
        except Exception as e:
            print(f"❌ Error creating VC Version 1 IMG: {e}")
            return False
    
    def get_creation_info(self) -> Dict[str, Any]:
        """Get information about created IMG files"""
        if not self.img_path or not os.path.exists(self.img_path):
            return {}
        
        try:
            img_size = os.path.getsize(self.img_path)
            dir_size = os.path.getsize(self.dir_path) if os.path.exists(self.dir_path) else 0
            
            return {
                'img_path': self.img_path,
                'dir_path': self.dir_path,
                'img_size_bytes': img_size,
                'dir_size_bytes': dir_size,
                'total_size_mb': (img_size + dir_size) / (1024 * 1024),
                'entries_count': len(self.entries),
                'version': 'VER1',
                'format': 'IMG Version 1 (DIR+IMG)'
            }
        except Exception:
            return {}


def create_version_1_img(output_path: str, initial_size_mb: int = 100, 
                        game_preset: Optional[Dict[str, Any]] = None) -> bool:
    """Convenience function to create Version 1 IMG file"""
    creator = IMGVersion1Creator()
    
    if game_preset:
        game_code = game_preset.get('code', '')
        if game_code == 'gta3':
            return creator.create_gta3_version_1(output_path, initial_size_mb, game_preset)
        elif game_code == 'gtavc':
            return creator.create_vc_version_1(output_path, initial_size_mb, game_preset)
    
    # Default Version 1 creation
    return creator.create_version_1(output_path, initial_size_mb)


def get_version_1_specs() -> Dict[str, Any]:
    """Get Version 1 IMG format specifications"""
    return {
        'format_name': 'IMG Version 1',
        'file_extensions': ['.img', '.dir'],
        'header_signature': None,  # No header signature
        'dir_entry_size': 32,  # 4 offset + 4 size + 24 name
        'sector_size': 2048,
        'max_entries': 65535,
        'supports_compression': False,
        'supports_encryption': False,
        'games': ['GTA III', 'GTA Vice City', 'Legacy projects']
    }


# Export functions
__all__ = [
    'IMGVersion1Creator',
    'create_version_1_img',
    'get_version_1_specs'
]
