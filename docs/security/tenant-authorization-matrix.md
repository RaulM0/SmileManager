# Autorización por clínica: estado de implementación

La siguiente matriz describe únicamente los controles nuevos, no el comportamiento de todas las rutas existentes.

| Operación implementada                                    | Administrador activo de clínica activa | Médico o personal activos    | Sin membresía vigente |
| --------------------------------------------------------- | -------------------------------------- | ---------------------------- | --------------------- |
| Enumerar clínicas propias activas                         | Sí                                     | Sí                           | No                    |
| Validar contexto propio                                   | Sí                                     | Sí                           | No                    |
| Cambiar rol o estado de una membresía de la misma clínica | Sí, con restricciones abajo            | No                           | No                    |
| Consulta clínica mediante la función de política nueva    | No por el rol administrativo           | Médico asignado; personal no | No                    |

Los cambios de membresía se serializan mediante bloqueo de la clínica, verifican el rol actual en base de datos y generan un evento de auditoría en la misma transacción. No se permite eliminar al último administrador activo mediante esta operación, asignar `PLATFORM_ADMIN`, ni reactivar una membresía que no tenga aceptación registrada. Una membresía revocada requiere una nueva invitación aceptada. Estas garantías no cubren modificaciones directas en SQL o por código que ignore este servicio.

Las rutas clínicas heredadas no aplican esta matriz: la política compartida heredada excluye recursos asignados a clínica y usuarios que tienen o tuvieron membresías, pero aún hay que auditar toda vía directa. El backoffice clínico global y la lectura de modelos clínicos en Django Admin responden con denegación, incluidos los superusuarios, hasta implementar acceso excepcional autorizado y auditado. El acceso operativo del backoffice permanece separado. No habilitar uso multiclínica hasta implementar y probar todas las vías de acceso y escritura.

La API adicional `clinics/patients/` aplica la capacidad clínica de médico a listado, detalle, creación y actualización; también exige asignación al médico para registros existentes y genera eventos de auditoría con clínica. La clínica en un cuerpo de petición se rechaza y la de creación se obtiene del contexto validado. Las rutas anteriores permanecen fuera de esta protección.

`clinics/appointments/` aplica esa capacidad y exige que la cita y su paciente pertenezcan a la clínica. Los endpoints de antecedentes y odontograma bajo `clinics/patients/` verifican al paciente asignado, preservan versiones y registran la clínica de las revisiones nuevas. Las consultas se crean y leen mediante rutas `clinics/` con el paciente autorizado y bloqueado durante la creación. Ninguno de estos endpoints concede acceso clínico al administrador por su rol administrativo.

Las rutas `clinics/patients/<id>/clinical-images/` y `clinics/clinical-images/<id>/` permiten subir y leer imágenes del paciente asignado; las descargas comprueban el contexto antes de abrir storage. Un resultado requiere una ejecución exitosa de la misma clínica y se bloquea si hay procedencia contradictoria. La inferencia multitenant ejecuta el modelo sin publicar archivos y vuelve a comprobar clínica, usuario, membresía y recurso bajo bloqueo antes de publicar el resultado. La revocación o suspensión durante la inferencia impide esa publicación.
