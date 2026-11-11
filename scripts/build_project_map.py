"""Build Obsidian navigation from source paths and static imports, without executing code."""
import argparse
import ast
import json
import posixpath
from pathlib import Path
import re
import subprocess
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/mapa'
GROUPS = {
    'Configuracion': ('SmileManager', 'Configuración Django, rutas y entornos.'),
    'Usuarios': ('Usuarios', 'Cuentas, clínicas, membresías, sesiones y auditoría.'),
    'Pacientes': ('Pacientes', 'Expediente, consultas y documentos clínicos.'),
    'Agenda': ('Citas', 'Citas, transiciones y recordatorios.'),
    'Inteligencia artificial': ('DiagnosticosIA', 'Análisis de imágenes y seguimiento de ejecuciones.'),
    'API y seguridad': ('api', 'Endpoints, autorización, servicios y controles de seguridad.'),
    'Interfaz': ('frontend', 'React, navegación, contexto y servicios HTTP.'),
    'Operacion': ('scripts', 'Herramientas, contenedores, respaldos y operación local.'),
}
EXTENSIONS = {'.py', '.ts', '.tsx', '.js', '.css', '.html', '.sh'}
EXACT = {'compose.yaml', 'Dockerfile', 'requirements.txt', 'frontend/package.json', 'frontend/vite.config.ts', 'frontend/playwright.config.js'}


def slug(path):
    # JSON quoting inside frontmatter keeps special characters literal.
    return quote(path, safe='').replace('%', '_') + '.md'


def group(path):
    if path.startswith(('docker/', 'scripts/')) or path in EXACT and not path.startswith('frontend/'):
        return 'Operacion'
    return next((name for name, (prefix, _) in GROUPS.items() if path.startswith(prefix + '/')), None)


def link(path, label=None):
    return f'[[docs/mapa/archivos/{slug(path)[:-3]}|{label or path}]]'


def read_source(path, staged=False):
    if staged:
        return subprocess.check_output(['git', 'show', ':' + path], cwd=ROOT).decode('utf-8')
    return (ROOT / path).read_text(encoding='utf-8')


def discover(staged=False):
    if staged:
        output = subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=ROOT)
        candidates = []
        for entry in output.split(b'\0'):
            if not entry:
                continue
            metadata, raw = entry.split(b'\t', 1)
            mode, _, stage = metadata.split()
            if stage != b'0':
                raise RuntimeError('Resolve index conflicts before updating the map.')
            if mode in (b'100644', b'100755'):
                candidates.append(raw.decode())
    else:
        output = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT)
        candidates = [raw.decode() for raw in output.split(b'\0') if raw]
    paths = set()
    for path in candidates:
        file = ROOT / path
        if not group(path) or (not staged and (not file.is_file() or file.is_symlink())):
            continue
        if path in EXACT or file.suffix in EXTENSIONS:
            paths.add(path)
    return sorted(paths)


def inspect(path, known, staged=False):
    text = read_source(path, staged)
    symbols, imports = [], set()
    if path.endswith('.py'):
        tree = ast.parse(text)
        for item in tree.body:
            if isinstance(item, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                symbols.append((item.name, item.lineno))
        package = path[:-3].split('/')[:-1]
        for item in ast.walk(tree):
            if isinstance(item, ast.Import):
                modules = [alias.name.split('.') for alias in item.names]
            elif isinstance(item, ast.ImportFrom):
                base = package[:len(package) - item.level + 1] if item.level else []
                module = base + (item.module.split('.') if item.module else [])
                modules = [module] + [module + [alias.name] for alias in item.names]
            else:
                continue
            for module in modules:
                for candidate in ('/'.join(module) + '.py', '/'.join(module) + '/__init__.py'):
                    if candidate in known and candidate != path:
                        imports.add(candidate)
    elif path.endswith(('.ts', '.tsx', '.js')):
        symbols = [(match.group(1), text[:match.start()].count('\n') + 1) for match in re.finditer(
            r'^(?:export\s+)?(?:default\s+)?(?:async\s+)?(?:function|class|interface|type|const)\s+(\w+)', text, re.M)]
        for match in re.finditer(r'''(?:from\s*|import\s*\(?\s*)['"](\.[^'"]+)['"]''', text):
            base = posixpath.normpath(posixpath.join(posixpath.dirname(path), match.group(1)))
            for candidate in [base] + [base + ext for ext in ('.ts', '.tsx', '.js')] + [base + '/index' + ext for ext in ('.ts', '.tsx', '.js')]:
                if candidate in known and candidate != path:
                    imports.add(candidate)
    return symbols, sorted(imports)


def render(staged=False):
    paths = discover(staged)
    known = set(paths)
    result = {}
    buckets = {name: [] for name in GROUPS}
    for path in paths:
        section = group(path)
        buckets[section].append(path)
        symbols, imports = inspect(path, known, staged)
        name = Path(path).name
        lines = ['---', 'generated: true', f'source: {json.dumps(path)}', f'aliases: [{json.dumps(path)}]', 'tags: [mapa, archivo]', '---',
                 f'# {name}', '', f'Módulo: [[docs/mapa/{section}]]. Inicio: [[docs/mapa/Inicio]].', '', '## Archivo real', '',
                 f'Ruta desde la raíz: `{path}`.', '', f'[Abrir archivo del proyecto](../../../{quote(path, safe="/")})', '',
                 'El enlace apunta al código original. Según el tipo de archivo, Obsidian lo abrirá o permitirá abrirlo con la aplicación predeterminada. Esta nota es un índice; leer el archivo real antes de modificarlo.', '', '## Símbolos principales', '']
        lines += [f'- `{name}` — línea {number}.' for name, number in symbols] or ['Sin declaraciones principales detectadas por el índice estático.']
        lines += ['', '## Dependencias internas', '']
        lines += [f'- {link(item)}' for item in imports] or ['Sin imports internos resueltos automáticamente.']
        lines += ['', 'Este índice resuelve imports Python y referencias relativas JS/TS; no ejecuta módulos ni representa todas las dependencias dinámicas.', '']
        result['archivos/' + slug(path)] = '\n'.join(lines)
    for section, (_, description) in GROUPS.items():
        lines = ['---', 'generated: true', 'tags: [mapa, modulo]', '---', f'# {section}', '', description, '', 'Volver a [[docs/mapa/Inicio]]. Consultar también [[docs/mapa/Como usar el mapa]].', '', '## Archivos', '']
        lines += [f'- {link(path)}' for path in buckets[section]]
        result[section + '.md'] = '\n'.join(lines) + '\n'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if the generated map is stale or references missing files.')
    args = parser.parse_args()
    output = render()
    stale = []
    for name, text in output.items():
        target = OUT / name
        if not target.exists() or target.read_text() != text:
            stale.append(name)
            if not args.check:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text)
    existing = set((OUT / 'archivos').glob('*.md'))
    expected = {OUT / name for name in output if name.startswith('archivos/')}
    extra = existing - expected
    if extra:
        # Preserve notes for removed files for review; never silently delete manual work.
        stale.extend(str(file.relative_to(OUT)) for file in extra)
        print('Obsolete file notes require review: ' + ', '.join(str(file.relative_to(OUT)) for file in extra))
    print(f'Map: {len(output) - len(GROUPS)} source files, {len(GROUPS)} modules; ' + ('current' if not stale else f'{len(stale)} entries updated or stale'))
    if args.check and stale:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
