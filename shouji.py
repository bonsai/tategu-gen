"""
FreeCAD Parametric Shoji Screen Generator
Amida-kuji (あみだくじ) Kumiko Pattern - 2 Panels
With Export Buttons (PNG, DXF, GLB)
"""

import FreeCAD as App
import FreeCADGui as Gui
import Part

import Mesh
import random
import time
import os
import subprocess

# Import Qt for toolbar (FreeCAD uses PySide2)
try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import (QAction, QToolBar, QDialog, QVBoxLayout, 
                                 QHBoxLayout, QLabel, QSlider, QSpinBox, 
                                 QDialogButtonBox)
except ImportError:
    try:
        from PySide.QtCore import Qt
        from PySide.QtGui import (QAction, QToolBar, QDialog, QVBoxLayout, 
                                QHBoxLayout, QLabel, QSlider, QSpinBox, 
                                QDialogButtonBox)
    except ImportError:
        # Fallback stubs for syntax checking
        class QAction: pass
        class QToolBar: pass
        class QDialog: pass
        class QVBoxLayout: pass
        class QHBoxLayout: pass
        class QLabel: pass
        class QSlider: pass
        class QSpinBox: pass
        class QDialogButtonBox: pass
        class Qt:
            Horizontal = 0

# ============== Parameters ==============
# Shoji frame dimensions (in mm)
SHOJI_WIDTH = 910        # Width of each shoji panel
SHOJI_HEIGHT = 1820      # Height of each shoji panel
FRAME_THICKNESS = 30     # Frame thickness
FRAME_DEPTH = 40         # Frame depth

# Kumiko (lattice) parameters
NUM_VERTICAL_LINES = 5   # Number of vertical lines (Amida-kuji poles)
NUM_HORIZONTAL_LEVELS = 10  # Number of horizontal connection levels
HORIZONTAL_PROBABILITY = 0.4  # Probability of horizontal bar at each level (0-1)

# Parameter ranges for sliders
MIN_VERTICAL_LINES = 3
MAX_VERTICAL_LINES = 20
MIN_HORIZONTAL_LEVELS = 3
MAX_HORIZONTAL_LEVELS = 30

# Random seed for reproducible patterns (None = different every time)
RANDOM_SEED = None       # Set to integer for reproducible pattern, None for random

# Kumiko bar dimensions
KUMIKO_WIDTH = 10      # Width of kumiko bars
KUMIKO_THICKNESS = 8   # Thickness of kumiko bars

# Output folder
OUTPUT_FOLDER = os.path.join(App.getUserAppDataDir(), "ShojiExports")
IMAGE_FOLDER = os.path.join(App.getUserAppDataDir(), "ShojiImages")


def create_amida_pattern(num_vertical, num_levels, probability, seed=None):
    """
    Create Amida-kuji pattern with vertical lines and random horizontal connections
    """
    if seed is not None:
        random.seed(seed)

    horizontal_connections = []
    for level in range(num_levels):
        for pos in range(num_vertical - 1):
            if random.random() < probability:
                if pos > 0 and (level, pos - 1) in horizontal_connections:
                    continue
                if pos < num_vertical - 2 and (level, pos + 1) in horizontal_connections:
                    continue
                horizontal_connections.append((level, pos))

    return horizontal_connections


def create_shoji_frame(width, height, thickness, depth):
    """Create the outer frame of a shoji screen"""
    outer_box = Part.makeBox(width, depth, height)
    inner_width = width - thickness * 2
    inner_height = height - thickness * 2
    inner_cutout = Part.makeBox(inner_width, depth, inner_height)
    inner_cutout.translate(App.Vector(thickness, 0, thickness))
    frame = outer_box.cut(inner_cutout)
    return frame


def create_vertical_bar(x_pos, z_bottom, z_top, width, thickness, depth):
    """Create a vertical kumiko bar"""
    bar = Part.makeBox(width, depth, z_top - z_bottom)
    bar.translate(App.Vector(x_pos - width/2, 0, z_bottom))
    return bar


def create_horizontal_bar(x_start, z_pos, length, width, thickness, depth):
    """Create a horizontal kumiko bar"""
    bar = Part.makeBox(length, depth, width)
    bar.translate(App.Vector(x_start, 0, z_pos - width/2))
    return bar


