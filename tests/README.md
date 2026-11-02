# Feasibility tests

Small throw-away scenes used to de-risk design choices **before** building them into the main model `DFE_01`. Each test isolates one question, so a failure points to a single cause.

## T1 – Can a moving carrier transport loose parts reliably? (AMR concept)

**Run:** https://digital-factory.io/vebjs/?inputscene=https://mihamoscow.github.io/DF-DFE01/tests/T1_cart&repoMod3d=https://difactory.github.io/repository/models/PickPlaceCell/

### Why this test
The candidate concept replaces a long floor conveyor with an **AMR (autonomous mobile robot) carrying a tote**, a common solution in highly automated plants because it keeps the floor free and is easy to re-route. In VEB.js the carrier is a kinematic (`MotionType: ANIMATED`) body moved by the timeline, while the parts are dynamic bodies simulated by the Havok physics engine. It is not obvious that dynamic parts will ride stably on a kinematic body that moves, stops and turns. This is the single biggest technical risk of the concept, so it is tested first and in isolation.

The parts of DFE_01 are identical except for friction: most have μ ≈ 0.95, while `part_08` (μ = 0.1) and `part_09` (μ = 0.101) are very slippery. The test therefore includes both kinds of part.

### Set-up
| Carrier | Asset | Load |
|---|---|---|
| **A – walled tote** | `Box_part.glb` (120 × 60 × 210 mm, 5 mm floor) | 3 parts in a row: μ = 0.95, 0.1, 0.101 |
| **B – open pallet** | `Pallet.glb` (180 × 62 × 180 mm) | 2 parts: μ = 0.95, 0.1 |

Both carriers are kinematic (mass 0), start side by side 400 mm apart, and run **the same motion profile**, so the only difference is the container (walls vs no walls).

### Motion profile (from `T1_cart_anim.json`)
| Time | Move | Purpose |
|---|---|---|
| 3–7 s | +1000 mm in 4 s (0.25 m/s) | normal, gentle transport speed for a loaded AMR |
| 9–10 s | −1000 mm in 1 s (1.0 m/s), instant start/stop | stress case: abrupt acceleration and braking |
| 12–14 s | 90° turn on the spot in 2 s | turning (centrifugal effect on loose parts) |

### Expected results and what they mean
| Observation | Interpretation | Decision |
|---|---|---|
| A keeps all 3 parts in every phase | totes contain parts, including slippery ones | AMR + tote concept is feasible |
| B loses the slippery part (especially in phase 2 or 3) | open platforms are not robust for μ = 0.1 parts | justifies using a walled tote |
| parts jitter, sink through, or are left behind as the carrier moves | the physics engine does not drag dynamic bodies along with a moving kinematic one | AMR concept not reliable in VEB.js → fall back to conveyor + robot |
| the 90° turn has no effect | rotation is not supported in timeline `moveAdditive` | route the AMR with straight legs only |

### Results – run 2026-11-02 (positions logged every 0.5 s from the Babylon scene)

| Time after Play | ToteA z | A_grip (x, y, z) | Observation |
|---|---|---|---|
| 0 s (at rest) | 0 | (0, 4, −65) | all 3 parts rest correctly on the tote floor |
| 4.0 s | 140 | (0, 3, −65) | tote starts moving; **parts do not move with it** |
| 5.5 s | 515 | (0, −14, −65) | tote has left; parts fall where they were |
| 8.5 s | 1000 | (0, −91, −65) | tote arrived empty; parts keep falling |
| 25 s | 0 | (0, −751, −65) | parts in free fall (no physical floor below y = 0) |

Additional observations:
- The tote's **rear wall passed through the parts** without pushing them (z of A_grip constant at −65 while the wall swept past).
- On the open pallet, the slippery part (μ = 0.1) slid off **before any motion**, just from settling on the uneven pallet top.
- The scene floor is visual only: anything that falls off a device falls forever.
- Carrier motion itself (translation via timeline `moveAdditive`) works exactly as specified (250 mm/s, 1 m/s).

