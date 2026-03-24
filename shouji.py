"""
FreeCAD Parametric Shoji Screen Generator
Amida-kuji (あみだくじ) Kumiko Pattern - 2 Panels
"""

import FreeCAD as App
import Part
import math
import random

# ============== Parameters ==============
# Shoji frame dimensions (in mm)
SHOJI_WIDTH = 900      # Width of each shoji panel
SHOJI_HEIGHT = 1800    # Height of each shoji panel
FRAME_THICKNESS = 30   # Frame thickness
FRAME_DEPTH = 40       # Frame depth

# Kumiko (lattice) parameters
NUM_VERTICAL_LINES = 5    # Number of vertical lines (Amida-kuji poles)
NUM_HORIZONTAL_LEVELS = 10  # Number of horizontal connection levels
HORIZONTAL_PROBABILITY = 0.4  # Probability of horizontal bar at each level (0-1)

# Kumiko bar dimensions
KUMIKO_WIDTH = 10      # Width of kumiko bars
KUMIKO_THICKNESS = 8   # Thickness of kumiko bars

# Output
OUTPUT_FILE = "shoji_amida_2panels.FCStd"


def create_amida_pattern(width, height, num_vertical, num_levels, probability, seed=None):
    """
    Create Amida-kuji pattern with vertical lines and random horizontal connections
    
    Returns: list of horizontal connections [(level, vertical_index), ...]
    """
    if seed is not None:
        random.seed(seed)
    
    horizontal_connections = []
    
    for level in range(num_levels):
        # Available positions for horizontal bars (between vertical lines)
        available_positions = list(range(num_vertical - 1))
        
        # Randomly add horizontal bars with probability
        for pos in available_positions:
            if random.random() < probability:
                # Check if adjacent position already has a bar (avoid overlapping)
                if pos > 0 and (level, pos - 1) in horizontal_connections:
                    continue
                if pos < num_vertical - 2 and (level, pos + 1) in horizontal_connections:
                    continue
                horizontal_connections.append((level, pos))
    
    return horizontal_connections


def create_shoji_frame(width, height, thickness, depth):
    """
    Create the outer frame of a shoji screen
    """
    # Outer box
    outer_box = Part.makeBox(width, depth, height)
    
    # Inner cutout
    inner_width = width - thickness * 2
    inner_height = height - thickness * 2
    inner_cutout = Part.makeBox(inner_width, depth, inner_height)
    inner_cutout.translate(App.Vector(thickness, 0, thickness))
    
    # Frame = outer - inner
    frame = outer_box.cut(inner_cutout)
    
    return frame


def create_vertical_bar(x_pos, z_bottom, z_top, width, thickness, depth):
    """
    Create a vertical kumiko bar
    """
    bar = Part.makeBox(width, depth, z_top - z_bottom)
    bar.translate(App.Vector(x_pos - width/2, 0, z_bottom))
    return bar


def create_horizontal_bar(x_start, z_pos, length, width, thickness, depth):
    """
    Create a horizontal kumiko bar
    """
    bar = Part.makeBox(length, depth, width)
    bar.translate(App.Vector(x_start, 0, z_pos - width/2))
    return bar


def create_kumiko_pattern(frame_width, frame_height, num_vertical, num_levels, 
                          horizontal_connections, kumiko_width, kumiko_thickness, frame_thickness):
    """
    Create the complete kumiko lattice pattern
    """
    kumiko_parts = []
    
    # Calculate spacing
    usable_width = frame_width - frame_thickness * 2
    usable_height = frame_height - frame_thickness * 2
    
    vertical_spacing = usable_width / (num_vertical - 1) if num_vertical > 1 else 0
    level_spacing = usable_height / (num_levels + 1) if num_levels > 0 else 0
    
    # Create vertical bars
    for i in range(num_vertical):
        x_pos = frame_thickness + i * vertical_spacing
        z_bottom = frame_thickness
        z_top = frame_height - frame_thickness
        
        bar = create_vertical_bar(x_pos, z_bottom, z_top, kumiko_width, kumiko_thickness, FRAME_DEPTH)
        kumiko_parts.append(bar)
    
    # Create horizontal connections (Amida-kuji rungs)
    for level, vert_index in horizontal_connections:
        z_pos = frame_thickness + (level + 1) * level_spacing
        x_start = frame_thickness + vert_index * vertical_spacing
        length = vertical_spacing
        
        bar = create_horizontal_bar(x_start, z_pos, length, kumiko_width, kumiko_thickness, FRAME_DEPTH)
        kumiko_parts.append(bar)
    
    return kumiko_parts


