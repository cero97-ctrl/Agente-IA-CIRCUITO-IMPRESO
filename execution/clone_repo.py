import argparse
import subprocess
import sys
import os
import shutil
import json

def main():
    parser = argparse.ArgumentParser(description="Clona un repositorio de GitHub.")
    parser.add_argument("--repo-url", required=True, help="URL del repositorio.")
    parser.add_argument("--branch", help="Rama específica.")
    parser.add_argument("--output-dir", required=True, help="Directorio de destino.")
    
    args = parser.parse_args()
    
    # Asegurar que el directorio de salida esté limpio
    if os.path.exists(args.output_dir):
        try:
            shutil.rmtree(args.output_dir)
        except Exception as e:
            print(json.dumps({"error": f"No se pudo limpiar el directorio: {str(e)}"}))
            sys.exit(1)

    cmd = ["git", "clone", args.repo_url, args.output_dir]
    if args.branch:
        cmd.extend(["--branch", args.branch])
        
    try:
        # Ejecutar git clone
        result = subprocess.run(
            cmd, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        print(json.dumps({"status": "success", "local_repo_path": args.output_dir}))
        
    except subprocess.CalledProcessError as e:
        print(json.dumps({"error": f"Error al clonar: {e.stderr}"}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()