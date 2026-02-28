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
    radius1 = params.get('radius1', 5)
    radius2 = params.get('radius2', 0)

    script_lines = [
        "import sys",
        "import os",
        "import subprocess",
        "import time",
        "",
        "# --- Configuración de Entorno Gráfico (Headless) ---",
        "# Iniciamos Xvfb para que FreeCADGui tenga un 'monitor' donde dibujar",
        "try:",
        "    # Verificamos si Xvfb ya está corriendo",
        "    if os.system('pgrep Xvfb > /dev/null') != 0:",
        "        print('Iniciando servidor gráfico virtual (Xvfb)...', file=sys.stderr)",
        "        subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1024x768x24', '-ac', '+extension', 'GLX', '+render', '-noreset'])",
        "        time.sleep(3) # Esperar a que Xvfb arranque",
        "except Exception as e:",
        "    print(f'Warning: No se pudo iniciar Xvfb: {e}', file=sys.stderr)",
        "",
        "# El PYTHONPATH se configura en el Dockerfile, la búsqueda manual ya no es necesaria.",
        "try:",
        "    import FreeCAD",
        "    import FreeCADGui as Gui",
        "    import Part",
        "    import Mesh",
        "    import MeshPart",
        "except ImportError as e:",
        "    print(f'Error: No se pudo importar FreeCAD o sus módulos. PYTHONPATH: {sys.path}', file=sys.stderr)",
        "    print(f'Detalle del error: {e}', file=sys.stderr)",
        "    print('Posible causa: La imagen Docker está desactualizada o corrupta.', file=sys.stderr)",
        "    print('SOLUCIÓN: Ejecuta `python3 execution/build_sandbox.py` para reconstruir la imagen.', file=sys.stderr)",
        "    sys.exit(1)",
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
    elif shape == 'sphere':
        obj_name = 'MySphere'
        script_lines.extend([
            f"obj = doc.addObject('Part::Sphere', '{obj_name}')",
            f"obj.Radius = {radius}",
        ])
    elif shape == 'cone':
        obj_name = 'MyCone'
        script_lines.extend([
            f"obj = doc.addObject('Part::Cone', '{obj_name}')",
            f"obj.Radius1 = {radius1}",
            f"obj.Radius2 = {radius2}",
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
        "output_filename_png = os.path.join(output_dir, 'modelo_3d.png')",
        "",
        f"export_obj = doc.getObject('{obj_name}')",
        "if export_obj is None:",
        f"    print('Error: No se pudo encontrar el objeto {obj_name} para exportar.')",
        "    sys.exit(1)",
        "",
        f"print('Objeto {obj_name} encontrado. Procediendo a exportar...')",
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
        "# --- Generar Renderizado Realista (PNG) ---",
        "try:",
        "    print('Generando vista previa realista con FreeCADGui...')",
        "    Gui.setupGui()",
        "    Gui.showMainWindow() # Inicializa la ventana principal en el display virtual",
        "    ",
        "    # Configurar vista",
        "    gui_doc = Gui.ActiveDocument",
        "    if not gui_doc: gui_doc = Gui.getDocument(doc.Name)",
        "    ",
        "    view = gui_doc.ActiveView",
        "    view.viewIsometric()",
        "    view.fitAll()",
        "    view.saveImage(output_filename_png, 800, 600, 'White')",
        "    print(f'PNG guardado en: {output_filename_png}')",
        "except Exception as e:",
        "    print(f'Warning: No se pudo generar el render PNG: {e}', file=sys.stderr)",
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