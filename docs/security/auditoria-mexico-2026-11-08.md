# Auditoría técnica de seguridad y preparación regulatoria — SmileManager

Fecha: 8 de noviembre de 2026. Referencia Git: `dcdcc38`; se revisó también el árbol de trabajo, que ya tenía cambios en `frontend/package-lock.json`. Este informe no modifica la aplicación ni ese cambio preexistente.

Actualizaciones posteriores autorizadas: [etapa 1](etapa-1-resultados.md) y [etapa 2](etapa-2-resultados.md). Los hallazgos de este documento reflejan el momento de auditoría; consultar esas entregas para las correcciones, pruebas y pendientes actuales. El dictamen general sigue NO-GO por las evidencias operativas y regulatorias pendientes.

## Dictamen ejecutivo

**NO-GO para autorizar producción con datos clínicos reales a partir de la evidencia disponible. No es posible acreditar seguridad alta ni cumplimiento regulatorio integral.** Hay controles técnicos valiosos, pero subsisten brechas verificables y controles externos sin acreditar. Esto no significa que se haya demostrado una intrusión ni que todos los componentes sean inseguros.

Este documento es una auditoría técnica preliminar de código y preparación regulatoria. No constituye certificado de conformidad, resolución de una autoridad, prueba de penetración integral ni dictamen jurídico. La aprobación requiere determinar el prestador, uso previsto, versión, despliegue y procedimiento de evaluación aplicables.

## Alcance y método

- Arquitectura Django/DRF, React, PostgreSQL, almacenamiento S3 e inferencia local YOLO.
- Inspección de configuración, rutas, autenticación, autorización por clínica, documentos clínicos, consentimiento, auditoría, cargas, contenedores, CI y documentación operativa.
- Inventario de archivos rastreados por Git sin visualizar documentos, imágenes ni identificaciones. No se verificó si son datos reales, sintéticos o material público.
- Consulta de legislación y publicaciones oficiales mexicanas enlazadas abajo.
- Ejecución de dos archivos de pruebas frontend: **7 pruebas aprobadas**. Alcance: cliente API y manejo de medios protegidos; no demuestra autorización del servidor.
- `python3 -c "import django; print(django.get_version())"` terminó con `ModuleNotFoundError`. No se ejecutaron pruebas Django, PostgreSQL, `check --deploy`, E2E completos ni escaneos nuevos de dependencias o secretos. Los resultados históricos del repositorio no se contabilizan como validación actual.
- No se accedió a producción, cuentas AWS, políticas IAM, correo real, respaldos, configuración del proxy o panel de CI. No se hicieron ataques de disponibilidad, cambios operativos ni remediaciones.

Las severidades son una priorización cualitativa de riesgo, no puntuaciones CVSS. **Confirmado** significa evidencia en el repositorio; **condicional** depende de topología o datos; **no acreditado** significa que falta evidencia y no prueba por sí solo una falla.

## Marco mexicano y ruta de aprobación

