# Renderware Modding Suite - Coding Guidelines

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [UI Design Principles](#ui-design-principles)
- [Theme System](#theme-system)
- [Responsive Design](#responsive-design)
- [Tool Development](#tool-development)
- [File Organization](#file-organization)
- [Best Practices](#best-practices)
- [Common Patterns](#common-patterns)
- [Testing & Debugging](#testing--debugging)

## Architecture Overview

### Application Structure
```
application/
├── main.py                     # Entry point
├── main_application.py         # Main window and application logic
├── styles.py                   # Centralized theme system
├── responsive_utils.py         # Responsive design utilities
├── content_area.py            # Central content management
├── file_explorer.py           # File browser component
├── tools_panel.py             # Tools sidebar
├── status_bar.py              # Status information
├── common/                    # Shared utilities
│   ├── message_box.py         # Standardized dialogs
│   └── rw_versions.py         # RenderWare version detection
└── tools/                     # Individual tools
    ├── tool_registry.py       # Tool registration system
    └── [ToolName]/            # Tool-specific modules
        ├── __init__.py
        ├── [tool]_controller.py  # Business logic
        ├── [Tool].py             # UI implementation
        └── core/                 # Tool-specific utilities
```

### Core Principles
1. **Separation of Concerns**: UI, business logic, and data management are separate
2. **Responsive Design**: All UI elements adapt to different screen sizes
3. **Centralized Theming**: All colors and styles come from the theme system
4. **Modular Tools**: Each tool is self-contained and follows the same patterns

## UI Design Principles

### 1. Consistent Visual Hierarchy
```python
# Header levels (use responsive font configs)
rm = get_responsive_manager()
fonts = rm.get_font_config()

header_label = QLabel("🔧 Tool Name")
header_label.setStyleSheet(f"font-weight: bold; font-size: {fonts['header']['size']}px;")

subheader_label = QLabel("Section Title")
subheader_label.setStyleSheet(f"font-weight: bold; font-size: {fonts['subheader']['size']}px;")
```

### 2. Dark Theme Enforcement
**ALWAYS** use theme constants, never hardcode colors:
```python
from application.styles import ModernDarkTheme

# ✅ CORRECT
widget.setStyleSheet(f"background-color: {ModernDarkTheme.BACKGROUND_PRIMARY};")

# ❌ WRONG
widget.setStyleSheet("background-color: #1e1e1e;")
```

### 3. Responsive Spacing and Sizing
```python
rm = get_responsive_manager()
spacing = rm.get_spacing_config()
button_size = rm.get_button_size()

layout.setContentsMargins(spacing['medium'], spacing['small'], spacing['medium'], spacing['small'])
button.setMinimumSize(button_size[0], button_size[1])
```

## Theme System

### Theme Constants Reference
```python
# Background Colors
ModernDarkTheme.BACKGROUND_PRIMARY   = "#1e1e1e"  # Main window background
ModernDarkTheme.BACKGROUND_SECONDARY = "#252526"  # Panel backgrounds
ModernDarkTheme.BACKGROUND_TERTIARY  = "#2d2d30"  # Widget backgrounds

# Text Colors
ModernDarkTheme.TEXT_PRIMARY    = "#cccccc"  # Main text
ModernDarkTheme.TEXT_SECONDARY  = "#969696"  # Secondary text
ModernDarkTheme.TEXT_ACCENT     = "#007acc"  # Links, highlights
ModernDarkTheme.TEXT_SUCCESS    = "#4ec9b0"  # Success messages
ModernDarkTheme.TEXT_WARNING    = "#dcdcaa"  # Warning messages
ModernDarkTheme.TEXT_ERROR      = "#f44747"  # Error messages

# Border Colors
ModernDarkTheme.BORDER_PRIMARY   = "#2d2d30"  # Main borders
ModernDarkTheme.BORDER_SECONDARY = "#464647"  # Secondary borders
ModernDarkTheme.BORDER_ACCENT    = "#007acc"  # Focused borders

# Interactive Colors
ModernDarkTheme.HOVER_COLOR      = "#3e3e42"  # Hover states
ModernDarkTheme.SELECTION_COLOR  = "#37373d"  # Selected items
ModernDarkTheme.BUTTON_PRIMARY   = "#0e639c"  # Button background
ModernDarkTheme.BUTTON_HOVER     = "#1177bb"  # Button hover
ModernDarkTheme.BUTTON_PRESSED   = "#005a9e"  # Button pressed
```

### Theme Application
```python
# Apply theme to entire application (in main.py)
theme = ModernDarkTheme()
app.setStyleSheet(theme.get_main_stylesheet())
theme.apply_dark_palette(app)

# For individual widgets
widget.setStyleSheet(f"""
    QWidget {{
        background-color: {ModernDarkTheme.BACKGROUND_SECONDARY};
        color: {ModernDarkTheme.TEXT_PRIMARY};
        border: 1px solid {ModernDarkTheme.BORDER_SECONDARY};
    }}
""")
```

## Responsive Design

### Get Responsive Manager
```python
from application.responsive_utils import get_responsive_manager

rm = get_responsive_manager()
```

### Font Configuration
```python
fonts = rm.get_font_config()
# Available font sizes:
# fonts['header']['size']     - Large headers
# fonts['subheader']['size']  - Section headers
# fonts['body']['size']       - Normal text
# fonts['small']['size']      - Small text
# fonts['code']['size']       - Code/monospace
# fonts['menu']['size']       - Menu items
# fonts['status']['size']     - Status bar
```

### Spacing Configuration
```python
spacing = rm.get_spacing_config()
# Available spacing:
# spacing['small']   - 4-8px depending on scale
# spacing['medium']  - 6-12px depending on scale
# spacing['large']   - 11-22px depending on scale
# spacing['xlarge']  - 14-28px depending on scale
```

### Responsive Sizing
```python
# Button sizes
button_size = rm.get_button_size()  # Returns (width, height)

# Scaled sizes
scaled_width = rm.get_scaled_size(200)  # Scales 200px based on DPI

# Panel dimensions
panel_min, panel_max = rm.get_panel_width()  # Min/max panel widths

# Window size
window_size = rm.get_window_size()  # Optimal window size

# Icon size
icon_size = rm.get_icon_size()  # Consistent icon sizing
```

### Breakpoint System
```python
# Current breakpoint
if rm.breakpoint == "small":
    # Mobile/small screen layout
elif rm.breakpoint == "medium":
    # Tablet layout
elif rm.breakpoint == "large":
    # Desktop layout
```

## Tool Development

### 1. Tool Structure Template
Every tool should follow this structure:

```python
# tools/YourTool/YourTool.py
"""
YourTool for Renderware Modding Suite
Brief description of what this tool does
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QGroupBox)
from PySide6.QtCore import Qt, Signal

from application.common.message_box import message_box
from application.responsive_utils import get_responsive_manager
from application.styles import ModernDarkTheme
from .your_controller import YourController


class YourTool(QWidget):
    """Your tool main widget"""
    
    # Signals for communication with main application
    tool_action = Signal(str, str)  # action_name, parameters
    status_update = Signal(str)     # status_message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = YourController()
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the user interface with responsive design"""
        rm = get_responsive_manager()
        fonts = rm.get_font_config()
        spacing = rm.get_spacing_config()
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(spacing['medium'], spacing['medium'], 
                                     spacing['medium'], spacing['medium'])
        
        # Header
        header = QLabel("🔧 Your Tool")
        header.setStyleSheet(f"""
            font-weight: bold; 
            font-size: {fonts['header']['size']}px; 
            color: {ModernDarkTheme.TEXT_PRIMARY};
            padding: {spacing['medium']}px;
        """)
        main_layout.addWidget(header)
        
        # Tool content
        self.create_tool_content(main_layout)
        
        # Apply responsive sizing
        self.setMinimumHeight(rm.get_scaled_size(400))
    
    def create_tool_content(self, parent_layout):
        """Create the main tool content"""
        # Group boxes for organization
        main_group = QGroupBox("Main Operations")
        group_layout = QVBoxLayout(main_group)
        
        # Add your tool's widgets here
        # Remember to use responsive sizing and theme colors
        
        parent_layout.addWidget(main_group)
    
    def setup_connections(self):
        """Setup signal connections"""
        # Connect controller signals
        self.controller.operation_completed.connect(self.on_operation_completed)
        self.controller.error_occurred.connect(self.on_error)
    
    def on_operation_completed(self, message):
        """Handle successful operations"""
        self.status_update.emit(message)
        message_box.info(message, "Success", self)
    
    def on_error(self, error_message):
        """Handle errors"""
        self.status_update.emit(f"Error: {error_message}")
        message_box.error(error_message, "Error", self)
```

### 2. Controller Pattern
```python
# tools/YourTool/your_controller.py
"""
Controller for YourTool business logic
Handles all non-UI operations
"""

from PySide6.QtCore import QObject, Signal
from pathlib import Path


class YourController(QObject):
    """Controller for YourTool operations"""
    
    # Signals for UI communication
    operation_completed = Signal(str)  # success_message
    error_occurred = Signal(str)       # error_message
    progress_updated = Signal(int)     # progress_percentage
    
    def __init__(self):
        super().__init__()
        self.current_file = None
    
    def load_file(self, file_path):
        """Load a file for processing"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                self.error_occurred.emit(f"File not found: {file_path}")
                return False
            
            # Your file loading logic here
            self.current_file = file_path
            self.operation_completed.emit(f"Loaded: {file_path.name}")
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to load file: {str(e)}")
            return False
    
    def process_operation(self, operation_type, parameters=None):
        """Process a specific operation"""
        try:
            if not self.current_file:
                self.error_occurred.emit("No file loaded")
                return False
            
            # Your operation logic here
            # Use progress_updated.emit(percentage) for long operations
            
            self.operation_completed.emit("Operation completed successfully")
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Operation failed: {str(e)}")
            return False
```

### 3. Tool Registration
```python
# In tools/__init__.py, add your tool:
from .YourTool.YourTool import YourTool

# In tools/tool_registry.py, register your tool:
def get_available_tools():
    return {
        "your_tool": {
            "name": "Your Tool",
            "description": "Brief description",
            "class": YourTool,
            "icon": "🔧",
            "category": "Utilities"
        }
    }
```

## File Organization

### Import Guidelines
```python
# Standard library imports first
import sys
import os
from pathlib import Path

# Third-party imports
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel)
from PySide6.QtCore import Qt, Signal

# Application imports (use relative imports within tools)
from application.common.message_box import message_box
from application.responsive_utils import get_responsive_manager
from application.styles import ModernDarkTheme

# Tool-specific imports (relative)
from .your_controller import YourController
```

### File Naming Conventions
- **Classes**: PascalCase (`YourTool`, `FileManager`)
- **Files**: snake_case (`your_tool.py`, `file_manager.py`)
- **Modules**: lowercase (`core`, `utils`)
- **Constants**: UPPER_SNAKE_CASE (`BACKGROUND_PRIMARY`)

## Best Practices

### 1. Error Handling
```python
try:
    # Risky operation
    result = some_operation()
    self.status_update.emit("Operation successful")
except FileNotFoundError:
    message_box.error("File not found", "Error", self)
except PermissionError:
    message_box.error("Permission denied", "Error", self)
except Exception as e:
    message_box.error(f"Unexpected error: {str(e)}", "Error", self)
    print(f"⚠️ Debug info: {e}")  # For development
```

### 2. Memory Management
```python
# For large file operations, use progress indicators
def process_large_file(self, file_path):
    total_size = file_path.stat().st_size
    processed = 0
    
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):  # Process in chunks
            # Process chunk
            processed += len(chunk)
            progress = int((processed / total_size) * 100)
            self.progress_updated.emit(progress)
```

### 3. User Feedback
```python
# Always provide feedback for user actions
def save_file(self):
    if self.controller.save_current_file():
        self.status_bar.show_success("File saved successfully")
    else:
        self.status_bar.show_error("Failed to save file")
```

### 4. Consistent Widget Styling
```python
def create_styled_button(self, text, action=None):
    """Create a consistently styled button"""
    rm = get_responsive_manager()
    button_size = rm.get_button_size()
    fonts = rm.get_font_config()
    
    button = QPushButton(text)
    button.setMinimumSize(button_size[0], button_size[1])
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {ModernDarkTheme.BUTTON_PRIMARY};
            color: {ModernDarkTheme.TEXT_PRIMARY};
            border: none;
            border-radius: 4px;
            font-size: {fonts['body']['size']}px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {ModernDarkTheme.BUTTON_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {ModernDarkTheme.BUTTON_PRESSED};
        }}
    """)
    
    if action:
        button.clicked.connect(action)
    
    return button
```

## Common Patterns

### 1. File Dialog Pattern
```python
def browse_file(self, filter_text="All Files (*)"):
    """Standard file browsing with error handling"""
    from PySide6.QtWidgets import QFileDialog
    
    file_path, _ = QFileDialog.getOpenFileName(
        self, 
        "Select File", 
        "", 
        filter_text
    )
    
    if file_path:
        return Path(file_path)
    return None
```

### 2. Progress Dialog Pattern
```python
def show_progress_dialog(self, title, maximum=100):
    """Standard progress dialog"""
    from PySide6.QtWidgets import QProgressDialog
    from PySide6.QtCore import Qt
    
    progress = QProgressDialog(title, "Cancel", 0, maximum, self)
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.setMinimumDuration(0)
    
    # Style the progress dialog
    progress.setStyleSheet(f"""
        QProgressDialog {{
            background-color: {ModernDarkTheme.BACKGROUND_SECONDARY};
            color: {ModernDarkTheme.TEXT_PRIMARY};
        }}
        QProgressBar {{
            background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
            border: 1px solid {ModernDarkTheme.BORDER_SECONDARY};
            border-radius: 4px;
        }}
        QProgressBar::chunk {{
            background-color: {ModernDarkTheme.TEXT_ACCENT};
            border-radius: 3px;
        }}
    """)
    
    return progress
```

### 3. Table Widget Pattern
```python
def create_data_table(self, headers):
    """Create a consistently styled table"""
    from PySide6.QtWidgets import QTableWidget, QHeaderView
    
    table = QTableWidget()
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    
    # Style the table
    rm = get_responsive_manager()
    fonts = rm.get_font_config()
    spacing = rm.get_spacing_config()
    
    table.setStyleSheet(f"""
        QTableWidget {{
            background-color: {ModernDarkTheme.BACKGROUND_SECONDARY};
            gridline-color: {ModernDarkTheme.BORDER_SECONDARY};
            border: 1px solid {ModernDarkTheme.BORDER_PRIMARY};
            font-size: {fonts['body']['size']}px;
        }}
        QTableWidget::item {{
            padding: {spacing['small']}px;
        }}
        QTableWidget::item:selected {{
            background-color: {ModernDarkTheme.TEXT_ACCENT};
        }}
        QHeaderView::section {{
            background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
            color: {ModernDarkTheme.TEXT_PRIMARY};
            padding: {spacing['small']}px;
            border: 1px solid {ModernDarkTheme.BORDER_PRIMARY};
            font-weight: bold;
        }}
    """)
    
    # Configure headers
    header = table.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    
    return table
```

## Testing & Debugging

### 1. Debug Output
```python
# Use consistent debug output format
print(f"✅ Success: {message}")
print(f"⚠️ Warning: {message}")
print(f"❌ Error: {message}")
print(f"🔧 Debug: {debug_info}")
```

### 2. Responsive Testing
```python
# Test your UI at different scales
def test_responsive_scaling(self):
    """Test UI at different scale factors"""
    rm = get_responsive_manager()
    original_scale = rm.scale_factor
    
    # Test different scales
    for scale in [0.8, 1.0, 1.25, 1.5, 2.0]:
        rm.scale_factor = scale
        self.refresh_ui()
        # Visual inspection or automated checks
    
    # Restore original scale
    rm.scale_factor = original_scale
    self.refresh_ui()
```

### 3. Memory Monitoring
```python
import psutil
import os

def get_memory_usage():
    """Get current memory usage for debugging"""
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    return f"{memory_mb:.1f} MB"
```

## Quick Reference Checklist

When creating a new tool, ensure you have:

- [ ] Used `get_responsive_manager()` for all sizing
- [ ] Used `ModernDarkTheme` constants for all colors
- [ ] Implemented proper error handling with `message_box`
- [ ] Added responsive font sizing with `fonts['type']['size']`
- [ ] Used consistent spacing with `spacing['size']`
- [ ] Followed the MVC pattern (UI, Controller, Model)
- [ ] Added proper signal connections for communication
- [ ] Implemented progress feedback for long operations
- [ ] Added tool registration in `tool_registry.py`
- [ ] Tested at different UI scales
- [ ] Added proper documentation and comments

---

**Remember**: Consistency is key! Following these guidelines ensures your tools integrate seamlessly with the existing application architecture and provide a professional, cohesive user experience.
