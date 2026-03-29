import os
import shutil
import subprocess

def main():
    """
    Prepara un proyecto clonado desde la plantilla para un nuevo uso.
    1. Elimina el historial de Git (.git).
    2. Limpia la carpeta de documentos (docs/).
    3. Limpia la memoria del agente y archivos temporales (.tmp/).
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    print("🧹 Limpiando el proyecto para un nuevo comienzo...")

    # 1. Eliminar .git para empezar un nuevo historial
    git_dir = os.path.join(project_root, ".git")
    if os.path.exists(git_dir):
        print(f"   - Eliminando directorio .git en {git_dir}")
        shutil.rmtree(git_dir, ignore_errors=True)
        print("   - Inicializando nuevo repositorio Git...")
        subprocess.run(["git", "init"], cwd=project_root, check=True)

    # 2. Limpiar carpeta de documentos (docs/)
    docs_dir = os.path.join(project_root, "docs")
    if os.path.exists(docs_dir):
        print(f"   - Limpiando la carpeta {docs_dir}...")
        essential_docs = ["CNC.md", "COMMAND_REFERENCE.md", ".gitignore"]
        for filename in os.listdir(docs_dir):
            if filename in essential_docs:
                continue
            file_path = os.path.join(docs_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"     - No se pudo borrar {file_path}. Razón: {e}")

    # 3. Limpiar carpeta temporal (.tmp/)
    tmp_dir = os.path.join(project_root, ".tmp")
    if os.path.exists(tmp_dir):
        print(f"   - Limpiando la carpeta {tmp_dir}...")
        for filename in os.listdir(tmp_dir):
            if filename == ".gitignore":
                continue
            file_path = os.path.join(tmp_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"     - No se pudo borrar {file_path}. Razón: {e}")

    print("\n✅ ¡Proyecto listo para empezar!")
    print("   - Se ha inicializado un nuevo repositorio Git.")
    print("   - La memoria y los documentos específicos del proyecto anterior han sido eliminados.")
    print("\nPróximos pasos recomendados:")
    print("   1. Edita `README.md` para describir tu nuevo proyecto.")
    print("   2. Crea tu primer commit: `git add .` y `git commit -m 'Initial commit'`")

if __name__ == "__main__":
    main()