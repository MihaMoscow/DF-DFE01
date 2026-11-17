#!/usr/bin/env python3
"""Generate FactoryFloor.glb and FactoryWalls.glb for DFE_01.

Creates:
1. assets/FactoryFloor.glb: 8m x 10m high-resolution textured factory floor
   with polished concrete base, OSHA/ISO hazard zones around robot cell and box,
   slate AMR transit highway with yellow borders and docking targets,
   and ISO safety-green pedestrian walkways with walking person stencils and zebra crosswalks.
2. assets/FactoryWalls.glb: 3.5m industrial factory perimeter walls with two-tone siding,
   safety kickplates, structural I-beam columns, logistics rollup door, emergency exit door,
   and upper high-bay clerestory windows.
"""

import io
import json
import math
import os
import struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = "/Users/mi_sha/Documents/21. PoliMI Studies/2. Courses/2026/7_Digital factory/3_Project/02_model/assets"

# Floor world bounds in mm
X_MIN, X_MAX = -5000.0, 3000.0  # 8000 mm (8.0 m)
Z_MIN, Z_MAX = -3000.0, 7000.0  # 10000 mm (10.0 m)
W_MM = X_MAX - X_MIN
H_MM = Z_MAX - Z_MIN

# Image resolution (power of two for optimal WebGL mipmapping)
IMG_W = 2048
IMG_H = 2048
SCALE_X = IMG_W / W_MM  # px per mm (0.256 px/mm)
SCALE_Z = IMG_H / H_MM  # px per mm (0.2048 px/mm)


def to_px(x_mm, z_mm):
    """Convert scene mm coordinates to image pixel coordinates."""
    u = (x_mm - X_MIN) / W_MM
    v = (z_mm - Z_MIN) / H_MM
    px = int(round(u * (IMG_W - 1)))
    py = int(round(v * (IMG_H - 1)))
    return px, py


def get_font(size):
    for path in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSMono.ttf",
    ]:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def draw_hazard_stripes(draw, x0, z0, x1, z1, border_w_mm=120, stripe_pitch_mm=100):
    """Draw 45-degree yellow and black diagonal hazard warning border around [x0, z0, x1, z1]."""
    p0 = to_px(x0, z0)
    p1 = to_px(x1, z1)
    left = min(p0[0], p1[0])
    right = max(p0[0], p1[0])
    top = min(p0[1], p1[1])
    bottom = max(p0[1], p1[1])
    bw = int(round(border_w_mm * SCALE_X))

    # Outer and inner rectangles
    # We clip stripes to the border region (outer minus inner)
    pitch = int(round(stripe_pitch_mm * SCALE_X * math.sqrt(2)))
    if pitch < 4:
        pitch = 10

    # Create a mask for the border frame
    frame_mask = Image.new("L", (IMG_W, IMG_H), 0)
    m_draw = ImageDraw.Draw(frame_mask)
    m_draw.rectangle([left, top, right, bottom], fill=255)
    m_draw.rectangle([left + bw, top + bw, right - bw, bottom - bw], fill=0)

    # Generate diagonal stripes
    diag_img = Image.new("RGB", (IMG_W, IMG_H), (30, 30, 30))
    d_draw = ImageDraw.Draw(diag_img)
    stripe_w = pitch // 2
    # Diagonals: x + y = c
    c_min = left + top - IMG_H
    c_max = right + bottom + IMG_H
    for c in range(c_min, c_max, pitch):
        poly = [
            (c, 0),
            (c + stripe_w, 0),
            (c + stripe_w - IMG_H, IMG_H),
            (c - IMG_H, IMG_H),
        ]
        d_draw.polygon(poly, fill=(255, 204, 0))

    # Composite onto canvas using frame_mask
    canvas = draw._image
    canvas.paste(diag_img, (0, 0), frame_mask)


