#!/usr/bin/env python3
"""
Streamlit wrapper for room_layout_visualizer.py
Uses the exact same visualization code, just with Streamlit controls instead of matplotlib widgets
"""

import streamlit as st
import matplotlib.pyplot as plt
from room_layout_visualizer import RoomLayoutVisualizer, LayoutMode, INITIAL_CONFIG

# Page config
st.set_page_config(
    page_title="Room Layout Visualizer",
    page_icon="🛏️",
    layout="wide"
)

st.title("🛏️ Room Layout Visualizer")
st.markdown("Interactive headboard strip and lighting planner - all dimensions in inches")

# Sidebar controls
with st.sidebar:
    st.header("Room Settings")

    room_width = st.slider("Room Width (in)", 100.0, 200.0, INITIAL_CONFIG["room_width"], 0.5)
    nightstand_width = st.slider("Nightstand Width (in)", 18.0, 36.0, INITIAL_CONFIG["nightstand_width"], 0.5)
    strip_width = st.slider("Strip Width (in)", 2.0, 10.0, INITIAL_CONFIG["strip_width"], 0.5)
    right_light_pos = st.slider("Right Light from Left Wall (in)", 80.0, 120.0, INITIAL_CONFIG["right_light_from_left_wall"], 0.5)
    wall_gap = st.slider("Wall Gap (in)", 0.0, 40.0, INITIAL_CONFIG["wall_gap"], 0.5)
    num_strips = st.slider("Number of Strips", 5, 30, INITIAL_CONFIG["num_strips"], 1)
    bed_depth = st.slider("Bed Depth (in)", 60.0, 100.0, INITIAL_CONFIG["bed_depth"], 0.5)

    st.header("Advanced Settings (Variable Mode)")
    outer_gap_size = st.slider("Gap Size - Outer (Variable Mode) (in)", 5.0, 30.0, INITIAL_CONFIG["outer_gap_size"], 0.5)
    inner_gap_size = st.slider("Gap Size - Inner (Variable Mode) (in)", 5.0, 30.0, INITIAL_CONFIG["inner_gap_size"], 0.5)
    num_inner_gaps = st.slider("Num Inner Gaps (Variable Mode)", 1, 10, INITIAL_CONFIG["num_inner_gaps"], 1)

    st.header("Layout Mode")
    layout_mode_name = st.radio(
        "Strip Layout",
        ["Even Gaps", "Start Left", "Start Right", "Variable Gaps"]
    )

    st.header("View Mode")
    view_mode_name = st.radio("View", ["Top View", "Side View"])

# Map radio button selections to internal values
layout_mode_map = {
    "Even Gaps": LayoutMode.EVEN_GAPS,
    "Start Left": LayoutMode.START_LEFT,
    "Start Right": LayoutMode.START_RIGHT,
    "Variable Gaps": LayoutMode.VARIABLE_GAPS,
}

# Create visualizer with current config
config = {
    "room_width": room_width,
    "nightstand_width": nightstand_width,
    "strip_width": strip_width,
    "right_light_from_left_wall": right_light_pos,
    "wall_gap": wall_gap,
    "num_strips": num_strips,
    "bed_depth": bed_depth,
    "outer_gap_size": outer_gap_size,
    "inner_gap_size": inner_gap_size,
    "num_inner_gaps": num_inner_gaps,
}

# Create a new visualizer instance without showing it
viz = RoomLayoutVisualizer.__new__(RoomLayoutVisualizer)
viz.config = config
viz.layout_mode = layout_mode_map[layout_mode_name]
viz.view_mode = "top" if view_mode_name == "Top View" else "side"
viz._update_bed_width()

# Create the plot
fig, ax = plt.subplots(figsize=(18, 12))
viz.ax = ax
viz.fig = fig

# Draw using the original visualization code
viz.draw_layout()

# Display in Streamlit
st.pyplot(fig)

# Summary stats
positions = viz._calculate_positions()
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Bed Width", f"{positions['bed']['width']:.1f}\"")
with col2:
    st.metric("Left Light Position", f"{positions['lights']['left']:.1f}\"")
with col3:
    st.metric("Right Light Position", f"{positions['lights']['right']:.1f}\"")
with col4:
    gap_width = positions["strips"].get("gap_width", 0)
    st.metric("Gap Width", f"{gap_width:.1f}\"")
