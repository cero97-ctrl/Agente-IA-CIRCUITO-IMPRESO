#!/usr/bin/env bash
set -euo pipefail

# USO:
#   ./git-update.sh                 # Auto-incrementa el parche (v1.0.0 -> v1.0.1)
#   ./git-update.sh --version v1.2.0 # Establece una versión manual
#   ./git-update.sh --version v2.0.0 # Establece una versión mayor
#
# Este script añade cambios, crea un commit con la versión, crea el tag git y hace push.

# --- Argument Parsing ---
VERSION=""
MANUAL_VERSION=false
# Handle arguments
while (( "$#" )); do
  case "$1" in
    --version)
      if (( $# > 1 )) && [ -n "$2" ] && [ "${2:0:1}" != "-" ]; then
        VERSION=$2
        MANUAL_VERSION=true
        shift 2
      else
        echo "Error: --version requiere un argumento no vacío." >&2
        exit 1
      fi
      ;;
    *) # unsupported flags
      echo "Error: Flag no soportado $1" >&2
      exit 1
      ;;
  esac
done

# Si no se proporciona una versión, auto-incrementar el parche
if [ "$MANUAL_VERSION" = false ]; then
    echo "No se especificó versión. Buscando el último tag para auto-incrementar..."
    # Obtener el último tag, o v0.0.0 si no existe ninguno
    LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
    
    # Quitar el prefijo 'v'
    VERSION_ONLY=${LATEST_TAG#v}
    
    # Separar en partes
    IFS='.' read -r -a parts <<< "$VERSION_ONLY"
    MAJOR=${parts[0]}
    MINOR=${parts[1]}
    PATCH=${parts[2]}
    
    # Incrementar el número de parche
    NEW_PATCH=$((PATCH + 1))
    VERSION="v$MAJOR.$MINOR.$NEW_PATCH"
    echo "Próxima versión (patch): $VERSION"
fi

# Get the directory where the script is located
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"

# Ensure update_repo.sh exists and is executable
if [ ! -f "./update_repo.sh" ]; then
  echo "Error: update_repo.sh not found in $SCRIPT_DIR"
  exit 1
fi
chmod +x ./update_repo.sh

# Detect current branch (defaults to main if detection fails)
CURRENT_BRANCH=$(git symbolic-ref --quiet --short HEAD || echo "main")

echo "Starting update for branch: $CURRENT_BRANCH"

# Commit local changes
git add -A

COMMIT_MSG="Version $VERSION"

# Only commit if there are staged changes
if ! git diff --staged --quiet; then
  echo "Committing changes with message: '$COMMIT_MSG'"
  git commit -m "$COMMIT_MSG"
  
  # Validar formato solo si la versión fue manual
  if [ "$MANUAL_VERSION" = true ]; then
    if [[ ! "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "⚠️  Advertencia: La versión '$VERSION' no sigue el formato estándar 'vX.Y.Z' (ej: v1.0.0)."
        echo "   Estándar sugerido: v<Mayor>.<Menor>.<Parche>"
        read -r -p "¿Continuar de todos modos? [y/N] " response
        if [[ ! "$response" =~ ^[yY]$ ]]; then
            echo "❌ Abortando actualización."
            exit 1
        fi
    fi
  fi

  echo "Tagging commit with version $VERSION..."
  if git rev-parse "$VERSION" >/dev/null 2>&1; then
      echo "Warning: Tag '$VERSION' ya existe. Omitiendo creación de tag."
  else
      git tag -a "$VERSION" -m "$COMMIT_MSG"
      echo "Subiendo tag $VERSION al remoto..."
      git push origin "$VERSION"
  fi

else
  echo "No hay cambios locales para commitear."
fi

# Call update_repo.sh to push the branch changes
./update_repo.sh --remote origin --branch "$CURRENT_BRANCH" --push
