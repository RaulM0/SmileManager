from datetime import timedelta
from html.parser import HTMLParser
from types import SimpleNamespace

from django.core import mail
from django.template.loader import render_to_string
from django.test import SimpleTestCase, override_settings
from django.utils import timezone

from api.tenant_views import deliver_invitation


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.hrefs.extend(value for key, value in attrs if key == 'href')


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class EmailTemplateTests(SimpleTestCase):
    def test_invitation_delivers_html_and_text_with_same_fragment_link(self):
        invitation = SimpleNamespace(
            clinic=SimpleNamespace(name='Clínica de prueba'),
            email='invited@example.test', expires_at=timezone.now() + timedelta(days=1),
        )
        deliver_invitation(invitation, 'synthetic-token', 'https://example.test/invitations/accept')
        message = mail.outbox[-1]
        self.assertEqual(message.to, [invitation.email])
        html, mimetype = message.alternatives[0]
        self.assertEqual(mimetype, 'text/html')
        parser = Links()
        parser.feed(html)
        expected = 'https://example.test/invitations/accept#synthetic-token'
        self.assertIn(expected, parser.hrefs)
        self.assertIn(expected, message.body)
        self.assertIn(invitation.clinic.name, html)
        self.assertIn('Revisar invitación', html)
        self.assertIn('vence el', html)

    def test_shared_templates_escape_content_and_preserve_message_lines(self):
        for template in ('emails/mensaje_paciente.html', 'emails/appointment_reminder_tenant.html'):
            with self.subTest(template=template):
                html = render_to_string(template, {
                    'clinic_name': 'Clínica <script>unsafe</script>',
                    'asunto': '<img src=x onerror=unsafe>',
                    'mensaje': 'Primera línea\nSegunda <script>unsafe</script>',
                })
                self.assertIn('SmileManager', html)
                self.assertIn('#176b78', html)
                self.assertIn('Primera línea<br>Segunda', html)
                self.assertNotIn('<script>', html)
                self.assertNotIn('<img src=x', html)
                self.assertIn('&lt;script&gt;', html)

    def test_invitation_escapes_link_attributes(self):
        html = render_to_string('api/emails/invitation.html', {
            'clinic_name': '<script>unsafe</script>',
            'invitation_url': 'https://example.test/" onclick="unsafe',
        })
        self.assertNotIn('<script>', html)
        self.assertNotIn('href="https://example.test/" onclick=', html)
        self.assertIn('&quot;', html)
