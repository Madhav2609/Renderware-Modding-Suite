"""
Simplified Build script for Renderware Modding Suite
Builds executable using Nuitka in standalone mode.
"""

import subprocess
import sys
import os
from pathlib import Path

def build_executable_simple():
    """Build the executable using Nuitka - standalone mode"""
    print(" Building Renderware Modding Suite Executable with Nuitka (Standalone Mode)...")

    # Define paths
    project_root = Path(__file__).parent
    dist_dir = project_root / "dist"
    application_main = project_root / "application" / "main.py"
    icon_file = project_root / "icon.ico"
    
    # Detect if running in GitHub Actions
    is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
    
    # Determine Python executable
    if is_github_actions:
        # In GitHub Actions, use the system Python (requirements already installed)
        python_exe = sys.executable
        print(f" GitHub Actions detected, using system Python: {python_exe}")
    else:
        # Local development, try venv first, fallback to system Python
        venv_python = project_root / ".venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            python_exe = str(venv_python)
            print(f" Local development, using venv Python: {python_exe}")
        else:
            python_exe = sys.executable
            print(f" Local development, using system Python: {python_exe}")

    # Check if required files exist
    if not application_main.exists():
        print(f" Main application file not found: {application_main}")
        return False
    
    if not icon_file.exists():
        print(f" Icon file not found: {icon_file}, proceeding without icon")
        use_icon = False
    else:
        use_icon = True

    # Create dist directory if it doesn't exist
    dist_dir.mkdir(exist_ok=True)

    # Base Nuitka command
    nuitka_cmd = [
        python_exe, "-m", "nuitka",
        "--standalone",                   # Enable standalone mode
        "--assume-yes-for-downloads",     # Auto-accept downloads in CI
        f"--output-dir={dist_dir}",       # Output directory
        f"--output-filename=RenderwareModdingSuite.exe",
        "--enable-plugin=pyqt6",          # Enable PyQt6 plugin
        str(application_main)             # Main entry point
    ]
    
    # Add verbose output only for local builds (too noisy for CI)
    if not is_github_actions:
        nuitka_cmd.insert(3, "--verbose")
    
    # Add Windows-specific options
    if os.name == 'nt':  # Windows
        nuitka_cmd.append("--windows-console-mode=disable")
        
        # Add icon if available
        if use_icon:
            nuitka_cmd.append(f"--windows-icon-from-ico={icon_file}")
            nuitka_cmd.append(f"--include-data-file={icon_file}=icon.ico")

    print(f" Running Nuitka command...")
    if not is_github_actions:
        print(f"Command: {' '.join(nuitka_cmd)}")
    
    try:
        # Run the Nuitka command
        result = subprocess.run(nuitka_cmd, check=True, text=True)
        print(" Nuitka build completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f" Nuitka build failed with error code {e.returncode}")
        return False
        
    except FileNotFoundError:
        print(f" Python executable not found: {python_exe}")
        print("Make sure Python and Nuitka are properly installed.")
        return False
        
    except Exception as e:
        print(f" Unexpected error during build: {str(e)}")
        return False


if __name__ == "__main__":
    print(" Starting build process...")
    
    if build_executable_simple():
        print("\n Build completed successfully!")
        
        # Show output information
        project_root = Path(__file__).parent
        dist_dir = project_root / "dist"
        exe_path = dist_dir / "RenderwareModdingSuite.exe"
        
        if exe_path.exists():
            print(f" Executable created at: {exe_path}")
            print(f" File size: {exe_path.stat().st_size / (1024*1024):.2f} MB")
        else:
            print(" Executable file not found in expected location")
            
    else:
        print("\n Build failed")
        sys.exit(1)
