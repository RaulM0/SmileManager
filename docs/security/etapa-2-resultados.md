# Etapa 2 — Identidad, privacidad y documentos

Implementación posterior a la aprobación del plan de auditoría, el 8 de noviembre de 2026. Alcance: MX-02, MX-03, MX-04 y MX-06. Los cambios están en el repositorio; no se aplicaron migraciones a la base existente ni se hizo un despliegue de producción.

## Estado por hallazgo

| Hallazgo | Cambios verificables | Pendiente para cierre integral |
|---|---|---|
| MX-02 | El flujo publicado ya no acepta texto vacío ni una identificación como aceptación. Exige plantilla versionada, documento firmado adjunto, nombre y calidad del firmante, fecha y constancia del profesional. Conserva original, huellas, sustituciones y revocaciones independientes. | Aprobar el procedimiento de firma y revisión documental, supuestos legales, representación y textos. La aplicación registra evidencia; no verifica automáticamente una firma autógrafa ni certifica validez jurídica. |
| MX-03 | Avisos completos configurables por clínica, versiones protegidas, publicación restringida y consulta pública. Sin configuración se informa el pendiente, sin atribuir genéricamente responsabilidad a SmileManager. | Proporcionar identidad jurídica, domicilio, contacto y procedimientos aprobados; asignar responsables y operar solicitudes ARCO. No se inventaron datos ni se publicaron textos reales. |
| MX-04 | Borrador y cierre explícito de notas con confirmación de identidad; autor y fecha preservados; sellos de integridad; adendas independientes; snapshots sellados de antecedentes y odontograma; controles SQL de inmutabilidad en PostgreSQL. | Validar requisitos de firma por documento y mecanismo jurídicamente aplicable. Custodia independiente, roles SQL efectivos y retención operativa siguen pendientes. No se implementó firma electrónica avanzada ni se firma retrospectivamente información histórica. |
| MX-06 | MFA obligatorio para cuentas administrativas, TOTP, recuperación de un solo uso, sesiones revocables, caducidad absoluta e inactividad, reautenticación y recuperación operativa controlada. | Custodiar claves y códigos, verificar enrolamiento inicial de administradores, aprobar responsables de recuperación y ensayar el procedimiento en el despliegue. |

**Dictamen general: continúa NO-GO.** La aprobación del código no acredita por sí sola cumplimiento sanitario, privacidad operativa o seguridad de infraestructura.

## Autenticación y sesiones

- Cada access/refresh JWT queda ligado a `AuthSession` mediante un identificador. Logout, cierre individual, cierre de otras sesiones y recuperación de contraseña invalidan el acceso ligado a esa sesión en su siguiente validación. Los tokens antiguos sin vínculo se rechazan.
- Límite absoluto de ocho horas desde el inicio e inactividad de treinta minutos sin solicitudes autorizadas. La renovación no extiende el límite absoluto. La inactividad se refiere a solicitudes al servidor; no es un detector de presencia humana.
- Reautenticación dentro de cinco minutos para escrituras administrativas y cambios de perfil/sesiones. El usuario confirma identidad y vuelve a enviar la operación; no se repiten escrituras automáticamente.
- MFA requerido para administradores de clínica activos, administradores de plataforma, asignaciones de backoffice y cuentas con `is_staff`/`is_superuser` de Django. El rol de recepción `STAFF` de una clínica no equivale a ese indicador de Django. Al conceder privilegios, una sesión previa sin MFA deja de ser suficiente.
- El desafío previo a autenticar vence en cinco minutos, permite como máximo cinco verificaciones fallidas y queda ligado a la contraseña vigente. No emite tokens completos antes de verificar MFA.
- TOTP de seis dígitos y periodos de treinta segundos; tolerancia de un periodo y rechazo de códigos ya utilizados. La semilla se cifra con Fernet. Diez códigos de recuperación aleatorios se muestran una vez y se conservan mediante hashes.
- Restablecer contraseña conserva el segundo factor. La recuperación operativa de MFA invalida además la contraseña anterior, los desafíos y las sesiones para evitar que alguien con la contraseña anterior tome el nuevo enrolamiento.
- No se guardan tokens, semillas o códigos en localStorage/sessionStorage. Las respuestas de autenticación y documentos usan controles de no caché.

La revocación no puede retirar información ya entregada ni cancelar retroactivamente una solicitud cuya autorización ocurrió antes del cierre de sesión.

## Consentimiento y privacidad

