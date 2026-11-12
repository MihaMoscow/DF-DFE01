#!/usr/bin/env python3
"""
sync_to_xlsm.py - Synchronize DFE_01.json and DFE_01_anim.json back into DFE_01.xlsm.

Uses only Python's standard library (zipfile + xml.etree.ElementTree + re) so that:
  1. No external packages (like openpyxl) are required.
  2. VBA macros (xl/vbaProject.bin), buttons, drawings, ActiveX controls, namespaces
     (xmlns:xdr, xmlns:x14, mc:Ignorable), and styles are preserved byte-for-byte.
  3. Valid Excel formulas (<f> with Excel "" quote escaping) AND cached formula values
     (<v>) are written to Assets and Anim, so the workbook opens cleanly in Excel and
     works with export_json.py.

Usage:
    python3 tools/sync_to_xlsm.py
"""
import json
import os
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET
import zipfile

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def qn(tag):
    return f"{{{NS_MAIN}}}{tag}"


def fmt_num(v):
    """Format a number the way Excel / JSON expects (integers without .0)."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if v.is_integer():
            return str(int(v))
        return repr(v)
    return str(v)


def format_properties_inner(props):
    """Format the inner body of an asset's properties object (without outer braces)."""
    if not props:
        return ""
    parts = []
    for k, v in props.items():
        if isinstance(v, str):
            parts.append(f'"{k}": "{v}"')
        elif isinstance(v, bool):
            parts.append(f'"{k}": {"true" if v else "false"}')
        elif isinstance(v, (int, float)):
            parts.append(f'"{k}": {fmt_num(v)}')
        else:
            parts.append(f'"{k}": {json.dumps(v)}')
    return ", ".join(parts)


def make_cell(col, row, style=None, value=None, formula=None, is_num=False):
    """Create an unprefixed OpenXML <c> element (inherits default worksheet xmlns)."""
    c = ET.Element("c")
    c.set("r", f"{col}{row}")
    if style is not None:
        c.set("s", style)

    if formula is not None:
        f_el = ET.SubElement(c, "f")
        f_el.text = formula
        if not is_num:
            c.set("t", "str")
        v_el = ET.SubElement(c, "v")
        v_el.text = str(value) if value is not None else ""
    elif value is not None and value != "":
        if is_num:
            v_el = ET.SubElement(c, "v")
            v_el.text = fmt_num(value)
        else:
            c.set("t", "inlineStr")
            is_el = ET.SubElement(c, "is")
            t_el = ET.SubElement(is_el, "t")
            s_val = str(value)
            if s_val.startswith(" ") or s_val.endswith(" ") or "\n" in s_val:
                t_el.set("xml:space", "preserve")
            t_el.text = s_val
    return c


def extract_row_styles(sheet_xml_text, template_rows=(3, 5)):
    """Extract column -> style mapping from existing template rows."""
    root = ET.fromstring(sheet_xml_text)
    sheet_data = root.find(qn("sheetData"))
    styles = {}
    for r_el in sheet_data.findall(qn("row")):
        r_idx = int(r_el.get("r", "0"))
        if r_idx in template_rows:
            for c_el in r_el.findall(qn("c")):
                ref = c_el.get("r", "")
                col = "".join(ch for ch in ref if ch.isalpha())
                s = c_el.get("s")
                if s is not None and col not in styles:
                    styles[col] = s
    return styles


