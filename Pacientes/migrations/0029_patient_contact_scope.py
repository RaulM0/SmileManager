from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('Pacientes', '0028_imagenesclinicas_is_active')]

    operations = [
        migrations.RemoveConstraint(model_name='paciente', name='unique_telefono_por_medico'),
        migrations.RemoveConstraint(model_name='paciente', name='unique_email_por_medico'),
        migrations.AddConstraint(model_name='paciente', constraint=models.UniqueConstraint(fields=('telefono', 'medico'), condition=models.Q(clinic__isnull=True), name='legacy_phone_doctor_uniq')),
        migrations.AddConstraint(model_name='paciente', constraint=models.UniqueConstraint(fields=('email', 'medico'), condition=models.Q(clinic__isnull=True), name='legacy_email_doctor_uniq')),
        migrations.AddConstraint(model_name='paciente', constraint=models.UniqueConstraint(fields=('clinic', 'telefono', 'medico'), condition=models.Q(clinic__isnull=False), name='clinic_phone_doctor_uniq')),
        migrations.AddConstraint(model_name='paciente', constraint=models.UniqueConstraint(fields=('clinic', 'email', 'medico'), condition=models.Q(clinic__isnull=False), name='clinic_email_doctor_uniq')),
    ]
