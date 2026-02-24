#!/usr/bin/env python3
import serial
import time
import argparse
import sys
import os

def stream_gcode(port, baudrate, gcode_file):
    """
    Envía un archivo G-Code a una máquina CNC con GRBL, línea por línea.
    """
    if not os.path.exists(gcode_file):
        print(f"❌ Error: El archivo G-Code '{gcode_file}' no fue encontrado.")
        # No usamos sys.exit para que el bot pueda reportar el error.
        return False

    try:
        # Abrir conexión serial
        s = serial.Serial(port, baudrate)
        print(f"✅ Conectado a la CNC en {port} a {baudrate} baudios.")
    except serial.SerialException as e:
        print(f"❌ Error de conexión: No se pudo abrir el puerto '{port}'.")
        print(f"   Asegúrate de que la CNC esté conectada y el puerto sea correcto.")
        print(f"   Detalle: {e}")
        return False

    # Despertar a GRBL
    s.write(b"\r\n\r\n")
    time.sleep(2)   # Esperar a que GRBL se inicialice
    s.flushInput()  # Limpiar cualquier dato basura en el buffer de entrada

    print("🚀 Iniciando transmisión de G-Code...")

    # Enviar el archivo
    with open(gcode_file, 'r') as f:
        for line in f:
            l = line.strip() # Limpiar espacios y saltos de línea
            if not l or l.startswith(';'):
                continue # Ignorar líneas vacías o comentarios

            print(f"   -> {l}")
            s.write((l + '\n').encode('utf-8')) # Enviar línea
            
            # Esperar respuesta 'ok' de GRBL
            response = s.readline().decode('utf-8').strip()
            print(f"   <- {response}")
            if 'ok' not in response:
                print(f"🔥 Error de la CNC: {response}. Abortando.")
                s.close()
                return False

    s.close()
    print("\n🎉 Trabajo finalizado. Conexión cerrada.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stream G-Code to a GRBL-based CNC.")
    parser.add_argument("--port", required=True, help="Puerto serial (ej: /dev/ttyUSB0 o COM3).")
    parser.add_argument("--file", required=True, help="Ruta al archivo .nc a enviar.")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (usualmente 115200 para GRBL).")
    args = parser.parse_args()

    # Asumimos que si se ejecuta desde CLI, el archivo está en .tmp
    file_path = args.file if os.path.isabs(args.file) else os.path.join(".tmp", args.file)

    stream_gcode(args.port, args.baud, file_path)