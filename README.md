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

- **Modern and Intuitive UI:** A sleek, dark-themed interface built with PySide6 that enforces consistent theming regardless of system settings.
- **Responsive Design:** Adaptive UI that automatically adjusts to different screen sizes, DPI settings, and scaling factors.
- **System-Independent Theming:** Dark theme that works consistently across all operating systems without depending on system theme settings.
- **Modular Tool System:** The application is built around a central tool registry, allowing new modding tools to be seamlessly integrated.
- **File Explorer:** An integrated file explorer for easy navigation and access to game files.
- **Real-time Memory Monitoring:** A status bar widget that displays the application's current memory usage.
- **Advanced RenderWare Support:** Comprehensive detection and analysis of DFF, TXD, and COL files with version identification across all GTA games.
- **Enhanced Filtering:** Advanced filtering capabilities by game version, file format, and RenderWare compatibility.
- **Professional Architecture:** Clean separation of concerns with MVC pattern, making the codebase maintainable and extensible.

### Included Tools

- **IMG Editor:** A powerful tool for managing `.img` archives with comprehensive RenderWare version detection and modern tabbed interface.
  - **Multi-Archive Support:** Open and manage multiple IMG archives simultaneously with tabbed interface.
  - **Archive Format Support:** Both Version 1 (GTA III/VC) and Version 2 (SA) IMG archives.
  - **Advanced RenderWare Support:**
    - Automatic detection of DFF, TXD, and COL file formats
    - Version identification for all GTA games (III, VC, SA, LCS, VCS)
    - Enhanced filtering by game version and file format
    - Detailed tooltips with version information
    - Real-time analysis of archive contents
  - **Operations:**
    - Create, open, and save archives
    - Add, remove, and replace files within archives
    - Extract files from archives with organized output
    - Rebuild archives to optimize space
    - Advanced search and filtering capabilities
    - Multi-selection operations for batch processing
  - **User Experience:**
    - Responsive design that adapts to screen size
    - Consistent dark theme throughout interface
    - Progress indicators for long operations
    - Comprehensive error handling and user feedback
    - Context-sensitive help and tooltips

*(More tools are planned for future releases. See `CODING_GUIDELINES.md` for tool development standards.)*

## Architecture

The application follows a modern, modular architecture to ensure scalability and maintainability.

- **Main Application (`main_application.py`):** The core of the suite with system-independent theme enforcement. It initializes the main window and manages the overall layout, which consists of a file explorer, a central content area, and a tools panel.
- **Theme System (`styles.py`):** Centralized theming with `ModernDarkTheme` class that provides consistent colors and styling across all components, independent of system theme settings.
- **Responsive Design (`responsive_utils.py`):** Comprehensive responsive design system that adapts to different screen sizes, DPI settings, and user scaling preferences.
- **Tool Registry (`tool_registry.py`):** A centralized system for managing and instantiating all available modding tools. This allows for easy addition of new tools without modifying the core application logic.
- **Content Area (`content_area.py`):** The main workspace where the selected tool's UI is displayed with tabbed interface support.
- **Modular Tools (e.g., `IMG_Editor/`):** Each tool is a self-contained module following MVC pattern with separated UI and business logic components.
- **Backend Logic:** The business logic for each tool is separated from the UI using controller classes, allowing for cleaner code and easier testing.
- **Common Utilities (`common/`):** Shared components like message dialogs and RenderWare version detection that maintain consistency across tools.

## Technical Details

- **Language:** Python 3.8+
- **UI Framework:** PySide6
- **Styling:** A custom dark theme system (`styles.py`) with system-independent theme enforcement.
- **Responsive Design:** Adaptive UI that scales properly across different screen sizes and DPI settings.
- **Architecture:** Modular MVC pattern with separation of UI, business logic, and data management.
- **Dependencies:**
  - `PySide6`: For the graphical user interface.
  - `psutil`: For monitoring system memory usage.
  - `nuitka`: For building optimized executables (optional).
  - `darkdetect`: Legacy dependency (no longer used - theme is now system-independent).

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

All detection logic is centralized in `application/common/rw_versions.py` for consistency across tools.

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
    nuitka --standalone --onefile --enable-plugin=pyside6,qt-plugins application/main.py
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

### Quick Start for New Tools

1. Follow the tool template in `CODING_GUIDELINES.md`
2. Use `get_responsive_manager()` for all sizing and spacing
3. Use `ModernDarkTheme` constants for all colors
4. Implement the controller pattern for business logic
5. Register your tool in `tool_registry.py`

Example tool structure:
```
tools/YourTool/
├── __init__.py
├── YourTool.py           # UI implementation
├── your_controller.py    # Business logic
└── core/                 # Tool-specific utilities
```

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
