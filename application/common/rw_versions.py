
"""
RenderWare Version Constants - Expanded
Standalone module for all RenderWare version definitions and utilities
Used by IMG, TXD, DFF, MDL, and validation systems
Includes support for DFF models, MDL files, and other 3D formats
"""

import struct
from enum import Enum
from typing import Dict, Optional, Tuple

## Methods list -
# get_rw_version_name
# is_valid_rw_version
# get_default_version_for_game
# get_version_info
# parse_rw_version
# get_model_format_version
# is_dff_compatible_version
# is_txd_compatible_version
# get_col_version_info
# get_txd_version_info
# get_dff_version_info
# detect_rw_file_format
# get_mdl_version_info

class RWVersion(Enum):
    """RenderWare version constants"""
    RW_VERSION_3_0_0_0 = 0x30000
    RW_VERSION_3_1_0_1 = 0x31001
    RW_VERSION_3_2_0_0 = 0x32000
    RW_VERSION_3_3_0_2 = 0x33002
    RW_VERSION_3_4_0_1 = 0x34001
    RW_VERSION_3_4_0_3 = 0x34003
    RW_VERSION_3_5_0_0 = 0x35000
    RW_VERSION_3_5_0_2 = 0x35002
    RW_VERSION_3_6_0_3 = 0x36003
    RW_VERSION_3_7_0_2 = 0x37002


class RWSection(Enum):
    """RenderWare section type constants"""
    STRUCT = 0x0001
    STRING = 0x0002
    EXTENSION = 0x0003
    TEXTURE = 0x0006
    MATERIAL = 0x0007
    MATERIAL_LIST = 0x0008
    MATLIST = 0x0008
    ATOMIC = 0x000E
    PLANE_SECTION = 0x000F
    GEOMETRY = 0x000F
    WORLD = 0x0010
    CLUMP = 0x0010
    FRAME_LIST = 0x0014
    ATOMIC_SECT = 0x0014
    TEXTURE_NATIVE = 0x0015
    TEXTURE_DICTIONARY = 0x0016
    TEXDICTIONARY = 0x0016
    ANIM_DICTIONARY = 0x0017
    ANIMDICTIONARY = 0x0017
    CLUMP_SECT = 0x001A
    RASTER = 0x001E


class ModelFormat(Enum):
    """Model file format types"""
    DFF = "dff"          # RenderWare DFF models
    TXD = "txd"          # RenderWare TXD textures
    COL = "col"          # RenderWare COL collision
    MDL = "mdl"          # Source/GoldSrc MDL models  
    WDR = "wdr"          # GTA IV+ World Drawable
    YDR = "ydr"          # GTA V+ Drawable
    OBJ = "obj"          # Wavefront OBJ
    PLY = "ply"          # Stanford PLY
    COLLADA = "dae"      # COLLADA format
    GLTF = "gltf"        # glTF format


class COLVersion(Enum):
    """COL collision file version constants"""
    COL_1 = 1           # COL1 - GTA III, Vice City (FourCC: 'COLL')
    COL_2 = 2           # COL2 - San Andreas (FourCC: 'COL2')
    COL_3 = 3           # COL3 - San Andreas advanced (FourCC: 'COL3')
    COL_4 = 4           # COL4 - Extended format (FourCC: 'COL4')


class TXDVersion(Enum):
    """TXD texture dictionary version constants"""
    TXD_GTA3 = 0x31001      # GTA III TXD textures
    TXD_GTAVC = 0x33002     # Vice City TXD textures
    TXD_GTASOL = 0x34003    # State of Liberty TXD textures
    TXD_GTASA = 0x36003     # San Andreas TXD textures
    TXD_BULLY = 0x35000     # Bully TXD textures
    TXD_LCS = 0x35000       # Liberty City Stories TXD textures
    TXD_VCS = 0x35002       # Vice City Stories TXD textures


