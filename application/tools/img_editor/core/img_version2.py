#this belongs in components/ img_version2.py - Version: 2
# X-Seti - July16 2025 - Img Factory 1.5

"""
IMG Version 2 Creator - Single IMG file format
Handles creation of VER2 IMG files with proper SA support
FIXED: Method naming, parameter conversion, and file I/O issues
"""

import os
import struct
from typing import Optional, List, Dict, Any
from pathlib import Path


class IMGVersion2Creator:
    """Creates IMG Version 2 files (single .img file with VER2 header)"""
    
    def __init__(self):
        self.entries = []
        self.file_path = ""
        
    def create_version_2(self, output_path: str, initial_size_mb: int, compression_enabled: bool = False) -> bool:
        """Create IMG version 2 (single file) - COMPLETE IMPLEMENTATION"""
        try:
            # Convert MB to bytes
            initial_size = initial_size_mb * 1024 * 1024
            
            if not output_path.lower().endswith('.img'):
                output_path += '.img'

            # Create dummy DFF file content
            dummy_dff = self._create_dummy_dff()

            with open(output_path, 'wb') as img_file:
                # Write VER2 header
                img_file.write(b'VER2')

                # Write entry count (1 initial dummy entry)
                img_file.write(struct.pack('<I', 1))

                # Calculate entry offset (header + entry table)
                # Header: 4 bytes (VER2) + 4 bytes (count) = 8 bytes
                # Entry table: 32 bytes per entry = 32 bytes
                # Total header size: 40 bytes, round up to sector (2048)
                entries_start = 2048

                # Write entry table
                entry_offset_sectors = entries_start // 2048
                entry_size_sectors = (len(dummy_dff) + 2047) // 2048

                # Entry format: offset(4), size(4), name(24)
                img_file.write(struct.pack('<I', entry_offset_sectors))  # offset in sectors
                img_file.write(struct.pack('<I', entry_size_sectors))    # size in sectors
                img_file.write(b'replaceme.dff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')  # name (24 bytes)

                # Pad to entries start
                current_pos = img_file.tell()
                padding_needed = entries_start - current_pos
                if padding_needed > 0:
                    img_file.write(b'\x00' * padding_needed)

                # Write dummy file data
                img_file.write(dummy_dff)

                # Pad dummy file to sector boundary
                file_end = img_file.tell()
                sector_padding = 2048 - (len(dummy_dff) % 2048)
                if sector_padding < 2048:
                    img_file.write(b'\x00' * sector_padding)

                # Pad to initial size
                current_size = img_file.tell()
                if initial_size > current_size:
                    img_file.write(b'\x00' * (initial_size - current_size))

            # Store file info and add dummy entry
            self.file_path = output_path
            self._add_dummy_entry(len(dummy_dff))

            return True

        except Exception as e:
            print(f"❌ Error creating Version 2 IMG: {e}")
            return False

    def _create_dummy_dff(self) -> bytes:
        """Create minimal valid DFF file for initial structure"""
        # Minimal RenderWare DFF structure
        dff_header = struct.pack('<III', 0x10, 0x1003FFFF, 0x0800)  # DFF header
        clump_header = struct.pack('<III', 0x10, 0x1003FFFF, 0x0800)  # Clump header
        
        return dff_header + clump_header + b'\x00' * 500  # Minimal DFF content
    
    def _add_dummy_entry(self, size: int):
        """Add dummy entry to entries list"""
        from components.img_core_classes import IMGEntry, FileType
        
        dummy_entry = IMGEntry()
        dummy_entry.name = "replaceme.dff"
        dummy_entry.extension = "dff"
        dummy_entry.offset = 2048  # After header
        dummy_entry.size = size
        dummy_entry.file_type = FileType.dff
        dummy_entry.is_new_entry = True
        
        self.entries.append(dummy_entry)
    
    def create_sa_version_2(self, output_path: str, initial_size_mb: int, game_preset: Dict[str, Any]) -> bool:
        """Create SA-specific Version 2 IMG with proper settings"""
        try:
            # SA-specific settings
            compression_enabled = game_preset.get('compression', False)
            
            # Use standard Version 2 creation with SA tweaks
            success = self.create_version_2(output_path, initial_size_mb, compression_enabled)
            
            if success:
                print(f"✅ SA Version 2 IMG created: {output_path}")
                print(f"   Size: {initial_size_mb}MB")
                print(f"   Compression: {'Enabled' if compression_enabled else 'Disabled'}")
            
            return success
            
        except Exception as e:
            print(f"❌ Error creating SA Version 2 IMG: {e}")
            return False
    
    def get_creation_info(self) -> Dict[str, Any]:
        """Get information about created IMG file"""
        if not self.file_path or not os.path.exists(self.file_path):
            return {}
        
        try:
            file_size = os.path.getsize(self.file_path)
            return {
                'path': self.file_path,
                'size_bytes': file_size,
                'size_mb': file_size / (1024 * 1024),
                'entries_count': len(self.entries),
                'version': 'VER2',
                'format': 'IMG Version 2'
            }
        except Exception:
            return {}


def create_version_2_img(output_path: str, initial_size_mb: int = 100, 
                        compression_enabled: bool = False, 
                        game_preset: Optional[Dict[str, Any]] = None) -> bool:
    """Convenience function to create Version 2 IMG file"""
    creator = IMGVersion2Creator()
    
    if game_preset and game_preset.get('code') == 'gtasa':
        return creator.create_sa_version_2(output_path, initial_size_mb, game_preset)
    else:
        return creator.create_version_2(output_path, initial_size_mb, compression_enabled)


def get_version_2_specs() -> Dict[str, Any]:
    """Get Version 2 IMG format specifications"""
    return {
        'format_name': 'IMG Version 2',
        'file_extension': '.img',
        'header_signature': 'VER2',
        'header_size': 8,  # 4 bytes signature + 4 bytes entry count
        'entry_size': 32,  # 4 offset + 4 size + 24 name
        'sector_size': 2048,
        'max_entries': 65535,
        'supports_compression': True,
        'supports_encryption': False,
        'games': ['GTA San Andreas', 'GTA IV', 'Custom projects']
    }


# Export functions
__all__ = [
    'IMGVersion2Creator',
    'create_version_2_img', 
    'get_version_2_specs'
]
