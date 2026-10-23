# Modelo de datos

| Modelo | Relaciones y propósito |
|---|---|
| auth.User | médico/autenticación |
| Usuarios.Perfil | OneToOne User; clínica, teléfono, dirección, notas |
| Paciente | FK médico SET_NULL; identidad, contacto, estado; uniques `(telefono, medico)`, `(email, medico)` |
| AntescedentesMedicos | FK paciente y médico; 26 indicadores y cuatro textos |
| Consulta | FK paciente y médico; fecha, motivo, diagnóstico, tratamiento, observaciones |
| ImagenesClinicas | FK paciente, consulta opcional y médico; original y resultado |
| Odontograma | FK paciente/médico; tres JSON y timestamps |
| EstudioComparativo | FK paciente/médico; metadatos, cinco fotos antes, cuatro después |
| Consentimiento | FK paciente/médico; texto, aceptación, INE y PDF reservado |
| Cita | FK paciente; fecha/hora, motivo, estado P/C/A, observaciones |

No se planean cambios de esquema para la primera migración. El aislamiento se refuerza en querysets/permisos API. Las migraciones legacy se preservan; `0018` fue reparada previamente con `SeparateDatabaseAndState` por columnas duplicadas entre ramas.
