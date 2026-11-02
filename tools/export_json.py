#!/usr/bin/env python3
"""
export_json.py - Mac/Linux-safe replacement for the "Export Scene JSON" and
"Export Animation JSON" buttons in the DFE_XY.xlsm workbooks
(Digital Factory, Polimi).

It reproduces the VBA macros in Module1 (ExportCustomConcatenationToFile,
ExportAnimationToFile, FormatJson) one-to-one, but writes the files with
correct path separators on any OS.

IMPORTANT: the JSON text of each asset/animation row is built by Excel
formulas (Assets!AX, Anim!V, Sequences!O). This script reads the values
Excel last CALCULATED and SAVED. So the workflow is:
    edit in Excel -> Save (Cmd+S) -> run this script.
If you edit the workbook with another tool that does not recalculate,
the exported JSON will be stale.

Usage:
    python3 export_json.py DFE_01.xlsm            # writes scene + anim JSON next to the workbook
    python3 export_json.py DFE_01.xlsm --scene    # scene only
    python3 export_json.py DFE_01.xlsm --anim     # animation only
    python3 export_json.py DFE_01.xlsm --outdir some/folder
    python3 export_json.py DFE_01.xlsm --check    # also validate the output is parseable JSON

Requires: openpyxl  (pip3 install openpyxl)
"""
import argparse
import json
import os
import sys

try:
    import openpyxl
except ImportError:
    sys.exit("openpyxl is missing: run  pip3 install openpyxl")

NL = "\n"  # Unix line endings (cleaner git diffs); the VBA uses NL


def cell_str(ws, ref):
    """Excel cell value as VBA would concatenate it (empty -> '')."""
    v = ws[ref].value
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def col_val(ws, col, row):
    return cell_str(ws, f"{col}{row}")


def last_row(ws, col="A"):
    """Equivalent of Cells(Rows.Count, col).End(xlUp).Row."""
    for r in range(ws.max_row, 0, -1):
        if ws[f"{col}{r}"].value not in (None, ""):
            return r
    return 1


# ---------- FormatJson port (behaviour kept identical to the VBA) ----------

def find_matching_bracket(s, start):
    level = 0
    in_string = False
    for i in range(start, len(s)):
        ch = s[i]
        if ch == '"':
            if i == 0 or s[i - 1] != "\\":
                in_string = not in_string
        elif not in_string:
            if ch == "[":
                level += 1
            elif ch == "]":
                level -= 1
                if level == 0:
                    return i
    return -1


def is_numeric_array(s):
    inner = s.strip()
    if not (inner.startswith("[") and inner.endswith("]")):
        return False
    inner = inner[1:-1]
    allowed = set("0123456789,.-+ Ee")
    return all(c in allowed for c in inner)


def format_numeric_array(s):
    while ", " in s:
        s = s.replace(", ", ",")
    return s.replace(",", ", ")


def format_json(s):
    out = []
    indent = 0
    in_string = False
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == '"':
            if i == 0 or s[i - 1] != "\\":
                in_string = not in_string
            out.append(ch)
        elif not in_string:
            if ch == "[":
                j = find_matching_bracket(s, i)
                if j >= 0:
                    chunk = s[i:j + 1]
                    if is_numeric_array(chunk):
                        out.append(format_numeric_array(chunk))
                        i = j
                    else:
                        indent += 1
                        out.append("[" + NL + " " * (indent * 2))
                else:
                    out.append(ch)
            elif ch == "{":
                indent += 1
                out.append("{" + NL + " " * (indent * 2))
            elif ch in "}]":
                indent -= 1
                out.append(NL + " " * (indent * 2) + ch)
            elif ch == ",":
                out.append("," + NL + " " * (indent * 2))
            elif ch == ":":
                out.append(": ")
            else:
                out.append(ch)
        else:
            out.append(ch)
        i += 1
    return "".join(out)


# ---------- the two exports ----------

def base_name(wb_path, ws_context):
    custom = cell_str(ws_context, "B10").strip()
    if custom:
        return custom
    return os.path.splitext(os.path.basename(wb_path))[0]


def build_scene(wb):
    ctx, assets_ws = wb["Context"], wb["Assets"]
    lr = last_row(assets_ws)
    assets, inscene = [], []
    for r in range(3, lr + 1):
        if col_val(assets_ws, "A", r).strip() == "":
            continue
        assets.append(col_val(assets_ws, "AX", r))
        if col_val(assets_ws, "B", r).strip() == "1":
            inscene.append('"' + col_val(assets_ws, "A", r) + '"')
    return (cell_str(ctx, "D1") + cell_str(ctx, "B4") + cell_str(ctx, "E1")
            + cell_str(ctx, "B5") + cell_str(ctx, "F1") + cell_str(ctx, "B6")
            + '"},' + cell_str(ctx, "G1") + ",".join(inscene)
            + cell_str(ctx, "H1") + ",".join(assets) + "]}")


def build_anim(wb):
    ctx, anim_ws, seq_ws = wb["Context"], wb["Anim"], wb["Sequences"]
    lr = last_row(anim_ws)  # the VBA uses the Anim last row for both loops
    anims, seqs = [], []
    for r in range(3, lr + 1):
        if col_val(anim_ws, "A", r).strip() != "":
            anims.append(col_val(anim_ws, "V", r))
    for r in range(3, lr + 1):
        if col_val(seq_ws, "A", r).strip() != "":
            seqs.append(col_val(seq_ws, "O", r))
    return (cell_str(ctx, "D2") + cell_str(ctx, "B4") + cell_str(ctx, "E2")
            + cell_str(ctx, "B5") + cell_str(ctx, "F2") + cell_str(ctx, "B7")
            + cell_str(ctx, "G2") + ",".join(anims) + cell_str(ctx, "H2")
            + ",".join(seqs) + cell_str(ctx, "I2"))


def write(path, text, check):
    formatted = format_json(text)
    if check:
        try:
            json.loads(formatted)
        except json.JSONDecodeError as e:
            print(f"  WARNING: {os.path.basename(path)} is not valid JSON: {e}")
    # trailing newline like VBA Print #
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(formatted + NL)
    print(f"  wrote {path}")


def main():
    ap = argparse.ArgumentParser(description="Export scene/animation JSON from a DFE .xlsm")
    ap.add_argument("workbook")
    ap.add_argument("--scene", action="store_true", help="export scene JSON only")
    ap.add_argument("--anim", action="store_true", help="export animation JSON only")
    ap.add_argument("--outdir", help="output folder (default: next to the workbook)")
    ap.add_argument("--check", action="store_true", help="validate output parses as JSON")
    a = ap.parse_args()

    wb_path = os.path.abspath(a.workbook)
    wb = openpyxl.load_workbook(wb_path, data_only=True, read_only=False)
    if wb["Assets"]["AX3"].value is None:
        sys.exit("No calculated values found. Open the workbook in Excel, Save it, then re-run.")

    outdir = os.path.abspath(a.outdir) if a.outdir else os.path.dirname(wb_path)
    os.makedirs(outdir, exist_ok=True)
    name = base_name(wb_path, wb["Context"])
    do_scene = a.scene or not a.anim
    do_anim = a.anim or not a.scene

    if do_scene:
        write(os.path.join(outdir, name + ".json"), build_scene(wb), a.check)
    if do_anim:
        write(os.path.join(outdir, name + "_anim.json"), build_anim(wb), a.check)


if __name__ == "__main__":
    main()
