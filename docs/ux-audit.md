# Auditoría de usabilidad del frontend clínico

## Alcance y método

Evaluación heurística experta del React actual, con perspectiva de recepción, asistencia y odontología. Se revisaron rutas, navegación, servicios, formularios, estados, tablas y acciones, y se recorrió la aplicación en Chromium con Django y una base y archivos de prueba aislados. No se utilizaron datos de pacientes reales ni se modificó la aplicación. Los perfiles y escenarios son hipótesis de trabajo, no resultados de entrevistas.

En el recorrido de esta auditoría se inició sesión, creó un paciente, se editó sin guardar y se abandonó el formulario, se creó y canceló una cita y se visitaron **27 rutas privadas** con un expediente de prueba. Se inspeccionaron capturas del detalle del paciente a 1280 px y de la agenda y expediente a 390 px. En estas dos últimas pantallas el ancho del documento fue 390 px. Se contrastaron las demás pantallas con su implementación y con el registro de pruebas previas en `frontend/e2e/core-flow.spec.js` y `docs/frontend-redesign/12-FINAL-VALIDATION.md`.

**Límites de evidencia:** esta evaluación no incluye sesiones con recepcionistas o dentistas, tiempos de tarea, mediciones de error humano, lector de pantalla real, contrastes completos ni todos los estados/roles/navegadores. La visita a rutas comprueba renderización básica, no que todas sus acciones hayan sido probadas en esta corrida. La receta y el resultado diagnóstico requieren registros adicionales y se evaluaron por código y evidencia E2E previa. No se certifica conformidad WCAG ni seguridad clínica. Los hallazgos con consecuencias clínicas requieren validación por responsables clínicos.

