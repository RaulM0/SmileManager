from django.shortcuts import redirect

# Rutas públicas que no requieren login
EXEMPT_PATHS = [
    '/sesiones/login/',
    '/sesiones/logout/',
]

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            if request.path not in EXEMPT_PATHS:
                # Redirige al login con next para volver después
                return redirect(f"/sesiones/login/?next={request.path}")

        response = self.get_response(request)
        return response