class DFFVersion(Enum):
    """DFF-specific version constants"""
    DFF_GTA3 = 0x31001      # GTA III DFF models
    DFF_GTAVC = 0x33002     # Vice City DFF models
    DFF_GTASOL = 0x34001    # State of Liberty
    DFF_GTASA = 0x36003     # San Andreas DFF models
    DFF_BULLY = 0x36003     # Bully DFF models
    DFF_MANHUNT = 0x34003   # Manhunt DFF models


class MDLVersion(Enum):
    """MDL model version constants (GTA Stories PSP format)"""
    MDL_LCS = 0x35000       # Liberty City Stories PSP
    MDL_VCS = 0x35002       # Vice City Stories PSP
    MDL_PSP_BASE = 0x35000  # Base PSP RenderWare version


def get_rw_version_name(version_value: int) -> str: #vers 2
    """Get human-readable RenderWare version name from version value"""
    # Extended version mapping including all common variants
    rw_versions = {
        # Standard versions
        0x30000: "3.0.0.0",
        0x31001: "3.1.0.1",
        0x32000: "3.2.0.0",
        0x33002: "3.3.0.2",
        0x34001: "3.4.0.1",
        0x34003: "3.4.0.3",
        0x35000: "3.5.0.0",
        0x35002: "3.5.0.2",
        0x36003: "3.6.0.3",
        0x37002: "3.7.0.2",
        
        # Extended format versions (with additional bits)
        0x0800FFFF: "3.0.0.0",
        0x1003FFFF: "3.1.0.1", 
        0x1005FFFF: "3.2.0.0",
        0x1401FFFF: "3.4.0.1",  # FIXME: Need correct hex value for 3.4.0.1 extended format
        0x1400FFFF: "3.4.0.3",
        0x1803FFFF: "3.6.0.3",
        0x1C020037: "3.7.0.2",
        
        # Game-specific variants
        0x310100: "3.1.0.1 (GTA3)",
        0x320001: "3.2.0.1 (Vice City)", 
        0x340001: "3.4.0.1 (Manhunt, State of Liberty)",
        0x340003: "3.4.0.3 (San Andreas)",
        0x360003: "3.6.0.3 (San Andreas)",
        
        # Additional SA variants
        0x1803FFFF: "3.6.0.3 (SA)",
        0x34003: "3.4.0.3 (SA)",
        
        # GTA Stories (PSP) variants
        0x35000: "3.5.0.0 (Liberty City Stories)",
        0x35002: "3.5.0.2 (Vice City Stories)",
    }
    
    return rw_versions.get(version_value, f"Unknown (0x{version_value:X})")


def is_valid_rw_version(version_value: int) -> bool: #vers 1
    """Check if RenderWare version value is valid"""
    # Check if it's in the range of known RW versions
    if 0x30000 <= version_value <= 0x3FFFF:
        return True
    
    # Check extended format versions
    if version_value in [0x0800FFFF, 0x1003FFFF, 0x1005FFFF, 0x1401FFFF, 0x1400FFFF, 0x1803FFFF, 0x1C020037]:
        return True
        
    return False


def get_default_version_for_game(game: str) -> int: #vers 1
    """Get default RenderWare version for specific game"""
    game_versions = {
        'gta3': RWVersion.RW_VERSION_3_1_0_1.value,
        'gtavc': RWVersion.RW_VERSION_3_3_0_2.value,
        'gtasol': RWVersion.RW_VERSION_3_4_0_1.value,
        'gtasa': RWVersion.RW_VERSION_3_6_0_3.value,
        'bully': RWVersion.RW_VERSION_3_5_0_0.value,
        'lcs': RWVersion.RW_VERSION_3_5_0_0.value,      # Liberty City Stories
        'vcs': RWVersion.RW_VERSION_3_5_0_2.value,      # Vice City Stories
        'manhunt': RWVersion.RW_VERSION_3_4_0_3.value,
        'manhunt2': RWVersion.RW_VERSION_3_6_0_3.value,
    }
    
    return game_versions.get(game.lower(), RWVersion.RW_VERSION_3_6_0_3.value)


