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

### Results
| Date | Phase 1 | Phase 2 | Phase 3 | Notes |
|---|---|---|---|---|
| | | | | |
