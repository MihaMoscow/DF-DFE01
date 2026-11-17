import json
import re

PI = 3.14159265358979
HALF_PI = 1.5707963267949

# Stacked tote Y bases resting flush on 4 mm FloorPad (no initial drop)
TOTE_Y = {
    1: 244,
    2: 184,
    3: 124,
    4: 64,
    5: 4,
}
TOTE_SPAWN_Y = TOTE_Y


STACK_Z = 1230
PP_Z = 1180


def make_tote_and_clamps(tote_id, y_pos):
    assets = [
        {
            "id": tote_id,
            "type": "https://w3id.org/ontoeng/factory#Pallet",
            "representations": [{"file": "Box_part.glb", "unit": 1}],
            "position": [0, y_pos, STACK_Z],
            "rotation": [0, HALF_PI, 0],
            "placementRelTo": "building",
            "properties": {
                "mass": 2,
                "restitution": 0.0,
                "friction": 0.9,
            },
        }
    ]
    # 2 slots per tote at X_world = -40 (C1) and +40 (C2) -> 34 mm gap between 46 mm parts, 37 mm wall clearance
    for idx, z_off in [(1, -40), (2, 40)]:
        cid = f"{tote_id}.C{idx}"
        j1 = f"{cid}.Jaw1"
        j2 = f"{cid}.Jaw2"
        assets.append(
            {
                "id": cid,
                "type": "https://w3id.org/ontoeng/factory#JawGripper",
                "representations": [{"file": "ToteClamp.glb", "unit": 1}],
                "position": [0, 55, z_off],
                "rotation": [0, 0, 0],
                "placementRelTo": tote_id,
                "parentObject": tote_id,
                "properties": {
                    "mass": 0,
                    "restitution": 0.0,
                    "friction": 0.0,
                    "MotionType": "ANIMATED",
                },
                "statechart": {
                    "id": f"{cid}_SC",
                    "initial": "open",
                    "states": {
                        "open": {
                            "on": {"clamp": "closed"},
                            "entry": [
                                {"action": "moveTo", "target": j1, "position": [47, -35, 0]},
                                {"action": "moveTo", "target": j2, "position": [-47, -35, 0]},
                            ],
                        },
                        "closed": {
                            "on": {"unclamp": "open"},
                            "entry": [
                                {"action": "moveTo", "target": j1, "position": [27, -35, 0]},
                                {"action": "moveTo", "target": j2, "position": [-27, -35, 0]},
                            ],
                        },
                    },
                },
            }
        )
        assets.append(
            {
                "id": j1,
                "type": "https://w3id.org/ontoeng/factory#JawFinger",
                "representations": [{"file": "ToteClamp.glb#TC_Jaw1", "unit": 1}],
                "position": [47, -35, 0],
                "placementRelTo": cid,
                "parentObject": cid,
                "properties": {
                    "mass": 0,
                    "restitution": 0.0,
                    "friction": 0.0,
                    "MotionType": "ANIMATED",
                    "isTrigger": True,
                },
            }
        )
        assets.append(
            {
                "id": j2,
                "type": "https://w3id.org/ontoeng/factory#JawFinger",
                "representations": [{"file": "ToteClamp.glb#TC_Jaw2", "unit": 1}],
                "position": [-47, -35, 0],
                "placementRelTo": cid,
                "parentObject": cid,
                "properties": {
                    "mass": 0,
                    "restitution": 0.0,
                    "friction": 0.0,
                    "MotionType": "ANIMATED",
                    "isTrigger": True,
                },
            }
        )
    return assets


