"""
IMG Editor Core Package
This package contains the core functionality for handling GTA IMG archives.
"""

from .Core import IMGEntry, IMGArchive, SECTOR_SIZE, V2_SIGNATURE, MAX_FILENAME_LENGTH
from .File_Operations import File_Operations
from .IMG_Operations import IMG_Operations
from .Import_Export import Import_Export

__all__ = [
    'IMGEntry', 
    'IMGArchive',
    'SECTOR_SIZE',
    'V2_SIGNATURE',
    'MAX_FILENAME_LENGTH',
    'File_Operations',
    'IMG_Operations',
    'Import_Export'
]
