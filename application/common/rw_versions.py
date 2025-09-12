"""
RenderWare Version Management System
Leverages DFF.py version extraction functions and versionsets.json for version handling

Enhanced Version Display Features:
- Shows platform information: "3.6.0.3 (San Andreas) All / (Manhunt) PC"
- Handles version conflicts: "3.4.0.3 (Vice City) PC / (GTA 3) Mobile"  
- Groups platforms intelligently: "All" for 3+ platforms, individual listing for 1-2
- Maintains backwards compatibility with existing APIs
- Supports both basic and enhanced version strings
"""

import json
import os
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Import the DFF module for version extraction functionality
try:
    from . import DFF
except ImportError:
    import DFF


class RWVersionManager:
    """RenderWare Version Manager using DFF.py functions and versionsets.json data"""
    
    def __init__(self, versionsets_file: Optional[str] = None):
        """Initialize the version manager with versionsets data"""
        self._versionsets_data = None
        self._platform_info = None
        
        # Default path to versionsets file
        if versionsets_file is None:
            current_dir = Path(__file__).parent
            versionsets_file = current_dir / "versionsets.json"
        
        self._load_versionsets(versionsets_file)
    
    def _load_versionsets(self, filepath: str):
        """Load versionsets data from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._versionsets_data = data.get('version_sets', [])
                self._platform_info = data.get('platform_info', {})
        except Exception as e:
            print(f"Warning: Could not load versionsets data from {filepath}: {e}")
            self._versionsets_data = []
            self._platform_info = {}
    
    def get_rw_version(self, library_id: Optional[int] = None) -> int:
        """Extract RW version using DFF.py function"""
        return DFF.Sections.get_rw_version(library_id)
    
    def get_library_id(self, version: int, build: int) -> int:
        """Get library ID using DFF.py function"""
        return DFF.Sections.get_library_id(version, build)
    
    def set_library_id(self, version: int, build: int):
        """Set library ID using DFF.py function"""
        DFF.Sections.set_library_id(version, build)
    
    def version_string_to_hex(self, version_str: str) -> int:
        """Convert version string like '3.6.0.3' to hex value like 0x36003"""
        try:
            parts = version_str.split('.')
            if len(parts) >= 3:
                major = int(parts[0])
                minor = int(parts[1])
                patch1 = int(parts[2])
                patch2 = int(parts[3]) if len(parts) > 3 else 0
                
                # Convert to hex format used by RenderWare
                return (major << 16) | (minor << 12) | (patch1 << 8) | patch2
        except (ValueError, IndexError):
            pass
        return 0
    
    def hex_to_version_string(self, version_hex: int) -> str:
        """Convert hex version to string format"""
        major = (version_hex >> 16) & 0xFF
        minor = (version_hex >> 12) & 0xF
        patch1 = (version_hex >> 8) & 0xF
        patch2 = version_hex & 0xFF
        
        if patch2 > 0:
            return f"{major}.{minor}.{patch1}.{patch2}"
        else:
            return f"{major}.{minor}.{patch1}.0"
    
    def get_version_info(self, version_value: int) -> Dict[str, Any]:
        """Get detailed version information"""
        version_str = self.hex_to_version_string(version_value)
        
        # Find matching game/set information
        game_info = self.find_game_by_version(version_value)
        all_games_info = self.find_all_games_by_version(version_value)
        
        return {
            'version_hex': f"0x{version_value:X}",
            'version_string': version_str,
            'version_display_string': self.get_version_display_string(version_value),
            'version_value': version_value,
            'is_valid': self.is_valid_rw_version(version_value),
            'game_info': game_info,  # First match for backward compatibility
            'all_games_info': all_games_info,  # All matches
            'platforms_info': self._platform_info
        }
    
    def is_valid_rw_version(self, version_value: int) -> bool:
        """Check if RenderWare version value is valid"""
        # Check if it's in the typical RW version range
        if 0x30000 <= version_value <= 0x3FFFF:
            return True
        
        # Check extended format versions
        extended_formats = [0x0800FFFF, 0x1003FFFF, 0x1005FFFF, 0x1401FFFF, 0x1400FFFF, 0x1803FFFF, 0x1C020037]
        if version_value in extended_formats:
            return True
        
        return False
    
    def find_game_by_version(self, version_value: int) -> Optional[Dict[str, Any]]:
        """Find game/set information by RW version (returns first match for backward compatibility)"""
        matches = self.find_all_games_by_version(version_value)
        return matches[0] if matches else None
    
    def find_all_games_by_version(self, version_value: int) -> List[Dict[str, Any]]:
        """Find all game/set information matching a RW version"""
        version_str = self.hex_to_version_string(version_value)
        matches = []
        
        for game_set in self._versionsets_data:
            for platform in game_set.get('platforms', []):
                is_match = False
                match_info = {
                    'name': game_set.get('name'),
                    'display_name': game_set.get('display_name', game_set.get('name')),
                    'icon_name': game_set.get('icon_name'),
                    'platform': platform.get('platform'),
                    'data_types': platform.get('data_types', [])
                }
                
                # Check exact version match
                if platform.get('rw_version') == version_str:
                    is_match = True
                
                # Check if version is within range
                elif platform.get('rw_version_min') and platform.get('rw_version_max'):
                    min_ver = platform.get('rw_version_min')
                    max_ver = platform.get('rw_version_max')
                    min_hex = self.version_string_to_hex(min_ver)
                    max_hex = self.version_string_to_hex(max_ver)
                    if min_hex <= version_value <= max_hex:
                        is_match = True
                        match_info['version_range'] = f"{min_ver} - {max_ver}"
                
                if is_match:
                    matches.append(match_info)
        
        return matches
    
    def get_version_display_string(self, version_value: int, include_platforms: bool = True) -> str:
        """
        Get a formatted display string for a RenderWare version with game and platform info.
        
        Args:
            version_value: The RW version value
            include_platforms: Whether to include platform information
            
        Returns:
            Formatted string like "3.6.0.3 (San Andreas) All" or "3.4.0.3 (Vice City) PC / (GTA 3) Mobile"
        """
        version_str = self.hex_to_version_string(version_value)
        
        if not include_platforms:
            return version_str
        
        matches = self.find_all_games_by_version(version_value)
        if not matches:
            return version_str
        
        # Group matches by game
        game_groups = {}
        for match in matches:
            game_name = match['display_name']
            platform = match['platform']
            
            if game_name not in game_groups:
                game_groups[game_name] = []
            game_groups[game_name].append(platform)
        
        # Get all available main platforms for reference
        main_platforms = {'PC', 'PS2', 'XBOX', 'MOBILE', 'PSP', 'GAMECUBE'}
        
        # Format the display string
        game_parts = []
        for game_name, platforms in game_groups.items():
            platforms = sorted(platforms)
            
            # Check if this game has most of the main platforms (3+ platforms indicates multi-platform)
            if len(platforms) >= 3:
                game_parts.append(f"({game_name}) All")
            elif len(platforms) == 1:
                game_parts.append(f"({game_name}) {platforms[0]}")
            else:
                # For 2 platforms, list them
                platform_str = " / ".join(platforms)
                game_parts.append(f"({game_name}) {platform_str}")
        
        if game_parts:
            return f"{version_str} {' / '.join(game_parts)}"
        else:
            return version_str
    
    def get_version_basic_string(self, version_value: int) -> str:
        """
        Get a basic version string without platform information for compatibility.
        
        Args:
            version_value: The RW version value
            
        Returns:
            Basic version string like "3.6.0.3"
        """
        return self.hex_to_version_string(version_value)
    
    def get_games_list(self) -> List[Dict[str, Any]]:
        """Get list of all games/sets with their version information"""
        games = []
        for game_set in self._versionsets_data:
            game_info = {
                'name': game_set.get('name'),
                'display_name': game_set.get('display_name', game_set.get('name')),
                'icon_name': game_set.get('icon_name'),
                'platforms': []
            }
            
            for platform in game_set.get('platforms', []):
                platform_info = {
                    'platform': platform.get('platform'),
                    'rw_version': platform.get('rw_version'),
                    'rw_version_hex': self.version_string_to_hex(platform.get('rw_version', '0.0.0.0')),
                    'data_types': platform.get('data_types', [])
                }
                
                # Add version range if available
                if platform.get('rw_version_min') and platform.get('rw_version_max'):
                    platform_info['version_range'] = {
                        'min': platform.get('rw_version_min'),
                        'max': platform.get('rw_version_max'),
                        'min_hex': self.version_string_to_hex(platform.get('rw_version_min', '0.0.0.0')),
                        'max_hex': self.version_string_to_hex(platform.get('rw_version_max', '0.0.0.0'))
                    }
                
                game_info['platforms'].append(platform_info)
            
            games.append(game_info)
        
        return games
    
    def get_platform_data_types(self, platform: str) -> List[str]:
        """Get supported data types for a platform"""
        return self._platform_info.get(platform, [])
    
    def is_dff_compatible_version(self, version_value: int) -> bool:
        """Check if RenderWare version is compatible with DFF format"""
        # DFF files are compatible with most RW versions
        return self.is_valid_rw_version(version_value)
    
    def is_txd_compatible_version(self, version_value: int) -> bool:
        """Check if RenderWare version is compatible with TXD format"""
        # TXD files are compatible with most RW versions
        return self.is_valid_rw_version(version_value)
    
    def detect_file_format_version(self, file_data: bytes, filename: str = "") -> Tuple[str, str, int]:
        """Detect RenderWare file format and version from data"""
        if len(file_data) < 12:
            return "Unknown", "Unknown", 0
        
        # Get file extension
        ext = filename.lower().split('.')[-1] if '.' in filename else ""
        
        try:
            import struct
            
            # Check for COL files first (they have unique FourCC signatures)
            if ext == "col" or len(file_data) >= 4:
                try:
                    fourcc = file_data[0:4].decode('ascii', errors='ignore')
                    if fourcc in ['COLL', 'COL2', 'COL3', 'COL4']:
                        col_versions = {
                            'COLL': "COL1 (GTA III/VC)",
                            'COL2': "COL2 (GTA SA)",
                            'COL3': "COL3 (GTA SA Advanced)",
                            'COL4': "COL4 (Extended)"
                        }
                        return "COL", col_versions.get(fourcc, f"Unknown COL ({fourcc})"), 0
                except:
                    pass
            
            # Check for RenderWare files with standard headers
            if len(file_data) >= 12:
                section_type = struct.unpack('<I', file_data[0:4])[0]
                version = struct.unpack('<I', file_data[8:12])[0]
                
                # Extract actual version using DFF function
                rw_version = self.get_rw_version(version)
                
                if section_type == 0x0010:  # CLUMP (DFF)
                    format_name = "DFF"
                    version_name = self.get_version_display_string(rw_version)
                    return format_name, version_name, rw_version
                    
                elif section_type == 0x0016:  # TEXDICTIONARY (TXD)
                    format_name = "TXD"
                    version_name = self.get_version_display_string(rw_version)
                    return format_name, version_name, rw_version
                    
                elif self.is_valid_rw_version(rw_version):
                    # Generic RenderWare file
                    format_name = ext.upper() or "RW"
                    version_name = self.get_version_display_string(rw_version)
                    return format_name, version_name, rw_version
                    
        except Exception as e:
            print(f"Error detecting file format: {e}")
        
        return ext.upper() or "Unknown", "Unknown format", 0