def make_pp_statechart():
    # With PP at Z=1180 and -90 deg baked into visual children of Pick_and_Place_Robot.glb:
    # - PP.FloatingX (rail slider + cable chain) slides along PP local Z: 324.0 (pick @ Z=970) <-> 64.0 (stack @ Z=1230)
    # - PP.FloatingZ (cross-arm) slides along PP local X: 100 (pick) <-> 140 (slot1) / 60 (slot2), Z fixed on slider at -120.8
    # - PP.FloatingY (vertical quill) at [171, y, -6] (rotated -90 deg from [-6, y, -171])
    lower_on = {f"goLower{k}": f"lower{k}" for k in range(1, 6)}
    states = {
        "rest": {
            "on": {"goPick": "pick"},
            "entry": [
                {"action": "moveTo", "target": "PP.FloatingX", "position": [-243.7, 369, 324]},
                {"action": "moveTo", "target": "PP.FloatingZ", "position": [100, 80, -120.8]},
                {"action": "moveTo", "target": "PP.FloatingY", "position": [171, -40, -6]},
                {"action": "moveTo", "target": "PP.Finger1", "position": [0, -38, 38], "delay": 500},
                {"action": "moveTo", "target": "PP.Finger2", "position": [0, -38, -38], "delay": 500},
            ],
        },
        "pick": {
            "on": {"goLift": "lift", "goRest": "rest"},
            "entry": [
                {"action": "moveTo", "target": "PP.FloatingX", "position": [-243.7, 369, 324]},
                {"action": "moveTo", "target": "PP.FloatingZ", "position": [100, 80, -120.8]},
                {"action": "moveTo", "target": "PP.FloatingY", "position": [171, -175, -6]},
                {"action": "moveTo", "target": "PP.Finger1", "position": [0, -38, 3], "delay": 1500},
                {"action": "moveTo", "target": "PP.Finger2", "position": [0, -38, -3], "delay": 1500},
            ],
        },
        "lift": {
            "on": {
                "goPlace1": "place1",
                "goPlace2": "place2",
                "goRest": "rest",
            },
            "entry": [
                {"action": "moveTo", "target": "PP.FloatingY", "position": [171, -40, -6]}
            ],
        },
        "place1": {
            "on": {**lower_on, "goRest": "rest"},
            "entry": [
                {"action": "moveTo", "target": "PP.FloatingX", "position": [-243.7, 369, 64]},
                {"action": "moveTo", "target": "PP.FloatingZ", "position": [140, 80, -120.8]},
            ],
        },
        "place2": {
            "on": {**lower_on, "goRest": "rest"},
            "entry": [
                {"action": "moveTo", "target": "PP.FloatingX", "position": [-243.7, 369, 64]},
                {"action": "moveTo", "target": "PP.FloatingZ", "position": [60, 80, -120.8]},
            ],
        },
        "release": {
            "on": {"goUp": "up"},
            "entry": [
                {"action": "moveTo", "target": "PP.Finger1", "position": [0, -38, 38]},
                {"action": "moveTo", "target": "PP.Finger2", "position": [0, -38, -38]},
            ],
        },
        "up": {
            "on": {"goRest": "rest"},
            "entry": [
                {"action": "moveTo", "target": "PP.FloatingY", "position": [171, -40, -6]}
            ],
        },
    }
    for k, ty in TOTE_Y.items():
        ly = ty - 397
        states[f"lower{k}"] = {
            "on": {"goRelease": "release"},
            "entry": [
                {"action": "moveTo", "target": "PP.FloatingY", "position": [171, ly, -6]}
            ],
        }
    return {"id": "PP_SC", "initial": "rest", "states": states}


