# Renderware Modding Suite

**A modern, modular, and extensible modding suite for the Grand Theft Auto 3D era games (GTA III, Vice City, San Andreas, Liberty City Stories, Vice City Stories).**

This suite provides a powerful and user-friendly interface for modding RenderWare-based assets. It emphasizes clean architecture, responsive UI, centralized theming, and an extensible tool registry enabling rapid addition of new modding utilities.

## Table of Contents

- [Features](#features)
- [Tool Overview](#tool-overview)
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
- [Roadmap](#roadmap)
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

## Tool Overview

### Included Tools (Current)

| Tool | Purpose | Key Capabilities |
|------|---------|------------------|
| IMG Editor | Manage GTA IMG archives | Multi-archive tabs, v1/v2 IMG formats, batch import/export, RW version scanning, COL detection |
| TXD Editor | View & inspect texture dictionaries | Multi-TXD tabs, texture list & metadata, preview, info dialogs (editing WIP) |
| DFF Viewer | Inspect 3D models | Qt3D rendering, camera navigation, axis gizmo, material/color extraction |
| RW Analyze | Low-level RW chunk exploration | Recursive chunk tree, header info, version mapping, corruption detection |
| IDE Editor | Edit item definition files | Schema-driven parsing, structured + raw view, collapsible sections, edit tracking |
| Debug System | Unified logging & metrics | Categorized logs, timers, memory tracking, file session logs |

### Highlighted Tool Details

**IMG Editor**
- Multi-archive tab system (open many IMG simultaneously)
- Version 1 & 2 support (III/VC vs SA) with automatic detection
- RW-aware filtering: by file type (DFF/TXD/COL) and game version
- Batch import (files/folders), export (selected/all), deletion & restoration tracking
- Progress dialogs with cancellation
- RenderWare version summary dashboard (counts by game & format)

**TXD Editor**
- Multiple TXDs opened in tabs
- Texture table: name, platform flags, dimensions
- Info dialog summarizing statistics
- Planned: texture replacement/export/compression tooling (see Roadmap)

**DFF Viewer**
- Hardware-accelerated Qt3D rendering
- Orbit / pan / zoom + reset & focus-on-bounds
- Geometry + material extraction with axis gizmo

**RW Analyze**
- Generic chunk parser (DFF / TXD / COL / others)
- Recursive tree with type, size, offset, decoded version & game
- Corruption detection (size boundary checks) + performance timers

**IDE Editor**
- Schema-driven structured sections with collapsible panels
- Raw view toggle for direct editing
- Row add/delete, dirty-state tracking, planned validation improvements

**Debug System**
- TRACE→CRITICAL levels with category tagging (SYSTEM, UI, FILE_IO, TOOL, MEMORY, PERFORMANCE, USER_ACTION)
- Performance timers + memory sampling integrated with status bar
- Colored console + per-session log files in `logs/`

*(Architecture supports rapid addition of new tools; see `CODING_GUIDELINES.md`.)*

## Architecture

The application follows a modern, modular architecture to ensure scalability and maintainability.

- **Main Application (`main_application.py`):** The core application with comprehensive window management, menu system, and component coordination. Features system-independent theme enforcement, memory monitoring, and advanced UI scaling controls.
- **Theme System (`styles.py`):** Centralized theming with `ModernDarkTheme` class providing 30+ color constants and system palette override for consistent dark theme across all platforms.
- **Responsive Design (`responsive_utils.py`):** Complete responsive design system with breakpoint detection, DPI awareness, font scaling, and adaptive component sizing for optimal experience across all screen sizes.
- **Debug System (`debug_system.py`):** Professional logging system with categorized output, performance timers, memory tracking, and colored terminal output for comprehensive development and troubleshooting support.
- **Tool Registry (`tool_registry.py`):** Centralized tool management system supporting dynamic tool registration, instantiation, and metadata management (currently registers IMG Editor, TXD Editor, DFF Viewer, RW Analyze, IDE Editor).
- **Content Area (`content_area.py`):** Advanced tabbed workspace with tool lifecycle management, cleanup handling, and seamless switching between different tool interfaces.
- **File Explorer (`file_explorer.py`):** Integrated file browser with responsive design and file selection capabilities for easy navigation of game assets.
- **Tools Panel (`tools_panel.py`):** Dynamic tools sidebar that adapts to available tools and provides quick access to all modding utilities.
- **Status Bar (`status_bar.py`):** Comprehensive status display with memory usage monitoring, file information, and operation feedback.
- **Modular Tools:** Each tool follows an MVC-inspired separation (UI + controller/logic where needed) and integrates with logging + responsive systems:
  - IMG Editor (`tools/IMG_Editor/`)
  - TXD Editor (`tools/TXD_Editor/`)
  - DFF Viewer (`tools/DFF_Viewer/`)
  - RW Analyze (`tools/RW_Analyze/`)
  - IDE Editor (`tools/IDE_Editor/`)
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

See `CODING_GUIDELINES.md` for detailed architecture, style, and tool scaffolding guidance. This README focuses on high-level orientation.

### Key Development Resources

- Architecture & Patterns: `CODING_GUIDELINES.md`
- Theme System: `styles.py` (`ModernDarkTheme`)
- Responsive Design: `responsive_utils.py`
- Tool Registry: `tools/tool_registry.py`
- RW Versioning: `common/rw_versions.py`
- DFF Parser: `common/DFF.py`
- TXD Parser: `common/txd.py`

### Current Tool Architecture (Abridged)

```
tools/IMG_Editor/
├── IMG_Editor.py          # Main UI coordinator
├── img_controller.py      # Archive logic
├── ui_interaction_handlers.py
├── img_editor_tool.py
├── core/
│   ├── Core.py
│   ├── IMG_Operations.py
│   ├── Import_Export.py
│   └── File_Operations.py

tools/TXD_Editor/
├── TXD_Editor.py          # Multi-TXD interface
├── core/
│   ├── TXD_Operations.py
│   └── File_Operations.py

tools/RW_Analyze/
├── RW_Analyze.py
├── RW_Analyze_core.py

tools/IDE_Editor/
├── IDE_Editor.py
├── IDE_core.py

tools/DFF_Viewer/
├── DFF_Viewer.py
```

### Quick Start for New Tools

1. Start minimal (look at `RW_Analyze`) or scaffold complexity (like `IMG_Editor`).
2. Separate controller/business logic when operations grow (> single file UI).
3. Use `get_responsive_manager()` for every size/font/spacing decision.
4. Use only `ModernDarkTheme` constants. No hardcoded colors.
5. Add signals for integration (`tool_action`, domain-specific events).
6. Register in `tool_registry.py` with name, description, icon.
7. Use `get_debug_logger()` with categories + performance timers.
8. Provide `cleanup()` for long-lived resources.
9. Test under varying DPI/scale factors (0.8–2.0) & resolutions.
10. Document module header (purpose + interactions).

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
6. **Update Docs:** If you add a capability or tool, update README + guidelines

### Types of Contributions

- **New Tools:** Create additional modding tools following the established patterns
- **Bug Fixes:** Fix issues in existing functionality
- **UI Improvements:** Enhance the user interface and experience
- **Performance Optimizations:** Improve application performance and memory usage
- **Documentation:** Improve or expand documentation and examples

## Roadmap

Short-term (Active):
- TXD texture export & replacement workflow
- IDE Editor validation rules & auto-fix suggestions
- RW Analyze: hex pane + export selected chunk
- IMG Editor: async background indexing & parsing improvements

Mid-term:
- Batch DFF statistics / optimization tool
- COL viewer & editor integration
- Plugin / script API for external extensions
- Texture compression analysis & conversion helpers

Long-term / Exploration:
- Cross-platform binary packaging (Linux/macOS artifacts)
- 3D material/texture binding in DFF Viewer
- In-app update checker

Have an idea? Open an issue and label it enhancement.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
