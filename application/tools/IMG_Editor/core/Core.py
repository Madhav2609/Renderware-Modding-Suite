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
import sys
from pathlib import Path

# Add the application root to sys.path for imports
app_root = Path(__file__).parent.parent.parent.parent
if str(app_root) not in sys.path:
    sys.path.insert(0, str(app_root))

from application.common.rw_versions import parse_rw_version, get_model_format_version, is_valid_rw_version, detect_rw_file_format

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
        self._rw_version = None  # Cached RenderWare version
        self._rw_version_name = None  # Cached RW version name
        self._format_info = None # Cached format information
    
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
    
    @property
    def rw_version(self):
        """Get the RenderWare version of this entry if available."""
        return self._rw_version
    
    @property
    def rw_version_name(self):
        """Get the human-readable RenderWare version name."""
        return self._rw_version_name
    
    @property
    def format_info(self):
        """Get format information tuple (format, version_name)."""
        return self._format_info
    
    def detect_rw_version(self, data: bytes):
        """
        Detect RenderWare version from entry data.
        
        Args:
            data: The raw data of the entry
        """
        if len(data) < 4:
            self._rw_version = None
            self._rw_version_name = "Unknown"
            self._format_info = (self.type, "Unknown")
            return
        
        try:
            # Use the enhanced detection from rw_versions
            file_format, version_description, version_value = detect_rw_file_format(data, self.name)
            
            if file_format == "COL":
                # COL files don't have RW versions in the traditional sense
                self._rw_version = None
                self._rw_version_name = version_description
                self._format_info = (file_format, version_description)
            elif version_value > 0 and is_valid_rw_version(version_value):
                self._rw_version = version_value
                self._rw_version_name = version_description
                self._format_info = (file_format, version_description)
            else:
                # Fall back to original method for other file types
                if len(data) >= 12:
                    # Check if it's a RenderWare file by looking at the version field
                    version_data = data[8:12]
                    version_value, version_name = parse_rw_version(version_data)
                    
                    if is_valid_rw_version(version_value):
                        self._rw_version = version_value
                        self._rw_version_name = version_name
                        
                        # Get format-specific information
                        format_type, format_version = get_model_format_version(self.name, data)
                        self._format_info = (format_type, format_version)
                    else:
                        # Not a valid RenderWare file
                        self._rw_version = None
                        self._rw_version_name = "Not RenderWare"
                        self._format_info = (self.type, "Non-RW")
                else:
                    self._rw_version = None
                    self._rw_version_name = "Unknown"
                    self._format_info = (self.type, "Unknown")
                
        except Exception as e:
            self._rw_version = None
            self._rw_version_name = f"Error: {str(e)}"
            self._format_info = (self.type, "Error")
    
    def is_renderware_file(self) -> bool:
        """Check if this entry is a RenderWare file."""
        # COL files are RenderWare-related but don't have traditional RW versions
        if self._format_info and self._format_info[0] == "COL":
            return "COL" in self._rw_version_name if self._rw_version_name else False
        return self._rw_version is not None and is_valid_rw_version(self._rw_version)
    
    def get_detailed_info(self) -> str:
        """Get detailed information string about this entry."""
        info = f"{self.name} ({self.type})"
        if self._rw_version_name:
            info += f" - {self._rw_version_name}"
        if self._format_info and self._format_info[1] != "Unknown":
            info += f" [{self._format_info[0]}]"
        return info
    
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
    
    def analyze_entry_rw_version(self, entry):
        """
        Analyze and cache RenderWare version information for a specific entry.
        
        Args:
            entry: The IMGEntry object to analyze
        """
        try:
            # Read just the header (first 64 bytes should be enough for version detection)
            with open(self.file_path, 'rb') as img_file:
                img_file.seek(entry.actual_offset)
                header_data = img_file.read(min(64, entry.actual_size))
                entry.detect_rw_version(header_data)
        except Exception as e:
            entry._rw_version = None
            entry._rw_version_name = f"Error reading: {str(e)}"
            entry._format_info = (entry.type, "Error")
    
    def analyze_all_entries_rw_versions(self):
        """
        Analyze RenderWare versions for all entries in the archive.
        This is useful for getting an overview of the archive contents.
        """
        if not self.file_path or not os.path.exists(self.file_path):
            return
        
        try:
            with open(self.file_path, 'rb') as img_file:
                for entry in self.entries:
                    try:
                        img_file.seek(entry.actual_offset)
                        header_data = img_file.read(min(64, entry.actual_size))
                        entry.detect_rw_version(header_data)
                    except Exception as e:
                        entry._rw_version = None
                        entry._rw_version_name = f"Error: {str(e)}"
                        entry._format_info = (entry.type, "Error")
        except Exception as e:
            print(f"Error analyzing archive: {e}")
    
    def get_rw_version_summary(self):
        """
        Get a summary of RenderWare versions found in the archive.
        
        Returns:
            Dict with version statistics
        """
        version_counts = {}
        format_counts = {}
        rw_files = 0
        total_files = len(self.entries)
        
        for entry in self.entries:
            if entry.rw_version_name:
                version_name = entry.rw_version_name
                version_counts[version_name] = version_counts.get(version_name, 0) + 1
                
                if entry.is_renderware_file():
                    rw_files += 1
            
            if entry.format_info:
                format_type = entry.format_info[0]
                format_counts[format_type] = format_counts.get(format_type, 0) + 1
        
        return {
            'total_files': total_files,
            'renderware_files': rw_files,
            'non_renderware_files': total_files - rw_files,
            'version_breakdown': version_counts,
            'format_breakdown': format_counts
        }
    
    def get_entries_by_rw_version(self, version_value):
        """
        Get all entries that match a specific RenderWare version.
        
        Args:
            version_value: The RenderWare version value to filter by
            
        Returns:
            List of IMGEntry objects
        """
        return [entry for entry in self.entries 
                if entry.rw_version == version_value]
    
    def get_entries_by_format(self, format_type):
        """
        Get all entries that match a specific format type.
        
        Args:
            format_type: The format type to filter by (e.g., 'DFF', 'TXD')
            
        Returns:
            List of IMGEntry objects
        """
        format_type = format_type.upper()
        return [entry for entry in self.entries 
                if entry.type == format_type]
    
    def __str__(self):
        """String representation of the IMG archive."""
        return f"IMG Archive: {Path(self.file_path).name if self.file_path else 'Not loaded'} ({self.get_version_string()}), {len(self.entries)} entries"
