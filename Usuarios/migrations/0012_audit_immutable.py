from django.db import migrations


def install(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute("""CREATE FUNCTION smile_immutable_audit() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN RAISE EXCEPTION 'Audit events are append-only'; END; $$""")
        schema_editor.execute('CREATE TRIGGER smile_audit_guard BEFORE UPDATE OR DELETE ON "Usuarios_auditevent" FOR EACH ROW EXECUTE FUNCTION smile_immutable_audit()')


def uninstall(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute('DROP TRIGGER IF EXISTS smile_audit_guard ON "Usuarios_auditevent"')
        schema_editor.execute('DROP FUNCTION IF EXISTS smile_immutable_audit()')


class Migration(migrations.Migration):
    dependencies = [('Usuarios', '0011_fileinspection_auditevent_content_sha256_and_more')]
    operations = [migrations.RunPython(install, uninstall)]
