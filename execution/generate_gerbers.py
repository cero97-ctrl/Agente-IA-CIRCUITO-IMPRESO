#!/usr/bin/env python3
import os, sys, json, zipfile, shutil, argparse, subprocess, time

def generate_gerbers(board_path, output_dir):
    """
    Generates Gerber and Drill files from a .kicad_pcb file.
    """
    # Load the board
    board = pcbnew.LoadBoard(board_path)
    pctl = pcbnew.PLOT_CONTROLLER(board)
    popt = pctl.GetPlotOptions()

    # --- Plot Options ---
    popt.SetOutputDirectory(output_dir)
    popt.SetPlotFrameRef(False)
    popt.SetUseGerberProtelExtensions(True)
    # SetExcludeEdgeLayer fue eliminado en KiCad 8; la exclusión se maneja
    # automáticamente al plotear capa por capa.
    popt.SetUseGerberAttributes(False)
    popt.SetGerberPrecision(6)
    popt.SetCreateGerberJobFile(False)
    popt.SetSubtractMaskFromSilk(True)

    # --- Layers to Plot (Standard for most manufacturers) ---
    layers = [
        ("F.Cu", pcbnew.F_Cu, "Top Copper"),
        ("B.Cu", pcbnew.B_Cu, "Bottom Copper"),
        ("F.Paste", pcbnew.F_Paste, "Top Paste"),
        ("B.Paste", pcbnew.B_Paste, "Bottom Paste"),
        ("F.SilkS", pcbnew.F_SilkS, "Top Silk"),
        ("B.SilkS", pcbnew.B_SilkS, "Bottom Silk"),
        ("F.Mask", pcbnew.F_Mask, "Top Mask"),
        ("B.Mask", pcbnew.B_Mask, "Bottom Mask"),
        ("Edge.Cuts", pcbnew.Edge_Cuts, "Board Outline"),
    ]

    # --- Plot Gerbers ---
    for layer_info in layers:
        pctl.SetLayer(layer_info[1])
        pctl.OpenPlotfile(layer_info[0], pcbnew.PLOT_FORMAT_GERBER, layer_info[2])
        pctl.PlotLayer()
    pctl.ClosePlot()

    # --- Generate Drill Files (Excellon) ---
    drill_writer = pcbnew.EXCELLON_WRITER(board)
    drill_writer.SetMapFileFormat(pcbnew.PLOT_FORMAT_PDF)
    drill_writer.SetFormat(True, pcbnew.EXCELLON_WRITER.DECIMAL_FORMAT, 3, 3)
    drill_writer.CreateDrillandMapFilesSet(output_dir, True, False)

def zip_gerbers(gerber_dir, zip_path):
    """Zips the contents of the gerber directory."""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(gerber_dir):
            for file in files:
                zf.write(os.path.join(root, file), os.path.basename(file))

def run_gerber_generation():
    parser = argparse.ArgumentParser(description="Genera un paquete de fabricación (Gerber+Drill) desde un archivo .kicad_pcb.")
    parser.add_argument("--board", required=True, help="Ruta al archivo .kicad_pcb de entrada.")
    parser.add_argument("--output-zip", required=True, help="Ruta del archivo ZIP de salida.")
    args = parser.parse_args()

    # Paths are relative to the sandbox environment
    board_file = args.board
    output_zip_file = args.output_zip
    
    # Usar un directorio temporal en la misma ubicación que la salida (por ejemplo, /mnt/out)
    # Esto asegura que los archivos temporales sean visibles en .out/ y se limpien con /limpiar
    gerber_temp_dir = os.path.join(os.path.dirname(output_zip_file), "gerbers_temp")

    if not os.path.exists(board_file):
        print(json.dumps({"status": "error", "message": f"Archivo de placa no encontrado: {board_file}"}))
        sys.exit(1)

    if os.path.exists(gerber_temp_dir): shutil.rmtree(gerber_temp_dir)
    os.makedirs(gerber_temp_dir)

    try:
        generate_gerbers(board_file, gerber_temp_dir)
        zip_gerbers(gerber_temp_dir, output_zip_file)
        shutil.rmtree(gerber_temp_dir)
        print(json.dumps({"status": "success", "file": output_zip_file}))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1)

def start_xvfb():
    """Inicia el servidor gráfico virtual si no está corriendo."""
    os.environ['DISPLAY'] = ':99'
    xvfb_proc = None
    try:
        if os.system('pgrep Xvfb > /dev/null') != 0:
            print('Iniciando servidor gráfico virtual (Xvfb)...', file=sys.stderr)
            xvfb_proc = subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1024x768x24', '-ac', '+extension', 'GLX', '+render', '-noreset'])
            time.sleep(3)
            if xvfb_proc.poll() is not None:
                raise RuntimeError(f"Xvfb terminó inesperadamente. Código: {xvfb_proc.returncode}")
    except Exception as e:
        raise RuntimeError(f"Error fatal al iniciar Xvfb: {e}")
    return xvfb_proc

if __name__ == "__main__":
    xvfb_proc = None
    try:
        xvfb_proc = start_xvfb()
        import pcbnew # Importar después de iniciar Xvfb
        run_gerber_generation()
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)
    finally:
        if xvfb_proc:
            xvfb_proc.terminate()