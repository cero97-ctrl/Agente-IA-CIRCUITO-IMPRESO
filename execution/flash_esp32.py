#!/usr/bin/env python3
"""
Flash MicroPython firmware to ESP32-S3 via CH340 (Soldered wires).
Requiere entrada manual en modo bootloader (BOOT + RESET) ya que el 
adaptador CH340 no suele tener control de auto-reset por software.
"""
import subprocess
import sys
import os
import time
import glob
import serial
import serial.tools.list_ports


def find_esp_port():
    """Auto-detecta el puerto serial del ESP32-S3."""
    ports = serial.tools.list_ports.comports()
    for p in ports:
        desc = (p.description or "").lower()
        hwid = (p.hwid or "").lower()
        # Busca identificadores comunes de Espressif o adaptadores seriales
        if any(x in desc or x in hwid for x in ["cp210", "ch34", "espressif", "usb-to-uart", "1a86", "10c4"]):
            return p.device
    # Fallback: buscar ttyUSB*
    for p in ports:
        if "ttyUSB" in p.device or "ttyACM" in p.device:
            return p.device
    return None


def test_serial_connection(port, baud=115200, timeout=2):
    """Verifica que hay comunicación serial real con el ESP32."""
    try:
        ser = serial.Serial(port, baud, timeout=timeout)
        # Intentar sincronización básica: enviar bytes de sincronización
        # Si el ESP32 está en bootloader, responderá
        ser.dtr = False
        ser.rts = False
        time.sleep(0.1)
        ser.reset_input_buffer()
        
        # Enviar un byte y ver si hay eco o respuesta
        ser.write(b'\x07\x07\x12\x20' + b'\x55' * 32)
        time.sleep(0.5)
        response = ser.read(ser.in_waiting or 1)
        ser.close()
        
        if response:
            return True, f"Recibidos {len(response)} bytes de respuesta"
        else:
            return False, "No se recibió respuesta del ESP32"
    except serial.SerialException as e:
        return False, f"Error serial: {e}"


def run_command(command):
    """Ejecuta un comando y muestra la salida en tiempo real."""
    print(f"Ejecutando: {' '.join(command)}")
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        for line in process.stdout:
            print(line, end='')
        process.wait()
        return process.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False


def show_instructions():
    """Muestra instrucciones de seguridad por si el auto-reset falla."""
    print()
    print("=" * 65)
    print("  🔌 MODO MANUAL - ADAPTADOR CH340 (Cables Soldados)")
    print("=" * 65)
    print()
    print("  PREPARACIÓN:")
    print("  1. MANTÉN PRESIONADO el botón BOOT.")
    print("  2. Pulsa y SUELTA el botón RESET.")
    print("  3. SUELTA el botón BOOT.")
    print()
    print("  💡 NOTA: Si el flasheo falla, intenta realizar la secuencia")
    print("  JUSTO DESPUÉS de presionar ENTER, mientras aparecen los puntos (...)")
    print("  en la pantalla.")
    print("=" * 65)
    print()


