#!/usr/bin/env python3
import argparse
import sys
import json
import time
import subprocess

try:
    import psutil
except ImportError:
    print(json.dumps(
        {"status": "error", "message": "Librería 'psutil' no encontrada. Instala con: pip install psutil"}), file=sys.stderr)
    sys.exit(1)

def get_zram_stats():
    """Intenta obtener estadísticas detalladas de ZRAM si está disponible."""
    try:
        # Ejecutamos zramctl en formato JSON para una integración limpia
        res = subprocess.run(['zramctl', '--output-all', '--json'], capture_output=True, text=True, timeout=2)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            return data.get("zramdevices", [])
    except:
        pass
    return []

def get_gpu_status():
    """Verifica si hay una GPU NVIDIA presente y funcional usando nvidia-smi."""
    try:
        res = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.used,memory.total,utilization.gpu', '--format=csv,noheader,nounits'], 
                             capture_output=True, text=True, timeout=2)
        if res.returncode == 0:
            parts = res.stdout.strip().split(',')
            return {"model": parts[0], "used_m": parts[1], "total_m": parts[2], "load": parts[3]}
    except:
        pass
    return None


def main():
    parser = argparse.ArgumentParser(description="Monitorear uso de CPU y Memoria.")
    parser.add_argument("--cpu-threshold", type=float, default=85.0, help="Umbral de alerta para CPU (%)")
    parser.add_argument("--mem-threshold", type=float, default=85.0, help="Umbral de alerta para Memoria (%)")
    args = parser.parse_args()

    # Medir CPU (requiere un pequeño intervalo para ser preciso)
    cpu_usage = psutil.cpu_percent(interval=1)

    # Medir Memoria
    mem = psutil.virtual_memory()
    mem_usage = mem.percent

    # Medir Disco (Raíz)
    disk = psutil.disk_usage('/')
    disk_usage = disk.percent

    # Medir ZRAM
    zram_devices = get_zram_stats()
    has_zram = len(zram_devices) > 0

    # Medir GPU (NVIDIA)
    gpu_info = get_gpu_status()

    alerts = []
    if cpu_usage > args.cpu_threshold:
        alerts.append(f"CPU Alto: {cpu_usage}% (Umbral: {args.cpu_threshold}%)")

    if mem_usage > args.mem_threshold:
        alerts.append(f"Memoria Alta: {mem_usage}% (Umbral: {args.mem_threshold}%)")
        
    if disk_usage > 90.0:
        alerts.append(f"Disco Casi Lleno: {disk_usage}%")

    result = {
        "status": "ok" if not alerts else "warning",
        "metrics": {
            "cpu_percent": cpu_usage,
            "memory_percent": mem_usage,
            "memory_used_gb": round(mem.used / (1024**3), 2),
            "memory_total_gb": round(mem.total / (1024**3), 2),
            "disk_percent": disk_usage,
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "zram_active": has_zram,
            "gpu_active": gpu_info is not None
        },
        "zram_details": zram_devices,
        "gpu_details": gpu_info,
        "alerts": alerts
    }

    print(json.dumps(result, indent=2))

    # Salir con error si hay alertas para que el orquestador lo note
    if alerts:
        sys.exit(1)


if __name__ == "__main__":
    main()
