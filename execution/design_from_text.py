#!/usr/bin/env python3
import argparse
import sys
import os
import json
import subprocess

def main():
    parser = argparse.ArgumentParser(description="Genera un diseño de circuito (JSON) a partir de texto.")
    parser.add_argument("--prompt", required=True, help="Descripción del circuito.")
    args = parser.parse_args()

    design_prompt = f"""
Actúa como un Ingeniero Electrónico experto. Tu tarea es diseñar un circuito electrónico funcional basado en la siguiente descripción y generar una lista de materiales (Bill of Materials) y una netlist en formato JSON.

Descripción del usuario: "{args.prompt}"

1.  **Selecciona componentes reales**. Basado en la función, elige valores o números de parte apropiados (ej: si es un blinker, sugiere un NE555; si es un regulador, un 7805).
2.  **Define la netlist**: Identifica las conexiones entre los pines de los componentes. Asegúrate de incluir alimentación (VCC, GND) si es necesario.

Devuelve SÓLO el JSON con la siguiente estructura:
{{
  "components": [
    {{ "ref": "R1", "type": "Resistor", "value": "10k", "footprint": "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal" }},
    {{ "ref": "D1", "type": "LED", "value": "Red", "footprint": "LED_THT:LED_D5.0mm" }}
  ],
  "netlist": [
    {{ "net_name": "VCC", "nodes": ["U1-8", "R1-1"] }},
    {{ "net_name": "GND", "nodes": ["U1-1", "D1-K"] }}
  ]
}}
"""
    
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_with_llm.py")
    cmd = [sys.executable, script_path, "--prompt", design_prompt]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.stderr:
             print(f"   [LOG chat_with_llm]: {result.stderr.strip()}", file=sys.stderr)
        
        try:
            response = json.loads(result.stdout)
            if "content" in response:
                print(json.dumps({"status": "success", "design": response["content"]}))
            else:
                print(json.dumps({"status": "error", "message": response.get("error", "Unknown error from LLM")}))
        except json.JSONDecodeError:
             print(json.dumps({"status": "error", "message": "Invalid JSON from chat_with_llm", "details": result.stdout}))

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))

if __name__ == "__main__":
    main()