# Decisiones de diseño

> Decisiones históricas: las interfaces HTML Django y `/sesiones/` fueron retiradas. Consultar [estado actual](../production/legacy-routes.md).

## UX-DEC-001 — La navegación actual define el shell

Problema: navbar solo expone cuatro de varios módulos y las páginas clínicas se navegan por enlaces contextuales.

Alternativas: mover todas las rutas al sidebar plano; mantener navbar; agrupar dominios con entrada de pacientes y citas.

Decisión: sidebar del workspace con entradas principales existentes y navegación local en el expediente; respetar cada ruta. Enlaces a privacidad y exportación permanecen alcanzables.

Razón: hacer legible dónde estoy/puedo ir sin perder enlaces secundarios ni forzar rutas sin datos.

Impacto: solo presentación y discoverability; el router y gates se mantienen.

Componentes: AppLayout, navegación de expediente, header paciente.

## UX-DEC-002 — Patient 360 parte de endpoints/rutas existentes

Problema: el record funciona como lanzador de tarjetas y el contexto del paciente puede perderse.

Alternativas: pantalla única que solicite nuevos datos; header persistente y navegación local; split master-detail en todas las pantallas.

Decisión: contexto paciente con ID y nombre real, más links locales persistentes en las rutas de paciente; conservar navegación por URL y vistas separadas. `PatientWorkspaceNav` consulta el endpoint existente `patients/:id/` al cambiar de ruta para reflejar una edición de nombre y muestra solo el ID si la consulta falla.

Razón: evita endpoints/datos nuevos y mantiene flujos verificables; el profesional reconoce siempre el expediente, incluso al abrir directamente odontograma o imágenes.

Impacto: 360 incremental; tabs muestran solo secciones existentes. Hay una petición GET adicional por navegación de subsección, sin alterar payloads ni permisos; cuentas sin acceso nunca reciben nombre. Pagos/tratamientos no se inventan.

Componentes: `PatientWorkspaceNav`, `AppLayout` y header del detalle.

## UX-DEC-003 — Agenda con capacidad documentada

Problema: API actual expone citas y la UI un calendario mensual y tabla; patrón resource scheduler podría sugerir recursos no disponibles.

Decisión: refinar calendario y tabla actuales; no fabricar vista profesional/día/semana. DATA_REQUIREMENT para recursos/intervalos y disponibilidad si luego se solicitan.

## UX-DEC-004 — Bootstrap se migra sin romper controles funcionales

La app usa Bootstrap JS para navbar móvil y estilos en toda la UI. Integrar Tailwind con preflight desactivado durante transición; retirar Bootstrap solo cuando se remplacen plugins/clases y los flujos mobile estén verificados.

## UX-DEC-005 — Tailwind coexistente durante la migración

Problema: la UI existente depende ampliamente de utilidades Bootstrap y estilos de componentes; un cambio masivo de clases pondría en riesgo forms, tablas, viewer y flujos clínicos.

Decisión: instalar Tailwind 3.4.17/PostCSS sin actualizar el framework, con prefijo `co-`, tokens clínicos y preflight apagado. Aplicar utilidades a shell y composición nueva; mantener CSS tokens y Bootstrap como capa de transición mientras se migra pantalla por pantalla.

Razón: compilar el sistema nuevo con bajo riesgo y reducir colisiones de reset antes de reemplazar patrones antiguos.

Impacto al inicio: Tailwind se integró con Bootstrap temporalmente. Estado actual: Bootstrap CSS/JS y la dependencia se retiraron tras la migración visual; ver UX-DEC-017.

## UX-DEC-006 — Layout adaptable al flujo real

Problema: la navegación actual tiene módulos clínicos secundarios accesibles desde el hub del paciente; elevarlos todos al sidebar cargaría la navegación y forzaría módulos inexistentes.

Decisión: sidebar por áreas de trabajo con rutas principales y una barra contextual Patient 360 que muestra solo rutas de paciente existentes. Exportaciones y privacidad permanecen accesibles.

Impacto: no se altera el árbol de rutas ni se inventan pagos, tratamientos o documentos.

## UX-DEC-007 — Estado operativo legible en Inicio

