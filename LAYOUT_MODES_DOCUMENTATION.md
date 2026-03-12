# Room Visualizer - Complete Documentation

This document explains the entire Room Visualizer system architecture, layout modes, rendering, and implementation details.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Key Concepts & Calculations](#key-concepts--calculations)
4. [Layout Modes](#layout-modes)
5. [Rendering System](#rendering-system)
6. [Streamlit Integration](#streamlit-integration)
7. [Common Pitfalls](#common-pitfalls)
8. [Testing & Debugging](#testing--debugging)

---

## System Overview

The Room Visualizer is an interactive bedroom layout planner that helps visualize headboard strips and lighting placement. It supports:

- **3 Layout Modes**: Start Left, Start Right, Variable Gaps
- **2 Rendering Modes**: 2D (matplotlib bird's-eye view) and 3D (plotly interactive)
- **Live Updates**: All sliders update visualization in real-time
- **Light Centering**: Automatically centers lights in gaps based on nightstand positions

**Tech Stack**:
- Backend: `room_layout_visualizer.py` (Python with matplotlib & plotly)
- Frontend: `app.py` (Streamlit web wrapper)
- Deployment: Streamlit Cloud (auto-deploys on git push)

---

## Architecture

### File Structure

```
room-visualizer/
├── room_layout_visualizer.py    # Core visualization logic
├── app.py                        # Streamlit web interface
├── requirements.txt              # Python dependencies
├── README.md                     # User-facing documentation
├── LAYOUT_MODES_DOCUMENTATION.md # This file
└── .gitignore                    # Git ignore rules
```

### Data Flow

```
User adjusts slider in Streamlit
    ↓
app.py updates config dictionary
    ↓
RoomLayoutVisualizer instance created
    ↓
_calculate_positions() called
    ↓
Mode-specific calculation (_calculate_start_left, etc.)
    ↓
Returns strip positions dict
    ↓
Rendering: draw_layout() for 2D OR create_3d_layout() for 3D
    ↓
Display to user via st.pyplot() or st.plotly_chart()
```

### Key Classes & Methods

**`RoomLayoutVisualizer`** (room_layout_visualizer.py):
- `__init__()`: Initialize config, create matplotlib figure/sliders
- `_calculate_positions()`: Main entry point for position calculations
- `_calculate_start_left()`: Start Left mode logic
- `_calculate_start_right()`: Start Right mode logic
- `_calculate_variable_gaps()`: Variable Gaps mode logic
- `draw_layout()`: 2D matplotlib rendering
- `create_3d_layout()`: 3D plotly rendering

---

## Key Concepts & Calculations

### Room Geometry

All measurements in **inches**:

```
                    room_width (default: 134.5")
        ┌────────────────────────────────────────────┐
        │                                            │
wall────┤  [NS]    [======= BED =======]    [NS]   │
gap     │   24"            bed_width          24"   │
        │                                            │
        └────────────────────────────────────────────┘
        0                                         134.5

NS = Nightstand
bed_depth (default: 80") + 48" foot space = 128" total room depth
```

### Constraint System

**The bed width is DERIVED, not configured directly**:

```python
# Right light MUST be centered on right nightstand at a fixed position
right_light_x = config["right_light_from_left_wall"]  # 103" (user input)

# Bed width calculated from this constraint:
bed_width = right_light_x - wall_gap - nightstand_width - (nightstand_width / 2)
```

**Example** (wall_gap=0, nightstand=24", right_light=103"):
```
bed_width = 103 - 0 - 24 - 12 = 67"
```

### Light Positions

**Always centered on nightstands** (not configurable):

```python
# Left light
left_light_x = wall_gap + nightstand_width / 2
# Default: 0 + 24/2 = 12"

# Right light
right_light_x = config["right_light_from_left_wall"]
# Default: 103" (this drives bed width calculation)
```

### Gap Centering Formula

To center a light in a gap between two strips:

```
Pattern: |Strip|------Gap------|Strip|
          a      b      c      d

For light centered at position L:
- Gap runs from b to d
- Center of gap: c = (b + d) / 2
- We want c = L

If strip width = w:
- b = a + w
- d = b + gap_width = a + w + gap_width
- c = (b + d) / 2 = ((a+w) + (a+w+gap_width)) / 2
- c = a + w + gap_width/2

Set c = L:
a + w + gap_width/2 = L
gap_width = 2 * (L - a - w)

If first strip at a=0:
gap_width = 2 * (L - w)
```

**This is the Start Left formula**: `gap = 2 * (left_light_x - strip_width)`

---

## Layout Modes

### Start Left Mode

**Pattern**: `|S|--gap--|S|--gap--|S|--gap--|S|... [leftover space]`

**Algorithm**:
```python
def _calculate_start_left():
    # 1. Calculate gap to center left light
    gap = 2 * (left_light_x - strip_width)

    # 2. Start at x=0, add strips until room runs out
    current_x = 0
    while current_x + strip_width <= room_width:
        add_strip(current_x)
        current_x += strip_width + gap

    # 3. Leftover space remains at right edge
```

**Key Properties**:
- First strip flush at left wall (x=0)
- Constant gap size throughout
- Left light perfectly centered in first gap
- Leftover space at right edge
- **No limit on number of strips** (continues until room runs out)

**Visual Example** (Room: 134.5", Strip: 4.5", Left Light: 12"):
```
Gap = 2*(12-4.5) = 15"

|████|------------15"------------|████|------------15"------------|████|... [leftover]
 0-4.5                          19.5-24
      💡 12"
   (centered)
```

---

### Start Right Mode

**Pattern**: `[leftover space] ...|S|--gap--|S|--gap--|S|`

**Algorithm**:
```python
def _calculate_start_right():
    # 1. Calculate gap to center right light in SECOND gap from right
    gap = (room_width - 2*strip_width - right_light_x) / 1.5

    # 2. Build from right to left
    current_x = room_width - strip_width  # Last strip at right wall
    while current_x >= 0:
        strips.insert(0, current_x)  # Insert at beginning
        current_x -= (strip_width + gap)

    # 3. Leftover space at left edge
```

**Why 1.5 in the formula?**

Pattern from right to left:
```
... Strip → Gap → Strip → Gap (RIGHT LIGHT HERE) → Strip (at wall)
    pos-2   pos-1  pos-0
```

Working backwards from right wall:
- Last strip: `room_width - strip_width` to `room_width`
- Gap 1: `room_width - strip_width - gap` to `room_width - strip_width`
- Strip 2: `room_width - 2*strip_width - gap` to `room_width - strip_width - gap`
- Gap 2 (light centered here): `room_width - 2*strip_width - 2*gap` to `room_width - 2*strip_width - gap`

Center of Gap 2:
```
center = (start + end) / 2
center = ((room_width - 2*strip_width - 2*gap) + (room_width - 2*strip_width - gap)) / 2
center = room_width - 2*strip_width - 1.5*gap
```

Set center = right_light_x:
```
room_width - 2*strip_width - 1.5*gap = right_light_x
1.5*gap = room_width - 2*strip_width - right_light_x
gap = (room_width - 2*strip_width - right_light_x) / 1.5
```

**Visual Example** (Room: 134.5", Strip: 4.5", Right Light: 103"):
```
Gap = (134.5 - 9 - 103) / 1.5 = 15"

[leftover] ...|████|------15"------|████|------15"------|████|
                                  91-95.5            110.5-115  130-134.5
                                            💡 103"
                                         (in 2nd gap)
```

---

### Variable Gaps Mode

**Pattern**: `|S|--outer--|S|--inner--|S|--inner--|S|--outer--|S|--outer--|S|`

**Algorithm**:
```python
def _calculate_variable_gaps():
    # 1. Calculate outer gap (same as Start Left)
    outer_gap = 2 * (left_light_x - strip_width)

    # 2. LEFT SIDE: Strip at 0, outer_gap, first inner strip
    add_strip(0)
    inner_zone_start = strip_width + outer_gap

    # 3. CALCULATE INNER ZONE BOUNDARIES
    # Find where gap containing right light starts
    right_light_gap_start = right_light_x - outer_gap/2
    last_inner_strip_x = right_light_gap_start - strip_width

    # 4. INNER ZONE: Fill space with variable gaps
    inner_zone_width = last_inner_strip_x - inner_zone_start
    inner_gap = (inner_zone_width - num_inner_gaps*strip_width) / num_inner_gaps

    current_x = inner_zone_start
    for i in range(num_inner_gaps + 1):
        add_strip(current_x)
        current_x += strip_width + inner_gap

    # 5. RIGHT SIDE: Continue outer_gap pattern to wall
    current_x = last_inner_strip_x + strip_width + outer_gap
    while current_x + strip_width <= room_width:
        add_strip(current_x)
        current_x += strip_width + outer_gap
```

**Critical Details**:

1. **Outer gap uses Start Left formula** - ensures left light is centered
2. **Strip after first outer_gap IS the first inner strip** - don't add it twice!
3. **Right side pattern continues to wall** - doesn't stop after right light
4. **Only 2 gap sizes**: outer_gap (15") and inner_gap (calculated)

**Visual Example** (Room: 134.5", Strip: 4.5", num_inner_gaps: 3):
```
Outer gap = 2*(12-4.5) = 15"

LEFT     INNER ZONE              RIGHT SIDE (continues)
|█|--15--|█|--16.3--|█|--16.3--|█|--15--|█|--15--|█|
 0      19.5       38          91      110.5     130
    💡12"                          💡103"
```

**Common Bug**: Don't create separate "left outer strip" and "first inner strip" - they're the same strip at position `strip_width + outer_gap`.

---

## Rendering System

### 2D Rendering (Matplotlib)

**File**: `room_layout_visualizer.py` → `draw_layout()`

**View**: Bird's-eye (top-down) view

**Components**:
1. **Room**: Floor rectangle, wall lines
2. **Furniture**: Bed (blue), nightstands (gold)
3. **Strips**: Red rectangles at `bed_depth + 5` y-position
4. **Lights**: Gold circles on back wall
5. **Annotations**: Gap measurements, dimensions

**Coordinate System**:
- X-axis: Width (left to right, 0 to room_width)
- Y-axis: Depth (front to back, 0 to bed_depth + 48)
- Origin: Front-left corner

**Key Code**:
```python
def draw_layout(self):
    self.ax.clear()
    positions = self._calculate_positions()

    self._draw_room(positions)
    self._draw_nightstands(positions)
    self._draw_bed(positions)
    self._draw_strips(positions)
    self._draw_lights(positions)
    self._draw_dimensions(positions)

    plt.draw()
```

---

### 3D Rendering (Plotly)

**File**: `room_layout_visualizer.py` → `create_3d_layout()`

**View**: Interactive 3D perspective

**Components**:
1. **Floor**: Mesh3d rectangle at z=0
2. **Walls**: Mesh3d surfaces (left, right, back)
3. **Bed**: 3D box (blue, height=24")
4. **Nightstands**: 3D boxes (gold, height=24")
5. **Vertical Strips**: Grey 3D boxes (height=24", starts at bed_height)
6. **Horizontal Strip**: Dark grey rail across all vertical strips
7. **Lights**: Spheres on back wall (z=bed_height+12")
8. **Gap Labels**: 3D text annotations above strips

**Coordinate System**:
- X-axis: Width (0 to room_width)
- Y-axis: Depth (0 to bed_depth + 48)
- Z-axis: Height (0 to wall_height=100")

**Critical Heights**:
```python
bed_height = 24"              # Top of mattress
strip_z_start = 24"           # Strips start at bed height
strip_z_end = 24 + 24 = 48"   # Strips are 24" tall
horizontal_strip_z = 48"      # Rail at top of strips
light_z = 24 + 12 = 36"       # Lights at midpoint of strips
```

**Horizontal Strip**:
```python
# CRITICAL: Extends from first strip to RIGHT WALL EDGE
first_strip_x = strips[0]["x"]
horizontal_strip_end = room_width  # NOT last strip position!
```

**Camera Persistence**:
```python
fig.update_layout(
    uirevision='constant'  # Preserve camera angle across updates
)
```

---

## Streamlit Integration

### File: `app.py`

**Architecture**:
```python
# 1. Sidebar controls (inputs)
with st.sidebar:
    render_mode = st.radio("View", ["2D", "3D"], index=1)
    layout_mode = st.radio("Strip Layout", ["Start Left", ...])
    # Mode-specific sliders
    # Room setting sliders

# 2. Create config dict from slider values
config = {
    "room_width": room_width,
    "strip_width": strip_width,
    ...
}

# 3. Create visualizer instance (without showing matplotlib GUI)
viz = RoomLayoutVisualizer.__new__(RoomLayoutVisualizer)
viz.config = config
viz.layout_mode = layout_mode_map[layout_mode_name]
viz._update_bed_width()

# 4. Render based on mode
if render_mode == "3D":
    fig_3d = viz.create_3d_layout()
    st.plotly_chart(fig_3d, use_container_width=True, key="room_3d_viz")
else:
    fig, ax = plt.subplots(figsize=(18, 12))
    viz.ax = ax
    viz.fig = fig
    viz.draw_layout()
    st.pyplot(fig)
```

**Critical Details**:

1. **Use `__new__()` instead of `__init__()`**: Avoid creating matplotlib GUI
2. **Set `key="room_3d_viz"`**: Preserves camera angle across reruns
3. **Conditional sliders**: Only show relevant sliders per mode
4. **Default to 3D**: `index=1` in radio button

**Camera Angle Preservation**:
- Streamlit reruns app on every slider change
- Without `key`, plotly chart is recreated (resets camera)
- With `key="room_3d_viz"` + `uirevision='constant'`, camera angle persists

---

## Common Pitfalls

### 1. Start Right: Centering in First Gap Instead of Second

❌ **Wrong**:
```python
gap = 2 * (room_width - strip_width - right_light_x)  # Centers in 1st gap
```

✅ **Correct**:
```python
gap = (room_width - 2*strip_width - right_light_x) / 1.5  # Centers in 2nd gap
```

### 2. Variable Gaps: Duplicate Strips

❌ **Wrong**:
```python
# Left outer
add_strip(0)
add_strip(strip_width + outer_gap)  # ← This is also first inner strip!

# Inner zone
current_x = strip_width + outer_gap
add_strip(current_x)  # ← Duplicate!
```

✅ **Correct**:
```python
# Left outer
add_strip(0)

# Inner zone (no duplicate)
current_x = strip_width + outer_gap  # First inner strip
add_strip(current_x)
```

### 3. Variable Gaps: Stopping After Right Light

❌ **Wrong**:
```python
# Stop after centering right light
if strip_contains_right_light:
    break
```

✅ **Correct**:
```python
# Continue to wall edge
while current_x + strip_width <= room_width:
    add_strip(current_x)
    current_x += strip_width + outer_gap
```

### 4. Horizontal Strip Not Extending to Wall

❌ **Wrong**:
```python
last_strip_x_end = strips[-1]["x"] + strips[-1]["width"]
horizontal_strip_width = last_strip_x_end - first_strip_x
```

✅ **Correct**:
```python
horizontal_strip_end = room_width  # Extend to wall, not last strip
horizontal_strip_width = horizontal_strip_end - first_strip_x
```

### 5. Camera Angle Resetting

❌ **Wrong**:
```python
st.plotly_chart(fig_3d)  # No key
```

✅ **Correct**:
```python
st.plotly_chart(fig_3d, key="room_3d_viz")  # Preserves state
```

### 6. Using `for range(num_strips)` Instead of `while`

❌ **Wrong**:
```python
for i in range(num_strips):  # Limited by slider
    add_strip(current_x)
    current_x += strip_width + gap
```

✅ **Correct**:
```python
while current_x + strip_width <= room_width:  # Fill to edge
    add_strip(current_x)
    current_x += strip_width + gap
```

---

## Testing & Debugging

### Visual Verification Checklist

**Start Left Mode**:
- [ ] First strip flush at x=0
- [ ] Left light at 12" centered in first gap (4.5" to 19.5")
- [ ] Constant gap size throughout
- [ ] Leftover space at right edge

**Start Right Mode**:
- [ ] Last strip flush at x=room_width
- [ ] Right light at 103" centered in SECOND gap from right
- [ ] Constant gap size throughout
- [ ] Leftover space at left edge

**Variable Gaps Mode**:
- [ ] First strip flush at x=0
- [ ] Left light at 12" centered in first 15" gap
- [ ] NO duplicate strips (check for 0.0" gaps)
- [ ] Inner gaps all the same size
- [ ] Right side has repeating 15" gaps to wall edge
- [ ] Right light at 103" centered in one of the 15" gaps
- [ ] Only 2 different gap sizes total (outer=15", inner=calculated)

### Debug Output

Add logging to trace calculations:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

def _calculate_variable_gaps(self, ...):
    logging.debug(f"outer_gap = {outer_gap}")
    logging.debug(f"inner_zone_start = {inner_zone_start}")
    logging.debug(f"last_inner_strip_x = {last_inner_strip_x}")
    logging.debug(f"inner_gap = {inner_gap}")

    for i, strip in enumerate(strips):
        logging.debug(f"Strip {i}: x={strip['x']:.2f}")
```

### Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Lights not centered | Wrong gap formula | Use `2*(light_x - strip_width)` |
| Duplicate strips with 0" gaps | Adding same strip twice | Remove duplicate adds |
| Camera resets on slider change | No Streamlit key | Add `key="room_3d_viz"` |
| Horizontal strip too short | Ending at last strip | Extend to `room_width` |
| Leftover space when shouldn't be | `for range(num_strips)` | Use `while` loop |
| Variable gaps has 3+ gap sizes | Wrong outer_gap formula | Use Start Left formula |

---

## Summary of Key Formulas

```python
# Light positions (always centered on nightstands)
left_light_x = wall_gap + nightstand_width / 2
right_light_x = config["right_light_from_left_wall"]

# Bed width (derived from right light constraint)
bed_width = right_light_x - wall_gap - nightstand_width - (nightstand_width / 2)

# Gap formulas by mode
start_left_gap = 2 * (left_light_x - strip_width)
start_right_gap = (room_width - 2*strip_width - right_light_x) / 1.5
variable_outer_gap = 2 * (left_light_x - strip_width)  # Same as Start Left!
variable_inner_gap = (inner_zone_width - num_inner_gaps*strip_width) / num_inner_gaps

# 3D heights
bed_height = 24"
strip_z_start = 24"
strip_z_end = 48"  # 24" tall strips
light_z = 36"  # Midpoint of strips
horizontal_strip_z = 48"  # Top of strips
```

---

## Summary Table

| Mode | Left Edge | Gap Calculation | Right Edge | # Gap Sizes |
|------|-----------|-----------------|------------|-------------|
| **Start Left** | Flush (x=0) | `2*(left_light_x - strip_width)` | Leftover | 1 (constant) |
| **Start Right** | Leftover | `(room_width - 2*strip - right_light_x)/1.5` | Flush | 1 (constant) |
| **Variable** | Flush (x=0) | Outer: `2*(left_light_x - strip_width)`<br>Inner: Calculated | Outer gaps continue to wall | 2 (outer + inner) |

---

Last Updated: 2026-03-12
