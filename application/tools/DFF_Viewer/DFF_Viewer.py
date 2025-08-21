#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyQt6 + Qt3D: DFF/OBJ Model Viewer with Interactive Inspector Highlighting.
This file provides both:
1) A standalone window (MainWindow) for direct running.
2) A suite-integrated tool widget (DFFViewerTool) to embed in the Modding Suite.
"""

import math
import struct
import sys

# Correctly import QBuffer and QByteArray from QtCore
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QBuffer, QByteArray 

from PyQt6.QtGui import QAction, QColor, QMatrix4x4
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
    QCylinderMesh, # Needed for the axis gizmo
)
from PyQt6.Qt3DRender import (
    QCamera,
    QCameraLens,
    QMesh,
    QDirectionalLight,
    QGeometryRenderer,
)

# Import the DFF parser and the Vector class
# Prefer in-suite path; fall back to local if directly running outside package
try:
    from application.common.DFF import dff, Vector, SkinPLG, HAnimPLG, UserData
except Exception:
    try:
        from DFF import dff, Vector, SkinPLG, HAnimPLG, UserData
    except Exception as e:
        # Delay QMessageBox usage to suite contexts; here print+exit for CLI
        print(f"Import Error: {e}")
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

        # --- Enhanced Three-Point Lighting Setup ---
        # 1. Key Light (main light source)
        self.key_light_entity = QEntity(self.root)
        self.key_light = QDirectionalLight(self.key_light_entity)
        self.key_light.setWorldDirection(QtGui.QVector3D(-0.8, -1.0, -0.6))
        self.key_light.setColor(QtGui.QColor(255, 255, 245)) # Bright, slightly warm
        self.key_light.setIntensity(1.0)
        self.key_light_entity.addComponent(self.key_light)

        # 2. Fill Light (soft light to fill shadows)
        self.fill_light_entity = QEntity(self.root)
        self.fill_light = QDirectionalLight(self.fill_light_entity)
        self.fill_light.setWorldDirection(QtGui.QVector3D(0.8, -0.4, 1.0))
        self.fill_light.setColor(QtGui.QColor(180, 200, 220)) # Dim, cool
        self.fill_light.setIntensity(0.4)
        self.fill_light_entity.addComponent(self.fill_light)

        # 3. Rim Light (to separate the model from the background)
        self.rim_light_entity = QEntity(self.root)
        self.rim_light = QDirectionalLight(self.rim_light_entity)
        self.rim_light.setWorldDirection(QtGui.QVector3D(0.3, 1.0, 0.5))
        self.rim_light.setColor(QtGui.QColor(150, 150, 150)) # Dim white
        self.rim_light.setIntensity(0.3)
        self.rim_light_entity.addComponent(self.rim_light)

        # Placeholder for the loaded model
        self.model_entity: QEntity | None = None
        self.original_materials = {} # To store original colors for toggling override
        self.current_dff_path: str | None = None

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
                index_byte_array.append(struct.pack('<3H', tri.a, tri.c, tri.b)) # Reverse winding

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

            transform = QTransform(part_entity)
            if atomic.frame < len(dff_file.frame_list):
                frame = dff_file.frame_list[atomic.frame]
                m = frame.rotation_matrix
                p = frame.position
                qmatrix = QMatrix4x4(m.right.x, m.up.x, m.at.x, p.x,
                                     m.right.y, m.up.y, m.at.y, p.y,
                                     m.right.z, m.up.z, m.at.z, p.z,
                                     0, 0, 0, 1).transposed()
                transform.setMatrix(qmatrix)

            material = QPhongMaterial(part_entity)
            material.setAmbient(QtGui.QColor(40, 40, 50)) # Add slight ambient color
            mat_color = QtGui.QColor(200, 200, 220)
            if geo.materials and geo.materials[0].color:
                c = geo.materials[0].color
                mat_color.setRgb(c.r, c.g, c.b, c.a)
            
            material.setDiffuse(mat_color)
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

    def reload(self):
        """Reload the last loaded DFF file, if any."""
        if self.current_dff_path:
            self.load_dff(self.current_dff_path)

    def set_background_color(self, color: QColor):
        self.view.defaultFrameGraph().setClearColor(color)

    def set_override_material_enabled(self, enabled: bool):
        if not self.model_entity:
            return
            
        materials = self.model_entity.findChildren(QPhongMaterial)
        for mat in materials:
            if enabled:
                mat.setDiffuse(QtGui.QColor(230, 230, 240))
            else:
                original = self.original_materials.get(id(mat))
                if original:
                    mat.setDiffuse(original['diffuse'])
                else:
                    mat.setDiffuse(QtGui.QColor(200, 200, 220)) # Fallback


class CameraDock(QWidget):
    distanceChanged = pyqtSignal(float)
    azimuthChanged = pyqtSignal(float)
    elevationChanged = pyqtSignal(float)
    bgColorPicked = pyqtSignal(QColor)
    overrideMaterialToggled = pyqtSignal(bool)

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

        self.chk_override = QCheckBox("Use light override material")
        self.chk_override.toggled.connect(self.overrideMaterialToggled)
        layout.addWidget(self.chk_override)

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
        self.btn_reload = QPushButton("Reload")
        self.btn_reset_view = QPushButton("Reset View")
        self.btn_background = QPushButton("Background...")
        self.btn_debug = QPushButton("Debug Parse")
        
        # Style buttons
        for btn in [self.btn_open, self.btn_reload, self.btn_reset_view, self.btn_background, self.btn_debug]:
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
        header_layout.addWidget(self.btn_reload)
        header_layout.addWidget(self.btn_reset_view)
        header_layout.addWidget(self.btn_background)
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
        
        # Add material override checkbox
        self.chk_override = QCheckBox("Light override material")
        camera_layout.addWidget(self.chk_override)
        
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
        self.btn_reload.clicked.connect(self.viewer.reload)
        self.btn_reset_view.clicked.connect(self.viewer.reset_view)
        self.btn_background.clicked.connect(self._on_pick_background)
        self.btn_debug.clicked.connect(self._on_debug_parse)
        
        # Camera control connections
        self.camera_controls.distanceChanged.connect(self.viewer.set_camera_distance)
        self.camera_controls.azimuthChanged.connect(self.viewer.set_camera_azimuth)
        self.camera_controls.elevationChanged.connect(self.viewer.set_camera_elevation)
        self.camera_controls.bgColorPicked.connect(self.viewer.set_background_color)
        self.camera_controls.overrideMaterialToggled.connect(self.viewer.set_override_material_enabled)
        self.chk_override.toggled.connect(self.viewer.set_override_material_enabled)
        
        # Viewer connections
        self.viewer.dff_loaded.connect(self._on_dff_loaded)
        
        # Inspector connections
        self.inspector_tree.currentItemChanged.connect(self._on_inspector_item_selected)

    def _show_status(self, message):
        """Show status message."""
        self.status_label.setText(message)
        if self.debug:
            self.debug.info(LogCategory.UI, "DFF Viewer status", {"message": message})
    
    def _on_open_file(self):
        """Handle open file action."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open DFF Model", "", "GTA DFF (*.dff);;Wavefront OBJ (*.obj)")
        if path:
            self._show_status(f"Loading: {path}")
            QtWidgets.QApplication.processEvents()
            
            if path.lower().endswith('.dff'):
                self.viewer.load_dff(path)
            elif path.lower().endswith('.obj'):
                self.viewer.load_obj(path)
            
            self._show_status(f"Loaded: {path}")
            self.tool_action.emit("file_loaded", path)
    
    def _on_pick_background(self):
        """Handle background color picker."""
        color = QColorDialog.getColor(QtGui.QColor(30, 30, 34), self, "Pick background color")
        if color.isValid():
            self.viewer.set_background_color(color)
            self.tool_action.emit("background_changed", color.name())
    
    def _on_dff_loaded(self, dff_file, geo_entity_map):
        """Handle DFF file loaded event."""
        # Update status
        frames = len(getattr(dff_file, 'frame_list', []) or [])
        geometries = len(getattr(dff_file, 'geometry_list', []) or [])
        atomics = len(getattr(dff_file, 'atomic_list', []) or [])
        
        status_text = f"Loaded DFF • Frames: {frames} • Geometries: {geometries} • Atomics: {atomics}"
        self._show_status(status_text)
        
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
        """Load a DFF or OBJ file (external interface)."""
        if file_path.lower().endswith('.dff'):
            self.viewer.load_dff(file_path)
        elif file_path.lower().endswith('.obj'):
            self.viewer.load_obj(file_path)
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
            return

        # --- File Info ---
        info_root = QTreeWidgetItem(self.inspector_tree, ["File Info"])
        self._add_tree_child(info_root, "RW Version", f"0x{dff_file.rw_version:X}")
        
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