def make_tg_statechart():
    # 2 + 2 + 1 stacked in Box: Layer 1 (Z=1000,1200 @ low_y=138), Layer 2 (low_y=198), Layer 3 (Z=1000 @ low_y=258)
    slot_cfg = {
        1: (1000, 138),
        2: (1200, 138),
        3: (1000, 198),
        4: (1200, 198),
        5: (1000, 258),
    }
    stack_z = STACK_Z
    aisle_z = 1800
    amr_dx = -470

    states = {
        "home": {
            "on": {
                "goDock": "dock",
                "goPickApproach": "pickApproach",
            },
            "entry": [
                {
                    "action": "moveTo",
                    "target": "TG",
                    "position": [-400, 551, stack_z],
                    "rotation": [0, HALF_PI, 0],
                },
                {
                    "action": "moveTo",
                    "target": "AMR",
                    "position": [-400 + amr_dx, 0, stack_z],
                    "rotation": [0, -HALF_PI, 0],
                },
                {"action": "moveTo", "target": "TG.Jaw1", "position": [90, -60, 0]},
                {"action": "moveTo", "target": "TG.Jaw2", "position": [-90, -60, 0]},
            ],
        },
        "pickApproach": {
            "on": {"goDock": "dock"},
            "entry": [
                {
                    "action": "moveTo",
                    "target": "TG",
                    "position": [-400, 551, stack_z],
                    "rotation": [0, HALF_PI, 0],
                },
                {
                    "action": "moveTo",
                    "target": "AMR",
                    "position": [-400 + amr_dx, 0, stack_z],
                    "rotation": [0, -HALF_PI, 0],
                },
            ],
        },
        "dock": {
            "on": {f"goDown{k}": f"down{k}" for k in range(1, 6)},
            "entry": [
                {
                    "action": "moveTo",
                    "target": "TG",
                    "position": [0, 551, stack_z],
                    "rotation": [0, HALF_PI, 0],
                },
                {
                    "action": "moveTo",
                    "target": "AMR",
                    "position": [amr_dx, 0, stack_z],
                    "rotation": [0, -HALF_PI, 0],
                },
            ],
        },
        "grip": {
            "on": {"goLift": "lift"},
            "entry": [
                {"action": "moveTo", "target": "TG.Jaw1", "position": [62, -60, 0]},
                {"action": "moveTo", "target": "TG.Jaw2", "position": [-62, -60, 0]},
            ],
        },
        "lift": {
            "on": {"goUndock": "undock"},
            "entry": [
                {
                    "action": "moveTo",
                    "target": "TG",
                    "position": [0, 551, stack_z],
                    "rotation": [0, HALF_PI, 0],
                }
            ],
        },
        "undock": {
            "on": {"goAisleOut": "aisleOut"},
            "entry": [
                {
                    "action": "moveTo",
                    "target": "TG",
                    "position": [-400, 551, stack_z],
                    "rotation": [0, HALF_PI, 0],
                },
                {
                    "action": "moveTo",
                    "target": "AMR",
                    "position": [-400 + amr_dx, 0, stack_z],
                    "rotation": [0, -HALF_PI, 0],
                },
            ],
        },
        "aisleOut": {
            "on": {"goBoxNorth": "boxNorth"},
            "entry": [
                {
                    "action": "moveTo",
                    "target": "TG",
                    "position": [-400, 551, aisle_z],
                    "rotation": [0, HALF_PI, 0],
                },
                {
                    "action": "moveTo",
                    "target": "AMR",
                    "position": [-400 + amr_dx, 0, aisle_z],
                    "rotation": [0, -HALF_PI, 0],
                },
            ],
        },
        "boxNorth": {
            "on": {
                **{f"goBoxSlot{k}": f"boxSlot{k}" for k in range(1, 6)},
                "goAisleIn": "aisleIn",
            },
            "entry": [
                {
                    "action": "moveTo",
                    "target": "TG",
                    "position": [-2200, 551, aisle_z],
                    "rotation": [0, HALF_PI, 0],
                },
                {
                    "action": "moveTo",
                    "target": "AMR",
                    "position": [-2200 + amr_dx, 0, aisle_z],
                    "rotation": [0, -HALF_PI, 0],
                },
            ],
        },
        "aisleIn": {
            "on": {
                "goHome": "home",
                "goPickApproach": "pickApproach",
            },
            "entry": [
                {
                    "action": "moveTo",
                    "target": "TG",
                    "position": [-400, 551, aisle_z],
                    "rotation": [0, HALF_PI, 0],
                },
                {
                    "action": "moveTo",
                    "target": "AMR",
                    "position": [-400 + amr_dx, 0, aisle_z],
                    "rotation": [0, -HALF_PI, 0],
                },
            ],
        },
    }

    for k, ty in TOTE_Y.items():
        states[f"down{k}"] = {
            "on": {"goGrip": "grip"},
            "entry": [
                {
                    "action": "moveTo",
                    "target": "TG",
                    "position": [0, ty + 120, stack_z],
                    "rotation": [0, HALF_PI, 0],
                }
            ],
        }

    for k, (sz, low_y) in slot_cfg.items():
        states[f"boxSlot{k}"] = {
            "on": {f"goBoxLower{k}": f"boxLower{k}"},
            "entry": [
                {
                    "action": "moveTo",
                    "target": "TG",
                    "position": [-2200, 551, sz],
                    "rotation": [0, HALF_PI, 0],
                },
                {
                    "action": "moveTo",
                    "target": "AMR",
                    "position": [-2200 + amr_dx, 0, sz],
                    "rotation": [0, -HALF_PI, 0],
                },
            ],
        }
        states[f"boxLower{k}"] = {
            "on": {f"goRelease{k}": f"release{k}"},
            "entry": [
                {
                    "action": "moveTo",
                    "target": "TG",
                    "position": [-2200, low_y, sz],
                    "rotation": [0, HALF_PI, 0],
                }
            ],
        }
        states[f"release{k}"] = {
            "on": {f"goBoxUp{k}": f"boxUp{k}"},
            "entry": [
                {"action": "moveTo", "target": "TG.Jaw1", "position": [90, -60, 0]},
                {"action": "moveTo", "target": "TG.Jaw2", "position": [-90, -60, 0]},
            ],
        }
        states[f"boxUp{k}"] = {
            "on": {"goBoxNorth": "boxNorth"},
            "entry": [
                {
                    "action": "moveTo",
                    "target": "TG",
                    "position": [-2200, 551, sz],
                    "rotation": [0, HALF_PI, 0],
                }
            ],
        }

    return {"id": "TG_SC", "initial": "home", "states": states}