def create_kumiko_pattern(frame_width, frame_height, num_vertical, num_levels,
                          horizontal_connections, kumiko_width, kumiko_thickness,
                          frame_thickness, frame_depth):
    """Create the complete kumiko lattice pattern"""
    kumiko_parts = []

    usable_width = frame_width - frame_thickness * 2
    usable_height = frame_height - frame_thickness * 2

    vertical_spacing = usable_width / (num_vertical - 1) if num_vertical > 1 else 0
    level_spacing = usable_height / (num_levels + 1) if num_levels > 0 else 0

    # Create vertical bars
    for i in range(num_vertical):
        x_pos = frame_thickness + i * vertical_spacing
        z_bottom = frame_thickness
        z_top = frame_height - frame_thickness
        bar = create_vertical_bar(x_pos, z_bottom, z_top, kumiko_width,
                                   kumiko_thickness, frame_depth)
        kumiko_parts.append(bar)

    # Create horizontal connections
    for level, vert_index in horizontal_connections:
        z_pos = frame_thickness + (level + 1) * level_spacing
        x_start = frame_thickness + vert_index * vertical_spacing
        length = vertical_spacing
        bar = create_horizontal_bar(x_start, z_pos, length, kumiko_width,
                                     kumiko_thickness, frame_depth)
        kumiko_parts.append(bar)

    return kumiko_parts


def create_shoji_panel(width, height, frame_thickness, frame_depth,
                       num_vertical, num_levels, probability, seed):
    """Create a complete shoji panel"""
    frame = create_shoji_frame(width, height, frame_thickness, frame_depth)
    horizontal_connections = create_amida_pattern(num_vertical, num_levels, probability, seed)
    kumiko_parts = create_kumiko_pattern(
        width, height, num_vertical, num_levels,
        horizontal_connections, KUMIKO_WIDTH, KUMIKO_THICKNESS,
        frame_thickness, frame_depth
    )

    all_parts = [frame] + kumiko_parts
    if len(all_parts) == 1:
        return all_parts[0]
    else:
        result = all_parts[0]
        for part in all_parts[1:]:
            result = result.fuse(part)
        return result


def create_double_shoji(gap=100):
    """Create two shoji panels side by side"""
    print("=" * 50)
    print("FreeCAD Parametric Shoji Generator")
    print("Amida-kuji Kumiko Pattern - 2 Panels")
    print("=" * 50)
    print(f"\nParameters:")
    print(f"  Panel Size: {SHOJI_WIDTH}mm × {SHOJI_HEIGHT}mm")
    print(f"  Frame Thickness: {FRAME_THICKNESS}mm")
    print(f"  Vertical Lines: {NUM_VERTICAL_LINES}")
    print(f"  Horizontal Levels: {NUM_HORIZONTAL_LEVELS}")
    print(f"  Connection Probability: {HORIZONTAL_PROBABILITY}")
    print(f"  Random Seed: {RANDOM_SEED}")
    print()

    # Generate seeds
    if RANDOM_SEED is None:
        left_seed = random.randint(0, 1000000)
        right_seed = random.randint(0, 1000000)
    else:
        left_seed = RANDOM_SEED
        right_seed = RANDOM_SEED + 1000

    print(f"Creating left panel... (seed: {left_seed})")
    left_panel = create_shoji_panel(
        SHOJI_WIDTH, SHOJI_HEIGHT, FRAME_THICKNESS, FRAME_DEPTH,
        NUM_VERTICAL_LINES, NUM_HORIZONTAL_LEVELS, HORIZONTAL_PROBABILITY,
        seed=left_seed
    )

    print(f"Creating right panel... (seed: {right_seed})")
    right_panel = create_shoji_panel(
        SHOJI_WIDTH, SHOJI_HEIGHT, FRAME_THICKNESS, FRAME_DEPTH,
        NUM_VERTICAL_LINES, NUM_HORIZONTAL_LEVELS, HORIZONTAL_PROBABILITY,
        seed=right_seed
    )

    # Position panels
    left_panel.translate(App.Vector(-SHOJI_WIDTH/2 - gap/2, 0, 0))
    right_panel.translate(App.Vector(SHOJI_WIDTH/2 + gap/2, 0, 0))

    # Create document
    doc = App.newDocument("Shoji_Amida")

    left_obj = doc.addObject("Part::Feature", "Shoji_Left")
    left_obj.Shape = left_panel
    left_obj.Label = "Shoji Left (Amida)"

    right_obj = doc.addObject("Part::Feature", "Shoji_Right")
    right_obj.Shape = right_panel
    right_obj.Label = "Shoji Right (Amida)"

    compound = doc.addObject("Part::Compound", "Shoji_Complete")
    compound.Links = [left_obj, right_obj]

    doc.recompute()

    # Set view
    import FreeCADGui as Gui
    if Gui.ActiveDocument:
        view = Gui.ActiveDocument.ActiveView
        if view:
            view.viewFront()
            view.fitAll()

    # Save FCStd
    fcstd_path = os.path.join(OUTPUT_FOLDER, "shoji_amida_2panels.FCStd")
    doc.saveAs(fcstd_path)
    print(f"\n✓ Saved: {fcstd_path}")

    return doc


