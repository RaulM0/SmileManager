"""Static inventory; every inferred control still requires dynamic review."""
import ast
from pathlib import Path

groups = [('Home', '/home/'), ('Sesiones', '/sesiones/'), ('Pacientes', '/registroPacientes/'), ('Citas', '/menu_citas/'), ('DiagnosticosIA', '/diagnosticos/')]
audit_source = Path('api/audit.py').read_text(encoding='utf-8')
print('# Matriz estática de rutas HTML\n')
print('Generada con `python scripts/inventory_legacy_routes.py`; es inventario estático, no prueba de comportamiento. Middleware de sesión y CSRF aplican según configuración; cada celda marcada revisar requiere prueba. Consumidor externo desconocido.\n')
print('| Ruta | Métodos | Auth | CSRF | Ownership | Write | Servicio | Audit | Versión | Archivos | Consumidor | Estado |')
print('|---|---|---|---|---|---|---|---|---|---|---|---|')
for app, prefix in groups:
    routes = ast.parse(Path(app, 'urls.py').read_text(encoding='utf-8'))
    views = ast.parse(Path(app, 'views.py').read_text(encoding='utf-8'))
    functions = {f.name: f for f in views.body if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))}
    for node in ast.walk(routes):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != 'path' or len(node.args) < 2:
            continue
        path = ast.literal_eval(node.args[0])
        view = node.args[1]
        if not isinstance(view, ast.Attribute):
            continue
        fn = functions.get(view.attr)
        if fn is None:
            continue
        source = ast.unparse(fn)
        keywords = {item.arg: item.value for item in node.keywords}
        name = ast.literal_eval(keywords['name']) if 'name' in keywords else ''
        method = 'POST' if 'require_POST' in source else 'GET' if 'require_GET' in source else 'GET/POST u otros: revisar'
        write = 'POST: revisar' if any(t in source for t in ('.save(', '.create(', '.delete(', '.update(', 'send_mail(', 'save_record(', 'save_appointment(', 'transition_appointment(', 'execute_analysis(')) else 'No detectada*'
        ownership = 'scoped/owned*' if any(t in source for t in ('scoped(', 'owned_or_404(', 'consistent_or_404(')) else 'revisar/NA'
        service = 'Sí*' if any(t in source for t in ('save_record(', 'save_appointment(', 'transition_appointment(', 'PatientSerializer(', 'deactivate_patient(', 'execute_analysis(')) else 'revisar/NA'
        audit = 'mapeado*' if f"('{name}'," in audit_source else 'revisar/NA'
        version = 'save_record*' if 'save_record(' in source else 'revisar/NA'
        files = 'revisar*' if any(t in source for t in ('FILES', 'FileResponse', 'storage', 'pdf_', 'imagen', 'archivo')) else 'no detectado*'
        print(f'| `{prefix}{path}` | {method} | middleware* | middleware* | {ownership} | {write} | {service} | {audit} | {version} | {files} | desconocido | BLOCKED |')
