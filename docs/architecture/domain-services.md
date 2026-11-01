# Servicios de dominio

`api/services/appointments.py` comparte validación de horario, actualización parcial y transiciones entre API y HTML. `P` pendiente permite `C` completada o `A` anulada; repetir estado es idempotente, y cambiar entre terminales o volver a pendiente devuelve conflicto. La creación conserva los estados aceptados previamente. **CLINICAL/BUSINESS DECISION REQUIRED:** confirmar reapertura, corrección de cancelación y fechas pasadas. No se interpreta coincidencia de horario como prohibida.

`api/services/clinical_records.py` serializa por paciente y crea revisiones de antecedentes y odontograma. `ConcurrentModification` y `ClinicalDataConflict` son 409; entrada inválida es 400 y autorización sigue 404. HTML/API comparten el mismo servicio. Django ORM sigue siendo persistencia. La validación de odontograma se centraliza en `api/services/odontogram.py`.

Los AuditEvent de antecedentes y odontograma se escriben en la misma transacción exterior mediante middleware; citas ahora tienen eventos en ambas superficies. Otras operaciones (estudios, consentimiento, archivos, IA y consulta) aún no comparten todos sus invariantes ni transacciones. ARCH-001 y SEC-010 permanecen **PARTIALLY RESOLVED**; no asumir auditoría completa.
