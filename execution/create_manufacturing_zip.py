#!/usr/bin/env python3
import argparse
import zipfile
import os
import sys

def main():
    parser = argparse.ArgumentParser(description="Crear un archivo ZIP con los Gerbers y Drills.")
    parser.add_argument("--files", nargs='+', required=True, help="Lista de archivos a incluir.")
    parser.add_argument("--output", required=True, help="Nombre del archivo ZIP de salida.")
    args = parser.parse_args()

    # Gestión de rutas para el Sandbox
    if os.path.exists("/mnt/out"):
        output_path = os.path.join("/mnt/out", args.output)
        files_to_zip = []
        for f in args.files:
            # Si la ruta no es absoluta, asumimos que está en /mnt/out
            if not os.path.isabs(f):
                files_to_zip.append(os.path.join("/mnt/out", f))
            else:
                files_to_zip.append(f)
    else:
        output_path = os.path.join(".tmp", args.output)
        os.makedirs(".tmp", exist_ok=True)
        files_to_zip = args.files

    print(f"📦 Empaquetando {len(files_to_zip)} archivos en {args.output}...")

    try:
        with zipfile.ZipFile(output_path, 'w') as zf:
            for file in files_to_zip:
                if os.path.exists(file):
                    print(f"   - Añadiendo: {os.path.basename(file)}")
                    zf.write(file, os.path.basename(file))
                else:
                    print(f"   ⚠️ Advertencia: Archivo no encontrado: {file}")
        
        print(output_path) # Imprimir ruta final para el bot

    except Exception as e:
        print(f"❌ Error creando ZIP: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()