---
name: check-precommit
description: Corre los mismos checks que el hook de pre-commit (lint, format, tests y build de backend y frontend) sin necesidad de hacer un commit real, e interpreta los resultados y qué arreglar. Usar cuando el usuario pide correr los checks, el lint, los tests, verificar que un commit no rompa nada, o pregunta si esto pasaría el pre-commit antes de comitear.
allowed-tools: Bash(scripts/check-precommit.sh*) Bash(cd backend && ruff*) Bash(cd backend && python -m pytest*) Bash(cd frontend && npm run lint*) Bash(cd frontend && npm test*) Bash(cd frontend && npm run build*)
---

# Correr los checks de pre-commit sin comitear

## Qué corre

`scripts/check-precommit.sh` ejecuta los mismos hooks que define
`.pre-commit-config.yaml`, sin necesitar un commit real:

- Higiene genérica: trailing-whitespace, end-of-file-fixer,
  check-merge-conflict, check-added-large-files, check-yaml.
- Backend (`^backend/`): `ruff` lint con `--fix` automático, `ruff-format`
  (autofix), `pytest -q`, `compileall` (chequeo de build).
- Frontend (`^frontend/`): `eslint` (`npm run lint`), `vitest` (`npm test`),
  `vite build` (`npm run build`).

Por default corre solo sobre lo que está en el staging area (`git add`),
igual que correría un commit real. Con `--all` corre sobre todo el repo.

## Cómo usarla

1. Correr `scripts/check-precommit.sh` (agregar `--all` si el usuario quiere
   chequear todo el repo, no solo lo staged).
2. Si no hay nada staged, el script mismo cae a `--all-files` y lo avisa —
   no hace falta pedir permiso para eso, es comportamiento propio del script.
3. Requiere `backend/.venv` y `frontend/node_modules` ya instalados (ver
   "Getting Started" del README). Si no existen, el script lo va a decir
   explícitamente — no instalar nada por tu cuenta sin que el usuario lo pida.

## Si algo falla, cómo interpretarlo (no solo repetir el output)

- **ruff (lint) / ruff-format**: son hooks autofix — si "fallan", en la
  mayoría de los casos es porque *ya arreglaron* algo
  (`--exit-non-zero-on-fix`) y el archivo quedó modificado en disco. No es
  un bug a diagnosticar: mostrale al usuario qué archivos cambiaron
  (`git diff` sobre esos paths) y avisale que hay que volver a `git add`
  esos archivos antes de reintentar. No lo hagas vos por tu cuenta — es una
  modificación del staging area, que la confirme el usuario.
- **backend - pytest**: leer el output real de pytest (no asumir), ubicar el
  test que rompió y arreglar el código de la app, no el test — salvo que el
  test mismo esté mal. Si hay que tocar un test porque el comportamiento
  cambió a propósito, decirlo explícitamente antes de tocarlo.
- **backend - compileall**: es un `SyntaxError`/`ImportError` real; el
  mensaje trae archivo y línea.
- **frontend - eslint**: probar `cd frontend && npm run lint:fix` antes de
  tocar código a mano; lo que no se autofixea trae archivo:línea y regla en
  el output.
- **frontend - vitest**: mismo criterio que pytest — arreglar el código,
  salvo cambio de comportamiento intencional.
- **frontend - vite build**: casi siempre errores de tipos (`tsc -b`); el
  output trae archivo:línea.

## Al terminar

Volvé a correr `scripts/check-precommit.sh` después de cada fix para
confirmar que ahora sí pasa todo — no asumas que un solo fix alcanza.
Re-correr el script no necesita confirmación: no cambia código por sí mismo
más allá de los autofixes que los propios hooks (ruff/eslint) ya aplican
como parte de correr.

Si el resultado final es "todo pasó" y el usuario no pidió comitear, no
comitees por tu cuenta — eso lo cubre la skill `git-ask-first`.
