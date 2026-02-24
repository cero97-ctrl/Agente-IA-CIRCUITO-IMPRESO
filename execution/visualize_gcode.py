#!/usr/bin/env python3
import argparse
import matplotlib.pyplot as plt
import re
import os
import sys

def parse_gcode(filepath):
    coords = []
    current_x = 0.0
    current_y = 0.0
    
    # Regex simple para encontrar X e Y (ej: G1 X10.5 Y20.2)
    if not os.path.exists(filepath):
        print(f"❌ Archivo no encontrado: {filepath}", file=sys.stderr)
        return []

    with open(filepath, 'r') as f:
        for line in f:
            line = line.upper().strip()
            # Ignorar comentarios y líneas vacías
            if not line or line.startswith(';') or line.startswith('('):
                continue
            
            # Actualizar estado actual si la línea tiene coordenadas
            match_x = re.search(r'X([\d\.-]+)', line)
            if match_x:
                current_x = float(match_x.group(1))
            
            match_y = re.search(r'Y([\d\.-]+)', line)
            if match_y:
                current_y = float(match_y.group(1))
                
            # Si es un movimiento (G0, G1, G2, G3) o tiene coordenadas, guardamos el punto
            if any(cmd in line for cmd in ['G0', 'G1', 'G2', 'G3', 'X', 'Y']):
                coords.append((current_x, current_y))
                
    return coords

def visualize(gcode_path, output_path):
    coords = parse_gcode(gcode_path)
    
    if not coords:
        print("⚠️ No se encontraron coordenadas válidas para graficar.")
        return

    xs, ys = zip(*coords)
    
    plt.figure(figsize=(10, 8))
    plt.plot(xs, ys, marker='.', linestyle='-', linewidth=1, markersize=3, label='Trayectoria')
    
    # Estética del gráfico
    plt.title(f"Vista Previa: {os.path.basename(gcode_path)}")
    plt.xlabel("X (mm)")
    plt.ylabel("Y (mm)")
    plt.grid(True, which='both', linestyle='--', alpha=0.7)
    plt.axhline(y=0, color='k', linewidth=0.5)
    plt.axvline(x=0, color='k', linewidth=0.5)
    plt.axis('equal') # Importante para no deformar la geometría
    plt.legend()
    
    plt.savefig(output_path, dpi=100)
    plt.close()
    
    # IMPORTANTE: Imprimir la ruta final para que listen_telegram.py la detecte y envíe la foto
    print(output_path)

def main():
    parser = argparse.ArgumentParser(description="Visualizador de G-Code a PNG.")
    parser.add_argument("--input", required=True, help="Archivo G-Code de entrada (.nc)")
    parser.add_argument("--output", default="preview.png", help="Nombre del archivo de salida")
    
    args = parser.parse_args()
    
    # Gestión de rutas para el Sandbox
    # En el sandbox, los archivos generados deben ir a /mnt/out para persistir
    if os.path.exists("/mnt/out"):
        output_full_path = os.path.join("/mnt/out", args.output)
        # Si la entrada es relativa, asumir que está en /mnt/out (donde se generó el gcode previo)
        input_full_path = args.input if os.path.isabs(args.input) else os.path.join("/mnt/out", args.input)
    else:
        # Modo local (pruebas fuera de docker)
        output_full_path = os.path.join(".tmp", args.output)
        input_full_path = args.input
        os.makedirs(".tmp", exist_ok=True)

    print(f"🎨 Generando vista previa de {input_full_path}...")
    visualize(input_full_path, output_full_path)

if __name__ == "__main__":
    main()