"""
Tool Registry for Renderware Modding Suite
Manages all available tools and their instantiation
"""

from application.tools.IMG_Editor import ImgEditorTool
from application.tools.DFF_Viewer.DFF_Viewer import DFFViewerTool
from application.tools.RW_Analyze.RW_Analyze import RWAnalyzeTool
from application.tools.IDE_Editor.IDE_Editor import IDEEditorTool





class ToolRegistry:
    """Registry for all available tools"""
    
    _tools = {
        'IMG_Editor': {
            'name': 'IMG_Editor',
            'class': ImgEditorTool,
            'description': 'Edit and manage IMG archive files',
            'icon': '📁'
        },
        'dff_viewer': {
            'name': 'DFF Viewer',
            'class': DFFViewerTool,
            'description': 'View and analyze 3D model files (DFF/OBJ)',
            'icon': '📦'
        },
        'rw_analyze': {
            'name': 'RW Analyze',
            'class': RWAnalyzeTool,
            'description': 'Analyze RenderWare chunks (DFF/TXD/COL) with tree and details',
            'icon': '🧩'
        },
        'ide_editor': {
            'name': 'IDE Editor',
            'class': IDEEditorTool,
            'description': 'Edit and validate IDE item definition files with table and raw views',
            'icon': '📋'
        },
        # Add other tools here as they are implemented
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
        