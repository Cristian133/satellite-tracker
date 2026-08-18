---
name: git-ask-first
description: Política del usuario para este repo: nunca ejecutar un comando de git que modifique el estado del repositorio (crear o cambiar de rama, commit, push, merge, rebase, reset, tag, borrar ramas, stash pop/drop, cherry-pick, abrir un PR, etc.) sin haber recibido antes un "sí" explícito para esa acción puntual. En vez de ejecutarlo, sugerirlo y esperar confirmación. USAR SIEMPRE antes de correr cualquiera de esas acciones por Bash o por una tool de git/gh — tanto cuando el usuario lo pide directamente ("comitea esto", "hace push", "creemos una rama", "mergeá esto", "abramos un PR", "hace rebase", "reseteá a...") como, sobre todo, cuando Claude está por hacerlo por iniciativa propia sin que nadie lo haya pedido en ese mensaje (p. ej. crear una rama automáticamente antes de editar código, o comitear al terminar una tarea). Los comandos de solo lectura (git status, diff, log, show, branch --list, stash list, fetch) no la necesitan.
---

# Git: pedir autorización antes de mutar el repo

## La regla

Nunca corras un comando de git (ni `gh`) que cambie el estado del repositorio
sin que el usuario haya dicho explícitamente que sí, **para esa acción
puntual**, en este intercambio. En su lugar: sugerí la acción y el comando
exacto, y esperá la confirmación antes de ejecutarlo.

Esto es más estricto que el comportamiento por default de crear una rama
automáticamente al estar parado en la rama principal antes de editar: en
este repo, ni siquiera eso corre sin preguntar primero.

## Por qué

El usuario prefiere mantener control total sobre qué entra al historial de
este repo y cuándo. Una vez que un commit, un push o un merge existen, no
son triviales de deshacer con prolijidad (más si otros ya los vieron, o si
hay un PR de por medio) — y aunque técnicamente casi todo se puede revertir,
el punto es que esas decisiones las toma el usuario, no Claude por su
cuenta. Aplica incluso a acciones que parecen inocuas, como crear una rama o
comitear un WIP: son cambios de estado que el usuario no pidió en ese
momento exacto, y puede tener una razón (otro esquema de ramas en mente,
querer revisar el diff primero, etc.) que Claude no ve.

## Comandos que requieren autorización explícita antes de correr

- Crear rama: `git checkout -b`, `git switch -c`, `git branch <nombre>` (+checkout)
- Cambiar de rama: `git checkout <rama>`, `git switch <rama>`
- Commit: `git commit`, `git commit --amend`
- Push: `git push`, incluido `--force`/`-f`
- Merge: `git merge`
- Rebase: `git rebase`
- Reset que mueve HEAD o descarta cambios: `git reset --hard`, `git reset` sobre commits ya hechos
- Tag: `git tag`
- Borrar ramas o tags: `git branch -d`/`-D`, `git tag -d`, `git push --delete`
- Stash destructivo: `git stash pop`, `git stash drop` (`git stash push`/`save` sí es libre: no descarta nada, queda reversible)
- Cherry-pick, filter-branch, o cualquier reescritura de historia
- Abrir un PR (`gh pr create`) — es una acción hacia afuera, la ve el resto del equipo

## Lo que sí podés correr libremente

Nada de esto cambia el estado del repo, así que no hace falta preguntar:
`git status`, `git diff`, `git log`, `git show`, `git branch --list`/`-a`,
`git stash list`, `git blame`, `git fetch` (solo actualiza refs remotas, no
toca ramas locales ni el working tree).

## Cómo pedirla

1. Decí en una frase qué harías y por qué.
2. Mostrá el comando exacto que correrías.
3. Esperá una confirmación explícita e inequívoca ("sí", "dale", "hacelo",
   "adelante"...) antes de ejecutar. Si el usuario sigue hablando de otra
   cosa, o queda en silencio, no es un sí.

Esto vale incluso cuando el propio pedido del usuario ya nombra la acción de
git directamente (p. ej. "commiteá esto", "creá la rama para X"). El rol de
Claude en esta skill es siempre sugerir — nunca el de decidir que un pedido
explícito ya es luz verde para ejecutar. Mostrá el comando igual y esperá
la confirmación separada antes de correrlo.

Una autorización no se generaliza a otra acción distinta ni a más adelante
en la conversación: que el usuario haya dicho "commiteá esto" no autoriza
después un push; que haya dicho "creá la rama" no autoriza el commit que
sigue. Cada acción mutante pide su propio sí — incluso si ya hiciste una
antes en el mismo turno o en turnos anteriores de esta charla.

## Ejemplo

> Usuario: "arreglá el bug de X"
> _(Claude edita el código)_
> Claude: "Ya arreglé el bug. ¿Querés que lo commitee? Sugiero: `git commit -am "fix: ..."`."
> Usuario: "sí, dale"
> _(ahora sí, Claude corre el commit)_
