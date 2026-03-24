"""
Timber Factory - Main UI & Export Controller
Generic framework for generating wood products in FreeCAD.
Currently supports: Shoji Amida
"""

import FreeCAD as App
import FreeCADGui as Gui
import os
import time
import subprocess
import Mesh
import xml.etree.ElementTree as ET
from xml.dom import minidom
import webbrowser

# --- Import Timber Logic Modules ---
from timber_logic_shoji import ShojiAmidaGenerator

# --- Qt Imports (PySide2/PySide) ---
try:
    from PySide2.QtCore import Qt, QObject
    from PySide2.QtWidgets import (QAction, QToolBar, QDialog, QVBoxLayout, 
                                 QHBoxLayout, QLabel, QSlider, QSpinBox, 
                                 QDialogButtonBox)
except ImportError:
    from PySide.QtCore import Qt, QObject
    from PySide.QtGui import (QAction, QToolBar, QDialog, QVBoxLayout, 
                                QHBoxLayout, QLabel, QSlider, QSpinBox, 
                                QDialogButtonBox)

# --- Global Instance ---
# Note: In the future, this can be expanded to support multiple product types
generator = ShojiAmidaGenerator()

# --- Path Setup ---
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
EXPORT_FOLDER = os.path.join(BASE_DIR, "exports")
if not os.path.exists(EXPORT_FOLDER):
    os.makedirs(EXPORT_FOLDER)

# --- Robust Export Functions ---

def export_png():
    """Exports current 3D view as high-res PNG"""
    view = Gui.ActiveDocument.ActiveView
    if not view: return
    path = os.path.join(EXPORT_FOLDER, "timber_product.png")
    try:
        view.saveImage(path, 1920, 1080, "Current")
        print(f"✓ Exported PNG: {path}")
    except Exception as e:
        print(f"PNG Export Error: {e}")

def export_dxf():
    """2D CAD export using Draft/importDXF module"""
    try:
        import importDXF
        doc = App.ActiveDocument
        objs = [doc.getObject("Shoji_Left"), doc.getObject("Shoji_Right")]
        valid_objs = [o for o in objs if o]
        if not valid_objs: return
        
        path = os.path.join(EXPORT_FOLDER, "timber_product.dxf")
        importDXF.export(valid_objs, path)
        print(f"✓ Exported DXF: {path}")
    except Exception as e:
        print(f"DXF Export Error: {e}. Ensure Draft workbench is installed.")

def export_glb():
    """3D Web export (GLTF) with automatic HTML viewer generation"""
    doc = App.ActiveDocument
    objs = [doc.getObject("Shoji_Left"), doc.getObject("Shoji_Right")]
    valid_objs = [o for o in objs if o]
    if not valid_objs: return
    
    path = os.path.join(EXPORT_FOLDER, "timber_product.gltf")
    exported = False
    
    # Method 1: App.export (Native glTF addon)
    try:
        App.export(valid_objs, path)
        exported = True
    except Exception as e:
        print(f"App.export (glTF) failed: {e}. Trying Mesh fallback...")
        
    # Method 2: Mesh.export (Reliable geometry fallback)
    if not exported:
        try:
            Mesh.export(valid_objs, path)
            exported = True
        except Exception as e:
            print(f"Mesh.export failed: {e}. Extension might not be supported.")
            # Final fallback: OBJ mesh
            path = path.replace(".gltf", "_fallback.obj")
            try:
                Mesh.export(valid_objs, path)
                print(f"✓ Exported Mesh OBJ as fallback: {path}")
                return
            except: pass

    if exported:
        print(f"✓ Exported GLTF: {path}")
        create_html_viewer(path)

