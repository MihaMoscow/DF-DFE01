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
