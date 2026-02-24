#!/usr/bin/env python3
import sys
import os
import importlib
import shutil

# Colores ANSI
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

REQUIRED_DIRS = ["execution", "directives", "docs", ".tmp"]
REQUIRED_FILES = [".env", "requirements.txt", "README.md"]
# Mapeo de nombre de paquete pip -> nombre de importación
REQUIRED_MODULES = {
    "requests": "requests",
    "python-dotenv": "dotenv",
    "google-generativeai": "google.generativeai",
    "chromadb": "chromadb",
    "docker": "docker",
    "pypdf": "pypdf",
    "PyYAML": "yaml"
}

def check_python_version():
    print(f"{Colors.HEADER}1. Verificando Python...{Colors.ENDC}")
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 10):
        print(f"{Colors.FAIL}❌ Python {v.major}.{v.minor} detectado. Se requiere Python 3.10+{Colors.ENDC}")
        return False
    print(f"{Colors.OKGREEN}✅ Python {v.major}.{v.minor}.{v.micro} OK{Colors.ENDC}")
    return True

def check_directories():
    print(f"\n{Colors.HEADER}2. Verificando Directorios...{Colors.ENDC}")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    all_ok = True
    for d in REQUIRED_DIRS:
        path = os.path.join(root, d)
        if os.path.exists(path) and os.path.isdir(path):
            print(f"{Colors.OKGREEN}✅ {d}/ encontrado{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}❌ {d}/ NO encontrado{Colors.ENDC}")
            if d == ".tmp":
                try:
                    os.makedirs(path, exist_ok=True)
                    print(f"{Colors.WARNING}   -> Creado directorio .tmp automáticamente{Colors.ENDC}")
                except Exception as e:
                    print(f"{Colors.FAIL}   -> No se pudo crear: {e}{Colors.ENDC}")
                    all_ok = False
            else:
                all_ok = False
    return all_ok

def check_files():
    print(f"\n{Colors.HEADER}3. Verificando Archivos Críticos...{Colors.ENDC}")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    all_ok = True
    for f in REQUIRED_FILES:
        path = os.path.join(root, f)
        if os.path.exists(path) and os.path.isfile(path):
            print(f"{Colors.OKGREEN}✅ {f} encontrado{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}❌ {f} NO encontrado{Colors.ENDC}")
            if f == ".env":
                print(f"{Colors.WARNING}   -> Crea un archivo .env con tus API KEYS.{Colors.ENDC}")
            all_ok = False
    return all_ok

def check_dependencies():
    print(f"\n{Colors.HEADER}4. Verificando Dependencias (Imports)...{Colors.ENDC}")
    all_ok = True
    for package, module_name in REQUIRED_MODULES.items():
        try:
            importlib.import_module(module_name)
            print(f"{Colors.OKGREEN}✅ {package} ({module_name}) importado correctamente{Colors.ENDC}")
        except ImportError:
            print(f"{Colors.FAIL}❌ {package} NO instalado (Falla import: {module_name}){Colors.ENDC}")
            all_ok = False
    
    if not all_ok:
        print(f"\n{Colors.WARNING}💡 Ejecuta: pip install -r requirements.txt{Colors.ENDC}")
    return all_ok

def check_docker():
    print(f"\n{Colors.HEADER}5. Verificando Docker (Opcional para Sandbox)...{Colors.ENDC}")
    if shutil.which("docker"):
        print(f"{Colors.OKGREEN}✅ Docker CLI encontrado{Colors.ENDC}")
        try:
            import docker
            client = docker.from_env()
            client.ping()
            print(f"{Colors.OKGREEN}✅ Docker Daemon respondiendo{Colors.ENDC}")
            
            # Verificar si la imagen del sandbox existe
            try:
                client.images.get("agent-sandbox:latest")
                print(f"{Colors.OKGREEN}✅ Imagen 'agent-sandbox:latest' lista{Colors.ENDC}")
            except docker.errors.ImageNotFound:
                print(f"{Colors.WARNING}⚠️  Imagen 'agent-sandbox:latest' NO encontrada. Se usará python:slim (más lento/básico).{Colors.ENDC}")
                print(f"{Colors.WARNING}   -> Recomendado: python execution/build_sandbox.py{Colors.ENDC}")
        except Exception:
             print(f"{Colors.WARNING}⚠️  Docker instalado pero el Daemon no responde (o librería python 'docker' no instalada){Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}⚠️  Docker no encontrado en PATH. El Sandbox no funcionará.{Colors.ENDC}")
    return True

def main():
    print(f"{Colors.BOLD}🔍 INICIANDO CHEQUEO DE SALUD DEL SISTEMA{Colors.ENDC}")
    
    steps_results = [
        check_python_version(),
        check_directories(),
        check_files(),
        check_dependencies(),
        check_docker()
    ]
    
    print("\n" + "="*40)
    if all(steps_results):
        print(f"{Colors.OKGREEN}{Colors.BOLD}✨ SISTEMA SALUDABLE. LISTO PARA OPERAR.{Colors.ENDC}")
        sys.exit(0)
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}💀 SE ENCONTRARON ERRORES CRÍTICOS.{Colors.ENDC}")
        sys.exit(1)

if __name__ == "__main__":
    main()