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
    hole_radius = params.get('hole_radius', 0)
    stud_radius = params.get('stud_radius', 0)
    stud_height = params.get('stud_height', 10)
    rotate_axis = params.get('rotate_axis', None)
    rotate_angle = params.get('rotate_angle', 0)
    fillet_radius = params.get('fillet_radius', 0)
    color_name = params.get('color', 'White')
    draw_axes = params.get('draw_axes', False)

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
        "# Inicializar GUI antes de crear el documento para asegurar que se cree el contexto gráfico",
        "try:",
        "    Gui.showMainWindow()",
        "except Exception as e:",
        "    print(f'Warning: No se pudo iniciar la GUI: {e}', file=sys.stderr)",
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
    elif shape == 'torus':
        obj_name = 'MyTorus'
        script_lines.extend([
            f"obj = doc.addObject('Part::Torus', '{obj_name}')",
            f"obj.Radius1 = {radius1}",
            f"obj.Radius2 = {radius2}",
        ])
    else: # Default to a box
        obj_name = 'DefaultBox'
        script_lines.extend([
            f"obj = doc.addObject('Part::Box', '{obj_name}')",
            f"obj.Length = 10",
            f"obj.Width = 10",
            f"obj.Height = 10",
        ])

    # --- Lógica para Agregados (Boolean Fuse) ---
    if stud_radius > 0:
        script_lines.extend([
            "",
            "# --- Operación de Unión (Pivote Superior) ---",
            "stud = doc.addObject('Part::Cylinder', 'StudTool')",
            f"stud.Radius = {stud_radius}",
            f"stud.Height = {stud_height}",
        ])
        
        # Posicionar el pivote (Centrado arriba)
        if shape == 'box':
            script_lines.append(f"stud.Placement.Base = FreeCAD.Vector({length}/2, {width}/2, {height})")
        elif shape == 'sphere':
            script_lines.append(f"stud.Placement.Base = FreeCAD.Vector(0, 0, {radius})")
        else:
            # Cylinder/Cone (Centrados en Z por defecto, top en Height)
            script_lines.append(f"stud.Placement.Base = FreeCAD.Vector(0, 0, {height})")
            
        script_lines.extend([
            "fuse = doc.addObject('Part::MultiFuse', 'Fuse')",
            f"fuse.Shapes = [doc.getObject('{obj_name}'), stud]",
            f"doc.getObject('{obj_name}').ViewObject.Visibility = False",
            "stud.ViewObject.Visibility = False",
            "doc.recompute()",
        ])
        obj_name = "Fuse" # Actualizar el nombre del objeto a exportar

    # --- Lógica para Agujeros (Boolean Cut) ---
    if hole_radius > 0:
        script_lines.extend([
            "",
            "# --- Operación de Corte (Agujero Central) ---",
            "hole = doc.addObject('Part::Cylinder', 'HoleTool')",
            f"hole.Radius = {hole_radius}",
        ])
        
        # Calcular altura del agujero (un poco más largo para asegurar el corte)
        total_h = height + (stud_height if stud_radius > 0 else 0)
        hole_h = total_h + 10 if shape in ['box', 'cylinder', 'cone'] else (radius * 2.5 if shape == 'sphere' else 50)
        script_lines.append(f"hole.Height = {hole_h}")
        
        # Posicionar el agujero (Centrado)
        if shape == 'box':
            script_lines.append(f"hole.Placement.Base = FreeCAD.Vector({length}/2, {width}/2, -5)")
        elif shape == 'sphere':
            script_lines.append(f"hole.Placement.Base = FreeCAD.Vector(0, 0, -{hole_h}/2)")
        else:
            # Cylinder/Cone/Torus (Centrados en Z por defecto)
            script_lines.append("hole.Placement.Base = FreeCAD.Vector(0, 0, -5)")
            
        script_lines.extend([
            "cut = doc.addObject('Part::Cut', 'Cut')",
            f"cut.Base = doc.getObject('{obj_name}')",
            "cut.Tool = hole",
            f"doc.getObject('{obj_name}').ViewObject.Visibility = False",
            "hole.ViewObject.Visibility = False",
            "doc.recompute()",
        ])
        obj_name = "Cut" # Actualizar el nombre del objeto a exportar

    # --- Lógica para Redondeo (Fillet) ---
    if fillet_radius > 0:
        script_lines.extend([
            "",
            "# --- Operación de Redondeo (Fillet) ---",
            "try:",
            "    # Usamos makeFillet directo en la forma (más robusto para scripts)",
            f"    base_obj = doc.getObject('{obj_name}')",
            f"    fillet_shape = base_obj.Shape.makeFillet({fillet_radius}, base_obj.Shape.Edges)",
            "    fillet_obj = doc.addObject('Part::Feature', 'Fillet')",
            "    fillet_obj.Shape = fillet_shape",
            f"    base_obj.ViewObject.Visibility = False",
            "    doc.recompute()",
            "    obj_name = 'Fillet'",
            "except Exception as e:",
            "    print(f'Warning: No se pudo aplicar el redondeo (posiblemente geometría compleja): {e}', file=sys.stderr)",
        ])

    # --- Lógica para Rotación ---
    if rotate_axis and rotate_angle != 0:
        axis_vec = "FreeCAD.Vector(0,0,1)" # Default Z
        if rotate_axis.lower() == 'x': axis_vec = "FreeCAD.Vector(1,0,0)"
        elif rotate_axis.lower() == 'y': axis_vec = "FreeCAD.Vector(0,1,0)"
        
        script_lines.extend([
            "",
            "# --- Operación de Rotación ---",
            f"rot_obj = doc.getObject('{obj_name}')",
            f"rot_obj.Placement = FreeCAD.Placement(rot_obj.Placement.Base, FreeCAD.Rotation({axis_vec}, {rotate_angle}))",
        ])

    # --- Lógica para Color ---
    color_map = {
        'Red': (1.0, 0.0, 0.0), 'Green': (0.0, 1.0, 0.0), 'Blue': (0.0, 0.0, 1.0),
        'Yellow': (1.0, 1.0, 0.0), 'Cyan': (0.0, 1.0, 1.0), 'Magenta': (1.0, 0.0, 1.0),
        'White': (0.9, 0.9, 0.9), 'Black': (0.1, 0.1, 0.1), 'Grey': (0.5, 0.5, 0.5),
        # Spanish fallbacks
        'Rojo': (1.0, 0.0, 0.0), 'Verde': (0.0, 1.0, 0.0), 'Azul': (0.0, 0.0, 1.0),
        'Amarillo': (1.0, 1.0, 0.0), 'Cian': (0.0, 1.0, 1.0), 'Blanco': (0.9, 0.9, 0.9),
        'Negro': (0.1, 0.1, 0.1), 'Gris': (0.5, 0.5, 0.5)
    }
    rgb = color_map.get(color_name, (0.9, 0.9, 0.9))
    
    script_lines.extend([
        "",
        "# --- Aplicar Color ---",
        "try:",
        f"    Gui.getDocument(doc.Name).getObject('{obj_name}').ShapeColor = {rgb}",
        "except Exception as e:",
        "    print(f'Warning: No se pudo aplicar el color: {e}', file=sys.stderr)"
    ])

    # --- Lógica para Dibujar Ejes (Referencia Visual) ---
    if draw_axes:
        script_lines.extend([
            "",
            "# --- Dibujar Ejes de Coordenadas (RGB = XYZ) ---",
            "try:",
            "    # Eje X (Rojo)",
            "    ax_x = doc.addObject('Part::Cylinder', 'AxisX')",
            "    ax_x.Radius = 0.5",
            "    ax_x.Height = 100",
            "    # Rotar 90 grados en Y para alinear con X",
            "    ax_x.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,0), FreeCAD.Rotation(FreeCAD.Vector(0,1,0), 90))",
            "    Gui.getDocument(doc.Name).getObject('AxisX').ShapeColor = (1.0, 0.0, 0.0)",
            "",
            "    # Eje Y (Verde)",
            "    ax_y = doc.addObject('Part::Cylinder', 'AxisY')",
            "    ax_y.Radius = 0.5",
            "    ax_y.Height = 100",
            "    # Rotar -90 grados en X para alinear con Y",
            "    ax_y.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,0), FreeCAD.Rotation(FreeCAD.Vector(1,0,0), -90))",
            "    Gui.getDocument(doc.Name).getObject('AxisY').ShapeColor = (0.0, 1.0, 0.0)",
            "",
            "    # Eje Z (Azul)",
            "    ax_z = doc.addObject('Part::Cylinder', 'AxisZ')",
            "    ax_z.Radius = 0.5",
            "    ax_z.Height = 100",
            "    Gui.getDocument(doc.Name).getObject('AxisZ').ShapeColor = (0.0, 0.0, 1.0)",
            "except Exception as e:",
            "    print(f'Warning: No se pudieron dibujar los ejes: {e}', file=sys.stderr)"
        ])

    script_lines.extend([
        "doc.recompute()",
        "",
        "# --- Guardar el modelo ---",
        "output_dir = '/mnt/out' if os.path.exists('/mnt/out') else '.'",
        "output_filename_step = os.path.join(output_dir, 'modelo_3d.step')",
        "output_filename_stl = os.path.join(output_dir, 'modelo_3d.stl')",
        "output_filename_obj = os.path.join(output_dir, 'modelo_3d.obj')",
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
        "# Exportar a OBJ (Wavefront)",
        "try:",
        "    print('Generando OBJ...')",
        "    mesh_obj = MeshPart.meshFromShape(Shape=export_obj.Shape, LinearDeflection=0.1)",
        "    mesh_obj.write(output_filename_obj)",
        "    print(f'OBJ guardado en: {output_filename_obj}')",
        "except Exception as e:",
        "    print(f'Error exportando a OBJ: {e}', file=sys.stderr)",
        "",
        "# Calcular Propiedades Físicas",
        "try:",
        "    vol = export_obj.Shape.Volume",
        "    # Densidad aprox PLA: 1.24 g/cm3 = 0.00124 g/mm3",
        "    mass = vol * 0.00124",
        "    print(f'PROPERTIES: Volume={vol:.2f} mm3 | Mass={mass:.2f} g (PLA)')",
        "except Exception as e:",
        "    print(f'Error calculando propiedades: {e}', file=sys.stderr)",
        "",
        "# --- Generar Renderizado Realista (PNG) ---",
        "try:",
        "    print('Generando vista previa realista con FreeCADGui...')",
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