"""
Shim module: legacy IMG_Editor re-exports.
This module re-exports classes from split modules.
Do not add implementations here; use the dedicated modules instead.
"""

# Re-export UI components
from .ui_components import (
    IMGFileInfoPanel,
    IMGEntriesTable,
    FilterPanel,
)

# Re-export Archive tab
from .archive_tab import IMGArchiveTab

# Re-export main tool widget
from .img_editor_tool import ImgEditorTool

__all__ = [
    "IMGFileInfoPanel",
    "IMGEntriesTable",
    "FilterPanel",
    "IMGArchiveTab",
    "ImgEditorTool",
]

# End of shim
