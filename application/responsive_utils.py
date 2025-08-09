"""
Responsive utilities for the Renderware Modding Suite
Handles DPI scaling, font sizing, and UI element sizing for different screen sizes
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRect
from PySide6.QtGui import QScreen, QFont
from typing import Dict, Tuple


class ResponsiveManager:
    """Manages responsive behavior across different screen sizes and DPI settings"""
    
    def __init__(self):
        self.app = QApplication.instance()
        self.screen_info = self._get_screen_info()
        self.scale_factor = self._calculate_scale_factor()
        self.breakpoint = self._determine_breakpoint()
        
    def _get_screen_info(self) -> Dict:
        """Get current screen information"""
        if not self.app:
            return {"width": 1920, "height": 1080, "dpi": 96, "physical_dpi": 96}
        
        primary_screen = self.app.primaryScreen()
        if primary_screen:
            geometry = primary_screen.geometry()
            dpi = primary_screen.logicalDotsPerInch()
            physical_dpi = primary_screen.physicalDotsPerInch()
            
            return {
                "width": geometry.width(),
                "height": geometry.height(),
                "dpi": dpi,
                "physical_dpi": physical_dpi,
                "device_pixel_ratio": primary_screen.devicePixelRatio()
            }
        
        return {"width": 1920, "height": 1080, "dpi": 96, "physical_dpi": 96, "device_pixel_ratio": 1.0}
    
    def _calculate_scale_factor(self) -> float:
        """Calculate scale factor based on screen DPI and size"""
        base_dpi = 96  # Standard Windows DPI
        current_dpi = self.screen_info["dpi"]
        
        # Base scale from DPI
        dpi_scale = current_dpi / base_dpi
        
        # Additional scale based on screen resolution
        width = self.screen_info["width"]
        
        if width <= 1366:  # Small laptops (14-15 inch)
            resolution_scale = 0.85
        elif width <= 1600:  # Medium screens (15-17 inch)
            resolution_scale = 0.95
        elif width <= 1920:  # Standard HD (17-21 inch)
            resolution_scale = 1.0
        elif width <= 2560:  # 2K screens (21-27 inch)
            resolution_scale = 1.1
        else:  # 4K and larger
            resolution_scale = 1.2
        
        # Combine both scales
        final_scale = dpi_scale * resolution_scale
        
        # Clamp to reasonable bounds
        return max(0.8, min(2.0, final_scale))
    
    def _determine_breakpoint(self) -> str:
        """Determine which breakpoint category the screen falls into"""
        width = self.screen_info["width"]
        
        if width <= 1366:
            return "small"      # 14-inch laptops and smaller
        elif width <= 1600:
            return "medium"     # 15-16 inch laptops
        elif width <= 1920:
            return "large"      # 17-21 inch displays
        elif width <= 2560:
            return "xlarge"     # 2K displays (22-27 inch)
        else:
            return "xxlarge"    # 4K displays (27+ inch)
    
    def get_scaled_font_size(self, base_size: int) -> int:
        """Get scaled font size based on screen characteristics"""
        scaled = int(base_size * self.scale_factor)
        return max(8, min(24, scaled))  # Clamp to reasonable font sizes
    
    def get_scaled_size(self, base_size: int) -> int:
        """Get scaled size for UI elements"""
        scaled = int(base_size * self.scale_factor)
        return max(1, scaled)
    
    def get_padding(self, base_padding: int) -> int:
        """Get scaled padding"""
        return self.get_scaled_size(base_padding)
    
    def get_icon_size(self, base_size: int = 16) -> int:
        """Get scaled icon size"""
        return self.get_scaled_size(base_size)
    
    def get_button_size(self) -> Tuple[int, int]:
        """Get recommended button size (min_width, height)"""
        if self.breakpoint == "small":
            return (self.get_scaled_size(60), self.get_scaled_size(22))
        elif self.breakpoint == "medium":
            return (self.get_scaled_size(70), self.get_scaled_size(24))
        else:
            return (self.get_scaled_size(80), self.get_scaled_size(26))
    
    def get_panel_width(self) -> Tuple[int, int]:
        """Get recommended panel width (min, max)"""
        if self.breakpoint == "small":
            return (150, 250)
        elif self.breakpoint == "medium":
            return (180, 280)
        else:
            return (200, 300)
    
    def get_content_margins(self) -> Tuple[int, int, int, int]:
        """Get content margins (left, top, right, bottom)"""
        if self.breakpoint == "small":
            margin = self.get_scaled_size(4)
        elif self.breakpoint == "medium":
            margin = self.get_scaled_size(6)
        else:
            margin = self.get_scaled_size(8)
        
        return (margin, margin, margin, margin)
    
    def get_window_size(self) -> Tuple[int, int]:
        """Get recommended initial window size"""
        width = self.screen_info["width"]
        height = self.screen_info["height"]
        
        # Use percentage of screen size
        if self.breakpoint == "small":
            return (int(width * 0.9), int(height * 0.85))
        elif self.breakpoint == "medium":
            return (int(width * 0.85), int(height * 0.8))
        else:
            return (int(width * 0.8), int(height * 0.75))
    
    def get_font_config(self) -> Dict[str, Dict]:
        """Get font configuration for different UI elements"""
        return {
            "header": {
                "size": self.get_scaled_font_size(14),
                "weight": "bold"
            },
            "subheader": {
                "size": self.get_scaled_font_size(12),
                "weight": "bold"
            },
            "body": {
                "size": self.get_scaled_font_size(12),
                "weight": "normal"
            },
            "small": {
                "size": self.get_scaled_font_size(12),
                "weight": "normal"
            },
            "code": {
                "size": self.get_scaled_font_size(11),
                "weight": "normal",
                "family": "'Fira Code', 'Consolas', 'Monaco', 'Cascadia Code', monospace"
            },
            "menu": {
                "size": self.get_scaled_font_size(12),
                "weight": "normal"
            },
            "status": {
                "size": self.get_scaled_font_size(12),
                "weight": "normal"
            }
        }
    
    def get_spacing_config(self) -> Dict[str, int]:
        """Get spacing configuration for different UI elements"""
        return {
            "small": self.get_scaled_size(4),
            "medium": self.get_scaled_size(6),
            "large": self.get_scaled_size(11),
            "xlarge": self.get_scaled_size(14)
        }
    
    def print_debug_info(self):
        """Print debug information about current scaling"""
        print(f"🖥️ Screen Info: {self.screen_info['width']}x{self.screen_info['height']} @ {self.screen_info['dpi']} DPI")
        print(f"📐 Scale Factor: {self.scale_factor:.2f}")
        print(f"📱 Breakpoint: {self.breakpoint}")
        print(f"🎨 Font Sizes: {self.get_font_config()}")
        print(f"📏 Spacing: {self.get_spacing_config()}")


# Global responsive manager instance
_responsive_manager = None

def get_responsive_manager() -> ResponsiveManager:
    """Get the global responsive manager instance"""
    global _responsive_manager
    if _responsive_manager is None:
        _responsive_manager = ResponsiveManager()
    return _responsive_manager

def refresh_responsive_manager():
    """Refresh the responsive manager (call when screen changes)"""
    global _responsive_manager
    _responsive_manager = ResponsiveManager()
    return _responsive_manager
