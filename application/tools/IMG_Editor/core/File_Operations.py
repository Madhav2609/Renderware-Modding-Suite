"""
File operations for IMG archives.
This module handles operations like opening, creating, saving, and closing IMG archives.
"""

import os
import struct
from pathlib import Path
import sys
from pathlib import Path as _Path

# Add the application root to sys.path for imports (align with Core.py)
app_root = _Path(__file__).parent.parent.parent.parent
if str(app_root) not in sys.path:
    sys.path.insert(0, str(app_root))

from application.debug_system import get_debug_logger, LogCategory
from .Core import IMGArchive, IMGEntry, SECTOR_SIZE, V2_SIGNATURE, MAX_FILENAME_LENGTH

# Module-level debug logger
debug_logger = get_debug_logger()

class ArchiveManager:
    """Manager class for handling multiple open IMG archives."""
    
    def __init__(self):
        self.open_archives = {}  # Dictionary: file_path -> IMGArchive
        self.active_archive = None  # Currently active archive
        
    def get_archive_count(self):
        """Returns the number of open archives."""
        return len(self.open_archives)
    
    def get_archive_paths(self):
        """Returns list of all open archive paths."""
        return list(self.open_archives.keys())
    
    def get_archive(self, file_path):
        """Get a specific archive by file path."""
        return self.open_archives.get(file_path)
    
    def set_active_archive(self, file_path):
        """Set the active archive."""
        if file_path in self.open_archives:
            self.active_archive = self.open_archives[file_path]
            return True
        return False
    
    def get_active_archive(self):
        """Get the currently active archive."""
        return self.active_archive
    
    def close_archive(self, file_path):
        """Close a specific archive."""
        if file_path in self.open_archives:
            try:
                # Get the archive before removing it
                img_archive = self.open_archives[file_path]
                
                # Clean up the archive object using its cleanup method
                if img_archive:
                    if hasattr(img_archive, 'cleanup'):
                        img_archive.cleanup()
                    else:
                        # Fallback cleanup
                        img_archive.file_path = None
                        img_archive.dir_path = None
                        img_archive.version = None
                        img_archive.entries = []
                        img_archive.modified = False
                
                # Remove from open archives
                del self.open_archives[file_path]
                
                # Update active archive if needed
                if self.active_archive and self.active_archive.file_path == file_path:
                    # Set new active archive if available
                    if self.open_archives:
                        self.active_archive = next(iter(self.open_archives.values()))
                    else:
                        self.active_archive = None
                
                debug_logger.info(LogCategory.FILE_IO, "Successfully closed archive", {"file_path": file_path})
                return True
                
            except Exception as e:
                debug_logger.log_exception(LogCategory.FILE_IO, f"Error closing archive {file_path}", e)
                # Force remove even if cleanup failed
                if file_path in self.open_archives:
                    del self.open_archives[file_path]
                return False
        return False
    
    def close_all_archives(self):
        """Close all open archives."""
        try:
            # Get all archive paths before clearing
            archive_paths = list(self.open_archives.keys())
            
            # Close each archive individually to ensure proper cleanup
            for file_path in archive_paths:
                try:
                    img_archive = self.open_archives[file_path]
                    if img_archive:
                        # Use the archive's cleanup method
                        if hasattr(img_archive, 'cleanup'):
                            img_archive.cleanup()
                        else:
                            # Fallback cleanup
                            img_archive.file_path = None
                            img_archive.dir_path = None
                            img_archive.version = None
                            img_archive.entries = []
                            img_archive.modified = False
                except Exception as e:
                    debug_logger.log_exception(LogCategory.FILE_IO, f"Error cleaning up archive {file_path}", e)
            
            # Clear all references
            self.open_archives.clear()
            self.active_archive = None
            
            debug_logger.info(LogCategory.FILE_IO, "Closed archives", {"count": len(archive_paths)})
            
        except Exception as e:
            debug_logger.log_exception(LogCategory.FILE_IO, "Error in ArchiveManager.close_all_archives", e)
            # Force clear even if there was an error
            self.open_archives.clear()
            self.active_archive = None

