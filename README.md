# Digital Factory – Project Work 2026-27 – DFE_01

Material handling system for assignment variant **DFE_01** (Digital Factory, Prof. Urgo, Politecnico di Milano).
Goal: move the 10 parts from conveyor B1 into the destination Box, avoiding the Grid obstacle, in a physically consistent way.

## Run it in VEB.js

https://digital-factory.io/vebjs/?inputscene=https://mihamoscow.github.io/DF-DFE01/DFE_01&repoMod3d=https://mihamoscow.github.io/DF-DFE01/assets/

Original (unmodified) assignment scene, for comparison:

https://digital-factory.io/vebjs/?inputscene=https://difactory.github.io/repository/scenes/PW/2026/DFE_01&repoMod3d=https://difactory.github.io/repository/models/PickPlaceCell/

## Files

| File | Role |
|---|---|
| `DFE_01.xlsm` | Primary model (spreadsheet). Edit here. |
| `DFE_01.json` | Scene (assets, positions, StateCharts) – exported from the xlsm |
| `DFE_01_anim.json` | Animation / event schedule – exported from the xlsm |
| `DFE_01_env.json` | Environment (cameras, lights, physics) – edited by hand |
| `tools/export_json.py` | Mac-safe replacement for the xlsm "Export" buttons |
| `tools/Module1_mac_fixed.bas` | Fixed VBA module, if you prefer the Excel buttons |
| `assets/` | Custom 3D models / resources (if any) |

## Edit → test loop

1. Edit `DFE_01.xlsm` in Excel and **save**.
2. `python3 tools/export_json.py DFE_01.xlsm --check`
3. Commit and push → GitHub Pages republishes in ~1 min.
4. Reload the VEB.js link above (hard refresh: Cmd+Shift+R).

## Regenerating the custom assets and the scene

All custom assets and the scene are produced by scripts in `tools/` (paths are relative to the repo, run from anywhere).

```
pip3 install -r requirements.txt
python3 tools/generate_amr_glb.py              # assets/AMR.glb, assets/ToteGripper.glb
python3 tools/generate_factory_environment.py  # assets/FactoryFloor.glb, assets/FactoryWalls.glb
python3 tools/make_floor_pad_glb.py            # assets/FloorPad.glb
python3 tools/fix_pp_robot_glb.py              # modifies assets/Pick_and_Place_Robot.glb in place (see note)
python3 tools/build_step6_floor_stack.py       # DFE_01.json + DFE_01_anim.json, validates StateChart transitions
python3 tools/sync_to_xlsm.py                  # writes scene + timeline back into DFE_01.xlsm
python3 tools/export_json.py DFE_01.xlsm --check   # confirms xlsm and JSON match
```

Notes:
- `fix_pp_robot_glb.py` must be run on the **original** course model
  (https://github.com/difactory/repository/blob/main/models/PickPlaceCell/Pick_and_Place_Robot.glb);
  it refuses to run twice on an already-fixed file. The repo already contains the fixed version.
- `FactoryFloor.glb` paints text with macOS system fonts (Arial/Helvetica); on other systems
  Pillow's default font is used, so the floor lettering may differ slightly. Geometry is identical.
- The xlsm remains the primary model; the Excel buttons **Export Scene JSON / Export Animation JSON**
  produce the same JSON as `export_json.py`.

Units are millimetres throughout.
