#!/usr/bin/env python3
import argparse
import subprocess
import os
import sys
import json
import glob
import shutil

def find_gerber_file(directory, layer_name_part, extensions):
    """Finds a gerber file for a specific layer by looking for a name part."""
    for ext in extensions:
        # KiCad 8+ style: *-F_Cu.gbr
        files = glob.glob(os.path.join(directory, f'*-{layer_name_part}.{ext}'))
        if files:
            return files[0]
    # Fallback for simpler names or other conventions
    for ext in extensions:
        files = glob.glob(os.path.join(directory, f'*.{ext}'))
        for f in files:
            if layer_name_part.lower() in os.path.basename(f).lower():
                return f
    # Last resort for copper, take any .gbr
    if 'cu' in layer_name_part.lower():
        for ext in ['gbr', 'gtl']:
            files = glob.glob(os.path.join(directory, f'*.{ext}'))
            if files:
                return files[0]
    return None

def find_drill_file(directory):
    """Finds the drill file."""
    for ext in ['drl', 'txt']:
        files = glob.glob(os.path.join(directory, f'*.{ext}'))
        if files:
            return files[0]
    return None

def generate_gcode(input_dir, output_nc_file):
    """
    Uses pcb2gcode to generate G-Code for isolation milling from Gerber files.
    """
    # --- Parámetros para la CNC (ajustables) ---
    BIT_DIAMETER = 0.2
    ISOLATION_PASSES = 2
    Z_CUT = -0.07
    Z_SAFE = 2.0
    Z_CHANGE = 10.0
    Z_CUT_BOARD = -2.0 # Profundidad de corte del borde (outline)
    Z_DRILL = -2.0     # Profundidad de taladrado
    FEEDRATE = 200
    CUT_FEED = 100     # Velocidad de corte de borde
    CUT_SPEED = 12000  # Spindle para corte
    CUT_INFEED = 100   # Velocidad de entrada para corte
    DRILL_FEED = 100   # Velocidad de bajada taladro
    DRILL_SPEED = 12000 # Spindle para taladro

    # --- Identificar archivos Gerber ---
    front_copper_file = find_gerber_file(input_dir, 'F_Cu', ['gbr', 'gtl'])
    drill_file = find_drill_file(input_dir)
    outline_file = find_gerber_file(input_dir, 'Edge_Cuts', ['gbr', 'gko', 'gm1'])

    if not front_copper_file:
        return {"status": "error", "message": "No se encontró el archivo de cobre frontal (ej: *-F_Cu.gbr)."}

    temp_output_dir = os.path.join(os.path.dirname(output_nc_file), "gcode_temp")
    if os.path.exists(temp_output_dir): shutil.rmtree(temp_output_dir)
    os.makedirs(temp_output_dir, exist_ok=True)

    command = [
        "pcb2gcode",
        f"--front={front_copper_file}",
        f"--mill-feed={FEEDRATE}", f"--mill-speed=12000",
        f"--zwork={Z_CUT}", f"--zsafe={Z_SAFE}",
        f"--zchange={Z_CHANGE}",
        f"--zcut={Z_CUT_BOARD}",
        f"--cut-feed={CUT_FEED}", f"--cut-speed={CUT_SPEED}", f"--cut-infeed={CUT_INFEED}",
        f"--zdrill={Z_DRILL}",
        f"--drill-feed={DRILL_FEED}", f"--drill-speed={DRILL_SPEED}",
        f"--cutter-diameter={BIT_DIAMETER}", 
        f"--offset={BIT_DIAMETER / 2}",
        f"--svg=preview.svg", # Generar vista previa SVG
        # f"--isolation-passes={ISOLATION_PASSES}", # Comentado por incompatibilidad con versiones antiguas de pcb2gcode
        "--metric"
    ]
    
    if drill_file: command.append(f"--drill={drill_file}")
    if outline_file: command.append(f"--outline={outline_file}")

    try:
        # Ejecutar el comando desde el directorio temporal para que los archivos de salida se creen allí.
        # check=False para permitir que pcb2gcode termine aunque tenga warnings (ej: clearance best effort)
        result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=temp_output_dir)
        
        # Verificar si se generó el archivo (puede ser .nc o .ngc dependiendo de la versión)
        generated_mill_file = os.path.join(temp_output_dir, 'front.nc')
        if not os.path.exists(generated_mill_file):
            generated_mill_file = os.path.join(temp_output_dir, 'front.ngc')

        if os.path.exists(generated_mill_file):
            shutil.move(generated_mill_file, output_nc_file)
            
            # Manejar vista previa SVG
            output_svg_file = output_nc_file.replace('.nc', '.svg')
            generated_svg_file = os.path.join(temp_output_dir, 'preview.svg')
            preview_file = None
            if os.path.exists(generated_svg_file):
                shutil.move(generated_svg_file, output_svg_file)
                preview_file = output_svg_file

            return {"status": "success", "file": output_nc_file, "preview": preview_file}
        else:
            return {"status": "error", "message": f"pcb2gcode falló (No generó archivo):\n{result.stderr}"}
    except FileNotFoundError:
        return {"status": "error", "message": "El comando 'pcb2gcode' no se encontró. Reconstruye el sandbox."}
    finally:
        if os.path.exists(temp_output_dir): shutil.rmtree(temp_output_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera G-Code desde archivos Gerber usando pcb2gcode.")
    parser.add_argument("--input-dir", required=True, help="Directorio que contiene los archivos Gerber.")
    parser.add_argument("--output-file", required=True, help="Ruta del archivo G-Code (.nc) de salida.")
    args = parser.parse_args()
    result = generate_gcode(args.input_dir, args.output_file)
    print(json.dumps(result))
    if result["status"] == "error": sys.exit(1)