| Instrumento | Aplicación y evaluación preliminar |
|---|---|
| [LFPDPPP vigente](https://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf), reforma 14-11-2025 | Para responsables privados: datos sensibles, fundamento del tratamiento, aviso, seguridad y derechos ARCO. Referencias: artículos 8, 9, 15, 18 y 19. El aviso publicado y el consentimiento requieren corrección y revisión legal. |
| [LGPDPPSO vigente](https://www.diputados.gob.mx/LeyesBiblio/pdf/LGPDPPSO.pdf), reforma 14-11-2025 | Si el responsable es una institución pública, aplicar este régimen y las disposiciones correspondientes al sujeto obligado. No se puede inferir cumplimiento gubernamental de una revisión pensada para clínica privada. |
| [NOM-004-SSA3-2012](https://sidof.segob.gob.mx/notas/docFuente/5272787) | Expediente clínico: conservación mínima de cinco años desde el último acto médico, confidencialidad y requisitos de notas y firmas. Referencias: 5.4 y 5.9–5.12. Conservación y autoría documental no acreditadas integralmente. |
| [NOM-024-SSA3-2012](https://sidof.segob.gob.mx/notas/docFuente/5280847) | SIRES: gestión de seguridad, documentos inalterables, firmas según alcance, roles, intercambio y consentimientos. Referencias: 6.3, 6.4, 6.5, 6.6 y 7. Falta matriz de requisitos, guías aplicables y evidencia de evaluación de conformidad para esta versión. |
| [COFEPRIS: guía de registro de dispositivos médicos](https://www.gob.mx/cofepris/documentos/guia-para-la-obtencion-del-registro-sanitario-de-dispositivos-medicos) | Por la función de diagnóstico por IA, determinar si el uso previsto encuadra como software como dispositivo médico. Es una cuestión regulatoria pendiente; no se afirma que todo sistema administrativo requiera registro sanitario. |

La [DGIS](https://www.gob.mx/salud/acciones-y-programas/direccion-general-de-informacion-en-salud-dgis) publica información de certificación NOM-024. Definir con la instancia competente el alcance, versión y guías a evaluar. No existe evidencia aportada de un certificado correspondiente a este producto y despliegue.

La programación de una modificación normativa no demuestra su entrada en vigor: el [Programa Nacional de Infraestructura de la Calidad 2026](https://www.dof.gob.mx/abrirPDF.php?anio=2026&archivo=24022026-MAT.pdf&repo=) menciona trabajos sobre NOM-024. Revalidar publicaciones y disposiciones vigentes al iniciar el trámite. Esta revisión no sustituye un análisis jurídico exhaustivo de cambios normativos.

## Hallazgos y criterios de cierre

### MX-01 — Archivos de categorías clínicas distribuidos con Git

**Alta; crítica si se confirma información personal real distribuida sin autorización. Confirmado el rastreo, no la exposición pública.**

`git ls-files media` identifica **276 archivos**: 10 en consentimientos, 110 en detecciones, 39 en estudios, 29 en imágenes clínicas y 88 en resultados. `db.sqlite3` sigue rastreada, pero su tamaño actual es **0 bytes**; no se afirma que esta copia contenga pacientes. `.gitignore` no elimina archivos previamente rastreados. Evidencia adicional: `docs/security/git-sensitive-data-remediation.md`.

**Riesgo:** clones, ramas y artefactos pueden convertirse en copias no gobernadas si los archivos contienen información sensible.

**Cierre:** clasificar los archivos con el responsable de privacidad; restringir distribución; inventariar remotos, historial, clones, forks y artefactos; retirar material sensible del versionado y coordinar depuración histórica cuando corresponda. Preservar evidencia y copias autorizadas. Determinar obligaciones de notificación si se confirma vulneración. Rotar secretos únicamente cuando su exposición se identifique. No se ejecutó eliminación ni reescritura de historial.

### MX-02 — Consentimiento marcado como aceptado sin evidencia suficiente del titular

**Alta. Confirmado en el flujo implementado.**

En `api/tenant_consents.py:74–88` el médico autorizado adjunta `archivo_ine`; `texto` admite vacío y el servidor asigna `fecha_aceptacion`. `api/services/consent_pdf.py` genera un documento con esos datos. No se observa firma o autenticación del paciente, representante o testigos en este flujo, ni una versión inmutable de plantilla que vincule la voluntad al contenido. Una identificación adjunta y una fecha generada por el servidor no demuestran, por sí solas, esa voluntad. Un documento externo firmado podría aportar evidencia, pero el flujo no la exige ni valida.

**Cierre:** separar consentimiento clínico y tratamiento de datos; definir supuestos legales y representación; exigir contenido adecuado y conservar evidencia verificable de aceptación vinculada a versión y documento. Revisar la necesidad y proporcionalidad de conservar identificaciones completas. No basta con agregar una casilla o declarar que todo consentimiento exige e.firma.

### MX-03 — Aviso de privacidad incompleto para uso operativo

**Alta. Confirmado en el aviso incluido.**

`frontend/src/pages/PrivacyPage.tsx:13` identifica genéricamente a SmileManager como responsable; no proporciona domicilio ni identidad jurídica concreta por clínica. La sección ARCO remite a contacto directo sin canal ni procedimiento concreto. Tampoco define mecanismos suficientes de limitación y revocación. La relación responsable/encargado entre clínica y proveedor queda ambigua.

**Cierre:** aviso validado por responsable, domicilio, identificación de datos sensibles, finalidades y mecanismos exigibles; procedimientos ARCO/revocación operables, plazos y responsables; contratos con encargados y reglas de proveedores. Un aviso distinto entregado por fuera debe aportarse y conciliarse con el publicado.

### MX-04 — Autoría, firma e integridad documental insuficientemente acreditadas

**Alta. Parcialmente confirmado; controles SQL y documentales externos no verificados.**

`Pacientes/models.py:87` conserva usuario médico y fecha de consulta, pero no evidencia de firma vinculada al contenido. `api/tenant_consultations.py` expone creación y lectura; no se encontró edición de consultas en esta superficie. El versionado de `api/services/clinical_records.py` mejora antecedentes y odontograma, pero los snapshots no constituyen por sí solos firma ni almacenamiento inalterable. Los modelos de revisiones y auditoría permanecen mutables mediante ORM/SQL con privilegios suficientes; no se halló protección de inmutabilidad en migraciones.

**Cierre:** matriz documental con requisitos de autoría/firma por tipo; conservación del nombre del firmante y contenido firmado; correcciones por adendas; protección verificable frente a modificación y borrado y validación de integridad. No se concluye que toda firma deba ser avanzada en todos los casos.

### MX-05 — Limitación de intentos insuficiente como defensa distribuida

**Alta condicionada a despliegue con múltiples procesos/instancias o proxy.**

`api/throttles.py:7–22` usa `SimpleRateThrottle`, `REMOTE_ADDR` y claves por cuenta. No hay `CACHES` compartido en la configuración de producción revisada: se depende de la caché local predeterminada. Los contadores no se comparten entre procesos. Tras un proxy, `REMOTE_ADDR` puede representar al proxy y bloquear usuarios legítimos en conjunto. No se comprobó abuso en producción.

**Cierre:** límite compartido con operaciones atómicas y controles en el borde; determinar IP confiable según topología sin aceptar cabeceras arbitrarias; probar concurrencia, múltiples workers, reinicios, login y recuperación. DRF advierte que su throttling no constituye por sí mismo una defensa contra fuerza bruta o denegación de servicio: [documentación oficial](https://www.django-rest-framework.org/api-guide/throttling/). Caché predeterminada: [Django](https://docs.djangoproject.com/en/5.2/ref/settings/#caches).

### MX-06 — Autenticación de administradores y duración de sesiones por reforzar

**Media; elevar prioridad para administradores con capacidad de conceder acceso. Confirmado en código.**

No se encontró MFA en el inicio de sesión. El acceso JWT dura cinco minutos; logout y recuperación invalidan refresh, pero no revocan inmediatamente access ya emitidos. `SESSION_COOKIE_AGE=1800` corresponde a sesiones Django y no establece inactividad de 30 minutos para la API JWT. `RefreshView` genera un refresh nuevo de ocho horas en cada rotación sin límite absoluto de sesión visible.

**Cierre:** MFA para cuentas privilegiadas, política explícita de inactividad y duración absoluta, reautenticación de acciones sensibles, inventario/revocación de sesiones y decisión documentada sobre la ventana residual. Los cinco minutos no se reportan como vulnerabilidad crítica. Referencia de expiración: [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/en/stable/settings.html).

### MX-07 — Custodia independiente de auditoría no acreditada

**Alta para trazabilidad y respuesta forense. Brecha de evidencia.**

Hay eventos por clínica, usuario, acción y request ID en `Usuarios/models.py:109` y llamadas explícitas en APIs tenant. No hay evidencia de envío a un repositorio independiente con retención protegida, alertas verificadas o privilegios SQL que impidan alteración por la identidad de aplicación. El logger operativo omite contenido clínico, lo que reduce filtraciones, pero no sustituye evidencia de auditoría íntegra.

**Cierre:** matriz de eventos exitosos y denegados, cuentas privilegiadas auditadas, sincronización horaria, retención y exportación a almacenamiento protegido; ensayo de detección de alteraciones. No se afirma que falte toda auditoría de acceso.

### MX-08 — Protección del despliegue y recuperación sin demostrar

**Bloqueador de aprobación por falta de evidencia; impacto potencial alto.**

`settings.py` configura S3, HTTPS y hosts, pero no demuestra bucket privado, IAM mínimo, cifrado efectivo de base/objetos/backups, claves, TLS PostgreSQL, configuración del proxy o alertas activas. `docs/operations/backup-recovery-plan.md` declara restauración sin verificar y RPO/RTO pendientes. La región S3 está fijada en `us-east-2`: requiere revisión contractual y de flujos de datos; no constituye automáticamente una infracción.

**Cierre:** evidencia sanitizada de configuración efectiva y privilegios; prueba anónima negativa con objeto sintético; TLS extremo a extremo según arquitectura; restauración conjunta de DB y archivos con medición RPO/RTO; alarmas y simulacro de incidente con responsables. Verificar retención clínica y excepciones legales antes de automatizar borrados. El Compose utiliza configuración local y el Dockerfile arranca `runserver`; tratarlos como desarrollo y acreditar un despliegue de producción separado. El `Procfile` sí utiliza Gunicorn.

### MX-09 — PDF validado superficialmente

**Media. Confirmado en código; explotación no demostrada.**

`api/upload_policy.py` limita tamaño y valida imágenes con Pillow; para PDF comprueba extensión, tipo declarado, cabecera y marcador final. Estas comprobaciones permiten pasar documentos con contenido activo u objetos incrustados. La descarga autenticada y como adjunto reduce exposición, pero no acredita seguridad del archivo que abrirá un operador.

**Cierre:** política de formatos y cuarentena, análisis de contenido/malware y, según riesgo, reconstrucción segura; no servir cargas activas como recursos ejecutables del origen de la aplicación. Probar archivos sintéticos y no introducir muestras maliciosas reales en este repositorio.

### MX-10 — Aseguramiento regulatorio y cadena de suministro pendientes

**Alta como preparación de aprobación; no implica CVE confirmado.**

No se aportó expediente de certificación, SGSI operativo, alcance de interoperabilidad/catálogos ni evaluación sanitaria del uso previsto de IA. Existe CI de pruebas y escaneos, pero no se consultó su ejecución ni protección de ramas. `requirements.txt` fija versiones sin hashes; las imágenes base y acciones CI usan etiquetas. Las versiones declaradas y los informes históricos de cero avisos no acreditan ausencia actual de vulnerabilidades.

**Cierre:** designar responsable regulatorio y documentar una matriz de requisitos, controles, evidencias y pruebas. Evaluar el uso clínico y regulatorio de IA. Aportar escaneos actuales de dependencias, credenciales y contenedores, inventario/SBOM y artefactos reproducibles. No se identificó un CVE vigente específico en esta auditoría.

## Controles positivos comprobados por lectura

- Producción rechaza DEBUG, ausencia de secreto y hosts no explícitos; fuerza HTTPS y cookies seguras, HSTS, `nosniff` y protección contra marcos.
- JWT access en memoria frontend; refresh HttpOnly/Strict con rotación y blacklist. Validación de origen en operaciones de autenticación.
- Consulta por membresía activa, clínica activa y médico asignado; roles separados y comprobación de contexto en servidor (`api/tenant_context.py`, `api/policies.py`).
- API clínica legacy cerrada por defecto; lectura clínica global de backoffice denegada mediante `NoGlobalClinicalAccess`. Las descripciones históricas de acceso global ya no reflejan esta implementación.
- Archivos tenant con nombres aleatorios, entrega protegida y respuestas sin caché; límites de imagen y exportación; neutralización de fórmulas Excel.
- Escrituras clínicas con transacciones, bloqueos y control de versiones en recursos seleccionados. Pruebas de aislamiento y concurrencia presentes, aunque no ejecutadas en esta revisión.
- RLS no implementado y documentado como límite; su ausencia no demuestra por sí misma una fuga ni incumplimiento. MFA, RLS, CSP, WAF y certificación ISO 27001 no se presentan como obligaciones legales universales.

## Plan de cierre y evidencia necesaria para reconsiderar el dictamen

| Orden | Trabajo | Responsable propuesto | Evidencia de cierre |
|---|---|---|---|
| 1 | Clasificar y contener material versionado; determinar alcance de distribución | Seguridad y privacidad | Inventario, clasificación y comprobación de copias/remotos; decisión de incidente |
| 2 | Corregir aviso, consentimiento y matriz de firma/retención | Jurídico, responsable clínico y desarrollo | Textos aprobados, flujo verificable y pruebas negativas de aceptación inválida |
| 3 | Endurecer autenticación, límites, auditoría y PDFs | Desarrollo y seguridad | Pruebas de sesiones, MFA, concurrencia, límites y custodia |
| 4 | Verificar infraestructura y restauración | Operaciones y seguridad | IAM/TLS/cifrado, accesos anónimos denegados y acta de restore DB+objetos |
| 5 | Ejecutar backend/PostgreSQL/E2E, SCA y pentest independiente sobre staging representativo | QA y auditor independiente | Resultados reproducibles, severidades resueltas y retest |
| 6 | Completar expediente regulatorio según uso y responsable | Dirección y responsable regulatorio | Matriz aplicable, evidencias de SGSI y evaluación de conformidad que corresponda |

No se asignan porcentajes de cumplimiento ni una nota de seguridad: faltan pruebas dinámicas y evidencia operativa para que sean defendibles. Puede continuarse desarrollo con datos sintéticos y entorno aislado. La autorización final debe identificar versión, infraestructura, riesgos residuales aceptados y responsables; este informe no habilita por sí solo uso clínico.
