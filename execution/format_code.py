#!/usr/bin/env python3
import os
import subprocess
import sys


def main():
    """
    Formatea todo el código Python del proyecto utilizando autopep8.
    Se alinea con las reglas definidas en .editorconfig (indentación de 4 espacios)
    y las reglas de auditoría (líneas de hasta 120 caracteres).
    """
    # Verificar instalación de autopep8
    try:
        import autopep8
    except ImportError:
        print("❌ Error: La librería 'autopep8' no está instalada.")
        print("   Ejecuta: pip install autopep8")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    print(f"🎨 Iniciando formateo de código en: {project_root}")

    # Argumentos para autopep8
    # --in-place: Modifica los archivos
    # --recursive: Busca en subdirectorios
    # --max-line-length 120: Coherencia con audit_codebase.py
    # --exclude: Ignorar carpetas de sistema/entorno

    exclude_patterns = ".git,.tmp,__pycache__,venv,env,.venv,.agent,.idea,.vscode"

    command = [
        sys.executable, "-m", "autopep8",
        "--in-place",
        "--recursive",
        "--max-line-length", "120",
        "--exclude", exclude_patterns,
        project_root
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Código formateado exitosamente.")
        else:
            print("⚠️  Hubo advertencias durante el formateo:")
            print(result.stderr)

    except Exception as e:
        print(f"❌ Error ejecutando autopep8: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