Problema: el dashboard presentaba el código de estado de la API (`P`, `C`, `A`) como texto de cita.

Decisión: traducir esos tres códigos existentes a Pendiente, Completada y Cancelada, con indicador y color semántico. Códigos no reconocidos conservan el valor recibido.

Razón: el estado debe poder leerse sin conocer códigos ni depender solo del color.

Impacto: presentación del estado; no transforma payloads ni reglas de negocio.

## UX-DEC-008 — Foco contenido en el drawer móvil

Problema: al abrir el drawer, el foco debe seguir la navegación móvil y no perderse detrás del scrim o en el contenido de fondo.

Decisión: al abrir, colocar el foco en el primer enlace; al llegar al primer/último elemento, envolver Tab/Shift+Tab; Escape cierra el drawer y devuelve el foco al toggle.

Razón: mantiene orientación y navegación por teclado dentro de la navegación temporal.

Validación: Playwright sobre el build de producción servido por Django comprueba entrada, wrap en ambos sentidos y restauración de foco al cerrar.

## UX-DEC-009 — Errores de validación asociados al campo

Problema: los formularios de paciente y cita mostraban el texto del servidor junto al campo, pero el control no exponía su estado inválido ni una relación accesible con el mensaje.

Decisión: conservar los mismos campos, restricciones, payloads y mensajes, y vincular los errores recibidos con `aria-invalid` y `aria-describedby`; el detalle general se anuncia como alerta.

Validación: Playwright fuerza un error de campo 400 para cada alta, comprueba estado/asociación/alerta y completa el reintento exitoso.

## UX-DEC-010 — Recursos del visor clínico servidos localmente

Problema: las imágenes de controles de OpenSeadragon se solicitaban a un CDN externo y aparecían rotas cuando ese host no estaba disponible.

Decisión: servir los recursos del paquete instalado desde `public/openseadragon/images/`, usando la base URL configurada por Vite.

Razón: el visor debe conservar controles de zoom, rotación y navegación sin depender de terceros ni de conectividad externa.

Impacto: no cambia el endpoint ni el origen de las imágenes clínicas; se empaquetan los 40 PNG de controles de OpenSeadragon.

Validación: build de producción y Playwright comprueban que todas las imágenes de controles del viewer carguen con ancho natural mayor a cero. El área negra de la captura proviene del fixture E2E de 1×1 px, no de la toolbar.

## UX-DEC-011 — Migración CSS por componentes compartidos

Problema: Bootstrap CSS es global y retirar su import antes de migrar sus clases rompería controles, tablas y grillas en rutas distintas.

Decisión: empezar por `PatientForm` y `AppointmentForm`, que comparten densidad y jerarquía; encapsular los patrones repetidos con `@apply` Tailwind (`clinical-form-*`) y dejar Bootstrap disponible para el resto.

Razón: ambas formas son críticas, se reutilizan entre alta/edición y tienen flujos E2E de validación, envío y responsive.

Impacto: se migró su presentación sin tocar estado, campos, reglas, payload ni callbacks. Los errores conservan `aria-invalid`/`aria-describedby`; controles mantienen foco visible.

Validación: lint, unit, build, E2E 3/3; capturas desktop (1280) y mobile (390) revisadas. Continuar hacia tablas solo tras estas comprobaciones.

## UX-DEC-012 — Agenda por fecha en móvil

Problema: la cuadrícula mensual de 42 días requería desplazamiento horizontal para leer citas en una pantalla estrecha.

Alternativas: reducir siete columnas hasta volverlas ilegibles; reemplazar definitivamente el calendario mensual; ofrecer agenda por fecha con cambio explícito a la cuadrícula.

Decisión: bajo 768 px mostrar primero las citas del mes seleccionado agrupadas por fecha y ordenadas por hora. El selector Agenda/Mes mantiene disponible la cuadrícula original y sus enlaces. La navegación de mes y Hoy afecta ambas vistas; la tabla de búsqueda, filtros y acciones conserva su comportamiento.

Razón: permite consultar la jornada sin desplazamiento horizontal, y deja el contexto mensual a un toque. Solo se usa información existente en `appointments/`.

