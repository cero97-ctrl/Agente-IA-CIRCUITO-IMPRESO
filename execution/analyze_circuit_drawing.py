#!/usr/bin/env python3
import argparse
import sys
import os
import subprocess
import json

def run_tool(script, args):
    """Ejecuta una herramienta del framework y devuelve su salida JSON."""
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script)
    cmd = [sys.executable, script_path] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.stderr:
            print(f"   [LOG {script}]: {result.stderr.strip()}", file=sys.stderr)
        return json.loads(result.stdout)
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Analiza un dibujo de circuito y su función.")
    parser.add_argument("--image", required=True, help="Ruta a la imagen del dibujo.")
    parser.add_argument("--prompt", required=True, help="Descripción de la función del circuito.")
    args = parser.parse_args()

    analysis_prompt = f"""
Actúa como un Ingeniero Electrónico experto. Analiza la imagen de un circuito dibujado a mano y la descripción de su función.
Tu tarea es generar una lista de materiales (Bill of Materials) y una netlist en formato JSON.

Función descrita por el usuario: "{args.prompt}"

1.  **Identifica los componentes** en el dibujo (resistencias, capacitores, transistores, ICs, etc.). Asigna un designador (R1, C1, U1).
2.  **Investiga y selecciona componentes reales**. Basado en la función, elige valores o números de parte apropiados (ej: si es un blinker, sugiere un NE555; si es un regulador, un 7805).
3.  **Define la netlist**: Identifica las conexiones entre los pines de los componentes.

Devuelve SÓLO el JSON con la siguiente estructura:
{{
  "components": [ {{ "ref": "R1", "type": "Resistor", "value": "10k Ohm" }} ],
  "netlist": [ {{ "net_name": "VCC", "nodes": ["U1-8", "R1-1"] }} ]
}}
"""
    res = run_tool("analyze_image.py", ["--image", args.image, "--prompt", analysis_prompt])
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()