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
        # --- LÓGICA MEJORADA ---
        # 1. Binarizar la imagen para un grabado claro
        img = Image.open(args.image).convert("L") # Escala de grises
        # Invertimos la imagen: lo que era oscuro (el logo) se vuelve blanco y será lo que se grabe.
        img = ImageOps.invert(img)
        # Binarizamos: todo lo que no sea negro puro se convierte en blanco (255).
        img = img.point(lambda p: 255 if p > 128 else 0, '1')
        
        # 2. Redimensionar
        aspect = img.height / img.width
        width_mm = args.size
        height_mm = width_mm * aspect
        
        resolution = 0.25 # mm/pixel (Resolución de escaneo, un poco más gruesa para velocidad)
        w_px = int(width_mm / resolution)
        h_px = int(height_mm / resolution)
        
        img = img.resize((w_px, h_px))
        pixels = img.load()
        
        # 3. Generar G-Code con lógica de barrido (Raster Scan)
        gcode = [
            "G21 ; Unidades mm",
            "G90 ; Absoluto",
            "G0 Z2.0 ; Altura de seguridad",
            "M3 S1000 ; Spindle ON"
        ]
        
        z_cut = -0.2
        z_safe = 1.0
        feed_rate = 300
        
        for y in range(h_px):
            y_mm = (h_px - 1 - y) * resolution # Origen abajo-izquierda
            
            # Barrido en serpentina para eficiencia
            x_range = range(w_px) if y % 2 == 0 else range(w_px - 1, -1, -1)
            
            is_cutting = False
            for x in x_range:
                x_mm = x * resolution
                
                # Si el pixel es blanco (255), debemos cortar
                if pixels[x, y] > 0 and not is_cutting:
                    # Empezar a cortar
                    gcode.append(f"G0 X{x_mm:.3f} Y{y_mm:.3f}")
                    gcode.append(f"G1 Z{z_cut} F100")
                    is_cutting = True
                elif pixels[x, y] == 0 and is_cutting:
                    # Parar de cortar
                    prev_x = x - 1 if y % 2 == 0 else x + 1
                    prev_x_mm = prev_x * resolution
                    gcode.append(f"G1 X{prev_x_mm:.3f} Y{y_mm:.3f} F{feed_rate}")
                    gcode.append(f"G0 Z{z_safe}")
                    is_cutting = False

            # Si la línea termina y seguíamos cortando, cerramos el segmento
            if is_cutting:
                last_x_mm = (w_px - 1 if y % 2 == 0 else 0) * resolution
                gcode.append(f"G1 X{last_x_mm:.3f} Y{y_mm:.3f} F{feed_rate}")
                gcode.append(f"G0 Z{z_safe}")
        
        gcode.append("G0 Z5.0")
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