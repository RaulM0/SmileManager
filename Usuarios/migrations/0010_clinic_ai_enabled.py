from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('Usuarios', '0009_platformadmin')]

    operations = [
        migrations.AddField(
            model_name='clinic',
            name='ai_enabled',
            field=models.BooleanField(default=False),
        ),
    ]
