#!/usr/bin/env python3
import docker
import sys
import os

def main():
    try:
        client = docker.from_env()
    except Exception as e:
        print(f"❌ Error conectando a Docker: {e}")
        sys.exit(1)

    print("🐳 Construyendo imagen de Sandbox personalizada (agent-sandbox)...")
    print("   Esto instalará: FreeCAD, KiCad, FCGear, pcb2gcode y librerías de Python.")
    print("   ⏳ Paciencia, esto puede tardar unos minutos la primera vez.")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dockerfile_path = os.path.join(project_root, "Dockerfile.sandbox")
    
    if not os.path.exists(dockerfile_path):
        print(f"❌ No se encontró el archivo Dockerfile.sandbox en {project_root}")
        sys.exit(1)

    try:
        # Construir la imagen con streaming de logs para mejor visibilidad
        print("🚀 Iniciando construcción de la imagen...")
        for line in client.api.build(path=project_root, dockerfile="Dockerfile.sandbox", tag="agent-sandbox:latest", decode=True, rm=True):
            if 'stream' in line:
                print(line['stream'], end='')
        
        print("\n✅ Imagen 'agent-sandbox:latest' construida exitosamente.")
        print("   ✅ Soporte para KiCad (pcbnew), FreeCAD, FCGear y Electrónica incluido.")
        print("   Ahora tus scripts de Python volarán. 🚀")
    except docker.errors.BuildError as e:
        print(f"\n❌ Error en el build: {e}")
        for line in e.build_log:
            if 'stream' in line: print(line['stream'].strip())
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")

if __name__ == "__main__":
    main()