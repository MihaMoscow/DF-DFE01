#!/usr/bin/env python3
"""Fix Pick_and_Place_Robot.glb so PP_Floating_X has identity rotation [0,0,0,1].

Previously, node 60 (PP_Floating_X) carried a -90 deg Y-rotation [0, -0.7071068, 0, 0.7071067].
Because VEB.js moveTo resets node rotation to [0,0,0], moving PP.FloatingX broke the robot's
orientation, forcing PP.FloatingZ to slide sideways off the stationary rail/cable slider.

This script moves the -90 deg Y-rotation down into the visual child nodes:
- PP_Floating_X_Bodies (7)
- PP_Floating_Z_Bodies (58)
- PP_Floating_Y_Bodies (22)
- PP_Gripper (25) (with its translation rotated -90 deg around Y)
- PP_Floating_Z (59) & PP_Floating_Y (26) default translations rotated -90 deg around Y
leaving PP_Floating_X (60) and PP_Floating_Z (59) and PP_Floating_Y (26) with identity rotation.
"""

import json
import os
import struct

GLB_PATH = "/Users/mi_sha/Documents/21. PoliMI Studies/2. Courses/2026/7_Digital factory/3_Project/02_model/assets/Pick_and_Place_Robot.glb"
Q_M90_Y = [0.0, -0.7071068286895752, 0.0, 0.7071067094802856]


def rot_m90_y(v):
    """Rotate [x, y, z] by -90 deg around +Y: (-z, y, x)."""
    return [-v[2], v[1], v[0]]


def main():
    with open(GLB_PATH, "rb") as f:
        data = f.read()

    magic, version, total_len = struct.unpack_from("<4sII", data, 0)
    assert magic == b"glTF" and version == 2
    c0_len, c0_type = struct.unpack_from("<I4s", data, 12)
    assert c0_type == b"JSON"
    gltf = json.loads(data[20 : 20 + c0_len].decode("utf-8"))
    bin_chunk = data[20 + c0_len :]  # preserve BIN chunk byte-for-byte

    nodes = {n["name"]: n for n in gltf["nodes"] if "name" in n}

    # Check original state
    n_fx = nodes["PP_Floating_X"]
    assert "rotation" in n_fx, "PP_Floating_X already has no rotation!"

    # 1. Remove rotation from PP_Floating_X
    del n_fx["rotation"]

    # 2. Add -90 deg Y rotation to visual body containers & PP_Gripper
    for name in ["PP_Floating_X_Bodies", "PP_Floating_Z_Bodies", "PP_Floating_Y_Bodies", "PP_Gripper"]:
        assert "rotation" not in nodes[name], f"{name} unexpectedly had rotation"
        nodes[name]["rotation"] = list(Q_M90_Y)

    # 3. Rotate translations of PP_Floating_Z, PP_Floating_Y, PP_Gripper by -90 deg around Y
    for name in ["PP_Floating_Z", "PP_Floating_Y", "PP_Gripper"]:
        t = nodes[name]["translation"]
        nodes[name]["translation"] = rot_m90_y(t)

    # Rebuild GLB
    j_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    while len(j_bytes) % 4 != 0:
        j_bytes += b" "

    new_total = 12 + 8 + len(j_bytes) + len(bin_chunk)
    header = struct.pack("<4sII", b"glTF", 2, new_total)
    c0_hdr = struct.pack("<I4s", len(j_bytes), b"JSON")

    with open(GLB_PATH, "wb") as f:
        f.write(header + c0_hdr + j_bytes + bin_chunk)

    print(f"Updated {GLB_PATH} ({total_len} -> {new_total} bytes)")
    for name in ["PP_Floating_X", "PP_Floating_X_Bodies", "PP_Floating_Z", "PP_Floating_Y", "PP_Gripper"]:
        print(" ", name, "-> trans:", nodes[name].get("translation"), "rot:", nodes[name].get("rotation"))


if __name__ == "__main__":
    main()
