from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import connection, DatabaseError, transaction
from django.test import skipUnlessDBFeature
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from Pacientes.models import Consulta, Paciente, PrivacyNotice, ConsentTemplate
from Usuarios.models import Clinic, ClinicMembership
from api.privacy import NOTICE_FIELDS
from .document_fixtures import publish_documents


class DocumentControlTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user('documents-admin', first_name='Responsable', last_name='Sintético')
        self.doctor = User.objects.create_user('documents-doctor', password='Clinical phrase 459!', first_name='Profesional', last_name='Sintético')
        self.clinic = Clinic.objects.create(name='A', slug='document-a', status='ACTIVE')
        self.other = Clinic.objects.create(name='B', slug='document-b', status='ACTIVE')
        ClinicMembership.objects.create(clinic=self.clinic, user=self.admin, role='CLINIC_ADMIN', status='ACTIVE')
        ClinicMembership.objects.create(clinic=self.clinic, user=self.doctor, role='DOCTOR', status='ACTIVE')
        self.patient = Paciente.objects.create(clinic=self.clinic, medico=self.doctor, nombre='Paciente', appat='Sintético', apmat='Prueba', fecha_nacimiento='2000-01-01', genero='F', telefono='5552223333', email='synthetic@example.test')
        self.headers = {'HTTP_X_CLINIC_ID': str(self.clinic.pk)}

    def notice_body(self):
        return {**{key: 'Contenido sintético revisado para esta prueba.' for key in NOTICE_FIELDS},
                'privacy_email': 'privacy@example.test', 'review_confirmed': True}

    def test_notice_requires_complete_data_and_admin_and_preserves_versions(self):
        self.client.force_authenticate(self.admin)
        url = reverse('publish-privacy-notice')
        self.assertEqual(self.client.post(url, self.notice_body(), HTTP_X_CLINIC_ID='invalid-clinic').status_code, 403)
        self.assertEqual(self.client.post(url, {'review_confirmed': True}, **self.headers).status_code, 400)
        self.assertEqual(self.client.post(url, {**self.notice_body(), 'review_confirmed': False}, **self.headers).status_code, 400)
        self.assertEqual(self.client.post(url, self.notice_body(), **self.headers).status_code, 201)
        self.assertEqual(self.client.post(url, self.notice_body(), **self.headers).data['version'], 2)
        first = PrivacyNotice.objects.get(clinic=self.clinic, version=1)
        with self.assertRaises(ValidationError):
            first.save()
        with self.assertRaises(ValidationError):
            PrivacyNotice.objects.filter(pk=first.pk).update(body={})
        self.client.force_authenticate(self.doctor)
        self.assertEqual(self.client.post(url, self.notice_body(), **self.headers).status_code, 403)
        self.client.force_authenticate(None)
        response = self.client.get(reverse('public-privacy-notice', args=[self.clinic.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['notice']['version'], 2)
        self.assertNotIn('approved_by', response.data['notice'])
        self.clinic.status = 'SUSPENDED'
        self.clinic.save(update_fields=['status'])
        self.assertEqual(self.client.get(reverse('public-privacy-notice', args=[self.clinic.slug])).data['notice']['version'], 2)

    def test_no_generic_notice_is_presented_as_published(self):
        self.client.force_authenticate(None)
        response = self.client.get(reverse('public-privacy-notice', args=[self.clinic.slug]))
        self.assertEqual(response.data, {'configured': False, 'notice': None})

    def test_templates_require_notice_and_cannot_cross_clinics(self):
        self.client.force_authenticate(self.admin)
        url = reverse('consent-templates')
        body = {'kind': 'PRIVACY', 'title': 'Consentimiento sintético', 'text': 'Contenido sintético revisado para esta prueba.', 'review_confirmed': True}
        self.assertEqual(self.client.post(url, body, **self.headers).status_code, 409)
        self.client.post(reverse('publish-privacy-notice'), self.notice_body(), **self.headers)
        response = self.client.post(url, body, **self.headers)
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(response.data['privacy_notice_id'])
        self.assertEqual(self.client.get(url, HTTP_X_CLINIC_ID=str(self.other.pk)).status_code, 403)

    def consultation(self):
        return Consulta.objects.create(paciente=self.patient, medico=self.doctor, fecha_consulta=timezone.now(), motivo_consulta='Control sintético', diagnostico='Sintético')

    def close(self, row):
        self.client.force_authenticate(self.doctor)
        return self.client.post(reverse('consultation-attestation', args=[row.pk, 'close']), {'password': 'Clinical phrase 459!', 'code': '', 'text': ''}, **self.headers)

    def test_closure_requires_identity_and_adenda_preserves_original(self):
        row = self.consultation()
        self.client.force_authenticate(self.doctor)
        url = reverse('consultation-attestation', args=[row.pk, 'close'])
        self.assertEqual(self.client.post(url, {'password': 'incorrect'}, **self.headers).status_code, 403)
        result = self.close(row)
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(result.data['integrity'], 'verified')
        self.assertEqual(result.data['author_name'], 'Profesional Sintético')
        row.refresh_from_db()
        original = row.content_sha256
        self.assertEqual(self.client.patch(reverse('tenant-consultation-detail', args=[row.pk]), {'diagnostico': 'cambio'}, **self.headers).status_code, 409)
        self.assertEqual(self.client.post(reverse('consultation-attestation', args=[row.pk, 'addendum']), {'password': 'Clinical phrase 459!', 'text': 'Aclaración sintética del documento previo.'}, **self.headers).status_code, 200)
        row.refresh_from_db()
        self.assertEqual(row.content_sha256, original)
        self.assertEqual(row.diagnostico, 'Sintético')
        self.assertEqual(row.addenda.count(), 1)

    def test_other_clinic_and_missing_professional_name_cannot_close(self):
        row = self.consultation()
        self.client.force_authenticate(self.doctor)
        url = reverse('consultation-attestation', args=[row.pk, 'close'])
        self.assertEqual(self.client.post(url, {'password': 'Clinical phrase 459!'}, HTTP_X_CLINIC_ID=str(self.other.pk)).status_code, 403)
        self.doctor.first_name = self.doctor.last_name = ''
        self.doctor.save(update_fields=['first_name', 'last_name'])
        self.assertEqual(self.close(row).status_code, 400)

    @skipUnlessDBFeature('has_select_for_update')
    def test_postgresql_rejects_raw_mutation_or_delete_of_sealed_documents(self):
        row = self.consultation()
        self.assertEqual(self.close(row).status_code, 200)
        for sql in ('UPDATE "Pacientes_consulta" SET diagnostico = %s WHERE id = %s',
                    'DELETE FROM "Pacientes_consulta" WHERE diagnostico = %s AND id = %s'):
            with self.assertRaises(DatabaseError), transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(sql, ['changed', row.pk] if sql.startswith('UPDATE') else ['Sintético', row.pk])
        notice, _ = publish_documents(self.clinic, self.admin)
        with self.assertRaises(DatabaseError), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute('UPDATE "Pacientes_privacynotice" SET approved_name = %s WHERE id = %s', ['Changed', notice.pk])
