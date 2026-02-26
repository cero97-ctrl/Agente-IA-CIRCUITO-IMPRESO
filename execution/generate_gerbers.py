#!/usr/bin/env python3
import pcbnew
import os
import sys
import json
import zipfile
import shutil
import argparse

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
    popt.SetExcludeEdgeLayer(True)
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

def main():
    parser = argparse.ArgumentParser(description="Genera un paquete de fabricación (Gerber+Drill) desde un archivo .kicad_pcb.")
    parser.add_argument("--board", required=True, help="Ruta al archivo .kicad_pcb de entrada.")
    parser.add_argument("--output-zip", required=True, help="Ruta del archivo ZIP de salida.")
    args = parser.parse_args()

    # Paths are relative to the sandbox environment
    board_file = args.board
    output_zip_file = args.output_zip
    gerber_temp_dir = "gerbers_temp"

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

if __name__ == "__main__":
    main()