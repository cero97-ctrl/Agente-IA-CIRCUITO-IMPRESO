#!/usr/bin/env python3
import cv2
import numpy as np
import os
import sys

def test_opencv_processing():
    """
    Verifica que OpenCV puede generar, leer y procesar una imagen de circuito.
    Simula la detección de taladrado (pads) mediante la transformada de Hough.
    """
    print("🔍 Iniciando validación de capacidad de visión (OpenCV)...")
    
    # 1. Crear una imagen sintética que simule un fragmento de PCB (Fondo blanco)
    image = np.ones((500, 500, 3), dtype=np.uint8) * 255
    
    # Dibujar algunos "pads" (círculos negros rellenos)
    # Estos simulan los puntos donde la CNC debería taladrar
    centers = [(100, 100), (400, 100), (250, 250), (100, 400), (400, 400)]
    for center in centers:
        cv2.circle(image, center, 20, (0, 0, 0), -1)
        
    # Crear directorio temporal si no existe
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tmp_dir = os.path.join(root_dir, ".tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    
    input_path = os.path.join(tmp_dir, "test_vision_input.png")
    cv2.imwrite(input_path, image)
    print(f"✅ Imagen de prueba generada en {input_path}")
    
    # 2. Procesar la imagen para detectar los taladros
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 5)
    
    # Detectar círculos (Hough Circles)
    circles = cv2.HoughCircles(
        blurred, 
        cv2.HOUGH_GRADIENT, 1, 50,
        param1=50, param2=15, minRadius=10, maxRadius=30
    )
    
    if circles is not None:
        circles = np.uint16(np.around(circles))
        num_detected = len(circles[0])
        print(f"✅ Se detectaron {num_detected} pads de taladrado correctamente.")
        
        # Dibujar resultados (Verde para el contorno, Rojo para el centro)
        for i in circles[0, :]:
            cv2.circle(image, (i[0], i[1]), i[2], (0, 255, 0), 2)
            cv2.circle(image, (i[0], i[1]), 2, (0, 0, 255), 3)
            
        output_path = os.path.join(tmp_dir, "test_vision_result.png")
        cv2.imwrite(output_path, image)
        print(f"✅ Resultado de visión guardado en {output_path}")
        return True
    else:
        print("❌ Fallo: No se detectaron los pads en la imagen sintética.")
        return False

if __name__ == "__main__":
    success = test_opencv_processing()
    if success:
        print("\n✨ [OK] El motor de visión OpenCV está configurado y funcionando.")
        sys.exit(0)
    else:
        print("\n🚨 [ERROR] Problemas detectados en el procesamiento de imagen.")
        sys.exit(1)