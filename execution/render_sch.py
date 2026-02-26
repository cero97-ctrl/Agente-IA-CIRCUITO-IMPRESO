#!/usr/bin/env python3
import sys
import os
import re
import matplotlib
matplotlib.use('Agg') # Usar backend sin interfaz gráfica
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def render_schematic(sch_path, output_image):
    if not os.path.exists(sch_path):
        print(f"Error: File not found {sch_path}")
        sys.exit(1)

    with open(sch_path, 'r') as f:
        content = f.read()

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_aspect('equal')
    ax.set_facecolor('#f5f5f5') # Fondo claro tipo papel
    ax.invert_yaxis() # En KiCad Y crece hacia abajo

    # 1. Dibujar Cables (Wires)
    # Formato: (wire (pts (xy 120.0 100.0) (xy 125.08 100.0))
    wire_pattern = r'\(wire \(pts \(xy ([\d\.]+) ([\d\.]+)\) \(xy ([\d\.]+) ([\d\.]+)\)\)'
    for match in re.finditer(wire_pattern, content):
        x1, y1, x2, y2 = map(float, match.groups())
        ax.plot([x1, x2], [y1, y2], color='#006600', linewidth=1.5) # Cables verdes

    # 2. Dibujar Símbolos (Componentes)
    # Dividimos el contenido por bloques de símbolos para procesar sus propiedades
    parts = content.split('(symbol (lib_id "')
    
    for part in parts[1:]:
        try:
            # Extraer ID de librería y posición
            lib_id_end = part.find('"')
            lib_id = part[:lib_id_end]
            
            at_match = re.search(r'\(at ([\d\.]+) ([\d\.]+) 0\)', part)
            if at_match:
                x, y = float(at_match.group(1)), float(at_match.group(2))
                
                # Extraer Referencia (R1, U1, etc)
                ref_match = re.search(r'\(property "Reference" "([^"]+)"', part)
                ref = ref_match.group(1) if ref_match else "?"
                
                # Extraer Valor (10k, NE555, etc)
                val_match = re.search(r'\(property "Value" "([^"]+)"', part)
                val = val_match.group(1) if val_match else "?"
                
                # Dibujar caja del componente (tamaño estimado según tipo)
                w, h = 10, 10 
                if "R" in lib_id: w, h = 4, 10
                elif "C" in lib_id: w, h = 4, 8
                elif "NE555" in lib_id: w, h = 12, 14
                elif "LED" in lib_id or "D" in lib_id: w, h = 4, 8
                
                # Rectángulo amarillo claro con borde azul (estilo KiCad clásico)
                rect = Rectangle((x - w/2, y - h/2), w, h, linewidth=1, edgecolor='#800000', facecolor='#FFFFCC', alpha=0.8)
                ax.add_patch(rect)
                
                # Etiquetas de texto
                ax.text(x, y - h/2 - 1, ref, ha='center', va='bottom', fontsize=10, color='#800000', weight='bold')
                ax.text(x, y + h/2 + 1, val, ha='center', va='top', fontsize=8, color='black')
                
        except Exception:
            pass

    # 3. Dibujar Etiquetas de Red (Labels)
    # Formato: (label "VCC" (at 125.08 100.0 180)
    label_pattern = r'\(label "([^"]+)" \(at ([\d\.]+) ([\d\.]+) ([\d\.]+)\)'
    for match in re.finditer(label_pattern, content):
        text, x, y, rot = match.groups()
        x, y = float(x), float(y)
        ax.text(x, y, text, ha='left', va='center', fontsize=9, color='#006600', weight='bold', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

    ax.autoscale()
    # Márgenes
    ax.margins(0.1)
    plt.axis('off')
    plt.title("Vista Previa Esquemático (KiCad)", color='black')
    plt.savefig(output_image, dpi=100, bbox_inches='tight')
    print(f"Render saved to {output_image}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: render_sch.py <sch_file> <output_image>")
        sys.exit(1)
    render_schematic(sys.argv[1], sys.argv[2])