def make_fence(fid, pos, along_x=False):
    rot = [0, HALF_PI, -HALF_PI] if along_x else [0, 0, -HALF_PI]
    return {
        "id": fid,
        "type": "https://w3id.org/ontoeng/factory#Artifact",
        "representations": [{"file": "Grid_second.glb", "unit": 1}],
        "position": pos,
        "rotation": rot,
        "placementRelTo": "building",
        "properties": {
            "mass": 0,
            "restitution": 0.1,
            "friction": 0.5,
            "MotionType": "STATIC",
        },
    }


def build_scene():
    assets = [
        {
            "id": "building",
            "type": "https://standards.buildingsmart.org/IFC/DEV/IFC4/ADD1/OWL#IfcBuilding",
        },
        {
            "id": "FactoryFloor",
            "type": "https://w3id.org/ontoeng/factory#Artifact",
            "representations": [{"file": "FactoryFloor.glb", "unit": 1}],
            "position": [0, 0, 0],
            "rotation": [0, 0, 0],
            "placementRelTo": "building",
        },
        {
            "id": "FactoryWalls",
            "type": "https://w3id.org/ontoeng/factory#Artifact",
            "representations": [{"file": "FactoryWalls.glb", "unit": 1}],
            "position": [0, 0, 0],
            "rotation": [0, 0, 0],
            "placementRelTo": "building",
        },
        {
            "id": "B1",
            "type": "https://w3id.org/ontoeng/factory#Conveyor",
            "representations": [{"file": "ConveyorNew.glb", "unit": 1}],
            "position": [0, 0, 0],
            "rotation": [0, 0, 0],
            "placementRelTo": "building",
            "properties": {
                "mass": 0,
                "restitution": 0.3,
                "friction": 0.0,
                "MotionType": "ANIMATED",
            },
            "statechart": {
                "id": "B1_SC",
                "initial": "idle",
                "states": {
                    "idle": {
                        "on": {"B1startF": "forward", "B1startB": "backward"},
                        "entry": {"action": "surfaceVelocity", "target": "B1", "velocity": [0, 0, 0]},
                    },
                    "forward": {
                        "on": {"B1stop": "idle"},
                        "entry": {"action": "surfaceVelocity", "target": "B1", "velocity": [0, 0, 80]},
                    },
                    "backward": {
                        "on": {"B1stop": "idle"},
                        "entry": {"action": "surfaceVelocity", "target": "B1", "velocity": [0, 0, -80]},
                    },
                },
            },
        },
        {
            "id": "Stopper_B1",
            "type": "https://w3id.org/ontoeng/factory#Actuator",
            "representations": [{"file": "Stopper.glb", "unit": 1}],
            "position": [-77.5, 230, 1005],
            "rotation": [0, 0, 0],
            "placementRelTo": "building",
            "properties": {
                "mass": 0,
                "restitution": 0.1,
                "friction": 0.5,
                "MotionType": "STATIC",
            },
        },
        {
            "id": "Sensor_B1",
            "type": "https://w3id.org/ontoeng/factory#SensorBarrier",
            "representations": [{"file": "Sensor.glb", "unit": 1}],
            "position": [-65, 245, 976],
            "rotation": [0, 0, -HALF_PI],
            "placementRelTo": "building",
        },
    ]

    # Static 4 mm floor staging pad providing solid Havok support at Z=STACK_Z (since env ground has no collider)
    assets.append(
        {
            "id": "TotePad",
            "type": "https://w3id.org/ontoeng/factory#Artifact",
            "representations": [{"file": "FloorPad.glb", "unit": 1}],
            "position": [0, 0, STACK_Z],
            "rotation": [0, 0, 0],
            "placementRelTo": "building",
            "properties": {
                "mass": 0,
                "restitution": 0.0,
                "friction": 0.9,
                "MotionType": "STATIC",
            },
        }
    )

    # Spawn bottom-up in asset order (Tote5 floor -> Tote1 top)
    for k in [5, 4, 3, 2, 1]:
        assets.extend(make_tote_and_clamps(f"Tote{k}", TOTE_SPAWN_Y[k]))

    part_frictions = [
        ("part_01", -900, 0.95),
        ("part_02", -700, 0.95),
        ("part_03", -500, 0.95),
        ("part_04", -300, 0.96),
        ("part_05", -100, 0.97),
        ("part_06", 100, 0.98),
        ("part_07", 300, 0.99),
        ("part_08", 500, 0.1),
        ("part_09", 700, 0.101),
        ("part_10", 900, 0.95),
    ]
    for pid, z_p, fric in part_frictions:
        assets.append(
            {
                "id": pid,
                "type": "https://w3id.org/ontoeng/factory#Artifact",
                "representations": [{"file": "Part.glb", "unit": 1}],
                "position": [0, 230, z_p],
                "rotation": [0, 0, 0],
                "placementRelTo": "building",
                "properties": {"mass": 1, "restitution": 0.1, "friction": fric},
            }
        )

    assets.extend(
        [
            {
                "id": "PP",
                "type": "https://w3id.org/ontoeng/factory#Robot",
                "representations": [{"file": "Pick_and_Place_Robot.glb", "unit": 1}],
                "position": [29, 0, PP_Z],
                "rotation": [0, PI, 0],
                "placementRelTo": "building",
                "statechart": make_pp_statechart(),
            },
            {
                "id": "PP.FloatingX",
                "type": "https://w3id.org/ontoeng/factory#RobotArm",
                "representations": [{"file": "Pick_and_Place_Robot.glb#PP_Floating_X", "unit": 1}],
                "placementRelTo": "PP",
                "parentObject": "PP",
            },
            {
                "id": "PP.FloatingZ",
                "type": "https://w3id.org/ontoeng/factory#RobotArm",
                "representations": [{"file": "Pick_and_Place_Robot.glb#PP_Floating_Z", "unit": 1}],
                "placementRelTo": "PP.FloatingX",
                "parentObject": "PP.FloatingX",
            },
            {
                "id": "PP.FloatingY",
                "type": "https://w3id.org/ontoeng/factory#RobotArm",
                "representations": [{"file": "Pick_and_Place_Robot.glb#PP_Floating_Y", "unit": 1}],
                "placementRelTo": "PP.FloatingZ",
                "parentObject": "PP.FloatingZ",
            },
            {
                "id": "PP.Gripper",
                "type": "https://w3id.org/ontoeng/factory#JawGripper",
                "representations": [{"file": "Pick_and_Place_Robot.glb#PP_Gripper", "unit": 1}],
                "placementRelTo": "PP.FloatingY",
                "parentObject": "PP.FloatingY",
            },
            {
                "id": "PP.Finger1",
                "type": "https://w3id.org/ontoeng/factory#JawFinger",
                "representations": [{"file": "Pick_and_Place_Robot.glb#PP_Finger1", "unit": 1}],
                "placementRelTo": "PP.Gripper",
                "parentObject": "PP.Gripper",
                "properties": {
                    "mass": 0,
                    "restitution": 0.0,
                    "friction": 0.0,
                    "MotionType": "ANIMATED",
                    "isTrigger": True,
                },
            },
            {
                "id": "PP.Finger2",
                "type": "https://w3id.org/ontoeng/factory#JawFinger",
                "representations": [{"file": "Pick_and_Place_Robot.glb#PP_Finger2", "unit": 1}],
                "placementRelTo": "PP.Gripper",
                "parentObject": "PP.Gripper",
                "properties": {
                    "mass": 0,
                    "restitution": 0.0,
                    "friction": 0.0,
                    "MotionType": "ANIMATED",
                    "isTrigger": True,
                },
            },
            {
                "id": "AMR",
                "type": "https://w3id.org/ontoeng/factory#Robot",
                "representations": [{"file": "AMR.glb", "unit": 1}],
                "position": [-870, 0, STACK_Z],
                "rotation": [0, -HALF_PI, 0],
                "placementRelTo": "building",
            },
            {
                "id": "TG",
                "type": "https://w3id.org/ontoeng/factory#JawGripper",
                "representations": [{"file": "ToteGripper.glb", "unit": 1}],
                "position": [-400, 551, STACK_Z],
                "rotation": [0, HALF_PI, 0],
                "placementRelTo": "building",
                "statechart": make_tg_statechart(),
            },
            {
                "id": "TG.Jaw1",
                "type": "https://w3id.org/ontoeng/factory#JawFinger",
                "representations": [{"file": "ToteGripper.glb#TG_Jaw1", "unit": 1}],
                "position": [90, -60, 0],
                "placementRelTo": "TG",
                "parentObject": "TG",
                "properties": {
                    "mass": 0,
                    "restitution": 0.0,
                    "friction": 0.0,
                    "MotionType": "ANIMATED",
                    "isTrigger": True,
                },
            },
            {
                "id": "TG.Jaw2",
                "type": "https://w3id.org/ontoeng/factory#JawFinger",
                "representations": [{"file": "ToteGripper.glb#TG_Jaw2", "unit": 1}],
                "position": [-90, -60, 0],
                "placementRelTo": "TG",
                "parentObject": "TG",
                "properties": {
                    "mass": 0,
                    "restitution": 0.0,
                    "friction": 0.0,
                    "MotionType": "ANIMATED",
                    "isTrigger": True,
                },
            },
            {
                "id": "Grid",
                "type": "https://w3id.org/ontoeng/factory#Artifact",
                "representations": [{"file": "Grid.glb", "unit": 1}],
                "position": [-2000, 540, 1100],
                "rotation": [0, 0, -HALF_PI],
                "placementRelTo": "building",
                "properties": {
                    "mass": 0,
                    "restitution": 0.3,
                    "friction": 0.0,
                    "MotionType": "ANIMATED",
                },
            },
            {
                "id": "Box",
                "type": "https://w3id.org/ontoeng/factory#Artifact",
                "representations": [{"file": "Box_large.glb", "unit": 1}],
                "position": [-2200, 0, 1100],
                "rotation": [0, 0, 0],
                "placementRelTo": "building",
                "properties": {
                    "mass": 0,
                    "restitution": 0.3,
                    "friction": 0.0,
                    "MotionType": "ANIMATED",
                },
            },
            # Safety cage around PP + cable chain (X=225..1135, Z=420..1410)
            make_fence("Fence_S1", [555, 540, 420], along_x=True),
            make_fence("Fence_S2", [805, 540, 420], along_x=True),
            make_fence("Fence_E1", [1135, 540, 750], along_x=False),
            make_fence("Fence_E2", [1135, 540, 1080], along_x=False),
            make_fence("Fence_N1", [555, 540, 1410], along_x=True),
            make_fence("Fence_N2", [805, 540, 1410], along_x=True),
            {
                "id": "SignalPole",
                "type": "https://w3id.org/ontoeng/factory#Actuator",
                "representations": [{"file": "SignalPole.glb", "unit": 1}],
                "position": [1150, 0, 420],
                "rotation": [-HALF_PI, 0, 0],
                "placementRelTo": "building",
            },
        ]
    )

    scene_ids = [a["id"] for a in assets]
    return {
        "context": {
            "UnitOfMeasureScale": 0.001,
            "Zup": False,
            "RepoPath": "https://mihamoscow.github.io/DF-DFE01/assets/",
        },
        "scene": scene_ids,
        "assets": assets,
    }