def main():
    # --- Detección automática del puerto ---
    print("🚀 FLASHEO ESP32-S3 (ADAPTADOR CH340)")
    print("─" * 40)
    
    port = find_esp_port()
    if not port:
        print("❌ No se detectó ningún dispositivo ESP32-S3.")
        print("   Verifica que el cable USB-C esté bien conectado.")
        return
    print(f"✅ Dispositivo detectado en: {port}")
    
    # --- Verificar permisos ---
    if not os.access(port, os.R_OK | os.W_OK):
        print(f"❌ Sin permisos para acceder a {port}.")
        print(f"   Ejecuta: sudo chmod 666 {port}")
        print(f"   O añádete al grupo dialout: sudo usermod -aG dialout $USER")
        return
    
    # --- Buscar firmware ---
    tmp_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ".tmp"
    )
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    firmware_path = os.path.join(tmp_dir, "esp32s3-firmware.bin")
    if not os.path.exists(firmware_path):
        posibles = glob.glob(os.path.join(tmp_dir, "ESP32_GENERIC_S3*.bin"))
        if posibles:
            firmware_path = posibles[0]
        else:
            print(f"❌ No se encontró firmware .bin en {tmp_dir}")
            print("   Descárgalo de: https://micropython.org/download/ESP32_GENERIC_S3/")
            return

    print(f"📦 Firmware: {os.path.basename(firmware_path)}")
    print(f"   Tamaño:  {os.path.getsize(firmware_path) / 1024:.0f} KB")

    # --- Verificar esptool ---
    if subprocess.run(["which", "esptool"], capture_output=True).returncode != 0:
        print("❌ 'esptool' no encontrado. Instálalo con: pip install esptool")
        return

    show_instructions()
    # --- Mostrar instrucciones y esperar ---
    input("Presiona ENTER para iniciar el proceso...")
    print()

    # Pequeña pausa
    time.sleep(1)

    # --- Test de conexión eliminado ---
    # Se elimina la apertura manual del puerto antes de esptool para evitar
    # que el toggle de DTR/RTS reinicie el chip y lo saque del modo bootloader.
    # print("🔍 Verificando comunicación serial...")
    # ok, msg = test_serial_connection(port)
    # ...

    # --- Parámetros de esptool ---
    # 115200 es más estable para cables largos o soldados
    BAUD = "115200"

    # --- Paso 1: Verificar chip ---
    print("📡 Paso 1/3: Sincronizando con el chip (Handshake)...")
    check_cmd = [
        "esptool",
        "--chip", "esp32s3",
        "--port", port,
        "--baud", BAUD,
        "--before", "no-reset",
        "--after", "no-reset",
        "chip-id"
    ]
    
    if not run_command(check_cmd):
        print()
        print("❌ No se pudo conectar al ESP32-S3.")
        print()
        print("🔧 SOLUCIONES:")
        print("  1. Realiza la secuencia manual: MANTENER BOOT -> PULSAR RESET -> SOLTAR BOOT.")
        print("  2. Verifica que TX y RX estén cruzados (TX->RX, RX->TX).")
        print("  3. Asegúrate de estar usando el puerto etiquetado como 'UART' en la placa.")
        print()
        
        retry = input("¿Quieres reintentar? (s/n): ").strip().lower()
        if retry == 's':
            if not run_command(check_cmd):
                print("❌ Fallo definitivo. Revisa el cableado.")
                return
        else:
            return

    # --- Paso 2: Borrar flash ---
    print("\n🧹 Paso 2/3: Borrando flash...")
    print("   (Esto puede tomar 15-30 segundos)")

    erase_cmd = [
        "esptool",
        "--chip", "esp32s3",
        "--port", port,
        "--baud", BAUD,
        "--before", "no-reset",
        "--after", "no-reset",
        "erase_flash"
    ]
    if not run_command(erase_cmd):
        print("❌ Falló el borrado de flash.")
        print("   Intenta re-entrar en bootloader y ejecutar de nuevo.")
        return

    # --- Paso 3: Escribir firmware ---
    print("\n✍️  Paso 3/3: Escribiendo MicroPython...")
    print(f"   Firmware: {os.path.basename(firmware_path)}")
    print("   (Esto puede tomar 1-3 minutos a 115200 baud)")

    flash_cmd = [
        "esptool",
        "--chip", "esp32s3",
        "--port", port,
        "--baud", BAUD,
        "--before", "no-reset",
        "--after", "hard_reset",
        "write_flash",
        "-z",
        "0x0",
        firmware_path
    ]

    if run_command(flash_cmd):
        print()
        print("=" * 60)
        print("  ✅ ¡ÉXITO! Firmware MicroPython cargado correctamente.")
        print()
        print("  Próximos pasos:")
        print("  1. Pulsa RESET en el ESP32-S3.")
        print("  2. Abre un terminal serial:")
        print(f"     python3 -m serial.tools.miniterm {port} 115200")
        print("  3. Deberías ver el prompt >>> de MicroPython.")
        print("=" * 60)
    else:
        print("\n❌ Error durante la escritura del firmware.")
        print("   Verifica conexiones y vuelve a intentar.")


if __name__ == "__main__":
    main()