from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class RetiredHtmlRoutesTests(TestCase):
    def test_react_is_the_root_and_api_remains_available(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/app/')
        self.assertEqual(self.client.get(reverse('api-session')).status_code, 200)

    def test_retired_html_and_admin_routes_are_unavailable_even_for_superusers(self):
        superuser = User.objects.create_superuser('synthetic-root', password='not-a-real-password')
        client = Client(enforce_csrf_checks=False)
        client.force_login(superuser)
        for path in ('/sesiones/login/', '/sesiones/logout/', '/home/', '/registroPacientes/',
                     '/registroPacientes/registrar_pacientes/', '/registroPacientes/antecedentes/1/',
                     '/registroPacientes/archivos/image/1/imagen/', '/menu_citas/',
                     '/menu_citas/confirmar_asistencia/1/', '/diagnosticos/',
                     '/diagnosticos/resultados/1/', '/admin/', '/admin/auth/user/'):
            for method in (client.get, client.post):
                with self.subTest(path=path, method=method.__name__):
                    self.assertEqual(method(path).status_code, 404)
