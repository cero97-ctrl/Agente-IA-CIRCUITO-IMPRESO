#!/usr/bin/env python3
import argparse
import os
import sys
from PIL import Image, ImageFilter, ImageOps

def main():
    parser = argparse.ArgumentParser(description="Convertir imagen a G-Code (Bordes).")
    parser.add_argument("--image", required=True, help="Ruta de la imagen de entrada.")
    parser.add_argument("--size", type=float, default=50.0, help="Ancho deseado en mm.")
    parser.add_argument("--output", default="output.nc", help="Nombre del archivo de salida.")
    args = parser.parse_args()

    # Gestión de rutas para el Sandbox
    if os.path.exists("/mnt/out"):
        # Estamos en Docker
        output_path = os.path.join("/mnt/out", args.output)
        # Si la entrada es relativa, asumimos que está en /mnt/out (donde se descargan las fotos)
        if not os.path.isabs(args.image):
             args.image = os.path.join("/mnt/out", args.image)
    else:
        # Estamos en Local
        output_path = os.path.join(".tmp", args.output)
        os.makedirs(".tmp", exist_ok=True)

    if not os.path.exists(args.image):
        print(f"❌ Error: Imagen no encontrada en {args.image}")
        sys.exit(1)

    print(f"🎨 Procesando imagen para CNC...")

    try:
        img = Image.open(args.image).convert("L") # Escala de grises
        
        # 1. Detectar bordes
        edges = img.filter(ImageFilter.FIND_EDGES)
        
        # 2. Redimensionar
        aspect = img.height / img.width
        width_mm = args.size
        height_mm = width_mm * aspect
        
        resolution = 0.2 # mm/pixel (Resolución de escaneo)
        w_px = int(width_mm / resolution)
        h_px = int(height_mm / resolution)
        
        edges = edges.resize((w_px, h_px))
        pixels = edges.load()
        
        # 3. Generar G-Code
        gcode = [
            "G21 ; Unidades mm",
            "G90 ; Absoluto",
            "G0 Z5.0 ; Seguridad",
            "M3 S1000 ; Spindle ON"
        ]
        
        threshold = 40 # Sensibilidad de detección de borde (0-255)
        
        for y in range(h_px):
            y_mm = (h_px - y) * resolution # Invertir Y (origen abajo-izq)
            for x in range(w_px):
                x_mm = x * resolution
                val = pixels[x, y]
                
                if val > threshold: # Si es un borde visible
                    gcode.append(f"G1 X{x_mm:.3f} Y{y_mm:.3f} Z-0.2 F300") # Corte
                    gcode.append(f"G0 Z1.0") # Levantar rápido
        
        gcode.append("G0 Z10.0")
        gcode.append("M5")
        gcode.append("M2")
        
        with open(output_path, "w") as f:
            f.write("\n".join(gcode))
            
        print(output_path) # Importante para que el bot sepa qué archivo enviar
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()