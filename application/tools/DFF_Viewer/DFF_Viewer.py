#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyQt6 + Qt3D: DFF/OBJ Model Viewer with Interactive Inspector Highlighting.
This file provides both:
1) A standalone window (MainWindow) for direct running.
2) A suite-integrated tool widget (DFFViewerTool) to embed in the Modding Suite.
"""

import math
import os
import struct
import traceback
import struct
import sys

# Correctly import QBuffer and QByteArray from QtCore
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QBuffer, QByteArray 

from PyQt6.QtGui import QAction, QColor, QMatrix4x4, QPixmap, QImage
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QToolBar,
    QLabel,
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSlider,
    QSpinBox,
    QPushButton,
    QColorDialog,
    QCheckBox,
    QMessageBox,
    QTreeWidget,
    QTreeWidgetItem,
    QSplitter,
    QGroupBox,
)

# Qt3D imports
from PyQt6.Qt3DCore import (
    QEntity,
    QTransform,
    QGeometry,
    QAttribute,
    QBuffer as Qt3DBuffer  # Import Qt3D specific buffer
)
from PyQt6.Qt3DExtras import (
    Qt3DWindow,
    QOrbitCameraController,
    QPhongMaterial,
    QDiffuseMapMaterial,
    QCylinderMesh, # Needed for the axis gizmo
)
from PyQt6.Qt3DRender import (
    QCamera,
    QCameraLens,
    QMesh,
    QDirectionalLight,
    QGeometryRenderer,
    QTexture2D,
    QTextureImage,
    QAbstractTexture,
    QTextureDataUpdate,
    QDepthTest,
    QCullFace,
    QAlphaTest,
)

# Import the DFF parser and the Vector class
# Prefer in-suite path; fall back to local if directly running outside package
try:
    from application.common.DFF import dff, Vector, SkinPLG, HAnimPLG, UserData
    from application.common.txd import txd, TextureNative
    print("[DFF Viewer] Using suite imports - TXD support enabled")
except ImportError as e:
    print(f"[DFF Viewer] Suite import failed: {e}")
    try:
        # This would be for standalone execution outside the suite
        from common.DFF import dff, Vector, SkinPLG, HAnimPLG, UserData
        from common.txd import txd, TextureNative
        print("[DFF Viewer] Using local common imports - TXD support enabled")
    except ImportError as e2:
        print(f"[DFF Viewer] Local import also failed: {e2}")
        # Try DFF-only mode
        try:
            from application.common.DFF import dff, Vector, SkinPLG, HAnimPLG, UserData
            # Create dummy TXD classes if txd import fails
            class txd:
                def __init__(self): 
                    self.native_textures = []
                    self.rw_version = 0
                    self.device_id = 0
                def load_file(self, path): 
                    raise Exception("TXD support not available - txd module failed to import")
            class TextureNative:
                def __init__(self): 
                    self.name = "dummy"
                def to_rgba(self, level=0): return None
                def get_width(self, level=0): return 0
                def get_height(self, level=0): return 0
            print("[DFF Viewer] TXD support disabled - only DFF parsing available")
        except ImportError as e3:
            print(f"Import Error: Could not import DFF parser: {e3}")
            sys.exit(1)

# Suite integrations (safe to import when running inside the app)
try:
    from application.responsive_utils import get_responsive_manager
    from application.styles import ModernDarkTheme
    from application.debug_system import get_debug_logger, LogCategory
    from application.common.message_box import message_box
except Exception:
    # Allow standalone run without suite modules
    get_debug_logger = lambda: None
    class LogCategory:  # type: ignore
        UI = TOOL = ERROR = 'GEN'
    def get_responsive_manager():  # type: ignore
        class Dummy:
            def get_font_config(self):
                return {k: {"size": 12} for k in ["header","subheader","body","small","code","menu","status"]}
            def get_spacing_config(self):
                return {"small": 4, "medium": 6, "large": 11, "xlarge": 14}
            def get_button_size(self):
                return (80, 26)
        return Dummy()
    class ModernDarkTheme:  # type: ignore
        BACKGROUND_TERTIARY = "#2a2a2a"
        BORDER_PRIMARY = "#3a3a3a"
        TEXT_ACCENT = "#4ea1ff"
    def message_box(): pass  # type: ignore


# =====================================================================
# Helper class for creating a 3D axis gizmo
# =====================================================================
class AxisGizmoEntity(QEntity):
    """An entity that displays a 3-axis (RGB) gizmo."""
    def __init__(self, parent=None, length=1.0, radius=0.02):
        super().__init__(parent)

        # X Axis (Red)
        x_axis = QEntity(self)
        x_mesh = QCylinderMesh()
        x_mesh.setRadius(radius)
        x_mesh.setLength(length)
        x_mat = QPhongMaterial(x_axis)
        x_mat.setAmbient(QColor(255, 0, 0))
        x_transform = QTransform()
        x_transform.setRotationZ(90) # Rotate to align with X axis
        x_transform.setTranslation(QtGui.QVector3D(length / 2, 0, 0))
        x_axis.addComponent(x_mesh)
        x_axis.addComponent(x_mat)
        x_axis.addComponent(x_transform)

        # Y Axis (Green)
        y_axis = QEntity(self)
        y_mesh = QCylinderMesh()
        y_mesh.setRadius(radius)
        y_mesh.setLength(length)
        y_mat = QPhongMaterial(y_axis)
        y_mat.setAmbient(QColor(0, 255, 0))
        y_transform = QTransform()
        y_transform.setTranslation(QtGui.QVector3D(0, length / 2, 0))
        y_axis.addComponent(y_mesh)
        y_axis.addComponent(y_mat)
        y_axis.addComponent(y_transform)

        # Z Axis (Blue)
        z_axis = QEntity(self)
        z_mesh = QCylinderMesh()
        z_mesh.setRadius(radius)
        z_mesh.setLength(length)
        z_mat = QPhongMaterial(z_axis)
        z_mat.setAmbient(QColor(0, 0, 255))
        z_transform = QTransform()
        z_transform.setRotationX(90) # Rotate to align with Z axis
        z_transform.setTranslation(QtGui.QVector3D(0, 0, length / 2))
        z_axis.addComponent(z_mesh)
        z_axis.addComponent(z_mat)
        z_axis.addComponent(z_transform)


class BlenderStyleCameraController:
    """Custom camera controller with Blender-style mouse navigation."""
    
    def __init__(self, camera, view_center=None):
        self.camera = camera
        self.view_center = view_center or QtGui.QVector3D(0.0, 0.0, 0.0)
        self.spherical = [8.0, 35.0, 35.0]  # distance, azimuth, elevation
        
        # Mouse interaction state
        self.mouse_pressed = False
        self.last_mouse_pos = None
        self.mouse_button = None
        
        # Navigation sensitivity
        self.orbit_sensitivity = 0.5
        self.pan_sensitivity = 0.01
        self.zoom_sensitivity = 0.1
        
        # Visual feedback
        self.is_navigating = False
        
        self._apply_camera_from_spherical()
    
    def _apply_camera_from_spherical(self):
        """Update camera position from spherical coordinates."""
        d, az_deg, el_deg = self.spherical
        az = math.radians(az_deg)
        el = math.radians(el_deg)
        
        x = d * math.cos(el) * math.cos(az)
        y = d * math.sin(el)
        z = d * math.cos(el) * math.sin(az)
        
        pos = QtGui.QVector3D(x, y, z) + self.view_center
        self.camera.setViewCenter(self.view_center)
        self.camera.setPosition(pos)
    
    def handle_mouse_press(self, event):
        """Handle mouse press events."""
        self.mouse_pressed = True
        # Handle both old and new Qt position methods
        if hasattr(event, 'position'):
            self.last_mouse_pos = event.position()
        elif hasattr(event, 'pos'):
            self.last_mouse_pos = event.pos()
        else:
            self.last_mouse_pos = QtCore.QPointF(event.x(), event.y())
            
        self.mouse_button = event.button() if hasattr(event, 'button') else None
        self.is_navigating = True
        print(f"Mouse pressed: {self.mouse_button}, pos: {self.last_mouse_pos}")
    
    def handle_mouse_release(self, event):
        """Handle mouse release events."""
        self.mouse_pressed = False
        self.last_mouse_pos = None
        self.mouse_button = None
        self.is_navigating = False
    
    def handle_mouse_move(self, event):
        """Handle mouse move events for navigation."""
        if not self.mouse_pressed or not self.last_mouse_pos:
            return
        
        # Handle both old and new Qt position methods
        if hasattr(event, 'position'):
            current_pos = event.position()
        elif hasattr(event, 'pos'):
            current_pos = event.pos()
        else:
            current_pos = QtCore.QPointF(event.x(), event.y())
            
        delta_x = current_pos.x() - self.last_mouse_pos.x()
        delta_y = current_pos.y() - self.last_mouse_pos.y()
        
        print(f"Mouse move: delta({delta_x}, {delta_y}), button: {self.mouse_button}")
        
        modifiers = event.modifiers() if hasattr(event, 'modifiers') else QtCore.Qt.KeyboardModifier.NoModifier
        
        # Middle mouse button or Shift+Left mouse: Orbit
        if (self.mouse_button == Qt.MouseButton.MiddleButton or 
            (self.mouse_button == Qt.MouseButton.LeftButton and 
             modifiers & Qt.KeyboardModifier.ShiftModifier)):
            print(f"Orbiting: {delta_x}, {delta_y}")
            self._orbit(delta_x, delta_y)
        
        # Shift+Middle mouse or Ctrl+Left mouse: Pan
        elif ((self.mouse_button == Qt.MouseButton.MiddleButton and 
               modifiers & Qt.KeyboardModifier.ShiftModifier) or
              (self.mouse_button == Qt.MouseButton.LeftButton and 
               modifiers & Qt.KeyboardModifier.ControlModifier)):
            print(f"Panning: {delta_x}, {delta_y}")
            self._pan(delta_x, delta_y)
        
        # Right mouse button: Zoom
        elif self.mouse_button == Qt.MouseButton.RightButton:
            print(f"Zooming: {delta_y}")
            self._zoom(delta_y)
        
        self.last_mouse_pos = current_pos
    
    def handle_wheel(self, event):
        """Handle mouse wheel events for zooming."""
        if hasattr(event, 'angleDelta'):
            delta = event.angleDelta().y() / 120.0  # Standard wheel step
        else:
            delta = event.delta() / 120.0 if hasattr(event, 'delta') else 0
        
        print(f"Wheel zoom: {delta}")
        self._zoom(-delta * 0.5)  # Negative for natural scrolling
    
    def _orbit(self, delta_x, delta_y):
        """Orbit around the view center."""
        self.spherical[1] += delta_x * self.orbit_sensitivity  # Azimuth
        self.spherical[2] = max(-89, min(89, self.spherical[2] - delta_y * self.orbit_sensitivity))  # Elevation
        self._apply_camera_from_spherical()
    
    def _pan(self, delta_x, delta_y):
        """Pan the view center."""
        # Get camera's right and up vectors
        cam_pos = self.camera.position()
        view_dir = (self.view_center - cam_pos).normalized()
        right = QtGui.QVector3D.crossProduct(view_dir, QtGui.QVector3D(0, 1, 0)).normalized()
        up = QtGui.QVector3D.crossProduct(right, view_dir).normalized()
        
        # Calculate pan distance based on camera distance
        pan_scale = self.spherical[0] * self.pan_sensitivity
        
        # Apply pan
        pan_offset = right * (-delta_x * pan_scale) + up * (delta_y * pan_scale)
        self.view_center += pan_offset
        self._apply_camera_from_spherical()
    
    def _zoom(self, delta):
        """Zoom in/out by changing distance."""
        zoom_factor = 1.0 + (delta * self.zoom_sensitivity)
        self.spherical[0] = max(0.1, self.spherical[0] * zoom_factor)
        self._apply_camera_from_spherical()
    
    def reset_view(self):
        """Reset to default view."""
        self.view_center = QtGui.QVector3D(0, 0, 0)
        self.spherical = [8.0, 35.0, 35.0]
        self._apply_camera_from_spherical()
    
    def focus_on_bounds(self, min_vec, max_vec):
        """Focus camera on given bounds."""
        center = (min_vec + max_vec) / 2.0
        radius = (max_vec - min_vec).length()
        
        self.view_center = center
        self.spherical[0] = max(4.0, radius * 1.5)
        self._apply_camera_from_spherical()


class Viewer3D(QWidget):
    # Signal now emits the dff object AND the geometry-to-entity map
    dff_loaded = pyqtSignal(object, dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create a Qt3D window and embed it in a QWidget container
        self.view = Qt3DWindow()
        self.view.defaultFrameGraph().setClearColor(QtGui.QColor(30, 30, 34))
        self.container = QtWidgets.QWidget.createWindowContainer(self.view)
        self.container.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Enable mouse tracking and set focus policy for better event handling
        self.container.setMouseTracking(True)
        self.container.setAttribute(QtCore.Qt.WidgetAttribute.WA_AcceptTouchEvents, False)
        self.setMouseTracking(True)  # Enable on the widget itself too
        
        # Install event filter for custom mouse handling
        self.container.installEventFilter(self)
        
        # Also install on the Qt3D view itself
        self.view.installEventFilter(self)
        
        # Try to grab mouse events more aggressively
        self.container.grabMouse()
        self.container.releaseMouse()  # Release immediately, just to test capability
        
        # Set cursor and tooltip for navigation help
        self.container.setToolTip("""3D Navigation:
