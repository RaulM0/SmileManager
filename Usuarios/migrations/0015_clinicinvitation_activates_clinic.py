from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('Usuarios', '0014_merge_security_and_ai')]
    operations = [migrations.AddField(
        model_name='clinicinvitation', name='activates_clinic',
        field=models.BooleanField(default=False),
    )]
