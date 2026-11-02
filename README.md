# Digital Factory – Project Work 2026-27 – DFE_01

Material handling system for assignment variant **DFE_01** (Digital Factory, Prof. Urgo, Politecnico di Milano).
Goal: move the 10 parts from conveyor B1 into the destination Box, avoiding the Grid obstacle, in a physically consistent way.

## Run it in VEB.js

https://digital-factory.io/vebjs/?inputscene=https://mihamoscow.github.io/DF-DFE01/DFE_01&repoMod3d=https://difactory.github.io/repository/models/PickPlaceCell/

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

Units are millimetres throughout.