def build_anim():
    events = []

    def add(ts_ms, target, ev):
        assert ts_ms % 100 == 0, f"Timestamp {ts_ms} must be multiple of 100ms"
        events.append((ts_ms, target, ev))

    # Proportional vertical travel durations for PP FloatingY (-40 -> -157..-397) and TG (551 -> 360..120)
    pp_vert_ms = {1: 1500, 2: 2000, 3: 2500, 4: 3000, 5: 3500}
    tg_down_ms = {1: 2000, 2: 2400, 3: 2800, 4: 3200, 5: 3600}

    # --- Advance part_10 into Stopper_B1 (Z=1005 -> part Z=970) ---
    add(1000, "B1", "B1startF")
    add(2200, "B1", "B1stop")

    t_pp = 2700
    t_tg_free = 0
    total_parts_fed = 1  # part_10 is already at Stopper_B1

    for k in range(1, 6):
        v_ms = pp_vert_ms[k]
        for slot in (1, 2):
            add(t_pp, "PP", "goPick")
            add(t_pp + 3000, "PP", "goLift")
            add(t_pp + 4500, "PP", f"goPlace{slot}")
            if total_parts_fed < 10:
                b_dur = 2600 if total_parts_fed in (1, 2) else 2500
                add(t_pp + 4500, "B1", "B1startF")
                add(t_pp + 4500 + b_dur, "B1", "B1stop")
                total_parts_fed += 1
            t_low = t_pp + 7500
            add(t_low, "PP", f"goLower{k}")
            t_rel = t_low + v_ms
            add(t_rel, "PP", "goRelease")
            add(t_rel + 1500, f"Tote{k}.C{slot}", "clamp")
            add(t_rel + 2500, "PP", "goUp")
            t_rest = t_rel + 2500 + v_ms
            add(t_rest, "PP", "goRest")
            t_pp = t_rest + 3000

        # Tote k is packed and PP is back at rest over B1 -> TG picks Tote k from stack [0, y, 1080]
        t_tg = max(t_pp, t_tg_free + 500)
        if k == 1:
            add(t_tg, "TG", "goDock")
            t_cur = t_tg + 2200
        else:
            add(t_tg, "TG", "goPickApproach")
            add(t_tg + 2200, "TG", "goDock")
            t_cur = t_tg + 4400

        d_ms = tg_down_ms[k]
        add(t_cur, "TG", f"goDown{k}")
        add(t_cur + d_ms, "TG", "goGrip")
        add(t_cur + d_ms + 1800, "TG", "goLift")
        t_undock = t_cur + d_ms + 4000
        add(t_undock, "TG", "goUndock")
        t_aisle = t_undock + 2200
        add(t_aisle, "TG", "goAisleOut")

        # Delivery to Box while next Tote k+1 is exposed!
        t_north = t_aisle + 3500
        add(t_north, "TG", "goBoxNorth")
        t_slot = t_north + 6800
        add(t_slot, "TG", f"goBoxSlot{k}")
        slot_dur = {1: 4200, 2: 3500, 3: 4200, 4: 3500, 5: 4200}[k]
        t_lower = t_slot + slot_dur
        add(t_lower, "TG", f"goBoxLower{k}")
        t_rel_tg = t_lower + 3200
        add(t_rel_tg, "TG", f"goRelease{k}")
        t_up_tg = t_rel_tg + 1500
        add(t_up_tg, "TG", f"goBoxUp{k}")
        t_ret_n = t_up_tg + 2500
        add(t_ret_n, "TG", "goBoxNorth")
        t_ain = t_ret_n + slot_dur
        add(t_ain, "TG", "goAisleIn")
        t_tg_free = t_ain + 6500
        if k == 5:
            add(t_tg_free, "TG", "goHome")
            t_tg_free += 3500

        # Wait until TG + Tote k have backed out and started north before starting PP on Tote k+1
        t_pp = t_aisle + 1500

    events.sort(key=lambda x: x[0])
    nodes = [
        {
            "id": target,
            "actions": [
                {
                    "trigger": {"type": "timestamp", "data": str(ts)},
                    "event": {"type": "sendEvent", "data": ev},
                }
            ],
        }
        for ts, target, ev in events
    ]
    return {
        "context": {
            "assetTrail": False,
            "UnitOfMeasureScale": 0.001,
            "Zup": False,
            "RepoAnim": "",
        },
        "nodes": nodes,
        "sequences": [],
        "bookmarks": [],
    }


