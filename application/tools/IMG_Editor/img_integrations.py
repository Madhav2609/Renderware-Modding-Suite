"""
IMG Editor Tool Integrations
Handles seamless integration between IMG Editor and other tools in the suite
"""

import os
import tempfile
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal

from application.debug_system import get_debug_logger, LogCategory

# Module-level debug logger
debug_logger = get_debug_logger()


class IMGToolIntegration(QObject):
    """Handles integration between IMG Editor and other tools"""
    
    # Signals for tool communication
    tool_open_requested = pyqtSignal(str, dict)  # tool_name, params
    
    def __init__(self, img_controller, parent=None):
        """Initialize tool integration handler
        
        Args:
            img_controller: The IMGController instance
            parent: Parent QObject
        """
        super().__init__(parent)
        self.img_controller = img_controller
        self._temp_files = []  # Track temporary files for cleanup
        
    def export_and_view_dff(self, entry, archive_tab):
        """Export DFF file and open it in DFF Viewer
        
        Args:
            entry: The IMG entry to export
            archive_tab: The archive tab containing the entry
        """
        debug_logger.info(LogCategory.TOOL, "Starting DFF export and view", 
                        {"file": entry.name})
        
        try:
            # Export DFF to temporary file
            temp_file = self._export_entry_to_temp(entry, archive_tab)
            if not temp_file:
                debug_logger.error(LogCategory.TOOL, "Failed to export DFF to temp file", 
                                 {"file": entry.name})
                return False
            
            # Open DFF Viewer tool with the exported file
            params = {
                'file_path': temp_file,
                'auto_load': True
            }
            
            debug_logger.info(LogCategory.TOOL, "Opening DFF in viewer", 
                            {"file": entry.name, "temp_path": temp_file})
            
            self.tool_open_requested.emit('dff_viewer', params)
            return True
            
        except Exception as e:
            debug_logger.error(LogCategory.TOOL, "Failed to export and view DFF", 
                             {"error": str(e), "file": entry.name})
            return False
    
    def export_and_analyze_dff(self, entry, archive_tab):
        """Export DFF file and open it in RW Analyzer
        
        Args:
            entry: The IMG entry to export
            archive_tab: The archive tab containing the entry
        """
        try:
            # Export DFF to temporary file
            temp_file = self._export_entry_to_temp(entry, archive_tab)
            if not temp_file:
                return False
            
            # Open RW Analyzer tool with the exported file
            params = {
                'file_path': temp_file,
                'auto_load': True,
                'analysis_mode': 'dff_sections'
            }
            
            debug_logger.info(LogCategory.TOOL, "Opening DFF in analyzer", 
                            {"file": entry.name, "temp_path": temp_file})
            
            self.tool_open_requested.emit('rw_analyze', params)
            return True
            
        except Exception as e:
            debug_logger.error(LogCategory.TOOL, "Failed to export and analyze DFF", 
                             {"error": str(e), "file": entry.name})
            return False
    
    def _export_entry_to_temp(self, entry, archive_tab):
        """Export an IMG entry to a temporary file
        
        Args:
            entry: The IMG entry to export
            archive_tab: The archive tab containing the entry
            
        Returns:
            str: Path to temporary file, or None if failed
        """
        try:
            # Create temporary file with proper extension
            file_ext = entry.type.lower() if hasattr(entry, 'type') and entry.type else 'bin'
            temp_dir = tempfile.gettempdir()
            temp_filename = f"{entry.name}"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            # Export the entry using the controller
            success, message = self.img_controller.export_entry(entry, output_path=temp_path)
            
            if success:
                self._temp_files.append(temp_path)
                debug_logger.debug(LogCategory.FILE_IO, "Entry exported to temp file", 
                                 {"entry": entry.name, "temp_path": temp_path})
                return temp_path
            else:
                debug_logger.error(LogCategory.FILE_IO, "Failed to export entry", 
                                 {"entry": entry.name, "message": message})
                return None
                
        except Exception as e:
            debug_logger.error(LogCategory.FILE_IO, "Exception during entry export", 
                             {"error": str(e), "entry": entry.name})
            return None
    
    def cleanup_temp_files(self):
        """Clean up temporary files created during integration"""
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    debug_logger.debug(LogCategory.FILE_IO, "Cleaned up temp file", 
                                     {"file": temp_file})
            except Exception as e:
                debug_logger.warning(LogCategory.FILE_IO, "Failed to clean up temp file", 
                                   {"file": temp_file, "error": str(e)})
        
        self._temp_files.clear()