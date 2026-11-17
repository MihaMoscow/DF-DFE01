#!/usr/bin/env python3
"""Generate a compact ASRS / ACR-inspired industrial AMR.glb and ToteGripper.glb (Direction A).

Design language (inspired by compact workstation ACRs, original parametric geometry):
- Rounded-stadium autonomous drive base with wheels tucked inside recessed wells (no exposed toy axles)
- Flush gloss-black 2D LiDAR optical visor band + thin recessed status LED strip
- Tapered enclosed vertical ASRS column fairing (light-grey composite + gunmetal + safety-yellow accents)
- Open front brushed-aluminum linear guideway & central ball-screw drive
- Matching ToteGripper.glb with sliding carriage inside the linear track + tapered cantilever arm
- Single-primitive TG_Jaw1 & TG_Jaw2 preserving exact Havok isTrigger bounds
"""

import json
import math
import os
import struct

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root (tools/..)
ASSETS_DIR = os.path.join(REPO_DIR, "assets")


def build_glb(gltf_dict, bin_blob):
    while len(bin_blob) % 4 != 0:
        bin_blob += b"\x00"
    j_bytes = json.dumps(gltf_dict, separators=(",", ":")).encode("utf-8")
    while len(j_bytes) % 4 != 0:
        j_bytes += b" "
    total_len = 12 + 8 + len(j_bytes) + 8 + len(bin_blob)
    header = struct.pack("<4sII", b"glTF", 2, total_len)
    c0_hdr = struct.pack("<I4s", len(j_bytes), b"JSON")
    c1_hdr = struct.pack("<I4s", len(bin_blob), b"BIN\x00")
    return header + c0_hdr + j_bytes + c1_hdr + bin_blob


def rounded_rect_poly(x0, z0, x1, z1, r, arc_segs=5):
    """Return CCW 2D polygon [(x, z), ...] for a rounded rectangle / stadium in XZ."""
    r = min(r, 0.48 * (x1 - x0), 0.48 * (z1 - z0))
    pts = []
    corners = [
        (x1 - r, z1 - r, 0.0, 0.5 * math.pi),
        (x0 + r, z1 - r, 0.5 * math.pi, math.pi),
        (x0 + r, z0 + r, math.pi, 1.5 * math.pi),
        (x1 - r, z0 + r, 1.5 * math.pi, 2.0 * math.pi),
    ]
    for cx, cz, a_start, a_end in corners:
        for i in range(arc_segs + 1):
            a = a_start + (a_end - a_start) * (i / arc_segs)
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


def normalize3(v):
    l = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    return (v[0] / l, v[1] / l, v[2] / l) if l > 1e-9 else (0.0, 1.0, 0.0)


