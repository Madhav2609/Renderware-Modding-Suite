"""
Import and export functionality for IMG archives.
This module handles importing files into and exporting entries from IMG archives.
"""

import os
import struct
import math
from pathlib import Path
from .Core import IMGArchive, IMGEntry, SECTOR_SIZE, MAX_FILENAME_LENGTH

class Import_Export:
    """Class containing methods for importing and exporting files to/from IMG archives."""
    
    @staticmethod
    def import_file(img_archive, file_path, entry_name=None):
        """
        Imports a file into an IMG archive.
        
        Args:
            img_archive: IMGArchive object to import into
            file_path: Path to the file to import
            entry_name: Optional name to use for the entry. If None, uses the file's basename.
            
        Returns:
            IMGEntry object representing the imported file
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine entry name
        if not entry_name:
            entry_name = os.path.basename(file_path)
            
        # Ensure name length is valid
        if len(entry_name.encode('ascii', errors='replace')) >= MAX_FILENAME_LENGTH:
            entry_name = entry_name[:MAX_FILENAME_LENGTH-1]  # Leave room for null terminator
        
        # Read file data
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Calculate size in sectors (rounded up)
        size_in_sectors = math.ceil(len(file_data) / SECTOR_SIZE)
        
        # Create new entry
        entry = IMGEntry()
        entry.name = entry_name
        entry.size = size_in_sectors
        entry.streaming_size = size_in_sectors if img_archive.version == 'V2' else 0
        entry.data = file_data
        
        # For now, we're just appending to the entries list
        # In a real implementation, we'd need to update offsets and physically write the data
        if img_archive.entries:
            last_entry = img_archive.entries[-1]
            entry.offset = last_entry.offset + last_entry.size
        else:
            # First entry starts after the directory
            if img_archive.version == 'V2':
                # V2: Directory size = 8 + (32 * number_of_entries)
                entry.offset = math.ceil((8 + 32) / SECTOR_SIZE)  # Account for header + 1 entry
            else:
                # V1: Directory is in separate file, so start at the beginning
                entry.offset = 0
        
        img_archive.entries.append(entry)
        img_archive.modified = True
        
        return entry
    
    @staticmethod
    def import_folder(img_archive, folder_path, recursive=False, filter_extensions=None):
        """
        Imports all files from a folder into an IMG archive.
        
        Args:
            img_archive: IMGArchive object to import into
            folder_path: Path to the folder to import
            recursive: If True, also imports from subdirectories
            filter_extensions: Optional list of file extensions to import
            
        Returns:
            List of IMGEntry objects representing the imported files
        """
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            raise NotADirectoryError(f"Folder not found: {folder_path}")
        
        imported_entries = []
        
        # Walk through directory
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                # Check extension if filter is provided
                if filter_extensions:
                    ext = os.path.splitext(file)[1].lower().lstrip('.')
                    if ext not in [e.lower().lstrip('.') for e in filter_extensions]:
                        continue
                
                file_path = os.path.join(root, file)
                
                # For entries from subdirectories, maintain relative path if recursive is True
                if recursive and root != folder_path:
                    rel_path = os.path.relpath(root, folder_path)
                    entry_name = os.path.join(rel_path, file).replace('\\', '/')
                else:
                    entry_name = file
                
                try:
                    entry = Import_Export.import_file(img_archive, file_path, entry_name)
                    imported_entries.append(entry)
                except Exception as e:
                    print(f"Error importing {file_path}: {str(e)}")
            
            # If not recursive, don't process subdirectories
            if not recursive:
                break
        
        return imported_entries
    
    @staticmethod
    def export_entry(img_archive, entry, output_path=None, output_dir=None):
        """
        Exports an entry from an IMG archive to a file.
        
        Args:
            img_archive: IMGArchive object to export from
            entry: IMGEntry object to export
            output_path: Optional specific path for the output file
            output_dir: Optional directory to export to (uses entry.name as filename)
            
        Returns:
            Path to the exported file
        """
        if not output_path and not output_dir:
            raise ValueError("Either output_path or output_dir must be provided")
        
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, entry.name)
        
        # Read entry data if not already loaded
        if not entry.data:
            with open(img_archive.file_path, 'rb') as f:
                f.seek(entry.actual_offset)
                entry.data = f.read(entry.actual_size)
        
        # Write data to output file
        with open(output_path, 'wb') as f:
            f.write(entry.data)
        
        return output_path
    
    @staticmethod
    def export_all(img_archive, output_dir, filter_type=None):
        """
        Exports all entries from an IMG archive.
        
        Args:
            img_archive: IMGArchive object to export from
            output_dir: Directory to export to
            filter_type: Optional file type filter
            
        Returns:
            List of paths to the exported files
        """
        os.makedirs(output_dir, exist_ok=True)
        
        exported_files = []
        
        for entry in img_archive.entries:
            # Apply type filter if provided
            if filter_type and entry.type != filter_type:
                continue
            
            try:
                output_path = Import_Export.export_entry(img_archive, entry, output_dir=output_dir)
                exported_files.append(output_path)
            except Exception as e:
                print(f"Error exporting {entry.name}: {str(e)}")
        
        return exported_files
    
    @staticmethod
    def export_by_type(img_archive, output_dir, types):
        """
        Exports entries of specific types from an IMG archive.
        
        Args:
            img_archive: IMGArchive object to export from
            output_dir: Directory to export to
            types: List of file types to export
            
        Returns:
            Dictionary mapping file types to lists of exported file paths
        """
        os.makedirs(output_dir, exist_ok=True)
        
        exported_files = {t: [] for t in types}
        
        for entry in img_archive.entries:
            # Check if entry type is in requested types
            if entry.type in types:
                try:
                    # Create type-specific subdirectory
                    type_dir = os.path.join(output_dir, entry.type)
                    os.makedirs(type_dir, exist_ok=True)
                    
                    output_path = Import_Export.export_entry(img_archive, entry, output_dir=type_dir)
                    exported_files[entry.type].append(output_path)
                except Exception as e:
                    print(f"Error exporting {entry.name}: {str(e)}")
        
        return exported_files
