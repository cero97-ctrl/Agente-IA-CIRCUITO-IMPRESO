#!/usr/bin/env python3
import serial
import serial.tools.list_ports
import sys
import time

def find_esp_port():
    """Auto-detecta el puerto serial del ESP32-S3."""
    ports = serial.tools.list_ports.comports()
    for p in ports:
        desc = (p.description or "").lower()
        hwid = (p.hwid or "").lower()
        if any(x in desc or x in hwid for x in ["cp210", "ch34", "espressif", "usb-to-uart", "1a86", "10c4", "ttyacm"]):
            return p.device
    return None

def main():
    port = find_esp_port()
    
    if not port:
        print("❌ No se detectó ningún dispositivo ESP32-S3.")
        sys.exit(1)

    baud = 115200 # Velocidad estándar del bootloader del ESP32

    try:
        ser = serial.Serial(port, baud, timeout=0.1)
        print(f"✅ Conectado a {port} a {baud} baudios.")
        print("🚀 Escuchando datos...")
        print("⚠️  SI NO VES NADA:")
        print("   1. ¿El LED 'ON' está encendido? Si no, revisa el cable ROJO y el JUMPER del CH340.")
        print("   2. Prueba intercambiando los cables BLANCO y VERDE.")
        print(" Presiona Ctrl+C para salir.\n" + "-"*50)
        
        while True:
            if ser.in_waiting:
                # Leemos crudo para evitar errores de decode en el arranque
                raw_data = ser.read(ser.in_waiting)
                try:
                    text = raw_data.decode('utf-8', errors='ignore')
                    if "waiting for download" in text.lower():
                        print("\n\n🌟 [SISTEMA] ¡Chip detectado en modo descarga! El hardware tiene energía y comunica correctamente.\n")
                    
                    sys.stdout.write(text)
                    sys.stdout.flush()
                except Exception:
                    # Si es basura binaria (común en el cambio de baudrate del boot)
                    print(f"[{raw_data.hex()}]", end='', flush=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoreo finalizado.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()