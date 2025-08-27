"""
Context menu functionality for IMG Editor table entries
"""

from PyQt6.QtWidgets import QMenu, QApplication
from PyQt6.QtCore import Qt
from .img_integrations import IMGToolIntegration
from application.debug_system import get_debug_logger, LogCategory
debug_logger = get_debug_logger()
class IMGTableContextMenu:
    """Context menu handler for IMG entries table"""
    
    def __init__(self, table_widget, img_controller=None):
        """Initialize context menu handler
        
        Args:
            table_widget: The IMGEntriesTable instance
            img_controller: The IMGController instance for tool integration
        """
        self.table = table_widget
        self.integration = IMGToolIntegration(img_controller) if img_controller else None
        
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
        
        # Get selected items count
        selected_items = self.table.selectedItems()
        selected_rows = set(item.row() for item in selected_items)
        
        # Rename action (only for single selection)
        if len(selected_rows) == 1:
            rename_action = menu.addAction("Rename")
            rename_action.triggered.connect(lambda: self._rename_entry(name_item))
            menu.addSeparator()
        
        # Copy entry info action
        copy_info_action = menu.addAction("Copy Entry Info")
        copy_info_action.triggered.connect(lambda: self._copy_entry_info(selected_rows))
        
        menu.addSeparator()
        
        # File type-specific actions
        self._add_file_type_specific_actions(menu, entry, selected_rows)
        
        # Selection actions
        select_inverse_action = menu.addAction("Select Inverse")
        select_inverse_action.triggered.connect(self._select_inverse)
        
        select_none_action = menu.addAction("Select None")
        select_none_action.triggered.connect(self._select_none)
        
        # Show menu at cursor position
        menu.exec(self.table.mapToGlobal(position))
    
    def _rename_entry(self, name_item):
        """Start editing the entry name"""
        if name_item:
            self.table.editItem(name_item)
    
    def _copy_entry_info(self, selected_rows):
        """Copy information about selected entries to clipboard"""
        if not selected_rows:
            return
        
        info_lines = []
        
        for row in sorted(selected_rows):
            name_item = self.table.item(row, 0)
            type_item = self.table.item(row, 1)
            size_item = self.table.item(row, 2)
            offset_item = self.table.item(row, 3)
            rw_version_item = self.table.item(row, 4)
            
            if name_item:
                entry = name_item.data(Qt.ItemDataRole.UserRole)
                name = name_item.text() if name_item else "Unknown"
                file_type = type_item.text() if type_item else "Unknown"
                size = size_item.text() if size_item else "0"
                offset = offset_item.text() if offset_item else "0"
                rw_version = rw_version_item.text() if rw_version_item else "N/A"
                
                info_lines.append(f"Name: {name}")
                info_lines.append(f"Type: {file_type}")
                info_lines.append(f"Size: {size}")
                info_lines.append(f"Offset: {offset}")
                info_lines.append(f"RW Version: {rw_version}")
                
                if len(selected_rows) > 1:
                    info_lines.append("-" * 40)
        
        # Remove the last separator if multiple entries
        if len(selected_rows) > 1 and info_lines and info_lines[-1].startswith("-"):
            info_lines.pop()
        
        clipboard_text = "\n".join(info_lines)
        clipboard = QApplication.clipboard()
        clipboard.setText(clipboard_text)
    
    def _select_inverse(self):
        """Select all unselected rows and deselect selected ones"""
        # Get currently selected rows
        selected_items = self.table.selectedItems()
        selected_rows = set(item.row() for item in selected_items)
        
        # Clear current selection
        self.table.clearSelection()
        
        # Select all rows that weren't previously selected
        for row in range(self.table.rowCount()):
            if row not in selected_rows:
                # Select entire row
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        item.setSelected(True)
    
    def _select_none(self):
        """Clear all selections"""
        self.table.clearSelection()
    
    def _add_file_type_specific_actions(self, menu, entry, selected_rows):
        """Add file type-specific context menu actions
        
        Args:
            menu: QMenu instance to add actions to
            entry: The IMG entry object for the clicked item
            selected_rows: Set of selected row indices
        """
        if not entry:
            return
        
        # Get file type from entry
        file_type = entry.type.lower() if hasattr(entry, 'type') and entry.type else ''
        
        # Placeholder for file type-specific actions
        # TODO: Implement specific actions based on file type
        
        # Example structure for different file types:
        if file_type == 'dff':
            # DFF (RenderWare 3D model) specific actions
            self._add_dff_actions(menu, entry, selected_rows)
        elif file_type == 'txd':
            # TXD (RenderWare texture dictionary) specific actions
            self._add_txd_actions(menu, entry, selected_rows)
        elif file_type == 'col':
            # COL (collision) specific actions
            self._add_col_actions(menu, entry, selected_rows)
        # Add more file types as needed
        
        # If any file type-specific actions were added, add a separator
        # This will be handled by individual type methods
    
    def _add_dff_actions(self, menu, entry, selected_rows):
        """Add DFF (RenderWare 3D model) specific actions"""
        if not self.integration:
            return
        
        # Add separator before DFF-specific actions
        menu.addSeparator()
        
        # View DFF action
        view_dff_action = menu.addAction("View DFF")
        view_dff_action.triggered.connect(lambda: self._view_dff(entry))
        
        # Analyze/Edit DFF sections action
        analyze_dff_action = menu.addAction("Analyze/Edit DFF Sections")
        analyze_dff_action.triggered.connect(lambda: self._analyze_dff(entry))
    
    def _view_dff(self, entry):
        """Export DFF and open in DFF Viewer"""
        debug_logger.info(LogCategory.TOOL, "DFF View action triggered", 
                        {"file": entry.name})
        
        if not self.integration:
            debug_logger.error(LogCategory.TOOL, "No integration available for DFF view", 
                             {"file": entry.name})
            return
        
        # Get the current archive tab
        archive_tab = self._get_current_archive_tab()
        if archive_tab:
            # Get archive path from the tab
            archive_path = getattr(archive_tab, 'archive_path', None) or \
                          (getattr(archive_tab, 'img_archive', None) and 
                           getattr(archive_tab.img_archive, 'file_path', None))
            
            debug_logger.info(LogCategory.TOOL, "Found archive tab, proceeding with export", 
                            {"file": entry.name, "archive": archive_path})
            self.integration.export_and_view_dff(entry, archive_tab)
        else:
            debug_logger.error(LogCategory.TOOL, "Could not find archive tab for DFF view", 
                             {"file": entry.name})
    
    def _analyze_dff(self, entry):
        """Export DFF and open in RW Analyzer"""
        if not self.integration:
            return
        
        # Get the current archive tab
        archive_tab = self._get_current_archive_tab()
        if archive_tab:
            self.integration.export_and_analyze_dff(entry, archive_tab)
    
    def _get_current_archive_tab(self):
        """Get the current archive tab from the table's parent hierarchy"""
        # Navigate up the widget hierarchy to find the archive tab
        parent = self.table.parent()
        while parent:
            debug_logger.debug(LogCategory.TOOL, f"Checking parent: {type(parent).__name__}", 
                             {"has_archive_path": hasattr(parent, 'archive_path'),
                              "has_img_archive": hasattr(parent, 'img_archive')})
            
            # Check for IMGArchiveTab (has archive_path or img_archive)
            if hasattr(parent, 'archive_path') or hasattr(parent, 'img_archive'):
                debug_logger.info(LogCategory.TOOL, f"Found archive tab: {type(parent).__name__}")
                return parent
            parent = parent.parent()
        
        debug_logger.error(LogCategory.TOOL, "No archive tab found in widget hierarchy")
        return None
    
    def _add_txd_actions(self, menu, entry, selected_rows):
        """Add TXD (RenderWare texture dictionary) specific actions"""
        # TODO: Implement TXD-specific actions
        # Examples: View textures, Export as images, Convert format, etc.
        pass
    
    def _add_col_actions(self, menu, entry, selected_rows):
        """Add COL (collision) specific actions"""
        # TODO: Implement COL-specific actions
        # Examples: View collision mesh, Export to OBJ, Analyze complexity, etc.
        pass
