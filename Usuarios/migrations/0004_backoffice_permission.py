from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('Usuarios', '0003_auditevent')]
    operations = [migrations.AlterModelOptions(name='auditevent', options={'ordering': ['-timestamp', '-id'], 'permissions': [('access_system_backoffice', 'Can access system backoffice')]})]