def draw_pedestrian_symbol(draw, x_mm, z_mm, size_mm=600):
    """Draw a white stencil silhouette of a walking person."""
    px, py = to_px(x_mm, z_mm)
    s = int(round(size_mm * SCALE_X))
    hs = s // 2

    # Head
    r = s // 6
    draw.ellipse([px - r, py - hs, px + r, py - hs + 2 * r], fill=(255, 255, 255))

    # Torso
    draw.line([(px, py - hs + 2 * r), (px - s // 10, py + s // 6)], fill=(255, 255, 255), width=max(2, s // 8))

    # Arms
    draw.line([(px, py - hs + int(2.5 * r)), (px + s // 4, py - s // 10)], fill=(255, 255, 255), width=max(2, s // 10))
    draw.line([(px, py - hs + int(2.5 * r)), (px - s // 4, py)], fill=(255, 255, 255), width=max(2, s // 10))

    # Legs
    draw.line([(px - s // 10, py + s // 6), (px + s // 4, py + hs)], fill=(255, 255, 255), width=max(2, s // 8))
    draw.line([(px - s // 10, py + s // 6), (px - s // 3, py + hs - s // 8), (px - s // 3 - s // 10, py + hs)], fill=(255, 255, 255), width=max(2, s // 8))


def draw_amr_dock_target(draw, x_mm, z_mm, label="AMR DOCK"):
    """Draw an industrial AMR docking station target."""
    px, py = to_px(x_mm, z_mm)
    size_px = int(round(500 * SCALE_X))
    hs = size_px // 2

    # Yellow background box
    draw.rectangle([px - hs, py - hs, px + hs, py + hs], outline=(255, 204, 0), width=4)
    # Corner brackets
    bracket_len = hs // 2
    b_w = 6
    # Top-left
    draw.line([(px - hs, py - hs), (px - hs + bracket_len, py - hs)], fill=(255, 204, 0), width=b_w)
    draw.line([(px - hs, py - hs), (px - hs, py - hs + bracket_len)], fill=(255, 204, 0), width=b_w)
    # Top-right
    draw.line([(px + hs, py - hs), (px + hs - bracket_len, py - hs)], fill=(255, 204, 0), width=b_w)
    draw.line([(px + hs, py - hs), (px + hs, py - hs + bracket_len)], fill=(255, 204, 0), width=b_w)
    # Bottom-left
    draw.line([(px - hs, py + hs), (px - hs + bracket_len, py + hs)], fill=(255, 204, 0), width=b_w)
    draw.line([(px - hs, py + hs), (px - hs, py + hs - bracket_len)], fill=(255, 204, 0), width=b_w)
    # Bottom-right
    draw.line([(px + hs, py + hs), (px + hs - bracket_len, py + hs)], fill=(255, 204, 0), width=b_w)
    draw.line([(px + hs, py + hs), (px + hs, py + hs - bracket_len)], fill=(255, 204, 0), width=b_w)

    # Center crosshair
    draw.line([(px - hs // 2, py), (px + hs // 2, py)], fill=(255, 204, 0), width=3)
    draw.line([(px, py - hs // 2), (px, py + hs // 2)], fill=(255, 204, 0), width=3)
    draw.ellipse([px - 10, py - 10, px + 10, py + 10], outline=(255, 204, 0), width=3)

    # Label
    font = get_font(18)
    draw.text((px - hs + 10, py - hs - 24), label, fill=(255, 204, 0), font=font)


def draw_arrow(draw, x0_mm, z0_mm, x1_mm, z1_mm, color=(255, 204, 0), width_px=6):
    """Draw a directional navigation arrow."""
    p0 = to_px(x0_mm, z0_mm)
    p1 = to_px(x1_mm, z1_mm)
    draw.line([p0, p1], fill=color, width=width_px)
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    angle = math.atan2(dy, dx)
    arrow_len = 24
    angle_spread = 0.5
    a1 = (p1[0] - arrow_len * math.cos(angle - angle_spread), p1[1] - arrow_len * math.sin(angle - angle_spread))
    a2 = (p1[0] - arrow_len * math.cos(angle + angle_spread), p1[1] - arrow_len * math.sin(angle + angle_spread))
    draw.polygon([p1, a1, a2], fill=color)


def create_factory_floor_texture():
    print(f"Creating floor texture ({IMG_W}x{IMG_H})...")
    # Base polished concrete
    base_color = (196, 199, 203)
    img = Image.new("RGB", (IMG_W, IMG_H), base_color)

    # Add procedural concrete grain
    np.random.seed(42)
    noise = (np.random.randn(IMG_H, IMG_W) * 3.5).astype(np.int16)
    arr = np.array(img, dtype=np.int16)
    for c in range(3):
        arr[:, :, c] = np.clip(arr[:, :, c] + noise, 0, 255)
    img = Image.fromarray(arr.astype(np.uint8))
    draw = ImageDraw.Draw(img)

    # 1. Concrete Expansion Joint Grid (1000 mm x 1000 mm)
    joint_color = (150, 153, 157)
    for x in range(int(X_MIN), int(X_MAX) + 1, 1000):
        p_top = to_px(x, Z_MAX)
        p_bot = to_px(x, Z_MIN)
        draw.line([p_top, p_bot], fill=joint_color, width=2)
    for z in range(int(Z_MIN), int(Z_MAX) + 1, 1000):
        p_left = to_px(X_MIN, z)
        p_right = to_px(X_MAX, z)
        draw.line([p_left, p_right], fill=joint_color, width=2)

    # 2. SAFE WALKING AREA (Pedestrian Corridor BETWEEN Box and Conveyor) - ISO 3864 Safety Green
    green_color = (55, 130, 80)
    white_color = (255, 255, 255)
    font_large = get_font(28)
    font_med = get_font(22)
    border_w = 6

    # Green pedestrian corridor: X in [-1650, -850] (800 mm wide), Z in [-2600, 4200]
    p_gw0 = to_px(-1650, 4200)
    p_gw1 = to_px(-850, -2600)
    draw.rectangle([min(p_gw0[0], p_gw1[0]), min(p_gw0[1], p_gw1[1]), max(p_gw0[0], p_gw1[0]), max(p_gw0[1], p_gw1[1])], fill=green_color)

    # White border lines along both sides of the pedestrian corridor (and ends)
    draw.line([to_px(-1650, -2600), to_px(-1650, 4200)], fill=white_color, width=border_w)
    draw.line([to_px(-850, -2600), to_px(-850, 4200)], fill=white_color, width=border_w)
    draw.line([to_px(-1650, -2600), to_px(-850, -2600)], fill=white_color, width=border_w)
    draw.line([to_px(-1650, 4200), to_px(-850, 4200)], fill=white_color, width=border_w)

    # Pedestrian silhouettes & labels along the green corridor (outside AMR crossing)
    for z in [-2000, -1000, 0, 800, 3000, 3700]:
        draw_pedestrian_symbol(draw, -1250, z, size_mm=480)
    draw.text(to_px(-1580, -1450), "PEDESTRIAN SAFE ZONE", fill=white_color, font=font_med)
    draw.text(to_px(-1580, 2600), "PEDESTRIAN SAFE ZONE", fill=white_color, font=font_med)

    # 3. AMR ZONE OF WORK (Dedicated Mobile Robot Transit Highway)
    slate_amr = (150, 158, 168)
    yellow = (255, 204, 0)

    # Segment 1: Main East-West Corridor (Z in [1450, 2250], X in [-2650, 100])
    p_m0 = to_px(-2650, 2250)
    p_m1 = to_px(100, 1450)
    draw.rectangle([min(p_m0[0], p_m1[0]), min(p_m0[1], p_m1[1]), max(p_m0[0], p_m1[0]), max(p_m0[1], p_m1[1])], fill=slate_amr)

    # Segment 2: North-South Tote Pickup Spur (X in [-750, 50], Z in [1050, 1850])
    p_s0 = to_px(-750, 1850)
    p_s1 = to_px(50, 1050)
    draw.rectangle([min(p_s0[0], p_s1[0]), min(p_s0[1], p_s1[1]), max(p_s0[0], p_s1[0]), max(p_s0[1], p_s1[1])], fill=slate_amr)

    # Segment 3: Box Delivery Spur (X in [-2650, -1750], Z in [750, 1850])
    p_b0 = to_px(-2650, 1850)
    p_b1 = to_px(-1750, 750)
    draw.rectangle([min(p_b0[0], p_b1[0]), min(p_b0[1], p_b1[1]), max(p_b0[0], p_b1[0]), max(p_b0[1], p_b1[1])], fill=slate_amr)

    # Zebra Crosswalk where Pedestrian Corridor (X in [-1650, -850]) crosses AMR Lane (Z in [1450, 2250])
    for z_c in range(1520, 2200, 120):
        draw.line([to_px(-1600, z_c), to_px(-900, z_c)], fill=white_color, width=12)
    draw.text(to_px(-1620, 2320), "CROSSWALK: AMR STOPS FOR PEDESTRIAN", fill=yellow, font=get_font(18))

    # AMR Lane Solid Yellow Borders
    yw = 5
    # Main corridor North line
    draw.line([to_px(-2650, 2250), to_px(100, 2250)], fill=yellow, width=yw)
    # Tote spur East line
    draw.line([to_px(100, 2250), to_px(100, 1050)], fill=yellow, width=yw)
    # Tote spur South line
    draw.line([to_px(100, 1050), to_px(-750, 1050)], fill=yellow, width=yw)
    # Inner corner East
    draw.line([to_px(-750, 1050), to_px(-750, 1450)], fill=yellow, width=yw)
    draw.line([to_px(-750, 1450), to_px(-1750, 1450)], fill=yellow, width=yw)
    draw.line([to_px(-1750, 1450), to_px(-1750, 750)], fill=yellow, width=yw)
    # Box spur South line
    draw.line([to_px(-1750, 750), to_px(-2650, 750)], fill=yellow, width=yw)
    # Box spur West line
    draw.line([to_px(-2650, 750), to_px(-2650, 2250)], fill=yellow, width=yw)

    # Dashed White Centerlines for AMR navigation
    for x in range(-2500, 0, 160):
        draw.line([to_px(x, 1800), to_px(x + 90, 1800)], fill=white_color, width=4)
    for z in range(1150, 1750, 160):
        draw.line([to_px(-400, z), to_px(-400, z + 90)], fill=white_color, width=4)
    for z in range(900, 1750, 160):
        draw.line([to_px(-2200, z), to_px(-2200, z + 90)], fill=white_color, width=4)

    # Directional flow arrows for AMR
    draw_arrow(draw, -500, 1400, -500, 1650, color=yellow, width_px=5)
    draw_arrow(draw, -700, 1920, -1100, 1920, color=yellow, width_px=5)
    draw_arrow(draw, -1400, 1920, -1800, 1920, color=yellow, width_px=5)
    draw_arrow(draw, -2100, 1650, -2100, 1350, color=yellow, width_px=5)

    # Stenciled AMR Lane Labels
    draw.text(to_px(-780, 2050), "AMR TRANSIT LANE", fill=yellow, font=font_med)
    draw.text(to_px(-2580, 2050), "AMR TRANSIT LANE", fill=yellow, font=font_med)

    # Docking Station Targets
    draw_amr_dock_target(draw, -400, 1230, label="AMR DOCK 1 (PICK)")
    draw_amr_dock_target(draw, -2200, 1100, label="AMR DOCK 2 (DROP)")

    # 4. DANGEROUS ZONES / RESTRICTED MACHINERY CELLS
    # Robotic Cell 1 + Full Conveyor B1: encloses B1 (-900..1005), PP, Fence_E1 (1135), and TotePad
    draw_hazard_stripes(draw, -350, -1200, 1250, 1550, border_w_mm=120, stripe_pitch_mm=80)
    # Stenciled warnings inside Robotic Cell
    font_bold = get_font(22)
    draw.text(to_px(250, 600), "DANGER: AUTOMATED ROBOT CELL", fill=(255, 204, 0), font=font_bold)
    draw.text(to_px(250, 480), "STAY CLEAR DURING OPERATION", fill=(220, 50, 50), font=get_font(18))
    # Conveyor footprint label at south infeed end
    p_inf0, p_inf1 = to_px(-220, -1050), to_px(220, -750)
    draw.rectangle([min(p_inf0[0], p_inf1[0]), min(p_inf0[1], p_inf1[1]), max(p_inf0[0], p_inf1[0]), max(p_inf0[1], p_inf1[1])], outline=yellow, width=3)
    draw.text(to_px(-200, -1020), "INFEED CONVEYOR B1", fill=yellow, font=get_font(16))

    # Packaging / Box Cell 2: Box & Grid station
    draw_hazard_stripes(draw, -2700, 600, -1700, 1600, border_w_mm=120, stripe_pitch_mm=80)
    draw.text(to_px(-2600, 1480), "PALLETIZING CELL", fill=(255, 204, 0), font=font_bold)
    draw.text(to_px(-2550, 1380), "AUTOMATIC CONTAINER PACKAGING", fill=(255, 204, 0), font=get_font(16))

    # Stencil container footprint for Box
    p_box0 = to_px(-2550, 1400)
    p_box1 = to_px(-1850, 800)
    draw.rectangle([min(p_box0[0], p_box1[0]), min(p_box0[1], p_box1[1]), max(p_box0[0], p_box1[0]), max(p_box0[1], p_box1[1])], outline=(255, 255, 255), width=3)
    draw.text(to_px(-2450, 1080), "BOX CONTAINER 1200x800", fill=white_color, font=get_font(18))

    return img


def build_glb(gltf_dict, bin_blob):
    """Assemble a standard glTF 2.0 binary GLB file."""
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


def generate_factory_floor_glb():
    """Build FactoryFloor.glb containing the textured slab."""
    img = create_factory_floor_texture()
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    png_bytes = buf.getvalue()
    print(f"Compressed PNG size: {len(png_bytes) / 1024:.1f} KB")

    # Geometry: A solid box slab spanning [X_MIN, X_MAX] in X, [-50, 0] in Y, [Z_MIN, Z_MAX] in Z
    # In metres (unit=1 in mm scene)
    x0, x1 = X_MIN * 0.001, X_MAX * 0.001
    z0, z1 = Z_MIN * 0.001, Z_MAX * 0.001
    y_bot = -0.050  # 50 mm thick foundation
    y_top = 0.0     # exact floor level (no competing env.ground)

    # Vertices for top face (textured):
    # Our image has py=0 at Z_MIN (south, top of camera.d1 view), py=IMG_H-1 at Z_MAX (north, bottom of view).
    # In glTF, V=0 is top of image (py=0), V=1 is bottom of image (py=IMG_H-1).
    # So Z=Z_MIN -> V=0; Z=Z_MAX -> V=1!
    top_pos = [(x0, y_top, z1), (x1, y_top, z1), (x1, y_top, z0), (x0, y_top, z0)]
    top_norm = [(0.0, 1.0, 0.0)] * 4
    top_uv = [(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]
    top_idx = [0, 2, 1, 0, 3, 2]

    # Side and bottom faces (untextured concrete dark grey)
    side_faces = [
        # South face (z = z0)
        ((x0, y_bot, z0), (x1, y_bot, z0), (x1, y_top, z0), (x0, y_top, z0), (0, 0, -1)),
        # North face (z = z1)
        ((x1, y_bot, z1), (x0, y_bot, z1), (x0, y_top, z1), (x1, y_top, z1), (0, 0, 1)),
        # West face (x = x0)
        ((x0, y_bot, z1), (x0, y_bot, z0), (x0, y_top, z0), (x0, y_top, z1), (-1, 0, 0)),
        # East face (x = x1)
        ((x1, y_bot, z0), (x1, y_bot, z1), (x1, y_top, z1), (x1, y_top, z0), (1, 0, 0)),
        # Bottom face (y = y_bot)
        ((x0, y_bot, z0), (x1, y_bot, z0), (x1, y_bot, z1), (x0, y_bot, z1), (0, -1, 0)),
    ]
    side_pos = []
    side_norm = []
    side_uv = []
    side_idx = []
    for f_idx, (v0, v1, v2, v3, n) in enumerate(side_faces):
        b = f_idx * 4
        side_pos.extend([v0, v1, v2, v3])
        side_norm.extend([n, n, n, n])
        side_uv.extend([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])
        side_idx.extend([b, b + 1, b + 2, b, b + 2, b + 3])

    # Pack buffers
    # Primitive 0: Top face with texture
    pos0_b = b"".join(struct.pack("<3f", *p) for p in top_pos)
    norm0_b = b"".join(struct.pack("<3f", *n) for n in top_norm)
    uv0_b = b"".join(struct.pack("<2f", *u) for u in top_uv)
    idx0_b = b"".join(struct.pack("<H", i) for i in top_idx)
    while len(idx0_b) % 4 != 0:
        idx0_b += b"\x00"

    # Primitive 1: Side/bottom faces
    pos1_b = b"".join(struct.pack("<3f", *p) for p in side_pos)
    norm1_b = b"".join(struct.pack("<3f", *n) for n in side_norm)
    uv1_b = b"".join(struct.pack("<2f", *u) for u in side_uv)
    idx1_b = b"".join(struct.pack("<H", i) for i in side_idx)
    while len(idx1_b) % 4 != 0:
        idx1_b += b"\x00"

    # Combine binary blob
    bin_blob = (
        pos0_b + norm0_b + uv0_b + idx0_b +
        pos1_b + norm1_b + uv1_b + idx1_b +
        png_bytes
    )

    # Calculate offsets
    off_pos0 = 0
    off_norm0 = off_pos0 + len(pos0_b)
    off_uv0 = off_norm0 + len(norm0_b)
    off_idx0 = off_uv0 + len(uv0_b)

    off_pos1 = off_idx0 + len(idx0_b)
    off_norm1 = off_pos1 + len(pos1_b)
    off_uv1 = off_norm1 + len(norm1_b)
    off_idx1 = off_uv1 + len(uv1_b)

    off_img = off_idx1 + len(idx1_b)

    gltf = {
        "asset": {"version": "2.0", "generator": "dfe01_factory_floor_gen"},
        "scenes": [{"nodes": [0]}],
        "scene": 0,
        "nodes": [{"name": "FactoryFloor_Root", "mesh": 0}],
        "meshes": [
            {
                "name": "FactoryFloor_Mesh",
                "primitives": [
                    {
                        "attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2},
                        "indices": 3,
                        "material": 0,
                    },
                    {
                        "attributes": {"POSITION": 4, "NORMAL": 5, "TEXCOORD_0": 6},
                        "indices": 7,
                        "material": 1,
                    },
                ],
            }
        ],
        "materials": [
            {
                "name": "FloorPaintedMat",
                "pbrMetallicRoughness": {
                    "baseColorTexture": {"index": 0},
                    "metallicFactor": 0.05,
                    "roughnessFactor": 0.45,
                },
                "doubleSided": True,
            },
            {
                "name": "FloorFoundationMat",
                "pbrMetallicRoughness": {
                    "baseColorFactor": [0.25, 0.27, 0.30, 1.0],
                    "metallicFactor": 0.1,
                    "roughnessFactor": 0.8,
                },
            },
        ],
        "textures": [{"source": 0, "sampler": 0}],
        "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 33071, "wrapT": 33071}],
        "images": [{"bufferView": 8, "mimeType": "image/png"}],
        "buffers": [{"byteLength": len(bin_blob)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": off_pos0, "byteLength": len(pos0_b), "target": 34962},
            {"buffer": 0, "byteOffset": off_norm0, "byteLength": len(norm0_b), "target": 34962},
            {"buffer": 0, "byteOffset": off_uv0, "byteLength": len(uv0_b), "target": 34962},
            {"buffer": 0, "byteOffset": off_idx0, "byteLength": len(top_idx) * 2, "target": 34963},
            {"buffer": 0, "byteOffset": off_pos1, "byteLength": len(pos1_b), "target": 34962},
            {"buffer": 0, "byteOffset": off_norm1, "byteLength": len(norm1_b), "target": 34962},
            {"buffer": 0, "byteOffset": off_uv1, "byteLength": len(uv1_b), "target": 34962},
            {"buffer": 0, "byteOffset": off_idx1, "byteLength": len(side_idx) * 2, "target": 34963},
            {"buffer": 0, "byteOffset": off_img, "byteLength": len(png_bytes)},
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3", "min": [x0, y_top, z0], "max": [x1, y_top, z1]},
            {"bufferView": 1, "componentType": 5126, "count": 4, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": 4, "type": "VEC2"},
            {"bufferView": 3, "componentType": 5123, "count": len(top_idx), "type": "SCALAR"},
            {"bufferView": 4, "componentType": 5126, "count": len(side_pos), "type": "VEC3", "min": [x0, y_bot, z0], "max": [x1, y_top, z1]},
            {"bufferView": 5, "componentType": 5126, "count": len(side_norm), "type": "VEC3"},
            {"bufferView": 6, "componentType": 5126, "count": len(side_uv), "type": "VEC2"},
            {"bufferView": 7, "componentType": 5123, "count": len(side_idx), "type": "SCALAR"},
        ],
    }

    glb = build_glb(gltf, bin_blob)
    out_path = os.path.join(ASSETS_DIR, "FactoryFloor.glb")
    with open(out_path, "wb") as f:
        f.write(glb)
    print(f"FactoryFloor.glb written: {len(glb)} bytes -> {out_path}")


def generate_factory_walls_glb():
    """Build FactoryWalls.glb with 3.5m industrial walls, columns, baseboards, rollup door, and windows."""
    print("Generating FactoryWalls.glb...")

    x0, x1 = X_MIN * 0.001, X_MAX * 0.001  # -5.0, 3.0 m
    z0, z1 = Z_MIN * 0.001, Z_MAX * 0.001  # -3.0, 7.0 m
    y0, y1 = 0.0, 3.5                     # 0.0 to 3.5 m
    t = 0.15                              # wall thickness 150 mm

    # Materials:
    # 0: Lower Wainscot Slate Wall [0.28, 0.31, 0.35]
    # 1: Upper Wall Off-White Panels [0.84, 0.86, 0.88]
    # 2: Yellow Kickplate & Accent Trim [1.0, 0.8, 0.0]
    # 3: Structural Steel Columns / I-Beams [0.20, 0.23, 0.28]
    # 4: Logistics Rollup Door Slats [0.65, 0.68, 0.72]
    # 5: Emergency Exit Door Green [0.18, 0.52, 0.28]
    # 6: Clerestory High-Bay Windows (Reflective Blue) [0.65, 0.78, 0.88, 0.8]

    materials = [
        {"name": "LowerWallSlate", "pbrMetallicRoughness": {"baseColorFactor": [0.28, 0.31, 0.35, 1.0], "roughnessFactor": 0.6, "metallicFactor": 0.1}, "doubleSided": True},
        {"name": "UpperWallWhite", "pbrMetallicRoughness": {"baseColorFactor": [0.85, 0.86, 0.88, 1.0], "roughnessFactor": 0.75, "metallicFactor": 0.05}, "doubleSided": True},
        {"name": "SafetyYellowTrim", "pbrMetallicRoughness": {"baseColorFactor": [1.0, 0.80, 0.0, 1.0], "roughnessFactor": 0.4, "metallicFactor": 0.1}, "doubleSided": True},
        {"name": "SteelColumnDark", "pbrMetallicRoughness": {"baseColorFactor": [0.18, 0.20, 0.24, 1.0], "roughnessFactor": 0.5, "metallicFactor": 0.4}, "doubleSided": True},
        {"name": "RollupDoorSlats", "pbrMetallicRoughness": {"baseColorFactor": [0.62, 0.65, 0.70, 1.0], "roughnessFactor": 0.4, "metallicFactor": 0.3}, "doubleSided": True},
        {"name": "EmergencyExitGreen", "pbrMetallicRoughness": {"baseColorFactor": [0.18, 0.55, 0.28, 1.0], "roughnessFactor": 0.5, "metallicFactor": 0.1}, "doubleSided": True},
        {"name": "WindowGlassBlue", "pbrMetallicRoughness": {"baseColorFactor": [0.65, 0.78, 0.88, 1.0], "roughnessFactor": 0.15, "metallicFactor": 0.3}, "doubleSided": True},
    ]

    prims_data = {m_idx: {"pos": [], "norm": [], "idx": []} for m_idx in range(len(materials))}

    def add_box(bx0, by0, bz0, bx1, by1, bz1, mat_idx):
        """Add an axis-aligned box to the primitive of material mat_idx."""
        data = prims_data[mat_idx]
        b_idx = len(data["pos"])
        # 6 faces
        faces = [
            # +Y (top)
            ((bx0, by1, bz0), (bx0, by1, bz1), (bx1, by1, bz1), (bx1, by1, bz0), (0, 1, 0)),
            # -Y (bottom)
            ((bx0, by0, bz1), (bx0, by0, bz0), (bx1, by0, bz0), (bx1, by0, bz1), (0, -1, 0)),
            # +X
            ((bx1, by0, bz0), (bx1, by1, bz0), (bx1, by1, bz1), (bx1, by0, bz1), (1, 0, 0)),
            # -X
            ((bx0, by0, bz1), (bx0, by1, bz1), (bx0, by1, bz0), (bx0, by0, bz0), (-1, 0, 0)),
            # +Z
            ((bx0, by0, bz1), (bx1, by0, bz1), (bx1, by1, bz1), (bx0, by1, bz1), (0, 0, 1)),
            # -Z
            ((bx1, by0, bz0), (bx0, by0, bz0), (bx0, by1, bz0), (bx1, by1, bz0), (0, 0, -1)),
        ]
        for f_idx, (v0, v1, v2, v3, n) in enumerate(faces):
            start = b_idx + f_idx * 4
            data["pos"].extend([v0, v1, v2, v3])
            data["norm"].extend([n, n, n, n])
            data["idx"].extend([start, start + 1, start + 2, start, start + 2, start + 3])

    # 1. SOUTH WALL (Z = z0 = -3.0 m, spanning X in [x0, x1])
    # Kickplate (Y in [0, 0.12])
    add_box(x0, 0.0, z0 - t, x1, 0.12, z0, mat_idx=2)
    # Lower wall (Y in [0.12, 1.0])
    add_box(x0, 0.12, z0 - t, x1, 1.0, z0, mat_idx=0)
    # Yellow trim (Y in [1.0, 1.06])
    add_box(x0, 1.0, z0 - t, x1, 1.06, z0, mat_idx=2)
    # Upper wall (Y in [1.06, y1])
    add_box(x0, 1.06, z0 - t, x1, y1, z0, mat_idx=1)

    # 2. EAST WALL (X = x1 = +3.0 m, spanning Z in [z0, z1])
    # Kickplate
    add_box(x1, 0.0, z0, x1 + t, 0.12, z1, mat_idx=2)
    # Lower wall
    add_box(x1, 0.12, z0, x1 + t, 1.0, z1, mat_idx=0)
    # Yellow trim
    add_box(x1, 1.0, z0, x1 + t, 1.06, z1, mat_idx=2)
    # Upper wall with Clerestory Window band (Y in [2.2, 3.2])
    add_box(x1, 1.06, z0, x1 + t, 2.2, z1, mat_idx=1)
    # Window band
    add_box(x1, 2.2, z0 + 0.5, x1 + t * 0.5, 3.2, z1 - 0.5, mat_idx=6)
    # Window upper wall
    add_box(x1, 3.2, z0, x1 + t, y1, z1, mat_idx=1)

    # 3. WEST WALL (X = x0 = -5.0 m, spanning Z in [z0, z1])
    # Has an Emergency Exit Door at Z in [-0.5, 0.5], height 2.2 m
    # South section: Z in [z0, -0.5]
    add_box(x0 - t, 0.0, z0, x0, 0.12, -0.5, mat_idx=2)
    add_box(x0 - t, 0.12, z0, x0, 1.0, -0.5, mat_idx=0)
    add_box(x0 - t, 1.0, z0, x0, 1.06, -0.5, mat_idx=2)
    add_box(x0 - t, 1.06, z0, x0, 2.2, -0.5, mat_idx=1)
    add_box(x0 - t, 2.2, z0 + 0.5, x0, 3.2, -0.5, mat_idx=6)  # window
    add_box(x0 - t, 3.2, z0, x0, y1, -0.5, mat_idx=1)

    # Door section: Z in [-0.5, 0.5]
    # Green door leaf
    add_box(x0 - t * 0.8, 0.0, -0.5, x0, 2.2, 0.5, mat_idx=5)
    # Emergency exit sign above door
    add_box(x0 - t * 0.9, 2.25, -0.3, x0 + 0.02, 2.45, 0.3, mat_idx=5)
    # Wall above door
    add_box(x0 - t, 2.2, -0.5, x0, y1, 0.5, mat_idx=1)

    # North section: Z in [0.5, z1]
    add_box(x0 - t, 0.0, 0.5, x0, 0.12, z1, mat_idx=2)
    add_box(x0 - t, 0.12, 0.5, x0, 1.0, z1, mat_idx=0)
    add_box(x0 - t, 1.0, 0.5, x0, 1.06, z1, mat_idx=2)
    add_box(x0 - t, 1.06, 0.5, x0, 2.2, z1, mat_idx=1)
    add_box(x0 - t, 2.2, 0.5, x0, 3.2, z1 - 0.5, mat_idx=6)  # window
    add_box(x0 - t, 3.2, 0.5, x0, y1, z1, mat_idx=1)

    # 4. NORTH WALL (Z = z1 = +7.0 m, spanning X in [x0, x1])
    # Has a Logistics Roll-Up Door at X in [-1.5, 0.5], height 3.0 m
    # West section: X in [x0, -1.5]
    add_box(x0, 0.0, z1, -1.5, 0.12, z1 + t, mat_idx=2)
    add_box(x0, 0.12, z1, -1.5, 1.0, z1 + t, mat_idx=0)
    add_box(x0, 1.0, z1, -1.5, 1.06, z1 + t, mat_idx=2)
    add_box(x0, 1.06, z1, -1.5, y1, z1 + t, mat_idx=1)

    # Roll-up door section: X in [-1.5, 0.5]
    # Door slats
    add_box(-1.5, 0.0, z1, 0.5, 3.0, z1 + t * 0.5, mat_idx=4)
    # Yellow door frame surround
    add_box(-1.58, 0.0, z1, -1.5, 3.08, z1 + t, mat_idx=2)
    add_box(0.5, 0.0, z1, 0.58, 3.08, z1 + t, mat_idx=2)
    add_box(-1.58, 3.0, z1, 0.58, 3.08, z1 + t, mat_idx=2)
    # Wall above door
    add_box(-1.5, 3.08, z1, 0.5, y1, z1 + t, mat_idx=1)

    # East section: X in [0.5, x1]
    add_box(0.5, 0.0, z1, x1, 0.12, z1 + t, mat_idx=2)
    add_box(0.5, 0.12, z1, x1, 1.0, z1 + t, mat_idx=0)
    add_box(0.5, 1.0, z1, x1, 1.06, z1 + t, mat_idx=2)
    add_box(0.5, 1.06, z1, x1, y1, z1 + t, mat_idx=1)

    # 5. STRUCTURAL STEEL COLUMNS (Pillars) along perimeter
    col_w = 0.28
    col_positions = [
        # Corners
        (x0, z0), (x1 - col_w, z0), (x0, z1 - col_w), (x1 - col_w, z1 - col_w),
        # South intermediate
        (-2.5, z0), (0.0, z0),
        # North intermediate
        (-3.5, z1 - col_w), (1.5, z1 - col_w),
        # West intermediate
        (x0, 0.0), (x0, 3.5),
        # East intermediate
        (x1 - col_w, 0.0), (x1 - col_w, 3.5),
    ]
    for cx, cz in col_positions:
        add_box(cx, 0.0, cz, cx + col_w, y1, cz + col_w, mat_idx=3)

    # Assemble GLTF
    all_pos_bytes = []
    all_norm_bytes = []
    all_idx_bytes = []
    buffer_views = []
    accessors = []
    primitives = []

    cur_offset = 0
    buffer_idx = 0

    for m_idx in range(len(materials)):
        p_data = prims_data[m_idx]
        if not p_data["pos"]:
            continue
        p_bytes = b"".join(struct.pack("<3f", *p) for p in p_data["pos"])
        n_bytes = b"".join(struct.pack("<3f", *n) for n in p_data["norm"])
        i_bytes = b"".join(struct.pack("<H", i) for i in p_data["idx"])
        while len(i_bytes) % 4 != 0:
            i_bytes += b"\x00"

        # Pos bufferView
        pos_view = len(buffer_views)
        buffer_views.append({"buffer": 0, "byteOffset": cur_offset, "byteLength": len(p_bytes), "target": 34962})
        cur_offset += len(p_bytes)
        all_pos_bytes.append(p_bytes)

        # Norm bufferView
        norm_view = len(buffer_views)
        buffer_views.append({"buffer": 0, "byteOffset": cur_offset, "byteLength": len(n_bytes), "target": 34962})
        cur_offset += len(n_bytes)
        all_norm_bytes.append(n_bytes)

        # Idx bufferView
        idx_view = len(buffer_views)
        buffer_views.append({"buffer": 0, "byteOffset": cur_offset, "byteLength": len(i_bytes), "target": 34963})
        cur_offset += len(i_bytes)
        all_idx_bytes.append(i_bytes)

        # Accessors
        pos_acc = len(accessors)
        min_p = [min(p[i] for p in p_data["pos"]) for i in range(3)]
        max_p = [max(p[i] for p in p_data["pos"]) for i in range(3)]
        accessors.append({"bufferView": pos_view, "componentType": 5126, "count": len(p_data["pos"]), "type": "VEC3", "min": min_p, "max": max_p})

        norm_acc = len(accessors)
        accessors.append({"bufferView": norm_view, "componentType": 5126, "count": len(p_data["norm"]), "type": "VEC3"})

        idx_acc = len(accessors)
        accessors.append({"bufferView": idx_view, "componentType": 5123, "count": len(p_data["idx"]), "type": "SCALAR"})

        primitives.append({
            "attributes": {"POSITION": pos_acc, "NORMAL": norm_acc},
            "indices": idx_acc,
            "material": m_idx,
        })

    bin_blob = b"".join(all_pos_bytes) + b"".join(all_norm_bytes) + b"".join(all_idx_bytes)

    # Fix buffer views offsets since all pos, then all norm, then all idx
    # Let's cleanly organize bin_blob as sequence of chunks
    bin_chunks = []
    clean_views = []
    clean_offset = 0
    view_map = {}
    for i, bv in enumerate(buffer_views):
        m_i = i // 3
        part = i % 3
        p_data = prims_data[m_i]
        if part == 0:
            b_chunk = b"".join(struct.pack("<3f", *p) for p in p_data["pos"])
        elif part == 1:
            b_chunk = b"".join(struct.pack("<3f", *n) for n in p_data["norm"])
        else:
            b_chunk = b"".join(struct.pack("<H", idx) for idx in p_data["idx"])
            while len(b_chunk) % 4 != 0:
                b_chunk += b"\x00"

        clean_views.append({"buffer": 0, "byteOffset": clean_offset, "byteLength": len(b_chunk), "target": bv["target"]})
        clean_offset += len(b_chunk)
        bin_chunks.append(b_chunk)

    final_bin = b"".join(bin_chunks)

    gltf = {
        "asset": {"version": "2.0", "generator": "dfe01_factory_walls_gen"},
        "scenes": [{"nodes": [0]}],
        "scene": 0,
        "nodes": [{"name": "FactoryWalls_Root", "mesh": 0}],
        "meshes": [{"name": "FactoryWalls_Mesh", "primitives": primitives}],
        "materials": materials,
        "buffers": [{"byteLength": len(final_bin)}],
        "bufferViews": clean_views,
        "accessors": accessors,
    }

    glb = build_glb(gltf, final_bin)
    out_path = os.path.join(ASSETS_DIR, "FactoryWalls.glb")
    with open(out_path, "wb") as f:
        f.write(glb)
    print(f"FactoryWalls.glb written: {len(glb)} bytes -> {out_path}")


if __name__ == "__main__":
    generate_factory_floor_glb()
    generate_factory_walls_glb()
    print("All factory environment assets generated successfully!")
