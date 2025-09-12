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

from application.common.rw_versions import RWVersionManager
from application.debug_system import get_debug_logger, LogCategory

# Module-level debug logger
debug_logger = get_debug_logger()

# Initialize RW Version Manager
rw_version_manager = RWVersionManager()

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
        self.is_new_entry = False # Flag to track if this is a new/modified entry
    
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
            # Use the enhanced detection from rw_version_manager
            file_format, version_description, version_value = rw_version_manager.detect_file_format_version(data, self.name)
            
            if file_format == "COL":
                # COL files don't have RW versions in the traditional sense
                self._rw_version = None
                self._rw_version_name = version_description
                self._format_info = (file_format, version_description)
            elif version_value > 0 and rw_version_manager.is_valid_rw_version(version_value):
                self._rw_version = version_value
                # Use the enhanced display string with platform information
                self._rw_version_name = rw_version_manager.get_version_display_string(version_value)
                self._format_info = (file_format, self._rw_version_name)
            else:
                # Fall back to original method for other file types
                if len(data) >= 12:
                    # Check if it's a RenderWare file by looking at the version field
                    version_data = data[8:12]
                    
                    if len(version_data) >= 4:
                        import struct
                        try:
                            library_id = struct.unpack('<I', version_data)[0]
                            # Extract actual RW version using DFF function
                            rw_version = rw_version_manager.get_rw_version(library_id)
                            
                            if rw_version_manager.is_valid_rw_version(rw_version):
                                self._rw_version = rw_version
                                # Use the enhanced display string with platform information
                                self._rw_version_name = rw_version_manager.get_version_display_string(rw_version)
                                
                                # Get format-specific information
                                ext = self.name.lower().split('.')[-1] if '.' in self.name else ""
                                if ext in ['dff', 'txd']:
                                    self._format_info = (ext.upper(), self._rw_version_name)
                                else:
                                    self._format_info = ("RW", self._rw_version_name)
                            else:
                                # Not a valid RenderWare file
                                self._rw_version = None
                                self._rw_version_name = "Not RenderWare"
                                self._format_info = (self.type, "Not RenderWare")
                        except (struct.error, Exception):
                            self._rw_version = None
                            self._rw_version_name = "Invalid"
                            self._format_info = (self.type, "Invalid")
                    else:
                        self._rw_version = None
                        self._rw_version_name = "Invalid"
                        self._format_info = (self.type, "Invalid")
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
        return self._rw_version is not None and rw_version_manager.is_valid_rw_version(self._rw_version)
    
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
        self.deleted_entries = [] # Track deleted entries for modification summary
    
    def __del__(self):
        """Destructor to ensure proper cleanup when the object is destroyed"""
        try:
            # Clear all references to free memory
            self.file_path = None
            self.dir_path = None
            self.version = None
            self.entries = []
            self.modified = False
            self.deleted_entries = []
        except Exception as e:
            # Ignore errors during cleanup
            pass
    
    def cleanup(self):
        """Explicit cleanup method to free resources"""
        try:
            # Clear all entries and their data
            for entry in self.entries:
                if hasattr(entry, 'data') and entry.data is not None:
                    entry.data = None
            
            # Clear all references
            self.entries = []
            self.deleted_entries = []
            self.file_path = None
            self.dir_path = None
            self.version = None
            self.modified = False
            
        except Exception as e:
            debug_logger.log_exception(LogCategory.FILE_IO, "Error during IMGArchive cleanup", e)
    
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
            debug_logger.log_exception(LogCategory.FILE_IO, "Error analyzing archive", e)
    
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
    
    def get_unique_file_types(self):
        """
        Get all unique file types present in the archive.
        
        Returns:
            List of unique file type strings
        """
        types = set()
        for entry in self.entries:
            if entry.type:
                types.add(entry.type)
        return sorted(list(types))
    
    def get_unique_rw_versions(self):
        """
        Get all unique RenderWare versions present in the archive.
        
        Returns:
            List of tuples (version_value, version_name) for unique versions
        """
        versions = {}
        for entry in self.entries:
            # Include all version names, including non-RenderWare ones
            if entry.rw_version_name:
                # Use rw_version as key, fallback to hash of name if None
                key = entry.rw_version if entry.rw_version is not None else hash(entry.rw_version_name)
                versions[key] = entry.rw_version_name
        return [(version, name) for version, name in sorted(versions.items(), key=lambda x: x[1])]
    
    def get_unique_formats(self):
        """
        Get all unique format types present in the archive.
        
        Returns:
            List of unique format type strings (e.g., 'DFF', 'TXD', 'COL')
        """
        formats = set()
        for entry in self.entries:
            if entry.format_info and len(entry.format_info) > 0:
                format_type = entry.format_info[0]
                if format_type:
                    formats.add(format_type)
        return sorted(list(formats))

    def filter_entries(self, filter_text=None, filter_type=None):
        """
        Filters entries in an IMG archive based on name and/or type.
        
        Args:
            filter_text: Text to filter names by
            filter_type: Type to filter by
            
        Returns:
            List of IMGEntry objects that match the filter
        """
        result = self.entries.copy()
        
        if filter_text:
            filter_text = filter_text.lower()
            result = [e for e in result if filter_text in e.name.lower()]
            
        if filter_type and filter_type.upper() != 'ALL':
            result = [e for e in result if e.type == filter_type.upper()]
            
        return result
    
    
    def delete_entries(self, entries):
        """
        Removes multiple entries from an IMG archive in memory only.
        The actual IMG file is not modified until save/rebuild operation.
        
        Args:
            entries: List of IMGEntry objects to remove
            
        Returns:
            Tuple of (success_count, failed_entries)
        """
        if not entries:
            return 0, []
        
        success_count = 0
        failed_entries = []
        
        for entry in entries:
            if entry in self.entries:
                # Only track as deleted if it's an existing entry (not a new entry)
                if not (hasattr(entry, 'is_new_entry') and entry.is_new_entry):
                    # This was an original entry from the file, so track it as deleted
                    self.deleted_entries.append(entry)
                    debug_logger.debug(LogCategory.TOOL, "Tracking deleted original entry", {"entry": entry.name})
                else:
                    # This was a new entry that was never saved, so just remove it
                    debug_logger.debug(LogCategory.TOOL, "Removing new entry (not saved)", {"entry": entry.name})
                
                self.entries.remove(entry)
                success_count += 1
            else:
                failed_entries.append(entry)
        
        if success_count > 0:
            self.modified = True
        
        return success_count, failed_entries
    
    def has_entry(self, entry_or_name):
        """
        Check if an entry exists in the archive.
        
        Args:
            entry_or_name: IMGEntry object or entry name to check
            
        Returns:
            True if entry exists, False otherwise
        """
        if isinstance(entry_or_name, str):
            return self.get_entry_by_name(entry_or_name) is not None
        else:
            return entry_or_name in self.entries
    
    def get_deleted_entries_count(self):
        """
        Get count of how many entries have been deleted from the original file.
        
        Returns:
            Information about deletions and modifications
        """
        return {
            "modified": self.modified, 
            "has_deletions": len(self.deleted_entries) > 0,
            "deleted_count": len(self.deleted_entries),
            "deleted_entries": [entry.name for entry in self.deleted_entries]
        }
    
    def get_entry_names(self):
        """
        Get list of all entry names in the archive.
        
        Returns:
            List of entry names
        """
        return [entry.name for entry in self.entries]
    
    def add_entry(self, filename, data):
        """
        Add new entry to IMG file - memory only operation.
        The actual IMG file will not be modified until save/rebuild.
        
        Args:
            filename: Name for the new entry
            data: Raw bytes data for the entry
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import math
            
            # Validate inputs
            if not filename or not data:
                debug_logger.error(LogCategory.FILE_IO, "Invalid filename or data provided for add_entry")
                return False
            
            # Ensure filename length is valid
            if len(filename.encode('ascii', errors='replace')) >= MAX_FILENAME_LENGTH:
                filename = filename[:MAX_FILENAME_LENGTH-1]  # Leave room for null terminator
                debug_logger.debug(LogCategory.TOOL, "Filename truncated", {"new_filename": filename})
            
            # Check for duplicate entries (replace if exists)
            existing_entry = None
            for i, entry in enumerate(self.entries):
                if entry.name.lower() == filename.lower():
                    existing_entry = entry
                    debug_logger.debug(LogCategory.TOOL, "Replacing existing entry", {"index": i, "filename": filename})
                    break
            
            if existing_entry:
                # Replace existing entry data
                debug_logger.debug(LogCategory.TOOL, "Updating existing entry data")
                existing_entry.data = data
                existing_entry.size = math.ceil(len(data) / SECTOR_SIZE)
                existing_entry.streaming_size = existing_entry.size if self.version == 'V2' else 0
                
                # Detect file type and RW version from data
                existing_entry.detect_rw_version(data)
                debug_logger.debug(LogCategory.TOOL, "Existing entry updated", {"size_sectors": existing_entry.size, "data_length": len(data)})
                
                # Mark entry as new/modified for future save operations
                existing_entry.is_new_entry = True
            else:
                # Create brand new entry
                debug_logger.debug(LogCategory.TOOL, "Creating new IMGEntry")
                new_entry = IMGEntry()
                new_entry.name = filename
                new_entry.data = data
                new_entry.size = math.ceil(len(data) / SECTOR_SIZE)
                new_entry.streaming_size = new_entry.size if self.version == 'V2' else 0
                
                # Calculate proper offset for new entry
                new_entry.offset = self.calculate_next_offset()
                debug_logger.debug(LogCategory.TOOL, "Calculated offset for new entry", {"offset_sectors": new_entry.offset, "offset_hex": f"0x{new_entry.offset:08X}"})
                
                # Detect file type and RW version from data
                new_entry.detect_rw_version(data)
                
                # Mark as new entry for future save operations
                new_entry.is_new_entry = True
                
                # Add to entries list
                self.entries.append(new_entry)
                debug_logger.info(LogCategory.TOOL, "Entry added successfully", {"filename": filename})
                debug_logger.debug(LogCategory.TOOL, "Total entries updated", {"total_entries": len(self.entries)})
            
            # Mark archive as modified
            self.modified = True
            return True
            
        except Exception as e:
            debug_logger.log_exception(LogCategory.FILE_IO, f"Failed to add entry {filename}", e)
            return False
    
    def calculate_next_offset(self):
        """
        Calculate the next available offset for a new entry.
        This is used for in-memory planning; actual offsets will be recalculated during save/rebuild.
        
        Returns:
            Next available offset in sectors
        """
        try:
            if not self.entries:
                # First entry
                if self.version == 'V1':
                    return 0  # Version 1 starts at beginning
                else:
                    # Version 2: Reserve space for directory (will be recalculated during save)
                    return 1  # Placeholder offset
            
            # Find the entry that ends the latest
            max_end = 0
            for entry in self.entries:
                if hasattr(entry, 'is_new_entry') and entry.is_new_entry:
                    # For new entries, use a calculated end position
                    entry_end = entry.offset + entry.size
                else:
                    # For existing entries, use their current position
                    entry_end = entry.offset + entry.size
                
                if entry_end > max_end:
                    max_end = entry_end
            
            # Return next sector boundary
            return max_end  # Already in sectors
            
        except Exception as e:
            debug_logger.log_exception(LogCategory.TOOL, "Failed to calculate next offset", e)
            return 0
    
    def has_new_or_modified_entries(self):
        """
        Check if the archive has any new, modified, or deleted entries that need to be saved.
        
        Returns:
            True if there are unsaved changes, False otherwise
        """
        if not self.modified:
            return False
        
        # Check for new entries
        for entry in self.entries:
            if hasattr(entry, 'is_new_entry') and entry.is_new_entry:
                return True
        
        # Check for deleted entries
        if len(self.deleted_entries) > 0:
            return True
        
        return False
    
    def get_new_entries_count(self):
        """
        Get the count of new entries that haven't been saved to file yet.
        
        Returns:
            Number of new entries
        """
        count = 0
        for entry in self.entries:
            if hasattr(entry, 'is_new_entry') and entry.is_new_entry:
                count += 1
        return count
    
    def get_deleted_entries_count_only(self):
        """
        Get just the count of deleted entries.
        
        Returns:
            Number of deleted entries
        """
        return len(self.deleted_entries)
    
    def get_deleted_entry_names(self):
        """
        Get list of names of deleted entries.
        
        Returns:
            List of deleted entry names
        """
        return [entry.name for entry in self.deleted_entries]
    
    def clear_modification_tracking(self):
        """
        Clear modification tracking. 
        This should be called after a successful save/rebuild operation.
        """
        self.modified = False
        self.deleted_entries.clear()
        
        # Clear new entry flags
        for entry in self.entries:
            if hasattr(entry, 'is_new_entry'):
                entry.is_new_entry = False
    
    def restore_deleted_entry(self, entry_name):
        """
        Restore a deleted entry back to the archive.
        
        Args:
            entry_name: Name of the entry to restore
            
        Returns:
            True if restored successfully, False if not found
        """
        for i, deleted_entry in enumerate(self.deleted_entries):
            if deleted_entry.name.lower() == entry_name.lower():
                # Move entry back to the main entries list
                restored_entry = self.deleted_entries.pop(i)
                self.entries.append(restored_entry)
                debug_logger.info(LogCategory.TOOL, "Restored deleted entry", {"entry": entry_name})
                return True
        
        debug_logger.warning(LogCategory.TOOL, "Could not find deleted entry to restore", {"entry": entry_name})
        return False
    
    def restore_all_deleted_entries(self):
        """
        Restore all deleted entries back to the archive.
        
        Returns:
            Number of entries restored
        """
        count = len(self.deleted_entries)
        self.entries.extend(self.deleted_entries)
        self.deleted_entries.clear()
        debug_logger.info(LogCategory.TOOL, "Restored deleted entries", {"count": count})
        return count
    
    def get_modification_summary(self):
        """
        Get a summary of modifications made to the archive.
        
        Returns:
            Dictionary with modification information
        """
        new_entries = self.get_new_entries_count()
        deleted_entries = len(self.deleted_entries)
        
        return {
            'is_modified': self.modified,
            'has_new_entries': new_entries > 0,
            'has_deleted_entries': deleted_entries > 0,
            'new_entries_count': new_entries,
            'deleted_entries_count': deleted_entries,
            'total_entries': len(self.entries),
            'original_entries_count': len(self.entries) + deleted_entries,  # Current + deleted
            'needs_save': self.has_new_or_modified_entries(),
            'deleted_entry_names': [entry.name for entry in self.deleted_entries]
        }
    
    def __str__(self):
        """String representation of the IMG archive."""
        return f"IMG Archive: {Path(self.file_path).name if self.file_path else 'Not loaded'} ({self.get_version_string()}), {len(self.entries)} entries"
