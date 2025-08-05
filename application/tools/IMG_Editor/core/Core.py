"""
Core components for handling GTA IMG archives.
This module defines the main classes for representing IMG files and their entries.

IMG Archive Format:
- Version 1 (GTA III & VC): Separate .dir and .img files
- Version 2 (GTA SA): Combined directory and data in single .img file

All files are stored in sectors of 2048 bytes regardless of their actual size.
"""

import os
import struct
from pathlib import Path

# Constants
SECTOR_SIZE = 2048
V2_SIGNATURE = b'VER2'
MAX_FILENAME_LENGTH = 24

class IMGEntry:
    """Represents a single entry in an IMG archive."""
    def __init__(self):
        self.offset = 0          # Offset in sectors (multiply by 2048 for actual byte offset)
        self.streaming_size = 0  # Size in sectors for streaming (V2 only)
        self.size = 0            # Size in sectors
        self.name = ""           # Filename (max 24 chars, null-terminated)
        self.is_compressed = False  # Flag for compression status
        self.data = None         # To hold entry data when loaded
    
    @property
    def actual_offset(self):
        """Returns the actual offset of the entry in bytes."""
        return self.offset * SECTOR_SIZE
    
    @property
    def actual_size(self):
        """Returns the actual size of the entry in bytes."""
        return self.size * SECTOR_SIZE
    
    @property
    def actual_streaming_size(self):
        """Returns the actual streaming size of the entry in bytes."""
        return self.streaming_size * SECTOR_SIZE
    
    @property
    def type(self):
        """Determines the file type from its extension."""
        if '.' in self.name:
            return self.name.split('.')[-1].upper()
        return "UNKNOWN"
    
    def __str__(self):
        return f"{self.name} (Offset: {self.offset}, Size: {self.size} sectors)"


class IMGArchive:
    """Represents an IMG archive file (V1 or V2), holding its properties and entries."""
    def __init__(self):
        self.file_path = None     # Path to the .img file
        self.dir_path = None      # Path to the .dir file (V1 only)
        self.version = None       # 'V1' or 'V2'
        self.entries = []         # List of IMGEntry objects
        self.modified = False     # Track if the archive has been modified
    
    def get_entry_by_name(self, name):
        """Finds an entry by its name (case-insensitive)."""
        name = name.lower()
        for entry in self.entries:
            if entry.name.lower() == name:
                return entry
        return None
    
    def get_entry_by_index(self, index):
        """Gets an entry by its index in the entries list."""
        if 0 <= index < len(self.entries):
            return self.entries[index]
        return None
    
    def get_file_count(self):
        """Returns the number of entries in the archive."""
        return len(self.entries)
    
    def get_version_string(self):
        """Returns a string representation of the IMG version."""
        if self.version == 'V1':
            return "Version 1 (GTA III & VC)"
        elif self.version == 'V2':
            return "Version 2 (GTA SA)"
        return "Unknown Version"
    
    def get_total_size(self):
        """Returns the total size of all entries in the archive in bytes."""
        total = 0
        for entry in self.entries:
            total += entry.actual_size
        return total
    
    def read_entry_data(self, entry, img_file=None):
        """
        Reads the data for a specific entry from the IMG archive.
        
        Args:
            entry: The IMGEntry object to read data for
            img_file: Optional file handle. If None, the file will be opened and closed within this method.
            
        Returns:
            Bytes data of the entry
        """
        close_file = False
        if img_file is None:
            img_file = open(self.file_path, 'rb')
            close_file = True
        
        try:
            img_file.seek(entry.actual_offset)
            data = img_file.read(entry.actual_size)
            return data
        finally:
            if close_file and img_file:
                img_file.close()
    
    def __str__(self):
        """String representation of the IMG archive."""
        return f"IMG Archive: {Path(self.file_path).name if self.file_path else 'Not loaded'} ({self.get_version_string()}), {len(self.entries)} entries"