**Fuentes de evaluación:** [10 heurísticas de Nielsen](https://www.nngroup.com/articles/ten-usability-heuristics/); [WCAG 2.2](https://www.w3.org/TR/WCAG22/), especialmente foco, etiquetas, errores y tamaño de objetivos. El mínimo de 24 × 24 CSS px de WCAG 2.2 AA tiene excepciones; no se declara incumplimiento sin medirlas.

## Resumen ejecutivo

La interfaz ofrece una base reconocible para trabajo clínico: menú principal breve, contexto persistente del paciente, agenda con filtros, formularios etiquetados, feedback de acciones y un odontograma interactivo. La prueba aislada permitió completar el alta y la cita, y los anchos móviles observados no desbordaron el documento.

Todavía no recomendaría afirmar que puede utilizarse con seguridad y eficiencia durante una jornada sin evaluación clínica adicional. Hay dos riesgos prioritarios: un antecedente nuevo se crea con respuestas negativas por defecto y un odontograma sin registro se visualiza como sano. Además, la navegación descarta cambios sin aviso, se cancela una cita inmediatamente y varias tareas frecuentes obligan a repetir la búsqueda del paciente. El diseño es coherente, aunque algunos hubs y resúmenes repiten información en vez de acercar tareas o contexto.

**Severidad** estima la consecuencia posible, no frecuencia medida: CRÍTICO = posible error clínico grave o tarea bloqueada; ALTO = pérdida de información o fricción considerable; MEDIO = impacto de claridad/eficiencia; BAJO = refinamiento. **Evidencia:** R = recorrido real aislado; C = lectura de código; P = prueba previa documentada; H = hipótesis que requiere validación. Las recomendaciones son propuestas sujetas a aprobación; varias cambian comportamiento o contratos y se identifican como tales.

## Mapa de producto y tareas

La SPA tiene 30 rutas de pantalla declaradas, incluyendo login y privacidad, con un fallback general. No se identificaron módulos React de pagos, inventario, tratamientos estructurados o permisos diferenciados; el tratamiento existe como texto de consulta/receta. Los perfiles de recepción/asistencia/odontología son escenarios, no roles implementados. La navegación principal ofrece Inicio, Citas, Pacientes, Diagnósticos y Exportaciones; el contexto de paciente añade Resumen, Expediente, Antecedentes, Consultas, Odontograma, Imágenes, Progreso y Consentimiento. `PatientSelector`, `PatientForm`, `AppointmentForm`, `PatientWorkspaceNav`, `useResource`, toasts, tablas y visor protegido son piezas reutilizadas.

| Perfil supuesto | Tarea y módulos disponibles | Riesgo contextual |
|---|---|---|
| Recepción | alta/búsqueda, citas, contacto y exportaciones | nombres repetidos y cambios de estado accidentales |
| Asistencia | seleccionar expediente, imágenes, consentimiento y progreso | volver a seleccionar paciente y campos sin orientación |
| Odontología | antecedentes, consulta/receta, odontograma, imágenes/IA | confundir dato no registrado con negativo o sano |
| Administración | listados y Excel | no se observan roles distintos; verificar permisos en operación real |

## Heurísticas de Nielsen

| # | Heurística | Evaluación y evidencias principales |
|---|---|---|
| 1 | Visibilidad del estado | Toasts y estados de carga/reintento existen; borradores sin indicador y descargas sin éxito visible: UX-03, UX-17. |
| 2 | Correspondencia con el mundo real | Texto clínico en español; «Anulada/Cancelada», «Resumen» y aceptación del consentimiento pueden confundir: UX-11, UX-14, UX-19. |
| 3 | Control y libertad | Navegación por secciones y teclado; perder borradores o cancelar sin revisión limita recuperación: UX-03, UX-04. |
| 4 | Consistencia y estándares | Componentes y estados compartidos; búsqueda dividida, nombres de acciones y confirmaciones difieren: UX-07, UX-11, UX-12. |
| 5 | Prevención de errores | Validación de campos y bloqueo durante envío; antecedentes y odontograma suponen estados clínicos: UX-01, UX-02. |
| 6 | Reconocimiento antes que recuerdo | Contexto Patient 360 positivo; cita y receta no conectan de vuelta con paciente; selector no desambigua homónimos: UX-06, UX-08. |
| 7 | Flexibilidad y eficiencia | Filtros, búsqueda y agenda móvil; hubs y reselección añaden pasos: UX-07, UX-09, UX-10. |
| 8 | Diseño estético y minimalista | Superficies sobrias y jerarquía operativa; detalle de paciente repite datos y el resumen clínico es un menú: UX-10, UX-16. |
| 9 | Recuperación de errores | Hay reintentos y errores por campo; algunos vacíos y fallos no indican el próximo paso: UX-13, UX-15, UX-18. |
| 10 | Ayuda y documentación | Existen algunos textos de ayuda; faltan guía contextual y explicaciones de acciones/formatos: UX-14, UX-18, UX-20. |

## Hallazgos priorizados

### UX-01 — CRÍTICO · Antecedentes nuevos como respuestas negativas

- **Pantalla/evidencia:** Antecedentes `MedicalHistoryPage.tsx`; `MedicalHistoryView.get_object` usa `get_or_create` al leer y `AntescedentesMedicos` inicializa booleanos en `False`. El formulario marca «No» si el valor es falso. C; la ruta fue visitada en R.
- **Escenario e impacto:** al abrir por primera vez un expediente, una alergia o condición no preguntada puede presentarse como ausencia confirmada. La consulta GET crea el registro con esos valores, incluso antes de guardar. Esto es un riesgo de interpretación clínica, no evidencia de daño ocurrido.
- **Recomendación:** validar con clínicos un estado explícito «Sin preguntar / Sí / No», conservar y distinguir registros históricos sin inventar respuestas, mostrar fecha/estado de revisión y evitar que una lectura cree una valoración confirmada. Requiere diseño de datos, migración y cambio de contrato; no puede resolverse solo con CSS.
- **Resultado esperado:** «desconocido» nunca se interpreta como «No»; el profesional identifica qué preguntas faltan. Heurísticas 2, 5 y 6.

### UX-02 — CRÍTICO · Odontograma vacío representado como sano

- **Pantalla/evidencia:** `OdontogramView.get` devuelve denticiones vacías cuando no existe registro; `fullDentition` en `OdontogramPage.tsx` rellena cada superficie con `sano` y el resumen las cuenta. C; captura previa y ruta R.
- **Escenario e impacto:** un odontólogo abre un expediente sin exploración y ve 52 piezas sanas; al guardar puede registrar ese estado sin una valoración completa. Es riesgo potencial que requiere confirmar con el flujo clínico.
- **Recomendación:** distinguir «sin valoración» de «sano», indicar cuándo no hay odontograma registrado y no persistir superficies no examinadas como sanas; acordar representación y compatibilidad histórica con clínicos.
- **Resultado esperado:** el diagrama refleja lo documentado y las ausencias de datos son visibles. Heurísticas 1, 2 y 5.

### UX-03 — ALTO · Se pierden cambios al navegar

- **Pantalla/evidencia:** edición de paciente y formularios con estado local; `AppLayout` remonta contenido al cambiar ruta. En R se modificó el nombre, se pulsó «Resumen» y volvió el valor anterior sin diálogo.
- **Escenario e impacto:** una interrupción durante antecedentes, odontograma o datos de contacto puede hacer perder trabajo y obligar a recapturar. El recorrido solo confirmó edición de paciente; los demás formularios deben probarse individualmente.
- **Recomendación:** detectar cambios pendientes y ofrecer «Seguir editando / Descartar» en navegación interna; preservar el borrador donde sea seguro y avisar antes de recarga/cierre según capacidad del navegador. No bloquear si no hay cambios.
- **Resultado esperado:** la salida accidental no elimina silenciosamente trabajo. Heurísticas 3, 5 y 9.

### UX-04 — ALTO · Cancelación/completado de cita inmediatos

- **Pantalla/evidencia:** botones de fila en `AppointmentsPage.tsx` llaman mutaciones directamente; R confirmó que «Cancelar» cambió el estado sin diálogo. Completado tiene el mismo patrón por código.
- **Escenario e impacto:** un clic equivocado cambia la agenda del día. Existe edición de estado, pero no una recuperación directa y explícita junto al aviso.
- **Recomendación:** confirmar la cancelación con paciente y fecha, o proporcionar deshacer fiable si las reglas lo permiten; evaluar un tratamiento equivalente para completar. Mantener acciones y endpoints hasta acordar la transición.
- **Resultado esperado:** menos cambios accidentales y recuperación entendible. Heurísticas 3 y 5.

### UX-05 — ALTO · Análisis de IA se ejecuta al abrir resultados

- **Pantalla/evidencia:** `DiagnosticResultPage.tsx` ejecuta `analyze()` al montar; `DiagnosticosIA/services.py` guarda el resultado. C; análisis real previamente cubierto por E2E.
- **Escenario e impacto:** «Ver / repetir análisis» mezcla consulta y acción; al abrir una imagen ya analizada se vuelve a procesar y a guardar un resultado. El usuario puede esperar solo revisar el existente.
- **Recomendación:** proponer vista de resultado existente y una acción explícita «Analizar nuevamente», con estado de procesamiento y aclaración del efecto; decidir con clínicos conservación/versionado del resultado. Cambia el comportamiento actual y requiere aprobación.
- **Resultado esperado:** se diferencia consultar de volver a ejecutar el modelo. Heurísticas 2, 3 y 5.

### UX-06 — ALTO · Selector sin información para distinguir pacientes

- **Pantalla/evidencia:** `PatientSelector.tsx` muestra solo `patient.text`; autocomplete en `api/views.py` busca únicamente `nombre`, devuelve hasta diez y ofrece nombre completo sin ID/contacto. C.
- **Escenario e impacto:** recepción recibe dos pacientes con nombres iguales o busca por apellido/teléfono en nueva cita; puede escoger uno incorrecto o creer que no existe.
- **Recomendación:** permitir búsqueda por nombre completo, apellido e identificador/contacto disponibles, presentar datos mínimos para desambiguar y conservar permisos; definir límites y privacidad con clínica. Requiere ampliar contrato/API.
- **Resultado esperado:** selección confiable sin consultar otra pantalla. Heurísticas 5 y 6.

### UX-07 — MEDIO · Búsqueda de pacientes separada del listado

- **Pantalla/evidencia:** hub `/patients` ofrece «Todos los pacientes» y «Buscar pacientes»; solo `/patients/search` muestra buscador (`PatientListPage.tsx`). C/R.
- **Escenario e impacto:** desde «Todos» un recepcionista no puede filtrar y debe regresar y abrir otra opción.
- **Recomendación:** mostrar la misma búsqueda en ambos accesos, conservar URLs y parámetros existentes, y mantener alta y paginación.
- **Resultado esperado:** una entrada menos en tareas frecuentes. Heurísticas 4 y 7.

### UX-08 — ALTO · Cita y receta sin regreso contextual al paciente

- **Pantalla/evidencia:** `AppointmentDetailPage.tsx` muestra nombre como texto; R contó cero enlaces al paciente. `PrescriptionPage.tsx` muestra paciente, pero la ruta `/consultations/:id/prescription` queda fuera de `PatientWorkspaceNav`. C.
- **Escenario e impacto:** desde una cita o receta el profesional debe volver al módulo y buscar de nuevo para abrir expediente, aumentando cambio de contexto.
- **Recomendación:** enlazar el paciente desde cita y receta con su ID autorizado; añadir regreso contextual a historial/expediente y conservar la URL de origen cuando proceda.
- **Resultado esperado:** el usuario pasa de cita a expediente sin memorizar nombre ni perder referencia. Heurísticas 3, 6 y 7.

### UX-09 — MEDIO · Nueva cita obliga a reseleccionar paciente

- **Pantalla/evidencia:** `AppointmentCreatePage.tsx` siempre inicia sin paciente y pide búsqueda; detalle de paciente no ofrece acción de cita contextual. C.
- **Escenario e impacto:** tras registrar o consultar a un paciente, recepción abre Citas → Nueva cita → vuelve a buscarlo.
- **Recomendación:** añadir acceso «Nueva cita» desde el expediente que lleve el ID por contexto explícito, validado en servidor; mantener la selección manual como alternativa y no crear datos de prueba en producción.
- **Resultado esperado:** menos recaptura y menor riesgo de seleccionar homónimo. Heurísticas 6 y 7.

### UX-10 — MEDIO · Inicio y resumen clínico informan pero requieren navegación extra

- **Pantalla/evidencia:** tablas de `DashboardPage.tsx` presentan citas sin enlaces de fila; `ClinicalRecordPage.tsx` es un menú de siete destinos. R/C.
- **Escenario e impacto:** para actuar sobre una cita visible en Inicio hay que abrir agenda y localizarla; en el expediente no se ve actividad clínica resumida.
- **Recomendación:** enlazar fecha/paciente a la cita y, donde la API ya lo soporte, mostrar una sección de últimas consultas o próxima cita con carga/error independientes. No inventar estados ni métricas.
- **Resultado esperado:** pasar de la información a la acción en contexto. Heurísticas 1, 6 y 7.

### UX-11 — MEDIO · Vocabulario de citas inconsistente

- **Pantalla/evidencia:** `AppointmentForm.tsx` usa «Anulada»; filtros y etiquetas de `AppointmentsPage.tsx` dicen «Cancelada». C.
- **Escenario e impacto:** al editar, el usuario puede interpretar que son estados diferentes.
- **Recomendación:** acordar un término clínico y usarlo en formulario, filtros, mensajes y detalle, conservando el código `A`.
- **Resultado esperado:** un mismo estado se reconoce igual en todas las pantallas. Heurísticas 2 y 4.

### UX-12 — MEDIO · Acciones repetidas «Acceder» y nombres ambiguos

- **Pantalla/evidencia:** `PatientsHubPage.tsx` usa seis enlaces independientes con texto «Acceder»; las filas clínicas usan el título como enlace. C/R.
- **Escenario e impacto:** con lector de pantalla o al recorrer solo enlaces, seis acciones tienen el mismo nombre; visualmente hay que asociarlas con su fila.
- **Recomendación:** nombrar enlaces por destino o hacer la fila completa un enlace con nombre accesible específico, conservando todos los destinos.
- **Resultado esperado:** cada destino se identifica por sí mismo. Heurísticas 4 y 6.

### UX-13 — MEDIO · Sin acceso directo para resolver prerrequisitos

- **Pantalla/evidencia:** carga de imagen indica «Primero registra una consulta» y deshabilita el envío, sin enlace a nueva consulta. C/R con expediente sin consultas.
- **Escenario e impacto:** el asistente debe localizar manualmente cómo registrar consulta y luego volver a imágenes.
- **Recomendación:** añadir enlace contextual a nueva consulta conservando el paciente y una vuelta clara a carga; no eliminar la validación existente.
- **Resultado esperado:** el estado vacío explica el siguiente paso y facilita completarlo. Heurísticas 3, 9 y 10.

### UX-14 — ALTO · Consentimiento no aclara quién acepta ni la consecuencia

- **Pantalla/evidencia:** `ConsentPage.tsx` usa «He leído y acepto» y «Aceptar y guardar», guarda texto/identificación y luego presenta «Consentimiento aceptado». C.
- **Escenario e impacto:** en una computadora compartida no es evidente si la persona que acepta es el paciente o el personal, ni cómo corregir una aceptación. No se evaluó la validez legal.
- **Recomendación:** revisar el flujo y lenguaje con responsables clínicos/legales; mostrar identidad del paciente y significado de la aceptación antes de guardarla, y definir corrección/auditoría autorizada sin presumir firma digital.
- **Resultado esperado:** el usuario entiende quién realiza la acción y qué queda registrado. Heurísticas 2, 5 y 10.

### UX-15 — MEDIO · Error de archivo sin recuperación completa del registro

- **Pantalla/evidencia:** la corrección previa de `DiagnosticResultPage.tsx` informa imagen ausente y enlaza a carga; la carga crea una imagen nueva y mantiene el registro anterior. C y pruebas previas.
- **Escenario e impacto:** al recuperar un archivo faltante, el usuario puede esperar que el estudio original quede reparado, pero obtiene otro registro.
- **Recomendación:** explicar que cargar crea otro registro y ofrecer una recuperación controlada del original solo si se valida identidad, permisos e historial; preservar trazabilidad.
- **Resultado esperado:** recuperación predecible sin asociar una imagen a un paciente equivocado. Heurísticas 2 y 9.

### UX-16 — BAJO · Información duplicada en ficha y navegación

- **Pantalla/evidencia:** `PatientDetailPage.tsx` repite nacimiento, edad, género, estado y contacto en cabecera y «Datos generales»; «Resumen clínico» es una lista de enlaces. R/C.
- **Escenario e impacto:** se consume espacio sin mejorar el reconocimiento de la próxima acción clínica.
- **Recomendación:** mantener una sola presentación de datos de contacto y reservar el espacio recuperado para acciones/contexto disponible, sin eliminar campos.
- **Resultado esperado:** lectura más rápida y menor repetición. Heurística 8.

### UX-17 — MEDIO · Descarga sin feedback final o estado claro para otras acciones

- **Pantalla/evidencia:** `ExportsPage.tsx` bloquea toda nueva descarga cuando `busy` es verdadero, pero solo expone `aria-disabled` para la fila activa y no presenta éxito; «Ver identificación» usa descarga. C.
- **Escenario e impacto:** ante un archivo lento el usuario puede pulsar otra descarga que no responde, o esperar que «Ver» abra una vista.
- **Recomendación:** indicar «Preparando descarga» con controles coherentes para todas las filas y renombrar «Ver identificación» según el resultado real; notificar fallos y conservar descargas.
- **Resultado esperado:** el usuario sabe qué ocurre y qué acción está disponible. Heurísticas 1, 2 y 4.

### UX-18 — MEDIO · Vacíos, errores y ayuda no siempre indican qué hacer

- **Pantalla/evidencia:** consultas vacías dicen «No hay consultas registradas» y tienen acción en cabecera; imágenes vacías y filtros no siempre ofrecen limpiar o crear contextual; `api/client.ts` puede devolver mensaje genérico. C/R.
- **Escenario e impacto:** ante una lista vacía o un error de red el usuario no siempre distingue ausencia real, filtro restrictivo o fallo, ni cómo recuperarse.
- **Recomendación:** distinguir vacío inicial, sin coincidencias y error; ofrecer limpiar filtros, registrar o reintentar según estado; usar toasts para resultados transitorios y mensajes persistentes solo cuando el estado afecte la tarea.
- **Resultado esperado:** el siguiente paso se reconoce sin capacitación. Heurísticas 1, 9 y 10.

### UX-19 — MEDIO · Calendario y tabla tienen alcances temporales distintos

- **Pantalla/evidencia:** calendario filtra visualmente por mes; tabla muestra todos los elementos devueltos por filtros. R: agenda móvil indicó mes vacío y debajo mostró una cita de otro mes.
- **Escenario e impacto:** recepción puede interpretar que no hay citas, aunque la tabla inferior muestra una fuera del mes.
- **Recomendación:** etiquetar claramente «Mes visible» y «Todas las citas que coinciden con los filtros», o sincronizar temporalmente tras validar uso; conservar acceso al listado completo.
- **Resultado esperado:** el alcance de cada representación es explícito. Heurísticas 1 y 2.

### UX-20 — MEDIO · Formularios largos sin indicación suficiente de obligatoriedad y avance

- **Pantalla/evidencia:** campos `required` en paciente, cita y cinco imágenes iniciales del estudio; etiquetas generalmente no señalan obligatorios; antecedentes reúne 24 preguntas y cuatro notas. C.
- **Escenario e impacto:** la persona descubre requisitos al intentar guardar y puede perder su lugar en móvil.
- **Recomendación:** identificar campos obligatorios/opcionales, explicar formatos antes de escribir y agrupar antecedentes por tema con progreso de revisión sin ocultar errores. Mantener validaciones actuales hasta acordar cambios.
- **Resultado esperado:** menos intentos fallidos y menor carga de memoria. Heurísticas 5, 6 y 10.

### UX-21 — MEDIO · Controles del odontograma exigen precisión fina

- **Pantalla/evidencia:** cada pieza expone cinco botones de superficie; la documentación previa comprobó 24 px y selección por cuadrante en móvil. C/P; captura desktop previa inspeccionada.
- **Escenario e impacto:** un toque accidental puede cambiar una cara próxima; el nombre accesible incluye número, superficie y estado, pero falta evaluación con lector de pantalla y clínica.
- **Recomendación:** medir objetivos y separación reales a 320/390/768 px, probar con usuarios y dispositivos táctiles, considerar detalle ampliado/selección de pieza y confirmación visual reversible. Mantener las 52 piezas y cinco superficies.
- **Resultado esperado:** selección precisa sin sacrificar el diagrama ni su accesibilidad. Heurísticas 5 y 7.

### UX-22 — MEDIO · Diagnóstico sin contexto clínico visible suficiente

- **Pantalla/evidencia:** `DiagnosticResultPage.tsx` muestra ID de imagen, visores y detecciones; no muestra en su encabezado el nombre del paciente ni enlace al expediente. C.
- **Escenario e impacto:** al cambiar entre estudios, el profesional debe recordar a quién pertenece la imagen.
- **Recomendación:** mostrar paciente/tipo/fecha provenientes del objeto existente y enlazar al expediente autorizado; explicar que la salida es una ayuda de análisis según validación clínica del producto.
- **Resultado esperado:** se mantiene la identidad durante la revisión. Heurísticas 2 y 6.

## Evaluación por pantalla y tarea

R = visitada en navegador en esta auditoría; C = código; P = evidencia E2E histórica. «Visitada» no significa que todos sus estados o acciones se hayan probado.

| Pantalla / ruta | Objetivo, acción principal y estados observados | Evaluación y evidencia |
|---|---|---|
| Login `/login` | Autenticarse; usuario, contraseña, mostrar y enviar; toast/error. | Labels y autocomplete; no se encontró recuperación de contraseña en la SPA. R/C. |
| Inicio `/` | Revisar jornada; abrir agenda, dos tablas. | Buena prioridad operativa; citas sin acceso directo; vacío sin CTA. UX-10. R/C. |
| Pacientes `/patients` | Elegir tarea; alta y seis accesos. | Duplicación de alta y seis «Acceder» ambiguos. UX-07/12. R/C. |
| Pacientes `/patients/list` | Examinar tabla paginada. | Acciones por fila; búsqueda ausente en esta variante. UX-07. R/C. |
| Búsqueda `/patients/search` | Buscar por nombre/teléfono/correo y abrir/editar. | Filtros por URL y paginación; falta limpiar explícito, ver riesgo homónimos. R/C. |
| Alta `/patients/new` | Registrar datos personales/contacto. | Labels y errores asociados; obligatorios y formato de teléfono poco anticipados. UX-20. R/C. |
| Contacto `/patients/contact` | Seleccionar y enviar correo. | Selector compartido y estado de envío; contexto de destinatario debe desambiguarse. UX-06. R/C. |
| Paciente `/patients/:id` | Identificar, editar, abrir expediente o desactivar. | Confirmación de desactivación; metadatos duplicados y sin acción contextual de cita. UX-09/16. R/C. |
| Edición `/patients/:id/edit` | Modificar datos; guardar. | Se comprobó pérdida de borrador al salir. UX-03. R/C. |
| Selector `/clinical-record` | Buscar paciente y abrir expediente. | Resultados por nombre; límite 10 y sin ID visible. UX-06. R/C. |
| Expediente `/patients/:id/record` | Elegir tarea clínica. | Contexto de nombre/ID persistente; menú, no resumen de actividad. UX-10. R/C. |
| Antecedentes `/patients/:id/medical-history` | Registrar 24 condiciones y notas. | Riesgo de «No» por defecto; formulario extenso. UX-01/20. R/C. |
| Nueva consulta `/patients/:id/consultations/new` | Capturar motivo, diagnóstico, tratamiento y notas. | Motivo obligatorio; al guardar lleva directamente a receta; confirmar con clínicos si es la salida esperada. R/C. |
| Historial `/patients/:id/consultations` | Revisar consultas y abrir receta. | Timeline claro, fecha y diagnóstico; no muestra tratamiento u observaciones hasta receta. UX-08/18. R/C. |
| Receta `/consultations/:id/prescription` | Leer e imprimir diagnóstico/tratamiento. | Paciente visible, sin navegación Patient 360 ni regreso explícito. UX-08. C/P. |
| Imágenes `/patients/:id/images` | Seleccionar carga, búsqueda o historial. | Acciones claras, añade un hub antes de la tarea. R/C. |
| Carga `/patients/:id/images/upload` | Asociar imagen a consulta. | Campos y validación; vacío sin enlace a prerrequisito. UX-13. R/C. |
| Búsqueda imágenes `/patients/:id/images/search` | Filtrar por fecha/consulta; descargar/eliminar. | Filtrado y estado parcial; eliminar pide confirmación. R/C/P. |
| Historial imágenes `/patients/:id/images/history` | Revisar, descargar, eliminar. | Descripción, fecha y acciones; ausencia de archivo requiere recuperación contextual. UX-15/18. R/C. |
| Odontograma `/patients/:id/odontogram` | Pintar estados de 52 piezas y guardar. | Diagrama FDI y leyenda; valor por defecto y precisión táctil requieren revisión. UX-02/21. R/C/P. |
| Progreso `/patients/:id/comparative-study` | Guardar texto y fotografías antes/después, PDF. | Cinco imágenes iniciales obligatorias sin guía previa suficiente; formulario largo. UX-03/20. R/C. |
| Consentimiento `/patients/:id/consent` | Aceptar y guardar identificación. | Texto/estado visibles; actor y consecuencias de aceptación ambiguos. UX-14/17. R/C. |
| Agenda `/appointments` | Filtrar, buscar, ver calendario y operar citas. | Buen estado textual y agenda móvil; cancelación directa; mes/lista con distinto alcance. UX-04/19. R/C. |
| Nueva cita `/appointments/new` | Seleccionar paciente y programar. | Dos pasos claros, pero búsqueda limitada y sin paciente precargado. UX-06/09/20. R/C. |
| Detalle cita `/appointments/:id` | Revisar fecha, paciente y motivo; editar. | Sin enlace al paciente ni regreso contextual. UX-08. R/C. |
| Editar cita `/appointments/:id/edit` | Corregir cita con formulario compartido. | Validación compartida; terminología «Anulada» y protección de borrador pendientes. UX-03/11. R/C. |
| Diagnósticos `/diagnostics` | Filtrar imágenes y abrir análisis. | Tabla y estados de procesamiento; exige contexto al entrar al resultado. UX-22. R/C. |
| Resultado `/diagnostics/:id` | Ver original, resultado y detecciones. | Autoanálisis al entrar; falta identidad visible; manejo de archivo faltante con enlace de carga. UX-05/15/22. C/P. |
| Exportaciones `/exports` | Descargar tres Excel. | Etiquetas de tipo claras; feedback/estado de descarga insuficiente. UX-17. R/C. |
| Privacidad `/privacy` | Leer aviso. | Acceso por pie dentro de sesión; la revisión legal del texto queda fuera de alcance. R/C. |

## Flujos actuales y propuestos

Las propuestas no inventan datos; cuando necesitan modificar API/modelo se indica.

1. **Encontrar expediente:** actual: Pacientes → Buscar pacientes → escribir → Buscar → Ver → expediente. Propuesto: Pacientes/listado con buscador → resultado identificado → expediente. Mantener alta, URLs y paginación; búsqueda ampliada requiere API.
2. **Crear cita desde paciente:** actual: Pacientes → localizar → Citas → Nueva cita → buscar de nuevo → seleccionar → capturar → guardar. Propuesto: ficha → Nueva cita con paciente validado → capturar → guardar. Preservar búsqueda manual.
3. **Atender cita:** actual: Inicio → agenda → localizar → Ver → anotar paciente → Pacientes → buscar → expediente. Propuesto: Inicio → cita → paciente → expediente; mantener filtros y detalle.
4. **Consulta y receta:** actual: expediente → Nueva consulta → guardar → receta → volver por navegador o menú. Propuesto: guardar → receta con enlaces a historial y expediente; mantener impresión y contenido.
5. **Cargar imagen sin consulta:** actual: imágenes → cargar → leer advertencia → navegar a nueva consulta → registrar → regresar → cargar. Propuesto: advertencia → crear consulta para paciente → volver a carga con contexto; conservar requisito.
6. **Cancelar cita:** actual: agenda → Cancelar → estado cambiado. Propuesto: agenda → Cancelar → comprobar paciente/fecha y confirmar, o deshacer fiable tras validar reglas. Es una modificación explícita del comportamiento.
7. **Registrar antecedentes/odontograma:** actual: abrir → valores negativos/sanos iniciales → editar lo conocido → guardar. Propuesto: abrir → distinguir no evaluado → registrar y revisar → guardar. Requiere cambio de datos y validación clínica; no inferir estado de registros antiguos.

## Accesibilidad y responsive

En el recorrido actual de 390 px agenda y expediente tuvieron `documentElement.scrollWidth === innerWidth`; eso no demuestra ausencia de scroll interno, legibilidad a 200 % ni comportamiento en todos los dispositivos. El historial previo documenta pruebas automatizadas de ancho, nombres accesibles, foco del drawer y controles del visor; deben tratarse como evidencia histórica y no como certificación. La captura móvil actual muestra navegación de paciente en varias filas y tabla transformada a registro; es funcional en esa muestra, pero aumenta desplazamiento vertical. La captura desktop de ficha muestra información repetida y botones claros.

Los controles de superficie dental, radiobuttons, contraste, orden de foco después de errores, avisos que desaparecen, áreas clicables y salida de diálogos requieren pruebas con teclado, lector de pantalla y usuarios. Medir WCAG 2.2 con criterios y excepciones aplicables. No se evaluaron todos los estados hover/disabled/error, orientación horizontal o dispositivos reales.

## Mejoras por tipo

- **Quick wins:** unificar «Cancelada», enlaces desde cita a paciente y desde Inicio a cita, nombres únicos en accesos, enlace para crear consulta desde carga, etiquetas de campos requeridos y ámbito mes/lista.
- **UX:** prevención de pérdida de borradores, confirmación o deshacer de cancelación, paciente preseleccionado, errores recuperables y decisión explícita de reanálisis.
- **UI:** reducir duplicación de datos, reforzar jerarquía de acciones, identificar estados y contexto sin depender del color, revisar tamaños y foco táctil.
- **Estructurales:** estados clínicos desconocidos, búsqueda/autocomplete desambiguado, navegación con contexto, protección de borradores y estados de datos compartidos; valorar migraciones y compatibilidad.
- **Avanzadas:** probar accesos rápidos y atajos con personal real, resumen clínico de datos existentes y recuperación trazable de archivos. No desarrollar atajos, KPIs ni recordatorios sin evidencia de necesidad y soporte de datos.

El detalle de orden, esfuerzo, dependencias y criterios de aceptación está en [plan de mejoras](ux-improvement-plan.md).