Impacto: cambio de presentación local en `AppointmentCalendar`, sin API, rutas ni parámetros nuevos. El estado de cita se escribe en la cuadrícula y la agenda para no depender del color.

Validación: lint, Vitest y build correctos; Playwright 3/3 con selector `aria-pressed`, scroll local y ancho a 390 px. Capturas desktop y móvil inspeccionadas. El recorrido manual de todos los estados y tamaños continúa pendiente.

## UX-DEC-013 — Historial de consultas como línea temporal clínica

Problema: la tabla anterior repetía columnas para registros que se consultan principalmente en secuencia cronológica por paciente.

Decisión: presentar cada consulta en una línea temporal compacta con fecha, motivo, diagnóstico y enlace directo a receta. Mantener el orden entregado por la API; no introducir una clasificación clínica ni campos de profesional inexistentes.

Razón: cada entrada se puede leer sin desplazamiento horizontal en móvil y conserva el contexto temporal en desktop.

Impacto: solo presentación de `ConsultationHistoryPage`; endpoint, error/retry, estado vacío y ruta de receta permanecen. La fecha se formatea en español con números tabulares.

Validación: E2E 3/3, motivo/enlace comprobados, 390/768 px sin overflow y capturas 1280/390 revisadas. Falta revisión manual con lector de pantalla y registros numerosos.

## UX-DEC-014 — Estudio comparativo como matriz clínica

Problema: nueve cargas de imagen se presentaban como tarjetas Bootstrap separadas, dificultando reconocer las fases antes/después y comparar posiciones.

Decisión: agrupar las cinco posiciones previas y cuatro posteriores en dos matrices compactas con label, archivo y preview en cada celda. Los datos generales permanecen antes de las imágenes y el PDF sigue en el encabezado cuando el estudio existe.

Razón: la estructura expresa el flujo clínico y evita tarjetas repetidas sin perder campos ni requisitos condicionales.

Impacto: presentación CSS/Tailwind de `ComparativeStudyPage`; FormData, método PUT, validaciones, previews, descarga y estados permanecen. La alerta global ahora se muestra solo si hay mensajes de error activos, para evitar una falsa alerta tras limpiar un campo.

Validación: lint, Vitest, build y E2E 3/3; la prueba comprueba ausencia de alerta antes del envío y conserva la validación 400/reintento. Capturas 1280/390 inspeccionadas.

## UX-DEC-015 — Odontograma como diagrama clínico táctil

Problema: las superficies de 16 px eran difíciles de tocar y, en móvil, las reglas CSS mostraban dos cuadrantes por fila por una sobrescritura de media query.

Decisión: preservar el mapa de 52 piezas y sus cinco superficies, aumentar cada objetivo a 24×24 px, nombrar cuadrantes, mantener scroll horizontal localizado y mostrar una instrucción visible. Bajo 576 px hay un cuadrante por fila; el resumen usa definición semántica en dos columnas.

Razón: mejorar precisión y reconocimiento sin simplificar el modelo dental ni ocultar piezas.

Impacto: solo presentación y feedback de aviso al editar una superficie; GET/PUT, `resumen`, limpieza confirmada y estados no cambian.

Validación: E2E clínico 1/1, objetivo táctil medido, scroll local y columnas móviles comprobados; capturas 1280/390 revisadas. Falta revisión manual de lector de pantalla y contraste de todos los estados.

## UX-DEC-016 — Visor diagnóstico como comparación de imágenes

Problema: la grilla Bootstrap envolvía dos visores especializados en tarjetas genéricas y dejaba una tabla de detecciones con ancho excesivo.

Decisión: dos paneles original/analizada lado a lado en desktop y apilados en móvil, con encabezados explícitos; tabla densa de tres columnas para detecciones. Mantener OpenSeadragon, controles locales, autoanálisis y acción de repetir.

Razón: la tarea principal es comparar la imagen fuente con su resultado y leer detecciones, no recorrer tarjetas.

Impacto: presentación y retry de GET; endpoints, análisis, overlays/visor y formato de detecciones permanecen.

