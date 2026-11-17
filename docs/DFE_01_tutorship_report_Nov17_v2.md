# DFE_01 – Project Progress & Technical Report (Nov 17, 2026) — v2

*v2: revised after an internal review against the model: corrected the AMR/robot pipelining claim, stated the physics state of the delivered parts, clarified the time-based control, corrected the tooling and asset statements, and restructured the tutor questions and next steps.*

## 1. Executive Summary & Operating Assumption

The `DFE_01` Digital Factory model implements a **complete end-to-end automated packaging and internal logistics cell** in VEB.js (`72` assets, `170` animation events, `285.9 s` total cycle time, `0` dropped StateChart events), fully synchronized into `DFE_01.xlsm` and pushed to GitHub (`origin/main`).

### Core Process Assumption: Packaging Department
The cell is modeled as a **packaging department** downstream of production:
1. Incoming parts (`part_01`–`part_10`, including low-friction variants `part_08`/`part_09` with $\mu \approx 0.1$) arrive on the fixed infeed conveyor `B1`.
2. Parts are packed into delivery-ready shipping totes (`Tote1`–`Tote5`, $2$ parts per tote) and secured inside each tote via internal `JawGripper` transport clamps (`C1`, `C2`).
3. A **compact ASRS/ACR-inspired Autonomous Mobile Robot (`AMR` + `TG`)** picks each sealed, delivery-ready tote and relocates it to the fixed delivery point (`Box`), stacking all 5 totes in a $2+2+1$ arrangement.

---

## 2. How Part Movement Is Organized & Design Rationale

### 2.1 End-to-End Material Flow
1. **Infeed Indexing (`B1`)**: Conveyor `B1` (`surfaceVelocity`) advances parts sequentially to `Stopper_B1` ($[-77.5, 230, 1005]\,\text{mm}$) monitored by `Sensor_B1`.
2. **Pick & Place Packing (`PP`)**: The Cartesian robot `PP` ($[29, 0, 1180]\,\text{mm}$) picks each part via `PP.Finger1/2` (`isTrigger: true`) and places $2$ parts per tote ($X = \pm 40\,\text{mm}$). `PP.FloatingX` slides along the rail (`Z = 324` $\leftrightarrow$ `64`), carrying the slider and cable chain together with the arm (`PP.FloatingZ` / `PP.FloatingY`).
3. **5-Tote Vertical Floor Stack (`TotePad` + `Tote5`..`Tote1`)**:
   - **Why a vertical floor stack instead of a second conveyor + robot rail?** Staging `Tote5`–`Tote1` in a single vertical stack ($[0, Y, 1230]\,\text{mm}$, $Y \in \{4, 64, 124, 184, 244\}$) on a `4 mm` `STATIC` floor pad (`TotePad`) eliminates a redundant tote conveyor and long linear robot travel, saving floor space, equipment cost, and cycle time.
   - **Top-Down Sequence**: `PP` fills `Tote1` (top) through `Tote5` (bottom) in sequence; as soon as a tote is filled and clamped, the AMR clears it from the top of the stack before `PP` loads the next tote below.
4. **Transport Lock (`Tote{1..5}.C1`, `.C2`)**:
   - **Why internal clamps?** In Havok physics, low-friction parts ($\mu = 0.1$) shift when lifted dynamically. Each tote carries two `JawGripper` clamps closing to `±27 mm`, locking the packed parts inside the tote as a **shipping transport lock** for safe delivery into `Box`.
   - **Physics state of the delivered parts**: when a clamp closes, the VEB.js `JawGripper` sets the part to `STATIC` and parents it to the clamp. The 10 parts therefore arrive in `Box` locked inside their totes (inside the `Box` volume), not as free `DYNAMIC` bodies resting on the `Box` floor. This is intentional (transport lock) and is to be confirmed with the tutor (§5.1).
