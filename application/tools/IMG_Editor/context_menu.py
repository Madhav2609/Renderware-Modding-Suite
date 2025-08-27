"""
Context menu functionality for IMG Editor table entries
"""

from PyQt6.QtWidgets import QMenu
from PyQt6.QtCore import Qt


class IMGTableContextMenu:
    """Context menu handler for IMG entries table"""
    
    def __init__(self, table_widget):
        """Initialize context menu handler
        
        Args:
            table_widget: The IMGEntriesTable instance
        """
        self.table = table_widget
        
    def show_context_menu(self, position):
        """Show context menu for table items"""
        item = self.table.itemAt(position)
        if not item:
            return
        
        # Get the entry from the first column of the row
        row = item.row()
        name_item = self.table.item(row, 0)
        if not name_item:
            return
            
        entry = name_item.data(Qt.ItemDataRole.UserRole)
        if not entry:
            return
        
        menu = QMenu(self.table)
        
        # Rename action
        rename_action = menu.addAction("Rename")
        rename_action.triggered.connect(lambda: self._rename_entry(name_item))
        
        # Show menu at cursor position
        menu.exec(self.table.mapToGlobal(position))
    
    def _rename_entry(self, name_item):
        """Start editing the entry name"""
        if name_item:
            self.table.editItem(name_item)