def export_png():
    """Export current view as PNG"""
    import FreeCADGui as Gui
    import os
    
    # Ensure image folder exists
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)
    
    doc = App.ActiveDocument
    if not doc:
        print("Error: No active document")
        return

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    png_path = os.path.join(IMAGE_FOLDER, f"shoji_amida_{timestamp}.png")
    
    try:
        view = Gui.ActiveDocument.ActiveView
        if view:
            view.saveImage(png_path, 1920, 1080, "Current")
            print(f"✓ Exported PNG: {png_path}")
        else:
            print("Error: No active view")
    except Exception as e:
        print(f"Error exporting PNG: {e}")


def export_dxf():
    """Export as DXF (2D projection)"""
    import os
    import importDXF
    
    # Ensure image folder exists
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)
    
    doc = App.ActiveDocument
    if not doc:
        print("Error: No active document")
        return

    dxf_path = os.path.join(IMAGE_FOLDER, "shoji_amida.dxf")
    
    try:
        # Get objects to export
        objects = [doc.getObject("Shoji_Left"), doc.getObject("Shoji_Right")]
        valid_objects = [obj for obj in objects if obj]
        
        if valid_objects:
            # Export using dedicated DXF module
            importDXF.export(valid_objects, dxf_path)
            print(f"✓ Exported DXF: {dxf_path}")
        else:
            print("Error: Shoji objects not found")
    except Exception as e:
        print(f"Error exporting DXF: {e}")
        print("Note: DXF export requires the 'Draft' workbench and DXF plugin to be active.")


def export_glb():
    """Export as GLB/GLTF"""
    import os
    
    # Ensure folder exists
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    
    doc = App.ActiveDocument
    if not doc:
        print("Error: No active document")
        return

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    gltf_path = os.path.join(OUTPUT_FOLDER, f"shoji_amida_{timestamp}.gltf")
    
    try:
        # Get all objects
        objects = [doc.getObject("Shoji_Left"), doc.getObject("Shoji_Right")]
        valid_objects = [obj for obj in objects if obj]
        
        if valid_objects:
            exported = False
            
            # Try core App.export (this is the most reliable in FreeCAD 1.0 if glTF is enabled)
            try:
                # App.export expects a list of objects and a filename
                App.export(valid_objects, gltf_path)
                exported = True
            except Exception as e:
                print(f"App.export failed: {e}")
                
            # Method 2: Try Mesh module export
            if not exported:
                try:
                    import Mesh
                    # Mesh.export is a module-level function
                    Mesh.export(valid_objects, gltf_path)
                    exported = True
                except Exception as e:
                    print(f"Mesh.export failed: {e}")
            
            if exported:
                print(f"✓ Exported GLTF: {gltf_path}")
                create_glb_html(gltf_path)
            else:
                print("Error: No suitable GLTF exporter found. Please install the 'glTF' addon via Tools -> Addon Manager.")
        else:
            print("Error: No objects found")
    except Exception as e:
        print(f"Error exporting GLTF: {e}")


