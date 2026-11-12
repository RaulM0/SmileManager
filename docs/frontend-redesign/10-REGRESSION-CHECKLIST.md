# Regression checklist

No hay pantallas marcadas VERIFIED todavía. Marcar únicamente con comprobación real.

## Evidencia runtime disponible (24-10-2026)

El flujo E2E cubrió las acciones críticas descritas en `12-FINAL-VALIDATION.md`, cancelación de cita, recuperación tras 503, dashboard y drawer. Se generaron/inspeccionaron capturas a 1440, 768 y 390 px; además, no-overflow se comprobó en rutas clave a 768/390 px. El E2E compilado comprueba entrada de foco al primer enlace del drawer, wrap con Shift+Tab/Tab, cierre con Escape y retorno del foco al toggle. Los grupos permanecen sin marcar como VERIFIED hasta completar contraste/teclado en todos los controles y el recorrido visual de cada ruta.

En los formularios de paciente, cita, antecedentes, consulta, correo, imagen clínica, estudio comparativo y consentimiento se forzaron errores API por campo y se comprobó `aria-invalid`, asociación al texto de error, alerta general cuando aplica, corrección del campo y reintento. El flujo también ejecuta submit exitoso, valida campos requeridos y comprueba secuencias de teclado representativas. Formulario de login, filtros/búsquedas y selectores se recorren dentro de los flujos; esto no equivale a verificación manual de todos los campos, ayudas y lectores de pantalla.

El viewer de diagnósticos fue inspeccionado en Chromium: los PNG de controles ahora se sirven desde el build local y Playwright comprueba que carguen. La primera captura usó 1×1 px; el E2E actual analiza una radiografía de 612×323 px y verifica original, resultado, detecciones y zoom por teclado.

La forma compartida de `PatientListPage` se migró a Tailwind; E2E vuelve a comprobar el resultado de búsqueda, el enlace Ver con nombre accesible, la región de paginación y la tabla desplazable a 390 px sin overflow del documento. No se marca toda la pantalla VERIFIED: loading/error/empty/paginación de múltiples páginas requieren revisión adicional.

`AppointmentsPage` conserva y verifica query params `status/search`, estados activos `aria-pressed`, tabla, `Ver/Editar`, `Completar` solo para pendientes y `Cancelar`; E2E ejecuta completar/cancelar y carga el listado filtrado por `status=A&search=…`. En móvil, la agenda por fecha es la vista predeterminada y el botón Mes recupera la cuadrícula de 42 días con scroll local; E2E comprueba ambas selecciones, el aviso de scroll y ausencia de overflow del documento. Capturas desktop/móvil inspeccionadas. Falta el pase manual completo de errores, permisos y teclado antes de marcar VERIFIED.

`ClinicalImageListPage` conserva filtros reactivos `date/consultation_id`, descarga directa y eliminación con confirmación; E2E comprueba ambos filtros, descarga `.png`, acepta confirmación y valida estado vacío tras DELETE. `DiagnosticsPage` conserva `patient/type/date` en query params, aplica filtro, muestra los datos retornados y abre el análisis pendiente. E2E valida parámetros/resultados, recuperación tras un 503, estados, enlace, responsive sin overflow y capturas desktop/móvil. No se marca todo el grupo VERIFIED hasta revisar estados de error/empty en cada ruta de forma manual.

`ConsultationHistoryPage` conserva fecha, motivo, diagnóstico y enlace a receta en una línea temporal. E2E comprueba el registro y destino, así como el ancho a 390/768 px. Capturas 1280/390 revisadas. `AppointmentDetailPage` conserva GET, edición y datos; ahora etiqueta el estado con texto e indicador. `ClinicalRecordPage` mantiene sus siete rutas clínicas. Falta recorrido manual de error/empty/teclado/roles para marcar VERIFIED.

`MedicalHistoryPage` y `ConsultationCreatePage` conservan campos, payload, validaciones, errores asociados, bloqueo de doble envío y reintentos después de 400. E2E comprueba cambio Sí/No con flechas del teclado, visibilidad de las cuatro notas médicas, orden de Tab en consulta y navegación a receta. Capturas 1280/390 revisadas; la primera captura desktop de antecedentes omitió tres notas por la posición de scroll al tomar la imagen, y una segunda captura desde el inicio mostró las cuatro. Falta prueba de lector de pantalla y combinaciones de permisos.

