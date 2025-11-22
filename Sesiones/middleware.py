from django.shortcuts import redirect

# Rutas públicas que no requieren login
EXEMPT_PREFIXES = [
    '/sesiones/login/',
    '/sesiones/logout/',
    '/admin/',        # permite todas las rutas del admin
    '/static/',       # archivos estáticos (admin usa estos)
]

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Si la ruta comienza con alguna ruta exenta, no requerimos login
        for prefix in EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return self.get_response(request)

        # Si no está autenticado → redirigir
        if not request.user.is_authenticated:
            return redirect(f"/sesiones/login/?next={path}")

        return self.get_response(request)
