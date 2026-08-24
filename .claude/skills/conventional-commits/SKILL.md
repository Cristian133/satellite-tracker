---
name: conventional-commits
description: Convención de mensajes de commit de este repo (Conventional Commits, validada por el hook commit-msg de commitlint en .pre-commit-config.yaml / frontend/commitlint.config.cjs). Usar al redactar, sugerir o corregir el mensaje de un commit en satellite-tracker.
---

# Mensajes de commit: Conventional Commits + commitlint

## Por qué

Desde que se agregó el hook `commitlint` (stage `commit-msg` en
`.pre-commit-config.yaml`, config en `frontend/commitlint.config.cjs`
extendiendo `@commitlint/config-conventional`), todo commit nuevo en este
repo tiene que pasar ese chequeo o el commit se rechaza. El historial previo
a ese hook mezcla mensajes libres en español ("Agregar predicción de pases
visibles...") con mensajes Conventional Commits en inglés (`feat: ...`,
`fix: ...`, `refactor(backend): ...`) — la parte libre no es una guía a
seguir, es de antes de que existiera la regla. De acá en adelante todo
commit tiene que cumplir el formato de abajo.

## Formato

```
<type>(<scope opcional>): <subject>

<body opcional>

<footer opcional>
```

- **type**: uno de `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`,
  `refactor`, `revert`, `style`, `test`. En minúscula, obligatorio.
- **scope** (opcional): el área tocada, en minúscula — `backend`,
  `frontend`, `ci`, etc. (ejemplo real ya en el historial:
  `refactor(backend): share a single broadcast loop for /ws/positions`).
- **subject**: obligatorio, en minúscula (nada de Sentence case, Title
  Case ni UPPERCASE), en imperativo ("add", no "added"/"adds"), sin punto
  final. La línea completa `type(scope): subject` no puede superar los
  100 caracteres.
- **body/footer**: libres — sí pueden ir en español si hace falta más
  contexto o justificación. Para un cambio incompatible: `BREAKING
  CHANGE: ...` en el footer, o `!` después del type/scope (ej.
  `feat(api)!: ...`).

Seguir el idioma ya usado en el repo para el `subject`: los commits
Conventional Commits existentes están en inglés (`feat:`, `fix:`, `docs:`,
`ci:`, `refactor(backend):`) — mantené esa consistencia salvo que el
usuario pida lo contrario.

## Ejemplos válidos (estilo del repo)

- `feat(frontend): add ground track rendering for satellite orbit`
- `fix(backend): handle empty TLE response from celestrak`
- `chore: bump vite to 5.4.2`
- `ci(frontend): use node 22 for lint job`
- `docs: update pre-commit hook installation steps`

## Qué rompe el hook (errores más comunes)

- Mensaje sin `type:` al principio (`type-empty`/`subject-empty`) — el
  estilo viejo del repo ("Agregar X...") ya no pasa.
- `type` fuera del enum de arriba, o en mayúscula.
- `subject` en Sentence case / Title Case, o terminado en punto.
- Línea de header (`type(scope): subject`) de más de 100 caracteres —
  cortar ahí y mandar el resto al body.

## Si el diff toca varias cosas a la vez

Un solo `type(scope)` no puede describir bien un cambio que mezcla, por
ejemplo, un fix de backend con una tarea de chore en CI. En ese caso
conviene proponer commits separados (uno por type/scope) en vez de forzar
un mensaje que no representa el diff — pero dividir el staging y comitear
cada uno sigue necesitando autorización explícita (ver más abajo).

## Antes de commitear

Para validar un mensaje sin hacer un commit real:

```bash
frontend/node_modules/.bin/commitlint --config frontend/commitlint.config.cjs --edit <archivo-con-el-mensaje>
```

o dejar que corra solo como parte de `git commit` (hook `commit-msg`, una
vez corrido `pre-commit install --hook-type pre-commit --hook-type
commit-msg` — ver README "Pre-commit hooks"). La skill `check-precommit`
cubre el resto de los hooks (lint/tests/build), no el mensaje de commit.

## Ejecutar el commit

Redactar y proponer el mensaje es libre; correr `git commit` (o dividir el
staging en varios commits) no — esa autorización la cubre la skill
`git-ask-first`: mostrar el mensaje exacto propuesto y esperar un sí
explícito antes de ejecutar el commit.
