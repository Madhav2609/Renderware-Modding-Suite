"""
Operations related to IMG archive manipulation.
This module handles functions like rebuilding, merging, splitting, and converting IMG archives.
"""

import os
import math
import struct
import tempfile
from pathlib import Path
from typing import Callable, Optional
from .Core import IMGArchive, IMGEntry, SECTOR_SIZE, V2_SIGNATURE, MAX_FILENAME_LENGTH
from .File_Operations import File_Operations


class IMG_Operations:
    """Class containing methods for various IMG archive operations."""
    
    @staticmethod
    def rebuild_archive(
        img_archive: IMGArchive,
        output_path: Optional[str] = None,
        version: Optional[str] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> IMGArchive:
        """
        Rebuilds an IMG archive, optionally changing its version.
        
        Args:
            img_archive: The IMGArchive object to rebuild
            output_path: Optional path for the rebuilt archive. If None, overwrites the original
            version: Optional target version ('V1' or 'V2'). Defaults to current archive version
            progress_callback: Optional callback receiving (percentage:int, message:str)
            
        Returns:
            A new IMGArchive object representing the rebuilt archive
        """
        if img_archive is None or not img_archive.file_path:
            raise ValueError("Invalid IMG archive provided")

        def report(pct: int, msg: str):
            if progress_callback:
                try:
                    progress_callback(pct, msg)
                except Exception:
                    pass

        original_img_path = img_archive.file_path
        original_dir_path = getattr(img_archive, 'dir_path', None)
        target_version = (version or img_archive.version or 'V2').upper()
        if target_version not in ('V1', 'V2'):
            target_version = 'V2'

        report(1, "Preparing entries for rebuild...")

        # Entries to write are the current in-memory entries (deleted ones were removed already)
        entries = list(img_archive.entries or [])
        entry_count = len(entries)

        # Build metadata list with final sizes (in sectors) and data source
        items = []
        for idx, entry in enumerate(entries):
            # Determine size in sectors
            if getattr(entry, 'is_new_entry', False) and entry.data is not None:
                size_sectors = math.ceil(len(entry.data) / SECTOR_SIZE)
            else:
                size_sectors = int(entry.size)

            # Normalize name to max 24 bytes (leave truncation policy consistent with add_entry)
            name = entry.name or ""
            name_bytes = name.encode('ascii', errors='replace')
            if len(name_bytes) >= MAX_FILENAME_LENGTH:
                name = name[: MAX_FILENAME_LENGTH - 1]

            items.append({
                'name': name,
                'size': size_sectors,
                'streaming_size': size_sectors if target_version == 'V2' else 0,
                'is_new': bool(getattr(entry, 'is_new_entry', False) and entry.data is not None),
                'source_entry': entry,  # for copying from original when not new
            })
            if entry_count > 0:
                report(1 + int((idx / entry_count) * 9), f"Preparing {idx+1}/{entry_count}...")

        # Determine output paths
        if output_path:
            new_img_path = output_path
        else:
            # Create temp file in same directory for atomic replace
            parent = os.path.dirname(original_img_path)
            base = os.path.basename(original_img_path)
            new_img_path = os.path.join(parent, f".{base}.rebuild.tmp")

        new_dir_path = None
        if target_version == 'V1':
            # Compute .dir path accordingly
            new_dir_path = new_img_path.replace('.img', '.dir') if new_img_path.lower().endswith('.img') else new_img_path + '.dir'

        # Compute offsets
        if target_version == 'V2':
            header_bytes = 8  # 'VER2' + uint32 count
            directory_bytes = entry_count * 32
            dir_total_bytes = header_bytes + directory_bytes
            dir_sectors = math.ceil(dir_total_bytes / SECTOR_SIZE)
            next_sector = dir_sectors
        else:
            next_sector = 0

        for item in items:
            item['offset'] = next_sector
            next_sector += item['size']

        # Write new archive
        report(12, "Writing new archive header and directory...")

        # Ensure parent folder exists
        os.makedirs(os.path.dirname(new_img_path) or '.', exist_ok=True)

        # Open files for writing
        if target_version == 'V2':
            with open(new_img_path, 'wb') as out_img:
                # Write header
                out_img.write(V2_SIGNATURE)
                out_img.write(struct.pack('<I', entry_count))
                # Write directory
                for item in items:
                    out_img.write(struct.pack('<I', int(item['offset'])))
                    out_img.write(struct.pack('<H', int(item['streaming_size'])))
                    out_img.write(struct.pack('<H', int(item['size'])))
                    name_bytes = item['name'].encode('ascii', errors='replace')
                    name_bytes = name_bytes[:MAX_FILENAME_LENGTH-1] if len(name_bytes) >= MAX_FILENAME_LENGTH else name_bytes
                    name_bytes = name_bytes + b'\0' * (MAX_FILENAME_LENGTH - len(name_bytes))
                    out_img.write(name_bytes)

                # Pad to directory sector boundary
                expected_pos = dir_sectors * SECTOR_SIZE
                current_pos = out_img.tell()
                if current_pos < expected_pos:
                    out_img.write(b'\0' * (expected_pos - current_pos))

                # Write data blocks
                report(20, "Writing entry data...")
                # Try to reuse one handle for reading original data
                src_handle = None
                try:
                    src_handle = open(original_img_path, 'rb')
                except Exception:
                    src_handle = None

                for i, item in enumerate(items):
                    is_new = item['is_new']
                    src_entry: IMGEntry = item['source_entry']
                    bytes_to_write = item['size'] * SECTOR_SIZE

                    if is_new and src_entry.data is not None:
                        data = src_entry.data
                        out_img.write(data)
                        remaining = bytes_to_write - len(data)
                        if remaining > 0:
                            out_img.write(b'\0' * remaining)
                    else:
                        # Copy from original IMG
                        if src_handle is None:
                            # Fallback: open per read
                            with open(original_img_path, 'rb') as fsrc:
                                fsrc.seek(src_entry.actual_offset)
                                remaining = bytes_to_write
                                chunk = 1024 * 1024
                                while remaining > 0:
                                    data = fsrc.read(min(chunk, remaining))
                                    if not data:
                                        # If read short, pad zeros
                                        out_img.write(b'\0' * remaining)
                                        break
                                    out_img.write(data)
                                    remaining -= len(data)
                        else:
                            src_handle.seek(src_entry.actual_offset)
                            remaining = bytes_to_write
                            chunk = 1024 * 1024
                            while remaining > 0:
                                data = src_handle.read(min(chunk, remaining))
                                if not data:
                                    out_img.write(b'\0' * remaining)
                                    break
                                out_img.write(data)
                                remaining -= len(data)

                    if entry_count > 0:
                        report(20 + int(((i + 1) / entry_count) * 75), f"Writing {i+1}/{entry_count} entries...")

                if src_handle:
                    try:
                        src_handle.close()
                    except Exception:
                        pass
        else:
            # V1: write data to .img and directory entries to .dir
            with open(new_img_path, 'wb') as out_img, open(new_dir_path, 'wb') as out_dir:
                report(15, "Writing V1 IMG data and directory...")
                for i, item in enumerate(items):
                    src_entry: IMGEntry = item['source_entry']
                    bytes_to_write = item['size'] * SECTOR_SIZE

                    # Write data block
                    if item['is_new'] and src_entry.data is not None:
                        data = src_entry.data
                        out_img.write(data)
                        remaining = bytes_to_write - len(data)
                        if remaining > 0:
                            out_img.write(b'\0' * remaining)
                    else:
                        with open(original_img_path, 'rb') as fsrc:
                            fsrc.seek(src_entry.actual_offset)
                            remaining = bytes_to_write
                            chunk = 1024 * 1024
                            while remaining > 0:
                                data = fsrc.read(min(chunk, remaining))
                                if not data:
                                    out_img.write(b'\0' * remaining)
                                    break
                                out_img.write(data)
                                remaining -= len(data)

                    # Write directory entry (offset, size, name)
                    out_dir.write(struct.pack('<I', int(item['offset'])))
                    out_dir.write(struct.pack('<I', int(item['size'])))
                    name_bytes = item['name'].encode('ascii', errors='replace')
                    name_bytes = name_bytes[:MAX_FILENAME_LENGTH-1] if len(name_bytes) >= MAX_FILENAME_LENGTH else name_bytes
                    name_bytes = name_bytes + b'\0' * (MAX_FILENAME_LENGTH - len(name_bytes))
                    out_dir.write(name_bytes)

                    if entry_count > 0:
                        report(15 + int(((i + 1) / entry_count) * 80), f"Writing {i+1}/{entry_count} entries...")

        report(97, "Finalizing rebuild...")

        # Replace original if requested
        if not output_path:
            # Ensure all handles closed, then replace atomically
            try:
                os.replace(new_img_path, original_img_path)
                if target_version == 'V1':
                    # Replace .dir as well
                    new_dir = new_dir_path
                    orig_dir = original_dir_path or original_img_path.replace('.img', '.dir')
                    if new_dir and os.path.exists(new_dir):
                        os.replace(new_dir, orig_dir)
            except Exception as e:
                # Cleanup temp files on failure
                try:
                    if os.path.exists(new_img_path):
                        os.remove(new_img_path)
                except Exception:
                    pass
                try:
                    if new_dir_path and os.path.exists(new_dir_path):
                        os.remove(new_dir_path)
                except Exception:
                    pass
                raise e

            final_img_path = original_img_path
        else:
            final_img_path = new_img_path

        # Re-open the new archive to get fresh metadata and offsets
        report(99, "Verifying rebuilt archive...")
        new_archive = File_Operations.open_archive(final_img_path)
        
        # Analyze RenderWare versions for all entries in the rebuilt archive
        if new_archive and hasattr(new_archive, 'entries') and new_archive.entries:
            report(99, "Analyzing RenderWare versions...")
            new_archive.analyze_all_entries_rw_versions()
        
        # Clear modification tracking/state
        if hasattr(new_archive, 'clear_modification_tracking'):
            new_archive.clear_modification_tracking()

        report(100, "Rebuild completed")
        return new_archive
    
    @staticmethod
    def merge_archives(archives, output_path):
        """
        Merges multiple openedIMG archives into one.
        
        Args:
            archives: List of IMGArchive objects to merge
            output_path: Path for the merged archive
            
        Returns:
            A new IMGArchive object representing the merged archive
        """
        # Implementation will go here
        pass
    
    @staticmethod
    def split_archive(img_archive, output_dir, max_size=None, by_type=False):
        """
        Splits an IMG archive into multiple smaller archives.
        
        Args:
            img_archive: The IMGArchive object to split
            output_dir: Directory to save the split archives
            max_size: Maximum size in bytes for each split archive
            by_type: If True, splits by file type instead of size
            
        Returns:
            List of new IMGArchive objects representing the split archives
        """
        # Implementation will go here
        pass
    
    @staticmethod
    def convert_format(img_archive, output_path, target_version):
        """
        Converts an IMG archive from one version to another.
        
        Args:
            img_archive: The IMGArchive object to convert
            output_path: Path for the converted archive
            target_version: Target version ('V1' or 'V2')
            
        Returns:
            A new IMGArchive object representing the converted archive
        """
        # Implementation will go here
        pass
    
    
   
    @staticmethod
    def compress_archive(img_archive, output_path=None, compression_level=6):
        """
        Compresses entries in an IMG archive (V2 only).
        
        Args:
            img_archive: The IMGArchive object to compress
            output_path: Optional path for the compressed archive. If None, overwrites the original.
            compression_level: Compression level (1-9, where 9 is highest)
            
        Returns:
            A new IMGArchive object representing the compressed archive
        """
        # Implementation will go here
        pass
    