5. **Compact ASRS / ACR Relocation (`AMR` + `TG`)**:
   - **Why a single-tote workstation ACR?** With `Box` only $\sim 1.8\,\text{m}$ from `TotePad`, the AMR moves $1$ tote per trip, so it doesn't have to wait for all 5 totes the way a multi-shelf batch ACR would.
   - **Trade-off of the vertical stack (current limitation)**: the stack is filled top-down, so `PP` can only load the next tote after the AMR has removed the one above it. Packing and transport therefore run mostly **in series**: `PP` waits for the AMR four times ($14.9 + 17.5 + 17.9 + 18.3 \approx 69\,\text{s}$ of the $285.9\,\text{s}$ cycle). The stack saves floor space and equipment at the cost of this idle time. A side-by-side tote buffer (two load positions) would let packing and transport overlap and is a candidate improvement.
   - **Kinematics & Clearance**: `TG` approaches `TotePad`, grips the tote, lifts, executes a straight `-X` `undock` ($[-400, 551, 1230]\,\text{mm}$) before entering the main transit aisle ($Z = 1800\,\text{mm}$), and uses an **inverted-L goose-neck arm** ($+160\dots+215\,\text{mm}$ above `TG`) so the reach boom clears `Box`'s $250\,\text{mm}$ rim by $48\,\text{mm}$ even at the lowest Layer-1 drop ($Y_{\text{TG}} = 138\,\text{mm}$).

### 2.2 Factory Layout, Environment & Safety Zones
- **Robot Safety Cage (`Fence_S1/S2`, `E1/E2`, `N1/N2`, `SignalPole`)**: Surrounds `PP` ($X \in [225, 1135]$, $Z \in [420, 1410]$) with full clearance for the moving cable chain, while leaving the long west side of `B1` open so operators can visually inspect parts on the belt.
- **Factory Floor & Walls (`FactoryFloor.glb`, `FactoryWalls.glb`)**: Enclosed $8\,\text{m} \times 10\,\text{m}$ shop floor with $3.5\,\text{m}$ industrial walls, steel columns, roll-up logistics door, emergency exit, and balanced high-bay lighting (`DFE_01_env.json`):
  - **Hazard Perimeter ($45^\circ$ Yellow/Black Stripes)**: Encloses the full length of conveyor `B1` + `PP` cell ($X \in [-350, 1250]$, $Z \in [-1200, 1550]$) and the `Box` station ($X \in [-2700, -1700]$, $Z \in [600, 1600]$).
  - **Pedestrian Safe Zone (ISO Green Corridor)**: Placed **between the delivery `Box` and the conveyor/robot cell** ($X \in [-1650, -850]$), featuring a high-visibility **zebra crosswalk** where it intersects the AMR transit corridor (`CROSSWALK: AMR STOPS FOR PEDESTRIAN`).
  - **AMR Transit Lane**: Slate polyurethane lane with solid yellow borders, dashed white centerline, flow arrows, and `AMR DOCK 1` / `AMR DOCK 2` target markings.

---

## 3. Technical Architecture (`72` Assets, `170` Events, `285.9 s`)

### 3.1 Scene Objects & Physics Properties (Havok Engine)

