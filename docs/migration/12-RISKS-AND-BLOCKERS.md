# Riesgos y bloqueos

## PRE_EXISTING_BUG

- **BUG-001:** editar paciente no valida email duplicado antes de guardar; puede terminar en `IntegrityError`.
- **BUG-002:** formato inválido al editar cita redirige a alta usando el id de cita como id de paciente.
- **BUG-003:** completar/cancelar cita y logout mutan estado mediante GET; riesgo CSRF.
- **BUG-004:** recordatorios filtran un `DateField` con datetimes e ignoran `hora`; ventana de 24 h no es fiable.
- **BUG-005:** `get_or_create` de antecedentes durante GET crea datos como efecto de lectura.
- **BUG-006:** modelos no imponen unicidad para antecedentes, odontograma, estudio o consentimiento aunque vistas los tratan como únicos.
- **BUG-007:** `enviar_mensaje` redirige a sí mismo sin paciente si faltan campos y su GET usa un template selector distinto al formulario.
- **BUG-008:** detecciones YOLO no se persisten; recargar vuelve a inferir y genera otra imagen resultado.

Se preservará el resultado observable durante paridad o se propondrá por separado una corrección con pruebas.

## REQUIRES_REVIEW

- `Consentimiento.pdf_generado` existe pero no tiene consumidor encontrado.
- `DiagnosticosIA.models`, `Home.models`, `Sesiones.models` están vacíos y se conservan.
- Existen numerosos archivos media históricos y bytecode versionado; no se eliminan durante migración.
- Confirmar programación externa del comando `enviar_recordatorios` en producción.
- Las credenciales SMTP/S3 y el scheduler externo deben validarse al desplegar, porque no pertenecen al repositorio.

## Riesgos técnicos

- PyTorch aumenta tiempos de arranque y uso de memoria.
- S3 y SMTP requieren pruebas separadas con credenciales de entorno.
- El bundle React contiene Bootstrap y OpenSeadragon y supera 500 kB minificado; es una advertencia de rendimiento, no una pérdida funcional.
- El legacy original no aportaba pruebas efectivas; la nueva suite de caracterización/API/E2E es ahora la protección de regresión.

No hay bloqueos activos ni cambios de comportamiento requeridos.
