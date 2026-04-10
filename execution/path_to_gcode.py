#!/usr/bin/env python3
import argparse
import json
import sys
import os

def generate_gcode(path, resolution, output_file, z_safety=2.0, z_cut=-0.1, feed_rate=300):
    """
    Convierte una lista de nodos (x, y) en un archivo G-Code (.nc).
    
    Args:
        path (list): Lista de tuplas/listas [[x1, y1], [x2, y2], ...]
        resolution (float): Tamaño de la celda en mm (ej. 0.25).
        output_file (str): Ruta del archivo de salida.
        z_safety (float): Altura de seguridad (mm).
        z_cut (float): Profundidad de corte (mm).
        feed_rate (float): Velocidad de avance (mm/min).
    """
    try:
        # Asegurar que el directorio de salida exista
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        with open(output_file, 'w') as f:
            # Cabecera estándar para controladores GRBL/G-Code
            f.write("; G-Code generado por Agente IA PCB\n")
            f.write("G21 ; Unidades en milímetros\n")
            f.write("G90 ; Posicionamiento absoluto\n")
            f.write(f"G0 Z{z_safety:.3f} ; Subir a altura segura\n\n")

            if not path:
                print("Error: La ruta proporcionada está vacía.", file=sys.stderr)
                return False

            # Moverse al inicio (primer punto del camino)
            start_x = path[0][0] * resolution
            start_y = path[0][1] * resolution
            f.write(f"G0 X{start_x:.3f} Y{start_y:.3f} ; Ir al inicio de la pista\n")
            
            # Bajar fresa de forma controlada para iniciar el grabado
            f.write(f"G1 Z{z_cut:.3f} F100 ; Penetrar cobre\n")

            # Trazar puntos de la ruta generada por el algoritmo de optimización
            for node in path[1:]:
                x = node[0] * resolution
                y = node[1] * resolution
                f.write(f"G1 X{x:.3f} Y{y:.3f} F{feed_rate:.0f}\n")

            # Finalizar operación y limpiar área
            f.write(f"\nG0 Z{z_safety:.3f} ; Levantar fresa\n")
            f.write("G0 X0 Y0 ; Regresar a origen (Home)\n")
            f.write("M2 ; Fin del programa\n")
            
        return True
    except Exception as e:
        print(f"Error escribiendo G-Code: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Generador de G-Code a partir de una ruta de nodos.")
    parser.add_argument("--path", required=True, help="Lista de puntos en JSON: '[[0,0],[1,1],...]'")
    parser.add_argument("--res", type=float, default=0.25, help="Resolución usada en el grid (mm/celda).")
    parser.add_argument("--output", required=True, help="Ruta del archivo .nc de salida.")
    parser.add_argument("--z-safe", type=float, default=2.0, help="Z de seguridad para movimientos aéreos.")
    parser.add_argument("--z-cut", type=float, default=-0.1, help="Z de profundidad para fresado de cobre.")
    parser.add_argument("--feed", type=float, default=300, help="Velocidad de avance en mm/min.")
    
    args = parser.parse_args()

    try:
        path_list = json.loads(args.path)
        if generate_gcode(path_list, args.res, args.output, args.z_safe, args.z_cut, args.feed):
            print(json.dumps({"status": "success", "file": args.output, "points_processed": len(path_list)}))
        else:
            sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"Fallo en la generación: {str(e)}"}))
        sys.exit(1)

if __name__ == "__main__":
    main()