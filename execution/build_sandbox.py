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
    print("   Esto instalará: pandas, numpy, matplotlib, requests, beautifulsoup4, pypdf.")
    print("   ⏳ Paciencia, esto puede tardar unos minutos la primera vez.")

    # Definir el contenido del Dockerfile
    dockerfile_content = """
 FROM ubuntu:22.04
 
 # Evitar archivos .pyc y buffering
 ENV DEBIAN_FRONTEND=noninteractive
 ENV PYTHONDONTWRITEBYTECODE=1
 ENV PYTHONUNBUFFERED=1
 
 # 1. Variables de entorno críticas para FreeCAD (solución del PDF)
 # Para que Python encuentre los módulos de FreeCAD y sepa qué display virtual usar.
 ENV PYTHONPATH="/usr/lib/freecad/lib:/usr/lib/freecad-python3/lib:${PYTHONPATH}"
 ENV DISPLAY=:99
 
 # 2. Instalación completa en una sola capa para optimizar
 RUN apt-get update && apt-get install -y --no-install-recommends \
     software-properties-common \
     gnupg \
     wget \
     xvfb \
     procps \
     libgl1-mesa-dri \
     libgl1-mesa-glx \
     && add-apt-repository -y ppa:freecad-maintainers/freecad-stable \
     && add-apt-repository -y ppa:kicad/kicad-8.0-releases \
     && apt-get update && apt-get install -y --no-install-recommends \
     python3 \
     python3-pip \
     kicad \
     freecad \
     freecad-python3 \
     && pip3 install --no-cache-dir pandas numpy matplotlib requests beautifulsoup4 pypdf opencv-python-headless skidl pathfinding \
     && apt-get clean \
     && rm -rf /var/lib/apt/lists/*
 
 # Asegurar que 'python' apunte a python3 para compatibilidad
 RUN ln -s /usr/bin/python3 /usr/bin/python
 
 WORKDIR /app
 """
    
    # Crear un archivo temporal para el contexto de build
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dockerfile_path = os.path.join(project_root, "Dockerfile.sandbox")
    
    with open(dockerfile_path, "w") as f:
        f.write(dockerfile_content)

    try:
        # Construir la imagen
        image, logs = client.images.build(path=project_root, dockerfile="Dockerfile.sandbox", tag="agent-sandbox:latest", rm=True, nocache=True)

        print("\n✅ Imagen 'agent-sandbox:latest' construida exitosamente.")
        print("   ✅ Soporte para KiCad (pcbnew), FreeCAD y Electrónica incluido.")
        print("   Ahora tus scripts de Python volarán. 🚀")
    except docker.errors.BuildError as e:
        print(f"\n❌ Error en el build: {e}")
        for line in e.build_log:
            if 'stream' in line: print(line['stream'].strip())
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")

if __name__ == "__main__":
    main()