def cross3(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def add_lofted_prism(prims, mat_idx, poly0, y0, poly1, y1, cap_bottom=True, cap_top=True):
    assert len(poly0) == len(poly1)
    n_pts = len(poly0)
    d = prims[mat_idx]

    for i in range(n_pts):
        j = (i + 1) % n_pts
        p00 = (poly0[i][0], y0, poly0[i][1])
        p10 = (poly0[j][0], y0, poly0[j][1])
        p11 = (poly1[j][0], y1, poly1[j][1])
        p01 = (poly1[i][0], y1, poly1[i][1])
        e1 = (p10[0] - p00[0], p10[1] - p00[1], p10[2] - p00[2])
        e2 = (p01[0] - p00[0], p01[1] - p00[1], p01[2] - p00[2])
        n = normalize3(cross3(e2, e1))
        s = len(d["pos"])
        d["pos"].extend([p00, p10, p11, p01])
        d["norm"].extend([n, n, n, n])
        d["idx"].extend([s, s + 1, s + 2, s, s + 2, s + 3])

    if cap_top:
        cx = sum(p[0] for p in poly1) / n_pts
        cz = sum(p[1] for p in poly1) / n_pts
        c_idx = len(d["pos"])
        d["pos"].append((cx, y1, cz))
        d["norm"].append((0.0, 1.0, 0.0))
        r_start = len(d["pos"])
        for p in poly1:
            d["pos"].append((p[0], y1, p[1]))
            d["norm"].append((0.0, 1.0, 0.0))
        for i in range(n_pts):
            j = (i + 1) % n_pts
            d["idx"].extend([c_idx, r_start + j, r_start + i])

    if cap_bottom:
        cx = sum(p[0] for p in poly0) / n_pts
        cz = sum(p[1] for p in poly0) / n_pts
        c_idx = len(d["pos"])
        d["pos"].append((cx, y0, cz))
        d["norm"].append((0.0, -1.0, 0.0))
        r_start = len(d["pos"])
        for p in poly0:
            d["pos"].append((p[0], y0, p[1]))
            d["norm"].append((0.0, -1.0, 0.0))
        for i in range(n_pts):
            j = (i + 1) % n_pts
            d["idx"].extend([c_idx, r_start + i, r_start + j])


def add_box(prims, mat_idx, x0, y0, z0, x1, y1, z1):
    d = prims[mat_idx]
    b = len(d["pos"])
    faces = [
        ((x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (0, 1, 0)),
        ((x0, y0, z1), (x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (0, -1, 0)),
        ((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1), (1, 0, 0)),
        ((x0, y0, z1), (x0, y1, z1), (x0, y1, z0), (x0, y0, z0), (-1, 0, 0)),
        ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1), (0, 0, 1)),
        ((x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (0, 0, -1)),
    ]
    for f_i, (v0, v1, v2, v3, n) in enumerate(faces):
        s = b + f_i * 4
        d["pos"].extend([v0, v1, v2, v3])
        d["norm"].extend([n, n, n, n])
        d["idx"].extend([s, s + 1, s + 2, s, s + 2, s + 3])


def add_tapered_beam_z(prims, mat_idx, x0, x1, z0, y0_bot, y0_top, z1, y1_bot, y1_top):
    d = prims[mat_idx]
    p = [
        (x0, y0_bot, z0), (x1, y0_bot, z0), (x1, y0_top, z0), (x0, y0_top, z0),
        (x0, y1_bot, z1), (x1, y1_bot, z1), (x1, y1_top, z1), (x0, y1_top, z1),
    ]
    quads = [
        (3, 2, 6, 7),
        (4, 5, 1, 0),
        (1, 5, 6, 2),
        (4, 0, 3, 7),
        (4, 7, 6, 5),
        (0, 1, 2, 3),
    ]
    for i0, i1, i2, i3 in quads:
        v0, v1, v2, v3 = p[i0], p[i1], p[i2], p[i3]
        e1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
        e2 = (v3[0] - v0[0], v3[1] - v0[1], v3[2] - v0[2])
        n = normalize3(cross3(e1, e2))
        s = len(d["pos"])
        d["pos"].extend([v0, v1, v2, v3])
        d["norm"].extend([n, n, n, n])
        d["idx"].extend([s, s + 1, s + 2, s, s + 2, s + 3])


def add_cylinder_x(prims, mat_idx, cx0, cx1, cy, cz, radius, segs=18):
    d = prims[mat_idx]
    for i in range(segs):
        a0 = 2.0 * math.pi * i / segs
        a1 = 2.0 * math.pi * (i + 1) / segs
        am = 0.5 * (a0 + a1)
        y0, z0 = cy + radius * math.cos(a0), cz + radius * math.sin(a0)
        y1, z1 = cy + radius * math.cos(a1), cz + radius * math.sin(a1)
        ny, nz = math.cos(am), math.sin(am)
        s = len(d["pos"])
        d["pos"].extend([(cx0, y0, z0), (cx1, y0, z0), (cx1, y1, z1), (cx0, y1, z1)])
        d["norm"].extend([(0, ny, nz)] * 4)
        d["idx"].extend([s, s + 1, s + 2, s, s + 2, s + 3])
    for cx, nx in [(cx0, -1.0), (cx1, 1.0)]:
        c_idx = len(d["pos"])
        d["pos"].append((cx, cy, cz))
        d["norm"].append((nx, 0.0, 0.0))
        r_start = len(d["pos"])
        for i in range(segs):
            a = 2.0 * math.pi * i / segs
            d["pos"].append((cx, cy + radius * math.cos(a), cz + radius * math.sin(a)))
            d["norm"].append((nx, 0.0, 0.0))
        for i in range(segs):
            nxt = (i + 1) % segs
            if nx > 0:
                d["idx"].extend([c_idx, r_start + nxt, r_start + i])
            else:
                d["idx"].extend([c_idx, r_start + i, r_start + nxt])


def add_cylinder_y(prims, mat_idx, cx, cy0, cy1, cz, radius, segs=16):
    d = prims[mat_idx]
    for i in range(segs):
        a0 = 2.0 * math.pi * i / segs
        a1 = 2.0 * math.pi * (i + 1) / segs
        am = 0.5 * (a0 + a1)
        x0, z0 = cx + radius * math.cos(a0), cz + radius * math.sin(a0)
        x1, z1 = cx + radius * math.cos(a1), cz + radius * math.sin(a1)
        nx, nz = math.cos(am), math.sin(am)
        s = len(d["pos"])
        d["pos"].extend([(x0, cy0, z0), (x0, cy1, z0), (x1, cy1, z1), (x1, cy0, z1)])
        d["norm"].extend([(nx, 0, nz)] * 4)
        d["idx"].extend([s, s + 1, s + 2, s, s + 2, s + 3])
    for cy, ny in [(cy0, -1.0), (cy1, 1.0)]:
        c_idx = len(d["pos"])
        d["pos"].append((cx, cy, cz))
        d["norm"].append((0.0, ny, 0.0))
        r_start = len(d["pos"])
        for i in range(segs):
            a = 2.0 * math.pi * i / segs
            d["pos"].append((cx + radius * math.cos(a), cy, cz + radius * math.sin(a)))
            d["norm"].append((0.0, ny, 0.0))
        for i in range(segs):
            nxt = (i + 1) % segs
            if ny > 0:
                d["idx"].extend([c_idx, r_start + i, r_start + nxt])
            else:
                d["idx"].extend([c_idx, r_start + nxt, r_start + i])


def pack_meshes(meshes_spec, materials):
    bin_chunks = []
    buffer_views = []
    accessors = []
    nodes = []
    meshes = []
    cur_off = 0

    for node_name, mesh_name, prims in meshes_spec:
        gltf_prims = []
        for mat_idx, d in prims.items():
            if not d["pos"]:
                continue
            p_b = b"".join(struct.pack("<3f", *p) for p in d["pos"])
            n_b = b"".join(struct.pack("<3f", *n) for n in d["norm"])
            i_b = b"".join(struct.pack("<H", i) for i in d["idx"])
            while len(i_b) % 4 != 0:
                i_b += b"\x00"

            pv = len(buffer_views)
            buffer_views.append({"buffer": 0, "byteOffset": cur_off, "byteLength": len(p_b), "target": 34962})
            cur_off += len(p_b)
            bin_chunks.append(p_b)

            nv = len(buffer_views)
            buffer_views.append({"buffer": 0, "byteOffset": cur_off, "byteLength": len(n_b), "target": 34962})
            cur_off += len(n_b)
            bin_chunks.append(n_b)

            iv = len(buffer_views)
            buffer_views.append({"buffer": 0, "byteOffset": cur_off, "byteLength": len(i_b), "target": 34963})
            cur_off += len(i_b)
            bin_chunks.append(i_b)

            pa = len(accessors)
            mn = [min(p[k] for p in d["pos"]) for k in range(3)]
            mx = [max(p[k] for p in d["pos"]) for k in range(3)]
            accessors.append({"bufferView": pv, "componentType": 5126, "count": len(d["pos"]), "type": "VEC3", "min": mn, "max": mx})
            na = len(accessors)
            accessors.append({"bufferView": nv, "componentType": 5126, "count": len(d["norm"]), "type": "VEC3"})
            ia = len(accessors)
            accessors.append({"bufferView": iv, "componentType": 5123, "count": len(d["idx"]), "type": "SCALAR"})

            gltf_prims.append({"attributes": {"POSITION": pa, "NORMAL": na}, "indices": ia, "material": mat_idx})

        nodes.append({"name": node_name, "mesh": len(meshes)})
        meshes.append({"name": mesh_name, "primitives": gltf_prims})

    bin_blob = b"".join(bin_chunks)
    gltf = {
        "asset": {"version": "2.0", "generator": "dfe01_compact_asrs_amr_gen"},
        "scenes": [{"nodes": list(range(len(nodes)))}],
        "scene": 0,
        "nodes": nodes,
        "meshes": meshes,
        "materials": materials,
        "buffers": [{"byteLength": len(bin_blob)}],
        "bufferViews": buffer_views,
        "accessors": accessors,
    }
    return build_glb(gltf, bin_blob)


def generate_amr_glb():
    # Realistic OEM robotics material palette:
    # 0: Industrial Light-Grey Composite Shell (~45%)
    # 1: Matte Gunmetal Anthracite Base (~35%)
    # 2: Dark Tire Rubber (tucked wheels)
    # 3: Brushed Aluminum Linear Guideway (~15%)
    # 4: Gloss Black LiDAR Optical Visor
    # 5: Safety Amber-Yellow Accent Trim (~5%)
    # 6: Subtle Cyan-White Operational LED Strip
    materials = [
        {"name": "ShellLightGrey", "pbrMetallicRoughness": {"baseColorFactor": [0.74, 0.76, 0.79, 1.0], "metallicFactor": 0.15, "roughnessFactor": 0.42}},
        {"name": "GunmetalBase", "pbrMetallicRoughness": {"baseColorFactor": [0.14, 0.15, 0.17, 1.0], "metallicFactor": 0.35, "roughnessFactor": 0.52}},
        {"name": "TireRubber", "pbrMetallicRoughness": {"baseColorFactor": [0.05, 0.05, 0.06, 1.0], "metallicFactor": 0.05, "roughnessFactor": 0.88}},
        {"name": "BrushedAluminum", "pbrMetallicRoughness": {"baseColorFactor": [0.64, 0.67, 0.71, 1.0], "metallicFactor": 0.82, "roughnessFactor": 0.26}},
        {"name": "LidarVisorGloss", "pbrMetallicRoughness": {"baseColorFactor": [0.02, 0.03, 0.05, 1.0], "metallicFactor": 0.25, "roughnessFactor": 0.06}},
        {"name": "SafetyAmberTrim", "pbrMetallicRoughness": {"baseColorFactor": [0.90, 0.62, 0.05, 1.0], "metallicFactor": 0.15, "roughnessFactor": 0.35}},
        {"name": "StatusLEDStrip", "pbrMetallicRoughness": {"baseColorFactor": [0.20, 0.80, 0.90, 1.0], "metallicFactor": 0.0, "roughnessFactor": 0.20}, "emissiveFactor": [0.12, 0.40, 0.48]},
    ]

    def new_prims():
        return {i: {"pos": [], "norm": [], "idx": []} for i in range(len(materials))}

    base = new_prims()

    # 1. Tucked-In Autonomous Drive Wheels (underneath skirt at X = ±0.135, completely inside 0.20m half-width!)
    for wx0, wx1 in [(-0.155, -0.115), (0.115, 0.155)]:
        for wz in [-0.150, 0.150]:
            add_cylinder_x(base, 2, wx0, wx1, 0.036, wz, 0.036, segs=18)
            add_cylinder_x(base, 3, wx0 - 0.001, wx1 + 0.001, 0.036, wz, 0.018, segs=12)

    # 2. Lower Rounded-Stadium Autonomous Base Skirt (18 mm ground clearance, Y = 0.018 .. 0.062)
    p_bot = rounded_rect_poly(-0.202, -0.292, 0.202, 0.292, r=0.145, arc_segs=6)
    p_mid = rounded_rect_poly(-0.198, -0.288, 0.198, 0.288, r=0.142, arc_segs=6)
    add_lofted_prism(base, 1, p_bot, 0.018, p_mid, 0.062)

    # 3. Flush Wrap-Around Gloss Black LiDAR Optical Visor (Y = 0.062 .. 0.106)
    p_vis = rounded_rect_poly(-0.193, -0.283, 0.193, 0.283, r=0.138, arc_segs=6)
    add_lofted_prism(base, 4, p_vis, 0.062, p_vis, 0.106, cap_bottom=False, cap_top=False)

    # 4. Thin Recessed Operational LED Status Strip (Y = 0.106 .. 0.113)
    p_led = rounded_rect_poly(-0.195, -0.285, 0.195, 0.285, r=0.140, arc_segs=6)
    add_lofted_prism(base, 6, p_led, 0.106, p_led, 0.113, cap_bottom=False, cap_top=False)

    # 5. Main Light-Grey Base Cowling tapering upward (Y = 0.113 .. 0.195)
    p_cowl0 = rounded_rect_poly(-0.200, -0.290, 0.200, 0.290, r=0.144, arc_segs=6)
    p_cowl1 = rounded_rect_poly(-0.185, -0.275, 0.185, 0.275, r=0.132, arc_segs=6)
    add_lofted_prism(base, 0, p_cowl0, 0.113, p_cowl1, 0.195)

    # 6. Top Deck Gunmetal Cover + Rear Powerpack Cowling (Z = +0.04 .. +0.23, Y = 0.195 .. 0.340)
    p_deck = rounded_rect_poly(-0.176, -0.266, 0.176, 0.266, r=0.125, arc_segs=6)
    add_lofted_prism(base, 1, p_deck, 0.195, p_deck, 0.205)

    p_pwr0 = rounded_rect_poly(-0.145, 0.030, 0.145, 0.245, r=0.060, arc_segs=4)
    p_pwr1 = rounded_rect_poly(-0.130, 0.055, 0.130, 0.215, r=0.050, arc_segs=4)
    add_lofted_prism(base, 1, p_pwr0, 0.205, p_pwr1, 0.325)
    # Safety amber rear bumper trim stripe
    p_trim = rounded_rect_poly(-0.132, 0.053, 0.132, 0.217, r=0.050, arc_segs=4)
    add_lofted_prism(base, 5, p_trim, 0.325, p_trim, 0.338)

    # 7. Enclosed Vertical ASRS / ACR Column (centered behind front linear track at Z = -0.12 m)
    mast = new_prims()
    # Tapered light-grey column fairing (Z = -0.095 .. +0.065, Y = 0.205 .. 0.800)
    p_col0 = rounded_rect_poly(-0.112, -0.095, 0.112, 0.065, r=0.025, arc_segs=4)
    p_col1 = rounded_rect_poly(-0.096, -0.095, 0.096, 0.045, r=0.020, arc_segs=4)
    add_lofted_prism(mast, 0, p_col0, 0.205, p_col1, 0.800)

    # Gunmetal top cap & safety amber accent band on column top (Y = 0.800 .. 0.835)
    p_cap0 = rounded_rect_poly(-0.098, -0.135, 0.098, 0.048, r=0.020, arc_segs=4)
    p_cap1 = rounded_rect_poly(-0.092, -0.130, 0.092, 0.042, r=0.018, arc_segs=4)
    add_lofted_prism(mast, 5, p_cap0, 0.800, p_cap0, 0.812, cap_bottom=True, cap_top=False)
    add_lofted_prism(mast, 1, p_cap0, 0.812, p_cap1, 0.838)

    # Open Front Brushed-Aluminum Linear Guideway Rails (at Z = -0.135 .. -0.095, Y = 0.205 .. 0.800)
    add_box(mast, 3, -0.088, 0.205, -0.135, -0.066, 0.800, -0.095)  # Left aluminum rail
    add_box(mast, 3, 0.066, 0.205, -0.135, 0.088, 0.800, -0.095)    # Right aluminum rail
    add_box(mast, 1, -0.066, 0.205, -0.105, 0.066, 0.800, -0.095)   # Dark inner recess channel
    add_cylinder_y(mast, 3, 0.0, 0.205, 0.800, -0.115, 0.011, segs=12)  # Central ball-screw rod

    glb = pack_meshes(
        [
            ("AMR_Base", "AMR_Base_Geom", base),
            ("AMR_Column", "AMR_Column_Geom", mast),
        ],
        materials,
    )
    out = os.path.join(ASSETS_DIR, "AMR.glb")
    with open(out, "wb") as f:
        f.write(glb)
    print(f"Wrote compact ASRS AMR.glb ({len(glb)} bytes) -> {out}")


def generate_tote_gripper_glb():
    """Build ToteGripper.glb matching the ACR linear guideway (Z = -0.35 m) + single-primitive jaws."""
    materials = [
        {"name": "GunmetalBase", "pbrMetallicRoughness": {"baseColorFactor": [0.14, 0.15, 0.17, 1.0], "metallicFactor": 0.35, "roughnessFactor": 0.52}},
        {"name": "BrushedAluminum", "pbrMetallicRoughness": {"baseColorFactor": [0.64, 0.67, 0.71, 1.0], "metallicFactor": 0.82, "roughnessFactor": 0.26}},
        {"name": "SafetyAmberTrim", "pbrMetallicRoughness": {"baseColorFactor": [0.90, 0.62, 0.05, 1.0], "metallicFactor": 0.15, "roughnessFactor": 0.35}},
    ]

    def new_prims():
        return {i: {"pos": [], "norm": [], "idx": []} for i in range(len(materials))}

    tg_body = new_prims()

    # Gripper head actuator housing centered at [0, 0, 0]
    p_head0 = rounded_rect_poly(-0.110, -0.040, 0.110, 0.040, r=0.012, arc_segs=3)
    p_head1 = rounded_rect_poly(-0.104, -0.036, 0.104, 0.036, r=0.010, arc_segs=3)
    add_lofted_prism(tg_body, 0, p_head0, -0.015, p_head1, 0.020)
    add_box(tg_body, 1, -0.106, -0.018, -0.014, 0.106, -0.015, 0.014)

    # Inverted-L / Goose-Neck Arm so horizontal boom clears Box rim (Y=250 mm) even at lowest drop (Y_TG=138 mm):
    # 1. Vertical drop-neck rising from gripper head [0, 0.020, 0] up to Y = +0.165 m
    add_box(tg_body, 0, -0.022, 0.020, -0.022, 0.022, 0.165, 0.022)
    add_box(tg_body, 1, -0.014, 0.020, -0.026, 0.014, 0.160, 0.026)

    # 2. High horizontal tapered cantilever boom at Y = +0.160 .. +0.215 m (Z = -0.335 .. +0.022)
    #    At Y_TG=138 mm, boom bottom is at 138+160 = 298 mm (+48 mm clear above Box's 250 mm wall!)
    add_tapered_beam_z(tg_body, 0, -0.024, 0.024, -0.335, 0.155, 0.215, 0.022, 0.165, 0.205)
    add_tapered_beam_z(tg_body, 2, -0.026, 0.026, -0.335, 0.215, 0.222, 0.022, 0.205, 0.211)

    # 3. Sliding lift carriage riding inside the ACR linear track (Z = -0.35 m, Y = +0.120 .. +0.240 m)
    #    At Y_TG=551 mm, carriage reaches Y = 791 mm (inside the 800 mm ACR rail!)
    add_box(tg_body, 1, -0.064, 0.120, -0.370, 0.064, 0.240, -0.325)
    add_box(tg_body, 0, -0.072, 0.135, -0.360, 0.072, 0.225, -0.335)

    # SINGLE-PRIMITIVE TG_Jaw1 & TG_Jaw2 (exact original dimensions & 1 material for Havok isTrigger)
    jaw1 = new_prims()
    add_box(jaw1, 1, -0.0075, -0.040, -0.025, 0.0075, 0.040, 0.025)

    jaw2 = new_prims()
    add_box(jaw2, 1, -0.0075, -0.040, -0.025, 0.0075, 0.040, 0.025)

    glb = pack_meshes(
        [
            ("TG_Body", "TG_Body_Geom", tg_body),
            ("TG_Jaw1", "TG_Jaw1_Geom", jaw1),
            ("TG_Jaw2", "TG_Jaw2_Geom", jaw2),
        ],
        materials,
    )
    out = os.path.join(ASSETS_DIR, "ToteGripper.glb")
    with open(out, "wb") as f:
        f.write(glb)
    print(f"Wrote compact ASRS ToteGripper.glb ({len(glb)} bytes) -> {out}")


if __name__ == "__main__":
    generate_amr_glb()
    generate_tote_gripper_glb()
