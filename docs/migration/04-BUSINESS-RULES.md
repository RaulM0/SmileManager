# Reglas de negocio

1. La unidad de aislamiento es el médico autenticado. Pacientes y todo dato clínico/cita deben pertenecerle directa o transitivamente.
2. Email y teléfono de Paciente son únicos por médico. Los datos identificativos se normalizan a mayúsculas en los flujos legacy.
3. “Eliminar paciente” significa estado `I`; eliminar imagen sí borra el registro.
4. Citas no aceptan fechas pasadas ni horas fuera de 08:00–20:00.
5. Consulta se crea con fecha actual y genera una receta imprimible.
6. Una imagen clínica exige consulta del mismo paciente y médico.
7. Antecedentes y odontograma se comportan como recursos únicos por paciente/médico aunque el esquema no impone unicidad.
8. El primer estudio comparativo exige cinco imágenes “antes”; las cuatro “después” son opcionales.
9. El consentimiento es inmutable en UI después de aceptar; INE máximo 5 MB y extensión controlada.
10. El análisis YOLO es síncrono, preserva el original y guarda un nuevo resultado en storage.
11. Exportaciones conservan nombres de archivo, hojas y columnas legacy.
12. Email de contacto usa siempre el email guardado del paciente y produce versiones texto/HTML.

Los defectos observados están en `12-RISKS-AND-BLOCKERS.md`; su corrección no se mezcla silenciosamente con la migración.
