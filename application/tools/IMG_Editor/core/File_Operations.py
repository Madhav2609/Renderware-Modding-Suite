"""
File operations for IMG archives.
This module handles operations like opening, creating, saving, and closing IMG archives.
"""

import os
import struct
from pathlib import Path
from .Core import IMGArchive, IMGEntry, SECTOR_SIZE, V2_SIGNATURE, MAX_FILENAME_LENGTH

class File_Operations:
    """Class containing methods for file operations on IMG archives."""
    
    @staticmethod
    def open_archive(file_path):
        """
        Opens an IMG archive and reads its contents.
        
        Args:
            file_path: Path to the IMG file
            
        Returns:
            IMGArchive object representing the opened archive
        """
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
        
        return img_archive
    
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
    def save_archive(img_archive, output_path=None):
        """
        Saves an IMG archive to disk.
        
        Args:
            img_archive: IMGArchive object to save
            output_path: Optional path to save to. If None, uses the archive's file_path.
            
        Returns:
            True if successful, False otherwise
        """
        if not output_path:
            output_path = img_archive.file_path
            
        if img_archive.version == 'V1':
            # Save V1 format (separate .dir and .img files)
            dir_path = output_path.replace('.img', '.dir')
            
            # Write .dir file
            with open(dir_path, 'wb') as dir_file:
                for entry in img_archive.entries:
                    dir_file.write(struct.pack('<I', entry.offset))  # Offset
                    dir_file.write(struct.pack('<I', entry.size))    # Size
                    
                    # Ensure name is no longer than MAX_FILENAME_LENGTH-1 bytes (leaving room for null terminator)
                    name_bytes = entry.name.encode('ascii', errors='replace')
                    if len(name_bytes) >= MAX_FILENAME_LENGTH:
                        name_bytes = name_bytes[:MAX_FILENAME_LENGTH-1]
                    
                    # Pad with nulls to make 24 bytes
                    name_bytes = name_bytes + b'\0' * (MAX_FILENAME_LENGTH - len(name_bytes))
                    dir_file.write(name_bytes)
            
            # For V1, we're only writing the directory, the .img file needs to be written separately
            # with the actual file data
        else:
            # Save V2 format (combined directory and data)
            with open(output_path, 'wb') as img_file:
                # Write header
                img_file.write(V2_SIGNATURE)  # 'VER2'
                img_file.write(struct.pack('<I', len(img_archive.entries)))  # Number of entries
                
                # Write directory entries
                for entry in img_archive.entries:
                    img_file.write(struct.pack('<I', entry.offset))  # Offset
                    img_file.write(struct.pack('<H', entry.streaming_size))  # Streaming size
                    img_file.write(struct.pack('<H', entry.size))  # Size in archive
                    
                    # Ensure name is no longer than MAX_FILENAME_LENGTH-1 bytes (leaving room for null terminator)
                    name_bytes = entry.name.encode('ascii', errors='replace')
                    if len(name_bytes) >= MAX_FILENAME_LENGTH:
                        name_bytes = name_bytes[:MAX_FILENAME_LENGTH-1]
                    
                    # Pad with nulls to make 24 bytes
                    name_bytes = name_bytes + b'\0' * (MAX_FILENAME_LENGTH - len(name_bytes))
                    img_file.write(name_bytes)
                
                # For V2, we would write the actual file data here after the directory
                # This would be done in a separate function when building a complete archive
        
        img_archive.modified = False
        return True
    
    @staticmethod
    def close_archive(img_archive):
        """
        Closes an IMG archive, cleaning up any resources.
        
        Args:
            img_archive: IMGArchive object to close
            
        Returns:
            True if successful, False otherwise
        """
        # Reset the archive object
        img_archive.file_path = None
        img_archive.dir_path = None
        img_archive.version = None
        img_archive.entries = []
        img_archive.modified = False
        
        return True
