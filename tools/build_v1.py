#!/usr/bin/env python3
"""
build_v1.py - generates the DFE_01_v1 scene (layout v1 of the packaging cell)
from the original DFE_01.json. Fixed assets (B1, parts, Grid, Box) are kept
unchanged; the robot is relocated and the cell elements are added.

Usage:  python3 tools/build_v1.py      (run from the repo root)
Output: DFE_01_v1.json, DFE_01_v1_anim.json, DFE_01_v1_env.json
All lengths in mm, world axes as in VEB.js (y up). B1 runs along +z at x = 0.
"""
import copy, json, math

SRC = json.load(open("DFE_01.json"))
A = {a["id"]: a for a in SRC["assets"]}
FT = "https://w3id.org/ontoeng/factory#"
assets = []

def add(a): assets.append(a); return a

# ---------- fixed assets (unchanged) ----------
for aid in ["building", "B1"] + [f"part_{i:02d}" for i in range(1, 11)] + ["Grid", "Box"]:
    add(copy.deepcopy(A[aid]))

# ---------- layout parameters ----------
PICK_Z = 931            # where the front part stops on B1 (stopper face at z = 960)
ROBOT = [71, 0, 936]    # robot base: pick point = base + (-71, *, -5)  (from T2 / PickPlaceCell example)
TOTE_X = 370            # tote station line (x), totes rotated 90 deg: long axis along x
TOTE_Y = 231            # tote bottom on the station conveyor belt (belt top 230)
TOTE_Z = [931, 791, 651, 511]   # tote 1 = filling position, aligned with the robot
SLOT_LOCAL = [-65, 0, 65]       # slot centres along the tote's long axis (local z)
SLOT_X = [TOTE_X + s for s in SLOT_LOCAL]          # world x of slots (local z -> world x)
SLOT_AXIS = [-x for x in SLOT_X]                   # robot FloatingZ axis value for each slot

# ---------- stopper at the end of B1 ----------
add({"id": "Stopper_B1", "type": FT + "Actuator", "representations": [{"file": "Stopper.glb", "unit": 1}],
     "position": [-77, 230, 960], "rotation": [0, 0, 0], "placementRelTo": "building",
     "properties": {"mass": 0, "restitution": 0.1, "friction": 0.5, "MotionType": "STATIC"}})
add({"id": "Sensor_B1", "type": FT + "SensorBarrier", "representations": [{"file": "Sensor.glb", "unit": 1}],
     "position": [-150, 230, 900], "rotation": [0, 0, 0], "placementRelTo": "building"})

# ---------- robot (relocated, new StateChart) ----------
FZ = lambda ax: {"action": "moveTo", "target": "PP.FloatingZ", "position": [-120, 80, ax]}
FY = lambda y, d=None: dict({"action": "moveTo", "target": "PP.FloatingY", "position": [-6, y, -171]}, **({"delay": d} if d else {}))
FING = lambda w, d=None: [dict({"action": "moveTo", "target": "PP.Finger1", "position": [0, -38, w]}, **({"delay": d} if d else {})),
                          dict({"action": "moveTo", "target": "PP.Finger2", "position": [0, -38, -w]}, **({"delay": d} if d else {}))]
UP, DOWN_PICK, DOWN_PLACE = -40, -175, -167
states = {
    "rest":    {"on": {"goPick": "pick"}, "entry": [FZ(0), FY(UP)] + FING(38, 500)},
    "pick":    {"on": {"goLift": "lift"}, "entry": [FZ(0), FY(DOWN_PICK)] + FING(3, 1500)},
    "lift":    {"on": {"goSlot1": "slot1", "goSlot2": "slot2", "goSlot3": "slot3"}, "entry": [FY(UP)]},
    "lower":   {"on": {"goRelease": "release"}, "entry": [FY(DOWN_PLACE)]},
    "release": {"on": {"goRest": "rest"}, "entry": FING(38)},
}
for k in range(3):
    states[f"slot{k+1}"] = {"on": {"goLower": "lower"}, "entry": [FZ(SLOT_AXIS[k])]}
for rid in ["PP", "PP.FloatingX", "PP.FloatingZ", "PP.FloatingY", "PP.Gripper", "PP.Finger1", "PP.Finger2"]:
    r = add(copy.deepcopy(A[rid]))
    if rid == "PP":
        r["position"] = ROBOT
        r["statechart"] = {"id": "PP_SC", "initial": "rest", "states": states}

# ---------- tote station: short conveyor + 4 clamping totes ----------
st = add(copy.deepcopy(A["B1"])); st["id"] = "ToteConveyor"; st["position"] = [TOTE_X, 0, 721]
st["scale"] = [1, 1, 0.55]
st["statechart"] = json.loads(json.dumps(st["statechart"]).replace('"B1', '"ToteConv').replace('"target": "B1"', '"target": "ToteConveyor"'))
for s in st["statechart"]["states"].values():
    s["entry"]["target"] = "ToteConveyor"
st["statechart"]["id"] = "ToteConveyor_SC"

def jaws(c, x): return [{"action": "moveTo", "target": f"{c}.Jaw1", "position": [x, -35, 0]},
                        {"action": "moveTo", "target": f"{c}.Jaw2", "position": [-x, -35, 0]}]
