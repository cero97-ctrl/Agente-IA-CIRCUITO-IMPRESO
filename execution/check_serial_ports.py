#!/usr/bin/env python3
import sys
import serial.tools.list_ports

def main():
    print("🔍 Buscando dispositivos seriales (ESP32/Arduino)...")
    
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("❌ No se detectaron puertos seriales.")
        print("   Posibles causas:")
        print("   1. Cable USB de 'solo carga' (prueba con otro).")
        print("   2. Falta de drivers (CH340 o CP210x).")
        print("   3. Problema de permisos (Linux: sudo usermod -a -G dialout $USER).")
        sys.exit(1)

    print(f"✅ Se encontraron {len(ports)} dispositivos:")
    for port in ports:
        vid = f"{port.vid:04X}" if port.vid is not None else "Desconocido"
        pid = f"{port.pid:04X}" if port.pid is not None else "Desconocido"
        print(f"   - Puerto: {port.device}")
        print(f"     Desc:   {port.description}")
        print(f"     HWID:   {port.hwid}")
        print(f"     ID:     VID:{vid} PID:{pid}")
        print("-" * 30)

if __name__ == "__main__":
    main()