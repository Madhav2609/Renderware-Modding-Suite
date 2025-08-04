"""
Tool Registry for Renderware Modding Suite
Manages all available tools and their instantiation
"""

from .img_editor import ImgEditorTool
from .batch_converter import BatchConverterTool
from .file_validator import FileValidatorTool
from .backup_manager import BackupManagerTool


class ToolRegistry:
    """Registry for all available tools"""
    
    _tools = {
        'img_editor': {
            'name': 'IMG Editor',
            'class': ImgEditorTool,
            'description': 'Edit and manage IMG archive files',
            'icon': '📁'
        },
        'batch_converter': {
            'name': 'Batch Converter',
            'class': BatchConverterTool,
            'description': 'Convert multiple files at once',
            'icon': '📦'
        },
        'file_validator': {
            'name': 'File Validator',
            'class': FileValidatorTool,
            'description': 'Validate file integrity and format',
            'icon': '✅'
        },
        'backup_manager': {
            'name': 'Backup Manager',
            'class': BackupManagerTool,
            'description': 'Manage file backups and versions',
            'icon': '💾'
        },
        # Future tools can be added here
        'model_viewer': {
            'name': 'Model Viewer',
            'class': None,  # To be implemented
            'description': 'View and preview 3D models',
            'icon': '👁️'
        },
        'texture_viewer': {
            'name': 'Texture Viewer',
            'class': None,  # To be implemented
            'description': 'View and edit textures',
            'icon': '�️'
        }
    }
    
    @classmethod
    def get_tool_info(cls, tool_name):
        """Get information about a tool"""
        return cls._tools.get(tool_name)
    
    @classmethod
    def get_all_tools(cls):
        """Get all registered tools"""
        return cls._tools.copy()
    
    @classmethod
    def create_tool(cls, tool_name, parent=None):
        """Create an instance of a tool"""
        tool_info = cls._tools.get(tool_name)
        if tool_info and tool_info['class']:
            return tool_info['class'](parent)
        return None
    
    @classmethod
    def is_tool_available(cls, tool_name):
        """Check if a tool is available and implemented"""
        tool_info = cls._tools.get(tool_name)
        return tool_info is not None and tool_info['class'] is not None
    
    @classmethod
    def register_tool(cls, tool_name, tool_class, name, description, icon):
        """Register a new tool"""
        cls._tools[tool_name] = {
            'name': name,
            'class': tool_class,
            'description': description,
            'icon': icon
        }
