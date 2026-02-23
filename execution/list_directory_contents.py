import argparse
import os
import json
import sys

def main():
    parser = argparse.ArgumentParser(description="Lista la estructura de un directorio.")
    parser.add_argument("--root-dir", required=True, help="Directorio a analizar.")
    parser.add_argument("--output-file", required=True, help="Archivo de salida.")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.root_dir):
        print(json.dumps({"error": f"El directorio {args.root_dir} no existe."}))
        sys.exit(1)

    lines = []
    try:
        for root, dirs, files in os.walk(args.root_dir):
            # Omitir carpeta .git para no ensuciar
            if ".git" in dirs:
                dirs.remove(".git")
                
            level = root.replace(args.root_dir, "").count(os.sep)
            indent = " " * 4 * level
            lines.append(f"{indent}{os.path.basename(root)}/")
            subindent = " " * 4 * (level + 1)
            for f in files:
                lines.append(f"{subindent}{f}")
                
        # Guardar en archivo
        os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
            
        print(json.dumps({"status": "success", "structure_file_path": args.output_file}))

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()