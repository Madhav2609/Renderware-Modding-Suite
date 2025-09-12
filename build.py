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
        "--enable-plugin=pyqt6", 
        
        # Qt Plugins - Include all necessary plugins for styling and platform support
        "--include-qt-plugins=platforms,styles,imageformats,iconengines,geometryloaders,sceneparsers,renderers",
        
        # Qt3D specific includes for DFF Viewer
        "--include-package=PyQt6.Qt3DCore",
        "--include-package=PyQt6.Qt3DExtras", 
        "--include-package=PyQt6.Qt3DRender",
        
        # Include the entire application directory to ensure all modules are found
        f"--include-package=application",
        f"--include-package-data=application",
        
        # Memory and performance optimizations
        "--lto=no",                           # Disable LTO for faster builds
        "--jobs=4",                           # Use 4 parallel jobs
        
        
        # Auto-download dependencies
        "--assume-yes-for-downloads",         # Auto-download dependencies
        
        str(application_main)                 # Main entry point
    ]

    # Enable verbose logging if requested via CLI flag
    verbose_enabled = ("--verbose" in sys.argv) or ("-v" in sys.argv)
    if verbose_enabled:
        print("[INFO] Verbose mode enabled for Nuitka build")
        # Remove redirection so we can see all build output
        for flag in ("--windows-force-stdout-spec=nul", "--windows-force-stderr-spec=nul"):
            while flag in nuitka_cmd:
                nuitka_cmd.remove(flag)
        # Add Nuitka verbosity flags before the entrypoint (last element)
        insert_at = len(nuitka_cmd) - 1
        extra_flags = ["--verbose", "--show-modules", "--show-progress"]
        for f in extra_flags:
            nuitka_cmd.insert(insert_at, f)

    # Add icon-related options only if icon file exists
    if icon_file.exists():
        nuitka_cmd.insert(-1, f"--windows-icon-from-ico={icon_file}")
        nuitka_cmd.insert(-1, f"--include-data-file={icon_file}=icon.ico")
    else:
        print(f"[WARNING] Icon file not found: {icon_file}, building without icon")

    # Ensure schema.json for IDE Editor is bundled as data
    schema_file = project_root / "application" / "tools" / "IDE_Editor" / "schema.json"
    if schema_file.exists():
        # Map to the same relative path inside the dist so Path(__file__).parent / 'schema.json' resolves
        nuitka_cmd.insert(-1, f"--include-data-file={schema_file}=application/tools/IDE_Editor/schema.json")
    else:
        print(f"[WARNING] schema.json not found at: {schema_file}. IDE Editor may not work in the build.")

    # Ensure versionsets.json for RW version manager is bundled
    versionsets_file = project_root / "application" / "common" / "versionsets.json"
    if versionsets_file.exists():
        # Keep relative path so rw_versions.py (Path(__file__).parent) works
        nuitka_cmd.insert(-1, f"--include-data-file={versionsets_file}=application/common/versionsets.json")
    else:
        print(f"[WARNING] versionsets.json not found at: {versionsets_file}. Version mapping features may be degraded.")

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
