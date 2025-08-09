"""
Comprehensive Build script for Renderware Modding Suite
Builds executable using Nuitka with full Qt/PySide6 support for cross-platform deployment.
"""

import subprocess
import shutil
import os
from pathlib import Path

def build_executable_comprehensive():
    """Build the executable using Nuitka"""
    print(" Building Renderware Modding Suite Executable with Nuitka...")

    # Define paths
    project_root = Path(__file__).parent
    dist_dir = project_root / "dist"
    application_main = project_root / "application" / "main.py"
    venv_python = project_root / ".venv" / "Scripts" / "python.exe"
    icon_file = project_root / "icon.ico"

    # Clean previous build
    if dist_dir.exists():
        print("Cleaning previous build...")
        shutil.rmtree(dist_dir)

    # Comprehensive Nuitka command with all Qt plugins and resources
    nuitka_cmd = [
        str(venv_python), "-m", "nuitka",
        "--standalone",                       # Enable standalone mode
        "--windows-console-mode=disable",    # Disable console window
        f"--output-dir={dist_dir}",           # Output directory
        f"--output-filename=RenderwareModdingSuite.exe",
        
        # PySide6 Configuration
        "--enable-plugin=pyside6",            # Enable PySide6 plugin
        
        # Qt Plugins - Include all necessary plugins for styling and platform support
        "--include-qt-plugins=platforms,styles,imageformats,iconengines",
        
        # Data files and resources
        f"--windows-icon-from-ico={icon_file}",  # Set application icon
        f"--include-data-file={icon_file}=icon.ico",  # Include icon as resource
        
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

    print(f" Running Nuitka command...")
    print(f"Command: {' '.join(nuitka_cmd)}")
    
    try:
        # Run the Nuitka command with real-time output
        result = subprocess.run(nuitka_cmd, check=True, text=True)
        print("✅ Nuitka build completed successfully!")
        
        # Post-build verification
        exe_path = dist_dir / "main.dist" / "RenderwareModdingSuite.exe"
        if exe_path.exists():
            print(f"✅ Executable created at: {exe_path}")
            print(f"📏 Executable size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
            
        else:
            print("❌ Executable not found after build")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Nuitka build failed with error code {e.returncode}")
        return False
    except FileNotFoundError:
        print("❌ Python executable not found. Make sure the virtual environment is set up correctly.")
        return False



if __name__ == "__main__":
    if build_executable_comprehensive():
        print("\n🎉 Comprehensive build completed successfully!")
        print("\n📋 Deployment Notes:")
        print("1. The executable is in dist/main.dist/")
        print("3. The entire .dist folder must be distributed together")
        print("4. Qt plugins are included for cross-platform styling")
    else:
        print("\n❌ Build failed")
