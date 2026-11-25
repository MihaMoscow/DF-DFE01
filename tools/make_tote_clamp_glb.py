#!/usr/bin/env python3
"""Generate assets/ToteClamp.glb - the transport clamp mounted inside each tote.

The file contains three named nodes (geometry in metres, unit = 1 in the mm scene):
  TC_Body  - small 10 x 5 x 10 mm mounting block (visual parent of the clamp)
  TC_Jaw1  - jaw, 10 x 25 x 40 mm box centred on its origin
  TC_Jaw2  - identical second jaw

In DFE_01.json each clamp loads the whole file as a JawGripper and the two jaws
as `ToteClamp.glb#TC_Jaw1` / `#TC_Jaw2` (JawFinger, isTrigger). The jaws must stay
single meshes with one primitive each, otherwise Babylon.js splits them and the
trigger-based gripping does not fire. Jaw positions (+-47 mm open, +-27 mm closed)
are set in the scene and the StateChart, not here.

Usage:  python3 tools/make_tote_clamp_glb.py [output.glb]
"""
import json
import os
import struct
import sys

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root (tools/..)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO_DIR, "assets", "ToteClamp.glb")

# Box corners in the order (-,-,-), (-,-,+), (-,+,-), (-,+,+), (+,-,-), (+,-,+), (+,+,-), (+,+,+)
# and 12 outward-facing triangles (counter-clockwise).
BOX_FACES = [1, 3, 0, 4, 1, 0, 0, 3, 2, 2, 4, 0, 1, 7, 3, 5, 1, 4,
             5, 7, 1, 3, 7, 2, 6, 4, 2, 2, 7, 6, 6, 5, 4, 7, 5, 6]


def box_corners(ex, ey, ez):
    hx, hy, hz = ex / 2, ey / 2, ez / 2
    return [(sx * hx, sy * hy, sz * hz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]


def f32(v):
    return struct.unpack("<f", struct.pack("<f", v))[0]


def build():
    body = box_corners(0.010, 0.005, 0.010)   # mounting block
    jaw = box_corners(0.010, 0.025, 0.040)    # jaw (shared by TC_Jaw1 and TC_Jaw2)
    body_rgba, jaw_rgba = (60, 60, 60, 255), (30, 140, 220, 255)  # dark grey, blue

    chunks = [
        b"".join(struct.pack("<I", i) for i in BOX_FACES),                 # 0 indices
        b"".join(struct.pack("<3f", *v) for v in body),                    # 1 body positions
        bytes(body_rgba) * 8,                                              # 2 body colours
        b"".join(struct.pack("<3f", *v) for v in jaw),                     # 3 jaw positions
        bytes(jaw_rgba) * 8,                                               # 4 jaw colours
    ]
    views, off = [], 0
    for c in chunks:
        views.append({"buffer": 0, "byteOffset": off, "byteLength": len(c)})
        off += len(c)
    binary = b"".join(chunks)

    def pos_acc(view, verts):
        return {"componentType": 5126, "type": "VEC3", "byteOffset": 0, "bufferView": view, "count": 8,
                "max": [f32(max(v[i] for v in verts)) for i in range(3)],
                "min": [f32(min(v[i] for v in verts)) for i in range(3)]}

    def col_acc(view, rgba):
        return {"componentType": 5121, "normalized": True, "type": "VEC4", "byteOffset": 0,
                "bufferView": view, "count": 8, "max": list(rgba), "min": list(rgba)}

    def mesh(name, extents, pos, col):
        return {"name": name, "extras": {"shape": "box", "extents": extents},
                "primitives": [{"attributes": {"POSITION": pos, "COLOR_0": col}, "indices": 0, "mode": 4}]}

    gltf = {
        "scene": 0,
        "scenes": [{"nodes": [0, 1, 2]}],
        "asset": {"version": "2.0", "generator": "DFE_01 tools/make_tote_clamp_glb.py"},
        "accessors": [
            {"componentType": 5125, "type": "SCALAR", "bufferView": 0, "count": len(BOX_FACES),
             "max": [7], "min": [0]},
            pos_acc(1, body), col_acc(2, body_rgba), pos_acc(3, jaw), col_acc(4, jaw_rgba),
        ],
        "meshes": [
            mesh("TC_Body_geom", [0.01, 0.005, 0.01], 1, 2),
            mesh("TC_Jaw1_geom", [0.01, 0.025, 0.04], 3, 4),
            mesh("TC_Jaw2_geom", [0.01, 0.025, 0.04], 3, 4),
        ],
        "nodes": [{"name": "TC_Body", "mesh": 0}, {"name": "TC_Jaw1", "mesh": 1}, {"name": "TC_Jaw2", "mesh": 2}],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": views,
    }
    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    binary += b"\x00" * (-len(binary) % 4)
    total = 12 + 8 + len(js) + 8 + len(binary)
    return (struct.pack("<4sII", b"glTF", 2, total) + struct.pack("<I4s", len(js), b"JSON") + js
            + struct.pack("<I4s", len(binary), b"BIN\x00") + binary)


if __name__ == "__main__":
    data = build()
    with open(OUT, "wb") as f:
        f.write(data)
    print(f"Wrote {OUT} ({len(data)} bytes)")