def get_version_info(version_value: int) -> Dict[str, any]: #vers 1
    """Get detailed version information"""
    return {
        'version_hex': f"0x{version_value:X}",
        'version_name': get_rw_version_name(version_value),
        'is_valid': is_valid_rw_version(version_value),
        'major': (version_value >> 16) & 0xFF,
        'minor': (version_value >> 8) & 0xFF,
        'patch': version_value & 0xFF
    }


def parse_rw_version(version_bytes: bytes) -> Tuple[int, str]: #vers 2
    """Parse RenderWare version from 4-byte header - FIXED"""
    if len(version_bytes) < 4:
        return 0, "Invalid"
    
    try:
        version_value = struct.unpack('<I', version_bytes)[0]
        version_name = get_rw_version_name(version_value)
        return version_value, version_name
    except struct.error:
        return 0, "Invalid"


def get_model_format_version(file_extension: str, data: bytes) -> Tuple[str, str]: #vers 2
    """Get model format and version from file data"""
    ext = file_extension.lower().lstrip('.')
    
    if ext == 'dff':
        if len(data) >= 12:
            try:
                # Check RenderWare header structure
                section_type = struct.unpack('<I', data[0:4])[0]
                if section_type == 0x0010:  # RW_SECTION_CLUMP
                    version = struct.unpack('<I', data[8:12])[0]
                    return "DFF", get_rw_version_name(version)
            except:
                pass
        return "DFF", "Unknown"
        
    elif ext == 'txd':
        if len(data) >= 12:
            try:
                # Check for TXD header structure
                section_type = struct.unpack('<I', data[0:4])[0]
                if section_type == 0x0016:  # RW_SECTION_TEXDICTIONARY
                    version = struct.unpack('<I', data[8:12])[0]
                    return "TXD", get_rw_version_name(version)
            except:
                pass
        return "TXD", "Unknown"
        
    elif ext == 'col':
        if len(data) >= 4:
            try:
                # Read FourCC signature for COL files as ASCII string
                fourcc = data[0:4].decode('ascii', errors='ignore')
                if fourcc == 'COLL':
                    return "COL", "COL1 (GTA III/VC)"
                elif fourcc == 'COL2':
                    return "COL", "COL2 (GTA SA)"
                elif fourcc == 'COL3':
                    return "COL", "COL3 (GTA SA Advanced)"
                elif fourcc == 'COL4':
                    return "COL", "COL4 (Extended)"
                else:
                    return "COL", f"Unknown COL format ({fourcc})"
            except:
                pass
        return "COL", "Invalid COL format"
        
    elif ext == 'mdl':
        # GTA Stories PSP MDL files
        if len(data) >= 12:
            try:
                version = struct.unpack('<I', data[8:12])[0]
                if version == 0x35000:
                    return "MDL", "Liberty City Stories PSP"
                elif version == 0x35002:
                    return "MDL", "Vice City Stories PSP"
                else:
                    return "MDL", f"GTA Stories (0x{version:X})"
            except:
                pass
        return "MDL", "GTA Stories PSP"
        
    elif ext == 'wdr':
        return "WDR", "GTA IV World Drawable"
        
    elif ext == 'ydr':
        return "YDR", "GTA V Drawable"
        
    return ext.upper(), "Unknown"


def is_dff_compatible_version(version_value: int) -> bool: #vers 1
    """Check if RenderWare version is compatible with DFF format"""
    compatible_versions = [
        0x31001,  # GTA3
        0x33002,  # Vice City
        0x34001,  # State Of Liberty
        0x34003,  # San Andreas
        0x36003,  # San Andreas/Bully
        0x35000,  # Liberty City Stories
        0x35002,  # Vice City Stories
    ]
    return version_value in compatible_versions


def is_txd_compatible_version(version_value: int) -> bool: #vers 1
    """Check if RenderWare version is compatible with TXD format"""
    compatible_versions = [
        0x31001,  # GTA3
        0x33002,  # Vice City
        0x34003,  # San Andreas
        0x36003,  # San Andreas/Bully
        0x35000,  # Liberty City Stories/Bully
        0x35002,  # Vice City Stories
    ]
    return version_value in compatible_versions


