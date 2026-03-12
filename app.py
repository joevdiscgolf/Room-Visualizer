import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Page config
st.set_page_config(
    page_title="Room Layout Visualizer",
    page_icon="🛏️",
    layout="wide"
)

st.title("🛏️ Room Layout Visualizer")
st.markdown("Interactive headboard strip and lighting planner - all dimensions in inches")

# Sidebar for controls
with st.sidebar:
    st.header("Room Settings")

    room_width = st.slider("Room Width (in)", 100.0, 200.0, 134.5, 0.5)
    nightstand_width = st.slider("Nightstand Width (in)", 18.0, 36.0, 24.0, 0.5)
    strip_width = st.slider("Strip Width (in)", 2.0, 10.0, 4.5, 0.5)
    right_light_pos = st.slider("Right Light from Left Wall (in)", 80.0, 120.0, 103.0, 0.5)
    wall_gap = st.slider("Wall Gap (in)", 0.0, 40.0, 0.0, 0.5)
    num_strips = st.slider("Number of Strips", 5, 30, 15, 1)
    bed_depth = st.slider("Bed Depth (in)", 60.0, 100.0, 80.0, 0.5)

    st.header("Layout Mode")
    layout_mode = st.radio(
        "Strip Layout",
        ["Even Gaps (whole wall)", "Start Left (center left light)", "Start Right (center right light)"]
    )

# Calculate bed width from constraint
bed_width = right_light_pos - wall_gap - nightstand_width - (nightstand_width / 2)

# Calculate positions
def calculate_positions():
    bed_x = wall_gap + nightstand_width
    right_nightstand_x = bed_x + bed_width

    left_light_x = wall_gap + nightstand_width / 2
    right_light_x = right_nightstand_x + nightstand_width / 2

    if layout_mode == "Even Gaps (whole wall)":
        total_strip_width = num_strips * strip_width
        total_gap_width = room_width - total_strip_width
        num_gaps = num_strips + 1
        gap_width = total_gap_width / num_gaps if num_gaps > 0 else 0

        strips = []
        current_x = gap_width
        for i in range(num_strips):
            strips.append({"x": current_x, "width": strip_width, "gap_before": gap_width})
            current_x += strip_width + gap_width

    elif layout_mode == "Start Left (center left light)":
        gap_width = (left_light_x - strip_width) / 1.5
        strips = []
        current_x = gap_width
        i = 0
        while i < num_strips and current_x + strip_width <= room_width:
            strips.append({"x": current_x, "width": strip_width, "gap_before": gap_width})
            current_x += strip_width + gap_width
            i += 1

    else:  # Start Right
        gap_width = (room_width - right_light_x - strip_width) / 1.5
        strips = []
        current_x = room_width - gap_width - strip_width
        i = 0
        while i < num_strips and current_x >= 0:
            strips.insert(0, {"x": current_x, "width": strip_width})
            current_x -= (gap_width + strip_width)
            i += 1

    return {
        "bed_x": bed_x,
        "bed_width": bed_width,
        "left_light_x": left_light_x,
        "right_light_x": right_light_x,
        "strips": strips,
        "gap_width": gap_width if strips else 0,
    }

positions = calculate_positions()

# Create the plot
fig, ax = plt.subplots(figsize=(20, 11))

# Draw room floor
floor = patches.Rectangle((0, 0), room_width, bed_depth + 20, linewidth=0, facecolor='#f5f5dc', alpha=0.3, zorder=0)
ax.add_patch(floor)

# Draw walls
ax.axvline(x=0, color='#654321', linewidth=4, zorder=1)
ax.axvline(x=room_width, color='#654321', linewidth=4, zorder=1)
ax.axhline(y=bed_depth + 20, color='#654321', linewidth=4, zorder=1)

# Wall labels
ax.text(-5, bed_depth + 10, 'Left\nWall', ha='center', va='center', fontsize=10, fontweight='bold', color='#654321')
ax.text(room_width + 5, bed_depth + 10, 'Right\nWall', ha='center', va='center', fontsize=10, fontweight='bold', color='#654321')
ax.text(room_width / 2, bed_depth + 25, 'Back Wall (Headboard)', ha='center', va='center', fontsize=10, fontweight='bold', color='#654321')

# Draw bed
bed_x = positions["bed_x"]
bed_rect = patches.Rectangle((bed_x, 0), positions["bed_width"], bed_depth, linewidth=3, edgecolor='#2c3e50', facecolor='#3498db', alpha=0.7, zorder=3)
ax.add_patch(bed_rect)
ax.text(bed_x + positions["bed_width"] / 2, bed_depth / 2, f'BED\n{positions["bed_width"]:.1f}" × {bed_depth:.1f}"', ha='center', va='center', fontsize=11, fontweight='bold', color='white')

