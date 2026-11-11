from django.db import migrations


IMMUTABLE_TABLES = (
    'Pacientes_privacynotice', 'Pacientes_consenttemplate', 'Pacientes_consentevidence',
    'Pacientes_consentrevocation', 'Pacientes_consultationaddendum', 'Pacientes_clinicalrevision',
)


def install(apps, schema_editor):
    # No historical note is retrospectively signed or attested.
    apps.get_model('Pacientes', 'Consulta').objects.filter(status='DRAFT').update(status='LEGACY')
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute("""CREATE FUNCTION smile_immutable_document() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF TG_TABLE_NAME = 'Pacientes_clinicalrevision' AND OLD.integrity_seal = '' AND TG_OP = 'UPDATE' THEN RETURN NEW; END IF;
          RAISE EXCEPTION 'Document is immutable; create a new version or addendum';
        END; $$""")
    for table in IMMUTABLE_TABLES:
        schema_editor.execute(f'CREATE TRIGGER smile_immutable BEFORE UPDATE OR DELETE ON "{table}" FOR EACH ROW EXECUTE FUNCTION smile_immutable_document()')
    schema_editor.execute("""CREATE FUNCTION smile_closed_consultation() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF OLD.status = 'CLOSED' THEN RAISE EXCEPTION 'Closed consultation is immutable'; END IF;
          IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
          RETURN NEW;
        END; $$""")
    schema_editor.execute('CREATE TRIGGER smile_closed BEFORE UPDATE OR DELETE ON "Pacientes_consulta" FOR EACH ROW EXECUTE FUNCTION smile_closed_consultation()')


def uninstall(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    for table in IMMUTABLE_TABLES:
        schema_editor.execute(f'DROP TRIGGER IF EXISTS smile_immutable ON "{table}"')
    schema_editor.execute('DROP TRIGGER IF EXISTS smile_closed ON "Pacientes_consulta"')
    schema_editor.execute('DROP FUNCTION IF EXISTS smile_closed_consultation()')
    schema_editor.execute('DROP FUNCTION IF EXISTS smile_immutable_document()')


class Migration(migrations.Migration):
    dependencies = [('Pacientes', '0030_clinicalrevision_actor_name_and_more')]
    operations = [migrations.RunPython(install, uninstall)]