• Middle Mouse: Orbit
• Shift + Middle Mouse: Pan
• Mouse Wheel: Zoom
• Shift + Left Mouse: Orbit
• Ctrl + Left Mouse: Pan
• Right Mouse: Zoom (drag)""")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.container)

        # Root entity
        self.root = QEntity()
        self.view.setRootEntity(self.root)

        # Camera setup
        self.cam = self.view.camera()
        self.cam.lens().setProjectionType(QCameraLens.ProjectionType.PerspectiveProjection)
        self.cam.lens().setPerspectiveProjection(45.0, 16/9, 0.1, 10000.0)

        # Custom camera controller (Blender-style)
        self.camera_controller = BlenderStyleCameraController(self.cam)
        
        # For backwards compatibility with existing code
        self.view_center = self.camera_controller.view_center
        self.spherical = self.camera_controller.spherical
        
        # Remove the default Qt3D camera controller to avoid conflicts
        # and ensure our custom controller takes precedence
        self.view.setActiveFrameGraph(self.view.defaultFrameGraph())

        # --- Balanced Two-Light Setup to prevent translucency while avoiding dark sides ---
        # Main light - primary illumination
        self.main_light_entity = QEntity(self.root)
        self.main_light = QDirectionalLight(self.main_light_entity)
        self.main_light.setWorldDirection(QtGui.QVector3D(-0.5, -0.7, -0.5))  # Good angle for models
        self.main_light.setColor(QtGui.QColor(255, 255, 255))  # Pure white light
        self.main_light.setIntensity(0.8)  # Slightly reduced main intensity
        self.main_light_entity.addComponent(self.main_light)
        
        # Subtle fill light to illuminate dark areas without causing translucency
        self.fill_light_entity = QEntity(self.root)
        self.fill_light = QDirectionalLight(self.fill_light_entity)
        self.fill_light.setWorldDirection(QtGui.QVector3D(0.5, 0.3, 0.5))  # Opposite direction
        self.fill_light.setColor(QtGui.QColor(200, 220, 255))  # Slightly cool fill
        self.fill_light.setIntensity(1.3)  # Increased intensity to better illuminate dark areas
        self.fill_light_entity.addComponent(self.fill_light)

        # Placeholder for the loaded model
        self.model_entity: QEntity | None = None
        self.original_materials = {} # To store original colors for toggling override
        self.current_dff_path: str | None = None
        self.current_dff: dff | None = None  # Store reference to loaded DFF file
        
        # TXD/Texture support
        self.current_txd: txd | None = None
        self.current_txd_path: str | None = None
        self.texture_cache = {}  # Cache for loaded Qt3D textures

    def mousePressEvent(self, event):
        """Handle mouse press events directly."""
        print(f"Direct mouse press: {event.button()}")
        self.camera_controller.handle_mouse_press(event)
        # Change cursor during navigation
        if event.button() == Qt.MouseButton.MiddleButton:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.setCursor(Qt.CursorShape.SizeAllCursor)  # Pan cursor
            else:
                self.setCursor(Qt.CursorShape.ClosedHandCursor)  # Orbit cursor
        elif event.button() == Qt.MouseButton.RightButton:
            self.setCursor(Qt.CursorShape.SizeVerCursor)  # Zoom cursor
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events directly."""
        print(f"Direct mouse release: {event.button()}")
        self.camera_controller.handle_mouse_release(event)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events directly."""
        self.camera_controller.handle_mouse_move(event)
        super().mouseMoveEvent(event)
    
    def wheelEvent(self, event):
        """Handle wheel events directly."""
        print(f"Direct wheel event: {event.angleDelta()}")
        self.camera_controller.handle_wheel(event)
        super().wheelEvent(event)
    
    def eventFilter(self, obj, event):
        """Event filter for custom mouse handling."""
        # Handle events on both container and view
        if obj in [self.container, self.view]:
            event_type = event.type()
            
            # Debug: Print event types to see what we're getting
            if event_type in [QtCore.QEvent.Type.MouseButtonPress, QtCore.QEvent.Type.MouseButtonRelease, 
                             QtCore.QEvent.Type.MouseMove, QtCore.QEvent.Type.Wheel]:
                print(f"Event Filter - Obj: {obj.__class__.__name__}, Event: {event_type}, Button: {getattr(event, 'button', lambda: 'N/A')() if hasattr(event, 'button') else 'N/A'}")
            
            if event_type == QtCore.QEvent.Type.MouseButtonPress:
                print(f"Event filter mouse press: {event.button()}")
                self.camera_controller.handle_mouse_press(event)
                # Change cursor during navigation
                if hasattr(event, 'button'):
                    if event.button() == Qt.MouseButton.MiddleButton:
                        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                            self.container.setCursor(Qt.CursorShape.SizeAllCursor)  # Pan cursor
                        else:
                            self.container.setCursor(Qt.CursorShape.ClosedHandCursor)  # Orbit cursor
                    elif event.button() == Qt.MouseButton.RightButton:
                        self.container.setCursor(Qt.CursorShape.SizeVerCursor)  # Zoom cursor
                return True
                
            elif event_type == QtCore.QEvent.Type.MouseButtonRelease:
                print(f"Event filter mouse release: {event.button()}")
                self.camera_controller.handle_mouse_release(event)
                # Reset cursor
                self.container.setCursor(Qt.CursorShape.ArrowCursor)
                return True
                
            elif event_type == QtCore.QEvent.Type.MouseMove:
                self.camera_controller.handle_mouse_move(event)
                return True
                
            elif event_type == QtCore.QEvent.Type.Wheel:
                print(f"Event filter wheel: {event.angleDelta()}")
                self.camera_controller.handle_wheel(event)
                return True
                
        return super().eventFilter(obj, event)

    def set_camera_distance(self, d: float):
        self.camera_controller.spherical[0] = max(0.2, float(d))
        self.camera_controller._apply_camera_from_spherical()
        # Update backwards compatibility references
        self.spherical = self.camera_controller.spherical

    def set_camera_azimuth(self, deg: float):
        self.camera_controller.spherical[1] = float(deg)
        self.camera_controller._apply_camera_from_spherical()
        self.spherical = self.camera_controller.spherical

    def set_camera_elevation(self, deg: float):
        self.camera_controller.spherical[2] = float(deg)
        self.camera_controller._apply_camera_from_spherical()
        self.spherical = self.camera_controller.spherical

    def reset_view(self):
        self.camera_controller.reset_view()
        # Update backwards compatibility references
        self.view_center = self.camera_controller.view_center
        self.spherical = self.camera_controller.spherical

    def clear_model(self):
        if self.model_entity is not None:
            self.model_entity.setParent(None)
            self.model_entity.deleteLater()
            self.model_entity = None
            self.original_materials = {}
            self.texture_cache.clear()  # Clear texture cache when clearing model
            self.current_dff = None  # Clear DFF reference

    def load_obj(self, path: str):
        self.clear_model()

        ent = QEntity(self.root)
        mesh = QMesh(ent)
        mesh.setSource(QUrl.fromLocalFile(path))

        transform = QTransform(ent)
        material = QPhongMaterial(ent)
        material.setDiffuse(QtGui.QColor(200, 200, 220))

        ent.addComponent(mesh)
        ent.addComponent(transform)
        ent.addComponent(material)

        self.model_entity = ent
        self.set_camera_distance(12.0)
        self.cam.setViewCenter(QtGui.QVector3D(0, 0, 0))
        

    def load_dff(self, path: str):
        self.clear_model()
        try:
            dff_file = dff()
            dff_file.load_file(path)
            self.current_dff = dff_file  # Store reference for texture name extraction
        except Exception as e:
            QMessageBox.critical(self, "DFF Parse Error", f"Could not parse DFF file: {e}")
            return

        # Remember the current file path for reload
        self.current_dff_path = path

        ent = QEntity(self.root)
        min_vec = QtGui.QVector3D(float('inf'), float('inf'), float('inf'))
        max_vec = QtGui.QVector3D(float('-inf'), float('-inf'), float('-inf'))
        
        # Dictionary to hold the created entities for mapping
        geometry_entities_map = {}

        # --- Build frame hierarchy world transforms ---
        # Represent each frame as rotation axes (right, up, at) and position.
        from collections import namedtuple
        AxesPos = namedtuple('AxesPos', 'rx ry rz ux uy uz ax ay az px py pz')

        def _local_axes_pos(frame) -> AxesPos:
            m = frame.rotation_matrix
            p = frame.position
            return AxesPos(
                m.right.x, m.right.y, m.right.z,
                m.up.x,    m.up.y,    m.up.z,
                m.at.x,    m.at.y,    m.at.z,
                p.x, p.y, p.z
            )

        def _mul3x3(a, b):
            # a,b are 3x3 as tuples in row-major: rows are (rx,ry,rz), (ux,uy,uz), (ax,ay,az)
            return (
                a[0]*b[0] + a[1]*b[3] + a[2]*b[6],
                a[0]*b[1] + a[1]*b[4] + a[2]*b[7],
                a[0]*b[2] + a[1]*b[5] + a[2]*b[8],

                a[3]*b[0] + a[4]*b[3] + a[5]*b[6],
                a[3]*b[1] + a[4]*b[4] + a[5]*b[7],
                a[3]*b[2] + a[4]*b[5] + a[5]*b[8],

                a[6]*b[0] + a[7]*b[3] + a[8]*b[6],
                a[6]*b[1] + a[7]*b[4] + a[8]*b[7],
                a[6]*b[2] + a[7]*b[5] + a[8]*b[8],
            )

        def _mul_vec3(mat, v):
            # mat is 3x3 row-major as tuple len 9; v is (x,y,z)
            return (
                mat[0]*v[0] + mat[1]*v[1] + mat[2]*v[2],
                mat[3]*v[0] + mat[4]*v[1] + mat[5]*v[2],
                mat[6]*v[0] + mat[7]*v[1] + mat[8]*v[2],
            )

        frame_world_mats: list[QMatrix4x4] = []
        parents: list[int] = []
        locals_axes: list[tuple] = []
        locals_pos: list[tuple] = []

        if hasattr(dff_file, 'frame_list') and dff_file.frame_list:
            # Pre-size arrays
            count = len(dff_file.frame_list)
            frame_world_mats = [QMatrix4x4() for _ in range(count)]
            parents = [ -1 for _ in range(count) ]
            locals_axes = [None for _ in range(count)]
            locals_pos = [None for _ in range(count)]

            for idx, f in enumerate(dff_file.frame_list):
                ap = _local_axes_pos(f)
                locals_axes[idx] = (ap.rx, ap.ry, ap.rz, ap.ux, ap.uy, ap.uz, ap.ax, ap.ay, ap.az)
                locals_pos[idx] = (ap.px, ap.py, ap.pz)
                parents[idx] = getattr(f, 'parent', -1)

            def build_world(use_parent_times_local: bool):
                computed = [False] * len(dff_file.frame_list)
                w_axes = [None] * len(dff_file.frame_list)
                w_pos = [None] * len(dff_file.frame_list)

                def compute(idx: int):
                    if computed[idx]:
                        return w_axes[idx], w_pos[idx]
                    parent = parents[idx]
                    laxes = locals_axes[idx]
                    lpos = locals_pos[idx]
                    if parent is not None and parent >= 0 and parent < len(locals_axes):
                        p_axes, p_pos = compute(parent)
                        if use_parent_times_local:
                            axes = _mul3x3(p_axes, laxes)
                            t = _mul_vec3(p_axes, lpos)
                            pos = (t[0] + p_pos[0], t[1] + p_pos[1], t[2] + p_pos[2])
                        else:
                            axes = _mul3x3(laxes, p_axes)
                            t = _mul_vec3(laxes, p_pos)
                            pos = (lpos[0] + t[0], lpos[1] + t[1], lpos[2] + t[2])
                    else:
                        axes = laxes
                        pos = lpos
                    w_axes[idx] = axes
                    w_pos[idx] = pos
                    computed[idx] = True
                    return axes, pos

                for i in range(len(dff_file.frame_list)):
                    compute(i)
                # Variance score of positions to detect collapse
                if w_pos:
                    cx = sum(p[0] for p in w_pos) / len(w_pos)
                    cy = sum(p[1] for p in w_pos) / len(w_pos)
                    cz = sum(p[2] for p in w_pos) / len(w_pos)
                    var = sum((p[0]-cx)**2 + (p[1]-cy)**2 + (p[2]-cz)**2 for p in w_pos) / len(w_pos)
                else:
                    var = 0.0
                return w_axes, w_pos, var

            axes_a, pos_a, var_a = build_world(True)   # parent * local
            axes_b, pos_b, var_b = build_world(False)  # local * parent

            chosen_axes = axes_a if var_a >= var_b else axes_b
            chosen_pos = pos_a if var_a >= var_b else pos_b

            # Build QMatrix4x4 list by assigning in place
            for idx in range(len(dff_file.frame_list)):
                axes = chosen_axes[idx]
                pos = chosen_pos[idx]
                frame_world_mats[idx] = QMatrix4x4(
                    axes[0], axes[3], axes[6], pos[0],
                    axes[1], axes[4], axes[7], pos[1],
                    axes[2], axes[5], axes[8], pos[2],
                    0, 0, 0, 1
                )

            # Minimal debug: print which convention chosen and a few sample positions
            try:
                print(f"[DFF Viewer] Transform order chosen: {'parent*local' if var_a >= var_b else 'local*parent'} (var_a={var_a:.3f}, var_b={var_b:.3f})")
                for i in range(min(5, len(chosen_pos))):
                    px,py,pz = chosen_pos[i]
                    print(f"  Frame {i}: parent={parents[i]} world_pos=({px:.3f},{py:.3f},{pz:.3f})")
            except Exception:
                pass

        for atomic in dff_file.atomic_list:
            if atomic.geometry >= len(dff_file.geometry_list):
                continue
            geo = dff_file.geometry_list[atomic.geometry]
            if not geo.vertices or not geo.triangles:
                continue

            part_entity = QEntity(ent)
            # Store the entity in our map using its geometry index
            geometry_entities_map[atomic.geometry] = part_entity
            
            vertex_byte_array = QByteArray()
            index_byte_array = QByteArray()
            
            has_normals = len(geo.normals) == len(geo.vertices)
            has_uvs = len(geo.uv_layers) > 0 and len(geo.uv_layers[0]) == len(geo.vertices)

            for i, v in enumerate(geo.vertices):
                vertex_byte_array.append(struct.pack('<3f', v.x, v.y, v.z))
                min_vec.setX(min(min_vec.x(), v.x)); min_vec.setY(min(min_vec.y(), v.y)); min_vec.setZ(min(min_vec.z(), v.z))
                max_vec.setX(max(max_vec.x(), v.x)); max_vec.setY(max(max_vec.y(), v.y)); max_vec.setZ(max(max_vec.z(), v.z))
                
                n = geo.normals[i] if has_normals else Vector(0.0, 1.0, 0.0)
                vertex_byte_array.append(struct.pack('<3f', n.x, n.y, n.z))

                uv_tuple = (0.0, 0.0)
                if has_uvs:
                    uv = geo.uv_layers[0][i]
                    uv_tuple = (uv.u, 1.0 - uv.v) # Invert V for OpenGL
                
                vertex_byte_array.append(struct.pack('<2f', *uv_tuple))

            for tri in geo.triangles:
                index_byte_array.append(struct.pack('<3H', tri.a, tri.b, tri.c)) # Use original winding order

            vertex_buffer = Qt3DBuffer(part_entity)
            vertex_buffer.setData(vertex_byte_array)
            index_buffer = Qt3DBuffer(part_entity)
            index_buffer.setData(index_byte_array)

            qt_geometry = QGeometry(part_entity)
            stride = 8 * 4  # 3f pos, 3f normal, 2f uv

            pos_attr = QAttribute(qt_geometry)
            pos_attr.setName(QAttribute.defaultPositionAttributeName())
            pos_attr.setBuffer(vertex_buffer)
            pos_attr.setVertexBaseType(QAttribute.VertexBaseType.Float)
            pos_attr.setVertexSize(3)
            pos_attr.setAttributeType(QAttribute.AttributeType.VertexAttribute)
            pos_attr.setByteStride(stride)
            pos_attr.setByteOffset(0)
            pos_attr.setCount(len(geo.vertices))

            norm_attr = QAttribute(qt_geometry)
            norm_attr.setName(QAttribute.defaultNormalAttributeName())
            norm_attr.setBuffer(vertex_buffer)
            norm_attr.setVertexBaseType(QAttribute.VertexBaseType.Float)
            norm_attr.setVertexSize(3)
            norm_attr.setAttributeType(QAttribute.AttributeType.VertexAttribute)
            norm_attr.setByteStride(stride)
            norm_attr.setByteOffset(3 * 4)
            norm_attr.setCount(len(geo.vertices))

            uv_attr = QAttribute(qt_geometry)
            uv_attr.setName(QAttribute.defaultTextureCoordinateAttributeName())
            uv_attr.setBuffer(vertex_buffer)
            uv_attr.setVertexBaseType(QAttribute.VertexBaseType.Float)
            uv_attr.setVertexSize(2)
            uv_attr.setAttributeType(QAttribute.AttributeType.VertexAttribute)
            uv_attr.setByteStride(stride)
            uv_attr.setByteOffset(6 * 4)
            uv_attr.setCount(len(geo.vertices))

            idx_attr = QAttribute(qt_geometry)
            idx_attr.setBuffer(index_buffer)
            idx_attr.setVertexBaseType(QAttribute.VertexBaseType.UnsignedShort)
            idx_attr.setAttributeType(QAttribute.AttributeType.IndexAttribute)
            idx_attr.setCount(len(geo.triangles) * 3)

            qt_geometry.addAttribute(pos_attr)
            qt_geometry.addAttribute(norm_attr) 
            qt_geometry.addAttribute(uv_attr)
            qt_geometry.addAttribute(idx_attr)

            renderer = QGeometryRenderer(part_entity)
            renderer.setGeometry(qt_geometry)
            # Ensure proper rendering settings for solid geometry
            renderer.setPrimitiveType(QGeometryRenderer.PrimitiveType.Triangles)

            transform = QTransform(part_entity)
            # Apply full world transform so children follow hierarchy
            if atomic.frame < len(frame_world_mats):
                transform.setMatrix(frame_world_mats[atomic.frame])

            # --- Material and Render States ---

            material = QPhongMaterial(part_entity)
            material.setAmbient(QtGui.QColor(40, 40, 50)) # Add slight ambient color
            mat_color = QtGui.QColor(200, 200, 220, 255)  # Ensure full opacity
            if geo.materials and geo.materials[0].color:
                c = geo.materials[0].color
                # Force full opacity to prevent translucency
                mat_color.setRgb(c.r, c.g, c.b, 255)
            
            material.setDiffuse(mat_color)
            # Ensure material specular is not too bright (can cause transparency effects)
            material.setSpecular(QtGui.QColor(64, 64, 64, 255))
            material.setShininess(32.0)
            self.original_materials[id(material)] = {'diffuse': mat_color}

            part_entity.addComponent(renderer)
            part_entity.addComponent(transform) 
            part_entity.addComponent(material)

        self.model_entity = ent
        if min_vec.x() != float('inf'):
            self.camera_controller.focus_on_bounds(min_vec, max_vec)
            # Update backwards compatibility references
            self.view_center = self.camera_controller.view_center
            self.spherical = self.camera_controller.spherical
        else:
            self.reset_view()

        # Emit the loaded dff file and the new entity map
        self.dff_loaded.emit(dff_file, geometry_entities_map)

    def load_txd(self, path: str):
        """Load a TXD file to provide textures for the current model."""
        try:
            txd_file = txd()
            txd_file.load_file(path)
            self.current_txd = txd_file
            self.current_txd_path = path
            
            # Clear texture cache when loading new TXD
            self.texture_cache.clear()
            
            # Apply textures to current model if available
            self._apply_textures_to_model()
            
            print(f"[DFF Viewer] Loaded TXD: {path}")
            print(f"  Native Textures: {len(txd_file.native_textures)}")
            
        except Exception as e:
            QMessageBox.critical(self, "TXD Load Error", f"Could not load TXD file: {e}")
            print(f"[DFF Viewer] TXD load error: {e}")

    def _create_qt3d_texture_from_native(self, native_texture: TextureNative) -> QTexture2D | None:
        """Convert a TXD native texture to Qt3D texture."""
        try:
            # Get RGBA data from the native texture
            rgba_data = native_texture.to_rgba(level=0)
            if not rgba_data:
                return None
                
            width = native_texture.get_width(0)
            height = native_texture.get_height(0)
            
            print(f"[DFF Viewer] Creating Qt3D texture: {native_texture.name} ({width}x{height})")
            
            # Create Qt3D texture with proper initialization for RGBA format
            texture = QTexture2D()
            texture.setFormat(QAbstractTexture.TextureFormat.RGBA8_UNorm)  # Use RGBA format for better compatibility
            texture.setWidth(width)
            texture.setHeight(height)
            texture.setLayers(1)
            texture.setMipLevels(1)
            texture.setGenerateMipMaps(False)  # Disable mipmaps for now
            
            # Create texture image from data
            texture_image = QTextureImage()
            
            # Convert RGBA data to QImage and save temporarily
            import tempfile
            import os
            qimage = QImage(rgba_data, width, height, QImage.Format.Format_RGBA8888)
            
            # Create a temporary file to hold the texture
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"dff_viewer_texture_{native_texture.name}_{id(self)}.png")
            qimage.save(temp_path, "PNG")
            
            # Set the texture image source
            texture_image.setSource(QUrl.fromLocalFile(temp_path))
            texture.addTextureImage(texture_image)
            
            print(f"[DFF Viewer] Successfully created Qt3D texture for {native_texture.name}")
            return texture
            
        except Exception as e:
            print(f"[DFF Viewer] Error creating Qt3D texture: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _get_required_texture_names(self):
        """Extract required texture names from the loaded DFF file."""
        required_textures = []
        
        if not hasattr(self, 'current_dff') or not self.current_dff:
            print("[DFF Viewer] No DFF file loaded to extract texture names")
            return required_textures
        
        try:
            # Check geometry materials for texture references
            if hasattr(self.current_dff, 'geometry_list') and self.current_dff.geometry_list:
                for geometry in self.current_dff.geometry_list:
                    if hasattr(geometry, 'materials') and geometry.materials:
                        for material in geometry.materials:
                            # Check for texture name in material
                            if hasattr(material, 'texture') and material.texture:
                                texture_name = material.texture
                                if texture_name and texture_name not in required_textures:
                                    required_textures.append(texture_name)
                                    print(f"[DFF Viewer] Found required texture: {texture_name}")
                            
                            # Also check textures array if it exists
                            if hasattr(material, 'textures') and material.textures:
                                for tex in material.textures:
                                    if hasattr(tex, 'name') and tex.name:
                                        texture_name = tex.name
                                        if texture_name and texture_name not in required_textures:
                                            required_textures.append(texture_name)
                                            print(f"[DFF Viewer] Found required texture: {texture_name}")
            
            print(f"[DFF Viewer] Total required textures found: {len(required_textures)}")
            
        except Exception as e:
            print(f"[DFF Viewer] Error extracting texture names: {e}")
            import traceback
            traceback.print_exc()
        
        return required_textures

    def _apply_textures_to_model(self):
        """Apply loaded TXD textures to the current DFF model."""
        if not self.current_txd or not self.model_entity:
            return
            
        try:
            # Find all geometry renderer entities in the current model
            renderers = self.model_entity.findChildren(QGeometryRenderer)
            
            print(f"[DFF Viewer] Applying textures - found {len(renderers)} geometry renderers, {len(self.current_txd.native_textures)} textures")
            
            if not self.current_txd.native_textures:
                print("[DFF Viewer] No textures in TXD to apply")
                return
            
            # Get required texture names from the DFF materials
            required_textures = self._get_required_texture_names()
            print(f"[DFF Viewer] Required textures from DFF: {required_textures}")
            
            # Create a mapping of available textures by name
            available_textures = {tex.name.lower(): tex for tex in self.current_txd.native_textures}
            print(f"[DFF Viewer] Available textures in TXD: {list(available_textures.keys())}")
            
            # Apply textures to geometry renderers by matching required textures
            applied_count = 0
            missing_textures = []
            
            for i, renderer in enumerate(renderers):
                # Get the parent entity of this renderer
                parent_entity = renderer.parent()
                if not parent_entity:
                    continue
                
                # Try to find the required texture for this geometry
                required_texture_name = None
                if i < len(required_textures):
                    required_texture_name = required_textures[i]
                elif required_textures:
                    # If we have fewer required textures than geometries, use the first one
                    required_texture_name = required_textures[0]
                
                if not required_texture_name:
                    print(f"[DFF Viewer] No required texture found for geometry {i}")
                    continue
                
                # Look for the texture in TXD (case-insensitive)
                native_texture = available_textures.get(required_texture_name.lower())
                
                if not native_texture:
                    # Texture not found in TXD
                    missing_texture = required_texture_name
                    if missing_texture not in missing_textures:
                        missing_textures.append(missing_texture)
                        print(f"[DFF Viewer] Missing texture: {missing_texture}")
                    continue
                
                print(f"[DFF Viewer] Applying texture '{native_texture.name}' to geometry {i}")
                
                # Create Qt3D texture if not cached
                if native_texture.name not in self.texture_cache:
                    qt3d_texture = self._create_qt3d_texture_from_native(native_texture)
                    if qt3d_texture:
                        self.texture_cache[native_texture.name] = qt3d_texture
                
                # Get texture from cache
                qt3d_texture = self.texture_cache.get(native_texture.name)
                if qt3d_texture and isinstance(qt3d_texture, QTexture2D):
                    # Remove old material and create new textured material
                    old_materials = parent_entity.findChildren(QPhongMaterial)
                    for old_mat in old_materials:
                        parent_entity.removeComponent(old_mat)
                        old_mat.deleteLater()
                    
                    # Create new material with diffuse map
                    textured_material = QDiffuseMapMaterial()
                    textured_material.setDiffuse(qt3d_texture)
                    textured_material.setAmbient(QtGui.QColor(20, 20, 20, 255))  # Darker ambient to avoid washing out texture
                    textured_material.setSpecular(QtGui.QColor(0, 0, 0, 255))  # No specular highlight for textured surfaces
                    textured_material.setShininess(2.0)  # Low shininess
                    
                    parent_entity.addComponent(textured_material)
                    applied_count += 1
                    
                    print(f"[DFF Viewer] Applied Qt3D texture {native_texture.name} to geometry {i}")
                else:
                    print(f"[DFF Viewer] Failed to create/apply texture for {native_texture.name}")
            
            # Show messages for missing textures
            if missing_textures:
                missing_list = ', '.join(missing_textures)
                message = f"Missing textures from TXD: {missing_list}. These textures will not be shown."
                QMessageBox.warning(None, "Missing Textures", message)
                print(f"[DFF Viewer] Warning: {message}")
                        
            print(f"[DFF Viewer] Successfully applied {applied_count} textures to {len(renderers)} geometries")
                            
        except Exception as e:
            print(f"[DFF Viewer] Error applying textures: {e}")
            import traceback
            traceback.print_exc()

    def clear_txd(self):
        """Clear loaded TXD and revert materials to original colors."""
        self.current_txd = None
        self.current_txd_path = None
        self.texture_cache.clear()
        
        # Revert materials to original colors by reloading the DFF
        if self.current_dff_path:
            print("[DFF Viewer] Reloading DFF to restore original materials")
            self.load_dff(self.current_dff_path)
        else:
            # If no DFF path, just recreate basic materials
            if self.model_entity:
                renderers = self.model_entity.findChildren(QGeometryRenderer)
                for renderer in renderers:
                    parent_entity = renderer.parent()
                    if parent_entity:
                        # Remove any existing materials
                        old_materials = parent_entity.findChildren(QPhongMaterial) + parent_entity.findChildren(QDiffuseMapMaterial)
                        for old_mat in old_materials:
                            parent_entity.removeComponent(old_mat)
                            old_mat.deleteLater()
                        
                        # Create new basic material
                        material = QPhongMaterial(parent_entity)
                        material.setDiffuse(QtGui.QColor(200, 200, 220))
                        material.setAmbient(QtGui.QColor(40, 40, 50))
                        parent_entity.addComponent(material)

    def reload(self):
        """Reload the last loaded DFF file, if any."""
        if self.current_dff_path:
            self.load_dff(self.current_dff_path)
            # Also reload TXD if one was loaded
            if self.current_txd_path:
                self.load_txd(self.current_txd_path)

    def set_background_color(self, color: QColor):
        self.view.defaultFrameGraph().setClearColor(color)


class CameraDock(QWidget):
    distanceChanged = pyqtSignal(float)
    azimuthChanged = pyqtSignal(float)
    elevationChanged = pyqtSignal(float)
    bgColorPicked = pyqtSignal(QColor)

    def __init__(self, parent=None, init_spherical=(8.0, 35.0, 35.0)):
        super().__init__(parent)
        d0, az0, el0 = init_spherical

        def labelled_slider(label: str, minimum: int, maximum: int, value: int, step: int = 1):
            box = QWidget()
            v = QVBoxLayout(box); v.setContentsMargins(0, 0, 0, 0)
            v.addWidget(QLabel(label))
            h = QHBoxLayout()
            s = QSlider(Qt.Orientation.Horizontal); s.setRange(minimum, maximum); s.setSingleStep(step); s.setValue(value)
            spin = QSpinBox(); spin.setRange(minimum, maximum); spin.setSingleStep(step); spin.setValue(value)
            s.valueChanged.connect(spin.setValue)
            spin.valueChanged.connect(s.setValue)
            h.addWidget(s); h.addWidget(spin)
            v.addLayout(h)
            return box, s

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        box_d, s_d = labelled_slider("Distance", 1, 2000, int(d0 * 10), 1)
        layout.addWidget(box_d)
        s_d.valueChanged.connect(lambda v: self.distanceChanged.emit(v / 10.0))

        box_az, s_az = labelled_slider("Azimuth", -180, 180, int(az0), 1)
        layout.addWidget(box_az)
        s_az.valueChanged.connect(lambda v: self.azimuthChanged.emit(float(v)))

        box_el, s_el = labelled_slider("Elevation", -89, 89, int(el0), 1)
        layout.addWidget(box_el)
        s_el.valueChanged.connect(lambda v: self.elevationChanged.emit(float(v)))

        self.btn_bg = QPushButton("Background color…")
        self.btn_bg.clicked.connect(self.pick_bg)
        layout.addWidget(self.btn_bg)

        layout.addStretch(1)

    def pick_bg(self):
        col = QColorDialog.getColor(QtGui.QColor(30, 30, 34), self, "Pick background color")
        if col.isValid():
            self.bgColorPicked.emit(col)


class DFFViewerMainWindow(QWidget):
    """Suite-integrated DFF Viewer main interface with docking panels."""
    tool_action = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.debug = get_debug_logger() if callable(get_debug_logger) else None
        
        # --- State management for highlighting ---
        self.item_to_geo_entity_map = {}
        self.item_to_frame_data_map = {}
        
        self.highlighted_entity = None
        self.highlighted_material_original_color = None
        self.axis_gizmo_entity = None
        # --- End state management ---

        self._setup_ui()
        self._connect_signals()
        
        # Initialize with welcome message
        self._show_status("DFF Viewer ready. Use 'Open DFF...' to load a model.")
        
        # Hide TXD controls initially
        self._show_txd_controls(False)

    def _setup_ui(self):
        """Setup the main UI layout with responsive design."""
        rm = get_responsive_manager()
        fonts = rm.get_font_config()
        spacing = rm.get_spacing_config()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(spacing['small'], spacing['small'], spacing['small'], spacing['small'])
        main_layout.setSpacing(spacing['medium'])
        
        # Header with controls
        self._create_header(fonts, spacing)
        
        # Main content area with splitter for docking
        self._create_content_area()
        
        # Status area
        self._create_status_area(fonts)
        
        main_layout.addWidget(self.header_widget)
        main_layout.addWidget(self.content_splitter, 1)
        main_layout.addWidget(self.status_widget)
    
    def _create_header(self, fonts, spacing):
        """Create header with tool controls."""
        self.header_widget = QWidget()
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(spacing['medium'])
        
        # Title
        title = QLabel("📦 DFF Viewer")
        title.setStyleSheet(f"font-weight: bold; font-size: {fonts['header']['size']}px; color: {ModernDarkTheme.TEXT_ACCENT};")
        header_layout.addWidget(title)
        
        header_layout.addStretch(1)
        
        # Control buttons
        self.btn_open = QPushButton("Open DFF...")
        self.btn_load_txd = QPushButton("Load TXD...")
        self.btn_clear_txd = QPushButton("Clear TXD")
        self.btn_reload = QPushButton("Reload")
        self.btn_reset_view = QPushButton("Reset View")
        self.btn_background = QPushButton("Background...")
        self.btn_debug = QPushButton("Debug Parse")
        
        # Initially hide TXD-related buttons until a DFF is loaded
        self.btn_load_txd.setVisible(False)
        self.btn_clear_txd.setVisible(False)
        
        # Style buttons
        for btn in [self.btn_open, self.btn_load_txd, self.btn_clear_txd, self.btn_reload, self.btn_reset_view, self.btn_background, self.btn_debug]:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ModernDarkTheme.BACKGROUND_TERTIARY};
                    border: 1px solid {ModernDarkTheme.BORDER_PRIMARY};
                    padding: {spacing['small']}px {spacing['medium']}px;
                    border-radius: 4px;
                    font-size: {fonts['body']['size']}px;
                }}
                QPushButton:hover {{
                    background-color: {ModernDarkTheme.BORDER_PRIMARY};
                }}
                QPushButton:pressed {{
                    background-color: {ModernDarkTheme.TEXT_ACCENT};
                }}
            """)
        
        header_layout.addWidget(self.btn_open)
        header_layout.addWidget(self.btn_load_txd)
        header_layout.addWidget(self.btn_clear_txd)
        header_layout.addWidget(self.btn_reload)
        header_layout.addWidget(self.btn_reset_view)
        header_layout.addWidget(self.btn_background)
        header_layout.addWidget(self.btn_debug)
        header_layout.addWidget(self.btn_debug)
    
    def _create_content_area(self):
        """Create main content area with splitter for docking."""
        self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - 3D Viewer
        self.viewer = Viewer3D(self)
        self.content_splitter.addWidget(self.viewer)
        
        # Right panel - Controls and Inspector
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(6, 6, 6, 6)
        
        # Camera controls
        self._create_camera_controls(right_layout)
        
        # DFF Inspector
        self._create_inspector_panel(right_layout)
        
        self.content_splitter.addWidget(self.right_panel)
        
        # Set splitter proportions (3D viewer gets more space)
        self.content_splitter.setSizes([800, 300])
        self.content_splitter.setStretchFactor(0, 1)
        self.content_splitter.setStretchFactor(1, 0)
    
    def _create_camera_controls(self, parent_layout):
        """Create camera control panel."""
        camera_group = QGroupBox("Camera & Display")
        camera_layout = QVBoxLayout(camera_group)
        
        # Create camera dock widget (reuse existing logic)
        self.camera_controls = CameraDock(self, init_spherical=tuple(self.viewer.spherical))
        camera_layout.addWidget(self.camera_controls)
        
        # Add navigation help
        help_label = QLabel("""<b>Navigation Controls:</b><br>
        • <b>Middle Mouse:</b> Orbit around model<br>
        • <b>Shift + Middle Mouse:</b> Pan view<br>
        • <b>Mouse Wheel:</b> Zoom in/out<br>
        • <b>Shift + Left Mouse:</b> Orbit (alternative)<br>
        • <b>Ctrl + Left Mouse:</b> Pan (alternative)<br>
        • <b>Right Mouse:</b> Zoom (drag up/down)""")
        help_label.setWordWrap(True)
        help_label.setStyleSheet("QLabel { font-size: 10px; color: #888; padding: 8px; background-color: #2a2a2a; border-radius: 4px; }")
        camera_layout.addWidget(help_label)
        
        
        parent_layout.addWidget(camera_group)
    
    def _create_inspector_panel(self, parent_layout):
        """Create DFF inspector panel."""
        inspector_group = QGroupBox("DFF Inspector")
        inspector_layout = QVBoxLayout(inspector_group)
        
        self.inspector_tree = QTreeWidget()
        self.inspector_tree.setHeaderLabels(["Property", "Value"])
        self.inspector_tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        inspector_layout.addWidget(self.inspector_tree)
        
        parent_layout.addWidget(inspector_group)
    
    def _create_status_area(self, fonts):
        """Create status display area."""
        self.status_widget = QWidget()
        status_layout = QHBoxLayout(self.status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: #bbb; font-size: {fonts['small']['size']}px;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch(1)
    
    def _connect_signals(self):
        """Connect all UI signals."""
        # Button connections
        self.btn_open.clicked.connect(self._on_open_file)
        self.btn_load_txd.clicked.connect(self._on_load_txd)
        self.btn_clear_txd.clicked.connect(self._on_clear_txd)
        self.btn_reload.clicked.connect(self.viewer.reload)
        self.btn_reset_view.clicked.connect(self.viewer.reset_view)
        self.btn_background.clicked.connect(self._on_pick_background)
        self.btn_debug.clicked.connect(self._on_debug_parse)
        
        # Camera control connections
        self.camera_controls.distanceChanged.connect(self.viewer.set_camera_distance)
        self.camera_controls.azimuthChanged.connect(self.viewer.set_camera_azimuth)
        self.camera_controls.elevationChanged.connect(self.viewer.set_camera_elevation)
        self.camera_controls.bgColorPicked.connect(self.viewer.set_background_color)
        
        # Viewer connections
        self.viewer.dff_loaded.connect(self._on_dff_loaded)
        
        # Inspector connections
        self.inspector_tree.currentItemChanged.connect(self._on_inspector_item_selected)

    def _show_status(self, message):
        """Show status message."""
        self.status_label.setText(message)
        if self.debug:
            self.debug.info(LogCategory.UI, "DFF Viewer status", {"message": message})
    
    def _show_txd_controls(self, show=True):
        """Show or hide TXD-related controls based on DFF model state."""
        self.btn_load_txd.setVisible(show)
        if not show:
            # Also hide clear button when hiding TXD controls
            self.btn_clear_txd.setVisible(False)
        elif self.viewer.current_txd:
            # Show clear button if TXD is loaded
            self.btn_clear_txd.setVisible(True)
    
    def _on_open_file(self):
        """Handle open file action."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open DFF Model", "", "GTA DFF (*.dff);;Wavefront OBJ (*.obj)")
        if path:
            self._show_status(f"Loading: {path}")
            QtWidgets.QApplication.processEvents()
            
            if path.lower().endswith('.dff'):
                self.viewer.load_dff(path)
                # Show TXD controls after successful DFF load
                self._show_txd_controls(True)
            elif path.lower().endswith('.obj'):
                self.viewer.load_obj(path)
                # OBJ files don't support TXD textures
                self._show_txd_controls(False)
            
            self._show_status(f"Loaded: {path}")
            self.tool_action.emit("file_loaded", path)
    
    def _on_pick_background(self):
        """Handle background color picker."""
        color = QColorDialog.getColor(QtGui.QColor(30, 30, 34), self, "Pick background color")
        if color.isValid():
            self.viewer.set_background_color(color)
            self.tool_action.emit("background_changed", color.name())
    
    def _on_load_txd(self):
        """Handle load TXD action."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Load TXD Texture Archive", "", "GTA TXD (*.txd)")
        if path:
            self._show_status(f"Loading TXD: {path}")
            QtWidgets.QApplication.processEvents()
            
            self.viewer.load_txd(path)
            
            # Update status with TXD info
            if self.viewer.current_txd:
                texture_count = len(self.viewer.current_txd.native_textures)
                self._show_status(f"✔ Loaded TXD: {texture_count} textures from {path}")
                self.tool_action.emit("txd_loaded", f"{texture_count} textures from {path}")
                # Show clear TXD button when TXD is successfully loaded
                self.btn_clear_txd.setVisible(True)
                # Refresh inspector to show TXD information
                self._populate_inspector(self.viewer.current_dff, None)
            else:
                self._show_status("✗ Failed to load TXD")
    
    def _on_clear_txd(self):
        """Handle clear TXD action."""
        if self.viewer.current_txd:
            self.viewer.clear_txd()
            self._show_status("✔ TXD textures cleared - reverted to original materials")
            self.tool_action.emit("txd_cleared", "Textures cleared")
            # Hide clear TXD button after clearing
            self.btn_clear_txd.setVisible(False)
            # Refresh inspector to remove TXD information
            self._populate_inspector(self.viewer.current_dff, None)
        else:
            self._show_status("No TXD loaded to clear")
    
    def _on_dff_loaded(self, dff_file, geo_entity_map):
        """Handle DFF file loaded event."""
        # Update status
        frames = len(getattr(dff_file, 'frame_list', []) or [])
        geometries = len(getattr(dff_file, 'geometry_list', []) or [])
        atomics = len(getattr(dff_file, 'atomic_list', []) or [])
        
        status_text = f"Loaded DFF • Frames: {frames} • Geometries: {geometries} • Atomics: {atomics}"
        
        # Add TXD info if available
        if self.viewer.current_txd:
            texture_count = len(self.viewer.current_txd.native_textures)
            status_text += f" • TXD: {texture_count} textures"
        
        self._show_status(status_text)
        
        # Show TXD controls now that a DFF is loaded
        self._show_txd_controls(True)
        
        # Populate inspector
        self._populate_inspector(dff_file, geo_entity_map)
        
        # Emit tool action
        self.tool_action.emit("dff_loaded", status_text)
    
    def _on_debug_parse(self):
        """Handle debug parse action."""
        if not self.viewer.current_dff_path:
            QMessageBox.information(self, "DFF Debug", "Load a DFF file first.")
            return
        
        try:
            d = dff()
            d.load_file(self.viewer.current_dff_path)
            msg = {
                "frames": len(getattr(d, 'frame_list', []) or []),
                "geometries": len(getattr(d, 'geometry_list', []) or []),
                "atomics": len(getattr(d, 'atomic_list', []) or []),
                "rw_version": hex(getattr(d, 'rw_version', 0) or 0),
            }
            
            if self.debug:
                self.debug.info(LogCategory.TOOL if hasattr(LogCategory, 'TOOL') else LogCategory.UI, "DFF debug summary", msg)
            
            # Show debug info in a message box
            debug_text = f"""DFF Debug Information:
            
Frames: {msg['frames']}
Geometries: {msg['geometries']}
Atomics: {msg['atomics']}
RW Version: {msg['rw_version']}
            
File: {self.viewer.current_dff_path}"""
            
            QMessageBox.information(self, "DFF Debug Info", debug_text)
            self._show_status(f"✔ Debug: {msg}")
            self.tool_action.emit("debug", str(msg))
            
        except Exception as e:
            if self.debug:
                self.debug.log_exception(LogCategory.TOOL if hasattr(LogCategory, 'TOOL') else LogCategory.UI, "DFF debug failed", e)
            QMessageBox.critical(self, "DFF Debug", f"Debug failed: {e}")
            self._show_status(f"✗ Debug failed: {e}")

    def load_file(self, file_path):
        """Load a DFF, OBJ, or TXD file (external interface)."""
        if file_path.lower().endswith('.dff'):
            self.viewer.load_dff(file_path)
        elif file_path.lower().endswith('.obj'):
            self.viewer.load_obj(file_path)
        elif file_path.lower().endswith('.txd'):
            # Load TXD - requires a DFF to be loaded first
            if self.viewer.current_dff_path:
                self.viewer.load_txd(file_path)
                self._show_status(f"✔ Loaded TXD textures for current model")
            else:
                self._show_status("⚠ Load a DFF model first before loading TXD textures")
        else:
            self._show_status(f"Unsupported file format: {file_path}")
    
    def get_current_file(self):
        """Get currently loaded file path."""
        return getattr(self.viewer, 'current_dff_path', None)

    def _add_tree_child(self, parent, prop, val):
        item = QTreeWidgetItem(parent)
        item.setText(0, str(prop))
        item.setText(1, str(val))
        return item

    def _populate_inspector(self, dff_file: dff | None, geo_entity_map: dict | None):
        # Clear previous state and maps
        self._on_inspector_item_selected(None, None) # Clear any existing highlights
        self.inspector_tree.clear()
        self.item_to_geo_entity_map.clear()
        self.item_to_frame_data_map.clear()

        if dff_file is None:
            # If no DFF is loaded, still show TXD information if available
            if hasattr(self, 'viewer') and self.viewer.current_txd:
                txd_root = QTreeWidgetItem(self.inspector_tree, [f"TXD Textures ({len(self.viewer.current_txd.native_textures)})"])
                if self.viewer.current_txd_path:
                    self._add_tree_child(txd_root, "File Path", self.viewer.current_txd_path)
                self._add_tree_child(txd_root, "RW Version", f"0x{self.viewer.current_txd.rw_version:X}")
                self._add_tree_child(txd_root, "Device ID", str(self.viewer.current_txd.device_id))
                
                for i, native_tex in enumerate(self.viewer.current_txd.native_textures):
                    tex_item = self._add_tree_child(txd_root, f"Texture {i}", native_tex.name)
                    self._add_tree_child(tex_item, "Dimensions", f"{native_tex.get_width(0)}x{native_tex.get_height(0)}")
                    self._add_tree_child(tex_item, "Depth", f"{native_tex.depth} bits")
                    self._add_tree_child(tex_item, "Mip Levels", str(native_tex.num_levels))
                    self._add_tree_child(tex_item, "Platform ID", str(native_tex.platform_id))
                    self._add_tree_child(tex_item, "D3D Format", f"0x{native_tex.d3d_format:X}")
                    if hasattr(native_tex, 'mask') and native_tex.mask:
                        self._add_tree_child(tex_item, "Mask", native_tex.mask)
                
                self.inspector_tree.expandToDepth(1)
            return

        # --- File Info ---
        info_root = QTreeWidgetItem(self.inspector_tree, ["File Info"])
        self._add_tree_child(info_root, "RW Version", f"0x{dff_file.rw_version:X}")
        
        # ... existing DFF processing code ...
        
        # --- Frame List ---
        if dff_file.frame_list:
            frame_root = QTreeWidgetItem(self.inspector_tree, [f"Frame List ({len(dff_file.frame_list)})"])
            for i, frame in enumerate(dff_file.frame_list):
                frame_item = self._add_tree_child(frame_root, f"Frame {i}", frame.name)
                # FIX: Use id(item) as the key, not the item itself
                self.item_to_frame_data_map[id(frame_item)] = frame
                self._add_tree_child(frame_item, "Parent Index", frame.parent)
                pos = frame.position
                self._add_tree_child(frame_item, "Position", f"({pos.x:.3f}, {pos.y:.3f}, {pos.z:.3f})")
                if frame.bone_data:
                    self._populate_hanim_plugin(frame_item, frame.bone_data)
                if frame.user_data:
                    self._populate_userdata_plugin(frame_item, frame.user_data)

        # --- Geometry List ---
        if dff_file.geometry_list:
            geom_root = QTreeWidgetItem(self.inspector_tree, [f"Geometry List ({len(dff_file.geometry_list)})"])
            for i, geo in enumerate(dff_file.geometry_list):
                geom_item = self._add_tree_child(geom_root, f"Geometry {i}", "")
                # FIX: Use id(item) as the key
                if geo_entity_map and i in geo_entity_map:
                    self.item_to_geo_entity_map[id(geom_item)] = geo_entity_map[i]

                self._add_tree_child(geom_item, "Flags", f"0x{geo.flags:08X}")
                self._add_tree_child(geom_item, "Vertex Count", len(geo.vertices))
                self._add_tree_child(geom_item, "Triangle Count", len(geo.triangles))
                self._add_tree_child(geom_item, "UV Layer Count", len(geo.uv_layers))
                
                if geo.materials:
                    mat_root = self._add_tree_child(geom_item, f"Materials ({len(geo.materials)})", "")
                    for j, mat in enumerate(geo.materials):
                        mat_item = self._add_tree_child(mat_root, f"Material {j}", "")
                        self._add_tree_child(mat_item, "Color", f"({mat.color.r}, {mat.color.g}, {mat.color.b}, {mat.color.a})")
                        if mat.textures:
                            tex_root = self._add_tree_child(mat_item, f"Textures ({len(mat.textures)})", "")
                            for k, tex in enumerate(mat.textures):
                                tex_item = self._add_tree_child(tex_root, f"Texture {k}", "")
                                self._add_tree_child(tex_item, "Name", tex.name)
                                self._add_tree_child(tex_item, "Mask Name", tex.mask)
                
                if 'skin' in geo.extensions:
                    self._populate_skin_plugin(geom_item, geo.extensions['skin'])

        # --- Atomic List ---
        if dff_file.atomic_list:
            atomic_root = QTreeWidgetItem(self.inspector_tree, [f"Atomic List ({len(dff_file.atomic_list)})"])
            for i, atomic in enumerate(dff_file.atomic_list):
                atomic_item = self._add_tree_child(atomic_root, f"Atomic {i}", "")
                self._add_tree_child(atomic_item, "Frame Index", atomic.frame)
                self._add_tree_child(atomic_item, "Geometry Index", atomic.geometry)
                self._add_tree_child(atomic_item, "Flags", f"0x{atomic.flags:08X}")
        
        # --- TXD Information (if loaded) ---
        if hasattr(self, 'viewer') and self.viewer.current_txd:
            txd_root = QTreeWidgetItem(self.inspector_tree, [f"TXD Textures ({len(self.viewer.current_txd.native_textures)})"])
            if self.viewer.current_txd_path:
                self._add_tree_child(txd_root, "File Path", self.viewer.current_txd_path)
            self._add_tree_child(txd_root, "RW Version", f"0x{self.viewer.current_txd.rw_version:X}")
            self._add_tree_child(txd_root, "Device ID", str(self.viewer.current_txd.device_id))
            
            for i, native_tex in enumerate(self.viewer.current_txd.native_textures):
                tex_item = self._add_tree_child(txd_root, f"Texture {i}", native_tex.name)
                self._add_tree_child(tex_item, "Dimensions", f"{native_tex.get_width(0)}x{native_tex.get_height(0)}")
                self._add_tree_child(tex_item, "Depth", f"{native_tex.depth} bits")
                self._add_tree_child(tex_item, "Mip Levels", str(native_tex.num_levels))
                self._add_tree_child(tex_item, "Platform ID", str(native_tex.platform_id))
                self._add_tree_child(tex_item, "D3D Format", f"0x{native_tex.d3d_format:X}")
                if hasattr(native_tex, 'mask') and native_tex.mask:
                    self._add_tree_child(tex_item, "Mask", native_tex.mask)
        
        self.inspector_tree.expandToDepth(1)
    
    def cleanup(self):
        """Clean up resources when closing."""
        try:
            if hasattr(self, 'viewer') and self.viewer:
                self.viewer.clear_model()
            if self.debug:
                self.debug.info(LogCategory.TOOL, "DFF Viewer cleaned up successfully")
        except Exception as e:
            if self.debug:
                self.debug.warning(LogCategory.TOOL, "Error during DFF Viewer cleanup", {"error": str(e)})

    def _on_inspector_item_selected(self, current_item: QTreeWidgetItem, previous_item: QTreeWidgetItem):
        # --- 1. Clear any previous highlighting ---
        
        # Reset previously highlighted geometry
        if self.highlighted_entity:
            material = self.highlighted_entity.findChild(QPhongMaterial)
            if material and self.highlighted_material_original_color:
                material.setDiffuse(self.highlighted_material_original_color)
            self.highlighted_entity = None
            self.highlighted_material_original_color = None

        # Remove previously created gizmo
        if self.axis_gizmo_entity:
            self.axis_gizmo_entity.setParent(None)
            self.axis_gizmo_entity.deleteLater()
            self.axis_gizmo_entity = None

        if not current_item:
            return

        # --- 2. Apply new highlight based on item type ---
        
        # FIX: Check for id(current_item) in the map keys
        # If it's a geometry item
        if id(current_item) in self.item_to_geo_entity_map:
            entity = self.item_to_geo_entity_map[id(current_item)]
            material = entity.findChild(QPhongMaterial)
            if material:
                self.highlighted_material_original_color = material.diffuse()
                highlight_color = QtGui.QColor("#ffdd00") # Bright yellow
                material.setDiffuse(highlight_color)
                self.highlighted_entity = entity
        
        # FIX: Check for id(current_item) in the map keys
        # If it's a frame item
        elif id(current_item) in self.item_to_frame_data_map:
            frame_data = self.item_to_frame_data_map[id(current_item)]
            
            # Use model radius to scale gizmo appropriately
            model_size = self.viewer.spherical[0] / 3.0 # Heuristic for size
            gizmo_size = max(0.2, model_size * 0.1)

            self.axis_gizmo_entity = AxisGizmoEntity(self.viewer.root, length=gizmo_size, radius=gizmo_size*0.04)

            # Set the gizmo's transform based on the frame data
            gizmo_transform = QTransform()
            m = frame_data.rotation_matrix
            p = frame_data.position
            qmatrix = QMatrix4x4(m.right.x, m.up.x, m.at.x, p.x,
                                 m.right.y, m.up.y, m.at.y, p.y,
                                 m.right.z, m.up.z, m.at.z, p.z,
                                 0, 0, 0, 1).transposed()
            gizmo_transform.setMatrix(qmatrix)
            self.axis_gizmo_entity.addComponent(gizmo_transform)

    def _populate_skin_plugin(self, parent_item: QTreeWidgetItem, skin: SkinPLG):
        skin_item = self._add_tree_child(parent_item, "Skin Plugin", "")
        self._add_tree_child(skin_item, "Num Bones", skin.num_bones)
        self._add_tree_child(skin_item, "Max Weights / Vertex", skin.max_weights_per_vertex)
        self._add_tree_child(skin_item, "Used Bones", skin._num_used_bones)

    def _populate_hanim_plugin(self, parent_item: QTreeWidgetItem, hanim: HAnimPLG):
        hanim_item = self._add_tree_child(parent_item, "HAnim Plugin", "")
        self._add_tree_child(hanim_item, "Bone Count", hanim.header.bone_count)
        if hanim.bones:
            bones_item = self._add_tree_child(hanim_item, "Bones", "")
            for bone in hanim.bones:
                self._add_tree_child(bones_item, f"Bone ID {bone.id}", f"(Index: {bone.index}, Type: {bone.type})")

    def _populate_userdata_plugin(self, parent_item: QTreeWidgetItem, udata: UserData):
        udata_item = self._add_tree_child(parent_item, "User Data Plugin", "")
        for section in udata.sections:
            sec_item = self._add_tree_child(udata_item, "Section", section.name.strip())
            for i, data_val in enumerate(section.data):
                self._add_tree_child(sec_item, f"Data [{i}]", str(data_val))


