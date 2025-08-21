# Renderware Modding Suite

**A modern, modular, and extensible modding suite for the Grand Theft Auto 3D era games (GTA III, Vice City, San Andreas).**

This suite provides a powerful and user-friendly interface for modding Renderware-based games. It is built with a focus on modularity, allowing for the easy addition of new tools and features.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Technical Details](#technical-details)
  - [RenderWare Version Detection System](#renderware-version-detection-system)
  - [Theme System](#theme-system)
  - [Responsive Design](#responsive-design)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Application](#running-the-application)
- [Building from Source](#building-from-source)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Features

The Renderware Modding Suite is designed to be a comprehensive solution for modders.

### Core Features

- **Modern and Intuitive UI:** A sleek, dark-themed interface built with PyQt6 that enforces consistent theming regardless of system settings.
- **Responsive Design:** Adaptive UI that automatically adjusts to different screen sizes, DPI settings, and scaling factors.
- **System-Independent Theming:** Dark theme that works consistently across all operating systems without depending on system theme settings.
- **Modular Tool System:** The application is built around a central tool registry, allowing new modding tools to be seamlessly integrated.
- **File Explorer:** An integrated file explorer for easy navigation and access to game files.
- **Real-time Memory Monitoring:** A status bar widget that displays the application's current memory usage.
- **Advanced RenderWare Support:** Comprehensive detection and analysis of DFF, TXD, and COL files with version identification across all GTA games.
- **Enhanced Filtering:** Advanced filtering capabilities by game version, file format, and RenderWare compatibility.
- **Professional Architecture:** Clean separation of concerns with MVC pattern, making the codebase maintainable and extensible.

### Included Tools

- **IMG Editor:** A comprehensive tool for managing `.img` archives with multi-archive tabbed interface and advanced RenderWare analysis.
  - **Multi-Archive Support:** Open and manage multiple IMG archives simultaneously with dedicated tabs for each archive.
  - **Archive Format Support:** Both Version 1 (GTA III/VC) and Version 2 (SA) IMG archives with full compatibility.
  - **Advanced RenderWare Detection:**
    - Automatic detection of DFF, TXD, and COL file formats with version identification
    - Support for all GTA games (III, VC, SA, LCS, VCS) with specific version detection
    - Enhanced filtering by game version, file format, and RenderWare compatibility
    - Real-time RenderWare version analysis with detailed breakdowns
    - COL file format detection (COL1, COL2, COL3, COL4)
  - **Archive Operations:**
    - Create new archives with version selection
    - Open single or multiple archives simultaneously
    - Import files, folders, or via IDE with preview functionality
    - Extract selected entries or entire archives with organized output
    - Delete entries with modification tracking and restore capabilities
    - Export operations with type filtering and preview
  - **Advanced Features:**
    - Comprehensive search and filtering with multiple criteria
    - Multi-selection operations for batch processing
    - Modification tracking with detailed status reporting
    - Progress indicators with cancellation support
    - Archive validation and integrity checking
  - **User Experience:**
    - Tabbed interface for managing multiple archives
    - Responsive table with sortable columns and alternating row colors
    - Real-time filtering with search, type, and RenderWare version filters
    - Context menus and keyboard shortcuts
    - Comprehensive error handling with detailed feedback

- **DFF Viewer:** A professional 3D model viewer with interactive inspection and advanced rendering capabilities.
  - **3D Rendering Engine:** Built on Qt3D with hardware-accelerated rendering and professional lighting setup.
  - **Model Support:**
    - Native DFF (RenderWare 3D model) file support with full geometry parsing
    - OBJ file support for standard 3D models
    - Automatic model bounds detection and camera positioning
  - **Interactive Navigation:**
    - Blender-style camera controls with mouse and keyboard navigation
    - Orbit, pan, and zoom operations with visual feedback
    - Customizable camera positioning with distance, azimuth, and elevation controls
    - Reset view and focus-on-bounds functionality
  - **Advanced Features:**
    - Interactive model inspector with geometry highlighting
    - Three-point lighting system (key, fill, rim lights) for professional visualization
    - Material override system for consistent model viewing
    - Background color customization
    - Real-time model reloading for development workflows
  - **Rendering Features:**
    - Hardware-accelerated rendering with proper vertex/normal/UV handling
    - Support for RenderWare frame hierarchies and transformations
    - Material color extraction from DFF files
    - Axis gizmo for spatial reference
  - **Integration:**
    - Seamless integration with suite's responsive design system
    - Debug logging integration for development and troubleshooting
    - Tool action signals for communication with main application

- **Debug System:** Comprehensive logging and monitoring system for development and troubleshooting.
  - **Multi-Level Logging:** Support for TRACE, DEBUG, INFO, WARNING, ERROR, and CRITICAL levels
  - **Categorized Logging:** Organized by SYSTEM, UI, FILE_IO, TOOL, MEMORY, PERFORMANCE, USER_ACTION categories
  - **Performance Monitoring:** Built-in performance timers for operation profiling
  - **Memory Tracking:** Real-time memory usage monitoring and logging
  - **File Logging:** Automatic log file generation with session tracking
  - **Colored Terminal Output:** Enhanced readability with color-coded log levels

*(The application architecture supports easy addition of new tools. See `CODING_GUIDELINES.md` for tool development standards.)*

## Architecture

The application follows a modern, modular architecture to ensure scalability and maintainability.

- **Main Application (`main_application.py`):** The core application with comprehensive window management, menu system, and component coordination. Features system-independent theme enforcement, memory monitoring, and advanced UI scaling controls.
- **Theme System (`styles.py`):** Centralized theming with `ModernDarkTheme` class providing 30+ color constants and system palette override for consistent dark theme across all platforms.
- **Responsive Design (`responsive_utils.py`):** Complete responsive design system with breakpoint detection, DPI awareness, font scaling, and adaptive component sizing for optimal experience across all screen sizes.
- **Debug System (`debug_system.py`):** Professional logging system with categorized output, performance timers, memory tracking, and colored terminal output for comprehensive development and troubleshooting support.
- **Tool Registry (`tool_registry.py`):** Centralized tool management system supporting dynamic tool registration, instantiation, and metadata management for seamless tool integration.
- **Content Area (`content_area.py`):** Advanced tabbed workspace with tool lifecycle management, cleanup handling, and seamless switching between different tool interfaces.
- **File Explorer (`file_explorer.py`):** Integrated file browser with responsive design and file selection capabilities for easy navigation of game assets.
- **Tools Panel (`tools_panel.py`):** Dynamic tools sidebar that adapts to available tools and provides quick access to all modding utilities.
- **Status Bar (`status_bar.py`):** Comprehensive status display with memory usage monitoring, file information, and operation feedback.
- **Modular Tools:** Each tool follows MVC architecture with separated concerns:
  - **IMG Editor (`IMG_Editor/`):** Multi-archive management with tabbed interface, advanced filtering, and RenderWare analysis
  - **DFF Viewer (`DFF_Viewer/`):** 3D model viewer with Qt3D rendering, interactive navigation, and professional lighting
- **Common Utilities (`common/`):** Shared components including:
  - **DFF Parser (`DFF.py`):** Complete RenderWare DFF file format parser with geometry, material, and animation support
  - **RenderWare Versions (`rw_versions.py`):** Comprehensive version detection for all GTA games and file formats
  - **Message Box (`message_box.py`):** Standardized dialog system with theme consistency

## Technical Details

- **Language:** Python 3.8+
- **UI Framework:** PyQt6
- **Styling:** A custom dark theme system (`styles.py`) with system-independent theme enforcement.
- **Responsive Design:** Adaptive UI that scales properly across different screen sizes and DPI settings.
- **Architecture:** Modular MVC pattern with separation of UI, business logic, and data management.
- **Dependencies:**
  - `PyQt6`: Complete GUI framework including Qt3D for 3D rendering capabilities
  - `psutil`: System monitoring for memory usage tracking and performance analysis
  - `nuitka`: Build system for creating optimized standalone executables (optional)
  - `colorama`: Terminal color support for enhanced debug output readability
  - `darkdetect`: Legacy dependency (retained for compatibility, theme is now system-independent)

### RenderWare Version Detection System

The suite includes a comprehensive RenderWare version detection system that provides advanced support for analyzing game files:

#### Supported File Formats
- **DFF (3D Models):** Complete support for all GTA games with section type detection (0x0010 CLUMP)
- **TXD (Texture Dictionaries):** Full RenderWare version extraction with section type detection (0x0016 TEXDICTIONARY)
- **COL (Collision Files):** Support for all COL variants with FourCC signature detection:
  - **COL1:** FourCC 'COLL' (GTA III, Vice City)
  - **COL2:** FourCC 'COL2' (GTA San Andreas)
  - **COL3:** FourCC 'COL3' (GTA SA Advanced)
  - **COL4:** FourCC 'COL4' (Extended format)

#### Game Version Support
- **GTA III:** RenderWare 3.1.0.1 (0x31001)
- **Vice City:** RenderWare 3.3.0.2 (0x33002)
- **San Andreas:** RenderWare 3.6.0.3 (0x36003) / 3.4.0.3 (0x34003)
- **Liberty City Stories:** RenderWare 3.5.0.0 (0x35000)
- **Vice City Stories:** RenderWare 3.5.0.2 (0x35002)

#### Key Features
- **Smart Detection Algorithm:** Analyzes file headers to determine format and version
- **Performance Optimized:** Header-only analysis for fast processing
- **Advanced Filtering:** Filter IMG archives by game version, file format, and COL type
- **Detailed Information:** Enhanced tooltips and version breakdown statistics
- **Error Handling:** Graceful failure handling for corrupted or unknown files

#### Technical Implementation
The system uses a multi-stage detection approach:
1. **COL Files:** FourCC signature detection for collision files
2. **RenderWare Files:** Section type + version analysis for DFF/TXD files
3. **Fallback Detection:** Generic file type identification for unknown formats

All detection logic is centralized in `application/common/rw_versions.py` for consistency across tools, with comprehensive support for both standard RenderWare files and collision formats.

### Theme System

The application features a comprehensive theme system designed to provide a consistent, professional dark theme experience across all platforms and system configurations.

#### Key Features
- **System Independence:** The theme works consistently regardless of OS theme settings (Windows dark/light mode, Linux themes, etc.)
- **Centralized Management:** All colors and styling are managed through the `ModernDarkTheme` class in `styles.py`
- **Palette Override:** Uses Qt's palette system to ensure even system-drawn widgets follow the dark theme
- **No Hardcoded Colors:** All UI components use theme constants for maintainable and consistent styling


### Responsive Design

The application implements a comprehensive responsive design system that ensures optimal user experience across different screen sizes and DPI settings.

#### Responsive Manager
The `get_responsive_manager()` provides centralized responsive utilities:
- **DPI Awareness:** Automatically detects and adapts to different DPI settings
- **Screen Size Detection:** Identifies screen size categories (small, medium, large)
- **Scale Factor Calculation:** Provides appropriate scaling for UI elements
- **Breakpoint System:** Responsive breakpoints for different layout arrangements

#### Key Features
- **Font Scaling:** Automatic font size adjustment based on screen DPI and user preferences
- **Spacing Management:** Consistent spacing that scales appropriately across different screens
- **Component Sizing:** Buttons, panels, and other components adapt to screen size
- **Layout Adaptation:** UI layouts adjust for optimal space usage on different screen sizes

#### Usage Example
```python
from application.responsive_utils import get_responsive_manager

rm = get_responsive_manager()
fonts = rm.get_font_config()
spacing = rm.get_spacing_config()

# Apply responsive sizing
label.setStyleSheet(f"font-size: {fonts['header']['size']}px;")
layout.setContentsMargins(spacing['medium'], spacing['small'], spacing['medium'], spacing['small'])
```

#### Usage Examples

**Basic Version Detection:**
```python
from application.common.rw_versions import detect_rw_file_format

# Detect file format and version from binary data
file_format, version_desc, version_num = detect_rw_file_format(data, "model.dff")
print(f"Format: {file_format}, Version: {version_desc}")
# Output: Format: DFF, Version: DFF (3.6.0.3)
```

**COL File Detection:**
```python
from application.common.rw_versions import get_col_version_info

# Analyze COL collision files
version_name, version_num = get_col_version_info(col_data)
print(f"COL Version: {version_name}")
# Output: COL Version: COL2 (GTA SA)
```

**IMG Archive Analysis:**
```python
# Automatic version analysis when loading IMG files in the editor
archive.analyze_all_entries_rw_versions()
summary = archive.get_rw_version_summary()
print(f"RenderWare files: {summary['renderware_files']}")
```

## Getting Started

Follow these instructions to get the Renderware Modding Suite up and running on your local machine.

### Prerequisites

- **Python 3.8 or higher** (Python 3.9+ recommended for optimal performance)
- **Git** (for cloning the repository)
- **Operating System:** Windows 10/11, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Memory:** At least 4GB RAM (8GB recommended for large archive operations)
- **Display:** Minimum 1280x720 resolution (application is responsive and adapts to different screen sizes)

### Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/your-username/GTA-Renderware-Modding-Suite.git
    cd GTA-Renderware-Modding-Suite
    ```

2.  **Create and activate a virtual environment:**
    ```sh
    # For Windows
    python -m venv .venv
    .venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the required packages:**
    ```sh
    pip install -r requirements.txt
    ```

**Note:** For building standalone executables, you can use the included build script:
```sh
python build.py
```

### Running the Application

Once the installation is complete, you can run the application with the following command:

```sh
python -m application.main
```

The application will start with:
- **Welcome Screen:** Initial interface with tool selection
- **Memory Monitoring:** Real-time memory usage display in status bar
- **Responsive UI:** Automatically adapted to your screen size and DPI
- **Debug Logging:** Comprehensive logging to terminal and log files
- **Menu System:** Full menu bar with keyboard shortcuts and zoom controls

## Building from Source

You can create a standalone executable of the application using the included build system.

### Using the Build Script

The project includes a comprehensive build script (`build.py`) that handles the entire build process:

```sh
python build.py
```

This script will:
- Install build dependencies (Nuitka)
- Create an optimized executable with all required files
- Generate a standalone distribution in the `build/` directory

### Manual Nuitka Build

Alternatively, you can use Nuitka manually for building:

1.  **Install Nuitka:**
    ```sh
    pip install nuitka
    ```

2.  **Build the executable:**
    ```sh
    nuitka --standalone --onefile --enable-plugin=PyQt6,qt-plugins application/main.py
    ```

    The final executable will be located in the `dist/` directory.

## Development

### For Developers

If you're planning to extend the application or create new tools, please refer to the comprehensive development documentation:

- **`CODING_GUIDELINES.md`** - Complete coding standards, architecture patterns, and tool development guidelines
- **`DEPLOYMENT_GUIDE.md`** - Deployment and distribution information

### Key Development Resources

- **Architecture Patterns:** MVC pattern with clear separation of UI, controllers, and business logic
- **Theme System:** Centralized theming with `ModernDarkTheme` class
- **Responsive Design:** `responsive_utils.py` for adaptive UI design
- **Tool Development:** Standardized patterns for creating new modding tools
- **Testing Guidelines:** Best practices for testing and debugging

### Current Tool Architecture

The application currently includes two fully implemented tools:

**IMG Editor Structure:**
```
tools/IMG_Editor/
├── __init__.py
├── IMG_Editor.py              # Main UI with tabbed interface
├── img_controller.py          # Business logic and archive management
├── ui_interaction_handlers.py # UI event handlers
├── progress_dialog.py         # Progress reporting
└── core/                      # Archive processing utilities
```

**DFF Viewer Structure:**
```
tools/DFF_Viewer/
├── __init__.py
├── DFF_Viewer.py             # 3D viewer with Qt3D integration
└── (integrated controller)    # Business logic within main class
```

### Quick Start for New Tools

1. Follow the established patterns from existing tools
2. Use `get_responsive_manager()` for all sizing and spacing
3. Use `ModernDarkTheme` constants for all colors
4. Implement the MVC pattern with separated UI and controller
5. Register your tool in `tool_registry.py`
6. Use the debug system for logging and performance monitoring
7. Follow the cleanup patterns for proper resource management

## Contributing

Contributions are welcome! If you have ideas for new features, improvements, or bug fixes, please feel free to open an issue or submit a pull request.

### Before Contributing

Please review the development documentation:
- **`CODING_GUIDELINES.md`** - Comprehensive coding standards and architecture patterns
- **`DEPLOYMENT_GUIDE.md`** - Build and deployment procedures

### Contribution Guidelines

1. **Follow the Architecture:** Use the established MVC pattern and modular design
2. **Maintain Theme Consistency:** Use `ModernDarkTheme` constants for all styling
3. **Implement Responsive Design:** Use `responsive_utils.py` for all sizing and spacing
4. **Write Clean Code:** Follow the coding standards in the guidelines document
5. **Test Thoroughly:** Ensure your changes work across different screen sizes and DPI settings

### Types of Contributions

- **New Tools:** Create additional modding tools following the established patterns
- **Bug Fixes:** Fix issues in existing functionality
- **UI Improvements:** Enhance the user interface and experience
- **Performance Optimizations:** Improve application performance and memory usage
- **Documentation:** Improve or expand documentation and examples

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
