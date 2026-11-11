---
tags: [mapa, inicio]
---
# SmileManager — mapa del proyecto

Este mapa conecta módulos, archivos y documentación. Abre **la raíz de SmileManager** como bóveda de Obsidian para que los enlaces al código permanezcan dentro de la bóveda.

Arquitectura y límites actuales: [[docs/architecture/module-boundaries]].

## Recorrer por responsabilidad

- [[docs/mapa/Configuracion]]: rutas Django y configuración por entorno.
- [[docs/mapa/Usuarios]]: cuentas, clínicas, sesiones, MFA y auditoría.
- [[docs/mapa/Pacientes]]: expediente y documentos clínicos.
- [[docs/mapa/Agenda]]: citas y recordatorios.
- [[docs/mapa/Inteligencia artificial]]: ejecuciones de análisis.
- [[docs/mapa/API y seguridad]]: endpoints, políticas y servicios.
- [[docs/mapa/Interfaz]]: pantallas, contexto y llamadas HTTP.
- [[docs/mapa/Operacion]]: contenedores, herramientas y respaldos.

## Encontrar una tarea

- Acceso y permisos: [[docs/mapa/Usuarios]] → [[docs/mapa/API y seguridad]] → [[docs/security/authorization-model]].
- Consultas y documentos: [[docs/mapa/Pacientes]] → [[docs/architecture/clinical-integrity]] → [[docs/security/etapa-2-resultados]].
- Archivos y antivirus: [[docs/mapa/API y seguridad]] → [[docs/security/upload-policy]] → [[docs/security/etapa-3-resultados]].
- Arranque y respaldo: [[docs/mapa/Operacion]] → [[docs/operations/docker-local]] → [[docs/operations/etapa-3-local]].
- Cambios de interfaz: [[docs/mapa/Interfaz]] → sus componentes, servicios y pruebas.

## Usar y mantener

Consulta [[docs/mapa/Como usar el mapa]]. Los nodos de archivo incluyen ruta real, símbolos con línea y enlaces hacia imports internos detectados estáticamente. El código es la fuente de verdad. No se incluyen datos clínicos, claves ni contenido de archivos de configuración privados.