def create_glb_html(glb_filename):
    """Create a simple HTML viewer for the GLB file"""
    import os
    import webbrowser
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Shoji Amida Viewer</title>
    <script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js"></script>
    <style>
        body {{ margin: 0; background: #222; }}
        model-viewer {{ width: 100vw; height: 100vh; }}
        .info {{ position: absolute; top: 10px; left: 10px; color: white; font-family: sans-serif; pointer-events: none; }}
    </style>
</head>
<body>
    <div class="info">Shoji Amida Viewer</div>
    <model-viewer src="{os.path.basename(glb_filename)}" 
                  camera-controls 
                  auto-rotate 
                  shadow-intensity="1" 
                  background-color="#333">
    </model-viewer>
</body>
</html>
"""
    html_path = glb_filename.replace('.gltf', '.html')
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✓ Created HTML Viewer: {html_path}")
    
    # Open HTML in browser
    html_url = "file:///" + html_path.replace('\\', '/')
    webbrowser.open(html_url)


def export_obj_and_blender():
    """Export as OBJ and open in Blender"""
    import os
    import subprocess
    
    # Ensure folder exists
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    
    doc = App.ActiveDocument
    if not doc:
        print("Error: No active document")
        return

    # Use forward slashes for FreeCAD export paths
    obj_path = os.path.join(OUTPUT_FOLDER, "shoji_amida.obj").replace('\\', '/')
    
    try:
        # Get the compound object
        compound = doc.getObject("Shoji_Complete")
        if compound:
            shape = compound.Shape
            # Export using Mesh module for better compatibility and quality
            Mesh.export([compound], obj_path)
            
            print(f"✓ Exported OBJ: {obj_path}")
            
            # Try to launch Blender
            blender_paths = [
                "blender", 
                r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
                r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
                r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
            ]
            
            launched = False
            # Normalize path for Blender command line
            native_obj_path = obj_path.replace('/', os.sep)
            
            for bp in blender_paths:
                try:
                    subprocess.Popen([bp, native_obj_path])
                    print(f"✓ Launching Blender: {bp}")
                    launched = True
                    break
                except Exception:
                    continue
            
            if not launched:
                print("Warning: Blender not found. OBJ is at: " + native_obj_path)
                os.startfile(OUTPUT_FOLDER)
        else:
            print("Error: Shoji_Complete not found")
    except Exception as e:
        print(f"Error exporting OBJ/Blender: {e}")


def export_cedxm():
    """Export Amida structure as CEDXM (Member-based Precut Data Format)"""
    import os
    import time
    import xml.etree.ElementTree as ET
    from xml.dom import minidom

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        
    cedxm_path = os.path.join(OUTPUT_FOLDER, "shoji_amida.cedxm")
    
    # Root element
    root = ET.Element("CEDXM", version="1.0", generator="FreeCAD Shoji Amida")
    
    # Header
    header = ET.SubElement(root, "Header")
    ET.SubElement(header, "Timestamp").text = time.strftime("%Y-%m-%dT%H:%M:%S")
    ET.SubElement(header, "Project").text = "Shoji_Amida_Kumiko"
    
    # Members collection
    members_node = ET.SubElement(root, "Members")
    
    def add_member(side, name, syurui, w, h, length, pos_vector, rot_type="horizontal"):
        member = ET.SubElement(members_node, "Member", id=f"{side}_{name}")
        
        # Pset_param according to the specification
        pset = ET.SubElement(member, "Cedxm_Pset_param")
        ET.SubElement(pset, "mokuzai").text = ".T."
        ET.SubElement(pset, "syurui").text = syurui
        ET.SubElement(pset, "jyusyu").text = "hinoki"
        ET.SubElement(pset, "kesyou").text = ".T."
        ET.SubElement(pset, "w").text = str(w)
        ET.SubElement(pset, "h").text = str(h)
        ET.SubElement(pset, "siten_keijyou").text = "katto"
        ET.SubElement(pset, "syuuten_keijyou").text = "katto"
        
        # Basic geometry
        geom = ET.SubElement(member, "Geometry")
        ET.SubElement(geom, "Start").attrib = {"x": str(pos_vector.x), "y": str(pos_vector.y), "z": str(pos_vector.z)}
        
        if rot_type == "vertical":
            ET.SubElement(geom, "End").attrib = {"x": str(pos_vector.x), "y": str(pos_vector.y), "z": str(pos_vector.z + length)}
        else:
            ET.SubElement(geom, "End").attrib = {"x": str(pos_vector.x + length), "y": str(pos_vector.y), "z": str(pos_vector.z)}

    def collect_panel_members(side, offset_x):
        # Frame - Bottom (dodai)
        add_member(side, "frame_bottom", "dodai", FRAME_THICKNESS, FRAME_DEPTH, SHOJI_WIDTH, App.Vector(offset_x, 0, 0))
        # Frame - Top (hari)
        add_member(side, "frame_top", "hari", FRAME_THICKNESS, FRAME_DEPTH, SHOJI_WIDTH, App.Vector(offset_x, 0, SHOJI_HEIGHT - FRAME_THICKNESS))
        # Frame - Left (kuda)
        add_member(side, "frame_left", "kuda", FRAME_THICKNESS, FRAME_DEPTH, SHOJI_HEIGHT, App.Vector(offset_x, 0, 0), "vertical")
        # Frame - Right (kuda)
        add_member(side, "frame_right", "kuda", FRAME_THICKNESS, FRAME_DEPTH, SHOJI_HEIGHT, App.Vector(offset_x + SHOJI_WIDTH - FRAME_THICKNESS, 0, 0), "vertical")
        
        # Kumiko Vertical (kuda)
        usable_width = SHOJI_WIDTH - FRAME_THICKNESS * 2
        vertical_spacing = usable_width / (NUM_VERTICAL_LINES - 1) if NUM_VERTICAL_LINES > 1 else 0
        for i in range(NUM_VERTICAL_LINES):
            x = offset_x + FRAME_THICKNESS + i * vertical_spacing
            add_member(side, f"kumiko_v_{i}", "kuda", KUMIKO_WIDTH, KUMIKO_THICKNESS, SHOJI_HEIGHT - FRAME_THICKNESS*2, App.Vector(x, 0, FRAME_THICKNESS), "vertical")
            
        # Kumiko Horizontal (taruki)
        # Re-generate connections based on time-based seed logic to match the 3D model
        seed_val = (int(time.time() * 1000) % 10000) if side == "left" else (int(time.time() * 1000 + 500) % 10000)
        if RANDOM_SEED is not None:
            seed_val = RANDOM_SEED if side == "left" else (RANDOM_SEED + 1000)
            
        connections = create_amida_pattern(NUM_VERTICAL_LINES, NUM_HORIZONTAL_LEVELS, HORIZONTAL_PROBABILITY, seed=seed_val)
        usable_height = SHOJI_HEIGHT - FRAME_THICKNESS * 2
        level_spacing = usable_height / (NUM_HORIZONTAL_LEVELS + 1)
        
        for idx, (level, vert_idx) in enumerate(connections):
            z = FRAME_THICKNESS + (level + 1) * level_spacing
            x = offset_x + FRAME_THICKNESS + vert_idx * vertical_spacing
            add_member(side, f"kumiko_h_{idx}", "taruki", KUMIKO_WIDTH, KUMIKO_THICKNESS, vertical_spacing, App.Vector(x, 0, z))

    # Collect for both panels
    collect_panel_members("left", -SHOJI_WIDTH/2 - 50) # gap=100
    collect_panel_members("right", SHOJI_WIDTH/2 + 50)
    
    # Pretty print XML
    xml_str = ET.tostring(root, encoding="utf-8")
    reparsed = minidom.parseString(xml_str)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    try:
        with open(cedxm_path, "w", encoding="utf-8") as f:
            f.write(pretty_xml)
        print(f"✓ Exported CEDXM: {cedxm_path}")
    except Exception as e:
        print(f"Error exporting CEDXM: {e}")


def regenerate():
    """Regenerate shoji with new random pattern"""
    global RANDOM_SEED
    
    doc = App.ActiveDocument
    if not doc:
        print("Error: No active document")
        return
    
    try:
        # Close current document
        App.closeDocument(doc.Name)
        
        # Generate new random seed
        RANDOM_SEED = None  # Force new random pattern
        
        # Create new shoji
        new_doc = create_double_shoji()
        
        print("✓ Regenerated with new random pattern!")
        
    except Exception as e:
        print(f"Error regenerating: {e}")
        import traceback
        traceback.print_exc()


def show_parameter_dialog():
    """Show dialog to adjust parameters with sliders"""
    global NUM_VERTICAL_LINES, NUM_HORIZONTAL_LEVELS, HORIZONTAL_PROBABILITY, SHOJI_WIDTH, SHOJI_HEIGHT
    
    dialog = QDialog()
    dialog.setWindowTitle("Shoji Parameters")
    dialog.setMinimumWidth(400)
    
    layout = QVBoxLayout()
    
    # Width
    width_layout = QHBoxLayout()
    width_layout.addWidget(QLabel("Width (mm):"))
    width_spin = QSpinBox()
    width_spin.setRange(500, 2000)
    width_spin.setValue(SHOJI_WIDTH)
    width_spin.valueChanged.connect(lambda v: globals().update({'SHOJI_WIDTH': v}))
    width_layout.addWidget(width_spin)
    layout.addLayout(width_layout)
    
    # Height
    height_layout = QHBoxLayout()
    height_layout.addWidget(QLabel("Height (mm):"))
    height_spin = QSpinBox()
    height_spin.setRange(1000, 3000)
    height_spin.setValue(SHOJI_HEIGHT)
    height_spin.valueChanged.connect(lambda v: globals().update({'SHOJI_HEIGHT': v}))
    height_layout.addWidget(height_spin)
    layout.addLayout(height_layout)
    
    # Vertical Lines (Division)
    div_layout = QHBoxLayout()
    div_layout.addWidget(QLabel("Vertical Lines (Division):"))
    div_spin = QSpinBox()
    div_spin.setRange(MIN_VERTICAL_LINES, MAX_VERTICAL_LINES)
    div_spin.setValue(NUM_VERTICAL_LINES)
    div_layout.addWidget(div_spin)
    div_slider = QSlider(Qt.Horizontal)
    div_slider.setRange(MIN_VERTICAL_LINES, MAX_VERTICAL_LINES)
    div_slider.setValue(NUM_VERTICAL_LINES)
    div_slider.valueChanged.connect(div_spin.setValue)
    div_spin.valueChanged.connect(div_slider.setValue)
    div_layout.addWidget(div_slider)
    layout.addLayout(div_layout)
    
    # Horizontal Levels (Max Number)
    level_layout = QHBoxLayout()
    level_layout.addWidget(QLabel("Horizontal Levels (Max):"))
    level_spin = QSpinBox()
    level_spin.setRange(MIN_HORIZONTAL_LEVELS, MAX_HORIZONTAL_LEVELS)
    level_spin.setValue(NUM_HORIZONTAL_LEVELS)
    level_layout.addWidget(level_spin)
    level_slider = QSlider(Qt.Horizontal)
    level_slider.setRange(MIN_HORIZONTAL_LEVELS, MAX_HORIZONTAL_LEVELS)
    level_slider.setValue(NUM_HORIZONTAL_LEVELS)
    level_slider.valueChanged.connect(level_spin.setValue)
    level_spin.valueChanged.connect(level_slider.setValue)
    level_layout.addWidget(level_slider)
    layout.addLayout(level_layout)
    
    # Probability
    prob_layout = QHBoxLayout()
    prob_layout.addWidget(QLabel("Density (0-1):"))
    prob_spin = QSpinBox()
    prob_spin.setRange(0, 100)
    prob_spin.setValue(int(HORIZONTAL_PROBABILITY * 100))
    prob_layout.addWidget(prob_spin)
    prob_slider = QSlider(Qt.Horizontal)
    prob_slider.setRange(0, 100)
    prob_slider.setValue(int(HORIZONTAL_PROBABILITY * 100))
    prob_slider.valueChanged.connect(prob_spin.setValue)
    prob_spin.valueChanged.connect(prob_slider.setValue)
    prob_layout.addWidget(prob_slider)
    layout.addLayout(prob_layout)
    
    # Buttons
    button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addWidget(button_box)
    
    dialog.setLayout(layout)
    
    if dialog.exec_() == QDialog.Accepted:
        # Update global parameters
        NUM_VERTICAL_LINES = div_spin.value()
        NUM_HORIZONTAL_LEVELS = level_spin.value()
        HORIZONTAL_PROBABILITY = prob_spin.value() / 100.0
        
        print(f"Parameters updated:")
        print(f"  Size: {SHOJI_WIDTH}mm × {SHOJI_HEIGHT}mm")
        print(f"  Vertical Lines: {NUM_VERTICAL_LINES}")
        print(f"  Horizontal Levels: {NUM_HORIZONTAL_LEVELS}")
        print(f"  Density: {HORIZONTAL_PROBABILITY}")
        
        # Regenerate with new parameters
        regenerate()


def create_toolbar():
    """Create toolbar with export buttons"""
    import FreeCADGui as Gui
    
    try:
        # Get main window
        mw = Gui.getMainWindow()
        if not mw:
            print("Error: Could not find FreeCAD main window. Toolbar not created.")
            return
        
        # Check if toolbar already exists and refresh it
        existing_toolbar = mw.findChild(QToolBar, "ShojiExportToolbar")
        if existing_toolbar:
            mw.removeToolBar(existing_toolbar)
            existing_toolbar.deleteLater()
            print("✓ Refreshing Shoji Export toolbar...")
        
        # Create actions
        actions = []
        
        # Parameters button
        action_params = QAction("⚙️ Parameters", mw)
        action_params.setObjectName("ShojiParameters")
        action_params.setToolTip("Adjust parameters with sliders")
        action_params.triggered.connect(show_parameter_dialog)
        actions.append(action_params)
        
        actions.append(None)  # Separator
        
        # Regenerate button
        action_regen = QAction("🔄 Regenerate", mw)
        action_regen.setObjectName("RegenerateShoji")
        action_regen.setToolTip("Regenerate with new random pattern")
        action_regen.triggered.connect(regenerate)
        actions.append(action_regen)
        
        actions.append(None)  # Separator
        
        # PNG Export
        action_png = QAction("📷 Export PNG", mw)
        action_png.setObjectName("ExportPNG")
        action_png.setToolTip("Export current view as PNG")
        action_png.triggered.connect(export_png)
        actions.append(action_png)
        
        # DXF Export
        action_dxf = QAction("📐 Export DXF", mw)
        action_dxf.setObjectName("ExportDXF")
        action_dxf.setToolTip("Export as DXF")
        action_dxf.triggered.connect(export_dxf)
        actions.append(action_dxf)
        
        # GLB Export
        action_glb = QAction("🌐 Export GLB + HTML", mw)
        action_glb.setObjectName("ExportGLB")
        action_glb.setToolTip("Export as GLB and create HTML viewer")
        action_glb.triggered.connect(export_glb)
        actions.append(action_glb)
        
        # Blender Export
        action_blender = QAction("🟠 Open in Blender", mw)
        action_blender.setObjectName("OpenInBlender")
        action_blender.setToolTip("Export OBJ and open in Blender")
        action_blender.triggered.connect(export_obj_and_blender)
        actions.append(action_blender)
        
        actions.append(None)  # Separator
        
        # CEDXM Export
        action_cedxm = QAction("📄 Export CEDXM", mw)
        action_cedxm.setObjectName("ExportCEDXM")
        action_cedxm.setToolTip("Export as CEDXM (Precut Data Format)")
        action_cedxm.triggered.connect(export_cedxm)
        actions.append(action_cedxm)
        
        # Create toolbar
        toolbar = mw.addToolBar("Shoji Export")
        toolbar.setObjectName("ShojiExportToolbar")
        for action in actions:
            if action is None:
                toolbar.addSeparator()
            else:
                toolbar.addAction(action)
        
        # Keep a reference to prevent garbage collection
        if not hasattr(Gui, "_shoji_toolbars"):
            Gui._shoji_toolbars = []
        Gui._shoji_toolbars.append(toolbar)
        
        # Show toolbar automatically
        toolbar.show()
        
        print("✓ Export toolbar created and shown")
        
    except Exception as e:
        print(f"Toolbar info: {e}")


def main():
    """Main function"""
    try:
        # Close any existing document
        if App.ActiveDocument:
            App.closeDocument(App.ActiveDocument.Name)
        
        doc = create_double_shoji()
        
        # Create export toolbar
        create_toolbar()
        
        print("\n" + "=" * 50)
        print("Generation Complete!")
        print("=" * 50)
        print("\nToolbar buttons:")
        print("  ⚙️ Parameters - Adjust division/size with sliders")
        print("  🔄 Regenerate - New random pattern")
        print("  📷 Export PNG - Screenshot")
        print("  📐 Export DXF - 2D CAD format")
        print("  🌐 Export GLB - 3D web viewer (HTML)")
        print("  🟠 Open in Blender - OBJ export & launch")
        print("  📄 Export CEDXM - Precut data format")
        print(f"\nOutput folder: {OUTPUT_FOLDER}")
        print(f"Image exports: {IMAGE_FOLDER}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
