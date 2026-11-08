from datetime import datetime, time, timedelta
from io import StringIO
from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from Citas.models import Cita
from Citas.services import send_appointment_reminders
from Pacientes.models import Paciente
from Usuarios.models import Clinic, ClinicMembership

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AdminReminderTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user(username='doctor',password='secret123')
        self.clinic=Clinic.objects.create(name='Clínica Uno', slug='clinic-a', status=Clinic.Status.ACTIVE)
        ClinicMembership.objects.create(user=self.user, clinic=self.clinic, role=ClinicMembership.Role.DOCTOR, status=ClinicMembership.Status.ACTIVE)
        self.patient=Paciente.objects.create(nombre='ANA',appat='LOPEZ',apmat='DIAZ',fecha_nacimiento='1990-01-01',genero='F',telefono='1',email='A@EXAMPLE.COM',medico=self.user,clinic=self.clinic)
    def test_reminder_service_preserves_command_behavior(self):
        now=timezone.make_aware(datetime.combine(timezone.localdate(),time(9)))
        Cita.objects.create(paciente=self.patient,fecha=(now+timedelta(days=1)).date(),hora=time(10),motivo='CONTROL')
        result=send_appointment_reminders(clinic_id=self.clinic.pk, now=now, dry_run=False)
        self.assertEqual(result['sent'],1); self.assertEqual(mail.outbox[0].to,[self.patient.email]); self.assertNotIn('CONTROL',mail.outbox[0].body)

    def test_dry_run_and_clinic_isolation(self):
        now=timezone.make_aware(datetime.combine(timezone.localdate(),time(9)))
        other=Clinic.objects.create(name='B', slug='clinic-b', status=Clinic.Status.ACTIVE)
        ClinicMembership.objects.create(user=self.user, clinic=other, role='DOCTOR', status='ACTIVE')
        foreign=Paciente.objects.create(nombre='B',appat='B',apmat='B',fecha_nacimiento='1990-01-01',genero='F',telefono='2',email='B@EXAMPLE.COM',medico=self.user,clinic=other)
        for patient in (self.patient, foreign):
            Cita.objects.create(paciente=patient,fecha=(now+timedelta(days=1)).date(),hora=time(10),motivo='CONTROL')
        self.assertEqual(send_appointment_reminders(clinic_id=self.clinic.pk, now=now)['found'], 1)
        self.assertEqual(len(mail.outbox), 0)
        result=send_appointment_reminders(clinic_id=self.clinic.pk, now=now, dry_run=False)
        self.assertEqual(result['sent'], 1)
        self.assertEqual(mail.outbox[0].to, [self.patient.email])
        self.assertIn('Clínica Uno', mail.outbox[0].alternatives[0].content)
        self.assertNotIn('CONTROL', mail.outbox[0].alternatives[0].content)

    def test_suspended_clinic_or_membership_cannot_send(self):
        now=timezone.make_aware(datetime.combine(timezone.localdate(),time(9)))
        Cita.objects.create(paciente=self.patient,fecha=(now+timedelta(days=1)).date(),hora=time(10),motivo='CONTROL')
        ClinicMembership.objects.filter(clinic=self.clinic, user=self.user).update(status='REVOKED')
        self.assertEqual(send_appointment_reminders(clinic_id=self.clinic.pk, now=now, dry_run=False)['sent'], 0)
        self.clinic.status=Clinic.Status.SUSPENDED
        self.clinic.save(update_fields=['status'])
        with self.assertRaises(ValueError):
            send_appointment_reminders(clinic_id=self.clinic.pk, now=now, dry_run=False)
        self.assertEqual(len(mail.outbox), 0)

    def test_command_defaults_to_dry_run(self):
        Cita.objects.create(paciente=self.patient,fecha=(timezone.localdate()+timedelta(days=1)),hora=time(10),motivo='CONTROL')
        output = StringIO()
        call_command('enviar_recordatorios', clinic_id=str(self.clinic.pk), stdout=output)
        self.assertIn('SIMULACIÓN', output.getvalue())
        self.assertEqual(len(mail.outbox), 0)