Carga de imagen, consentimiento, correo y estudio comparativo conservan selección, archivos, campos required, aceptación condicional, errores 400, reintentos, payloads, rutas de éxito y descarga de PDF. E2E completo 3/3 y capturas desktop/móvil revisadas. El estudio mostró una alerta roja antes de guardar por claves de error limpias; ahora se comprueban solo mensajes activos y E2E confirma que no hay alerta inicial, además del error 400 y el reintento. No marcar VERIFIED hasta los estados y roles restantes.

Hub, alta, edición, detalle y selector de pacientes conservan seis rutas, campos, autocomplete, desactivación con confirmación, navegación y validación de formulario. E2E 3/3 añade error 503 y reintento para GET de detalle y edición, y fallo 503 en desactivación con alerta visible seguido de intento exitoso. Capturas del formulario y detalle desktop/móvil revisadas. El aislamiento entre cuentas está probado; quedan paginación múltiple y accesibilidad completa.

El odontograma conserva 52 piezas y cinco superficies por pieza, seis estados, GET/PUT, resumen derivado y confirmación de limpieza. E2E clínico 1/1 tras actualizar la aserción del resumen comprueba Caries=1, guardado, superficie de 24×24 px y scroll horizontal de cuadrante en 390 px; captura móvil muestra un cuadrante por fila y resumen en dos columnas. Falta probar específicamente error de PUT, limpieza completa, reentrada, lector de pantalla y contraste de todas las muestras antes de VERIFIED.

El resultado diagnóstico mantiene autoanálisis, repetición manual, estado de procesamiento, visor OpenSeadragon original/analizado y tabla de clase/confianza/coordenadas. E2E completo 3/3 comprueba dos viewers, recursos PNG cargados, ausencia de alerta tras éxito y responsive 390/768; capturas desktop/móvil con radiografía real revisadas. El nuevo retry de GET de imagen y errores de POST deliberados requieren pruebas específicas; el zoom por teclado y anotaciones sí se observaron con la radiografía del repositorio.

Login/administración/receta: E2E 3/3 conserva redirect de autenticación, mostrar contraseña, impresión (botón oculto en media print), tres descargas XLSX y aviso de privacidad. Capturas 1280/390 revisadas. Una captura móvil reveló que los enlaces XLSX caían en la columna del icono; la grid se corrigió y la captura nueva muestra cada enlace alineado bajo su descripción. No se marca VERIFIED hasta revisar permisos, lector de pantalla y rutas/estados restantes.

Retirada del CSS Bootstrap: después de migrar utilidades residuales y borrar el import/dependencia, lint/unit/build/E2E 3/3 pasan; CSS de producción 127.65 kB. Inicio y formulario de cita móvil, login, exportaciones y receta se inspeccionaron con el build nuevo. Sigue pendiente un pase visual completo de todas las rutas y tamaños.

Barrido de rutas: 29 rutas privadas existentes se abrieron en Chromium con fixture real, cada una a 1280/768/390 px; se comprobó encabezado h1, ausencia de overflow de documento y botones visibles con nombre. Se probaron además 503 y reintento de `dashboard/`, GET de edición de cita y PUT de odontograma; la cancelación de «Limpiar todo» deja Caries=1, y búsqueda sin coincidencias muestra su estado vacío. Tras logout, ruta protegida con `?q=` devuelve a login y, al autenticar, vuelve a la misma ruta/query. La prueba descubrió y permitió corregir una redirección prematura hacia Inicio. E2E 3/3 y build/lint pasan tras la corrección. Pendiente: lector de pantalla real y estados degradados de cada ruta.

Visor: ahora el E2E sube la radiografía de 612×323 px existente en `media/imagenes_clinicas`, ejecuta el modelo y comprueba original/analizada con detecciones. Al intentar enfocar el control «Acercar», la primera corrida falló porque el control de la librería carecía de `tabIndex`; se añadió junto a rol/nombre español y soporte de Espacio. La siguiente corrida E2E pasó 3/3 y la captura móvil muestra zoom ejecutado con teclado. Hay aviso de scroll en tabla de detecciones; se inspeccionaron capturas 1280/390. Pendiente lector de pantalla real y contraste de etiquetas de detección sobre imágenes variadas.

Patient 360: la navegación local mantiene ID y nombre real del paciente en subsecciones; la prueba comprueba nombre tras abrir expediente y actualización después de editar. Una segunda cuenta recibe solo el ID en la barra y error en el detalle ajeno, sin fuga de nombre. Captura móvil 390 px inspeccionada y E2E 3/3.

