#!/usr/bin/env python3
import serial
import sys

def main():
    # Usamos el puerto detectado: /dev/ttyACM0
    port = "/dev/ttyACM0"
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
                    
                    print(text, end='', flush=True)
                except Exception:
                    # Si es basura binaria (común en el cambio de baudrate del boot)
                    print(f"[{raw_data.hex()}]", end='', flush=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoreo finalizado.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()