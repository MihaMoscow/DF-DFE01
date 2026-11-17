import json
import os
import struct

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root (tools/..)


def build_box_glb(dx, dy, dz, rgba=(0.25, 0.27, 0.30, 1.0)):
    """Build a valid binary GLB for a single axis-aligned box spanning:
    X in [-dx/2, dx/2], Y in [0, dy], Z in [-dz/2, dz/2] (in metres, i.e. unit=1 in mm scene).
    """
    hx, y0, y1, hz = dx / 2.0, 0.0, dy, dz / 2.0
    # 24 vertices (4 per face for crisp flat normals)
    faces = [
        # +Y (top)
        ((-hx, y1, -hz), (-hx, y1, hz), (hx, y1, hz), (hx, y1, -hz), (0, 1, 0)),
        # -Y (bottom)
        ((-hx, y0, hz), (-hx, y0, -hz), (hx, y0, -hz), (hx, y0, hz), (0, -1, 0)),
        # +X
        ((hx, y0, -hz), (hx, y1, -hz), (hx, y1, hz), (hx, y0, hz), (1, 0, 0)),
        # -X
        ((-hx, y0, hz), (-hx, y1, hz), (-hx, y1, -hz), (-hx, y0, -hz), (-1, 0, 0)),
        # +Z
        ((-hx, y0, hz), (hx, y0, hz), (hx, y1, hz), (-hx, y1, hz), (0, 0, 1)),
        # -Z
        ((hx, y0, -hz), (-hx, y0, -hz), (-hx, y1, -hz), (hx, y1, -hz), (0, 0, -1)),
    ]
    positions = []
    normals = []
    indices = []
    for f_idx, (v0, v1, v2, v3, n) in enumerate(faces):
        base = f_idx * 4
        positions.extend([v0, v1, v2, v3])
        normals.extend([n, n, n, n])
        indices.extend([base, base + 1, base + 2, base, base + 2, base + 3])

    pos_bytes = b"".join(struct.pack("<3f", *v) for v in positions)
    norm_bytes = b"".join(struct.pack("<3f", *n) for n in normals)
    idx_bytes = b"".join(struct.pack("<H", i) for i in indices)

    bin_blob = pos_bytes + norm_bytes + idx_bytes
    while len(bin_blob) % 4 != 0:
        bin_blob += b"\x00"

    gltf = {
        "asset": {"version": "2.0", "generator": "dfe01_make_floor_pad"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": "FloorPad_Body", "mesh": 0}],
        "meshes": [
            {
                "name": "FloorPad_Geom",
                "primitives": [
                    {
                        "attributes": {"POSITION": 0, "NORMAL": 1},
                        "indices": 2,
                        "material": 0,
                    }
                ],
            }
        ],
        "materials": [
            {
                "name": "SteelMat",
                "pbrMetallicRoughness": {
                    "baseColorFactor": list(rgba),
                    "metallicFactor": 0.3,
                    "roughnessFactor": 0.7,
                },
            }
        ],
        "buffers": [{"byteLength": len(bin_blob)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(pos_bytes), "target": 34962},
            {"buffer": 0, "byteOffset": len(pos_bytes), "byteLength": len(norm_bytes), "target": 34962},
            {"buffer": 0, "byteOffset": len(pos_bytes) + len(norm_bytes), "byteLength": len(idx_bytes), "target": 34963},
        ],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,
                "count": len(positions),
                "type": "VEC3",
                "min": [-hx, y0, -hz],
                "max": [hx, y1, hz],
            },
            {
                "bufferView": 1,
                "componentType": 5126,
                "count": len(normals),
                "type": "VEC3",
            },
            {
                "bufferView": 2,
                "componentType": 5123,
                "count": len(indices),
                "type": "SCALAR",
            },
        ],
    }

    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    while len(json_bytes) % 4 != 0:
        json_bytes += b" "

    total_len = 12 + 8 + len(json_bytes) + 8 + len(bin_blob)
    header = struct.pack("<3I", 0x46546C67, 2, total_len)
    chunk0 = struct.pack("<2I", len(json_bytes), 0x4E4F534A) + json_bytes
    chunk1 = struct.pack("<2I", len(bin_blob), 0x004E4942) + bin_blob
    return header + chunk0 + chunk1


if __name__ == "__main__":
    # 240 mm x 4 mm x 136 mm in metres (unit=1 in VEB.js mm scene)
    glb = build_box_glb(0.240, 0.004, 0.136)
    out = os.path.join(REPO_DIR, "assets", "FloorPad.glb")
    with open(out, "wb") as f:
        f.write(glb)
    print(f"Wrote {out} ({len(glb)} bytes)")