La administración utiliza `/app/compliance`, con una clínica seleccionada, para publicar el aviso y las plantillas. Se exige nombre completo del responsable que publica y confirmación de revisión. Una casilla administrativa es una constancia de publicación, no una validación jurídica automática.

Los avisos requieren identidad y domicilio del responsable, contacto, datos sensibles, finalidades, mecanismos ARCO, revocación, limitación, transferencias, conservación y comunicación de cambios. La versión publicada se consulta también sin iniciar sesión en `/app/privacy/<identificador-de-clinica>`. Suspender una clínica no oculta el contacto de privacidad para sus pacientes anteriores.

Las plantillas de consentimiento clínico y tratamiento de datos son distintas. La de datos queda ligada a una versión del aviso. Un aviso actualizado exige publicar la plantilla de datos correspondiente antes de registrar evidencia nueva con ella. El servidor rechaza plantillas anteriores aunque el cliente conserve un formulario abierto.

El procedimiento preparado es **documento firmado adjunto registrado por el profesional**. Su habilitación requiere la publicación de plantillas revisadas; falta la validación del procedimiento por el responsable clínico/jurídico. No sustituye un proceso de aceptación electrónica autenticada si ese fuera el mecanismo seleccionado.

No se exige cargar una identificación completa en el nuevo flujo. La evidencia incluye firmante, paciente/representante, fundamento de representación cuando corresponda, fecha de firma declarada, profesional que registra y fecha de registro. El archivo original se conserva sin reconstrucción, con SHA-256 y un sello de metadatos. Se verifica la huella antes de descargarlo. La carga no demuestra automáticamente que una firma sea auténtica.

Una sustitución conserva el documento anterior. Una revocación crea un registro nuevo y conserva la evidencia; no borra el expediente ni demuestra por sí sola que una solicitud ARCO haya sido atendida íntegramente. La operación y resolución de esas solicitudes siguen necesitando responsables y procedimientos.

Los registros anteriores permanecen identificados como históricos sin firma verificada. No se convierten en evidencias nuevas ni se consideran automáticamente válidos por tener `fecha_aceptacion`.

## Integridad clínica y límites

- Las notas nuevas nacen como borradores. El cierre exige contraseña y, si existe, segundo factor; además del nombre completo del profesional. La impresión ordinaria de un borrador queda deshabilitada en la pantalla de receta.
- Las correcciones de notas cerradas se registran como adendas con autor, fecha y huella del documento de referencia. Los documentos históricos admiten adendas identificadas como tales, sin atribuir firma al original.
- Antecedentes y odontograma conservan versiones selladas. Si el contenido actual no coincide con su última revisión sellada, se rechaza la actualización y se requiere conciliación.
- PostgreSQL rechaza UPDATE/DELETE ordinarios sobre avisos, plantillas, evidencias, revocaciones, adendas, revisiones selladas y notas cerradas. Las revisiones históricas sin sello conservan la posibilidad de actualizar procedencia durante una migración controlada.
- Los modelos añaden restricciones ordinarias de edición; SQLite se conserva para pruebas/desarrollo y no reproduce todos los bloqueos SQL. La configuración de producción ahora exige PostgreSQL.
- Un HMAC permite detectar alteraciones del contenido vinculado a una clave bajo custodia. No es firma electrónica avanzada ni prueba independiente de no repudio. Un propietario SQL puede deshabilitar triggers; quien comprometa también las claves puede falsificar sellos. Se requieren privilegios mínimos, custodia externa, auditoría independiente y respaldos protegidos.

## Migraciones y preparación de despliegue

Migraciones incorporadas:

- `Usuarios/0010_mfacredential_authsession_mfachallenge`: sesiones, credenciales MFA y desafíos.
- `Pacientes/0030_clinicalrevision_actor_name_and_more`: versiones de avisos/plantillas, evidencias, metadatos y adendas.
- `Pacientes/0031_document_integrity_guards`: clasificación histórica y controles PostgreSQL.

Al migrar, las consultas existentes se marcan `LEGACY`, sin generar firmas ni sellos retrospectivos. Las fechas y datos anteriores se conservan. Las nuevas notas creadas después de la migración empiezan como borrador.

Antes de desplegar:

