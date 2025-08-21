"""
Comprehensive Build script for Renderware Modding Suite
Builds executable using Nuitka with full Qt/PyQt6 support for cross-platform deployment.
"""

import subprocess
import shutil
import os
import sys
from pathlib import Path

def build_executable_comprehensive():
    """Build the executable using Nuitka"""
    print("Building Renderware Modding Suite Executable with Nuitka...")

    # Check if Nuitka is available
    try:
        subprocess.run([sys.executable, "-m", "nuitka", "--version"], 
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[ERROR] Nuitka is not installed. Please install it with: pip install nuitka")
        return False

    # Define paths
    project_root = Path(__file__).parent
    dist_dir = project_root / "dist"
    application_main = project_root / "application" / "main.py"
    
    # Use current Python executable instead of assuming virtual environment
    python_executable = sys.executable
    icon_file = project_root / "icon.ico"

    # Check if required files exist
    if not application_main.exists():
        print(f"[ERROR] Main application file not found: {application_main}")
        return False

    # Clean previous build
    if dist_dir.exists():
        print("Cleaning previous build...")
        shutil.rmtree(dist_dir)

    # Base Nuitka command
    nuitka_cmd = [
        python_executable, "-m", "nuitka",
        "--standalone",                       # Enable standalone mode
        "--windows-console-mode=disable",    # Disable console window
        f"--output-dir={dist_dir}",           # Output directory
        f"--output-filename=RenderwareModdingSuite.exe",
        
        # PyQt6 Configuration
        "--enable-plugin=pyqt6",            # Enable PyQt6 plugin
        
        # Qt Plugins - Include all necessary plugins for styling and platform support
        "--include-qt-plugins=platforms,styles,imageformats,iconengines",
        
        # Include the entire application directory to ensure all modules are found
        f"--include-package=application",
        f"--include-package-data=application",
        
        # Memory and performance optimizations
        "--lto=no",                           # Disable LTO for faster builds
        "--jobs=4",                           # Use 4 parallel jobs
        
        # Exclusions to reduce size
        "--nofollow-import-to=tkinter",       # Exclude tkinter
        "--nofollow-import-to=matplotlib",    # Exclude matplotlib if not needed
        "--nofollow-import-to=numpy",         # Exclude numpy if not needed
        "--nofollow-import-to=scipy",         # Exclude scipy if not needed
        
        # Auto-download dependencies
        "--assume-yes-for-downloads",         # Auto-download dependencies
        
        # Windows-specific optimizations
        "--windows-force-stdout-spec=nul",    # Redirect stdout
        "--windows-force-stderr-spec=nul",    # Redirect stderr
        
        str(application_main)                 # Main entry point
    ]

    # Add icon-related options only if icon file exists
    if icon_file.exists():
        nuitka_cmd.insert(-1, f"--windows-icon-from-ico={icon_file}")
        nuitka_cmd.insert(-1, f"--include-data-file={icon_file}=icon.ico")
    else:
        print(f"[WARNING] Icon file not found: {icon_file}, building without icon")

    print("Running Nuitka command...")
    print(f"Command: {' '.join(nuitka_cmd)}")
    
    try:
        # Run the Nuitka command with real-time output
        result = subprocess.run(nuitka_cmd, check=True, text=True)
        print("[SUCCESS] Nuitka build completed successfully!")
        
        # Post-build verification
        exe_path = dist_dir / "main.dist" / "RenderwareModdingSuite.exe"
        if exe_path.exists():
            print(f"[SUCCESS] Executable created at: {exe_path}")
            print(f"[INFO] Executable size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
            
        else:
            print("[ERROR] Executable not found after build")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Nuitka build failed with error code {e.returncode}")
        return False
    except FileNotFoundError:
        print("[ERROR] Python executable not found. Make sure Nuitka is installed.")
        return False



if __name__ == "__main__":
    if build_executable_comprehensive():
        print("\n[SUCCESS] Comprehensive build completed successfully!")
        print("\nDeployment Notes:")
        print("1. The executable is in dist/main.dist/")
        print("2. The entire .dist folder must be distributed together")
        print("3. Qt plugins are included for cross-platform styling")
    else:
        print("\n[ERROR] Build failed")