### Conclusion
In VEB.js, an object moved by the timeline (`moveAdditive`/`moveTo`) is **teleported frame by frame**: the physics engine sees a body without velocity, so friction does not drag parts and walls do not push them. A carrier can *support* parts when stationary but cannot *transport* them physically.

This also explains why the provided conveyor works: `surfaceVelocity` explicitly gives the belt surface a velocity that the physics engine uses.

**Consequences for the design**
1. A free-roaming AMR carrying loose parts is **not physically feasible** in VEB.js as is. It would only work if parts are rigidly attached to the cart during travel (`attach` event), which is weaker against the "no transport that ignores physics" rule.
2. Physical transport of loose parts must use **surface velocity (conveyors)**, **gravity (chutes/slides)** or **grasping (robot gripper)**.
3. Every transfer must be caught by a physical surface: there is no floor collider.
4. Slippery parts (part_08, part_09) need positive containment; open flat surfaces are not robust.

---

## T2 – Does the Cartesian robot gripper pick, carry and release parts, regardless of friction?

**Run:** https://digital-factory.io/vebjs/?inputscene=https://mihamoscow.github.io/DF-DFE01/tests/T2_gripper&repoMod3d=https://difactory.github.io/repository/models/PickPlaceCell/

### Why this test
T1 showed that only belts, gravity and grasping can move loose parts. The robot is therefore a key building block, and the parts' different friction values might affect a gripper. The robot's fingers are configured as *triggers* (mass 0, friction 0, `isTrigger: true`), which suggests grasping is not friction-based. This test checks that directly.

### Set-up
Three identical cells side by side, each a copy of the DFE_01 robot `PP` (same StateChart: `rest → pick → place → rest`) with one part placed on a stationary conveyor directly under its pick point:

| Cell | Part friction μ | Represents |
|---|---|---|
| PP1 | 0.95 | normal parts |
| PP2 | 0.1 | part_08 |
| PP3 | 0.101 | part_09 |

The pick point (robot x − 71 mm, belt height 230 mm) was taken from the official PickPlaceCell example. Timeline: `goPick` at 1 s, `goPlace` at 3.5 s, `goRest` at 6 s. Positions of parts, gripper and fingers were logged every 0.25 s.

### Results – run 2026-11-02
| Time | Gripper (PP1) | Part 1 | Part parent | What happens |
|---|---|---|---|---|
| 0–2 s | y 426 → 291 | (−941, 229, −5) | building | gripper descends; part untouched |
| 3.5 s | fingers close to 67 mm gap | (−941, 229, −5) | **PP1.Gripper** | part is **attached to the gripper** |
| 5 s | moves +200 mm in x, rises to y 426 | (−741, 364, −5) | PP1.Gripper | part carried rigidly with the gripper |
| 6 s | opens | (−741, 362, −5) | none | part released **in mid-air, 130 mm above the belt** |
| 6–30 s | back to rest | y 362 → 36 → … | none | part falls **very slowly** (~4.5 s for 130 mm), lands beyond the belt edge, keeps falling |

All three cells behaved **identically** (positions equal to the millimetre).

### Conclusions
1. **Grasping works and is independent of friction.** When the closing fingers overlap the part, VEB.js attaches the part to the gripper; on opening it detaches it. The slippery parts are no problem for the robot.
2. **The default program is not usable as it is.** The place position is only 200 mm from the pick position and the part is released mid-air: the StateChart must be rewritten (lower the gripper before opening; new place coordinates).
3. **The robot does not reach B1.** In DFE_01 its pick point is at x ≈ −941, while B1 runs along x = 0. The robot must be repositioned, or parts brought to it.
4. **Gravity is about 1000× too weak.** A free fall of 130 mm took ~4.5 s (real: 0.16 s). The environment sets gravity to `[0, −9.81, 0]` while the scene uses millimetres, so it acts as 9.81 mm/s². This makes drops look like slow motion, and it also weakens friction on belts (friction force ∝ normal force ∝ g). **To verify next (T3):** set gravity to `[0, −9810, 0]` and check that falls, belts and chutes behave realistically.

