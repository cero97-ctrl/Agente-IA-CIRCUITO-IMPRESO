#!/usr/bin/env bash
set -euo pipefail

# --- Argument Parsing ---
VERSION=""
# Handle arguments
while (( "$#" )); do
  case "$1" in
    --version)
      if (( $# > 1 )) && [ -n "$2" ] && [ "${2:0:1}" != "-" ]; then
        VERSION=$2
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

COMMIT_MSG="WIP: guardar cambios antes de pull"
if [ -n "$VERSION" ]; then
    COMMIT_MSG="Version $VERSION"
fi

# Only commit if there are staged changes
if ! git diff --staged --quiet; then
  echo "Committing changes with message: '$COMMIT_MSG'"
  git commit -m "$COMMIT_MSG"
  
  # Tag the commit if a version was provided
  if [ -n "$VERSION" ]; then
      # Validar formato SemVer (vX.Y.Z)
      if [[ ! "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
          echo "⚠️  Advertencia: La versión '$VERSION' no sigue el formato estándar 'vX.Y.Z' (ej: v1.0.0)."
          echo "   Estándar sugerido: v<Mayor>.<Menor>.<Parche>"
          read -r -p "¿Continuar de todos modos? [y/N] " response
          if [[ ! "$response" =~ ^[yY]$ ]]; then
              echo "❌ Abortando actualización."
              exit 1
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
  fi
else
  echo "No hay cambios locales para commitear."
fi

# Call update_repo.sh to push the branch changes
./update_repo.sh --remote origin --branch "$CURRENT_BRANCH" --push