Estado parcial de imágenes: E2E fuerza 503 solo en consultas, comprueba que la imagen siga visible, muestra aviso específico y «Reintentar consultas» repuebla el selector. Captura 390 px revisada. En resultado diagnóstico se forzó 503 en GET y POST de análisis manual; ambos reintentos terminaron sin alerta. Los encabezados tras retirar etiquetas redundantes conservaron h1, acciones y contexto ID; barrido de 29 rutas a 1280/768/390 px y E2E 3/3 pasaron.

Accesibilidad automatizada: en cada una de las 29 rutas privadas, Playwright comprueba que botones, enlaces e inputs/selects/textarea visibles tengan nombre o label. Todos pasaron. Los colores textuales de success/warning/info/activo/inactivo superan 4.5:1 según cálculo de tokens (6.13/5.95/7.52/6.72/6.41). Pendiente: lector de pantalla humano, foco completo en todos los flujos y contraste de anotaciones sobre radiografías variadas.

Listas con datos previos: al fallar un GET de citas tras cambiar el estado, el aviso aclara que se ven citas de la última carga y «Reintentar» recupera el filtro sin perder la URL. Un DELETE fallido de imagen muestra error de la acción; no lo presenta como error de listado ni repite el borrado con «Reintentar listado». E2E completo 3/3 tras añadir esta cobertura. Pacientes, imágenes y diagnósticos tienen el mismo aviso de datos previos cuando falla una nueva carga; las respuestas anteriores a un cambio de filtro se descartan. Queda revisión manual de todas las combinaciones de filtros y fallos.

Vitest agregó una prueba de carrera de búsqueda de pacientes: el GET del filtro nuevo responde primero y el GET antiguo después; la tabla mantiene el resultado nuevo. Suite unitaria 3/3. Agenda e imágenes usan identificador de carga para descartar respuestas antiguas; diagnóstico y pacientes invalidan sus efectos anteriores.

Contexto al cambiar ID: Vitest simula paciente 1 visible y navegación directa al paciente 2 sin permiso. Durante la nueva carga y tras el error, el nombre del paciente 1 no aparece. Detalle/edición de pacientes y citas descartan GET de IDs anteriores; los formularios de edición se remontan con el nuevo ID. Suite unitaria 4/4, E2E 3/3. Queda comprobación manual con varias cuentas y navegación entre registros reales.

## Global shell / UI-001–003

- [ ] Rutas funcionan
- [ ] Datos/sesión cargan
- [ ] API correcta
- [ ] Acciones y logout funcionan
- [ ] Formularios/validaciones funcionan
- [ ] Permisos/protección funcionan
- [ ] Loading/error/empty funcionan
- [ ] Navegación y redirect return funcionan
- [ ] Desktop / tablet / mobile
- [ ] Teclado/focus
- [ ] Paridad funcional
- [ ] Visual consistente

## Inicio UI-004 · Agenda UI-027–028 · Citas UI-029–031

- [ ] Ruta/datos/API
- [ ] Query params/search/status/calendar navigation
- [ ] Alta/edición/detalle/complete/cancel conservados
- [ ] Loading/empty/error
- [ ] Desktop / tablet / mobile / teclado
- [ ] Paridad funcional / visual consistente

## Pacientes UI-005–011

- [ ] Hub/rutas/search/pagination y URL params
- [ ] Alta/edición/campos/validación/API
- [ ] Detalle/desactivar confirmación/redirect
- [ ] Selector/autocomplete/contacto correo
- [ ] Loading/empty/error/success
- [ ] Responsive / teclado / paridad / consistencia

## Expediente y clínica UI-012–018, UI-023–024

- [ ] Navegación conserva todas las subsecciones
- [ ] Paciente y contexto visibles
- [ ] Antecedentes: 24 booleanos y 4 campos texto
- [ ] Consulta, historial, receta e impresión
- [ ] Odontograma FDI, 6 estados, 5 superficies, resumen/guardar/limpiar-confirmar
- [ ] Estudio comparativo: metadata, 9 campos archivo, required condicional y PDF
- [ ] Consentimiento: términos, aceptación, archivo, errores, documento existente
- [ ] API/payload/loading/error/success
- [ ] Responsive/teclado/paridad/consistencia

## Imágenes y diagnósticos UI-019–026, UI-034

- [ ] Hub/upload/filtros/history/search/download/delete confirm
- [ ] FormData y errores de archivo
- [ ] Diagnóstico filtros/análisis/estado de ejecución/error
- [ ] OpenSeadragon
- [ ] Responsive/teclado/paridad/consistencia

## Administración UI-032–033

- [ ] 3 descargas XLSX con nombres correctos
- [ ] Link/contenido de privacidad
- [ ] Responsive/teclado/consistencia
