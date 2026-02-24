#!/usr/bin/env python3
import argparse
import os
import sys
from PIL import Image, ImageOps

def main():
    parser = argparse.ArgumentParser(description="Convertir imagen a archivo Gerber (RS-274X).")
    parser.add_argument("--image", required=True, help="Ruta de la imagen de entrada.")
    parser.add_argument("--size", type=float, default=50.0, help="Ancho deseado en mm.")
    parser.add_argument("--output", default="output.gbr", help="Nombre del archivo de salida.")
    args = parser.parse_args()

    # Gestión de rutas para el Sandbox
    if os.path.exists("/mnt/out"):
        output_path = os.path.join("/mnt/out", args.output)
        if not os.path.isabs(args.image):
             args.image = os.path.join("/mnt/out", args.image)
    else:
        output_path = os.path.join(".tmp", args.output)
        os.makedirs(".tmp", exist_ok=True)

    if not os.path.exists(args.image):
        print(f"❌ Error: Imagen no encontrada en {args.image}")
        sys.exit(1)

    print(f"🏭 Procesando imagen para formato Gerber...")

    try:
        # 1. Procesamiento de imagen (Igual que para G-Code)
        img = Image.open(args.image).convert("L")
        img = ImageOps.invert(img) # Invertir: Negro original = Cobre (Blanco)
        img = img.point(lambda p: 255 if p > 128 else 0, '1')
        
        aspect = img.height / img.width
        width_mm = args.size
        height_mm = width_mm * aspect
        
        # Resolución alta para Gerber (0.1mm)
        resolution = 0.1 
        w_px = int(width_mm / resolution)
        h_px = int(height_mm / resolution)
        
        img = img.resize((w_px, h_px))
        pixels = img.load()
        
        # 2. Generación de Gerber RS-274X
        # Función auxiliar para formato 4.4 (ej: 10.5mm -> 105000)
        def to_gerber(mm):
            return int(mm * 10000)

        lines = []
        lines.append("%FSLAX44Y44*%") # Format Statement: Leading zeros, Absolute, 4.4
        lines.append("%MOMM*%")       # Mode: Millimeters
        lines.append("%LPD*%")        # Layer Polarity: Dark (Poner cobre)
        
        # Definir Apertura (La "broca" virtual de luz)
        # C = Circle, Diámetro = resolución
        lines.append(f"%ADD10C,{resolution:.4f}*%") 
        lines.append("D10*") # Seleccionar Apertura 10
        
        # Barrido Raster
        for y in range(h_px):
            y_mm = (h_px - 1 - y) * resolution
            y_g = to_gerber(y_mm)
            
            start_x = None
            for x in range(w_px):
                val = pixels[x, y]
                if val > 0: # Pixel activo (Cobre)
                    if start_x is None: start_x = x
                else: # Pixel vacío
                    if start_x is not None:
                        # Dibujar segmento acumulado
                        lines.append(f"X{to_gerber(start_x * resolution)}Y{y_g}D02*") # Mover al inicio
                        lines.append(f"X{to_gerber((x - 1) * resolution)}Y{y_g}D01*") # Dibujar hasta el fin
                        start_x = None
            
            # Cerrar segmento si la línea termina en cobre
            if start_x is not None:
                lines.append(f"X{to_gerber(start_x * resolution)}Y{y_g}D02*")
                lines.append(f"X{to_gerber((w_px - 1) * resolution)}Y{y_g}D01*")

        lines.append("M02*") # Fin del archivo
        
        with open(output_path, "w") as f:
            f.write("\n".join(lines))
            
        print(output_path)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()