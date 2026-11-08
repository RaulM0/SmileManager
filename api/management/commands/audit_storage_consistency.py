import hashlib
from functools import reduce
from operator import or_
from uuid import UUID

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from Pacientes.models import Consentimiento, EstudioComparativo, ImagenesClinicas
from DiagnosticosIA.models import AIAnalysisRun
from Usuarios.models import Clinic


FIELDS = {
    ImagenesClinicas: ('imagen', 'resultados'),
    EstudioComparativo: ('antes_oclusal_superior', 'antes_lateral_izquierda', 'antes_frontal', 'antes_lateral_derecha', 'antes_oclusal_inferior', 'despues_perfil', 'despues_semiperfil', 'despues_retrato_frontal', 'despues_retrato_sonrisa'),
    Consentimiento: ('archivo_ine', 'pdf_generado'),
}


def referenced_anywhere(name):
    """A tenant scan must never classify a cross-linked key as orphaned."""
    return any(model.objects.filter(reduce(or_, (Q(**{field: name}) for field in fields))).exists()
               for model, fields in FIELDS.items()) or AIAnalysisRun.objects.filter(result_name=name).exists()


class Command(BaseCommand):
    help = 'Auditoría de storage de solo lectura; no elimina archivos.'

    def add_arguments(self, parser):
        scope = parser.add_mutually_exclusive_group(required=True)
        scope.add_argument('--clinic-id')
        scope.add_argument('--all-clinics', action='store_true')
        parser.add_argument('--max-references', type=int, default=500)
        parser.add_argument('--include-orphans', action='store_true')
        parser.add_argument('--max-objects', type=int, default=5000)

    def handle(self, *args, **options):
        clinic_id = None
        if options['clinic_id']:
            try:
                clinic_id = UUID(options['clinic_id'])
            except (ValueError, TypeError, AttributeError) as exc:
                raise CommandError('Invalid clinic UUID.') from exc
            if not Clinic.objects.filter(pk=clinic_id).exists():
                raise CommandError('Clinic does not exist.')
        limit = options['max_references']
        if limit < 1 or options['max_objects'] < 1:
            raise CommandError('Los límites deben ser positivos.')
        references = set()
        scanned = missing = 0
        truncated = False
        for model, fields in FIELDS.items():
            for field in fields:
                rows = model.objects.exclude(**{field: ''}).exclude(**{field + '__isnull': True})
                if clinic_id is not None:
                    rows = rows.filter(paciente__clinic_id=clinic_id)
                for pk, name in rows.values_list('pk', field).iterator(chunk_size=500):
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
            runs = AIAnalysisRun.objects.exclude(result_name='')
            if clinic_id is not None:
                runs = runs.filter(clinic_id=clinic_id)
            for pk, name in runs.values_list('pk', 'result_name').iterator(chunk_size=500):
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
            if clinic_id is None:
                prefixes = {upload_to.rstrip('/') for model, fields in FIELDS.items() for field in fields
                            if isinstance((upload_to := model._meta.get_field(field).upload_to), str)}
                prefixes.update(('imagenes_clinicas', 'resultados', 'estudios/antes', 'estudios/despues', 'consentimientos/ine', 'consentimientos/pdf', 'tenants'))
            else:
                # Historical keys without this prefix cannot be classified by clinic.
                prefixes = {f'tenants/{clinic_id}'}
                self.stdout.write('ORPHAN_SCOPE tenant_prefix_only=true')
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
                    if key not in references and (clinic_id is None or not referenced_anywhere(key)):
                        orphans += 1
                        self.stdout.write('POTENTIAL_ORPHAN key_sha256=' + hashlib.sha256(key.encode()).hexdigest())
            self.stdout.write(f'OBJECTS checked={objects} orphans={orphans} truncated=false')
