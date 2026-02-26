#!/usr/bin/env python3
import json
import argparse
import os
import sys

def generate_script(params, output_script_path):
    shape = params.get('shape', 'box')
    length = params.get('length', 10)
    width = params.get('width', 10)
    height = params.get('height', 10)
    radius = params.get('radius', 5)

    script_lines = [
        "import sys",
        "import os",
        "import glob",
        "",
        "# FreeCAD's Python interpreter needs the path to its libraries",
        "possible_globs = [",
        "    '/usr/lib/freecad*/lib',",
        "    '/usr/lib/x86_64-linux-gnu/freecad*/lib',",
        "    '/usr/local/lib/freecad*/lib'",
        "]",
        "",
        "found_paths = []",
        "for g in possible_globs:",
        "    found_paths.extend(glob.glob(g))",
        "",
        "path_added = False",
        "for p in found_paths:",
        "    if os.path.exists(os.path.join(p, 'FreeCAD.so')):",
        "        if p not in sys.path:",
        "            sys.path.append(p)",
        "            print(f'Added FreeCAD path: {p}', file=sys.stderr)",
        "            path_added = True",
        "            break",
        "",
        "try:",
        "    import FreeCAD",
        "except ImportError:",
        "    if not path_added:",
        "        print('Attempting brute force search for FreeCAD.so in /usr/lib...', file=sys.stderr)",
        "        for root, dirs, files in os.walk('/usr/lib'):",
        "            if 'FreeCAD.so' in files:",
        "                sys.path.append(root)",
        "                print(f'Found and added: {root}', file=sys.stderr)",
        "                break",
        "    try:",
        "        import FreeCAD",
        "    except ImportError:",
        "        print(f'Error: No se pudo importar FreeCAD. sys.path: {sys.path}', file=sys.stderr)",
        "        sys.exit(1)",
        "",
        "import Part",
        "import Mesh",
        "import MeshPart",
        "",
        "doc = FreeCAD.newDocument('Model')",
        "",
    ]

    obj_name = "MyObject"

    if shape == 'box':
        obj_name = 'MyBox'
        script_lines.extend([
            f"obj = doc.addObject('Part::Box', '{obj_name}')",
            f"obj.Length = {length}",
            f"obj.Width = {width}",
            f"obj.Height = {height}",
        ])
    elif shape == 'cylinder':
        obj_name = 'MyCylinder'
        script_lines.extend([
            f"obj = doc.addObject('Part::Cylinder', '{obj_name}')",
            f"obj.Radius = {radius}",
            f"obj.Height = {height}",
        ])
    else: # Default to a box
        obj_name = 'DefaultBox'
        script_lines.extend([
            f"obj = doc.addObject('Part::Box', '{obj_name}')",
            f"obj.Length = 10",
            f"obj.Width = 10",
            f"obj.Height = 10",
        ])

    script_lines.extend([
        "doc.recompute()",
        "",
        "# --- Guardar el modelo ---",
        "output_dir = '/mnt/out' if os.path.exists('/mnt/out') else '.'",
        "output_filename_step = os.path.join(output_dir, 'modelo_3d.step')",
        "output_filename_stl = os.path.join(output_dir, 'modelo_3d.stl')",
        "",
        f"export_obj = doc.getObject('{obj_name}')",
        "if export_obj is None:",
        "    print(f'Error: No se pudo encontrar el objeto {obj_name} para exportar.')",
        "    sys.exit(1)",
        "",
        "print(f'Objeto {obj_name} encontrado. Procediendo a exportar...')",
        "",
        "# Exportar a STEP (formato CAD estándar)",
        "try:",
        "    Part.export([export_obj], output_filename_step)",
        "    print(f'STEP guardado en: {output_filename_step}')",
        "except Exception as e:",
        "    print(f'Error exportando a STEP: {e}', file=sys.stderr)",
        "    sys.exit(1)",
        "",
        "# Exportar a STL (formato de malla para impresión 3D)",
        "try:",
        "    print('Generando malla para STL...')",
        "    mesh = MeshPart.meshFromShape(Shape=export_obj.Shape, LinearDeflection=0.1)",
        "    mesh.write(output_filename_stl)",
        "    print(f'STL guardado en: {output_filename_stl}')",
        "except Exception as e:",
        "    print(f'Error exportando a STL: {e}', file=sys.stderr)",
        "    sys.exit(1)",
        "",
        "# --- Verificación final ---",
        "if not os.path.exists(output_filename_stl):",
        "    print('Error: La exportación finalizó sin errores aparentes, pero el archivo STL no se creó en el disco.', file=sys.stderr)",
        "    sys.exit(1)",
    ])

    try:
        os.makedirs(os.path.dirname(output_script_path), exist_ok=True)
        with open(output_script_path, 'w') as f:
            f.write("\n".join(script_lines))
        print(json.dumps({"status": "success", "file": output_script_path}))
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"Error escribiendo script de FreeCAD: {e}"}))
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera un script de Python para FreeCAD.")
    parser.add_argument("--params", required=True, help="Parámetros JSON para el modelo 3D.")
    parser.add_argument("--output", required=True, help="Ruta de salida para el script Python generado.")
    args = parser.parse_args()

    try:
        params_data = json.loads(args.params)
    except json.JSONDecodeError:
        print(json.dumps({"status": "error", "message": "Parámetros JSON no válidos."}))
        sys.exit(1)

    generate_script(params_data, args.output)