def build_asset_row_xml(row_idx, asset, in_scene_set, styles):
    """Build a <row> XML string for xl/worksheets/sheet2.xml (Assets)."""
    r_el = ET.Element("row")
    r_el.set("r", str(row_idx))
    r_el.set("spans", "1:52")

    aid = asset.get("id", "")
    in_scene = 1 if aid in in_scene_set else None
    descr = asset.get("descr", "")
    atype = asset.get("type", "")
    model = asset.get("model", "")

    reps = asset.get("representations", [])
    rep_file = reps[0].get("file", "") if reps else ""
    rep_unit = reps[0].get("unit", 1) if reps else None

    pos = asset.get("position")
    rot = asset.get("rotation")
    rel_to = asset.get("placementRelTo", "")
    parent_obj = asset.get("parentObject", "")
    conn_to = asset.get("connectedTo", [])
    conn_str = conn_to[0] if conn_to else ""
    assign_to = asset.get("assignmentTo", [])
    assign_str = assign_to[0] if assign_to else ""
    succ = asset.get("successors", [])
    succ_str = succ[0] if succ else ""
    task_time = asset.get("taskTime")

    props = asset.get("properties")
    props_str = format_properties_inner(props) if props else ""

    sc = asset.get("statechart")
    sc_pretty = json.dumps(sc, indent=2) if sc else ""
    sc_flat = sc_pretty.replace("\n", " ").replace("\t", " ") if sc else ""

    pol_obs = asset.get("polObserved")
    pol_obs_str = ", ".join(f'"{x}"' for x in pol_obs) if pol_obs else ""
    pol_thresh = asset.get("polThreshold")
    ctrl_mach = asset.get("controlledMach")
    ctrl_mach_str = ", ".join(f'"{x}"' for x in ctrl_mach) if ctrl_mach else ""

    cells = []

    def add_in(col, val, is_num=False):
        if val is not None and val != "":
            cells.append(make_cell(col, row_idx, styles.get(col), value=val, is_num=is_num))

    add_in("A", aid)
    if in_scene is not None:
        add_in("B", in_scene, is_num=True)
    add_in("C", descr)
    add_in("D", atype)
    add_in("E", model)
    if rep_file:
        add_in("F", rep_file)
        add_in("G", rep_unit, is_num=True)
    if pos is not None and len(pos) == 3:
        add_in("H", pos[0], is_num=True)
        add_in("I", pos[1], is_num=True)
        add_in("J", pos[2], is_num=True)
    if rot is not None and len(rot) == 3:
        add_in("K", rot[0], is_num=True)
        add_in("L", rot[1], is_num=True)
        add_in("M", rot[2], is_num=True)
    add_in("N", rel_to)
    add_in("O", parent_obj)
    add_in("P", conn_str)
    add_in("Q", assign_str)
    add_in("R", succ_str)
    if task_time is not None:
        add_in("S", task_time, is_num=True)
    add_in("T", props_str)
    add_in("Y", sc_pretty)
    add_in("Z", pol_obs_str)
    if pol_thresh is not None:
        add_in("AA", pol_thresh, is_num=True)
    add_in("AB", ctrl_mach_str)

    # Cached formula outputs AD..AX
    r = row_idx
    v_AD = f'{{"id": "{aid}"'
    v_AE = f',"descr":"{descr}"' if descr else ""
    v_AF = f',"type":"{atype}"' if atype else ""
    v_AG = f',"model":"{model}"' if model else ""
    v_AH = f',"representations":[{{"file":"{rep_file}","unit":{fmt_num(rep_unit)}}}]' if rep_file else ""
    v_AI = f',"position":[{fmt_num(pos[0])},{fmt_num(pos[1])},{fmt_num(pos[2])}]' if (pos is not None and len(pos) == 3) else ""
    v_AJ = f',"rotation":[{fmt_num(rot[0])},{fmt_num(rot[1])},{fmt_num(rot[2])}]' if (rot is not None and len(rot) == 3) else ""
    v_AK = f',"placementRelTo":"{rel_to}"' if rel_to else ""
    v_AL = f',"parentObject":"{parent_obj}"' if parent_obj else ""
    v_AM = f',"connectedTo":["{conn_str}"]' if conn_str else ""
    v_AN = f',"assignmentTo":["{assign_str}"]' if assign_str else ""
    v_AO = f',"successors":["{succ_str}"]' if succ_str else ""
    v_AP = f',"taskTime":{fmt_num(task_time)}' if task_time is not None else ""
    v_AQ = f',"properties":{{{props_str}}}' if props_str else ""
    v_AR = ""
    v_AS = f',"statechart":{sc_flat}' if sc_flat else ""
    v_AT = f',"polObserved":[{pol_obs_str}]' if pol_obs_str else ""
    v_AU = f',"polThreshold":{fmt_num(pol_thresh)}' if pol_thresh is not None else ""
    v_AV = f',"controlledMach":[{ctrl_mach_str}]' if ctrl_mach_str else ""
    v_AW = "}"
    v_AX = (
        v_AD + v_AE + v_AF + v_AG + v_AH + v_AI + v_AJ + v_AK + v_AL
        + v_AM + v_AN + v_AO + v_AP + v_AQ + v_AR + v_AS + v_AT + v_AU + v_AV + v_AW
    )

    # Excel formulas use doubled double-quotes ("") for literal quotes inside strings
    formulas = [
        ("AD", f'CONCATENATE("{{""",A$2,""": """,A{r},"""")', v_AD),
        ("AE", f'IF(C{r}<>"",CONCATENATE(",""",C$2,""":""",C{r},""""),"")', v_AE),
        ("AF", f'IF(D{r}<>"",CONCATENATE(",""",D$2,""":""",D{r},""""),"")', v_AF),
        ("AG", f'IF(E{r}<>"",CONCATENATE(",""",E$2,""":""",E{r},""""),"")', v_AG),
        ("AH", f'IF(F{r}<>"",CONCATENATE(",""representations"":[{{""file"":""",F{r},""",""unit"":",G{r},"}}]"),"")', v_AH),
        ("AI", f'IF(H{r}<>"",CONCATENATE(",""",H$2,""":[",H{r},",",I{r},",",J{r},"]"),"")', v_AI),
        ("AJ", f'IF(K{r}<>"",CONCATENATE(",""",K$2,""":[",K{r},",",L{r},",",M{r},"]"),"")', v_AJ),
        ("AK", f'IF(N{r}<>"",CONCATENATE(",""",N$2,""":""",N{r},""""),"")', v_AK),
        ("AL", f'IF(O{r}<>"",CONCATENATE(",""",O$2,""":""",O{r},""""),"")', v_AL),
        ("AM", f'IF(P{r}<>"",CONCATENATE(",""",P$2,""":[""",P{r},"""]"),"")', v_AM),
        ("AN", f'IF(Q{r}<>"",CONCATENATE(",""",Q$2,""":[""",Q{r},"""]"),"")', v_AN),
        ("AO", f'IF(R{r}<>"",CONCATENATE(",""",R$2,""":[""",R{r},"""]"),"")', v_AO),
        ("AP", f'IF(S{r}<>"",CONCATENATE(",""",S$2,""":",S{r}),"")', v_AP),
        ("AQ", f'IF(T{r}<>"",CONCATENATE(",""",T$2,""":{{",T{r},"}}"),"")', v_AQ),
        ("AR", f'IF(U{r}<>"",CONCATENATE(",""failureModes"":[{{""TTF"":""",U{r},""",""TTR"":""",V{r},"""}}",IF(W{r}<>"",CONCATENATE(",{{""TTF"":""",W{r},""",""TTR"":""",X{r},"""}}"),""),"]"),"")', v_AR),
        ("AS", f'IF(Y{r}<>"",CONCATENATE(",""",Y$2,""":",SUBSTITUTE(SUBSTITUTE(Y{r}, CHAR(10)," "), CHAR(9)," ")),"")', v_AS),
        ("AT", f'IF(Z{r}<>"",CONCATENATE(",""",Z$2,""":[",Z{r},"]"),"")', v_AT),
        ("AU", f'IF(AA{r}<>"",CONCATENATE(",""",AA$2,""":",AA{r}),"")', v_AU),
        ("AV", f'IF(AB{r}<>"",CONCATENATE(",""",AB$2,""":[",AB{r},"]"),"")', v_AV),
    ]
    for col, f_str, val_str in formulas:
        cells.append(make_cell(col, r, styles.get(col), value=val_str, formula=f_str))

    cells.append(make_cell("AW", r, styles.get("AW"), value="}"))
    f_AX = f"CONCATENATE(AD{r},AE{r},AF{r},AG{r},AH{r},AI{r},AJ{r},AK{r},AL{r},AM{r},AN{r},AO{r},AP{r},AQ{r},AR{r},AS{r},AT{r},AU{r},AV{r},AW{r})"
    cells.append(make_cell("AX", r, styles.get("AX"), value=v_AX, formula=f_AX))
    cells.append(make_cell("AY", r, styles.get("AY"), value=" "))

    for c_el in cells:
        r_el.append(c_el)
    return ET.tostring(r_el, encoding="unicode"), v_AX