| Category | Asset ID(s) | 3D Representation | Physics / MotionType | Key Properties & Coordinates |
| :--- | :--- | :--- | :--- | :--- |
| **Root** | `building` | — (`IfcBuilding`) | None | Scene placement root (`UnitOfMeasureScale: 0.001`) |
| **Original Fixed Assets** (properties as in the assignment, unchanged) | `B1` | `ConveyorNew.glb` | **Kinematic (`ANIMATED`)** | `mass: 0`, `restitution: 0.3`, `friction: 0`, pos `[0, 0, 0]` |
| | `Box` | `Box_large.glb` | **Kinematic (`ANIMATED`)** | `mass: 0`, `restitution: 0.3`, `friction: 0`, pos `[-2200, 0, 1100]` |
| | `Grid` | `Grid.glb` | **Kinematic (`ANIMATED`)** | `mass: 0`, `restitution: 0.3`, `friction: 0`, pos `[-2000, 540, 1100]` |
| **Dynamic Parts (10)** | `part_01`–`part_07`, `part_10` | `Part.glb` | **Dynamic** | `mass: 1`, `restitution: 0.1`, `friction: 0.95`, `Y = 230` |
| | `part_08`, `part_09` | `Part.glb` | **Dynamic** | `mass: 1`, `restitution: 0.1`, `friction: 0.1` / `0.101` (low-friction) |
| **Dynamic Totes (5)** | `Tote5`–`Tote1` | `Box_part.glb` | **Dynamic** | `mass: 2`, `restitution: 0`, `friction: 0.9`, `rot: [0, π/2, 0]`, `Y = 4..244` |
| **Internal Tote Clamps (10)** | `Tote{1..5}.C1`, `.C2` | `ToteClamp.glb` | **Kinematic (`ANIMATED`)** | `mass: 0`, `friction: 0`, parented to `Tote{k}` (`Z = ±40`) |
| | `Tote{k}.C{1,2}.Jaw1`, `.Jaw2` | `ToteClamp.glb#TC_Jaw{1,2}` | **Kinematic Trigger** | `MotionType: ANIMATED`, `isTrigger: true`, closes to `±27 mm` |
| **Pick & Place Robot** | `PP`, `.FloatingX/Z/Y`, `.Gripper` | `Pick_and_Place_Robot.glb` | **Visual Hierarchy** | Pos `[29, 0, 1180]`, `rot: [0, π, 0]` (`PP.FloatingX` + `.FloatingZ` move) |
| | `PP.Finger1`, `PP.Finger2` | `Pick_and_Place_Robot.glb#PP_Finger{1,2}` | **Kinematic Trigger** | `MotionType: ANIMATED`, `isTrigger: true` |
| **Compact ASRS AMR & Gripper** | `AMR` | `AMR.glb` | **Visual Carrier** | Pos `[-870, 0, 1230]`, `rot: [0, -π/2, 0]` (rounded base, LiDAR visor, mast) |
| | `TG` (`JawGripper`) | `ToteGripper.glb` | **Visual Parent** | Pos `[-400, 551, 1230]`, `rot: [0, π/2, 0]` (goose-neck arm + carriage) |
| | `TG.Jaw1`, `TG.Jaw2` | `ToteGripper.glb#TG_Jaw{1,2}` | **Kinematic Trigger** | `MotionType: ANIMATED`, `isTrigger: true` (single-primitive jaws) |
| **Static Supports & Fences** | `TotePad` | `FloorPad.glb` | **Static (`STATIC`)** | `mass: 0`, `friction: 0.9`, `restitution: 0`, `240×4×136 mm` at `[0, 0, 1230]` |
| | `Stopper_B1` | `Stopper.glb` | **Static (`STATIC`)** | `mass: 0`, `friction: 0.5`, `restitution: 0.1`, pos `[-77.5, 230, 1005]` |
| | `Fence_S1/S2`, `E1/E2`, `N1/N2` | `Grid_second.glb` | **Static (`STATIC`)** | `mass: 0`, `friction: 0.5`, `restitution: 0.1`, `X = 225..1135`, `Z = 420..1410` |
| **Visual Sensors & Environment** | `Sensor_B1`, `SignalPole` | `Sensor.glb`, `SignalPole.glb` | **Visual (No Physics)** | `[-65, 245, 976]` and `[1150, 0, 420]` |
| | `FactoryFloor`, `FactoryWalls` | `FactoryFloor.glb`, `FactoryWalls.glb` | **Visual (No Physics)** | `8m × 10m` floor (`2048×2048` texture) + `3.5m` industrial walls |

### 3.2 StateCharts & Code Pipeline (`170` Events)
- **StateCharts**:
  - `B1_SC` (`idle`, `forward`, `backward`)
  - `PP_SC` (`rest`, `pick`, `lift`, `place1`, `place2`, `release`, `up`, `lower1`–`lower5`)
  - `Tote{1..5}.C1_SC` / `C2_SC` (`open`, `closed`)
  - `TG_SC` (`34` states: `home`, `pickApproach`, `dock`, `grip`, `lift`, `undock`, `aisleOut`, `boxNorth`, `aisleIn`, `down1`–`5`, `boxSlot1`–`5`, `boxLower1`–`5`, `release1`–`5`, `boxUp1`–`5`)
- **Tooling & Workbook Sync**:
  - The custom assets (`AMR.glb`, `ToteGripper.glb`, `ToteClamp.glb`, `FloorPad.glb`, `FactoryFloor.glb`, `FactoryWalls.glb`) and the Step 5–6 scene were produced with procedural Python scripts. **These generator scripts are not yet in the repository** and will be committed to `tools/` before submission. `tools/` currently contains `export_json.py`, `sync_to_xlsm.py`, `serve_local.py`, `build_v1.py` and `Module1_mac_fixed.bas`.
  - `tools/sync_to_xlsm.py` and `tools/export_json.py --check DFE_01.xlsm` synchronize all `72` assets and `170` events into `DFE_01.xlsm` (`Context`, `Assets`, `Anim`, `Sequences`) while preserving VBA macros.

---

