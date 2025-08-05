"""
Simple Build script for Renderware Modding Suite
Builds executable without reinstalling packages
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path

def build_executable_simple():
    """Build the executable using PyInstaller - simple version"""
    
    print("🔨 Building Renderware Modding Suite Executable...")
    
    # Get project paths
    project_root = Path(__file__).parent
    ApplicationDir = project_root / "application"
    venv_python = project_root / ".venv" / "Scripts" / "python.exe"
    
    if not venv_python.exists():
        print(f"❌ Virtual environment Python not found at: {venv_python}")
        return False
    
    # Clean previous builds
    dist_dir = project_root / "dist"
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print("🧹 Cleaned previous dist directory")
    
    # PyInstaller command - simple version
    pyinstaller_cmd = [
        str(venv_python), "-m", "PyInstaller",
        "--onedir",                    # Single executable
        "--windowed",                   # No console window
        "--name=RenderwareModdingSuite", # Executable name
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui", 
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=darkdetect",
        str(ApplicationDir / "main.py")   # Main entry point
    ]
    
    print("📦 Running PyInstaller...")
    print(f"Command: {' '.join(pyinstaller_cmd)}")
    
    try:
        # Change to project directory
        os.chdir(project_root)
        
        # Run PyInstaller
        result = subprocess.run(pyinstaller_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            exe_path = dist_dir / "RenderwareModdingSuite" / "RenderwareModdingSuite.exe"
            if exe_path.exists():
                exe_size = exe_path.stat().st_size / (1024 * 1024)  # Size in MB
                print(f"✅ Build successful!")
                print(f"📁 Executable created: {exe_path}")
                print(f"📏 Size: {exe_size:.1f} MB")
                return True
            else:
                print("❌ Executable not found after build")
                return False
        else:
            print("❌ PyInstaller failed:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False

def main():
    """Main build process"""
    print("🚀 Renderware Modding Suite Simple Build")
    print("=" * 50)
    
    if build_executable_simple():
        print("\n🎉 Build completed successfully!")
        print("📁 Check the 'dist' folder for your executable")
        return 0
    else:
        print("\n❌ Build failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
