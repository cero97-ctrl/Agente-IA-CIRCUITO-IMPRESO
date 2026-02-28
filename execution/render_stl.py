#!/usr/bin/env python3
import sys
import os
import struct
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import art3d

def load_stl(file_path):
    # Simple STL loader (Binary & ASCII support)
    # Returns vertices as numpy array (N, 3, 3) -> N triangles, 3 vertices, 3 coords
    
    with open(file_path, 'rb') as f:
        header = f.read(80)
        count_bytes = f.read(4)
        if len(count_bytes) < 4:
            return []
        count = struct.unpack('<I', count_bytes)[0]
        
        # Check if binary: file size matches expected size
        expected_size = 80 + 4 + count * 50
        file_size = os.path.getsize(file_path)
        
        if file_size == expected_size:
            # Binary STL
            triangles = []
            for _ in range(count):
                data = f.read(50)
                # 12 floats (normal + 3 vertices), 2 bytes attribute
                floats = struct.unpack('<12f', data[:48])
                # Skip normal (0-2), take vertices (3-11)
                v1 = (floats[3], floats[4], floats[5])
                v2 = (floats[6], floats[7], floats[8])
                v3 = (floats[9], floats[10], floats[11])
                triangles.append([v1, v2, v3])
            return np.array(triangles)
        else:
            # ASCII STL (Fallback)
            triangles = []
            vertices = []
            with open(file_path, 'r') as f_txt:
                for line in f_txt:
                    parts = line.strip().split()
                    if len(parts) > 0 and parts[0] == 'vertex':
                        vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                        if len(vertices) == 3:
                            triangles.append(vertices)
                            vertices = []
            return np.array(triangles)

def render_stl(stl_path, output_image):
    if not os.path.exists(stl_path):
        print(f"Error: File not found {stl_path}")
        sys.exit(1)

    try:
        triangles = load_stl(stl_path)
        if len(triangles) == 0:
            print("Error: Empty or invalid STL")
            sys.exit(1)
            
        # Limit triangles for performance in preview
        if len(triangles) > 5000:
            indices = np.random.choice(len(triangles), 5000, replace=False)
            triangles = triangles[indices]

        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # Create collection
        mesh = art3d.Poly3DCollection(triangles)
        mesh.set_edgecolor('k')
        mesh.set_facecolor('#00aaff')
        mesh.set_alpha(0.5)
        ax.add_collection3d(mesh)

        # Auto-scale
        all_points = triangles.reshape(-1, 3)
        min_vals = all_points.min(axis=0)
        max_vals = all_points.max(axis=0)
        
        # Center
        center = (min_vals + max_vals) / 2
        range_vals = max_vals - min_vals
        max_range = range_vals.max()
        
        ax.set_xlim(center[0] - max_range/2, center[0] + max_range/2)
        ax.set_ylim(center[1] - max_range/2, center[1] + max_range/2)
        ax.set_zlim(center[2] - max_range/2, center[2] + max_range/2)
        
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        plt.title(f"Vista Previa 3D: {os.path.basename(stl_path)}")
        
        plt.savefig(output_image, dpi=100, bbox_inches='tight')
        print(f"Render saved to {output_image}")
        
    except Exception as e:
        print(f"Error rendering STL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: render_stl.py <stl_file> <output_image>")
        sys.exit(1)
    render_stl(sys.argv[1], sys.argv[2])