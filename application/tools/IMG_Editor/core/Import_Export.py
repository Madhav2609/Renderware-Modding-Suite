"""
Import and export functionality for IMG archives.
This module handles importing files into and exporting entries from IMG archives.
"""

import os
import struct
import math
from pathlib import Path
from .Core import IMGArchive, IMGEntry, SECTOR_SIZE, MAX_FILENAME_LENGTH
from application.debug_system import get_debug_logger, LogCategory

# Module-level logger
debug_logger = get_debug_logger()

class Import_Export:
    """Class containing methods for importing and exporting files to/from IMG archives."""
    
    
    @staticmethod
    def import_file(img_archive, file_path, entry_name=None):
        """
        Imports a file into an IMG archive (memory only operation).
        The actual IMG file will not be modified until save or rebuild.
        
        Args:
            img_archive: IMGArchive object to import into
            file_path: Path to the file to import
            entry_name: Optional name to use for the entry. If None, uses the file's basename.
            
        Returns:
            IMGEntry object representing the imported file, or None if failed
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Determine entry name
            if not entry_name:
                entry_name = os.path.basename(file_path)
            
            debug_logger.debug(LogCategory.FILE_IO, "Importing file", {"file_path": file_path, "entry_name": entry_name})
            
            # Read file data
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            debug_logger.debug(LogCategory.FILE_IO, "Read file bytes", {"file_path": file_path, "bytes": len(file_data)})
            
            # Use the add_entry method from IMGArchive
            success = img_archive.add_entry(entry_name, file_data)
            
            if success:
                # Find and return the newly added/updated entry
                entry = img_archive.get_entry_by_name(entry_name)
                if entry:
                    debug_logger.info(LogCategory.TOOL, "Successfully imported entry", {"entry_name": entry_name})
                    return entry
                else:
                    debug_logger.error(LogCategory.FILE_IO, "Entry added but could not be retrieved", {"entry_name": entry_name})
                    return None
            else:
                debug_logger.error(LogCategory.FILE_IO, "Failed to add entry to archive", {"entry_name": entry_name})
                return None
                
        except Exception as e:
            debug_logger.log_exception(LogCategory.FILE_IO, f"Failed to import file {file_path}", e)
            return None




    @staticmethod
    def import_via_ide(img_archive, ide_file_path, models_directory=None):
        """
        Import DFF models and TXD textures from an IDE file into an IMG archive.
        
        This function parses IDE files to extract model and texture references from:
        - objs sections: ID, ModelName, TextureName, ObjectCount, DrawDist, [DrawDist2, ...], Flags
        - tobj sections: ID, ModelName, TextureName, ObjectCount, DrawDist, [DrawDist2, ...], Flags, TimeOn, TimeOff
        
        Args:
            img_archive: IMGArchive object to import into
            ide_file_path: Path to the IDE file to parse
            models_directory: Directory containing the DFF and TXD files (if None, prompts user)
            
        Returns:
            Tuple of (imported_entries, failed_files, parsed_info) where:
            - imported_entries: List of successfully imported IMGEntry objects
            - failed_files: List of file paths that failed to import
            - parsed_info: Dictionary with parsing information
        """
        if not os.path.exists(ide_file_path):
            raise FileNotFoundError(f"IDE file not found: {ide_file_path}")
        
        imported_entries = []
        failed_files = []
        parsed_info = {
            'objs_count': 0,
            'tobj_count': 0,
            'unique_models': set(),
            'unique_textures': set(),
            'found_models': [],
            'found_textures': [],
            'missing_models': [],
            'missing_textures': []
        }
        
        debug_logger.info(LogCategory.TOOL, "Starting IDE import", {"ide_file_path": ide_file_path})
        
        # Parse IDE file
        models, textures = Import_Export._parse_ide_file(ide_file_path, parsed_info)
        
        if not models and not textures:
            debug_logger.warning(LogCategory.TOOL, "No models or textures found in IDE file", {"ide_file_path": ide_file_path})
            return imported_entries, failed_files, parsed_info
        
        # If models_directory not provided, we'll need to ask for it
        # For now, let's assume it's provided or use the IDE file's directory
        if models_directory is None:
            models_directory = os.path.dirname(ide_file_path)
            debug_logger.info(LogCategory.FILE_IO, "Using IDE file directory as models directory", {"models_directory": models_directory})
        
        # Find and import DFF files
        for model_name in models:
            dff_path = Import_Export._find_file_in_directory(models_directory, f"{model_name}.dff")
            if dff_path:
                parsed_info['found_models'].append(model_name)
                try:
                    entry = Import_Export.import_file(img_archive, dff_path)
                    if entry:
                        imported_entries.append(entry)
                        debug_logger.info(LogCategory.TOOL, "Imported model", {"model": f"{model_name}.dff"})
                    else:
                        failed_files.append(dff_path)
                        debug_logger.error(LogCategory.FILE_IO, "Failed to import model", {"path": dff_path})
                except Exception as e:
                    failed_files.append(dff_path)
                    debug_logger.log_exception(LogCategory.FILE_IO, f"Exception importing model {dff_path}", e)
            else:
                parsed_info['missing_models'].append(model_name)
                debug_logger.warning(LogCategory.FILE_IO, "Model file not found", {"model": f"{model_name}.dff"})
        
        # Find and import TXD files
        for texture_name in textures:
            txd_path = Import_Export._find_file_in_directory(models_directory, f"{texture_name}.txd")
            if txd_path:
                parsed_info['found_textures'].append(texture_name)
                try:
                    entry = Import_Export.import_file(img_archive, txd_path)
                    if entry:
                        imported_entries.append(entry)
                        debug_logger.info(LogCategory.TOOL, "Imported texture", {"texture": f"{texture_name}.txd"})
                    else:
                        failed_files.append(txd_path)
                        debug_logger.error(LogCategory.FILE_IO, "Failed to import texture", {"path": txd_path})
                except Exception as e:
                    failed_files.append(txd_path)
                    debug_logger.log_exception(LogCategory.FILE_IO, f"Exception importing texture {txd_path}", e)
            else:
                parsed_info['missing_textures'].append(texture_name)
                debug_logger.warning(LogCategory.FILE_IO, "Texture file not found", {"texture": f"{texture_name}.txd"})
        
        debug_logger.info(LogCategory.TOOL, "IDE import completed", {
            "models_found": len(parsed_info['found_models']),
            "models_missing": len(parsed_info['missing_models']),
            "textures_found": len(parsed_info['found_textures']),
            "textures_missing": len(parsed_info['missing_textures']),
            "total_imported": len(imported_entries),
            "total_failed": len(failed_files),
        })
        
        return imported_entries, failed_files, parsed_info
    
    @staticmethod
    def _parse_ide_file(ide_file_path, parsed_info):
        """
        Parse IDE file to extract model and texture names from objs and tobj sections.
        
        Args:
            ide_file_path: Path to the IDE file
            parsed_info: Dictionary to store parsing information
            
        Returns:
            Tuple of (models_set, textures_set) containing unique model and texture names
        """
        models = set()
        textures = set()
        current_section = None
        
        try:
            with open(ide_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#') or line.startswith(';'):
                        continue
                    
                    # Check for section headers
                    if line.lower() == 'objs':
                        current_section = 'objs'
                        debug_logger.debug(LogCategory.TOOL, "Found objs section", {"line": line_num})
                        continue
                    elif line.lower() == 'tobj':
                        current_section = 'tobj'
                        debug_logger.debug(LogCategory.TOOL, "Found tobj section", {"line": line_num})
                        continue
                    elif line.lower() == 'end':
                        debug_logger.debug(LogCategory.TOOL, "End of section", {"line": line_num})
                        current_section = None
                        continue
                    
                    # Parse entries based on current section
                    if current_section in ['objs', 'tobj']:
                        try:
                            parts = [part.strip() for part in line.split(',')]
                            if len(parts) >= 3:  # Need at least ID, ModelName, TextureName
                                model_name = parts[1].strip()
                                texture_name = parts[2].strip()
                                
                                # Validate names (should not be empty or numeric IDs)
                                if model_name and not model_name.isdigit() and model_name != '-1':
                                    models.add(model_name)
                                    parsed_info['unique_models'].add(model_name)
                                
                                if texture_name and not texture_name.isdigit() and texture_name != '-1':
                                    textures.add(texture_name)
                                    parsed_info['unique_textures'].add(texture_name)
                                
                                if current_section == 'objs':
                                    parsed_info['objs_count'] += 1
                                else:
                                    parsed_info['tobj_count'] += 1
                                
                                debug_logger.trace(LogCategory.TOOL, f"{current_section} entry", {"model": model_name, "texture": texture_name})
                        except Exception as e:
                            debug_logger.warning(LogCategory.TOOL, "Failed to parse IDE line", {"line_num": line_num, "line": line, "error": str(e)})
                            continue
        
        except Exception as e:
            debug_logger.log_exception(LogCategory.FILE_IO, "Failed to read IDE file", e)
            raise
        
        debug_logger.info(LogCategory.TOOL, "Parsed IDE file", {"unique_models": len(models), "unique_textures": len(textures)})
        return models, textures
    
    @staticmethod
    def _find_file_in_directory(directory, filename, recursive=True):
        """
        Find a file in a directory (case-insensitive search).
        
        Args:
            directory: Directory to search in
            filename: Filename to search for
            recursive: Whether to search subdirectories
            
        Returns:
            Full path to the file if found, None otherwise
        """
        filename_lower = filename.lower()
        
        if recursive:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.lower() == filename_lower:
                        return os.path.join(root, file)
        else:
            try:
                for file in os.listdir(directory):
                    if file.lower() == filename_lower:
                        return os.path.join(directory, file)
            except OSError:
                pass
        
        return None
    @staticmethod
    def import_folder(img_archive, folder_path, recursive=False, filter_extensions=None):
        """
        Imports all files from a folder into an IMG archive (memory only operation).
        The actual IMG file will not be modified until save or rebuild.
        
        Args:
            img_archive: IMGArchive object to import into
            folder_path: Path to the folder to import
            recursive: If True, also imports from subdirectories
            filter_extensions: Optional list of file extensions to import (e.g., ['dff', 'txd'])
            
        Returns:
            Tuple of (imported_entries, failed_files) where:
            - imported_entries: List of successfully imported IMGEntry objects
            - failed_files: List of file paths that failed to import
        """
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            raise NotADirectoryError(f"Folder not found: {folder_path}")
        
        imported_entries = []
        failed_files = []
        
        debug_logger.info(LogCategory.TOOL, "Starting folder import", {"folder_path": folder_path, "recursive": recursive, "filter_extensions": filter_extensions})
        
        # Walk through directory
        for root, dirs, files in os.walk(folder_path):
            debug_logger.debug(LogCategory.FILE_IO, "Processing directory", {"root": root})
            
            for file in files:
                # Check extension if filter is provided
                if filter_extensions:
                    ext = os.path.splitext(file)[1].lower().lstrip('.')
                    if ext not in [e.lower().lstrip('.') for e in filter_extensions]:
                        debug_logger.debug(LogCategory.FILE_IO, "Skipping file due to extension filter", {"file": file, "ext": ext})
                        continue
                
                file_path = os.path.join(root, file)
                
                # For entries from subdirectories, maintain relative path if recursive is True
                if recursive and root != folder_path:
                    rel_path = os.path.relpath(root, folder_path)
                    entry_name = os.path.join(rel_path, file).replace('\\', '/')
                    # Ensure the path separator is correct for IMG files
                    entry_name = entry_name.replace('\\', '/')
                else:
                    entry_name = file
                
                try:
                    debug_logger.debug(LogCategory.FILE_IO, "Attempting to import file", {"file_path": file_path, "entry_name": entry_name})
                    entry = Import_Export.import_file(img_archive, file_path, entry_name)
                    if entry:
                        imported_entries.append(entry)
                        debug_logger.info(LogCategory.TOOL, "Successfully imported file", {"entry_name": entry_name})
                    else:
                        failed_files.append(file_path)
                        debug_logger.error(LogCategory.FILE_IO, "Failed to import file", {"file_path": file_path})
                except Exception as e:
                    failed_files.append(file_path)
                    debug_logger.log_exception(LogCategory.FILE_IO, f"Exception importing {file_path}", e)
            
            # If not recursive, don't process subdirectories
            if not recursive:
                break
        
        debug_logger.info(LogCategory.TOOL, "Folder import completed", {"success_count": len(imported_entries), "failed_count": len(failed_files)})
        return imported_entries, failed_files
    
    @staticmethod
    def import_multiple_files(img_archive, file_paths, entry_names=None):
        """
        Imports multiple files into an IMG archive (memory only operation).
        The actual IMG file will not be modified until save or rebuild.
        
        Args:
            img_archive: IMGArchive object to import into
            file_paths: List of file paths to import
            entry_names: Optional list of entry names. If None, uses basenames of files.
            
        Returns:
            Tuple of (imported_entries, failed_files) where:
            - imported_entries: List of successfully imported IMGEntry objects  
            - failed_files: List of file paths that failed to import
        """
        if not file_paths:
            return [], []
        
        # Validate entry_names list if provided
        if entry_names and len(entry_names) != len(file_paths):
            raise ValueError("entry_names list must be same length as file_paths list")
        
        imported_entries = []
        failed_files = []
        
        debug_logger.info(LogCategory.TOOL, "Starting batch import", {"file_count": len(file_paths)})
        
        for i, file_path in enumerate(file_paths):
            try:
                # Determine entry name
                if entry_names:
                    entry_name = entry_names[i]
                else:
                    entry_name = os.path.basename(file_path)
                
                debug_logger.debug(LogCategory.FILE_IO, "Importing file in batch", {"index": i+1, "total": len(file_paths), "file_path": file_path, "entry_name": entry_name})
                
                entry = Import_Export.import_file(img_archive, file_path, entry_name)
                if entry:
                    imported_entries.append(entry)
                    debug_logger.info(LogCategory.TOOL, "Successfully imported in batch", {"index": i+1, "total": len(file_paths), "entry_name": entry_name})
                else:
                    failed_files.append(file_path)
                    debug_logger.error(LogCategory.FILE_IO, "Failed to import in batch", {"index": i+1, "total": len(file_paths), "file_path": file_path})
                    
            except Exception as e:
                failed_files.append(file_path)
                debug_logger.log_exception(LogCategory.FILE_IO, f"Exception importing {file_path}", e)
        
        debug_logger.info(LogCategory.TOOL, "Batch import completed", {"success_count": len(imported_entries), "failed_count": len(failed_files)})
        return imported_entries, failed_files
    
    @staticmethod
    def export_entry(img_archive, entry, output_path=None, output_dir=None):
        """
        Exports an entry from an IMG archive to a file.
        Handles both existing entries (from file) and new entries (in memory).
        
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
        
        # Check if entry has in-memory data (new/modified entries)
        if hasattr(entry, 'is_new_entry') and entry.is_new_entry and entry.data:
            debug_logger.debug(LogCategory.FILE_IO, "Exporting new/modified entry from memory", {"entry_name": entry.name})
            data_to_write = entry.data
        else:
            # Read entry data from file if not already loaded
            if not entry.data:
                debug_logger.debug(LogCategory.FILE_IO, "Reading entry data from file", {"entry_name": entry.name})
                with open(img_archive.file_path, 'rb') as f:
                    f.seek(entry.actual_offset)
                    data_to_write = f.read(entry.actual_size)
            else:
                data_to_write = entry.data
        
        # Write data to output file
        with open(output_path, 'wb') as f:
            f.write(data_to_write)
        
        debug_logger.info(LogCategory.FILE_IO, "Exported entry", {"entry_name": entry.name, "output_path": output_path, "bytes": len(data_to_write)})
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
            Tuple of (exported_files, failed_entries) where:
            - exported_files: List of paths to successfully exported files
            - failed_entries: List of entries that failed to export
        """
        os.makedirs(output_dir, exist_ok=True)
        
        exported_files = []
        failed_entries = []
        
        debug_logger.info(LogCategory.TOOL, "Starting export all", {"archive_path": img_archive.file_path, "filter_type": filter_type, "total_entries": len(img_archive.entries)})
        
        for entry in img_archive.entries:
            # Apply type filter if provided
            if filter_type and entry.type != filter_type:
                continue
            
            try:
                output_path = Import_Export.export_entry(img_archive, entry, output_dir=output_dir)
                exported_files.append(output_path)
            except Exception as e:
                failed_entries.append(entry)
                debug_logger.log_exception(LogCategory.FILE_IO, f"Error exporting {entry.name}", e)
        
        debug_logger.info(LogCategory.TOOL, "Export all completed", {"success_count": len(exported_files), "failed_count": len(failed_entries)})
        return exported_files, failed_entries
    
    @staticmethod
    def export_by_type(img_archive, output_dir, types):
        """
        Exports entries of specific types from an IMG archive.
        
        Args:
            img_archive: IMGArchive object to export from
            output_dir: Directory to export to
            types: List of file types to export
            
        Returns:
            Dictionary mapping file types to tuples of (exported_files, failed_entries)
        """
        os.makedirs(output_dir, exist_ok=True)
        
        results = {}
        for t in types:
            results[t] = ([], [])  # (exported_files, failed_entries)
        
        debug_logger.info(LogCategory.TOOL, "Starting export by type", {"types": types})
        
        for entry in img_archive.entries:
            # Check if entry type is in requested types
            if entry.type in types:
                try:
                    # Create type-specific subdirectory
                    type_dir = os.path.join(output_dir, entry.type)
                    os.makedirs(type_dir, exist_ok=True)
                    
                    output_path = Import_Export.export_entry(img_archive, entry, output_dir=type_dir)
                    results[entry.type][0].append(output_path)  # Add to exported_files
                except Exception as e:
                    results[entry.type][1].append(entry)  # Add to failed_entries
                    debug_logger.log_exception(LogCategory.FILE_IO, f"Error exporting {entry.name}", e)
        
        # Print summary
        for file_type, (exported, failed) in results.items():
            debug_logger.info(LogCategory.TOOL, "Export by type summary", {"type": file_type, "exported": len(exported), "failed": len(failed)})
        
        return results
    
    @staticmethod
    def validate_import_file(file_path, max_size_mb=None):
        """
        Validates a file before importing to catch potential issues early.
        
        Args:
            file_path: Path to the file to validate
            max_size_mb: Optional maximum file size in MB
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}"
            
            if not os.path.isfile(file_path):
                return False, f"Path is not a file: {file_path}"
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, f"File is empty: {file_path}"
            
            if max_size_mb and file_size > (max_size_mb * 1024 * 1024):
                return False, f"File too large ({file_size / (1024*1024):.1f}MB > {max_size_mb}MB): {file_path}"
            
            # Check filename
            filename = os.path.basename(file_path)
            if len(filename.encode('ascii', errors='replace')) >= MAX_FILENAME_LENGTH:
                return False, f"Filename too long (>{MAX_FILENAME_LENGTH-1} chars): {filename}"
            
            # Check if file is readable
            try:
                with open(file_path, 'rb') as f:
                    f.read(1)  # Try to read at least 1 byte
            except PermissionError:
                return False, f"Permission denied reading file: {file_path}"
            except Exception as e:
                return False, f"Cannot read file: {file_path} - {str(e)}"
            
            return True, "File is valid for import"
            
        except Exception as e:
            return False, f"Error validating file: {str(e)}"
    
    @staticmethod
    def get_import_preview(img_archive, file_paths):
        """
        Get a preview of what would happen if files were imported.
        Does not actually modify the archive.
        
        Args:
            img_archive: IMGArchive object
            file_paths: List of file paths to preview
            
        Returns:
            Dictionary with preview information
        """
        preview = {
            'total_files': len(file_paths),
            'valid_files': [],
            'invalid_files': [],
            'would_replace': [],
            'would_add': [],
            'total_size_bytes': 0,
            'total_size_sectors': 0
        }
        
        for file_path in file_paths:
            # Validate file
            is_valid, error_msg = Import_Export.validate_import_file(file_path)
            
            if not is_valid:
                preview['invalid_files'].append({
                    'file_path': file_path,
                    'error': error_msg
                })
                continue
            
            # File is valid
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            preview['valid_files'].append(file_path)
            preview['total_size_bytes'] += file_size
            preview['total_size_sectors'] += math.ceil(file_size / SECTOR_SIZE)
            
            # Check if would replace existing entry
            existing_entry = img_archive.get_entry_by_name(filename)
            if existing_entry:
                preview['would_replace'].append({
                    'file_path': file_path,
                    'entry_name': filename,
                    'existing_entry': existing_entry
                })
            else:
                preview['would_add'].append({
                    'file_path': file_path,
                    'entry_name': filename
                })
        
        return preview