# For backwards compatibility, keep the old MainWindow class as a standalone option
class MainWindow(QMainWindow):
    """Standalone DFF Viewer window for direct execution."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt3D DFF/OBJ Viewer – Interactive")
        self.resize(1600, 900)
        
        # Use the new main viewer widget as central widget
        self.viewer_widget = DFFViewerMainWindow(self)
        self.setCentralWidget(self.viewer_widget)
        
        # Add a simple menu bar
        self._create_menu()
        
        self.statusBar().showMessage("Ready. Use the viewer controls to load a DFF or OBJ model.")
    
    def _create_menu(self):
        """Create a simple menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        # Open action
        open_action = QAction('Open...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.viewer_widget._on_open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        # Reset view action
        reset_action = QAction('Reset View', self)
        reset_action.setShortcut('R')
        reset_action.triggered.connect(self.viewer_widget.viewer.reset_view)
        view_menu.addAction(reset_action)
        
        # Background action
        bg_action = QAction('Background...', self)
        bg_action.triggered.connect(self.viewer_widget._on_pick_background)
        view_menu.addAction(bg_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        # About action
        about_action = QAction('About', self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.information(self, "About Qt3D DFF/OBJ Viewer",
            ("<b>Qt3D DFF/OBJ Viewer</b><br>"
             "A viewer for .dff and .obj meshes built with PyQt6 + Qt3D.<br><br>"
             "Controls:<br>"
             "• Left-drag: orbit<br>"
             "• Middle-drag / Shift+Left: pan<br>"
             "• Wheel: zoom<br><br>"
             "Use the 'Open DFF...' button to load a model."))


def main():
    """Main entry point for standalone execution."""
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()