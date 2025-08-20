"""
Message Box Module
Provides standardized error, warning, and information message boxes
"""

from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt
from enum import Enum, auto

class MessageType(Enum):
    """Message type enumeration"""
    ERROR = auto()
    WARNING = auto()
    INFO = auto()
    SUCCESS = auto()

class MessageBox:
    """
    Unified message box for displaying errors, warnings, and information
    across the application.
    """
    
    @staticmethod
    def show_message(message: str, title: str = None, msg_type: MessageType = MessageType.INFO, 
                     parent=None, details: str = None):
        """
        Display a message box with the specified message, title and type
        
        Args:
            message: The main message to display
            title: The title of the message box
            msg_type: The type of message (ERROR, WARNING, INFO, SUCCESS)
            parent: The parent widget
            details: Optional detailed message to show in expandable section
        """
        msg_box = QMessageBox(parent)
        
        # Set icon based on message type
        if msg_type == MessageType.ERROR:
            msg_box.setIcon(QMessageBox.Icon.Critical)
            if not title:
                title = "Error"
        elif msg_type == MessageType.WARNING:
            msg_box.setIcon(QMessageBox.Icon.Warning)
            if not title:
                title = "Warning"
        elif msg_type == MessageType.SUCCESS:
            msg_box.setIcon(QMessageBox.Icon.Information)
            if not title:
                title = "Success"
        else:  # INFO
            msg_box.setIcon(QMessageBox.Icon.Information)
            if not title:
                title = "Information"
                
        # Set title and text
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        # Add details if provided
        if details:
            msg_box.setDetailedText(details)
        
        # Execute
        msg_box.exec()
    
    @staticmethod
    def error(message: str, title: str = "Error", parent=None, details: str = None):
        """Display an error message box"""
        MessageBox.show_message(message, title, MessageType.ERROR, parent, details)
    
    @staticmethod
    def warning(message: str, title: str = "Warning", parent=None, details: str = None):
        """Display a warning message box"""
        MessageBox.show_message(message, title, MessageType.WARNING, parent, details)
    
    @staticmethod
    def info(message: str, title: str = "Information", parent=None, details: str = None):
        """Display an information message box"""
        MessageBox.show_message(message, title, MessageType.INFO, parent, details)
    
    @staticmethod
    def success(message: str, title: str = "Success", parent=None, details: str = None):
        """Display a success message box"""
        MessageBox.show_message(message, title, MessageType.SUCCESS, parent, details)

# Create a global instance for easier imports
message_box = MessageBox()
