# DFE_01 – notes for the next tutorship

## Findings to discuss

### 1. Gravity is ~1000× too weak in the provided environment
- `DFE_01_env.json` sets `"gravity": [0, -9.81, 0]`, but the scene works in millimetres (`UnitOfMeasureScale: 0.001`).
- Measured in test T2: a 130 mm free fall took ~4.5 s (real: 0.16 s), i.e. effective g ≈ 9.81 mm/s².
- Effects: falls look like slow motion; belt friction is also ~1000× weaker (friction ∝ normal force ∝ g).
- Proposed fix: `"gravity": [0, -9810, 0]`, to be verified in test T3.
- **Question for tutor:** is this intended, and may we correct it in our env file?

### 2. Timeline-moved objects do not carry physics parts (test T1)
- A tote moved by timeline `moveAdditive` moved correctly, but the parts inside stayed in place and fell; walls passed through them.
- Cause: the motion is applied as position updates (teleport per frame), so the physics engine sees zero velocity.
- **Question for tutor:** what is the accepted way to model a mobile carrier (AMR) transporting parts? Options under consideration:
  a. drive the carrier through a StateChart (`moveTo`) instead of the timeline (to be tested, T4);
  b. lock the tote to the carrier during travel (`attach`), the same mechanism VEB.js already uses for the gripper;
  c. give the carrier deck a surface velocity matching the travel speed.

### 3. Robot gripper grasps by attachment (test T2)
- Picking works for all parts, slippery ones included (μ = 0.1): parts are attached to the gripper when the fingers close.
- The default `place` state releases the part 130 mm above the belt, 200 mm from the pick point.
- In DFE_01 the robot's pick point (x ≈ −941) does not reach B1 (x ≈ 0).

### 4. Layout facts
- The Grid is a vertical wall (1060 × 660 × 30 mm, top at y ≈ 1070) standing 50 mm from the Box on the conveyor side.
- No physical floor: anything that falls off a device falls forever.
- The 10 parts lie loose on B1 at a 200 mm pitch, with no fixture; part_08 and part_09 have μ ≈ 0.1.

## Next steps
1. **T3 – gravity + sensor:** test env with g = −9810: falls, belt transport, a chute, and whether the light-barrier sensor fires on its own.
2. **T4 – AMR retest:** with correct gravity, compare (a) StateChart `moveTo` driven cart, (b) tote attached to the cart, (c) deck surface velocity. Pick the most physically defensible option.
3. **Decide the concept:** AMR + tote vs conveyor + robot, using the T1–T4 evidence and the course criteria (realism, safety, placement, efficiency).
4. **Build the minimum working version** with 2–3 parts, then scale to all 10.
5. Deliverables: video, report, Dec 1 presentation.

Test details and data: [`tests/README.md`](../tests/README.md)

## Update after T4 (2026-11-02)
- Gravity −9810 tested: falls accelerate but are capped at ~200 mm/s (apparent engine speed limit); parts sank into thin tote floors. **Question:** is there a supported way to raise the speed cap, or should we keep −9.81?
- AMR: StateChart `moveTo`, timeline + `attach`, and deck `surfaceVelocity` all failed to carry loose parts. **Question:** how should a mobile carrier be modelled? Our next candidate is a mobile manipulator (gripper on the moving base), since gripper attachment is the only mechanism that carried parts.

## Update after T7–T10 (2026-11-03)
- **AMR solution found (T10):** an AMR deck moved by `moveAdditive` *plus* a deck `surfaceVelocity` equal to its travel speed carries a dynamic tote with loose parts (incl. μ = 0.1). Tested at 125 mm/s: tote follows within 0.2% forward, ~10% sideways.
- Engine limits found: dynamic bodies are capped at ~200 mm/s; timeline events must be on a 100 ms grid.
- Gripper internals (T8): custom JawGripper jaws must be single meshes loaded from the clamp body's own .glb.
- **Questions:** (1) Is the deck-surface-velocity technique acceptable as "physically consistent" transport? (2) Is the ~200 mm/s cap configurable? (3) Can we correct gravity (−9.81 → −9810)?

## Decision (2026-11-03): Option 1
Fixed Cartesian robot loads parts into totes ("packaging department"); an AMR carries the totes to the Box and places them inside (4 totes × ≤3 parts in a 2×2 grid). T9: custom tote gripper works, but contents of a lifted tote are left behind → tote must be transferred into the Box by rolling/sliding (T11). **Question for tutor:** are parts inside totes inside the Box acceptable as "parts placed inside the destination box"?