class DFFViewerTool(QWidget):
    """Enhanced suite-integrated DFF Viewer tool widget with full functionality."""
    tool_action = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.debug = get_debug_logger() if callable(get_debug_logger) else None
        
        # Create the main viewer window as the core component
        self.main_viewer = DFFViewerMainWindow(self)
        
        # Connect signals
        if hasattr(self.main_viewer, 'tool_action'):
            self.main_viewer.tool_action.connect(self.tool_action)
        
        self._setup_ui()

    def _setup_ui(self):
        """Setup the tool UI with the main viewer embedded."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Embed the main viewer directly
        layout.addWidget(self.main_viewer)
    
    def load_file(self, file_path):
        """Load a file through the main viewer."""
        self.main_viewer.load_file(file_path)
    
    def get_current_file(self):
        """Get currently loaded file."""
        return self.main_viewer.get_current_file()
    
    def get_debug_info(self):
        """Get debug information about the current DFF file."""
        if not hasattr(self.main_viewer.viewer, 'current_dff_path') or not self.main_viewer.viewer.current_dff_path:
            return None
        
        try:
            d = dff()
            d.load_file(self.main_viewer.viewer.current_dff_path)
            return {
                "frames": len(getattr(d, 'frame_list', []) or []),
                "geometries": len(getattr(d, 'geometry_list', []) or []),
                "atomics": len(getattr(d, 'atomic_list', []) or []),
                "rw_version": hex(getattr(d, 'rw_version', 0) or 0),
            }
        except Exception as e:
            if self.debug:
                self.debug.log_exception(LogCategory.TOOL if hasattr(LogCategory, 'TOOL') else LogCategory.UI, "DFF debug failed", e)
            return {"error": str(e)}
    
    def cleanup(self):
        """Clean up resources."""
        if hasattr(self.main_viewer, 'cleanup'):
            self.main_viewer.cleanup()
    
    def load_txd(self, file_path):
        """Load a TXD file for the current model."""
        if hasattr(self.main_viewer, 'viewer'):
            self.main_viewer.viewer.load_txd(file_path)
    
    def clear_txd(self):
        """Clear the currently loaded TXD textures."""
        if hasattr(self.main_viewer, 'viewer'):
            self.main_viewer.viewer.clear_txd()
    
    def get_current_txd(self):
        """Get the currently loaded TXD file path."""
        if hasattr(self.main_viewer, 'viewer'):
            return getattr(self.main_viewer.viewer, 'current_txd_path', None)
        return None
    
    def has_txd_support(self):
        """Check if TXD support is available."""
        return True




