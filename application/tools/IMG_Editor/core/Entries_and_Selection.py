"""
Entry management and selection functionality for IMG archives.
This module handles entry-level operations like adding, removing, and selecting entries.
"""

import os
import math
from pathlib import Path
from .Core import IMGEntry, SECTOR_SIZE, MAX_FILENAME_LENGTH

class Entries_and_Selection:
    """Class containing methods for managing entries and selections in IMG archives."""
    
    @staticmethod
    def add_entry(img_archive, entry):
        """
        Adds a new entry to an IMG archive.
        
        Args:
            img_archive: IMGArchive object to add to
            entry: IMGEntry object to add
            
        Returns:
            True if successful, False otherwise
        """
        # Ensure entry name is valid
        if not entry.name or len(entry.name.encode('ascii', errors='replace')) >= MAX_FILENAME_LENGTH:
            return False
        
        # Check for duplicate names
        if img_archive.get_entry_by_name(entry.name):
            return False
        
        # Update entry offset if not set
        if entry.offset == 0 and img_archive.entries:
            last_entry = img_archive.entries[-1]
            entry.offset = last_entry.offset + last_entry.size
        
        img_archive.entries.append(entry)
        img_archive.modified = True
        return True
    
    @staticmethod
    def remove_entry(img_archive, entry_or_name):
        """
        Removes an entry from an IMG archive.
        
        Args:
            img_archive: IMGArchive object to remove from
            entry_or_name: IMGEntry object or entry name to remove
            
        Returns:
            True if successful, False otherwise
        """
        entry = entry_or_name
        if isinstance(entry_or_name, str):
            entry = img_archive.get_entry_by_name(entry_or_name)
            
        if not entry or entry not in img_archive.entries:
            return False
        
        img_archive.entries.remove(entry)
        img_archive.modified = True
        return True
    
    @staticmethod
    def rename_entry(img_archive, entry_or_name, new_name):
        """
        Renames an entry in an IMG archive.
        
        Args:
            img_archive: IMGArchive object containing the entry
            entry_or_name: IMGEntry object or entry name to rename
            new_name: New name for the entry
            
        Returns:
            True if successful, False otherwise
        """
        entry = entry_or_name
        if isinstance(entry_or_name, str):
            entry = img_archive.get_entry_by_name(entry_or_name)
            
        if not entry or entry not in img_archive.entries:
            return False
        
        # Ensure new name is valid
        if not new_name or len(new_name.encode('ascii', errors='replace')) >= MAX_FILENAME_LENGTH:
            return False
        
        # Check for duplicate names
        if img_archive.get_entry_by_name(new_name) and img_archive.get_entry_by_name(new_name) != entry:
            return False
        
        entry.name = new_name
        img_archive.modified = True
        return True
    
    @staticmethod
    def replace_entry(img_archive, entry_or_name, new_data):
        """
        Replaces the data of an entry in an IMG archive.
        
        Args:
            img_archive: IMGArchive object containing the entry
            entry_or_name: IMGEntry object or entry name to replace
            new_data: New binary data for the entry
            
        Returns:
            True if successful, False otherwise
        """
        entry = entry_or_name
        if isinstance(entry_or_name, str):
            entry = img_archive.get_entry_by_name(entry_or_name)
            
        if not entry or entry not in img_archive.entries:
            return False
        
        # Calculate size in sectors (rounded up)
        size_in_sectors = math.ceil(len(new_data) / SECTOR_SIZE)
        
        # If size changed, we need to adjust offsets of subsequent entries
        # This is a simplified approach; real implementation would need to handle
        # actual file layout
        if size_in_sectors != entry.size:
            diff = size_in_sectors - entry.size
            entry_index = img_archive.entries.index(entry)
            
            for i in range(entry_index + 1, len(img_archive.entries)):
                img_archive.entries[i].offset += diff
        
        entry.size = size_in_sectors
        if img_archive.version == 'V2':
            entry.streaming_size = size_in_sectors
        entry.data = new_data
        img_archive.modified = True
        return True
    
    @staticmethod
    def move_entry(img_archive, entry_or_name, new_position):
        """
        Moves an entry to a new position in the entries list.
        
        Args:
            img_archive: IMGArchive object containing the entry
            entry_or_name: IMGEntry object or entry name to move
            new_position: New index position for the entry
            
        Returns:
            True if successful, False otherwise
        """
        entry = entry_or_name
        if isinstance(entry_or_name, str):
            entry = img_archive.get_entry_by_name(entry_or_name)
            
        if not entry or entry not in img_archive.entries:
            return False
        
        if new_position < 0 or new_position >= len(img_archive.entries):
            return False
            
        current_position = img_archive.entries.index(entry)
        if current_position == new_position:
            return True
        
        img_archive.entries.pop(current_position)
        img_archive.entries.insert(new_position, entry)
        img_archive.modified = True
        return True
    
    @staticmethod
    def sort_entries(img_archive, sort_by='name', reverse=False):
        """
        Sorts entries in an IMG archive.
        
        Args:
            img_archive: IMGArchive object to sort entries in
            sort_by: Field to sort by ('name', 'offset', 'size', 'type')
            reverse: If True, sort in descending order
            
        Returns:
            True if successful, False otherwise
        """
        if sort_by == 'name':
            img_archive.entries.sort(key=lambda e: e.name.lower(), reverse=reverse)
        elif sort_by == 'offset':
            img_archive.entries.sort(key=lambda e: e.offset, reverse=reverse)
        elif sort_by == 'size':
            img_archive.entries.sort(key=lambda e: e.size, reverse=reverse)
        elif sort_by == 'type':
            img_archive.entries.sort(key=lambda e: e.type, reverse=reverse)
        else:
            return False
        
        img_archive.modified = True
        return True
    
    @staticmethod
    def filter_entries(img_archive, filter_text=None, filter_type=None):
        """
        Filters entries in an IMG archive based on name and/or type.
        
        Args:
            img_archive: IMGArchive object to filter entries in
            filter_text: Text to filter names by
            filter_type: Type to filter by
            
        Returns:
            List of IMGEntry objects that match the filter
        """
        result = img_archive.entries.copy()
        
        if filter_text:
            filter_text = filter_text.lower()
            result = [e for e in result if filter_text in e.name.lower()]
            
        if filter_type and filter_type.upper() != 'ALL':
            result = [e for e in result if e.type == filter_type.upper()]
            
        return result
