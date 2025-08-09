
# Renderware Modding Suite

**A modern, modular, and extensible modding suite for the Grand Theft Auto 3D era games (GTA III, Vice City, San Andreas).**

This suite provides a powerful and user-friendly interface for modding Renderware-based games. It is built with a focus on modularity, allowing for the easy addition of new tools and features.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Technical Details](#technical-details)
  - [RenderWare Version Detection System](#renderware-version-detection-system)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Application](#running-the-application)
- [Building from Source](#building-from-source)
- [Contributing](#contributing)
- [License](#license)

## Features

The Renderware Modding Suite is designed to be a comprehensive solution for modders.

### Core Features

- **Modern and Intuitive UI:** A sleek, dark-themed interface built with PySide6 for a smooth user experience.
- **Modular Tool System:** The application is built around a central tool registry, allowing new modding tools to be seamlessly integrated.
- **File Explorer:** An integrated file explorer for easy navigation and access to game files.
- **Real-time Memory Monitoring:** A status bar widget that displays the application's current memory usage.
- **Advanced RenderWare Support:** Comprehensive detection and analysis of DFF, TXD, and COL files with version identification across all GTA games.
- **Enhanced Filtering:** Advanced filtering capabilities by game version, file format, and RenderWare compatibility.

### Included Tools

- **IMG Editor:** A powerful tool for managing `.img` archives with comprehensive RenderWare version detection.
  - Supports both Version 1 (GTA III/VC) and Version 2 (SA) IMG archives.
  - **Advanced RenderWare Support:**
    - Automatic detection of DFF, TXD, and COL file formats
    - Version identification for all GTA games (III, VC, SA, LCS, VCS)
    - Enhanced filtering by game version and file format
    - Detailed tooltips with version information
  - **Operations:**
    - Create, open, and save archives.
    - Add, remove, and replace files within an archive.
    - Extract files from an archive.
    - Rebuild archives to optimize space.
    - Search for entries within an archive.
    - Filter entries by RenderWare version and file type.

*(More tools are planned for future releases.)*

## Architecture

The application follows a modern, modular architecture to ensure scalability and maintainability.

- **Main Application (`main_application.py`):** The core of the suite. It initializes the main window and manages the overall layout, which consists of a file explorer, a central content area, and a tools panel.
- **Tool Registry (`tool_registry.py`):** A centralized system for managing and instantiating all available modding tools. This allows for easy addition of new tools without modifying the core application logic.
- **Content Area (`content_area.py`):** The main workspace where the selected tool's UI is displayed.
- **Modular Tools (e.g., `IMG_Editor.py`):** Each tool is a self-contained module with its own UI and backend logic. This separation of concerns makes the codebase easier to manage and extend.
- **Backend Logic:** The business logic for each tool is separated from the UI, allowing for cleaner code and easier testing. For example, the IMG Editor has its logic split into `Core.py`, `File_Operations.py`, `IMG_Operations.py`, etc.

## Technical Details

- **Language:** Python 3
- **UI Framework:** PySide6
- **Styling:** A custom dark theme (`styles.py`) that uses `darkdetect` to match the system's theme.
- **Dependencies:**
  - `PySide6`: For the graphical user interface.
  - `darkdetect`: To detect the operating system's theme.
  - `psutil`: For monitoring system memory usage.

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

- Python 3.8 or higher
- Git

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

### Running the Application

Once the installation is complete, you can run the application with the following command:

```sh
python application/main.py
```

## Building from Source

You can create a standalone executable of the application using PyInstaller.

1.  **Install PyInstaller:**
    ```sh
    pip install pyinstaller
    ```

2.  **Build the executable:**
    The project includes a `.spec` file that contains the build configuration for PyInstaller.

    ```sh
    pyinstaller RenderwareModdingSuite.spec
    ```

    The final executable will be located in the `dist/RenderwareModdingSuite` directory.

## Contributing

Contributions are welcome! If you have ideas for new features, improvements, or bug fixes, please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
