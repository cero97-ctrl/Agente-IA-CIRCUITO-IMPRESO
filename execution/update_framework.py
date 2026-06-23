#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os

def run_command(command, check=True):
    try:
        result = subprocess.run(command, check=check, text=True, capture_output=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if check:
            print(f"❌ Error ejecutando: {' '.join(command)}")
            print(f"   Detalle: {e.stderr.strip()}")
            sys.exit(1)
        return None

def main():
    parser = argparse.ArgumentParser(description="Actualiza solo el núcleo del framework desde la plantilla.")
    parser.add_argument("--template-url", required=True, help="URL del repositorio plantilla")
    parser.add_argument("--branch", default="main", help="Rama de la plantilla a usar")
    
    args = parser.parse_args()
    
    print(f"🔄 Actualizando Núcleo del Framework desde: {args.template_url}")

    # 1. Configurar remote
    remotes = run_command(["git", "remote"], check=False) or ""
    if "template" not in remotes.split():
        run_command(["git", "remote", "add", "template", args.template_url])
    else:
        run_command(["git", "remote", "set-url", "template", args.template_url])

    # 2. Fetch
    print("⬇️  Descargando cambios...")
    run_command(["git", "fetch", "template"])

    # 3. Checkout selectivo (Solo execution/ y .agent/)
    # Esto sobrescribe los scripts del framework con los de la plantilla, pero respeta directives/ de usuario
    paths_to_update = ["execution", ".agent", "requirements.txt", "setup.sh", ".gitignore"]
    
    print("📦 Actualizando archivos del núcleo...")
    try:
        # git checkout template/main -- path/to/file
        cmd = ["git", "checkout", f"template/{args.branch}", "--"] + paths_to_update
        run_command(cmd)
        print("✅ Núcleo actualizado exitosamente.")
        print("   Nota: Tus directivas personalizadas en directives/ no han sido tocadas.")
    except Exception as e:
        print(f"❌ Error durante la actualización: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()