#!/usr/bin/env python3
import sys, os, math, subprocess, time, json

def render_board(board_path, output_image):
    if not os.path.exists(board_path):
        print(f"Error: Board file not found: {board_path}")
        sys.exit(1)

    try:
        board = pcbnew.LoadBoard(board_path)
    except Exception as e:
        print(f"Error loading board: {e}")
        sys.exit(1)

    # Setup plot
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.set_aspect('equal')
    ax.set_facecolor('#202020') # Dark PCB background

    # Colors (KiCad standards: Red=Top, Blue=Bottom)
    color_f_cu = '#ff4444' # Rojo Brillante
    color_b_cu = '#4488ff' # Azul Eléctrico
    color_pads = '#eebb00' # Gold
    color_edge = '#ffffff' # White

    # 1. Draw Tracks (F.Cu and B.Cu) and Vias
    for item in board.GetTracks():
        if item.GetClass() in ["TRACK", "PCB_TRACK"]:
            layer = item.GetLayer()
            if layer in [pcbnew.F_Cu, pcbnew.B_Cu]:
                start = item.GetStart()
                end = item.GetEnd()
                width = item.GetWidth()
                
                x1, y1 = pcbnew.ToMM(start.x), pcbnew.ToMM(start.y)
                x2, y2 = pcbnew.ToMM(end.x), pcbnew.ToMM(end.y)
                w_mm = pcbnew.ToMM(width)
                
                color = color_f_cu if layer == pcbnew.F_Cu else color_b_cu
                # Aumentamos el multiplicador de ancho para mejor visibilidad y zorder alto
                ax.plot([x1, x2], [y1, y2], color=color, linewidth=w_mm*10, alpha=0.8, solid_capstyle='round', zorder=10)
        
        elif item.GetClass() in ["VIA", "PCB_VIA"]:
            pos = item.GetPosition()
            x, y = pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)
            width = pcbnew.ToMM(item.GetWidth())
            # Las vías se dibujan como anillos concéntricos
            ax.add_patch(Circle((x, y), width/2, color='#bcbcbc', zorder=5))
            ax.add_patch(Circle((x, y), width/4, color='#202020', zorder=6))

    # 2. Draw Pads
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            pos = pad.GetPosition()
            x, y = pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)
            size = pad.GetSize()
            w, h = pcbnew.ToMM(size.x), pcbnew.ToMM(size.y)
            shape = pad.GetShape()
            
            patch = None
            if shape == pcbnew.PAD_SHAPE_CIRCLE:
                patch = Circle((x, y), w/2, color=color_pads, alpha=1.0, zorder=15)
            elif shape in [pcbnew.PAD_SHAPE_RECT, pcbnew.PAD_SHAPE_ROUNDRECT, pcbnew.PAD_SHAPE_OVAL]:
                patch = Rectangle((x - w/2, y - h/2), w, h, color=color_pads, alpha=1.0, zorder=15)
            else:
                patch = Circle((x, y), min(w, h)/2, color=color_pads, alpha=1.0, zorder=15)
            
            if patch:
                ax.add_patch(patch)

    # 3. Draw Edge.Cuts
    for drawing in board.GetDrawings():
        if drawing.GetLayer() == pcbnew.Edge_Cuts:
            try:
                # Attempt to get start/end for line segments
                if hasattr(drawing, 'GetStart') and hasattr(drawing, 'GetEnd'):
                    start = drawing.GetStart()
                    end = drawing.GetEnd()
                    x1, y1 = pcbnew.ToMM(start.x), pcbnew.ToMM(start.y)
                    x2, y2 = pcbnew.ToMM(end.x), pcbnew.ToMM(end.y)
                    
                    shape = drawing.GetShape() if hasattr(drawing, 'GetShape') else -1
                    
                    if shape == pcbnew.SHAPE_T_RECT:
                        rect = Rectangle((x1, y1), x2 - x1, y2 - y1, linewidth=2, edgecolor=color_edge, facecolor='none')
                        ax.add_patch(rect)
                    elif shape == pcbnew.SHAPE_T_CIRCLE:
                        radius = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                        if hasattr(drawing, 'GetRadius'):
                            radius = pcbnew.ToMM(drawing.GetRadius())
                        circle = Circle((x1, y1), radius, linewidth=2, edgecolor=color_edge, facecolor='none')
                        ax.add_patch(circle)
                    else:
                        # Default to line segment
                        ax.plot([x1, x2], [y1, y2], color=color_edge, linewidth=2)
            except:
                pass

    ax.autoscale()
    ax.invert_yaxis()
    plt.title("Vista Previa PCB (Capas F.Cu y B.Cu)", color='white')
    plt.axis('off') # Hide axis
    
    plt.savefig(output_image, dpi=100, bbox_inches='tight', facecolor='#101010')
    print(f"Render saved to {output_image}")

def start_xvfb():
    """Inicia el servidor gráfico virtual si no está corriendo."""
    os.environ['DISPLAY'] = ':99'
    xvfb_proc = None
    try:
        if os.system('pgrep Xvfb > /dev/null') != 0:
            print('Iniciando servidor gráfico virtual (Xvfb)...', file=sys.stderr)
            xvfb_proc = subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1024x768x24', '-ac', '+extension', 'GLX', '+render', '-noreset'])
            time.sleep(3)
            if xvfb_proc.poll() is not None:
                raise RuntimeError(f"Xvfb terminó inesperadamente. Código: {xvfb_proc.returncode}")
    except Exception as e:
        raise RuntimeError(f"Error fatal al iniciar Xvfb: {e}")
    return xvfb_proc

if __name__ == "__main__":
    xvfb_proc = None
    try:
        xvfb_proc = start_xvfb()

        # Importar librerías que dependen del entorno gráfico AHORA
        import pcbnew
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle, Circle

        if len(sys.argv) < 3:
            print("Usage: render_pcb.py <board_file> <output_image>")
            sys.exit(1)
        
        render_board(sys.argv[1], sys.argv[2])

    except Exception as e:
        # Capturar cualquier error para asegurar que se imprima como JSON
        # y que el proceso termine correctamente.
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)
    finally:
        if xvfb_proc:
            xvfb_proc.terminate()