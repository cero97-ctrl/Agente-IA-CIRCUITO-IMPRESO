#!/usr/bin/env python3
import cv2
import numpy as np
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="Generar imagen de prueba con patrones circulares para taladrado.")
    parser.add_argument("--output", default="test_drill.jpg", help="Nombre del archivo de salida.")
    args = parser.parse_args()

    # Configuración de la imagen (Fondo blanco)
    width, height = 800, 600
    img = np.ones((height, width), dtype=np.uint8) * 255

    # Dibujar círculos negros (simulando pads de PCB)
    # Formato: (x, y, radio)
    pads = [
        (100, 100, 15), (200, 100, 15), (300, 100, 15), # Fila superior
        (100, 200, 10), (200, 200, 10), (300, 200, 10), # Fila media (más pequeños)
        (150, 300, 20), (250, 300, 20),                 # Fila inferior (más grandes)
        (400, 150, 12), (400, 250, 12)                  # Columna derecha
    ]

    print(f"🎨 Generando patrón de prueba con {len(pads)} taladros...")

    for (x, y, r) in pads:
        # Dibujar círculo relleno negro
        cv2.circle(img, (x, y), r, (0, 0, 0), -1)

    # Gestión de rutas para el Sandbox
    if os.path.exists("/mnt/out"):
        output_path = os.path.join("/mnt/out", args.output)
    else:
        output_path = os.path.join(".tmp", args.output)
        os.makedirs(".tmp", exist_ok=True)

    cv2.imwrite(output_path, img)
    
    # Imprimir ruta para que el bot la envíe
    print(output_path)

if __name__ == "__main__":
    main()