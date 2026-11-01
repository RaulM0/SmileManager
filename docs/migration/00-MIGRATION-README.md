# Migración Django Templates → React + DRF

Este directorio es la memoria técnica y fuente de verdad de la migración. El objetivo es conservar la aplicación legacy operativa mientras cada capacidad se migra y verifica verticalmente.

## Reanudación obligatoria

Antes de continuar, leer en orden: `02-FUNCTIONAL-INVENTORY.md`, `08-MIGRATION-PLAN.md`, `09-MIGRATION-STATUS.md`, `10-TESTING-AND-PARITY.md`, `11-DECISIONS.md` y `12-RISKS-AND-BLOCKERS.md`. Después revisar `git status` y ejecutar las validaciones anotadas en el status.

## Convenciones

- Los identificadores `FUNC-XXX` son permanentes.
- El legacy no se elimina hasta que la capacidad correspondiente esté `VERIFIED`.
- Los endpoints nuevos viven bajo `/api/v1/`.
- Los errores preexistentes se registran; no se corrigen silenciosamente.
- Estados: `NOT_STARTED`, `ANALYZED`, `BACKEND_MIGRATED`, `FRONTEND_MIGRATED`, `TESTED`, `VERIFIED`, `BLOCKED`.

Estado final: migración completa, 42/42 funcionalidades `VERIFIED`. Última actualización: 2026-10-23.
