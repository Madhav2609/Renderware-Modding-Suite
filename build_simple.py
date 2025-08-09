"""
Simplified Build script for Renderware Modding Suite
Builds executable using Nuitka in standalone mode.
"""

import subprocess
from pathlib import Path

def build_executable_simple():
    """Build the executable using Nuitka - standalone mode"""
    print("🔨 Building Renderware Modding Suite Executable with Nuitka (Standalone Mode)...")

    # Define paths
    project_root = Path(__file__).parent
    dist_dir = project_root / "dist"
    application_main = project_root / "application" / "main.py"
    venv_python = project_root / ".venv" / "Scripts" / "python.exe"
    icon_file = project_root / "icon.ico"

    # Nuitka command
    nuitka_cmd = [
        str(venv_python), "-m", "nuitka",
        "--standalone",                   # Enable standalone mode
        "--verbose",                   # Show detailed build output
        "--windows-console-mode=disable", # Disable console window
        f"--output-dir={dist_dir}",       # Output directory
        f"--output-filename=RenderwareModdingSuite.exe",
        "--enable-plugin=pyside6",        # Enable PySide6 plugin
        f"--windows-icon-from-ico={icon_file}",  # Set application icon
        f"--include-data-file={icon_file}=icon.ico",  # Include icon as resource
        str(application_main)             # Main entry point
    ]

    print(f"📦 Running Nuitka command: {' '.join(nuitka_cmd)}")
    
    try:
        # Run the Nuitka command with real-time output
        result = subprocess.run(nuitka_cmd, check=True, text=True)
        print("✅ Nuitka build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Nuitka build failed with error code {e.returncode}")
        return False
    except FileNotFoundError:
        print("❌ Python executable not found. Make sure the virtual environment is set up correctly.")
        return False


if __name__ == "__main__":
    if build_executable_simple():
        print("\n🎉 Build completed successfully!")
    else:
        print("\n❌ Build failed")
