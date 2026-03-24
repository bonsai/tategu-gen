"""
Timber Logic - Shoji Amida (Modular Version)
Handles geometric calculations for Japanese sliding doors (Shoji).
This is a module of the Timber Factory system.
"""

import FreeCAD as App
import Part
import random
import time

class ShojiAmidaGenerator:
    def __init__(self):
        # --- Physical Dimensions (mm) ---
        self.SHOJI_WIDTH = 910
        self.SHOJI_HEIGHT = 1820
        self.FRAME_THICKNESS = 30
        self.FRAME_DEPTH = 40
        self.KUMIKO_WIDTH = 10
        self.KUMIKO_THICKNESS = 8
        
        # --- Pattern Parameters ---
        self.NUM_VERTICAL_LINES = 5
        self.NUM_HORIZONTAL_LEVELS = 10
        self.HORIZONTAL_PROBABILITY = 0.4
        self.RANDOM_SEED = None
        
        # --- Internal State for Export ---
        self.last_left_seed = None
        self.last_right_seed = None
        self.last_left_conns = []
        self.last_right_conns = []

    def set_parameters(self, w, h, nv, nl, prob):
        self.SHOJI_WIDTH = w
        self.SHOJI_HEIGHT = h
        self.NUM_VERTICAL_LINES = nv
        self.NUM_HORIZONTAL_LEVELS = nl
        self.HORIZONTAL_PROBABILITY = prob

    def create_amida_pattern(self, nv, nl, prob, seed=None):
        """Pure logic for Amida-kuji rungs"""
        if seed is not None:
            random.seed(seed)
        connections = []
        for level in range(nl):
            for pos in range(nv - 1):
                if random.random() < prob:
                    # Logic to prevent overlapping rungs for clean wood joinery
                    if pos > 0 and (level, pos - 1) in connections:
                        continue
                    if pos < nv - 2 and (level, pos + 1) in connections:
                        continue
                    connections.append((level, pos))
        return connections

    def create_frame_shape(self, w, h, t, d):
        """Create the hollow rectangular frame"""
        outer = Part.makeBox(w, d, h)
        inner = Part.makeBox(w - t*2, d, h - t*2)
        inner.translate(App.Vector(t, 0, t))
        return outer.cut(inner)

    def generate_panel_geometry(self, connections):
        """Creates the full 3D shape of a single panel (Frame + Kumiko)"""
        frame = self.create_frame_shape(
            self.SHOJI_WIDTH, self.SHOJI_HEIGHT, 
            self.FRAME_THICKNESS, self.FRAME_DEPTH
        )
        
        kumiko_parts = []
        usable_w = self.SHOJI_WIDTH - self.FRAME_THICKNESS * 2
        usable_h = self.SHOJI_HEIGHT - self.FRAME_THICKNESS * 2
        
        v_spacing = usable_w / (self.NUM_VERTICAL_LINES - 1) if self.NUM_VERTICAL_LINES > 1 else 0
        l_spacing = usable_h / (self.NUM_HORIZONTAL_LEVELS + 1) if self.NUM_HORIZONTAL_LEVELS > 0 else 0

        # Vertical Kumiko (Poles)
        for i in range(self.NUM_VERTICAL_LINES):
            x = self.FRAME_THICKNESS + i * v_spacing
            bar = Part.makeBox(self.KUMIKO_WIDTH, self.FRAME_DEPTH, self.SHOJI_HEIGHT - self.FRAME_THICKNESS * 2)
            bar.translate(App.Vector(x - self.KUMIKO_WIDTH/2, 0, self.FRAME_THICKNESS))
            kumiko_parts.append(bar)

        # Horizontal Kumiko (Rungs)
        for level, v_idx in connections:
            z = self.FRAME_THICKNESS + (level + 1) * l_spacing
            x = self.FRAME_THICKNESS + v_idx * v_spacing
            bar = Part.makeBox(v_spacing, self.FRAME_DEPTH, self.KUMIKO_WIDTH)
            bar.translate(App.Vector(x, 0, z - self.KUMIKO_WIDTH/2))
            kumiko_parts.append(bar)

        # Fuse all into one solid
        result = frame
        for part in kumiko_parts:
            result = result.fuse(part)
        return result

    def generate_dual_shoji(self, gap=100):
        """Generates two panels with distinct seeds"""
        if self.RANDOM_SEED is None:
            self.last_left_seed = int(time.time() * 1000) % 10000
            self.last_right_seed = (self.last_left_seed + 500) % 10000
        else:
            self.last_left_seed = self.RANDOM_SEED
            self.last_right_seed = self.RANDOM_SEED + 1000

        self.last_left_conns = self.create_amida_pattern(
            self.NUM_VERTICAL_LINES, self.NUM_HORIZONTAL_LEVELS, 
            self.HORIZONTAL_PROBABILITY, self.last_left_seed
        )
        self.last_right_conns = self.create_amida_pattern(
            self.NUM_VERTICAL_LINES, self.NUM_HORIZONTAL_LEVELS, 
            self.HORIZONTAL_PROBABILITY, self.last_right_seed
        )

        left_shape = self.generate_panel_geometry(self.last_left_conns)
        right_shape = self.generate_panel_geometry(self.last_right_conns)

        # Translation for visual display
        left_shape.translate(App.Vector(-self.SHOJI_WIDTH/2 - gap/2, 0, 0))
        right_shape.translate(App.Vector(self.SHOJI_WIDTH/2 + gap/2, 0, 0))

        return left_shape, right_shape

    def get_member_data(self, side, offset_x):
        """Returns a list of dictionaries containing every single wood member's metadata"""
        members = []
        conns = self.last_left_conns if side == "left" else self.last_right_conns
        
        # Helper for adding members
        def add_m(name, syurui, w, h, length, pos, is_vert=False):
            end_x = pos.x + (0 if is_vert else length)
            end_z = pos.z + (length if is_vert else 0)
            members.append({
                "id": f"{side}_{name}", "syurui": syurui,
                "w": w, "h": h, "length": length,
                "start": pos, "end": App.Vector(end_x, pos.y, end_z)
            })

        # Frame Components
        add_m("bot", "dodai", self.FRAME_THICKNESS, self.FRAME_DEPTH, self.SHOJI_WIDTH, App.Vector(offset_x, 0, 0))
        add_m("top", "hari", self.FRAME_THICKNESS, self.FRAME_DEPTH, self.SHOJI_WIDTH, App.Vector(offset_x, 0, self.SHOJI_HEIGHT - self.FRAME_THICKNESS))
        add_m("left", "kuda", self.FRAME_THICKNESS, self.FRAME_DEPTH, self.SHOJI_HEIGHT, App.Vector(offset_x, 0, 0), True)
        add_m("right", "kuda", self.FRAME_THICKNESS, self.FRAME_DEPTH, self.SHOJI_HEIGHT, App.Vector(offset_x + self.SHOJI_WIDTH - self.FRAME_THICKNESS, 0, 0), True)

        # Kumiko Components
        usable_w = self.SHOJI_WIDTH - self.FRAME_THICKNESS * 2
        v_gap = usable_w / (self.NUM_VERTICAL_LINES - 1) if self.NUM_VERTICAL_LINES > 1 else 0
        for i in range(self.NUM_VERTICAL_LINES):
            x = offset_x + self.FRAME_THICKNESS + i * v_gap
            add_m(f"v_{i}", "kuda", self.KUMIKO_WIDTH, self.KUMIKO_THICKNESS, self.SHOJI_HEIGHT - self.FRAME_THICKNESS * 2, App.Vector(x, 0, self.FRAME_THICKNESS), True)

        usable_h = self.SHOJI_HEIGHT - self.FRAME_THICKNESS * 2
        h_gap = usable_h / (self.NUM_HORIZONTAL_LEVELS + 1)
        for idx, (l, v) in enumerate(conns):
            x = offset_x + self.FRAME_THICKNESS + v * v_gap
            z = self.FRAME_THICKNESS + (l + 1) * h_gap
            add_m(f"h_{idx}", "taruki", self.KUMIKO_WIDTH, self.KUMIKO_THICKNESS, v_gap, App.Vector(x, 0, z))

        return members