def build_anim_row_xml(row_idx, node, styles):
    """Build a <row> XML string for xl/worksheets/sheet3.xml (Anim)."""
    r_el = ET.Element("row")
    r_el.set("r", str(row_idx))
    r_el.set("spans", "1:23")

    aid = node.get("id", "")
    action = node.get("actions", [{}])[0]
    trig = action.get("trigger", {})
    ev = action.get("event", {})

    ts_ms = int(float(trig.get("data", "0")))
    ts_sec = ts_ms / 1000.0
    ev_type = ev.get("type", "")
    ev_data = ev.get("data", "")
    descr = ev.get("descr", "")
    pos = ev.get("position")
    rot = ev.get("rotation")
    rel_to = ev.get("placementRelTo", "")

    pos_str = json.dumps(pos) if pos is not None else ""
    rot_str = json.dumps(rot) if rot is not None else ""

    cells = []
    r = row_idx

    def add_in(col, val, is_num=False):
        if val is not None and val != "":
            cells.append(make_cell(col, r, styles.get(col), value=val, is_num=is_num))

    add_in("A", aid)
    add_in("B", ts_sec, is_num=True)
    add_in("C", ev_type)
    add_in("D", ev_data)
    add_in("E", descr)
    add_in("F", pos_str)
    add_in("G", rot_str)
    add_in("H", rel_to)

    v_J = "{"
    v_K = f'"id": "{aid}"' if aid else ""
    v_L = ', "actions": [{"trigger": {"type": "timestamp", "data": "'
    v_M = str(ts_ms)
    v_N = '"}, "event": {"type":'
    v_O = f'"{ev_type}"'
    v_P = f',"data": "{ev_data}"' if ev_data else ""
    v_Q = f',"descr": "{descr}"' if descr else ""
    v_R = f',"position": {pos_str}' if pos_str else ""
    v_S = f',"rotation": {rot_str}' if rot_str else ""
    v_T = f',"placementRelTo": "{rel_to}"' if rel_to else ""
    v_U = "} } ] }"
    v_V = (v_J + v_K + v_L + v_M + v_N + v_O + v_P + v_Q + v_R + v_S + v_T + v_U) if aid else ""

    cells.append(make_cell("J", r, styles.get("J"), value=v_J))
    cells.append(make_cell("K", r, styles.get("K"), value=v_K, formula=f'IF(A{r}<>"",CONCATENATE("""",A$2,""": """,$B$1,A{r},""""),"")'))
    cells.append(make_cell("L", r, styles.get("L"), value=v_L))
    cells.append(make_cell("M", r, styles.get("M"), value=v_M, formula=f"B{r}*1000", is_num=True))
    cells.append(make_cell("N", r, styles.get("N"), value=v_N))
    cells.append(make_cell("O", r, styles.get("O"), value=v_O, formula=f'CONCATENATE("""",C{r},"""")'))
    cells.append(make_cell("P", r, styles.get("P"), value=v_P, formula=f'IF(D{r}<>"",CONCATENATE(",""",D$2,""": """,D{r},""""),"")'))
    cells.append(make_cell("Q", r, styles.get("Q"), value=v_Q, formula=f'IF(E{r}<>"",CONCATENATE(",""",E$2,""": """,E{r},""""),"")'))
    cells.append(make_cell("R", r, styles.get("R"), value=v_R, formula=f'IF(F{r}<>"",CONCATENATE(",""",F$2,""": ",F{r}),"")'))
    cells.append(make_cell("S", r, styles.get("S"), value=v_S, formula=f'IF(G{r}<>"",CONCATENATE(",""",G$2,""": ",G{r}),"")'))
    cells.append(make_cell("T", r, styles.get("T"), value=v_T, formula=f'IF(H{r}<>"",CONCATENATE(",""",H$2,""": """,H{r},""""),"")'))
    cells.append(make_cell("U", r, styles.get("U"), value=v_U))
    cells.append(make_cell("V", r, styles.get("V"), value=v_V, formula=f'IF(A{r}<>"",CONCATENATE(J{r},K{r},L{r},M{r},N{r},O{r},P{r},Q{r},R{r},S{r},T{r},U{r}),"")'))
    cells.append(make_cell("W", r, styles.get("W"), value=" "))

    for c_el in cells:
        r_el.append(c_el)
    return ET.tostring(r_el, encoding="unicode"), v_V