def create_shoji_panel(width, height, frame_thickness, frame_depth, 
                       num_vertical, num_levels, probability, seed):
    """
    Create a complete shoji panel with frame and kumiko pattern
    """
    # Create frame
    frame = create_shoji_frame(width, height, frame_thickness, frame_depth)
    
    # Generate Amida-kuji pattern
    horizontal_connections = create_amida_pattern(
        width, height, num_vertical, num_levels, probability, seed
    )
    
    # Create kumiko pattern
    kumiko_parts = create_kumiko_pattern(
        width, height, num_vertical, num_levels,
        horizontal_connections, KUMIKO_WIDTH, KUMIKO_THICKNESS, frame_thickness
    )
    
    # Combine all parts
    all_parts = [frame] + kumiko_parts
    
    # Fuse all parts together
    if len(all_parts) == 1:
        return all_parts[0]
    else:
        result = all_parts[0]
        for part in all_parts[1:]:
            result = result.fuse(part)
        return result


def create_double_shoji(gap=100):
    """
    Create two shoji panels side by side (sliding door configuration)
    """
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
    print()
    
    # Create left panel (seed=42 for reproducible pattern)
    print("Creating left panel...")
    left_panel = create_shoji_panel(
        SHOJI_WIDTH, SHOJI_HEIGHT, FRAME_THICKNESS, FRAME_DEPTH,
        NUM_VERTICAL_LINES, NUM_HORIZONTAL_LEVELS, HORIZONTAL_PROBABILITY,
        seed=42
    )
    
    # Create right panel (seed=123 for different pattern)
    print("Creating right panel...")
    right_panel = create_shoji_panel(
        SHOJI_WIDTH, SHOJI_HEIGHT, FRAME_THICKNESS, FRAME_DEPTH,
        NUM_VERTICAL_LINES, NUM_HORIZONTAL_LEVELS, HORIZONTAL_PROBABILITY,
        seed=123
    )
    
    # Position panels (sliding door configuration with overlap)
    # Left panel slides to the left
    left_panel.translate(App.Vector(-SHOJI_WIDTH/2 - gap/2, 0, 0))
    
    # Right panel slides to the right
    right_panel.translate(App.Vector(SHOJI_WIDTH/2 + gap/2, 0, 0))
    
    # Create document
    doc = App.newDocument("Shoji_Amida")
    
    # Add parts to document
    left_obj = doc.addObject("Part::Feature", "Shoji_Left")
    left_obj.Shape = left_panel
    left_obj.Label = "Shoji Left (Amida)"
    
    right_obj = doc.addObject("Part::Feature", "Shoji_Right")
    right_obj.Shape = right_panel
    right_obj.Label = "Shoji Right (Amida)"
    
    # Create a compound for both panels
    compound = doc.addObject("Part::Compound", "Shoji_Complete")
    compound.Links = [left_obj, right_obj]
    
    # Set view properties
    doc.recompute()
    
    # Save document
    doc.saveAs(OUTPUT_FILE)
    print(f"\n✓ Saved to: {OUTPUT_FILE}")
    print(f"✓ Total width (both panels): {SHOJI_WIDTH * 2 + gap}mm")
    print(f"✓ Height: {SHOJI_HEIGHT}mm")
    
    return doc


def main():
    """
    Main function to generate the shoji screens
    """
    try:
        doc = create_double_shoji()
        print("\n" + "=" * 50)
        print("Generation Complete!")
        print("=" * 50)
        print("\nTo modify parameters, edit the variables at the top of this script:")
        print("  - SHOJI_WIDTH, SHOJI_HEIGHT: Panel dimensions")
        print("  - NUM_VERTICAL_LINES: Number of vertical poles")
        print("  - NUM_HORIZONTAL_LEVELS: Number of horizontal connection levels")
        print("  - HORIZONTAL_PROBABILITY: Density of horizontal bars (0.0-1.0)")
        print("\nOpen the .FCStd file in FreeCAD to view and modify.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
