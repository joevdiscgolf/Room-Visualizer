#!/usr/bin/env python3
"""
Room Layout Visualizer - Interactive headboard strip and lighting planner

Visualizes room layout with bed, nightstands, headboard strips, and lights.
All dimensions are configurable with sliders.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.widgets import Slider
import numpy as np
import plotly.graph_objects as go

# Initial configuration (all in inches)
INITIAL_CONFIG = {
    "room_width": 134.5,
    "nightstand_width": 24.0,
    "strip_width": 4.5,
    "right_light_from_left_wall": 103.0,  # Source of truth for bed calculation
    "wall_gap": 0.0,  # Gap from wall to furniture (0 = left-aligned)
    "num_strips": 15,  # Number of headboard strips across entire wall
    "bed_depth": 80.0,  # Depth of bed (front to back)
    "even_gap_size": 15.0,  # Gap size for even gaps mode
    "start_left_gap_size": 15.0,  # Gap size for start left mode
    "start_right_gap_size": 15.0,  # Gap size for start right mode
    "outer_gap_size": 15.0,  # Gap size outside lights (variable mode)
    "inner_gap_size": 10.0,  # Gap size between lights (variable mode)
    "num_inner_gaps": 3,  # Number of gaps between the two lights (variable mode)
}

# Layout modes
class LayoutMode:
    EVEN_GAPS = "even_gaps"
    START_LEFT = "start_left"
    START_RIGHT = "start_right"
    VARIABLE_GAPS = "variable_gaps"


class RoomLayoutVisualizer:
    def __init__(self):
        self.config = INITIAL_CONFIG.copy()
        self.layout_mode = LayoutMode.START_LEFT

        # Calculate initial bed width from constraint
        self._update_bed_width()

        # Create figure and axes - reasonable size that fits on screen
        self.fig, self.ax = plt.subplots(figsize=(16, 11))
        self.fig.set_facecolor('#fafbfc')
        plt.subplots_adjust(left=0.06, bottom=0.34, right=0.97, top=0.93)

        # Create mode selector (at top, above sliders)
        self._create_mode_selector()

        # Create sliders
        self._create_sliders()

        # Initial draw
        self.draw_layout()

    def _update_bed_width(self):
        """Calculate bed width based on right light position constraint."""
        # Right light is centered on right nightstand
        # right_light_pos = wall_gap + left_nightstand + bed_width + (right_nightstand / 2)
        # Solving for bed_width:
        right_light_pos = self.config["right_light_from_left_wall"]
        wall_gap = self.config["wall_gap"]
        nightstand_width = self.config["nightstand_width"]

        self.bed_width = right_light_pos - wall_gap - nightstand_width - (nightstand_width / 2)

    def _create_sliders(self):
        """Create sliders for adjustable parameters with improved styling."""
        slider_configs = [
            # Mode-specific settings (at top)
            ("even_gap_size", 5, 30, "Gap Size - Even Mode (in)"),
            ("start_left_gap_size", 5, 30, "Gap Size - Start Left Mode (in)"),
            ("start_right_gap_size", 5, 30, "Gap Size - Start Right Mode (in)"),
            ("outer_gap_size", 5, 30, "Outer Gap - Variable Mode (in)"),
            ("inner_gap_size", 5, 30, "Inner Gap - Variable Mode (in)"),
            ("num_inner_gaps", 1, 10, "Num Inner Gaps - Variable Mode"),
            # Room settings (below)
            ("room_width", 100, 200, "Room Width (in)"),
            ("nightstand_width", 18, 36, "Nightstand Width (in)"),
            ("strip_width", 2, 10, "Strip Width (in)"),
            ("right_light_from_left_wall", 80, 120, "Right Light from Left Wall (in)"),
            ("wall_gap", 0, 40, "Wall Gap (in)"),
            ("num_strips", 5, 30, "Number of Strips"),
            ("bed_depth", 60, 100, "Bed Depth (in)"),
        ]

        self.sliders = {}
        slider_height = 0.018
        slider_spacing = 0.024
        start_y = 0.26

        # Color scheme for sliders
        slider_color = '#3498db'
        track_color = '#ecf0f1'

        for idx, (key, min_val, max_val, label) in enumerate(slider_configs):
            y_pos = start_y - idx * slider_spacing
            ax_slider = plt.axes([0.15, y_pos, 0.70, slider_height])
            ax_slider.set_facecolor(track_color)

            slider = Slider(
                ax_slider, label, min_val, max_val,
                valinit=self.config[key], valstep=0.5 if key != "num_strips" and key != "num_inner_gaps" else 1,
                color=slider_color,
                initcolor='none'
            )
            # Style the slider components
            slider.label.set_fontsize(9)
            slider.label.set_fontweight('bold')
            slider.label.set_color('#2c3e50')
            slider.valtext.set_fontsize(9)
            slider.valtext.set_fontweight('bold')
            slider.valtext.set_color('#2c3e50')

            slider.on_changed(lambda val, k=key: self._on_slider_change(k, val))
            self.sliders[key] = slider

    def _create_mode_selector(self):
        """Create custom toggle buttons for layout mode selection - horizontal at top."""
        self.mode_buttons = []
        self.mode_button_axes = []
        mode_labels = ['Start Left', 'Start Right', 'Variable Gaps']

        # Title for mode selector - positioned at top left
        ax_title = plt.axes([0.07, 0.295, 0.08, 0.02])
        ax_title.set_xlim(0, 1)
        ax_title.set_ylim(0, 1)
        ax_title.axis('off')
        ax_title.text(0.5, 0.5, 'LAYOUT MODE:', ha='center', va='center',
                     fontsize=10, fontweight='bold', color='#2c3e50')

        # Horizontal buttons next to the title
        button_width = 0.12
        button_spacing = 0.008
        start_x = 0.16
        button_y = 0.29

        for idx, label in enumerate(mode_labels):
            x_pos = start_x + idx * (button_width + button_spacing)
            ax_btn = plt.axes([x_pos, button_y, button_width, 0.025])
            ax_btn.set_xlim(0, 1)
            ax_btn.set_ylim(0, 1)
            ax_btn.axis('off')

            # Store for click handling
            ax_btn.mode_label = label
            ax_btn.mode_idx = idx
            self.mode_button_axes.append(ax_btn)

            # Connect click event for the entire axis
            ax_btn.figure.canvas.mpl_connect('button_press_event',
                lambda event, ax=ax_btn, lbl=label: self._on_mode_button_click(event, ax, lbl))

        # Draw initial state
        self._update_mode_buttons()

    def _update_mode_buttons(self):
        """Update the visual appearance of mode buttons."""
        mode_labels = ['Start Left', 'Start Right', 'Variable Gaps']
        mode_map = {
            'Start Left': LayoutMode.START_LEFT,
            'Start Right': LayoutMode.START_RIGHT,
            'Variable Gaps': LayoutMode.VARIABLE_GAPS
        }

        for idx, ax in enumerate(self.mode_button_axes):
            ax.clear()
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')

            label = mode_labels[idx]
            is_selected = (mode_map[label] == self.layout_mode)

            # Draw button background
            if is_selected:
                bg_color = '#3498db'
                text_color = 'white'
                edge_color = '#2980b9'
            else:
                bg_color = '#ecf0f1'
                text_color = '#2c3e50'
                edge_color = '#bdc3c7'

            # Rounded rectangle background
            btn_rect = patches.FancyBboxPatch(
                (0.02, 0.08), 0.96, 0.84,
                boxstyle=patches.BoxStyle("Round", pad=0.02, rounding_size=0.3),
                facecolor=bg_color, edgecolor=edge_color, linewidth=2,
                transform=ax.transAxes, zorder=1
            )
            ax.add_patch(btn_rect)

            # Radio indicator (smaller for horizontal layout)
            indicator_x = 0.10
            indicator_y = 0.5

            outer_circle = patches.Circle(
                (indicator_x, indicator_y), 0.15,
                facecolor='white', edgecolor=edge_color, linewidth=1.5,
                transform=ax.transAxes, zorder=2
            )
            ax.add_patch(outer_circle)

            if is_selected:
                inner_circle = patches.Circle(
                    (indicator_x, indicator_y), 0.08,
                    facecolor='#2980b9', edgecolor='none',
                    transform=ax.transAxes, zorder=3
                )
                ax.add_patch(inner_circle)

            # Label text (centered in remaining space)
            ax.text(0.55, 0.5, label, ha='center', va='center',
                   fontsize=9, fontweight='bold' if is_selected else 'normal',
                   color=text_color, transform=ax.transAxes, zorder=4)

        plt.draw()

    def _on_mode_button_click(self, event, ax, label):
        """Handle click on mode button."""
        if event.inaxes != ax:
            return

        mode_map = {
            'Start Left': LayoutMode.START_LEFT,
            'Start Right': LayoutMode.START_RIGHT,
            'Variable Gaps': LayoutMode.VARIABLE_GAPS
        }

        if label in mode_map:
            self.layout_mode = mode_map[label]
            self._update_mode_buttons()
            self.draw_layout()

    def _on_slider_change(self, key, val):
        """Handle slider value changes."""
        self.config[key] = val
        self._update_bed_width()
        self.draw_layout()

    def draw_layout(self):
        """Draw the complete room layout."""
        self.ax.clear()

        # Calculate positions
        positions = self._calculate_positions()

        # Draw components
        self._draw_room(positions)
        self._draw_nightstands(positions)
        self._draw_bed(positions)
        self._draw_strips(positions)
        self._draw_lights(positions)
        self._draw_dimensions(positions)

        # Set axis properties for top view
        bed_depth = self.config["bed_depth"]
        strip_data = positions["strips"]
        num_strips = len(strip_data["strips"])
        gap_width = strip_data.get("gap_width", 0)
        mode = strip_data.get("mode", "even")
        total_room_depth = bed_depth + 48  # Add 48" at foot of bed

        self.ax.set_xlim(-10, self.config["room_width"] + 10)
        self.ax.set_ylim(-25, total_room_depth + 15)
        self.ax.set_xlabel('Distance from Left Wall (inches)', fontsize=11, fontweight='bold')
        self.ax.set_ylabel('Depth from Wall (inches)', fontsize=11, fontweight='bold')
        self.ax.set_aspect('equal')

        # Create title with summary
        total_strip_width = num_strips * self.config["strip_width"]

        if mode == "variable":
            outer_gap = strip_data.get("outer_gap", 0)
            inner_gap = strip_data.get("inner_gap", 0)
            num_inner = strip_data.get("num_inner_gaps", 0)
            mode_desc = f"Variable (Outer: {outer_gap:.2f}\" for lights, Inner: {inner_gap:.2f}\" x {num_inner} auto-calc)"
        else:
            mode_desc = {
                "even": f"Even gaps ({gap_width:.2f}\" auto-calc to center left light)",
                "start_left": f"Start Left ({gap_width:.2f}\" auto-calc, {strip_data.get('leftover', 0):.2f}\" leftover)",
                "start_right": f"Start Right ({gap_width:.2f}\" auto-calc, {strip_data.get('leftover', 0):.2f}\" leftover)",
            }.get(mode, "")

        title_text = (
            f'Room Layout Visualizer\n'
            f'Room: {self.config["room_width"]:.1f}" | '
            f'Bed: {positions["bed"]["width"]:.1f}" x {bed_depth:.1f}" | '
            f'{num_strips} Strips @ {self.config["strip_width"]}"ea = {total_strip_width:.1f}" | '
            f'{mode_desc}'
        )
        self.ax.set_title(title_text, fontsize=11, fontweight='bold', pad=15)
        self.ax.grid(True, alpha=0.3, linestyle='--')

        plt.draw()

    def _calculate_positions(self):
        """Calculate all positions for room elements."""
        wall_gap = self.config["wall_gap"]
        nightstand_width = self.config["nightstand_width"]

        # Left nightstand
        left_nightstand_x = wall_gap
        left_nightstand_width = nightstand_width

        # Bed
        bed_x = left_nightstand_x + left_nightstand_width
        bed_width = self.bed_width

        # Right nightstand
        right_nightstand_x = bed_x + bed_width
        right_nightstand_width = nightstand_width

        # Verify constraint
        right_light_calc = right_nightstand_x + (right_nightstand_width / 2)

        # Strips
        strip_positions = self._calculate_strip_positions(bed_x, bed_width)

        # Lights (always centered on nightstands)
        light_positions = self._calculate_light_positions(bed_x, bed_width)

        return {
            "left_nightstand": {"x": left_nightstand_x, "width": left_nightstand_width},
            "bed": {"x": bed_x, "width": bed_width},
            "right_nightstand": {"x": right_nightstand_x, "width": right_nightstand_width},
            "strips": strip_positions,
            "lights": light_positions,
            "right_light_calc": right_light_calc,
        }

    def _calculate_strip_positions(self, bed_x, bed_width):
        """Calculate positions for headboard strips based on selected mode."""
        num_strips = int(self.config["num_strips"])
        strip_width = self.config["strip_width"]
        room_width = self.config["room_width"]

        if self.layout_mode == LayoutMode.EVEN_GAPS:
            return self._calculate_even_gaps(num_strips, strip_width, room_width, bed_x, bed_width)
        elif self.layout_mode == LayoutMode.START_LEFT:
            return self._calculate_start_left(num_strips, strip_width, room_width, bed_x, bed_width)
        elif self.layout_mode == LayoutMode.START_RIGHT:
            return self._calculate_start_right(num_strips, strip_width, room_width, bed_x, bed_width)
        elif self.layout_mode == LayoutMode.VARIABLE_GAPS:
            return self._calculate_variable_gaps(num_strips, strip_width, room_width, bed_x, bed_width)

    def _calculate_even_gaps(self, num_strips, strip_width, room_width, bed_x, bed_width):
        """Calculate strip positions with even gaps across entire wall.

        Pattern: |S|--gap--|S|--gap--|S|--gap--|S|
        First strip starts flush at x=0.
        Gap size is AUTO-CALCULATED to center the left light in the first gap.
        """
        # Get left light position
        wall_gap = self.config["wall_gap"]
        nightstand_width = self.config["nightstand_width"]
        left_light_x = wall_gap + nightstand_width / 2

        # Auto-calculate gap size to center left light in first gap
        # First strip: 0 to strip_width
        # First gap: strip_width to (strip_width + gap)
        # For light to be centered: strip_width + gap/2 = left_light_x
        # gap = 2 * (left_light_x - strip_width)
        gap_width = 2 * (left_light_x - strip_width)

        # Ensure gap is at least 1 inch
        if gap_width < 1:
            gap_width = 1

        strips = []
        current_x = 0  # Start flush at left wall

        for i in range(num_strips):
            if current_x + strip_width > room_width:
                break  # Don't add strips that go past the wall

            strips.append({
                "x": current_x,
                "width": strip_width,
                "gap_before": gap_width if i > 0 else 0,
            })
            current_x += strip_width + gap_width

        return {
            "strips": strips,
            "gap_width": gap_width,
            "mode": "even",
            "bed_start": bed_x,
            "bed_end": bed_x + bed_width,
        }

    def _calculate_start_left(self, num_strips, strip_width, room_width, bed_x, bed_width):
        """Calculate strip positions starting from left.

        Pattern: |S|--gap--|S|--gap--|S|... [leftover space]
        First strip flush at x=0.
        Gap size is AUTO-CALCULATED to center the left light in the first gap.
        """
        # Get left light position
        wall_gap = self.config["wall_gap"]
        nightstand_width = self.config["nightstand_width"]
        left_light_x = wall_gap + nightstand_width / 2

        # Auto-calculate gap size to center left light in first gap
        gap_width = 2 * (left_light_x - strip_width)

        # Ensure gap is at least 1 inch
        if gap_width < 1:
            gap_width = 1

        strips = []
        current_x = 0  # Start flush at left wall

        # Continue adding strips until we run out of room
        while current_x + strip_width <= room_width:
            strips.append({
                "x": current_x,
                "width": strip_width,
                "gap_before": gap_width if len(strips) > 0 else 0,
            })
            current_x += strip_width + gap_width

        # Calculate leftover space
        if strips:
            last_strip_end = strips[-1]["x"] + strip_width
            leftover = room_width - last_strip_end
        else:
            leftover = room_width

        return {
            "strips": strips,
            "gap_width": gap_width,
            "leftover": leftover,
            "mode": "start_left",
            "bed_start": bed_x,
            "bed_end": bed_x + bed_width,
        }

    def _calculate_start_right(self, num_strips, strip_width, room_width, bed_x, bed_width):
        """Calculate strip positions starting from right.

        Pattern: [leftover space] ...|S|--gap--|S|--gap--|S|
        Last strip flush at right wall.
        Gap size is AUTO-CALCULATED to center the right light in the SECOND gap from the right.
        """
        # Get right light position
        right_light_x = self.config["right_light_from_left_wall"]

        # Auto-calculate gap size to center right light in SECOND gap from right
        # Pattern from right to left:
        #   Last strip: (room_width - strip_width) to room_width
        #   Gap 1: (room_width - strip_width - gap) to (room_width - strip_width)
        #   Strip 2: (room_width - 2*strip_width - gap) to (room_width - strip_width - gap)
        #   Gap 2: (room_width - 2*strip_width - 2*gap) to (room_width - 2*strip_width - gap) ← Light centered here
        # Gap 2 center = room_width - 2*strip_width - 1.5*gap
        # For light to be centered: room_width - 2*strip_width - 1.5*gap = right_light_x
        # 1.5*gap = room_width - 2*strip_width - right_light_x
        # gap = (room_width - 2*strip_width - right_light_x) / 1.5
        gap_width = (room_width - 2 * strip_width - right_light_x) / 1.5

        # Ensure gap is at least 1 inch
        if gap_width < 1:
            gap_width = 1

        # Build from right to left
        strips = []
        current_x = room_width - strip_width  # Start flush at right wall

        for i in range(num_strips):
            if current_x < 0:
                break

            strips.insert(0, {  # Insert at beginning to maintain left-to-right order
                "x": current_x,
                "width": strip_width,
                "gap_after": gap_width if i > 0 else 0,
            })
            current_x -= (gap_width + strip_width)

        # Calculate leftover space on left
        leftover = strips[0]["x"] if strips else 0

        return {
            "strips": strips,
            "gap_width": gap_width,
            "leftover": leftover,
            "mode": "start_right",
            "bed_start": bed_x,
            "bed_end": bed_x + bed_width,
        }

    def _calculate_variable_gaps(self, num_strips, strip_width, room_width, bed_x, bed_width):
        """Calculate strip positions with variable gap sizes.

        Pattern: |S|--15"--|S|--inner--|S|--inner--|S|--15"--|S|--15"--|S|

        Layout:
        - Left side: Strip + 15" gap (left light centered) + Strip
        - Middle: Variable inner gaps (based on num_inner_gaps)
        - Right side: Continues with 15" gaps to wall edge (right light centered in one)

        Outer gap uses Start Left logic: 2 * (left_light_x - strip_width)
        """
        num_inner_gaps = int(self.config["num_inner_gaps"])

        # Get light positions
        wall_gap = self.config["wall_gap"]
        nightstand_width = self.config["nightstand_width"]
        left_light_x = wall_gap + nightstand_width / 2

        # Use Start Left logic to calculate outer gap (centers left light)
        # gap = 2 * (left_light_x - strip_width)
        outer_gap = 2 * (left_light_x - strip_width)
        if outer_gap < 1:
            outer_gap = 1

        # Build the strip list
        strips = []

        # LEFT SIDE: Strip at 0, then 15" gap
        strips.append({"x": 0, "width": strip_width})

        # INNER ZONE starts after the 15" gap
        # The strip at (strip_width + outer_gap) is the FIRST inner strip
        inner_zone_start = strip_width + outer_gap

        # Calculate where right side pattern needs to start
        right_light_x = self.config["right_light_from_left_wall"]

        # The gap containing right light has its center at right_light_x
        # Gap runs from (right_light_x - outer_gap/2) to (right_light_x + outer_gap/2)
        right_light_gap_start = right_light_x - outer_gap / 2

        # Strip before this gap (this is the LAST inner strip)
        last_inner_strip_x = right_light_gap_start - strip_width

        # Inner zone width: from START of first inner strip to START of last inner strip
        # This distance contains: (num_inner_gaps) strips + (num_inner_gaps) gaps
        # Because: first strip, gap, strip, gap, strip, ..., gap, last strip
        #          └─────── num_inner_gaps × (strip + gap) ────────┘
        inner_zone_width = last_inner_strip_x - inner_zone_start

        # Calculate inner gap size
        if num_inner_gaps > 0:
            # inner_zone_width = num_inner_gaps * strip_width + num_inner_gaps * inner_gap
            # inner_gap = (inner_zone_width - num_inner_gaps * strip_width) / num_inner_gaps
            inner_gap = (inner_zone_width - num_inner_gaps * strip_width) / num_inner_gaps
        else:
            # Only one strip in inner zone, no gaps
            inner_gap = 0

        if inner_gap < 0:
            inner_gap = 0

        # Add inner strips (these include the strips that appear after the left 15" gap)
        current_x = inner_zone_start
        for i in range(num_inner_gaps + 1):
            strips.append({"x": current_x, "width": strip_width})
            current_x += strip_width + inner_gap

        # RIGHT SIDE: Continue with outer_gap pattern from after last inner strip
        # Start at the position after last inner strip + outer_gap
        current_x = last_inner_strip_x + strip_width + outer_gap
        # Continue adding strips all the way to the right edge
        while current_x + strip_width <= room_width + 0.01:  # Small epsilon for floating point
            strips.append({"x": current_x, "width": strip_width})
            current_x += strip_width + outer_gap

        return {
            "strips": strips,
            "outer_gap": outer_gap,  # Same for both left and right
            "inner_gap": inner_gap,
            "num_inner_gaps": num_inner_gaps,
            "mode": "variable",
            "bed_start": bed_x,
            "bed_end": bed_x + bed_width,
        }

    def _calculate_light_positions(self, bed_x, bed_width):
        """Calculate light positions (always centered on nightstands)."""
        wall_gap = self.config["wall_gap"]
        nightstand_width = self.config["nightstand_width"]

        # Left light centered on left nightstand
        left_light_x = wall_gap + nightstand_width / 2

        # Right light centered on right nightstand
        right_nightstand_x = bed_x + bed_width
        right_light_x = right_nightstand_x + nightstand_width / 2

        return {
            "left": left_light_x,
            "right": right_light_x,
        }

    def _draw_room(self, positions):
        """Draw room walls."""
        room_width = self.config["room_width"]
        bed_depth = self.config["bed_depth"]
        total_room_depth = bed_depth + 48  # Add 48" at foot of bed

        # Floor
        floor = patches.Rectangle(
            (0, 0), room_width, total_room_depth,
            linewidth=0, facecolor='#f5f5dc', alpha=0.3, zorder=0
        )
        self.ax.add_patch(floor)

        # Left wall
        self.ax.axvline(x=0, color='#654321', linewidth=4, label='Walls', zorder=1)

        # Right wall
        self.ax.axvline(x=room_width, color='#654321', linewidth=4, zorder=1)

        # Back wall (headboard wall)
        self.ax.axhline(y=total_room_depth, color='#654321', linewidth=4, linestyle='-', zorder=1)

        # Add wall labels
        self.ax.text(-5, total_room_depth / 2, 'Left\nWall', ha='center', va='center', fontsize=10, fontweight='bold', color='#654321')
        self.ax.text(room_width + 5, total_room_depth / 2, 'Right\nWall', ha='center', va='center', fontsize=10, fontweight='bold', color='#654321')
        self.ax.text(room_width / 2, total_room_depth + 5, 'Back Wall (Headboard)', ha='center', va='center', fontsize=10, fontweight='bold', color='#654321')

    def _draw_nightstands(self, positions):
        """Draw nightstands."""
        left_ns = positions["left_nightstand"]
        right_ns = positions["right_nightstand"]
        bed_depth = self.config["bed_depth"]
        total_room_depth = bed_depth + 48  # Add 48" at foot of bed
        ns_depth = 20  # Nightstand depth
        ns_y_start = total_room_depth - ns_depth  # Flush against back wall

        # Left nightstand (with shadow)
        shadow_left = patches.Rectangle(
            (left_ns["x"] + 1, ns_y_start + 1), left_ns["width"], ns_depth,
            linewidth=0, facecolor='gray', alpha=0.3, zorder=2
        )
        self.ax.add_patch(shadow_left)

        rect_left = patches.Rectangle(
            (left_ns["x"], ns_y_start), left_ns["width"], ns_depth,
            linewidth=2, edgecolor='#654321', facecolor='#daa520', label='Nightstands', zorder=3
        )
        self.ax.add_patch(rect_left)
        self.ax.text(
            left_ns["x"] + left_ns["width"] / 2, ns_y_start + ns_depth / 2,
            'Left\nNightstand', ha='center', va='center', fontsize=9, fontweight='bold', color='white'
        )

        # Right nightstand (with shadow)
        shadow_right = patches.Rectangle(
            (right_ns["x"] + 1, ns_y_start + 1), right_ns["width"], ns_depth,
            linewidth=0, facecolor='gray', alpha=0.3, zorder=2
        )
        self.ax.add_patch(shadow_right)

        rect_right = patches.Rectangle(
            (right_ns["x"], ns_y_start), right_ns["width"], ns_depth,
            linewidth=2, edgecolor='#654321', facecolor='#daa520', zorder=3
        )
        self.ax.add_patch(rect_right)
        self.ax.text(
            right_ns["x"] + right_ns["width"] / 2, ns_y_start + ns_depth / 2,
            'Right\nNightstand', ha='center', va='center', fontsize=9, fontweight='bold', color='white'
        )

    def _draw_bed(self, positions):
        """Draw bed."""
        bed = positions["bed"]
        bed_depth = self.config["bed_depth"]
        total_room_depth = bed_depth + 48  # Add 48" at foot of bed
        bed_y_start = total_room_depth - bed_depth  # Flush against back wall

        # Shadow
        shadow_bed = patches.Rectangle(
            (bed["x"] + 2, bed_y_start + 2), bed["width"], bed_depth,
            linewidth=0, facecolor='gray', alpha=0.3, zorder=2
        )
        self.ax.add_patch(shadow_bed)

        # Mattress
        mattress = patches.Rectangle(
            (bed["x"], bed_y_start), bed["width"], bed_depth,
            linewidth=3, edgecolor='#2c3e50', facecolor='#3498db', alpha=0.7, label='Bed', zorder=3
        )
        self.ax.add_patch(mattress)

        # Pillows at head (top - against wall)
        pillow_height = bed_depth * 0.2
        pillow1 = patches.Rectangle(
            (bed["x"] + bed["width"] * 0.1, total_room_depth - pillow_height - 2),
            bed["width"] * 0.35, pillow_height,
            linewidth=1, edgecolor='white', facecolor='#ecf0f1', alpha=0.8, zorder=4
        )
        pillow2 = patches.Rectangle(
            (bed["x"] + bed["width"] * 0.55, total_room_depth - pillow_height - 2),
            bed["width"] * 0.35, pillow_height,
            linewidth=1, edgecolor='white', facecolor='#ecf0f1', alpha=0.8, zorder=4
        )
        self.ax.add_patch(pillow1)
        self.ax.add_patch(pillow2)

        # Label
        self.ax.text(
            bed["x"] + bed["width"] / 2, bed_y_start + bed_depth / 2,
            f'BED\n{bed["width"]:.1f}" × {bed_depth:.1f}"',
            ha='center', va='center', fontsize=11, fontweight='bold', color='white'
        )

    def _draw_strips(self, positions):
        """Draw headboard strips and wall measurements."""
        self._draw_strips_top_view(positions)

    def _draw_strips_top_view(self, positions):
        """Draw strips in top-down view."""
        strip_data = positions["strips"]
        strips = strip_data["strips"]
        bed_start = strip_data["bed_start"]
        bed_end = strip_data["bed_end"]
        mode = strip_data.get("mode", "even")
        leftover = strip_data.get("leftover", 0)

        bed_depth = self.config["bed_depth"]
        strip_height = 3  # Make strips thinner and to-scale
        strip_y = bed_depth + 5
        room_width = self.config["room_width"]

        # Get light positions for variable mode
        wall_gap = self.config["wall_gap"]
        nightstand_width = self.config["nightstand_width"]
        left_light_x = wall_gap + nightstand_width / 2
        right_light_x = self.config["right_light_from_left_wall"]

        # Draw all gaps and strips
        for idx, strip in enumerate(strips):
            strip_x = strip["x"]
            strip_w = strip["width"]

            # Draw gap before this strip
            if idx == 0:
                # First gap (from left wall)
                gap_start = 0
                gap_end = strip_x
                if gap_end - gap_start > 0.1:
                    if mode == "start_right":
                        # Show leftover on left
                        self._draw_gap_region(gap_start, gap_end, strip_y, strip_height,
                                             f'Leftover\n{leftover:.2f}"', 'gray')
                    elif gap_end > 0:
                        # Not flush left - show gap
                        self._draw_gap_region(gap_start, gap_end, strip_y, strip_height,
                                             f'{gap_end:.2f}"', '#9c27b0')

            # Draw the strip
            self._draw_strip_rect(strip_x, strip_y, strip_w, strip_height, idx + 1)

            # Draw gap after this strip
            if idx < len(strips) - 1:
                next_strip = strips[idx + 1]
                gap_start = strip_x + strip_w
                gap_end = next_strip["x"]
                gap_size = gap_end - gap_start

                # Determine color based on mode and position (for variable gaps)
                if mode == "variable":
                    # Check if this gap contains a light
                    gap_center = (gap_start + gap_end) / 2
                    if abs(gap_center - left_light_x) < gap_size / 2 or abs(gap_center - right_light_x) < gap_size / 2:
                        color = '#ff6b35'  # Highlight gaps containing lights (orange)
                    else:
                        color = '#9c27b0'  # Inner gaps (purple)
                else:
                    color = '#9c27b0'

                self._draw_gap_region(gap_start, gap_end, strip_y, strip_height,
                                     f'{gap_size:.2f}"', color)
            else:
                # Last gap (to right wall or leftover)
                gap_start = strip_x + strip_w
                gap_end = room_width
                gap_size = gap_end - gap_start
                if mode == "start_left" and gap_size > 0.1:
                    # Show leftover on right
                    self._draw_gap_region(gap_start, gap_end, strip_y, strip_height,
                                         f'Leftover\n{leftover:.2f}"', 'gray')
                elif gap_size > 0.1:
                    self._draw_gap_region(gap_start, gap_end, strip_y, strip_height,
                                         f'{gap_size:.2f}"', '#9c27b0')

        # Mark bed boundaries
        self.ax.axvline(x=bed_start, color='blue', linewidth=1, linestyle=':', alpha=0.5, ymin=0.7, ymax=0.85)
        self.ax.axvline(x=bed_end, color='blue', linewidth=1, linestyle=':', alpha=0.5, ymin=0.7, ymax=0.85)

    def _draw_gap_region(self, start_x, end_x, y, height, label, color):
        """Draw a gap region with label."""
        gap_width = end_x - start_x
        if gap_width < 0.1:
            return

        # Draw faint background for gap
        gap_rect = patches.Rectangle(
            (start_x, y), gap_width, height,
            linewidth=0, facecolor=color, alpha=0.1, zorder=2
        )
        self.ax.add_patch(gap_rect)

        # Label
        self.ax.text(
            start_x + gap_width / 2, y + height + 3,
            label, ha='center', va='bottom',
            fontsize=8, color=color, style='italic', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8, edgecolor=color)
        )

    def _draw_strip_rect(self, x, y, width, height, number):
        """Draw a single strip rectangle."""
        # Shadow
        shadow = patches.Rectangle(
            (x + 0.3, y + 0.3), width, height,
            linewidth=0, facecolor='gray', alpha=0.3, zorder=3
        )
        self.ax.add_patch(shadow)

        # Strip
        rect = patches.Rectangle(
            (x, y), width, height,
            linewidth=1.5, edgecolor='#8b0000', facecolor='#cd5c5c',
            label='Headboard Strips' if number == 1 else '', zorder=4
        )
        self.ax.add_patch(rect)

        # Label (only if strip is wide enough)
        if width > 3:
            self.ax.text(
                x + width / 2, y + height / 2,
                str(number), ha='center', va='center',
                fontsize=7, fontweight='bold', color='white'
            )

    def _draw_lights(self, positions):
        """Draw light positions."""
        lights = positions["lights"]
        bed_depth = self.config["bed_depth"]
        total_room_depth = bed_depth + 48  # Add 48" at foot of bed
        light_y = total_room_depth  # On the back wall

        # Left light (with glow effect)
        glow_left = patches.Circle(
            (lights["left"], light_y), 5, color='#ffd700', alpha=0.2, zorder=6
        )
        self.ax.add_patch(glow_left)

        circle_left = patches.Circle(
            (lights["left"], light_y), 3, color='#ffd700', ec='#ff8c00', linewidth=2.5, label='Lights', zorder=7
        )
        self.ax.add_patch(circle_left)

        # Right light (with glow effect)
        glow_right = patches.Circle(
            (lights["right"], light_y), 5, color='#ffd700', alpha=0.2, zorder=6
        )
        self.ax.add_patch(glow_right)

        circle_right = patches.Circle(
            (lights["right"], light_y), 3, color='#ffd700', ec='#ff8c00', linewidth=2.5, zorder=7
        )
        self.ax.add_patch(circle_right)

        # Labels
        self.ax.text(lights["left"], light_y + 8, f'{lights["left"]:.1f}"',
                    ha='center', fontsize=9, color='#ff8c00', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='#ff8c00'))
        self.ax.text(lights["right"], light_y + 8, f'{lights["right"]:.1f}"',
                    ha='center', fontsize=9, color='#ff8c00', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='#ff8c00'))

    def _draw_dimensions(self, positions):
        """Draw dimension annotations."""
        bed_depth = self.config["bed_depth"]
        total_room_depth = bed_depth + 48  # Add 48" at foot of bed

        # Room width
        self.ax.annotate(
            '', xy=(self.config["room_width"], total_room_depth + 8), xytext=(0, total_room_depth + 8),
            arrowprops=dict(arrowstyle='<->', color='black', lw=2)
        )
        self.ax.text(
            self.config["room_width"] / 2, total_room_depth + 11,
            f'Room Width: {self.config["room_width"]:.1f}"',
            ha='center', fontsize=10, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.9, edgecolor='black', linewidth=1.5)
        )

        # Light verification (lights always centered on nightstands)
        lights = positions["lights"]
        right_light_actual = lights["right"]
        right_light_calc = positions["right_light_calc"]
        right_light_constraint = self.config["right_light_from_left_wall"]
        match = abs(right_light_calc - right_light_constraint) < 0.1

        self.ax.text(
            self.config["room_width"] / 2, -18,
            f'Lights (on wall) - Left: {lights["left"]:.1f}" | Right: {right_light_actual:.1f}" (target: {right_light_constraint:.1f}") {"✓" if match else "✗"}',
            ha='center', fontsize=9, color='green' if match else 'red', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.9, linewidth=1.5)
        )

        # Legend - position it in upper right inside the plot
        self.ax.legend(loc='upper right', fontsize=9, framealpha=0.95,
                      edgecolor='black', fancybox=True, shadow=True)

    def create_3d_layout(self):
        """Create a 3D plotly visualization of the room layout."""
        positions = self._calculate_positions()

        room_width = self.config["room_width"]
        bed_depth = self.config["bed_depth"]
        total_room_depth = bed_depth + 48  # Add 48" at foot of bed
        wall_height = 100  # Height of walls in inches
        headboard_height = 24  # Strips go ~24" above bed (half bed height)

        # Create figure
        fig = go.Figure()

        # Floor
        fig.add_trace(go.Mesh3d(
            x=[0, room_width, room_width, 0],
            y=[0, 0, total_room_depth, total_room_depth],
            z=[0, 0, 0, 0],
            i=[0, 0],
            j=[1, 2],
            k=[2, 3],
            color='#f5f5dc',
            opacity=0.3,
            name='Floor',
            showlegend=True,
            hoverinfo='skip'
        ))

        # Left wall
        fig.add_trace(go.Mesh3d(
            x=[0, 0, 0, 0],
            y=[0, total_room_depth, total_room_depth, 0],
            z=[0, 0, wall_height, wall_height],
            i=[0, 0],
            j=[1, 2],
            k=[2, 3],
            color='#8B7355',
            opacity=0.4,
            name='Walls',
            showlegend=True,
            hoverinfo='skip'
        ))

        # Right wall
        fig.add_trace(go.Mesh3d(
            x=[room_width, room_width, room_width, room_width],
            y=[0, total_room_depth, total_room_depth, 0],
            z=[0, 0, wall_height, wall_height],
            i=[0, 0],
            j=[1, 2],
            k=[2, 3],
            color='#8B7355',
            opacity=0.4,
            showlegend=False,
            hoverinfo='skip'
        ))

        # Back wall (headboard wall)
        fig.add_trace(go.Mesh3d(
            x=[0, room_width, room_width, 0],
            y=[total_room_depth, total_room_depth, total_room_depth, total_room_depth],
            z=[0, 0, wall_height, wall_height],
            i=[0, 0],
            j=[1, 2],
            k=[2, 3],
            color='#D2B48C',
            opacity=0.5,
            name='Back Wall',
            showlegend=True,
            hoverinfo='skip'
        ))

        # Bed (flush against back wall)
        bed = positions["bed"]
        bed_height = 24  # Mattress height in inches
        bed_x, bed_width = bed["x"], bed["width"]
        bed_y_start = total_room_depth - bed_depth  # Flush against back wall

        fig.add_trace(go.Mesh3d(
            x=[bed_x, bed_x + bed_width, bed_x + bed_width, bed_x, bed_x, bed_x + bed_width, bed_x + bed_width, bed_x],
            y=[bed_y_start, bed_y_start, total_room_depth, total_room_depth, bed_y_start, bed_y_start, total_room_depth, total_room_depth],
            z=[0, 0, 0, 0, bed_height, bed_height, bed_height, bed_height],
            i=[0, 0, 0, 0, 4, 4, 6, 6, 4, 5, 2, 2],
            j=[1, 2, 4, 5, 5, 6, 7, 2, 0, 1, 3, 6],
            k=[2, 3, 5, 1, 6, 7, 4, 6, 5, 6, 6, 7],
            color='#3498db',
            opacity=0.7,
            name='Bed',
            showlegend=True,
            hoverinfo='skip'
        ))

        # Nightstands (flush against back wall)
        left_ns = positions["left_nightstand"]
        right_ns = positions["right_nightstand"]
        ns_depth = 20
        ns_height = 24
        ns_y_start = total_room_depth - ns_depth  # Flush against back wall

        # Left nightstand
        fig.add_trace(go.Mesh3d(
            x=[left_ns["x"], left_ns["x"] + left_ns["width"], left_ns["x"] + left_ns["width"], left_ns["x"],
               left_ns["x"], left_ns["x"] + left_ns["width"], left_ns["x"] + left_ns["width"], left_ns["x"]],
            y=[ns_y_start, ns_y_start, total_room_depth, total_room_depth, ns_y_start, ns_y_start, total_room_depth, total_room_depth],
            z=[0, 0, 0, 0, ns_height, ns_height, ns_height, ns_height],
            i=[0, 0, 0, 0, 4, 4, 6, 6, 4, 5, 2, 2],
            j=[1, 2, 4, 5, 5, 6, 7, 2, 0, 1, 3, 6],
            k=[2, 3, 5, 1, 6, 7, 4, 6, 5, 6, 6, 7],
            color='#daa520',
            opacity=0.9,
            name='Nightstands',
            showlegend=True,
            hoverinfo='skip'
        ))

        # Right nightstand
        fig.add_trace(go.Mesh3d(
            x=[right_ns["x"], right_ns["x"] + right_ns["width"], right_ns["x"] + right_ns["width"], right_ns["x"],
               right_ns["x"], right_ns["x"] + right_ns["width"], right_ns["x"] + right_ns["width"], right_ns["x"]],
            y=[ns_y_start, ns_y_start, total_room_depth, total_room_depth, ns_y_start, ns_y_start, total_room_depth, total_room_depth],
            z=[0, 0, 0, 0, ns_height, ns_height, ns_height, ns_height],
            i=[0, 0, 0, 0, 4, 4, 6, 6, 4, 5, 2, 2],
            j=[1, 2, 4, 5, 5, 6, 7, 2, 0, 1, 3, 6],
            k=[2, 3, 5, 1, 6, 7, 4, 6, 5, 6, 6, 7],
            color='#daa520',
            opacity=0.9,
            showlegend=False,
            hoverinfo='skip'
        ))

        # Headboard strips (grey, only bed height above furniture)
        strip_data = positions["strips"]
        strips = strip_data["strips"]
        strip_depth = 2  # Depth of strip coming out from wall
        strip_y_start = total_room_depth - strip_depth
        strip_z_start = bed_height  # Start at bed height
        strip_z_end = bed_height + headboard_height  # End ~48" above bed

        for idx, strip in enumerate(strips):
            strip_x = strip["x"]
            strip_width = strip["width"]

            fig.add_trace(go.Mesh3d(
                x=[strip_x, strip_x + strip_width, strip_x + strip_width, strip_x,
                   strip_x, strip_x + strip_width, strip_x + strip_width, strip_x],
                y=[strip_y_start, strip_y_start, total_room_depth, total_room_depth, strip_y_start, strip_y_start, total_room_depth, total_room_depth],
                z=[strip_z_start, strip_z_start, strip_z_start, strip_z_start, strip_z_end, strip_z_end, strip_z_end, strip_z_end],
                i=[0, 0, 0, 0, 4, 4, 6, 6, 4, 5, 2, 2],
                j=[1, 2, 4, 5, 5, 6, 7, 2, 0, 1, 3, 6],
                k=[2, 3, 5, 1, 6, 7, 4, 6, 5, 6, 6, 7],
                color='#808080',  # Grey
                opacity=0.9,
                name='Headboard Strips' if idx == 0 else None,
                showlegend=idx == 0,
                hoverinfo='skip'
            ))

        # Horizontal strip across all vertical strips (headboard look)
        # Extends from first vertical strip all the way to the right wall edge
        if strips:
            first_strip_x = strips[0]["x"]
            horizontal_strip_end = room_width  # Extend to right wall edge
            horizontal_strip_width = horizontal_strip_end - first_strip_x
            horizontal_strip_height = 4  # Horizontal strip thickness
            horizontal_strip_z = bed_height + headboard_height - horizontal_strip_height / 2

            fig.add_trace(go.Mesh3d(
                x=[first_strip_x, horizontal_strip_end, horizontal_strip_end, first_strip_x,
                   first_strip_x, horizontal_strip_end, horizontal_strip_end, first_strip_x],
                y=[strip_y_start, strip_y_start, total_room_depth, total_room_depth, strip_y_start, strip_y_start, total_room_depth, total_room_depth],
                z=[horizontal_strip_z, horizontal_strip_z, horizontal_strip_z, horizontal_strip_z,
                   horizontal_strip_z + horizontal_strip_height, horizontal_strip_z + horizontal_strip_height,
                   horizontal_strip_z + horizontal_strip_height, horizontal_strip_z + horizontal_strip_height],
                i=[0, 0, 0, 0, 4, 4, 6, 6, 4, 5, 2, 2],
                j=[1, 2, 4, 5, 5, 6, 7, 2, 0, 1, 3, 6],
                k=[2, 3, 5, 1, 6, 7, 4, 6, 5, 6, 6, 7],
                color='#696969',  # Dark grey
                opacity=0.9,
                name='Horizontal Strip',
                showlegend=True,
                hoverinfo='skip'
            ))

        # Lights (on the wall, not nightstands)
        lights = positions["lights"]
        light_z = bed_height + 12  # On wall, lower than horizontal strip
        light_y = total_room_depth - 1  # On the wall surface
        light_radius = 3

        # Create sphere coordinates
        u = np.linspace(0, 2 * np.pi, 20)
        v = np.linspace(0, np.pi, 20)
        x_sphere = light_radius * np.outer(np.cos(u), np.sin(v))
        y_sphere = light_radius * np.outer(np.sin(u), np.sin(v))
        z_sphere = light_radius * np.outer(np.ones(np.size(u)), np.cos(v))

        # Left light
        fig.add_trace(go.Surface(
            x=x_sphere + lights["left"],
            y=y_sphere + light_y,
            z=z_sphere + light_z,
            colorscale=[[0, '#ffd700'], [1, '#ffd700']],
            showscale=False,
            name='Lights',
            showlegend=True,
            hoverinfo='skip',
            opacity=0.9
        ))

        # Right light
        fig.add_trace(go.Surface(
            x=x_sphere + lights["right"],
            y=y_sphere + light_y,
            z=z_sphere + light_z,
            colorscale=[[0, '#ffd700'], [1, '#ffd700']],
            showscale=False,
            showlegend=False,
            hoverinfo='skip',
            opacity=0.9
        ))

        # Add gap measurements as 3D annotations
        annotation_z = strip_z_end + 5  # Above the strips
        for idx, strip in enumerate(strips):
            strip_x = strip["x"]
            strip_width = strip["width"]

            # Gap after this strip
            if idx < len(strips) - 1:
                next_strip = strips[idx + 1]
                gap_start = strip_x + strip_width
                gap_end = next_strip["x"]
                gap_size = gap_end - gap_start
                gap_center_x = (gap_start + gap_end) / 2

                fig.add_trace(go.Scatter3d(
                    x=[gap_center_x],
                    y=[total_room_depth],
                    z=[annotation_z],
                    mode='text',
                    text=[f'{gap_size:.1f}"'],
                    textfont=dict(size=10, color='#9c27b0'),
                    showlegend=False,
                    hoverinfo='skip'
                ))

        # Layout configuration
        mode_desc = {
            LayoutMode.EVEN_GAPS: "Even Gaps",
            LayoutMode.START_LEFT: "Start Left",
            LayoutMode.START_RIGHT: "Start Right",
            LayoutMode.VARIABLE_GAPS: "Variable Gaps"
        }.get(self.layout_mode, "Unknown")

        fig.update_layout(
            title=f'3D Room Layout - {mode_desc} Mode<br>Room: {room_width:.1f}" × {total_room_depth:.1f}" | Bed: {bed_width:.1f}" × {bed_depth:.1f}"',
            scene=dict(
                xaxis=dict(title='Width (inches)', backgroundcolor='rgb(230, 230,230)', gridcolor='white', showbackground=True),
                yaxis=dict(title='Depth (inches)', backgroundcolor='rgb(230, 230,230)', gridcolor='white', showbackground=True),
                zaxis=dict(title='Height (inches)', backgroundcolor='rgb(230, 230,230)', gridcolor='white', showbackground=True),
                camera=dict(
                    eye=dict(x=1.5, y=-1.5, z=0.8),
                    center=dict(x=0, y=0, z=0),
                    up=dict(x=0, y=0, z=1)
                ),
                aspectmode='data'
            ),
            showlegend=True,
            legend=dict(x=0.7, y=0.9),
            margin=dict(l=0, r=0, b=0, t=40),
            height=700,
            uirevision='constant'  # Preserve camera angle when data changes
        )

        return fig

    def show(self):
        """Display the visualizer."""
        # Try to maximize window
        manager = plt.get_current_fig_manager()
        try:
            manager.full_screen_toggle()
        except:
            pass

        plt.show()


if __name__ == "__main__":
    visualizer = RoomLayoutVisualizer()
    visualizer.show()
