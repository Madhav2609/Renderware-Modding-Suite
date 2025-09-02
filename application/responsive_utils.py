"""
Responsive utilities for the Renderware Modding Suite
Handles DPI scaling, font sizing, and UI element sizing for different screen sizes
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QRect
from PyQt6.QtGui import QScreen, QFont
from typing import Dict, Tuple
from application.debug_system import get_debug_logger, LogCategory


class ResponsiveManager:
    """Manages responsive behavior across different screen sizes and DPI settings"""
    
    def __init__(self):
        self.app = QApplication.instance()
        self.debug_logger = get_debug_logger()
        self.screen_info = self._get_screen_info()
        self.scale_factor = self._calculate_scale_factor()
        self.breakpoint = self._determine_breakpoint()
        
    def _get_screen_info(self) -> Dict:
        """Get current screen information"""
        if not self.app:
            return {"width": 1920, "height": 1080, "dpi": 96, "physical_dpi": 96, "device_pixel_ratio": 1.0}
        
        try:
            # Get primary screen - safer approach for PyQt6
            primary_screen = None
            if hasattr(self.app, 'primaryScreen'):
                primary_screen = self.app.primaryScreen()
            elif hasattr(self.app, 'desktop'):
                # Fallback for older versions
                desktop = self.app.desktop()
                if hasattr(desktop, 'screenGeometry'):
                    geometry = desktop.screenGeometry()
                    return {
                        "width": geometry.width(),
                        "height": geometry.height(), 
                        "dpi": 96,
                        "physical_dpi": 96,
                        "device_pixel_ratio": 1.0
                    }
            
            if primary_screen:
                geometry = primary_screen.geometry()
                dpi = getattr(primary_screen, 'logicalDotsPerInch', lambda: 96)()
                physical_dpi = getattr(primary_screen, 'physicalDotsPerInch', lambda: 96)()
                device_pixel_ratio = getattr(primary_screen, 'devicePixelRatio', lambda: 1.0)()
                
                return {
                    "width": geometry.width(),
                    "height": geometry.height(),
                    "dpi": dpi,
                    "physical_dpi": physical_dpi,
                    "device_pixel_ratio": device_pixel_ratio
                }
        except Exception as e:
            # Log the error if debug logger is available
            if hasattr(self, 'debug_logger') and self.debug_logger:
                self.debug_logger.warning(LogCategory.UI, f"Could not get screen info: {e}")
        
        # Return defaults if everything fails
        return {"width": 1920, "height": 1080, "dpi": 96, "physical_dpi": 96, "device_pixel_ratio": 1.0}
    
    def _calculate_scale_factor(self) -> float:
        """Calculate scale factor based on screen DPI, size, and aspect ratio"""
        base_dpi = 96  # Standard Windows DPI
        current_dpi = self.screen_info["dpi"]
        
        # Base scale from DPI
        dpi_scale = current_dpi / base_dpi
        
        # Additional scale based on screen resolution and aspect ratio
        width = self.screen_info["width"]
        height = self.screen_info["height"]
        aspect_ratio = width / height if height > 0 else 1.0
        
        # Resolution-based scale
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
        
        # Aspect ratio adjustments (16:9 is baseline)
        baseline_aspect = 16/9
        aspect_scale = 1.0
        
        if aspect_ratio > baseline_aspect * 1.3:  # Ultra-wide displays
            aspect_scale = 1.15
        elif aspect_ratio < baseline_aspect * 0.8:  # Square-ish displays
            aspect_scale = 0.95
        
        # Combine all scales
        final_scale = dpi_scale * resolution_scale * aspect_scale
        
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
            return (self.get_scaled_size(50), self.get_scaled_size(20))
        elif self.breakpoint == "medium":
            return (self.get_scaled_size(60), self.get_scaled_size(22))
        else:
            return (self.get_scaled_size(65), self.get_scaled_size(24))
    
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
        """Get recommended window size based on screen and breakpoint"""
        try:
            # Try to get available geometry from screen
            if self.app and hasattr(self.app, 'primaryScreen'):
                screen = self.app.primaryScreen()
                if screen and hasattr(screen, 'availableGeometry'):
                    avail = screen.availableGeometry()
                    width, height = avail.width(), avail.height()
                else:
                    width, height = self.screen_info["width"], self.screen_info["height"]
            else:
                width, height = self.screen_info["width"], self.screen_info["height"]
        except:
            # Fallback to screen info
            width, height = self.screen_info["width"], self.screen_info["height"]

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
                "size": self.get_scaled_font_size(12),
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
    
    def get_status_bar_height(self) -> int:
        """Get appropriate status bar height to prevent oversizing"""
        base_height = 24
        scaled_height = self.get_scaled_size(base_height)
        
        # Clamp to reasonable bounds - status bars shouldn't be too tall
        return max(20, min(32, scaled_height))
    
    def get_menu_height(self) -> int:
        """Get appropriate menu bar height"""
        base_height = 22
        return self.get_scaled_size(base_height)
    
    def get_toolbar_height(self) -> int:
        """Get appropriate toolbar height"""
        base_height = 32
        return self.get_scaled_size(base_height)
    
    def get_widget_size_constraints(self, widget_type: str) -> tuple:
        """Get size constraints for different widget types"""
        constraints = {
            "status_bar": (None, self.get_status_bar_height()),  # (min_height, max_height)
            "menu_bar": (None, self.get_menu_height()),
            "toolbar": (None, self.get_toolbar_height()),
            "button": (self.get_scaled_size(24), self.get_scaled_size(32)),
            "tab_bar": (None, self.get_scaled_size(28)),
        }
        
        return constraints.get(widget_type, (None, None))
        """Print debug information about current scaling"""
        # Summary info
        self.debug_logger.info(LogCategory.UI, "Responsive manager debug info", {
            "screen": f"{self.screen_info['width']}x{self.screen_info['height']}",
            "dpi": self.screen_info.get('dpi'),
            "scale_factor": round(self.scale_factor, 2),
            "breakpoint": self.breakpoint,
        })
        # Detailed configs
        self.debug_logger.debug(LogCategory.UI, "Font configuration", self.get_font_config())
        self.debug_logger.debug(LogCategory.UI, "Spacing configuration", self.get_spacing_config())


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