def splice_sheet_rows(xml_bytes, build_rows_fn, max_col):
    """Replace rows >= 3 in a worksheet XML string while preserving all headers, namespaces, and controls."""
    xml_text = xml_bytes.decode("utf-8")
    styles = extract_row_styles(xml_text)

    row3_idx = xml_text.find('<row r="3"')
    end_sd_idx = xml_text.find("</sheetData>")
    assert end_sd_idx != -1, "Missing </sheetData> in worksheet"
    start_replace = row3_idx if row3_idx != -1 else end_sd_idx

    row_xml_strings, row_count = build_rows_fn(styles)
    new_xml = xml_text[:start_replace] + "".join(row_xml_strings) + xml_text[end_sd_idx:]

    last_r = max(2, 2 + row_count)
    new_xml = re.sub(
        r'<dimension ref="[^"]+"/>',
        f'<dimension ref="A1:{max_col}{last_r}"/>',
        new_xml,
        count=1,
    )
    # Verify well-formed XML before writing
    ET.fromstring(new_xml)
    return new_xml.encode("utf-8")


def sync(model_dir):
    xlsm_path = os.path.join(model_dir, "DFE_01.xlsm")
    scene_path = os.path.join(model_dir, "DFE_01.json")
    anim_path = os.path.join(model_dir, "DFE_01_anim.json")

    with open(scene_path, "r", encoding="utf-8") as f:
        scene_data = json.load(f)
    with open(anim_path, "r", encoding="utf-8") as f:
        anim_data = json.load(f)

    in_scene_set = set(scene_data.get("scene", []))
    assets = scene_data.get("assets", [])
    nodes = anim_data.get("nodes", [])

    ax_values = []
    v_values = []

    def make_asset_rows(styles):
        rows = []
        for idx, asset in enumerate(assets, start=3):
            row_xml, v_ax = build_asset_row_xml(idx, asset, in_scene_set, styles)
            rows.append(row_xml)
            ax_values.append(v_ax)
        return rows, len(rows)

    def make_anim_rows(styles):
        rows = []
        for idx, node in enumerate(nodes, start=3):
            row_xml, v_v = build_anim_row_xml(idx, node, styles)
            rows.append(row_xml)
            v_values.append(v_v)
        return rows, len(rows)

    fd, tmp_path = tempfile.mkstemp(suffix=".xlsm")
    os.close(fd)

    try:
        with zipfile.ZipFile(xlsm_path, "r") as zin, zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "xl/calcChain.xml":
                    continue
                data = zin.read(item.filename)
                if item.filename == "xl/worksheets/sheet2.xml":
                    data = splice_sheet_rows(data, make_asset_rows, max_col="AZ")
                elif item.filename == "xl/worksheets/sheet3.xml":
                    data = splice_sheet_rows(data, make_anim_rows, max_col="W")
                elif item.filename == "[Content_Types].xml":
                    text = data.decode("utf-8").replace(
                        '<Override PartName="/xl/calcChain.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.calcChain+xml"/>',
                        "",
                    )
                    data = text.encode("utf-8")
                elif item.filename == "xl/_rels/workbook.xml.rels":
                    text = re.sub(
                        r'<Relationship\b[^>]*calcChain\.xml"[^>]*/>',
                        "",
                        data.decode("utf-8"),
                    )
                    ET.fromstring(text)
                    data = text.encode("utf-8")
                zout.writestr(item, data)

        shutil.move(tmp_path, xlsm_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    parsed_assets = [json.loads(s) for s in ax_values]
    parsed_nodes = [json.loads(s) for s in v_values]
    assert len(parsed_assets) == len(assets), "Asset count mismatch"
    assert len(parsed_nodes) == len(nodes), "Anim node count mismatch"
    print(f"Synced {len(assets)} assets and {len(nodes)} animation events into {xlsm_path}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sync(base_dir)
