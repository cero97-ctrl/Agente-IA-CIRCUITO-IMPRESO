#!/usr/bin/env python3
import os
import shutil
import sys
import json
import subprocess


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    print(f"🧹 Limpiando proyecto en: {project_root}", file=sys.stderr)

    # 0. Limpiar .out/ usando un script bash dedicado
    clean_out_script_path = os.path.join(script_dir, "clean_out.sh")
    if os.path.exists(clean_out_script_path):
        print("   - Ejecutando script de limpieza para .out/...", file=sys.stderr)
        os.chmod(clean_out_script_path, 0o755) # Asegurar que sea ejecutable
        result = subprocess.run([clean_out_script_path], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"     ⚠️ Error en clean_out.sh: {result.stderr}", file=sys.stderr)
    else:
        print(f"     ⚠️ No se encontró el script 'clean_out.sh'.", file=sys.stderr)

    # 1. Limpiar .tmp/
    tmp_dir = os.path.join(project_root, ".tmp")
    if os.path.exists(tmp_dir):
        print("   - Limpiando .tmp/ ...", file=sys.stderr)
        for filename in os.listdir(tmp_dir):
            file_path = os.path.join(tmp_dir, filename)
            try:
                # Mantener archivos críticos (base de datos, .gitkeep)
                if filename in [".gitkeep", "agent_database.db", "telegram_offset.txt", "last_3d_params.json", "current_design.json"]:
                    print(f"     🛡️ Protegiendo archivo crítico: {filename}", file=sys.stderr)
                    continue

                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"     ⚠️ Error borrando {file_path}: {e}", file=sys.stderr)

    # 2. Limpiar __pycache__ y otros artefactos de Python
    print("   - Eliminando cachés de Python (__pycache__, .pytest_cache) ...", file=sys.stderr)
    for root, dirs, files in os.walk(project_root):
        # Modificar dirs in-place para evitar recorrer directorios eliminados
        if "__pycache__" in dirs:
            path = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(path)
                dirs.remove("__pycache__")
            except Exception as e:
                print(f"     ⚠️ Error borrando {path}: {e}", file=sys.stderr)

        if ".pytest_cache" in dirs:
            path = os.path.join(root, ".pytest_cache")
            try:
                shutil.rmtree(path)
                dirs.remove(".pytest_cache")
            except Exception as e:
                print(f"     ⚠️ Error borrando {path}: {e}", file=sys.stderr)

    # 3. Limpiar reportes y backups específicos
    files_to_clean = ["WEEKLY_REPORT.md", "README.md.bak"]
    print("   - Eliminando reportes antiguos y backups ...", file=sys.stderr)
    for f in files_to_clean:
        f_path = os.path.join(project_root, f)
        if os.path.exists(f_path):
            try:
                os.remove(f_path)
                print(f"     Eliminado: {f}", file=sys.stderr)
            except Exception as e:
                print(f"     ⚠️ Error borrando {f}: {e}", file=sys.stderr)

    # 4. Limpiar archivos no esenciales en docs/
    docs_dir = os.path.join(project_root, "docs")
    if os.path.exists(docs_dir):
        print("   - Limpiando archivos no esenciales en docs/ ...", file=sys.stderr)
        for filename in os.listdir(docs_dir):
            # No borrar archivos esenciales
            if filename in ["CNC.md", "COMMAND_REFERENCE.md", ".gitignore"]:
                continue

            if filename.endswith(".tex") or filename.startswith("Reporte_Tecnico_"):
                f_path = os.path.join(docs_dir, filename)
                try:
                    os.remove(f_path)
                    print(f"     Eliminado de docs/: {filename}", file=sys.stderr)
                except Exception as e:
                    print(f"     ⚠️ Error borrando {filename}: {e}", file=sys.stderr)

    print(json.dumps({"status": "success", "message": "Limpieza completada."}))


if __name__ == "__main__":
    main()
