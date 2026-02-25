#!/usr/bin/env python3
"""Converts a JSON design (from AI circuit analysis) to KiCad 9.0 native schematic (.kicad_sch).
Replaces the old netlist (export) format with the native S-expression schematic format."""
import json
import argparse
import sys
import os
import re
import uuid as uuid_module
import datetime

def new_uuid():
    return str(uuid_module.uuid4())

# ---------------------------------------------------------------------------
# Pin definitions for each symbol type
# rel_x/rel_y: position relative to symbol origin
# body_angle: direction FROM connection point TOWARD body (KiCad screen convention)
#   0=right, 90=down, 180=left, 270=up
# ---------------------------------------------------------------------------
PIN_INFO = {
    "Device:R": [
        {"num": "1", "rx": 0, "ry": 3.81,  "ba": 270},
        {"num": "2", "rx": 0, "ry": -3.81, "ba": 90},
    ],
    "Device:C": [
        {"num": "1", "rx": 0, "ry": 3.81,  "ba": 270},
        {"num": "2", "rx": 0, "ry": -3.81, "ba": 90},
    ],
    "Device:C_Polarized": [
        {"num": "1", "rx": 0, "ry": 3.81,  "ba": 270},
        {"num": "2", "rx": 0, "ry": -3.81, "ba": 90},
    ],
    "Device:LED": [
        {"num": "1", "rx": -1.27, "ry": 0, "ba": 0},
        {"num": "2", "rx": 1.27,  "ry": 0, "ba": 180},
    ],
    "Device:D": [
        {"num": "1", "rx": -1.27, "ry": 0, "ba": 0},
        {"num": "2", "rx": 1.27,  "ry": 0, "ba": 180},
    ],
    "Timer:NE555": [
        {"num": "1", "rx": -7.62, "ry": 5.08,  "ba": 0},    # GND
        {"num": "2", "rx": -7.62, "ry": 2.54,  "ba": 0},    # TR
        {"num": "3", "rx": 7.62,  "ry": 2.54,  "ba": 180},  # Q
        {"num": "4", "rx": -2.54, "ry": -8.89, "ba": 90},   # R
        {"num": "5", "rx": 7.62,  "ry": -2.54, "ba": 180},  # CV
        {"num": "6", "rx": -7.62, "ry": -2.54, "ba": 0},    # THR
        {"num": "7", "rx": -7.62, "ry": -5.08, "ba": 0},    # DIS
        {"num": "8", "rx": 2.54,  "ry": -8.89, "ba": 90},   # VCC
    ],
}

# ---------------------------------------------------------------------------
# Library symbol S-expression templates
# ---------------------------------------------------------------------------
def _font(sz=1.27):
    return f'(font (size {sz} {sz}))'

def _effects(sz=1.27, hide=False, justify=""):
    h = " hide" if hide else ""
    j = f' (justify {justify})' if justify else ""
    return f'(effects {_font(sz)}{j}{h})'

def _pin(ptype, x, y, angle, length, name, number):
    return (f'        (pin {ptype} line (at {x} {y} {angle}) (length {length})\n'
            f'          (name "{name}" {_effects()})\n'
            f'          (number "{number}" {_effects()})\n'
            f'        )')

def lib_sym_resistor():
    return f"""    (symbol "Device:R"
      (pin_numbers hide)
      (pin_names (offset 0))
      (in_bom yes) (on_board yes)
      (property "Reference" "R" (at 2.032 0 90) {_effects()})
      (property "Value" "R" (at -1.778 0 90) {_effects()})
      (property "Footprint" "" (at 0 0 0) {_effects(hide=True)})
      (property "Datasheet" "~" (at 0 0 0) {_effects(hide=True)})
      (symbol "R_0_1"
        (rectangle (start -1.016 -2.54) (end 1.016 2.54)
          (stroke (width 0.254) (type default)) (fill (type none))))
      (symbol "R_1_1"
{_pin("passive", 0, 3.81, 270, 1.27, "~", "1")}
{_pin("passive", 0, -3.81, 90, 1.27, "~", "2")}
      )
    )"""

def lib_sym_capacitor():
    return f"""    (symbol "Device:C"
      (pin_numbers hide)
      (pin_names (offset 0.254))
      (in_bom yes) (on_board yes)
      (property "Reference" "C" (at 0.635 2.54 0) {_effects(justify="left")})
      (property "Value" "C" (at 0.635 -2.54 0) {_effects(justify="left")})
      (property "Footprint" "" (at 0 0 0) {_effects(hide=True)})
      (property "Datasheet" "~" (at 0 0 0) {_effects(hide=True)})
      (symbol "C_0_1"
        (polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762))
          (stroke (width 0.508) (type default)) (fill (type none)))
        (polyline (pts (xy -2.032 0.762) (xy 2.032 0.762))
          (stroke (width 0.508) (type default)) (fill (type none))))
      (symbol "C_1_1"
{_pin("passive", 0, 3.81, 270, 2.794, "~", "1")}
{_pin("passive", 0, -3.81, 90, 2.794, "~", "2")}
      )
    )"""