---

## T4 – AMR retest: three ways to move the carrier, gravity corrected

**Run:** https://digital-factory.io/vebjs/?inputscene=https://mihamoscow.github.io/DF-DFE01/tests/T4_amr&repoMod3d=https://difactory.github.io/repository/models/PickPlaceCell/

Env gravity set to `[0, -9810, 0]` (mm/s²). Three totes (`Box_part`), each with one grippy (μ 0.95) and one slippery (μ 0.1) part, plus one part dropped from 1000 mm as a gravity check.

| Tote | Motion method | Result |
|---|---|---|
| A | StateChart `moveTo` (same mechanism as robot axes) | tote moved 1000 mm in < 1 s; **parts stayed and fell** |
| B | timeline `moveAdditive` + `attach` parts to tote at t = 1.5 s | attach had **no effect** on these parts; **parts stayed and fell** |
| C | timeline `moveAdditive` + `surfaceVelocity` 250 mm/s on tote floor | **parts stayed and fell** |

Gravity check: the dropped part accelerated at first, then fell at a **constant ~200 mm/s**. The physics engine appears to cap speed at ~200 units/s, i.e. 200 mm/s in this scene. Correcting g therefore does not make falls realistic on its own.

Side effect: with g = 9810, the parts sank through the tote's 5 mm floor while settling (resting at y ≈ −11, inside the floor). Thin mesh floors are not reliable at high gravity.

### Conclusion
Every way of moving a kinematic carrier tested so far moves the carrier but not the loose parts on it. The only mechanism observed to carry parts is the **gripper attachment** (T2). That suggests a feasible AMR variant: a **mobile manipulator**, i.e. a robot/gripper mounted on the moving base that holds the part during travel (like KUKA KMR). To test next (T5).

---

## T5 – Mobile manipulator: robot drives while holding a part ✅

**Run:** https://digital-factory.io/vebjs/?inputscene=https://mihamoscow.github.io/DF-DFE01/tests/T5_mobile_manip&repoMod3d=https://difactory.github.io/repository/models/PickPlaceCell/

### Why
T1/T4 showed that moving carriers cannot carry loose parts, and VEB.js offers no "set velocity" action. But T2 showed the gripper holds parts by attachment, so a part held by the gripper should travel with anything that moves the gripper. This mirrors real mobile manipulators (KUKA KMR, MiR + UR, Yandex Robotics' picking robot).

### Set-up
- Robot `PP` from DFE_01 with one new StateChart state, **`carry`** (lift with fingers closed), inserted between `pick` and `place`.
- New controller asset **`AMR`** whose StateChart drives the whole robot with `moveTo` (`PP` → z = 1500 mm).
- One slippery part (μ = 0.1, like part_08) on a pick table; a place table 1.5 m away.
- Timeline: `goPick` 1 s → `goCarry` 3.5 s → `drive` 5 s → `goPlace` 9 s. Default gravity.

### Results – run 2026-11-02
| Time | Robot base | Part | Part parent |
|---|---|---|---|
| 4.3 s | (−870, 0, 0) | (−941, 229, −5) | **PP.Gripper** (gripped) |
| 6.3 s | (−870, 0, 0) | (−941, 364, −5) | PP.Gripper (lifted) |
| 7.3 s | (−870, 0, 1363) | (−941, 364, 1358) | PP.Gripper (**travelling with the robot**) |
| 8.3 s | (−870, 0, 1500) | (−941, 364, 1495) | PP.Gripper (arrived) |
| 12.3 s | (−870, 0, 1500) | (−741, 363, 1495) | released over the place table, falls onto it |

### Conclusion
**A mobile manipulator works in VEB.js.** The part stays exactly in the gripper during travel (offset constant to the millimetre) and is released at the destination. The concept is feasible. Open points for the real design: the drive is fast (~1.5 m in ~1.5 s, needs a realistic speed), the robot needs a visible mobile base (3D asset), and the default place still releases 130 mm above the surface.