1. Verificar respaldo recuperable de base y objetos; ensayar actualización desde una copia controlada representativa. Las pruebas desde cero no sustituyen ese ensayo.
2. Instalar las dependencias declaradas, incluida `cryptography==50.0.2`; mantener Redis y su configuración de la etapa 1.
3. Provisionar en gestor externo `MFA_ENCRYPTION_KEYS`: claves Fernet separadas por comas, primera para cifrar y anteriores para descifrar durante rotación. No usar el valor local de pruebas.
4. Provisionar `DOCUMENT_SEAL_KEYS`: valores aleatorios de alta entropía, al menos 32 caracteres, primera clave para sellar y anteriores para verificar. No reutilizar claves de MFA ni retirarlas mientras se necesiten para documentos existentes.
5. Respaldar claves con acceso restringido y recuperación probada. Su pérdida puede impedir MFA o la verificación documental.
6. Detener escrituras durante la actualización, aplicar migraciones y arrancar todos los workers con configuración coherente. Los usuarios deberán iniciar sesión nuevamente; administradores deben completar MFA.
7. Revisar nombres profesionales, enrolamiento administrativo, datos jurídicos, versiones de textos y procedimiento de aceptación antes de registrar documentos reales.

No ejecutar una reversión de esquema después de registrar evidencias nuevas sin un plan de preservación: eliminar las tablas nuevas perdería sus referencias. La vuelta a código anterior elimina controles de revocación/MFA; requiere evaluación explícita de riesgo. No se ejecutó reversión ni migración sobre datos reales.

## Recuperación operativa de MFA

El comando `reset_account_mfa` está disponible únicamente por operación en el servidor. No se expone como endpoint web y no se ejecutó sobre cuentas reales.

```bash
python manage.py reset_account_mfa USUARIO --confirm-username USUARIO --reason "Referencia de autorización y revisión externa"
```

Exige confirmación exacta y cuenta activa con correo único. Debe precederlo una verificación externa del titular y autorización documentada; la herramienta no puede comprobar esas acciones. Invalida contraseña anterior y sesiones, retira MFA y deja un evento de auditoría cuya referencia debe asociarse al expediente de autorización. No muestra la contraseña aleatoria ni envía correos. El titular deberá usar recuperación de contraseña y volver a enrolar MFA. El operador no debe facilitar el nuevo acceso a quien solo conozca la contraseña anterior.

## Validación

- Suite backend completa con PostgreSQL temporal y Redis: **280 pruebas aprobadas, sin omisiones**. Retests posteriores de 21, 25, 11 y 12 pruebas cubrieron campos opcionales, autenticación, origen de sesión, configuración de producción, aviso de clínica suspendida e identificadores malformados; todos aprobados. La prueba adicional de origen se añadió después de la ejecución completa.
- Suite completa SQLite temporal y Redis: **280 pruebas aprobadas, 22 omitidas** según capacidades del motor.
- Frontend: **57 pruebas aprobadas**; typecheck, lint y build correctos. Build conserva aviso de tamaño de un chunk; no es un hallazgo de seguridad por sí mismo.
- Playwright completo: **12 pruebas aprobadas**, con servidor SQLite/E2E aislado y navegador Chromium/Edge headless. Incluye enrolamiento TOTP real, recuperación de un solo uso, revocación inmediata, publicación pública de avisos, flujo clínico, documento firmado adjunto, cierre, multiclínica y recuperación de contraseña.
- Se corrigieron durante el retest una carrera de carga del formulario de aviso, campos opcionales vacíos de cierre/reautenticación y contratos de pruebas que esperaban el flujo anterior. Se conservó el límite de consultas para impedir una consulta por adenda o nota en el listado.
- `makemigrations --check --dry-run`: sin cambios pendientes. `git diff --check` y control de categorías sensibles del índice: correctos.
- Escaneo Python final: 104 paquetes inventariados, cero avisos en los auditables y sin diferencias con las versiones declaradas. Se omitieron las variantes CPU de Torch/Torchvision; consulta complementaria de sus versiones públicas: cero avisos. `pip check`: sin conflictos. Esto no valida los binarios CPU ni el sistema operativo del contenedor.
- Gitleaks del árbol de trabajo, con el mismo alcance y salida redactada de la etapa 1: cero hallazgos en la comprobación final. El historial sigue pendiente de saneamiento cuando corresponda; este escaneo no clasifica datos personales.

No se verificaron TLS real, entrega SMTP real, protección de ramas ni operación regulatoria. No se utilizaron datos reales ni se enviaron mensajes externos. El correo E2E se guardó en un directorio temporal local.

Referencias técnicas: [RFC 6238](https://www.rfc-editor.org/rfc/rfc6238), [Fernet y rotación de claves](https://cryptography.io/en/latest/fernet/). El marco jurídico y los pendientes de certificación continúan en el [informe original](auditoria-mexico-2026-11-08.md).
