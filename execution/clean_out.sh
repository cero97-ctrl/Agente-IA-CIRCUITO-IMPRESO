#!/usr/bin/env bash
set -euo pipefail

# Este script limpia y recrea el directorio .out/ en la raíz del proyecto.

# Obtener el directorio donde se encuentra el script
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")
OUT_DIR="$PROJECT_ROOT/.out"

echo "   - Limpiando y recreando el directorio .out/ ..." >&2

# Eliminar el directorio si existe y recrearlo
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

# Asegurar que .gitkeep exista para que git no ignore el directorio vacío
touch "$OUT_DIR/.gitkeep"