# Draw nightstands
ns_depth = 20
left_ns_x = wall_gap
right_ns_x = bed_x + positions["bed_width"]

for ns_x, label in [(left_ns_x, 'Left\nNightstand'), (right_ns_x, 'Right\nNightstand')]:
    ns_rect = patches.Rectangle((ns_x, (bed_depth / 2) - (ns_depth / 2)), nightstand_width, ns_depth, linewidth=2, edgecolor='#654321', facecolor='#daa520', zorder=3)
    ax.add_patch(ns_rect)
    ax.text(ns_x + nightstand_width / 2, bed_depth / 2, label, ha='center', va='center', fontsize=9, fontweight='bold', color='white')

# Draw headboard strips
strip_y = bed_depth + 5
strip_height = 12

for idx, strip in enumerate(positions["strips"]):
    rect_strip = patches.Rectangle((strip["x"], strip_y), strip["width"], strip_height, linewidth=2, edgecolor='#8b0000', facecolor='#cd5c5c', zorder=5)
    ax.add_patch(rect_strip)
    ax.text(strip["x"] + strip["width"] / 2, strip_y + strip_height / 2, f'{idx + 1}\n{strip["width"]}\"', ha='center', va='center', fontsize=8, fontweight='bold', color='white')

# Draw lights
light_y = bed_depth / 2
for light_x in [positions["left_light_x"], positions["right_light_x"]]:
    glow = patches.Circle((light_x, light_y), 5, color='#ffd700', alpha=0.2, zorder=6)
    ax.add_patch(glow)
    circle = patches.Circle((light_x, light_y), 3, color='#ffd700', ec='#ff8c00', linewidth=2.5, zorder=7)
    ax.add_patch(circle)
    ax.plot([light_x, light_x], [light_y, bed_depth + 5], '#ffa500', linestyle='--', linewidth=2, alpha=0.6, zorder=5)
    ax.text(light_x, light_y - 8, f'{light_x:.1f}"', ha='center', fontsize=9, color='#ff8c00', fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='#ff8c00'))

# Dimensions
ax.annotate('', xy=(room_width, bed_depth + 35), xytext=(0, bed_depth + 35), arrowprops=dict(arrowstyle='<->', color='black', lw=2))
ax.text(room_width / 2, bed_depth + 38, f'Room Width: {room_width:.1f}"', ha='center', fontsize=11, fontweight='bold', bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.9, edgecolor='black'))

# Set axis properties
ax.set_xlim(-10, room_width + 10)
ax.set_ylim(-20, bed_depth + 50)
ax.set_aspect('equal')
ax.set_xlabel('Distance from Left Wall (inches)', fontsize=12, fontweight='bold')
ax.set_ylabel('Depth from Wall (inches)', fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3, linestyle='--')

# Title
num_strips_actual = len(positions["strips"])
total_strip_width = num_strips_actual * strip_width
num_gaps_over_bed = num_strips_actual + 1
title_text = f'Room: {room_width:.1f}" | Bed: {positions["bed_width"]:.1f}" × {bed_depth:.1f}" | {num_strips_actual} Strips ({strip_width}"ea = {total_strip_width:.1f}") | {num_gaps_over_bed} Gaps over bed'
ax.set_title(title_text, fontsize=11, fontweight='bold', pad=15)

# Display
st.pyplot(fig)

# Summary stats
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Bed Width", f"{positions['bed_width']:.1f}\"")
with col2:
    st.metric("Left Light Position", f"{positions['left_light_x']:.1f}\"")
with col3:
    st.metric("Right Light Position", f"{positions['right_light_x']:.1f}\"")
with col4:
    st.metric("Gap Between Strips", f"{positions['gap_width']:.1f}\"")

# Instructions
with st.expander("ℹ️ How to Use"):
    st.markdown("""
    **Adjust the sliders on the left to customize your room layout:**

    - **Room Width**: Total width of your wall
    - **Nightstand Width**: Width of each nightstand
    - **Strip Width**: Width of each headboard strip
    - **Right Light Position**: Distance from left wall to right light (determines bed width)
    - **Wall Gap**: Space between wall and furniture
    - **Number of Strips**: Total strips across the wall
    - **Bed Depth**: How deep your bed is (front to back)

    **Layout Modes:**
    - **Even Gaps**: Distributes strips evenly across entire wall
    - **Start Left**: Centers first gap on left light
    - **Start Right**: Centers first gap on right light

    All measurements are in inches.
    """)
