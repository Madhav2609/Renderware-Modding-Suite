"""
Status Bar Widget for Renderware Modding Suite
Shows application status, file information, and progress
"""

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QProgressBar,
                            QPushButton)
from PyQt6.QtCore import Qt, QTimer
from .responsive_utils import get_responsive_manager


class StatusBarWidget(QWidget):
    """Status bar showing application state and file information"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        # Timer for clearing temporary messages
        self.message_timer = QTimer()
        self.message_timer.timeout.connect(self.clear_temporary_message)
        self.message_timer.setSingleShot(True)
    
    def setup_ui(self):
        """Setup the status bar UI with responsive sizing"""
        rm = get_responsive_manager()
        fonts = rm.get_font_config()
        spacing = rm.get_spacing_config()
        
        layout = QHBoxLayout()
        layout.setContentsMargins(spacing['small'], spacing['small']//2, spacing['small'], spacing['small']//2)
        
        # Status message label with responsive font
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: #61dafb; font-weight: bold; font-size: {fonts['status']['size']}px;")
        
        # File info label with responsive font
        self.file_label = QLabel("No file loaded")
        self.file_label.setStyleSheet(f"color: #888; font-size: {fonts['status']['size']}px;")
        
        # Progress bar (hidden by default) with responsive width
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(rm.get_scaled_size(200))
        self.progress_bar.setVisible(False)
        
        # Memory usage with responsive font
        self.memory_label = QLabel("Memory: 0 MB")
        self.memory_label.setStyleSheet(f"color: #888; font-size: {fonts['small']['size']}px;")
        
        # Add widgets to layout
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.file_label)
        layout.addStretch()
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.memory_label)
        
        self.setLayout(layout)
    
    def set_status(self, message, temporary=False, timeout=3000):
        """Set status message"""
        self.status_label.setText(message)
        
        if temporary:
            self.message_timer.start(timeout)
    
    def set_file_info(self, file_path, file_size=None):
        """Set current file information"""
        if file_path:
            import os
            file_name = os.path.basename(file_path)
            
            if file_size is None and os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
            
            if file_size is not None:
                # Format file size
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                
                self.file_label.setText(f"📄 {file_name} ({size_str})")
            else:
                self.file_label.setText(f"📄 {file_name}")
        else:
            self.file_label.setText("No file loaded")
    
    def show_progress(self, visible=True):
        """Show/hide progress bar"""
        self.progress_bar.setVisible(visible)
    
    def set_progress(self, value, maximum=100):
        """Set progress bar value"""
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(value)
        
        if not self.progress_bar.isVisible():
            self.progress_bar.setVisible(True)
    
    def set_memory_usage(self, mb_used):
        """Set memory usage display"""
        self.memory_label.setText(f"Memory: {mb_used:.1f} MB")
    
    def clear_temporary_message(self):
        """Clear temporary status message"""
        self.status_label.setText("Ready")
    
    def show_error(self, message):
        """Show error status"""
        self.status_label.setText(f"❌ {message}")
        self.status_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        self.message_timer.start(5000)  # Show error for 5 seconds
    
    def show_success(self, message):
        """Show success status"""
        self.status_label.setText(f"✅ {message}")
        self.status_label.setStyleSheet("color: #51cf66; font-weight: bold;")
        self.message_timer.start(3000)  # Show success for 3 seconds
    
    def show_warning(self, message):
        """Show warning status"""
        self.status_label.setText(f"⚠️ {message}")
        self.status_label.setStyleSheet("color: #ffd43b; font-weight: bold;")
        self.message_timer.start(4000)  # Show warning for 4 seconds
