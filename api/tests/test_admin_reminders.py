from datetime import datetime, time, timedelta
from django.contrib import admin
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from Citas.models import Cita
from Citas.services import send_appointment_reminders
from Pacientes.models import Paciente

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AdminReminderTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user(username='doctor',password='secret123')
        self.patient=Paciente.objects.create(nombre='ANA',appat='LOPEZ',apmat='DIAZ',fecha_nacimiento='1990-01-01',genero='F',telefono='1',email='A@EXAMPLE.COM',medico=self.user)
    def test_models_remain_registered_in_admin(self):
        self.assertIn(Paciente,admin.site._registry); self.assertIn(Cita,admin.site._registry)
    def test_reminder_service_preserves_command_behavior(self):
        now=timezone.make_aware(datetime.combine(timezone.localdate(),time(9)))
        Cita.objects.create(paciente=self.patient,fecha=(now+timedelta(days=1)).date(),hora=time(10),motivo='CONTROL')
        result=send_appointment_reminders(now=now)
        self.assertEqual(result['sent'],1); self.assertEqual(mail.outbox[0].to,[self.patient.email]); self.assertIn('CONTROL',mail.outbox[0].body)