class File_Operations:
    """Class containing methods for file operations on IMG archives."""
    
    @staticmethod
    def open_archive(file_path, archive_manager=None):
        """
        Opens an IMG archive and reads its contents.
        
        Args:
            file_path: Path to the IMG file
            archive_manager: Optional ArchiveManager instance for multi-archive support
            
        Returns:
            IMGArchive object representing the opened archive
        """
        # Check if file is already open in archive manager
        if archive_manager and file_path in archive_manager.open_archives:
            return archive_manager.open_archives[file_path]
        
        img_archive = IMGArchive()
        img_archive.file_path = file_path
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"IMG file not found: {file_path}")
        
        # Try to determine version and read entries
        with open(file_path, 'rb') as f:
            # Check if it's V2 by looking for the 'VER2' signature
            header = f.read(4)
            if header == V2_SIGNATURE:
                # Version 2 (GTA SA)
                img_archive.version = 'V2'
                
                # Read number of entries
                entry_count = struct.unpack('<I', f.read(4))[0]
                
                # Read entries
                for _ in range(entry_count):
                    entry = IMGEntry()
                    entry.offset = struct.unpack('<I', f.read(4))[0]
                    entry.streaming_size = struct.unpack('<H', f.read(2))[0]
                    entry.size = struct.unpack('<H', f.read(2))[0]
                    
                    # If size is 0, use streaming size
                    if entry.size == 0:
                        entry.size = entry.streaming_size
                    
                    # Read filename (null-terminated, 24 bytes max)
                    name_bytes = f.read(MAX_FILENAME_LENGTH)
                    null_pos = name_bytes.find(b'\0')
                    if null_pos != -1:
                        name_bytes = name_bytes[:null_pos]
                    
                    entry.name = name_bytes.decode('ascii', errors='replace')
                    img_archive.entries.append(entry)
            else:
                # Assume Version 1 (GTA III & VC) - need to read .dir file
                img_archive.version = 'V1'
                dir_path = file_path.replace('.img', '.dir')
                img_archive.dir_path = dir_path
                
                if not os.path.exists(dir_path):
                    raise FileNotFoundError(f"DIR file not found: {dir_path}")
                
                # Read directory entries from .dir file
                with open(dir_path, 'rb') as dir_file:
                    while True:
                        entry_data = dir_file.read(32)  # Each entry is 32 bytes
                        if not entry_data or len(entry_data) < 32:
                            break
                            
                        entry = IMGEntry()
                        entry.offset = struct.unpack('<I', entry_data[:4])[0]
                        entry.size = struct.unpack('<I', entry_data[4:8])[0]
                        
                        # Read filename (null-terminated, 24 bytes max)
                        name_bytes = entry_data[8:]
                        null_pos = name_bytes.find(b'\0')
                        if null_pos != -1:
                            name_bytes = name_bytes[:null_pos]
                        
                        entry.name = name_bytes.decode('ascii', errors='replace')
                        img_archive.entries.append(entry)
        
        # Add to archive manager if provided
        if archive_manager:
            archive_manager.open_archives[file_path] = img_archive
            if not archive_manager.active_archive:
                archive_manager.active_archive = img_archive
        
        return img_archive
    
    @staticmethod
    def open_multiple_archives(file_paths, archive_manager):
        """
        Opens multiple IMG archives using the archive manager.
        
        Args:
            file_paths: List of paths to IMG files
            archive_manager: ArchiveManager instance
            
        Returns:
            Tuple (success_count, failed_files, error_messages)
        """
        success_count = 0
        failed_files = []
        error_messages = []
        
        for file_path in file_paths:
            try:
                File_Operations.open_archive(file_path, archive_manager)
                success_count += 1
            except Exception as e:
                failed_files.append(file_path)
                error_messages.append(f"{Path(file_path).name}: {str(e)}")
        
        return success_count, failed_files, error_messages
    
      

    @staticmethod
    def create_new_archive(file_path, version='V2'):
        """
        Creates a new empty IMG archive.
        
        Args:
            file_path: Path for the new IMG file
            version: Version of the IMG file to create ('V1' or 'V2')
            
        Returns:
            IMGArchive object representing the new archive
        """
        img_archive = IMGArchive()
        img_archive.file_path = file_path
        img_archive.version = version
        
        if version == 'V1':
            img_archive.dir_path = file_path.replace('.img', '.dir')
            
            # Create empty .img and .dir files
            with open(file_path, 'wb') as f:
                pass  # Just create an empty file
                
            with open(img_archive.dir_path, 'wb') as f:
                pass  # Just create an empty file
        else:
            # Create empty V2 .img file with header
            with open(file_path, 'wb') as f:
                f.write(V2_SIGNATURE)  # 'VER2'
                f.write(struct.pack('<I', 0))  # 0 entries
        
        img_archive.modified = True
        return img_archive
    
    
    @staticmethod
    def close_archive(img_archive, archive_manager=None):
        """
        Closes an IMG archive, cleaning up any resources.
        
        Args:
            img_archive: IMGArchive object to close
            archive_manager: Optional ArchiveManager instance
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove from archive manager if provided
            if archive_manager and img_archive.file_path:
                archive_manager.close_archive(img_archive.file_path)
            
            # Use the archive's cleanup method
            if hasattr(img_archive, 'cleanup'):
                img_archive.cleanup()
            else:
                # Fallback cleanup if cleanup method doesn't exist
                img_archive.file_path = None
                img_archive.dir_path = None
                img_archive.version = None
                img_archive.entries = []
                img_archive.modified = False
            
            return True
            
        except Exception as e:
            debug_logger.log_exception(LogCategory.FILE_IO, "Error in close_archive", e)
            return False