Validación: E2E 3/3 y capturas 1280/390; PNGs de controles con ancho natural positivo. Falta revisar radiografía de resolución real y accesibilidad de controles del visor.

## UX-DEC-017 — Retirar Bootstrap al completar la migración visual

Problema: la hoja Bootstrap global añadía reglas de reset/utilidades que impedían confirmar el comportamiento del sistema Tailwind y ampliaban el CSS de producción.

Alternativas: conservar indefinidamente la hoja como capa compatible; retirarla tras migrar cada uso visual real.

Decisión: trasladar Inicio, formularios de citas, hub de imágenes, loaders y captions restantes a las clases del workspace; retirar import, reglas puente y dependencia `bootstrap`. Mantener `bootstrap-icons` como iconografía única.

Razón: Tailwind y las reglas clínicas ya cubren las superficies reales. La reducción de CSS de 357.41 a 127.65 kB permite un sistema visual menos ambiguo.

Impacto: no cambian rutas, APIs, payloads ni estados. La eliminación del reset global puede revelar diferencias en rutas poco visitadas; por ello la verificación visual completa sigue pendiente.

Validación: lint, Vitest 2/2, build y Playwright 3/3 después de retirar la hoja. Se inspeccionaron capturas móvil de Inicio, cita, login, receta y exportaciones; el enlace XLSX móvil se corrigió durante esa revisión.

## UX-DEC-018 — Retorno de login a la tarea solicitada

Problema: tras autenticarse desde una ruta protegida, `LoginPage` podía renderizar un `<Navigate to="/">` antes de ejecutar la navegación del submit, perdiendo la ruta de retorno y su query string.

Decisión: calcular el destino a partir de `location.state.from` (`pathname`, `search`, `hash`) y usarlo tanto en la rama de usuario autenticado como al completar `login()`.

Razón: una sesión reabierta debe recuperar el contexto operativo, incluyendo búsqueda/filtro de la URL.

Impacto: navegación de login; no cambia contrato de autenticación ni endpoints.

Validación: E2E logout → abrir `/app/patients/search?q=…` → login → misma ruta y búsqueda precargada; suite completa 3/3.

## UX-DEC-019 — Encabezados clínicos sin etiquetas repetitivas

Problema: el pase visual con `frontend-design` mostró etiquetas superiores en mayúsculas y separadores «·» en casi todas las pantallas. En Inicio, Pacientes, Agenda y vistas bajo Patient 360 repiten el área ya visible en navegación; la acumulación se acerca al patrón de dashboard genérico que el brief rechaza.

Plan visual: paleta base canvas `#f4f6f7`, superficie `#ffffff`, texto `#1d2a32`, secundario `#52616a`, marca `#176b78` y línea `#dce3e6`; Inter para texto y números tabulares donde importan. Mantener shell lateral y herramientas clínicas compactas, alineadas a la izquierda. La identidad visible la aportan agenda, diagrama dental, contexto del paciente y tablas de trabajo.

Alternativas: mantener un eyebrow en todas las páginas por consistencia; eliminar todos; conservar únicamente el dato contextual que ayuda a actuar (ID de cita/imagen/consulta o paciente).

Decisión: retirar etiquetas de área redundantes donde sidebar o Patient 360 ya dan contexto; redactar el metadata útil en estilo de frase, sin mayúsculas decorativas ni separadores superfluos. Mantener títulos operativos y acciones principales en posición estable.

Razón: reduce ruido en sesiones de trabajo largas y hace que el lenguaje visual dependa de la tarea clínica, no de una plantilla de encabezados.

Impacto: solo texto de presentación y espaciado del header. Rutas, enlaces, datos, llamadas y estados permanecen.

Validación: lint, build y E2E 3/3 tras el pase; capturas de Inicio, Pacientes, login y visor a 390 px revisadas. Se mantuvieron ID de cita/imagen/consulta y nombre de paciente donde aportan contexto.

## UX-DEC-020 — Resultados anteriores ante fallos de filtros

Problema: si un GET de listado falla después de cambiar filtros, la tabla anterior puede permanecer visible y parecer el resultado del filtro nuevo. En imágenes, un error de DELETE también podía confundirse con fallo del listado.