def create_html_viewer(gltf_path):
    """Generates a standalone HTML viewer using Google's <model-viewer>"""
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Timber Factory 3D Viewer</title>
    <script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js"></script>
    <style>
        body {{ margin: 0; background: #1a1a1a; color: white; font-family: sans-serif; overflow: hidden; }}
        model-viewer {{ width: 100vw; height: 100vh; display: block; }}
        .header {{ position: absolute; top: 20px; left: 20px; z-index: 10; pointer-events: none; }}
    </style>
</head>
<body>
    <div class="header"><h1>Timber Factory</h1><p>Interactive 3D Preview</p></div>
    <model-viewer src="{os.path.basename(gltf_path)}" 
                  camera-controls auto-rotate 
                  shadow-intensity="1.5" environment-image="neutral"
                  exposure="1.0">
    </model-viewer>
</body>
</html>"""
    html_path = gltf_path.replace(".gltf", ".html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # Open in system browser (path normalization for file:// protocol)
    url = "file:///" + html_path.replace('\\', '/')
    webbrowser.open(url)

def open_in_blender():
    """Converts model to OBJ and launches Blender immediately"""
    doc = App.ActiveDocument
    if not doc: return
    obj_path = os.path.join(EXPORT_FOLDER, "timber_product.obj").replace('\\', '/')
    
    try:
        comp = doc.getObject("Shoji_Complete")
        if not comp: return
        
        # High quality tessellation for Blender rendering
        tess = comp.Shape.tessellate(0.05) 
        mesh_obj = Mesh.Mesh(tess)
        mesh_obj.write(obj_path)
        print(f"✓ Exported OBJ: {obj_path}")
        
        # Potential Blender install paths
        blender_paths = [
            "blender", 
            r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"
        ]
        
        native_path = obj_path.replace('/', os.sep)
        for bp in blender_paths:
            try:
                subprocess.Popen([bp, native_path])
                print(f"✓ Launching Blender: {bp}")
                return
            except: continue
        
        print("Blender executable not found. Opening export folder.")
        os.startfile(EXPORT_FOLDER)
    except Exception as e:
        print(f"Blender Integration Error: {e}")

def export_cedxm():
    """Generates industry-standard CEDXM (CEDAR XML) precut data"""
    cedxm_path = os.path.join(EXPORT_FOLDER, "timber_product.cedxm")
    root = ET.Element("CEDXM", version="1.0", generator="FreeCAD Timber Factory")
    
    # XML Header
    header = ET.SubElement(root, "Header")
    ET.SubElement(header, "Timestamp").text = time.strftime("%Y-%m-%dT%H:%M:%S")
    ET.SubElement(header, "Project").text = "Timber_Factory_Project"
    
    # Metadata for the project
    meta = ET.SubElement(root, "Metadata")
    ET.SubElement(meta, "Creator").text = "FreeCAD Timber Script"
    
    members_node = ET.SubElement(root, "Members")
    
    def add_xml_member(m_data):
        m = ET.SubElement(members_node, "Member", id=m_data["id"])
        
        # Full Cedxm_Pset_param implementation from specification
        pset = ET.SubElement(m, "Cedxm_Pset_param")
        ET.SubElement(pset, "mokuzai").text = ".T."
        ET.SubElement(pset, "syurui").text = m_data["syurui"]
        ET.SubElement(pset, "jyusyu").text = "hinoki"
        ET.SubElement(pset, "toukyuu").text = "tokuiti"
        ET.SubElement(pset, "kesyou").text = ".T."
        ET.SubElement(pset, "w").text = str(m_data["w"])
        ET.SubElement(pset, "h").text = str(m_data["h"])
        ET.SubElement(pset, "siten_keijyou").text = "katto"
        ET.SubElement(pset, "syuuten_keijyou").text = "katto"
        
        # Detailed Geometry node
        geom = ET.SubElement(m, "Geometry")
        ET.SubElement(geom, "Start").attrib = {
            "x": f"{m_data['start'].x:.2f}", 
            "y": f"{m_data['start'].y:.2f}", 
            "z": f"{m_data['start'].z:.2f}"
        }
        ET.SubElement(geom, "End").attrib = {
            "x": f"{m_data['end'].x:.2f}", 
            "y": f"{m_data['end'].y:.2f}", 
            "z": f"{m_data['end'].z:.2f}"
        }
        ET.SubElement(geom, "Length").text = f"{m_data['length']:.2f}"

    # Collect members from both panels using generator state
    for side in ["left", "right"]:
        offset_x = -generator.SHOJI_WIDTH/2 - 50 if side == "left" else generator.SHOJI_WIDTH/2 + 50
        members = generator.get_member_data(side, offset_x)
        for m_data in members:
            add_xml_member(m_data)
    
    # Formatted XML output
    xml_str = minidom.parseString(ET.tostring(root, encoding="utf-8")).toprettyxml(indent="  ")
    try:
        with open(cedxm_path, "w", encoding="utf-8") as f:
            f.write(xml_str)
        print(f"✓ Exported CEDXM: {cedxm_path}")
    except Exception as e:
        print(f"CEDXM Export Error: {e}")

# --- UI / Interaction ---

def show_parameter_dialog():
    """Full parameter adjustment dialog with synchronized sliders and spinboxes"""
    d = QDialog(Gui.getMainWindow())
    d.setWindowTitle("Timber Factory - Shoji Parameters")
    d.setMinimumWidth(450)
    layout = QVBoxLayout(d)
    
    def create_row(title, val, min_v, max_v):
        row = QHBoxLayout()
        row.addWidget(QLabel(title))
        spin = QSpinBox(); spin.setRange(min_v, max_v); spin.setValue(val)
        slider = QSlider(Qt.Horizontal); slider.setRange(min_v, max_v); slider.setValue(val)
        spin.valueChanged.connect(slider.setValue)
        slider.valueChanged.connect(spin.setValue)
        row.addWidget(spin); row.addWidget(slider)
        layout.addLayout(row)
        return spin

    # Add all controls
    w_spin = create_row("Width (mm):", generator.SHOJI_WIDTH, 500, 2500)
    h_spin = create_row("Height (mm):", generator.SHOJI_HEIGHT, 1000, 3500)
    v_spin = create_row("Vertical Poles:", generator.NUM_VERTICAL_LINES, 3, 30)
    l_spin = create_row("Pattern Levels:", generator.NUM_HORIZONTAL_LEVELS, 3, 50)
    p_spin = create_row("Amida Density (%):", int(generator.HORIZONTAL_PROBABILITY*100), 0, 100)
    
    bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    layout.addWidget(bb)
    bb.accepted.connect(d.accept)
    bb.rejected.connect(d.reject)
    
    if d.exec_() == QDialog.Accepted:
        generator.set_parameters(
            w_spin.value(), h_spin.value(), 
            v_spin.value(), l_spin.value(), 
            p_spin.value() / 100.0
        )
        regenerate_model()

def regenerate_model():
    """The core regeneration sequence called after parameter changes or 'Regen' button"""
    if App.ActiveDocument:
        App.closeDocument(App.ActiveDocument.Name)
    
    print("Regenerating Timber Model...")
    left_shape, right_shape = generator.generate_dual_shoji()
    
    doc = App.newDocument("Timber_Factory_Model")
    
    # Left Panel Object
    l_obj = doc.addObject("Part::Feature", "Shoji_Left")
    l_obj.Shape = left_shape
    l_obj.Label = f"Shoji Left (Seed: {generator.last_left_seed})"
    
    # Right Panel Object
    r_obj = doc.addObject("Part::Feature", "Shoji_Right")
    r_obj.Shape = right_shape
    r_obj.Label = f"Shoji Right (Seed: {generator.last_right_seed})"
    
    # Unified Compound
    comp = doc.addObject("Part::Compound", "Shoji_Complete")
    comp.Links = [l_obj, r_obj]
    comp.Label = "Shoji Complete Assembly"
    
    doc.recompute()
    
    # Visual Polish
    if Gui.ActiveDocument and Gui.ActiveDocument.ActiveView:
        Gui.ActiveDocument.ActiveView.viewFront()
        Gui.ActiveDocument.ActiveView.fitAll()
    
    refresh_toolbar()
    print("✓ Model successfully updated!")

def refresh_toolbar():
    """Ensures the toolbar is present and updated with the latest functionality"""
    mw = Gui.getMainWindow()
    if not mw: return
    
    # Clean up existing toolbar to avoid duplicates
    old_tb = mw.findChild(QToolBar, "TimberFactoryToolbar")
    if old_tb: 
        mw.removeToolBar(old_tb)
        old_tb.deleteLater()
    
    tb = mw.addToolBar("Timber Factory")
    tb.setObjectName("TimberFactoryToolbar")
    
    # Button Definitions (Icon/Label and Function)
    actions = [
        ("⚙️ Params", show_parameter_dialog), 
        ("🔄 New Pattern", regenerate_model), 
        (None, None),
        ("📷 Export PNG", export_png), 
        ("📐 Export DXF", export_dxf), 
        ("🌐 3D Web/HTML", export_glb),
        ("🟠 Open Blender", open_in_blender), 
        ("📄 Export CEDXM", export_cedxm)
    ]
    
    for label, func in actions:
        if label is None: 
            tb.addSeparator()
        else:
            act = QAction(label, mw)
            act.triggered.connect(func)
            tb.addAction(act)
    
    # Maintain reference to prevent GC deletion
    if not hasattr(Gui, "_timber_toolbars"): Gui._timber_toolbars = []
    Gui._timber_toolbars.append(tb)
    tb.show()

# --- Entry Point ---
if __name__ == "__main__":
    regenerate_model()