## 4. Compliance Audit vs. Course Brief (`DF_ProjectWork_2026_DFE.pdf` & `DF_ProjectWork_26-27.pdf`)

| Brief Requirement | Reference | Status | Notes / Evidence |
| :--- | :--- | :--- | :--- |
| Fixed assets (`B1`, `Box`, `Grid`) keep original position & orientation | `DFE` §3.1 | **Compliant** | `B1` at `[0,0,0]`, `Box` at `[-2200,0,1100]`, `Grid` at `[-2000,540,1100]` untouched. `PP` repositioned/modified as permitted by §4.2. |
| All 10 parts moved into `Box` with physical consistency (no teleportation) | `DFE` §3.2, §5.1–5.2 | **Compliant** | Full `285.9 s` run verified in VEB.js: all 10 parts conveyed on `B1`, picked by `PP`, clamped in `Tote1..Tote5`, carried by `TG`/`AMR`, and stacked `2+2+1` in `Box`. |
| Millimetres `[mm]` unit consistency | `DFE` §3.4 | **Compliant** | `UnitOfMeasureScale: 0.001`; all custom `.glb` assets authored in metres with `unit: 1`. |
| Reproducibility & custom asset availability | `DFE` §3.3, §4.2, §8.4 | **Compliant** | All 16 `.glb` assets used in the scene are hosted in `assets/` on GitHub Pages (`LightCurtain.glb` is also in `assets/` but is not used in the current scene), `"RepoPath"` is set to `"https://mihamoscow.github.io/DF-DFE01/assets/"` in `DFE_01.json` and `DFE_01.xlsm`, and `README.md` points directly to the GitHub Pages VEB.js URL. |
| `DFE_01.xlsm` as primary modelling tool + Export JSON check | `DFE` §6.1, §8.1.1 | **Action Needed** | Synced and verified via `export_json.py --check`, pending final manual button test (`Export Scene JSON` / `Export Animation JSON`) inside Excel. |
| Event-driven / sensor-based control & advanced features | `DFE` §4.3.3, §5.6 | **Partial / Optional** | StateCharts drive `B1`, `PP`, `Tote{1..5}.C{1,2}` and `TG`, but every transition is triggered by a time schedule (`170` timed `sendEvent`s on a `100 ms` grid), i.e. open-loop control. `Sensor_B1` and `SignalPole` are placed but not yet wired; sensor-triggered picking is the planned Additional Module extension. |
| Technical Report (following official template) | `DFE` §6.2 | **Outstanding** | Not yet written. |
| Demonstration Video | `DFE` §6.3 | **Outstanding** | Not yet recorded. |
| Intermediate Presentation | `26-27` p. 13 | **Outstanding** | Scheduled for **December 1, 2026**. |

---

## 5. Questions for Tutorship & Next Steps

### 5.1 Questions for the Tutor

1. **Parts in `Box` (transport lock)**: the parts end up `STATIC`, parented to the closed clamps, inside totes standing in `Box`. Does this count as "all parts moved into the Box", or should the clamps open after placement so that the parts end up as free dynamic bodies?
2. **Custom handling assets**: are the totes (`Box_part.glb`), the internal clamps (`ToteClamp.glb`) and the custom `AMR` / `TG` models acceptable additions?
3. **Control logic**: is a time-scheduled event sequence acceptable for the base requirement, or is sensor/event-driven control expected?
4. **AMR motion**: `AMR` and `TG` move together via `moveTo` in each `TG_SC` state (straight-line segments around the `Grid`). Is this level of AMR kinematics sufficient?

### 5.2 Next Steps

1. **Excel macro parity**: run Excel's **Export Scene JSON** / **Export Animation JSON** buttons once and compare the output with `export_json.py --check` (`RepoPath` is already set to GitHub Pages).
2. **Reproducibility**: commit the asset/scene generator scripts to `tools/`.
3. **Cameras**: `camera.d2` and `camera.d3` are identical defaults; define overview, robot-cell and `Box` views for the video.
4. **Optional improvements**: wire `Sensor_B1` to trigger the `PP` pick (Additional Module, §4.3.3 / §5.6); evaluate a side-by-side tote buffer to remove the ~69 s robot idle time.
5. **Deliverables before Dec 1, 2026**: record the **Demonstration Video** (§6.3), draft the **Technical Report** (§6.2), and prepare the **Dec 1 Intermediate Presentation**.