for t, z in enumerate(TOTE_Z, 1):
    tid = f"Tote{t}"
    add({"id": tid, "type": FT + "Pallet", "representations": [{"file": "Box_part.glb", "unit": 1}],
         "position": [TOTE_X, TOTE_Y, z], "rotation": [0, math.pi / 2, 0], "placementRelTo": "building",
         "properties": {"mass": 2, "restitution": 0.1, "friction": 0.9}})
    for k, sz in enumerate(SLOT_LOCAL, 1):
        c = f"{tid}.C{k}"
        add({"id": c, "type": FT + "JawGripper", "representations": [{"file": "ToteClamp.glb", "unit": 1}],
             "position": [0, 55, sz], "rotation": [0, 0, 0], "placementRelTo": tid, "parentObject": tid,
             "properties": {"mass": 0, "restitution": 0, "friction": 0, "MotionType": "ANIMATED"},
             "statechart": {"id": c + "_SC", "initial": "open", "states": {
                 "open": {"on": {"clamp": "closed"}, "entry": jaws(c, 47)},
                 "closed": {"on": {"unclamp": "open"}, "entry": jaws(c, 31)}}}})
        for j, x in (("1", 47), ("2", -47)):
            add({"id": f"{c}.Jaw{j}", "type": FT + "JawFinger", "representations": [{"file": f"ToteClamp.glb#TC_Jaw{j}", "unit": 1}],
                 "position": [x, -35, 0], "placementRelTo": c, "parentObject": c,
                 "properties": {"mass": 0, "restitution": 0, "friction": 0, "MotionType": "ANIMATED", "isTrigger": True}})

# ---------- safety fence (Grid_second panels, 1060 mm high), door + light curtain ----------
X0, X1, Z0, Z1 = -250, 650, 450, 1500
def panel(pid, cx, cz, along, length):
    rot = [0, 0, -math.pi / 2] if along == "z" else [0, math.pi / 2, -math.pi / 2]
    add({"id": pid, "type": FT + "Artifact", "representations": [{"file": "Grid_second.glb", "unit": 1}],
         "position": [cx, 540, cz], "rotation": rot, "scale": [1, 1, round(length / 660, 3)], "placementRelTo": "building",
         "properties": {"mass": 0, "restitution": 0.1, "friction": 0.5, "MotionType": "STATIC"}})
panel("Fence_W1", X0, 780, "z", 660); panel("Fence_W2", X0, 1170, "z", 660)
panel("Fence_E1", X1, 780, "z", 660); panel("Fence_E2", X1, 1170, "z", 660)
panel("Fence_N1", -25, Z1, "x", 450)                      # door x 200..600 left open for the AMR
panel("Fence_S1", -190, Z0, "x", 120); panel("Fence_S2", 430, Z0, "x", 440)   # gap for B1
add({"id": "LightCurtain", "type": FT + "SensorBarrier", "representations": [{"file": "LightCurtain.glb", "unit": 1}],
     "position": [400, 0, Z1], "rotation": [0, 0, 0], "placementRelTo": "building"})
add({"id": "SignalPole", "type": FT + "Actuator", "representations": [{"file": "SignalPole.glb", "unit": 1}],
     "position": [X1 + 30, 0, Z0 + 20], "rotation": [-math.pi / 2, 0, 0], "placementRelTo": "building"})

# ---------- AMR placeholder, parked outside the door ----------
add({"id": "AMR", "type": FT + "Robot", "representations": [{"file": "AMR.glb", "unit": 1}],
     "position": [400, 0, 1900], "rotation": [0, math.pi, 0], "placementRelTo": "building"})

ctx = dict(SRC["context"]); ctx["RepoPath"] = "https://mihamoscow.github.io/DF-DFE01/assets/"
json.dump({"context": ctx, "scene": [a["id"] for a in assets], "assets": assets}, open("DFE_01_v1.json", "w"), indent=1)

# ---------- timeline: B1 runs, robot fills tote 1 (3 parts), clamps close ----------
ev = lambda t, d: {"trigger": {"type": "timestamp", "data": str(t)}, "event": {"type": "sendEvent", "data": d}}
robot, clamps = [], {k: [] for k in range(1, 4)}
belt = [ev(1000, "B1startF"), ev(1500, "B1stop")]      # bring the first part to the stopper
T = 3000
for k in range(1, 4):
    robot += [ev(T, "goPick"), ev(T + 2500, "goLift"), ev(T + 4000, f"goSlot{k}"), ev(T + 6000, "goLower"),
              ev(T + 7500, "goRelease"), ev(T + 8500, "goRest")]
    clamps[k].append(ev(T + 8000, "clamp"))
    belt += [ev(T + 4000, "B1startF"), ev(T + 6600, "B1stop")]   # index the next part (200 mm pitch at 80 mm/s)
    T += 9500
nodes = [{"id": "B1", "actions": belt}, {"id": "PP", "actions": robot}]
nodes += [{"id": f"Tote1.C{k}", "actions": clamps[k]} for k in range(1, 4)]
json.dump({"context": {"assetTrail": False, "UnitOfMeasureScale": 0.001, "Zup": False, "RepoAnim": ""},
           "nodes": nodes, "sequences": [], "bookmarks": []}, open("DFE_01_v1_anim.json", "w"), indent=1)

env = json.load(open("DFE_01_env.json"))
env["cameras"][0].update({"position": [1700, 1500, 2700], "rotation": [0.5, -2.5, 0], "speed": 64})
env["cameras"][1].update({"position": [700, 700, 1200], "rotation": [0.55, -2.2, 0], "speed": 32})
json.dump(env, open("DFE_01_v1_env.json", "w"), indent=1)
print(len(assets), "assets; slot axis values", SLOT_AXIS)