def lib_sym_cpolarized():
    return f"""    (symbol "Device:C_Polarized"
      (pin_numbers hide)
      (pin_names (offset 0.254))
      (in_bom yes) (on_board yes)
      (property "Reference" "C" (at 0.635 2.54 0) {_effects(justify="left")})
      (property "Value" "C_Polarized" (at 0.635 -2.54 0) {_effects(justify="left")})
      (property "Footprint" "" (at 0 0 0) {_effects(hide=True)})
      (property "Datasheet" "~" (at 0 0 0) {_effects(hide=True)})
      (symbol "C_Polarized_0_1"
        (polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762))
          (stroke (width 0.508) (type default)) (fill (type none)))
        (polyline (pts (xy -2.032 0.762) (xy 2.032 0.762))
          (stroke (width 0.508) (type default)) (fill (type none)))
        (polyline (pts (xy -1.27 1.524) (xy -0.508 1.524))
          (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy -0.889 1.143) (xy -0.889 1.905))
          (stroke (width 0.254) (type default)) (fill (type none))))
      (symbol "C_Polarized_1_1"
{_pin("passive", 0, 3.81, 270, 2.794, "+", "1")}
{_pin("passive", 0, -3.81, 90, 2.794, "-", "2")}
      )
    )"""

def lib_sym_led():
    return f"""    (symbol "Device:LED"
      (pin_numbers hide)
      (pin_names (offset 1.016) hide)
      (in_bom yes) (on_board yes)
      (property "Reference" "D" (at 0 2.54 0) {_effects()})
      (property "Value" "LED" (at 0 -2.54 0) {_effects()})
      (property "Footprint" "" (at 0 0 0) {_effects(hide=True)})
      (property "Datasheet" "~" (at 0 0 0) {_effects(hide=True)})
      (symbol "LED_0_1"
        (polyline (pts (xy -1.27 -1.27) (xy -1.27 1.27))
          (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy -1.27 0) (xy 1.27 0))
          (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 -1.27) (xy 1.27 1.27) (xy -1.27 0) (xy 1.27 -1.27))
          (stroke (width 0.254) (type default)) (fill (type none))))
      (symbol "LED_1_1"
{_pin("passive", -3.81, 0, 0, 2.54, "K", "1")}
{_pin("passive", 3.81, 0, 180, 2.54, "A", "2")}
      )
    )"""

def lib_sym_diode():
    return f"""    (symbol "Device:D"
      (pin_numbers hide)
      (pin_names (offset 1.016) hide)
      (in_bom yes) (on_board yes)
      (property "Reference" "D" (at 0 2.54 0) {_effects()})
      (property "Value" "D" (at 0 -2.54 0) {_effects()})
      (property "Footprint" "" (at 0 0 0) {_effects(hide=True)})
      (property "Datasheet" "~" (at 0 0 0) {_effects(hide=True)})
      (symbol "D_0_1"
        (polyline (pts (xy -1.27 1.27) (xy -1.27 -1.27))
          (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 0) (xy -1.27 0))
          (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 -1.27) (xy 1.27 1.27) (xy -1.27 0) (xy 1.27 -1.27))
          (stroke (width 0.254) (type default)) (fill (type none))))
      (symbol "D_1_1"
{_pin("passive", -3.81, 0, 0, 2.54, "K", "1")}
{_pin("passive", 3.81, 0, 180, 2.54, "A", "2")}
      )
    )"""

def lib_sym_ne555():
    return f"""    (symbol "Timer:NE555"
      (pin_names (offset 1.016))
      (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 10.16 0) {_effects()})
      (property "Value" "NE555" (at 0 -10.16 0) {_effects()})
      (property "Footprint" "" (at 0 0 0) {_effects(hide=True)})
      (property "Datasheet" "~" (at 0 0 0) {_effects(hide=True)})
      (symbol "NE555_0_1"
        (rectangle (start -5.08 -6.35) (end 5.08 6.35)
          (stroke (width 0.254) (type default)) (fill (type background))))
      (symbol "NE555_1_1"
{_pin("power_in",  -7.62,  5.08,  0,   2.54, "GND", "1")}
{_pin("input",     -7.62,  2.54,  0,   2.54, "TR",  "2")}
{_pin("output",     7.62,  2.54,  180, 2.54, "Q",   "3")}
{_pin("input",     -2.54, -8.89,  90,  2.54, "R",   "4")}
{_pin("input",      7.62, -2.54,  180, 2.54, "CV",  "5")}
{_pin("input",     -7.62, -2.54,  0,   2.54, "THR", "6")}
{_pin("input",     -7.62, -5.08,  0,   2.54, "DIS", "7")}
{_pin("power_in",   2.54, -8.89,  90,  2.54, "VCC", "8")}
      )
    )"""

