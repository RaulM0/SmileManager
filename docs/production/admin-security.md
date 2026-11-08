# Administración y seguridad

La interfaz Django Admin no está instalada ni publicada. Las rutas `/admin/` devuelven 404, incluso para un superusuario; no existe un bypass web mediante Django Admin. El rol explícito `PlatformAdmin` y la administración por clínica se gestionan mediante las APIs y el backoffice React, con sus comprobaciones y auditoría. Ser `is_staff` o `is_superuser` no concede el rol de plataforma.

Esta eliminación no protege frente a acceso privilegiado al ORM, a comandos, a la base de datos o al almacenamiento. Esos accesos requieren control operacional independiente. El arranque de roles de plataforma utiliza el procedimiento documentado en [tenant-onboarding.md](../operations/tenant-onboarding.md).
