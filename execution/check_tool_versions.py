#!/usr/bin/env python3
import subprocess
import sys
import json

def get_version(command):
    try:
        # Ejecutamos el comando con --version
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        output = result.stdout.strip() or result.stderr.strip()
        # Tomamos la primera línea que suele contener la versión
        return output.split('\n')[0]
    except FileNotFoundError:
        return "No instalado"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    tools = {
        "OS (Base)": ["cat", "/etc/os-release"],
        "Python": ["python3", "--version"],
        "KiCad (PCB Editor)": ["kicad-cli", "--version"], # KiCad 8+ usa kicad-cli
        "FreeCAD": ["freecadcmd", "--version"],
        "pcb2gcode": ["pcb2gcode", "--version"],
        "Gerber Tools": ["gerbv", "--version"] # Si estuviera instalado
    }

    report = {}

    # Caso especial para OS Release
    try:
        with open("/etc/os-release", "r") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("PRETTY_NAME="):
                    report["OS (Base)"] = line.split("=")[1].strip().replace('"', '')
                    break
    except:
        report["OS (Base)"] = "Linux Genérico"

    # Chequear herramientas
    for name, cmd in tools.items():
        if name == "OS (Base)": continue
        report[name] = get_version(cmd)

    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()