"""
Progress Dialog for IMG Editor Operations
Provides a modal dialog with progress bar and cancel functionality for long-running operations.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QProgressBar, QPushButton, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QFontDatabase

from application.responsive_utils import get_responsive_manager
from application.styles import ModernDarkTheme


def _get_font_weight(weight_str):
    """Convert string weight to QFont weight constant."""
    weight_map = {
        "normal": QFont.Weight.Normal,
        "bold": QFont.Weight.Bold,
        "light": QFont.Weight.Light,
        "medium": QFont.Weight.Medium
    }
    return weight_map.get(weight_str, QFont.Weight.Normal)


class IMGProgressDialog(QDialog):
    """
    Modal progress dialog for IMG operations.
    Shows progress bar, status message, and cancel button.
    """
    
    # Signals
    cancelled = pyqtSignal()  # Emitted when user cancels the operation

    def __init__(self, title="Operation in Progress", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 150)
        
        # Setup UI
        self._setup_ui()
        self._apply_styling()
        
        # State
        self._cancelled = False
        
    def _setup_ui(self):
        """Setup the user interface."""
        rm = get_responsive_manager()
        fonts = rm.get_font_config()
        spacing = rm.get_spacing_config()
        
        layout = QVBoxLayout(self)
        layout.setSpacing(spacing['medium'])
        layout.setContentsMargins(spacing['medium'], spacing['medium'], 
                                 spacing['medium'], spacing['medium'])
        
        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Cancel button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
    def _apply_styling(self):
        """Apply modern dark theme styling."""
        rm = get_responsive_manager()
        fonts = rm.get_font_config()
        spacing = rm.get_spacing_config()
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #404040;
                border-radius: {spacing['small']}px;
            }}
            
            QLabel {{
                color: white;
                font-size: {fonts['body']['size']}px;
                font-weight: {fonts['body']['weight']};
                padding: {spacing['small']}px;
            }}
            
            QProgressBar {{
                border: 1px solid #404040;
                border-radius: {spacing['small']}px;
                background-color: #1e1e1e;
                text-align: center;
                color: white;
                font-size: {fonts['body']['size']}px;
            }}
            
            QProgressBar::chunk {{
                background-color: #0078d4;
                border-radius: {spacing['small']}px;
            }}
            
            QPushButton {{
                background-color: #404040;
                border: 1px solid #606060;
                border-radius: {spacing['small']}px;
                color: white;
                padding: {spacing['small']}px {spacing['medium']}px;
                font-size: {fonts['body']['size']}px;
                font-weight: {fonts['body']['weight']};
                min-width: 80px;
            }}
            
            QPushButton:hover {{
                background-color: #505050;
                border-color: #707070;
            }}
            
            QPushButton:pressed {{
                background-color: #303030;
                border-color: #505050;
            }}
        """)
    
    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        self._cancelled = True
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("Cancelling...")
        self.cancelled.emit()
    
    def update_progress(self, percentage, message=None):
        """
        Update the progress bar and status message.
        
        Args:
            percentage: Progress percentage (0-100)
            message: Optional status message to display
        """
        self.progress_bar.setValue(percentage)
        if message:
            self.status_label.setText(message)
    
    def set_status(self, message):
        """Set the status message without changing progress."""
        self.status_label.setText(message)
    
    def is_cancelled(self):
        """Check if the operation was cancelled."""
        return self._cancelled
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        if self._cancelled:
            event.accept()
        else:
            # Prevent closing by clicking X - user must cancel
            event.ignore()


class IMGProgressPanel(QFrame):
    """
    Non-modal progress panel for embedding in the main UI.
    Shows progress bar and status for ongoing operations.
    """
    
    # Signals
    cancelled = pyqtSignal()  # Emitted when user cancels the operation

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)  # Hidden by default
        self._setup_ui()
        self._apply_styling()
        
        # State
        self._cancelled = False
        
    def _setup_ui(self):
        """Setup the user interface."""
        rm = get_responsive_manager()
        fonts = rm.get_font_config()
        spacing = rm.get_spacing_config()
        
        layout = QVBoxLayout(self)
        layout.setSpacing(spacing['small'])
        layout.setContentsMargins(spacing['small'], spacing['small'], 
                                 spacing['small'], spacing['small'])
        
        # Header with title and cancel button
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Operation in Progress")
        self.title_label.setFont(QFont('Arial',
                                      fonts['header']['size'],
                                      _get_font_weight(fonts['header']['weight'])))
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedSize(60, 25)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        header_layout.addWidget(self.cancel_button)
        
        layout.addLayout(header_layout)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(20)
        layout.addWidget(self.progress_bar)
        
    def _apply_styling(self):
        """Apply modern dark theme styling."""
        rm = get_responsive_manager()
        fonts = rm.get_font_config()
        spacing = rm.get_spacing_config()
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #2b2b2b;
                border: 1px solid #404040;
                border-radius: {spacing['small']}px;
                padding: {spacing['small']}px;
            }}
            
            QLabel {{
                color: white;
                font-size: {fonts['body']['size']}px;
                font-weight: {fonts['body']['weight']};
            }}
            
            QProgressBar {{
                border: 1px solid #404040;
                border-radius: {spacing['small']}px;
                background-color: #1e1e1e;
                text-align: center;
                color: white;
                font-size: {fonts['body']['size']}px;
            }}
            
            QProgressBar::chunk {{
                background-color: #0078d4;
                border-radius: {spacing['small']}px;
            }}
            
            QPushButton {{
                background-color: #404040;
                border: 1px solid #606060;
                border-radius: {spacing['small']}px;
                color: white;
                font-size: {fonts['body']['size']}px;
                font-weight: {fonts['body']['weight']};
            }}
            
            QPushButton:hover {{
                background-color: #505050;
                border-color: #707070;
            }}
            
            QPushButton:pressed {{
                background-color: #303030;
                border-color: #505050;
            }}
        """)
    
    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        self._cancelled = True
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("...")
        self.cancelled.emit()
    
    def start_operation(self, title="Operation in Progress"):
        """Start a new operation and show the panel."""
        self._cancelled = False
        self.title_label.setText(title)
        self.status_label.setText("Initializing...")
        self.progress_bar.setValue(0)
        self.cancel_button.setEnabled(True)
        self.cancel_button.setText("Cancel")
        self.setVisible(True)
    
    def update_progress(self, percentage, message=None):
        """
        Update the progress bar and status message.
        
        Args:
            percentage: Progress percentage (0-100)
            message: Optional status message to display
        """
        self.progress_bar.setValue(percentage)
        if message:
            self.status_label.setText(message)
    
    def set_status(self, message):
        """Set the status message without changing progress."""
        self.status_label.setText(message)
    
    def complete_operation(self, success=True, message=None):
        """Complete the operation and hide the panel."""
        if success:
            self.progress_bar.setValue(100)
            if message:
                self.status_label.setText(message)
            
            # Auto-hide after a short delay
            QTimer.singleShot(2000, self.hide)
        else:
            self.hide()
    
    def is_cancelled(self):
        """Check if the operation was cancelled."""
        return self._cancelled
    
    def hide(self):
        """Hide the progress panel."""
        self.setVisible(False)
        self._cancelled = False
    
    def reset(self):
        """Reset the progress panel to initial state."""
        self._cancelled = False
        self.title_label.setText("Operation in Progress")
        self.status_label.setText("Initializing...")
        self.progress_bar.setValue(0)
        self.cancel_button.setEnabled(True)
        self.cancel_button.setText("Cancel")
        self.setVisible(False) 