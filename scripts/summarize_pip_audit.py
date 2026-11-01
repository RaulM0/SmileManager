"""Render pip-audit JSON without embedding credentials or application data."""
import json
import sys

with open(sys.argv[1], encoding='utf-8') as source:
    data = json.load(source)
print('# pip-audit: dependencias instaladas')
print('\nSalida de pip-audit 2.10.1; los identificadores pueden solaparse entre fuentes. Severidad no proporcionada por esta salida. Los parches indicados son por advisory, no garantizan resolver todos los avisos del paquete.\n')
print('| Paquete | Versión | Advisory | Versiones corregidas |')
print('|---|---|---|---|')
for dependency in data['dependencies']:
    for vulnerability in dependency.get('vulns', []):
        fixes = ', '.join(vulnerability.get('fix_versions', [])) or 'No indicada'
        print(f"| {dependency['name']} | {dependency['version']} | {vulnerability['id']} | {fixes} |")
