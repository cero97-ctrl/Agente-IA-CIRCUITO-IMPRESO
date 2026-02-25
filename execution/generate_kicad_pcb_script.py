#!/usr/bin/env python3
"""
Genera un script Python que, al ser ejecutado dentro de la Consola de Scripting
de KiCad PCB Editor (pcbnew), crea un archivo .kicad_pcb con los componentes
colocados y las conexiones (ratsnest) definidas a partir de un JSON de diseño.
"""
import json
import argparse
import os
import sys

# Este script NO importa pcbnew directamente, ya que está diseñado para
# generar otro script que SÍ lo importará dentro de KiCad.

def generate_pcb_script(design_json_path, output_script_path):
    """
    Crea un script Python para KiCad PCB Editor.
    """
    # Cargar el JSON de diseño
    try:
        with open(design_json_path, 'r') as f:
            design_data = json.load(f)
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"Error leyendo JSON de diseño: {e}"}))
        sys.exit(1)

    components = design_data.get("components", [])
    netlist_data = design_data.get("netlist", [])

    # Generar el contenido del script de KiCad
    script_lines = [
        "import pcbnew",
        "import os",
        "import json",
        "",
        "# --- Configuración de la Placa ---",
        "BOARD_WIDTH_MM = 100",
        "BOARD_HEIGHT_MM = 70",
        "GRID_SPACING_X_MM = 25",
        "GRID_SPACING_Y_MM = 25",
        "START_X_MM = 20",
        "START_Y_MM = 20",
        "",
        "# --- Helper para convertir mm a unidades internas de KiCad (nanómetros) ---",
        "def mm_to_nm(mm_val):",
        "    return int(mm_val * 1000000)",
        "",
        "# --- Crear una nueva placa ---",
        "board = pcbnew.BOARD()",
        "",
        "# --- Definir el contorno de la placa (Edge.Cuts) ---",
        "edge_layer = pcbnew.Edge_Cuts",
        "board_outline = pcbnew.PCB_SHAPE(board)",
        "board_outline.SetShape(pcbnew.SHAPE_T_RECT)",
        "board_outline.SetStart(pcbnew.wxPoint(mm_to_nm(0), mm_to_nm(0)))",
        "board_outline.SetEnd(pcbnew.wxPoint(mm_to_nm(BOARD_WIDTH_MM), mm_to_nm(BOARD_HEIGHT_MM)))",
        "board_outline.SetLayer(edge_layer)",
        "board.Add(board_outline)",
        "",
        "# --- Datos de componentes y netlist (inyectados desde el JSON original) ---",
        f"components_data = {json.dumps(components, indent=2)}",
        f"netlist_data = {json.dumps(netlist_data, indent=2)}",
        "",
        "# --- Cargar y colocar Footprints (Huellas) ---",
        "footprints_by_ref = {}",
        "for i, comp in enumerate(components_data):",
        "    ref = comp['ref']",
        "    footprint_name = comp.get('footprint', 'Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal') # Nombre de la huella",
        "    ",
        "    # Calcular posición en una cuadrícula simple",
        "    col = i % (BOARD_WIDTH_MM // GRID_SPACING_X_MM)",
        "    row = i // (BOARD_WIDTH_MM // GRID_SPACING_X_MM)",
        "    pos_x_mm = START_X_MM + col * GRID_SPACING_X_MM",
        "    pos_y_mm = START_Y_MM + row * GRID_SPACING_Y_MM",
        "    ",
        "    # Intentar cargar la huella desde las librerías de KiCad",
        "    # Esto requiere que la librería esté configurada en KiCad",
        "    try:",
        "        footprint_lib_id = footprint_name.split(':', 1)",
        "        if len(footprint_lib_id) == 2:",
        "            lib_name, fp_name = footprint_lib_id",
        "            fp = pcbnew.FootprintLoad(lib_name, fp_name)",
        "        else:",
        "            # Si no tiene formato 'Lib:Footprint', intentar cargar directamente por nombre",
        "            fp = pcbnew.FootprintLoad('', footprint_name)",
        "        ",
        "        if fp is None:",
        "            raise Exception('FootprintLoad devolvió None')",
        "        ",
        "        fp.SetReference(ref)",
        "        fp.SetPosition(pcbnew.wxPoint(mm_to_nm(pos_x_mm), mm_to_nm(pos_y_mm)))",
        "        fp.SetLayer(pcbnew.F_Cu) # Colocar en la capa frontal",
        "        board.Add(fp)",
        "        footprints_by_ref[ref] = fp",
        "        print(f'Footprint {ref} ({footprint_name}) colocado en ({pos_x_mm:.2f}, {pos_y_mm:.2f})')",
        "    except Exception as e:",
        "        print(f'Error cargando footprint {footprint_name} para {ref}: {e}')",
        "        # Crear un footprint genérico como fallback si falla la carga",
        "        fp = pcbnew.FOOTPRINT(board)",
        "        fp.SetReference(ref)",
        "        fp.SetPosition(pcbnew.wxPoint(mm_to_nm(pos_x_mm), mm_to_nm(pos_y_mm)))",
        "        fp.SetLayer(pcbnew.F_Cu)",
        "        board.Add(fp)",
        "        footprints_by_ref[ref] = fp",
        "",
        "# --- Crear Netlist y conectar Pads ---",
        "nets_by_name = {}",
        "for net_info in netlist_data:",
        "    net_name = net_info.get('net_name') or net_info.get('netname')",
        "    if net_name not in nets_by_name:",
        "        net = pcbnew.NETINFO_ITEM(board, net_name)",
        "        board.Add(net)",
        "        nets_by_name[net_name] = net",
        "    else:",
        "        net = nets_by_name[net_name]",
        "    ",
        "    for node in net_info['nodes']:",
        "        ref, pin_num = node.split('-')",
        "        if ref in footprints_by_ref:",
        "            fp = footprints_by_ref[ref]",
        "            pad = fp.FindPadByNumber(pin_num)",
        "            if pad:",
        "                pad.SetNetCode(net.GetNetCode())",
        "            else:",
        "                print(f'Warning: Pad {pin_num} not found for {ref}.')",
        "        else:",
        "            print(f'Warning: Footprint {ref} not found in placed components for net {net_name}.')",
        "",
        "# --- Enrutado Básico (solo Ratsnest por ahora) ---",
        "# Para un enrutado automático real, se necesitaría un algoritmo de enrutado (ej. A*)",
        "# y manejo de capas, vías, reglas de diseño, etc. Por ahora, solo se mostrará el ratsnest.",
        "",
        "# --- Guardar la placa ---",
        "output_dir = '/mnt/out' if os.path.exists('/mnt/out') else os.path.dirname(os.path.abspath(__file__))",
        "output_filename = os.path.join(output_dir, 'circuito_generado.kicad_pcb')",
        "pcbnew.SaveBoard(output_filename, board)",
        "print(f'PCB guardado en: {output_filename}')",
    ]

    # Escribir el script generado en el archivo de salida
    try:
        os.makedirs(os.path.dirname(output_script_path) or ".", exist_ok=True)
        with open(output_script_path, 'w') as f:
            f.write("\n".join(script_lines))
        print(json.dumps({"status": "success", "file": output_script_path}))
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"Error escribiendo script de PCB: {e}"}))
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera un script Python para crear un archivo KiCad PCB (.kicad_pcb).")
    parser.add_argument("--json", required=True, help="Ruta al archivo JSON de diseño.")
    parser.add_argument("--output", required=True, help="Ruta de salida para el script Python generado.")
    args = parser.parse_args()

    generate_pcb_script(args.json, args.output)