Alternativas: vaciar toda la tabla al iniciar cada consulta; conservar los resultados anteriores con una explicación y reintento.

Decisión: conservar los datos ya mostrados para no interrumpir el trabajo, pero avisar que proceden de la última carga y ofrecer reintento de la consulta. Separar errores de acciones destructivas. Descartar respuestas de GET anteriores cuando se cambia de filtro o se abandona la pantalla.

Razón: los datos previos todavía sirven de contexto, siempre que su vigencia sea explícita; una respuesta atrasada nunca debe sustituir una búsqueda más reciente.

Impacto: pacientes, agenda, diagnósticos e imágenes. No se modifican endpoints, parámetros, payloads ni controles de filtros/acciones.

Validación: Playwright 3/3 con 503 de filtro de citas, aviso y reintento, y DELETE de imagen fallido seguido de éxito; Vitest 3/3 incluye respuesta antigua de paciente llegando después del filtro nuevo. Lint y build pasan. Falta inspección manual de todas las combinaciones de error y datos previos.

## UX-DEC-021 — Contexto clínico ligado al ID actual

Problema: React puede reutilizar la misma pantalla de detalle/edición al cambiar solo el ID de una ruta. Mientras llega el siguiente GET, el estado anterior puede mostrar datos de otro paciente o cita; un formulario montado conserva además sus valores iniciales.

Decisión: reiniciar el contenido de la ruta cuando cambia `pathname`; en las vistas de detalle/edición de paciente y cita guardar el ID junto con los datos/error y descartar respuestas de rutas anteriores. Remontar los formularios de edición cuando cambia el ID.

Razón: en un workspace clínico el encabezado, los datos y la acción de guardar deben corresponder siempre al registro indicado por la URL actual.

Impacto: solo ciclo de vida visual y de carga en rutas parametrizadas; no cambian endpoints, permisos, payloads ni navegación.

Validación: Vitest 4/4 incluye navegación paciente 1 → paciente 2 con GET denegado sin exposición del paciente 1; Playwright 3/3, lint y build pasan. Falta recorrido manual con múltiples registros y cuentas.

## UX-DEC-022 — JWT de acceso efímero y refresh restringido

Problema: la SPA dependía de la sesión Django y una cabecera CSRF, y los archivos descargados mediante enlaces directos no podían usar Bearer.

Decisión: DRF usa exclusivamente JWT Bearer; access dura cinco minutos y reside en memoria. Refresh dura ocho horas en cookie HttpOnly, SameSite Strict y restringida a `/api/v1/auth/`; se rota y revoca. La SPA obtiene archivos mediante fetch con Bearer. `/sesiones/` conserva su autenticación propia.

Razón: separa el contrato de la SPA del sitio Django sin persistir tokens clínicos en localStorage. El refresh queda limitado a los endpoints de autenticación.

Impacto: cliente API, contexto de autenticación, cuatro rutas auth, descargas y vistas de archivos. Producción requiere `SECRET_KEY` y migraciones `token_blacklist`.

Validación: backend 42/42, Vitest 8/8 y E2E 3/3. Falta comprobar la configuración real del servidor de medios de producción.

## UX-DEC-023 — Caché clínica por recurso y filtro

Problema: cada pantalla cargaba datos de forma independiente y una petición fallida de filtros podía borrar el contexto anterior.

Decisión: TanStack Query en memoria, claves por recurso/ID/filtros, servicios tipados para endpoints y mutaciones que invalidan los listados afectados. Los formularios conservan sus borradores locales; el dato remoto compartido pertenece al caché. La última lista exitosa se presenta con aviso explícito si falla un filtro nuevo.

Razón: reutiliza datos entre subsecciones del paciente, evita solicitudes duplicadas, aísla pacientes y cuentas y mantiene un contexto operativo durante errores de red.

Impacto: listas de pacientes/citas/diagnósticos/imágenes, selector de paciente, `useResource`, cambios de paciente/cita/consulta/imagen/análisis, logout y cambio de identidad.

Validación: Vitest 8/8 incluye refresh concurrente y caché; E2E 3/3 incluye filtros 503, acciones clínicas y segunda cuenta.

