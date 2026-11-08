# Backoffice de SmileManager

El backoffice permite crear usuarios, conceder explícitamente acceso de backoffice al crearlos y activar o desactivar cuentas con auditoría. La recuperación de contraseña sigue disponible desde la aplicación React.

El acceso requiere la asignación explícita de `Usuarios.access_system_backoffice` o un administrador de plataforma activo. `is_staff` y el estado de superusuario no conceden por sí solos esta capacidad. Las cuentas administrativas están protegidas contra desactivación desde este panel.

La consulta y escritura clínica global están bloqueadas, incluidas las rutas heredadas de edición de pacientes, antecedentes, odontograma y transiciones de citas. El permiso de backoffice no permite omitir el contexto de clínica ni la asignación al profesional. Django Admin y las interfaces HTML heredadas no se publican.

La administración de plataforma requiere su rol explícito e incluye alta y estado de clínicas e invitaciones del administrador inicial. El acceso de backoffice por sí solo no concede el rol de plataforma.

Las listas de auditoría e IA del backoffice exponen únicamente los metadatos administrativos permitidos. No se almacenan contraseñas ni tokens en auditoría.

Véanse [preparación multitenant](../production/multitenancy-readiness.md), [matriz de autorización](../security/tenant-authorization-matrix.md) y [alta de clínicas](../operations/tenant-onboarding.md) para los límites y validaciones pendientes.
