# Room Visualizer - Layout Modes Documentation

This document explains exactly how each layout mode calculates strip positions and gap sizes.

## Key Concepts

- **Strip Width**: Width of each vertical headboard strip (default: 4.5")
- **Room Width**: Total width of the room (default: 134.5")
- **Nightstand Width**: Width of each nightstand (default: 24")
- **Left Light**: Centered on left nightstand at `wall_gap + nightstand_width / 2` (default: 12")
- **Right Light**: Centered on right nightstand at `right_light_from_left_wall` (default: 103")

## Layout Modes

### Start Left Mode

**Pattern**: `|S|--gap--|S|--gap--|S|--gap--|S|... [leftover space]`

**Logic**:
1. First strip starts flush at x=0
2. Gap size auto-calculated to center the left light in the first gap
3. Formula: `gap = 2 * (left_light_x - strip_width)`
   - Example: `gap = 2 * (12 - 4.5) = 15"`
4. Continues with same gap size until strips would exceed room width
5. Leftover space remains at the right edge

**Visual Example** (Room: 134.5", Nightstand: 24", Strip: 4.5"):
```
|████|------------15"------------|████|------------15"------------|████|... [leftover]
 0-4.5                          19.5-24

      💡 12"
   LEFT LIGHT
(centered in 15" gap)
```

---

### Start Right Mode

**Pattern**: `[leftover space] ...|S|--gap--|S|--gap--|S|`

**Logic**:
1. Last strip ends flush at room edge (x=room_width)
2. Gap size auto-calculated to center the right light in the **SECOND** gap from the right
3. Formula: `gap = (room_width - 2 * strip_width - right_light_x) / 1.5`
   - Why 1.5? Pattern from right: Last strip → Gap 1 → Strip → **Gap 2 (light here)** → more strips
   - Light at `room_width - 2*strip_width - 1.5*gap`
4. Builds from right to left, then reverses list for display
5. Leftover space remains at the left edge

**Visual Example** (Room: 134.5", Right Light: 103", Strip: 4.5"):
```
                                          Formula: gap = (134.5 - 9 - 103) / 1.5 = 15"

[leftover] ...|████|------------15"------------|████|------------15"------------|████|
                                              91-95.5                         110.5-115  130-134.5

                                                           💡 103"
                                                        RIGHT LIGHT
                                                    (centered in 2nd gap)
```

---

### Variable Gaps Mode

**Pattern**: `|S|--15"--|S|--inner--|S|--inner--|S|--15"--|S|--15"--|S|`

**Logic**:
1. **Outer Gap Calculation** (same as Start Left):
   - `outer_gap = 2 * (left_light_x - strip_width) = 15"`
   - This gap size centers the left light

2. **Left Outer Structure**:
   - Strip at x=0
   - Gap of 15" (left light centered here)
   - Strip at x=19.5

3. **Inner Zone**:
   - Starts at end of left outer (x=24)
   - Ends where right side pattern begins
   - Contains `num_inner_gaps + 1` strips with variable spacing
   - Inner gap size auto-calculated: `(inner_zone_width - total_strip_width) / num_inner_gaps`

4. **Right Side Pattern**:
   - **CRITICAL**: Continues with 15" gap pattern all the way to the wall
   - One of these gaps is positioned to center the right light
   - Gap containing right light: from `(right_light_x - outer_gap/2)` to `(right_light_x + outer_gap/2)`
   - Continues: Strip, 15" gap, Strip, 15" gap, Strip... to wall edge

**Visual Example** (Room: 134.5", Nightstand: 24", Strip: 4.5", Outer Gap: 15"):
```
LEFT OUTER          INNER ZONE (variable)               RIGHT SIDE (15" gaps continue)
|████|--15"--|████|--------|████|--------|████|--15"--|████|--15"--|████|--15"--|████|
 0-4.5      19.5-24  inner  33-37.5 inner  47-51.5   91-95.5    110.5-115    130-134.5
                     gap            gap
      💡 12"                                               💡 103"
   (centered)                                           (centered in 15" gap)

Breakdown:
- Left outer: 0" to 24" (strip + 15" + strip)
- Inner zone: 24" to 91" (variable gaps based on num_inner_gaps slider)
- Right side: 91" to 134.5" (repeating 15" gap pattern)
  - Strip 91-95.5
  - Gap 95.5-110.5 (15") ← RIGHT LIGHT centered at 103"
  - Strip 110.5-115
  - Gap 115-130 (15")
  - Strip 130-134.5
```

**Key Insight**: The outer gap (15") is used for:
1. Left side: Centering the left light
2. Right side: **Continues as a repeating pattern** all the way to the wall edge
   - One of these 15" gaps naturally centers the right light
   - Pattern doesn't stop after the right light—it continues to the wall

---

## Summary Table

| Mode | Left Edge | Gap Calculation | Right Edge | Key Feature |
|------|-----------|-----------------|------------|-------------|
| **Start Left** | Flush (x=0) | `2*(left_light_x - strip_width)` | Leftover space | Centers left light in first gap |
| **Start Right** | Leftover space | `(room_width - 2*strip - right_light_x)/1.5` | Flush (x=room_width) | Centers right light in **second** gap from right |
| **Variable** | Flush (x=0) | Outer: `2*(left_light_x - strip_width)`<br>Inner: Auto-calculated | 15" gaps continue to wall | Two gap sizes: outer (15") repeated on right side, inner (variable) |

---

## Common Mistakes to Avoid

1. ❌ **Start Right**: Don't center light in first gap from right—use the SECOND gap
2. ❌ **Variable Gaps**: Don't calculate outer gap as `nightstand_width - strip_width`—use Start Left formula
3. ❌ **Variable Gaps**: Don't stop the 15" gap pattern after the right light—continue all the way to the wall
4. ❌ **Variable Gaps**: Don't try to make outer gaps symmetrical by averaging—they ARE symmetrical because the right side uses the same outer_gap value
5. ✅ **Always**: Use the Start Left formula `2*(left_light_x - strip_width)` for outer gaps in Variable mode

---

## Testing Checklist

When verifying each mode works correctly:

- [ ] **Start Left**: Left light perfectly centered in first gap (4.5" to 19.5")
- [ ] **Start Right**: Right light perfectly centered in **second** gap from right
- [ ] **Variable Gaps**:
  - [ ] Left light centered in first 15" gap
  - [ ] Right light centered in one of the 15" gaps on right side
  - [ ] 15" gaps continue all the way to right edge of room
  - [ ] Only 2 different gap sizes total (15" outer, variable inner)
  - [ ] Inner gaps divide remaining space evenly based on slider

---

Last Updated: 2026-03-12
