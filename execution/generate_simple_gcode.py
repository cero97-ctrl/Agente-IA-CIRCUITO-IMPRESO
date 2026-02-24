#!/usr/bin/env python3
import argparse
import os

def generar_gcode(puntos, archivo_salida, velocidad=300, z_seguridad=2.0, z_corte=-0.1):
    """
    Genera un archivo G-Code simple a partir de una lista de puntos (x, y).
    """
    print(f"🔨 Generando G-Code en: {archivo_salida}")
    print(f"   - Puntos: {len(puntos)}")
    print(f"   - Velocidad: {velocidad} mm/min")
    
    try:
        with open(archivo_salida, "w") as f:
            # 1. Cabecera
            f.write("G21 ; Unidades en mm\n")
            f.write("G90 ; Posicionamiento absoluto\n")
            f.write(f"G0 Z{z_seguridad} ; Subir fresa (Seguridad)\n\n")

            if not puntos:
                print("⚠️  Advertencia: Lista de puntos vacía.")
                return False

            # 2. Ir al inicio
            inicio = puntos[0]
            f.write(f"G0 X{inicio[0]:.3f} Y{inicio[1]:.3f} ; Ir al inicio\n")
            f.write("M3 S1000 ; Encender Spindle (si aplica)\n")
            f.write(f"G1 Z{z_corte} F100 ; Bajar fresa\n")

            # 3. Trayectoria
            for x, y in puntos[1:]:
                f.write(f"G1 X{x:.3f} Y{y:.3f} F{velocidad}\n")

            # 4. Finalizar
            f.write(f"\nG0 Z{z_seguridad} ; Levantar fresa\n")
            f.write("M5 ; Apagar Spindle\n")
            f.write("M2 ; Fin del programa\n")
        
        return True
    except Exception as e:
        print(f"❌ Error escribiendo archivo: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Generador simple de G-Code para pruebas.")
    parser.add_argument("--shape", choices=["cuadrado", "triangulo"], default="cuadrado", help="Forma a generar")
    parser.add_argument("--size", type=float, default=10.0, help="Tamaño de la figura en mm")
    parser.add_argument("--output", default="test_pcb.nc", help="Archivo de salida")
    
    args = parser.parse_args()
    
    # Gestión de rutas para el Sandbox
    if os.path.exists("/mnt/out"):
        # Si la salida es relativa, la ponemos en /mnt/out
        output_full_path = args.output if os.path.isabs(args.output) else os.path.join("/mnt/out", args.output)
    else:
        # Modo local
        output_full_path = os.path.join(".tmp", args.output)
        os.makedirs(".tmp", exist_ok=True)
    
    # Definir geometrías simples para prueba
    if args.shape == "cuadrado":
        # Cuadrado de size x size empezando en 0,0
        path = [(0,0), (args.size, 0), (args.size, args.size), (0, args.size), (0,0)]
    elif args.shape == "triangulo":
        path = [(0,0), (args.size, 0), (args.size/2, args.size), (0,0)]
    
    success = generar_gcode(path, output_full_path)
    
    if success:
        # IMPORTANTE: Imprimir la ruta final para que listen_telegram.py la detecte
        print(output_full_path)

if __name__ == "__main__":
    main()