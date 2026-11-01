# Plan incremental

1. **Fase 0 — Baseline:** auditoría, documentos, Docker, DRF/Vite, pruebas base, convivencia `/app/` + legacy.
2. **Fase 1 — Sesión/layout/dashboard:** FUNC-001–005. Habilita todas las páginas protegidas.
3. **Fase 2 — Pacientes:** FUNC-006–013; servicio/serializers, CRUD y selector.
4. **Fase 3 — Consultas y expediente:** FUNC-014–017.
5. **Fase 4 — Imágenes:** FUNC-018–022; multipart y storage.
6. **Fase 5 — Citas:** FUNC-032–038; comparte selector de pacientes.
7. **Fase 6 — Odontograma:** FUNC-023; portar y probar el estado JS complejo.
8. **Fase 7 — Estudios/consentimiento:** FUNC-024–027; uploads y PDF.
9. **Fase 8 — Exportación/email:** FUNC-028–031 y FUNC-042.
10. **Fase 9 — IA:** FUNC-039–040; inferencia, errores y visualización.
11. **Fase 10 — Paridad final:** E2E, visual, seguridad, producción, decidir retiro legacy; FUNC-041 permanece.

Cada fase exige API + React + pruebas + actualización documental antes de `VERIFIED`.

## Ejecución

- Fases 0–9: implementadas el 2026-10-23.
- Fase 10: completada el 2026-10-23 con pruebas backend, frontend, E2E clínica, inferencia real y navegación responsive.
