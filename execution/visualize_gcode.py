#!/usr/bin/env python3
import argparse
import matplotlib.pyplot as plt
import re
import os
import sys
import math

def parse_gcode_segments(filepath):
    segments = []
    current_x = 0.0
    current_y = 0.0
    current_mode = 'G0' # Asumimos G0 (rápido) por defecto al inicio
    current_feed = 300.0 # Velocidad por defecto (mm/min) si no se especifica
    
    if not os.path.exists(filepath):
        print(f"❌ Archivo no encontrado: {filepath}", file=sys.stderr)
        return []

    with open(filepath, 'r') as f:
        for line in f:
            line = line.upper().strip()
            if not line or line.startswith(';') or line.startswith('('):
                continue
            
            # Detectar cambio de modo (modal)
            if 'G0' in line: current_mode = 'G0'
            elif 'G1' in line: current_mode = 'G1'
            elif 'G2' in line: current_mode = 'G1' # Tratamos arcos como corte para simplificar visualización
            elif 'G3' in line: current_mode = 'G1'
            
            # Detectar velocidad (Feed Rate)
            match_f = re.search(r'F([\d\.-]+)', line)
            if match_f:
                current_feed = float(match_f.group(1))
            
            # Detectar coordenadas
            new_x = current_x
            new_y = current_y
            has_move = False
            
            match_x = re.search(r'X([\d\.-]+)', line)
            if match_x:
                new_x = float(match_x.group(1))
                has_move = True
            
            match_y = re.search(r'Y([\d\.-]+)', line)
            if match_y:
                new_y = float(match_y.group(1))
                has_move = True
                
            if has_move:
                # Calcular distancia del segmento
                dist = math.sqrt((new_x - current_x)**2 + (new_y - current_y)**2)
                segments.append({
                    'x': [current_x, new_x],
                    'y': [current_y, new_y],
                    'type': current_mode,
                    'dist': dist,
                    'feed': current_feed
                })
                current_x = new_x
                current_y = new_y
                
    return segments

def visualize(gcode_path, output_path):
    segments = parse_gcode_segments(gcode_path)
    
    if not segments:
        print("⚠️ No se encontraron coordenadas válidas para graficar.")
        return

    plt.figure(figsize=(10, 8))
    
    # Separar datos para plotear eficientemente (usando None para romper líneas)
    g0_x, g0_y = [], []
    g1_x, g1_y = [], []
    
    total_time_min = 0.0
    rapid_feed = 1500.0 # Estimación de velocidad máxima de la máquina para G0 (mm/min)
    
    for seg in segments:
        # Calcular tiempo del segmento: Tiempo = Distancia / Velocidad
        speed = rapid_feed if seg['type'] == 'G0' else seg['feed']
        if speed > 0:
            total_time_min += seg['dist'] / speed
            
        if seg['type'] == 'G0':
            g0_x.extend(seg['x'] + [None])
            g0_y.extend(seg['y'] + [None])
        else:
            g1_x.extend(seg['x'] + [None])
            g1_y.extend(seg['y'] + [None])

    # Plotear Viajes (G0) - Rojo punteado, fino
    if g0_x:
        plt.plot(g0_x, g0_y, color='red', linestyle='--', linewidth=0.5, alpha=0.5, label='Viaje (G0)')
    
    # Plotear Cortes (G1) - Azul sólido
    if g1_x:
        plt.plot(g1_x, g1_y, color='blue', linestyle='-', linewidth=1.5, alpha=0.8, label='Corte (G1)')
    
    # Estética del gráfico
    # Formatear tiempo
    minutes = int(total_time_min)
    seconds = int((total_time_min * 60) % 60)
    plt.title(f"Vista: {os.path.basename(gcode_path)}\nTiempo Est: {minutes}m {seconds}s")
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