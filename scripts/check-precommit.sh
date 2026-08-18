#!/usr/bin/env bash
# Corre los mismos checks que el hook de pre-commit (limpieza básica, lint,
# tests unitarios y build para FE y BE), sin necesidad de hacer un commit
# real. Pensado para correrlo mientras trabajás y confirmar que un commit
# no va a fallar antes de intentarlo.
#
# Uso:
#   scripts/check-precommit.sh          # sobre los archivos staged (lo mismo que correría `git commit`)
#   scripts/check-precommit.sh --all    # sobre todo el repo, haya o no algo staged
#
# Requiere que ya hayas seguido el "Getting Started" del README para el
# backend (.venv) y el frontend (node_modules) — este script no instala
# nada, solo corre las herramientas que ya deberían estar ahí.

set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

on_error() {
  echo ""
  echo "❌ Algo falló — el commit fallaría en este estado. Revisá arriba qué hook rompió."
}
trap on_error ERR

if command -v pre-commit >/dev/null 2>&1; then
  PRE_COMMIT=(pre-commit)
elif [ -x backend/.venv/bin/pre-commit ]; then
  PRE_COMMIT=(backend/.venv/bin/pre-commit)
else
  echo "❌ No se encontró 'pre-commit' instalado (ni en el PATH ni en backend/.venv)." >&2
  echo "   Instalalo con: pip install pre-commit  (ver README, sección 'Pre-commit hooks')" >&2
  exit 1
fi

if [ "${1:-}" = "--all" ]; then
  echo "▶ Corriendo todos los hooks sobre TODO el repo..."
  "${PRE_COMMIT[@]}" run --all-files
elif git diff --cached --quiet; then
  echo "⚠️  No hay nada en el staging area (git add). No hay qué comparar contra un commit real;"
  echo "   corriendo sobre todo el repo en su lugar."
  "${PRE_COMMIT[@]}" run --all-files
else
  echo "▶ Corriendo los hooks sobre los archivos staged (lo mismo que correría 'git commit')..."
  "${PRE_COMMIT[@]}" run
fi

echo ""
echo "✅ Todo pasó — el commit no debería fallar por pre-commit."
