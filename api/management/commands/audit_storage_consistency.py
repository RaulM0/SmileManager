import hashlib

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from Pacientes.models import Consentimiento, EstudioComparativo, ImagenesClinicas
from DiagnosticosIA.models import AIAnalysisRun


FIELDS = {
    ImagenesClinicas: ('imagen', 'resultados'),
    EstudioComparativo: ('antes_oclusal_superior', 'antes_lateral_izquierda', 'antes_frontal', 'antes_lateral_derecha', 'antes_oclusal_inferior', 'despues_perfil', 'despues_semiperfil', 'despues_retrato_frontal', 'despues_retrato_sonrisa'),
    Consentimiento: ('archivo_ine', 'pdf_generado'),
}


class Command(BaseCommand):
    help = 'Auditoría de storage de solo lectura; no elimina archivos.'

    def add_arguments(self, parser):
        parser.add_argument('--max-references', type=int, default=500)
        parser.add_argument('--include-orphans', action='store_true')
        parser.add_argument('--max-objects', type=int, default=5000)

    def handle(self, *args, **options):
        limit = options['max_references']
        if limit < 1 or options['max_objects'] < 1:
            raise CommandError('Los límites deben ser positivos.')
        references = set()
        scanned = missing = 0
        truncated = False
        for model, fields in FIELDS.items():
            for field in fields:
                for pk, name in model.objects.exclude(**{field: ''}).exclude(**{field + '__isnull': True}).values_list('pk', field).iterator(chunk_size=500):
                    if scanned >= limit:
                        truncated = True
                        break
                    scanned += 1
                    references.add(name)
                    if not default_storage.exists(name):
                        missing += 1
                        self.stdout.write(f'MISSING category={model.__name__}.{field} id={pk}')
                if truncated:
                    break
            if truncated:
                break
        if not truncated:
            for pk, name in AIAnalysisRun.objects.exclude(result_name='').values_list('pk', 'result_name').iterator(chunk_size=500):
                if scanned >= limit:
                    truncated = True
                    break
                scanned += 1
                references.add(name)
                if not default_storage.exists(name):
                    missing += 1
                    self.stdout.write(f'MISSING category=AIAnalysisRun.result_name id={pk}')
        self.stdout.write(f'REFERENCES checked={scanned} missing={missing} truncated={str(truncated).lower()}')
        if options['include_orphans']:
            if truncated:
                raise CommandError('Referencias truncadas: no es seguro clasificar huérfanos. Aumente --max-references.')
            prefixes = {model._meta.get_field(field).upload_to.rstrip('/') for model, fields in FIELDS.items() for field in fields}
            stack = list(prefixes)
            visited = set()
            objects = orphans = 0
            while stack:
                prefix = stack.pop()
                if prefix in visited:
                    continue
                if len(visited) >= options['max_objects']:
                    self.stdout.write(f'OBJECTS checked={objects} orphans={orphans} truncated=true')
                    return
                visited.add(prefix)
                try:
                    dirs, files = default_storage.listdir(prefix)
                except FileNotFoundError:
                    continue
                stack.extend(prefix + '/' + name for name in dirs)
                for name in files:
                    if objects >= options['max_objects']:
                        self.stdout.write(f'OBJECTS checked={objects} orphans={orphans} truncated=true')
                        return
                    objects += 1
                    key = prefix + '/' + name
                    if key not in references:
                        orphans += 1
                        self.stdout.write('POTENTIAL_ORPHAN key_sha256=' + hashlib.sha256(key.encode()).hexdigest())
            self.stdout.write(f'OBJECTS checked={objects} orphans={orphans} truncated=false')