def get_col_version_info(col_data: bytes) -> Tuple[str, int]: #vers 2
    """Get COL file version information from data"""
    if len(col_data) < 4:
        return "Unknown", 0
    
    try:
        # Read FourCC as ASCII string
        fourcc = col_data[0:4].decode('ascii', errors='ignore')
        if fourcc == 'COLL':
            return "COL1 (GTA III/VC)", 1
        elif fourcc == 'COL2':
            return "COL2 (GTA SA)", 2
        elif fourcc == 'COL3':
            return "COL3 (GTA SA Advanced)", 3
        elif fourcc == 'COL4':
            return "COL4 (Extended)", 4
        else:
            return f"Unknown COL format ({fourcc})", 0
    except:
        return "Invalid COL format", 0


def get_txd_version_info(txd_data: bytes) -> Tuple[str, int]: #vers 1
    """Get TXD file version information from data"""
    if len(txd_data) < 12:
        return "Unknown", 0
    
    try:
        section_type = struct.unpack('<I', txd_data[0:4])[0]
        if section_type == 0x0016:  # RW_SECTION_TEXDICTIONARY
            version = struct.unpack('<I', txd_data[8:12])[0]
            version_name = get_rw_version_name(version)
            return f"TXD ({version_name})", version
        else:
            return "Invalid TXD format", 0
    except:
        return "Error reading TXD", 0


def get_dff_version_info(dff_data: bytes) -> Tuple[str, int]: #vers 1
    """Get DFF file version information from data"""
    if len(dff_data) < 12:
        return "Unknown", 0
    
    try:
        section_type = struct.unpack('<I', dff_data[0:4])[0]
        if section_type == 0x0010:  # RW_SECTION_CLUMP
            version = struct.unpack('<I', dff_data[8:12])[0]
            version_name = get_rw_version_name(version)
            return f"DFF ({version_name})", version
        else:
            return "Invalid DFF format", 0
    except:
        return "Error reading DFF", 0


def detect_rw_file_format(data: bytes, filename: str = "") -> Tuple[str, str, int]: #vers 1
    """Detect RenderWare file format, version, and type from data"""
    if len(data) < 4:
        return "Unknown", "Unknown", 0
    
    # Get file extension
    ext = filename.lower().split('.')[-1] if '.' in filename else ""
    
    # Check for COL files first (they have unique FourCC signatures)
    if ext == "col":
        version_name, version_num = get_col_version_info(data)
        return "COL", version_name, version_num
    
    # Also check by FourCC if no extension
    if len(data) >= 4:
        try:
            fourcc = data[0:4].decode('ascii', errors='ignore')
            if fourcc in ['COLL', 'COL2', 'COL3', 'COL4']:
                version_name, version_num = get_col_version_info(data)
                return "COL", version_name, version_num
        except:
            pass
    
    # Check for RenderWare files with standard headers
    if len(data) >= 12:
        try:
            section_type = struct.unpack('<I', data[0:4])[0]
            version = struct.unpack('<I', data[8:12])[0]
            
            if section_type == 0x0010:  # CLUMP (DFF)
                version_name = get_rw_version_name(version)
                return "DFF", f"DFF ({version_name})", version
            elif section_type == 0x0016:  # TEXDICTIONARY (TXD)
                version_name = get_rw_version_name(version)
                return "TXD", f"TXD ({version_name})", version
            elif is_valid_rw_version(version):
                # Generic RenderWare file
                version_name = get_rw_version_name(version)
                return ext.upper() or "RW", f"RW ({version_name})", version
        except:
            pass
    
    return ext.upper() or "Unknown", "Unknown format", 0


def get_mdl_version_info(mdl_version: int) -> str: #vers 1
    """Get GTA Stories MDL version information string"""
    mdl_versions = {
        0x35000: "Liberty City Stories (PSP)",
        0x35002: "Vice City Stories (PSP)",
    }
    return mdl_versions.get(mdl_version, f"Unknown GTA Stories MDL (0x{mdl_version:X})")
