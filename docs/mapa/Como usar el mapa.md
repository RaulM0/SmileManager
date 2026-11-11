# Cómo usar el mapa

## Abrir y ver el grafo

1. En Obsidian, elige **Abrir carpeta como bóveda** y selecciona `/home/raul/repos/SmileManager` (la raíz del repositorio, no únicamente `docs/`).
2. Abre [[docs/mapa/Inicio]] mediante el selector rápido (`Ctrl+O`).
3. Abre **Vista de grafo** desde la barra lateral o la paleta de comandos. La configuración inicial filtra `path:docs/mapa`: aparecen módulos y archivos, con vínculos entre sus dependencias.
4. Para explorar un área, abre su nota y utiliza el **grafo local**, inicialmente con profundidad 1. Amplía la profundidad para seguir relaciones.
5. Borra el filtro del grafo si quieres incluir las auditorías y el resto de la documentación.

No hacen falta plugins comunitarios. La configuración se aplica a esta bóveda; las preferencias personales de otras bóvedas no se cambian. Las exclusiones reducen ruido visual; no son controles de acceso ni una política de sincronización. Mantén el repositorio local y no publiques o sincronices su contenido completo sin revisar qué se incluye.

## Buscar y leer archivos

Busca con `Ctrl+O` un nombre o ruta como `api/authentication.py`; las notas tienen la ruta completa como alias. Para buscar símbolos, usa la búsqueda global y escribe `path:docs/mapa Authentication` o el nombre concreto de una clase o función.

Cada nota de archivo muestra:

- Ruta relativa desde la raíz del repositorio.
- Enlace al archivo real, que Obsidian puede abrir o enviar a la aplicación predeterminada según su tipo y la configuración del equipo.
- Clases y funciones principales con sus líneas actuales.
- Dependencias internas reconocidas por el generador.

Si el sistema no tiene una aplicación asociada al archivo, ábrelo desde tu editor usando la ruta indicada. El mapa no incorpora un editor de código ni garantiza que Obsidian pueda mostrar todos los formatos.

## Referencia para el asistente

Puedes pedir: «Consulta el mapa de Usuarios y localiza dónde se revocan sesiones». El asistente debe comenzar por los índices, seguir las rutas relevantes y leer el código original y las instrucciones aplicables antes de editar. El grafo ayuda a localizar; no sustituye la revisión del código ni demuestra cobertura completa de dependencias.

## Actualizar

Desde la raíz:

```sh
python3 scripts/build_project_map.py
python3 scripts/build_project_map.py --check
```

El generador considera archivos de código de Git y archivos nuevos no ignorados dentro de los módulos permitidos. No copia el código ni ejecuta imports. Regenera índices de módulos y notas de archivo; edita las explicaciones manuales en `Inicio.md` o en otras notas propias. Informa notas de archivos eliminados para revisarlas sin borrarlas automáticamente.

Las relaciones provienen de imports Python y rutas relativas JS/TS. No resuelve todas las dependencias dinámicas, aliases de compilador, endpoints HTTP, consultas ORM ni llamadas entre procesos. Las notas de migraciones y pruebas también aparecen; usa el grafo local para reducir el ruido.


## Hook de Codex para commits

La configuración versionada está en `codex/hooks.json`. El hook `PreToolUse` adapta los comandos de Git de Codex y activa `.githooks/pre-commit` únicamente en los commits de este repositorio, sin configurar `core.hooksPath` global ni localmente.

Para iniciar Codex con el hook cargado:

```sh
python3 scripts/codex_with_obsidian.py
```

El lanzador pasa la configuración nativa mediante `-c hooks.PreToolUse=...`. En `/hooks`, revisa y confía la definición; en la aplicación, esa revisión aparece en Settings → Hooks. El entorno actual protege `.codex/` contra escritura: la configuración ya está creada en `codex/hooks.json`, pero no quedó instalada automáticamente en `.codex/hooks.json`. Si deseas el descubrimiento automático en otras sesiones, instala esa configuración como `.codex/hooks.json` desde una terminal con acceso de escritura y vuelve a abrir Codex. Conserva e integra cualquier hook existente.

El adaptador también puede usarse directamente:

```sh
python3 scripts/codex_git.py commit -m "Describe el cambio"
```

El mapa incluido en el commit se genera desde el índice de Git, incluyendo el preparado automático de `commit --all`. No agrega código sin preparar. Conserva las modificaciones locales de notas y elimina del índice únicamente notas generadas cuyos archivos de origen se eliminaron. Si hay cambios locales de notas conservados, el contenido del mapa en disco puede diferir del incluido en el commit; puedes regenerar el mapa del espacio de trabajo después.

La adaptación cubre comandos normales `git ...` en el shell del evento. Ejecutables absolutos, `command git`, shells anidados, otras herramientas Git, hooks deshabilitados/no confiados y `--no-verify` pueden evitarla. Es automatización de trabajo, no una barrera de seguridad. Las instrucciones de `AGENTS.md` exigen el adaptador también cuando el hook todavía no está activado.

Pruebas aisladas:

```sh
python3 -m unittest discover -s scripts/tests -p test_codex_obsidian_hooks.py -v
```

Referencia: [Hooks de Codex — documentación oficial](https://learn.chatgpt.com/docs/hooks).
