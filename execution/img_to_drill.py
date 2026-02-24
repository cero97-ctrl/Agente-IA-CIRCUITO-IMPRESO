#!/usr/bin/env python3
import argparse
import cv2
import numpy as np
import os
import sys

def main():
    parser = argparse.ArgumentParser(description="Detectar agujeros y generar archivo Excellon (.drl).")
    parser.add_argument("--image", required=True, help="Imagen de entrada.")
    parser.add_argument("--size", type=float, default=50.0, help="Ancho de la placa en mm.")
    parser.add_argument("--output", default="output.drl", help="Archivo de salida.")
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
        print(f"❌ Error: Imagen {args.image} no encontrada.")
        sys.exit(1)

    print("🔩 Procesando imagen para detectar taladros...")

    # Leer imagen en escala de grises
    img = cv2.imread(args.image, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print("❌ Error leyendo imagen con OpenCV.")
        sys.exit(1)

    # Suavizar para reducir ruido y mejorar detección de círculos
    img = cv2.medianBlur(img, 5)
    
    height, width = img.shape
    mm_per_pixel = args.size / width
    
    # Configuración de detección (HoughCircles)
    # minDist: Distancia mínima entre centros (ej. 1mm)
    min_dist_px = int(1.0 / mm_per_pixel) 
    
    circles = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, 1, min_dist_px,
                               param1=50, param2=20,
                               minRadius=int(0.3/mm_per_pixel), maxRadius=int(3.0/mm_per_pixel))

    holes = []
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            # i[0]=x, i[1]=y, i[2]=radio
            x_mm = i[0] * mm_per_pixel
            # Excellon usa coordenadas cartesianas (Y crece hacia arriba), imagen es Y hacia abajo
            # Asumimos origen en esquina inferior izquierda de la imagen
            y_mm = (height - i[1]) * mm_per_pixel
            
            holes.append((x_mm, y_mm))
            
    if not holes:
        print("⚠️ No se detectaron círculos claros. Asegúrate de que la imagen tenga buen contraste (puntos negros/blancos).")
    
    # Generar archivo Excellon
    with open(output_path, "w") as f:
        f.write("M48\n")     # Inicio de cabecera
        f.write("METRIC\n")  # Unidades métricas
        f.write("T1C0.800\n") # Definir Herramienta 1 (Broca 0.8mm estándar)
        f.write("%\n")       # Fin de cabecera
        f.write("T1\n")      # Seleccionar Herramienta 1
        
        for x, y in holes:
            f.write(f"X{x:.3f}Y{y:.3f}\n")
            
        f.write("M30\n")     # Fin de archivo
        
    print(output_path)

if __name__ == "__main__":
    main()