LIB_SYMBOL_GENERATORS = {
    "Device:R": lib_sym_resistor,
    "Device:C": lib_sym_capacitor,
    "Device:C_Polarized": lib_sym_cpolarized,
    "Device:LED": lib_sym_led,
    "Device:D": lib_sym_diode,
    "Timer:NE555": lib_sym_ne555,
}

# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------
def classify_component(comp):
    """Return (lib_id, footprint) for a component dict."""
    ctype = (comp.get("type") or "").lower()
    cval  = (comp.get("value") or "").lower()
    
    if "resistor" in ctype or "resistencia" in ctype:
        lib_id = "Device:R"
        fp = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"
    elif "capacitor" in ctype or "condensador" in ctype:
        if any(kw in ctype for kw in ("electrolytic", "electrolítico", "electrolitico", "polarized")):
            lib_id = "Device:C_Polarized"
            fp = "Capacitor_THT:CP_Radial_D5.0mm_P2.50mm"
        else:
            lib_id = "Device:C"
            fp = "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
    elif "led" in ctype:
        lib_id = "Device:LED"
        fp = "LED_THT:LED_D5.0mm"
    elif "diode" in ctype or "diodo" in ctype:
        lib_id = "Device:D"
        fp = "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal"
    elif "555" in cval or "timer" in ctype or "ne555" in cval:
        lib_id = "Timer:NE555"
        fp = "Package_DIP:DIP-8_W7.62mm"
    else:
        lib_id = "Device:R"
        fp = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"
    return lib_id, fp

# ---------------------------------------------------------------------------
# Stub direction from pin body angle (opposite direction)
# ---------------------------------------------------------------------------
STUB_LEN = 5.08  # 2 grid units

def stub_offset(body_angle):
    """Return (dx, dy) for wire stub extending AWAY from body."""
    return {
        0:   (-STUB_LEN, 0),       # body right → stub left
        90:  (0, -STUB_LEN),       # body down  → stub up
        180: (STUB_LEN, 0),        # body left  → stub right
        270: (0, STUB_LEN),        # body up    → stub down
    }[body_angle]

def label_angle(body_angle):
    """Label text direction at stub end."""
    return {0: 180, 90: 90, 180: 0, 270: 270}[body_angle]

# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------
def generate_kicad_sch(design_json, output_file):
    # --- Parse input JSON ---
    try:
        if isinstance(design_json, str):
            content = design_json
            if os.path.exists(design_json):
                with open(design_json, 'r') as f:
                    content = f.read()
            content = content.strip()
            if "```" in content:
                match = re.search(r"```(?:json)?(.*?)```", content, re.DOTALL)
                if match:
                    content = match.group(1).strip()
                else:
                    content = content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
        else:
            data = design_json
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"Error leyendo JSON: {e}"}))
        sys.exit(1)

    root_uuid = new_uuid()
    project_name = os.path.splitext(os.path.basename(output_file))[0]
    components = data.get("components", [])
    nets = data.get("netlist", [])

    # --- Determine which lib_symbols are needed ---
    used_libs = set()
    comp_infos = []
    for comp in components:
        lib_id, fp = classify_component(comp)
        used_libs.add(lib_id)
        comp_infos.append({
            "ref": comp.get("ref", "U?"),
            "value": comp.get("value", "?"),
            "lib_id": lib_id,
            "footprint": fp,
        })

    # --- Build pin-to-net mapping ---
    # net nodes format: "REF-PIN" e.g. "U1-8", "R1-1"
    pin_to_net = {}
    for net in nets:
        net_name = net.get("net_name") or net.get("netname", "unnamed")
        for node in net.get("nodes", []):
            if "-" in node:
                ref, pin = node.split("-", 1)
                pin_norm = pin.lower()
                if "cathode" in pin_norm or pin_norm == "k": pin = "1"
                elif "anode" in pin_norm or pin_norm == "a": pin = "2"
                elif pin_norm in ("pos", "+"): pin = "1"
                elif pin_norm in ("neg", "-"): pin = "2"
                elif "vcc" in pin_norm: pin = "8"
                elif "gnd" in pin_norm: pin = "1"
                pin_to_net[(ref, pin)] = net_name

    # --- Auto-layout: place components in a grid ---
    COLS = 3
    X_SPACING = 50.0
    Y_SPACING = 40.0
    X_START = 80.0
    Y_START = 60.0

    for i, ci in enumerate(comp_infos):
        col = i % COLS
        row = i // COLS
        ci["x"] = X_START + col * X_SPACING
        ci["y"] = Y_START + row * Y_SPACING

    # --- Build output lines ---
    lines = []
    lines.append(f'(kicad_sch (version 20231120) (generator "Agente_IA_CNC") (generator_version "9.0")')
    lines.append(f'  (uuid "{root_uuid}")')
    lines.append(f'  (paper "A4")')
    lines.append(f'  (title_block')
    lines.append(f'    (title "{project_name}")')
    lines.append(f'    (date "{datetime.datetime.now().strftime("%Y-%m-%d")}")')
    lines.append(f'    (comment 1 "Generated by Agente IA CNC")')
    lines.append(f'  )')

    # --- lib_symbols section ---
    lines.append(f'  (lib_symbols')
    for lib_id in sorted(used_libs):
        gen = LIB_SYMBOL_GENERATORS.get(lib_id)
        if gen:
            lines.append(gen())
    lines.append(f'  )')

    # --- Symbol instances ---
    wires = []
    labels = []
    for ci in comp_infos:
        sym_uuid = new_uuid()
        cx, cy = ci["x"], ci["y"]
        lib_id = ci["lib_id"]
        
        lines.append(f'  (symbol (lib_id "{lib_id}") (at {cx} {cy} 0) (unit 1)')
        lines.append(f'    (in_bom yes) (on_board yes)')
        lines.append(f'    (uuid "{sym_uuid}")')
        lines.append(f'    (property "Reference" "{ci["ref"]}" (at {cx} {cy - 5.08} 0) {_effects()})')
        lines.append(f'    (property "Value" "{ci["value"]}" (at {cx} {cy + 5.08} 0) {_effects()})')
        lines.append(f'    (property "Footprint" "{ci["footprint"]}" (at {cx} {cy} 0) {_effects(hide=True)})')
        lines.append(f'    (property "Datasheet" "~" (at {cx} {cy} 0) {_effects(hide=True)})')

        # Pin entries
        pins = PIN_INFO.get(lib_id, [])
        for p in pins:
            lines.append(f'    (pin "{p["num"]}" (uuid "{new_uuid()}"))')

        # Instances
        lines.append(f'    (instances')
        lines.append(f'      (project "{project_name}"')
        lines.append(f'        (path "/{root_uuid}" (reference "{ci["ref"]}") (unit 1))')
        lines.append(f'      )')
        lines.append(f'    )')
        lines.append(f'  )')

        # Generate wire stubs and labels for connected pins
        for p in pins:
            net_name = pin_to_net.get((ci["ref"], p["num"]))
            if not net_name:
                continue
            pin_x = cx + p["rx"]
            pin_y = cy + p["ry"]
            dx, dy = stub_offset(p["ba"])
            end_x = pin_x + dx
            end_y = pin_y + dy
            la = label_angle(p["ba"])
            wires.append((pin_x, pin_y, end_x, end_y))
            labels.append((net_name, end_x, end_y, la))

    # --- Wires ---
    for (x1, y1, x2, y2) in wires:
        lines.append(f'  (wire (pts (xy {x1} {y1}) (xy {x2} {y2}))')
        lines.append(f'    (stroke (width 0) (type default))')
        lines.append(f'    (uuid "{new_uuid()}")')
        lines.append(f'  )')

    # --- Net labels ---
    for (name, lx, ly, la) in labels:
        lines.append(f'  (label "{name}" (at {lx} {ly} {la}) (fields_autoplaced)')
        lines.append(f'    (effects (font (size 1.27 1.27)) (justify left))')
        lines.append(f'    (uuid "{new_uuid()}")')
        lines.append(f'  )')

    # --- Sheet instances ---
    lines.append(f'  (sheet_instances')
    lines.append(f'    (path "/" (page "1"))')
    lines.append(f'  )')

    lines.append(f')')

    # --- Write file ---
    try:
        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
        with open(output_file, "w") as f:
            f.write("\n".join(lines) + "\n")
        print(json.dumps({"status": "success", "file": output_file}))
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"Error escribiendo archivo: {e}"}))
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convertir JSON de diseño a KiCad 9.0 Schematic (.kicad_sch)")
    parser.add_argument("--json", required=True, help="Archivo JSON de entrada")
    parser.add_argument("--output", required=True, help="Archivo .kicad_sch de salida")
    args = parser.parse_args()
    generate_kicad_sch(args.json, args.output)