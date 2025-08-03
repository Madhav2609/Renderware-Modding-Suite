"""
Backend Manager for Renderware Modding Suite
Handles communication with the C++ backend
"""

import os
import sys
import subprocess


class BackendManager:
    """Manages communication with the C++ backend"""
    
    def __init__(self):
        self.backend_path = self._find_backend_executable()
    
    def _find_backend_executable(self):
        """Find the backend executable"""
        # Check if running as PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            bundle_dir = sys._MEIPASS
            backend_path = os.path.join(bundle_dir, 'backend', 'renderware_backend.exe')
        else:
            # Running as script
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            backend_path = os.path.join(project_root, 'backend', 'build', 'bin', 'Debug', 'renderware_backend.exe')
        
        if os.path.exists(backend_path):
            print(f"✅ Backend found at: {backend_path}")
            return backend_path
        else:
            print(f"❌ Backend not found at: {backend_path}")
            return None
    
    def run_command(self, command, *args):
        """Run a command with the backend"""
        if not self.backend_path:
            return False, "Backend executable not found"
        
        try:
            cmd = [self.backend_path, command] + list(args)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr
        except subprocess.TimeoutExpired:
            return False, "Backend command timed out"
        except Exception as e:
            return False, f"Backend error: {str(e)}"
    
    def test_backend(self):
        """Test if backend is working"""
        return self.run_command("test")
    
    def list_formats(self):
        """Get list of supported formats"""
        return self.run_command("formats")
    
    def load_file(self, file_path, file_type):
        """Load a file using the backend"""
        command_map = {
            'dff': 'load_dff',
            'txd': 'load_txd', 
            'col': 'load_col',
            'ifp': 'load_ifp',
            'ide': 'load_ide',
            'ipl': 'load_ipl'
        }
        
        command = command_map.get(file_type.lower())
        if command:
            return self.run_command(command, file_path)
        else:
            return False, f"Unsupported file type: {file_type}"