if __name__ == "__main__":
    scene = build_scene()
    anim = build_anim()
    compact_num_array = re.compile(r"\[\n\s+([^\[\]\{\}]+?)\n\s+\]", re.DOTALL)

    def dump_pretty(obj):
        text = json.dumps(obj, indent=2)
        def repl(m):
            items = [x.strip() for x in m.group(1).split(",")]
            if len(items) <= 4 and all(len(x) < 24 for x in items):
                return "[" + ", ".join(items) + "]"
            return m.group(0)
        return compact_num_array.sub(repl, text)

    scratch = "/Users/mi_sha/.gemini/antigravity/brain/092a3012-2695-43dd-be95-bc9c4d34456e/scratch"
    model_dir = "/Users/mi_sha/Documents/21. PoliMI Studies/2. Courses/2026/7_Digital factory/3_Project/02_model"
    for d in [scratch, model_dir]:
        with open(f"{d}/DFE_01.json", "w", encoding="utf-8") as f:
            f.write(dump_pretty(scene))
        with open(f"{d}/DFE_01_anim.json", "w", encoding="utf-8") as f:
            f.write(dump_pretty(anim))

    # Validate statechart transitions
    sc_map = {}
    state_map = {}
    for a in scene["assets"]:
        if "statechart" in a:
            sc_map[a["id"]] = a["statechart"]["states"]
            state_map[a["id"]] = a["statechart"]["initial"]

    for n in anim["nodes"]:
        aid = n["id"]
        ev = n["actions"][0]["event"]["data"]
        ts = int(n["actions"][0]["trigger"]["data"])
        cur = state_map[aid]
        transitions = sc_map[aid][cur].get("on", {})
        assert ev in transitions, f"INVALID transition at {ts}ms: {aid} in '{cur}' has no '{ev}'"
        state_map[aid] = transitions[ev]

    last_ts = int(anim["nodes"][-1]["actions"][0]["trigger"]["data"])
    print(f"Built {len(scene['assets'])} assets and {len(anim['nodes'])} anim events (end={last_ts/1000:.1f}s)")
    print("Statechart validation PASSED: 0 dropped events!")
    print("Final states:", {k: v for k, v in state_map.items() if k in ("B1", "PP", "TG")})
