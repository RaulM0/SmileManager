from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import LoginForm
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme
from api.throttles import limit_legacy, AddressThrottle, AccountThrottle

# Create your views here.

@limit_legacy(AddressThrottle, AccountThrottle)
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user:
                request.audit_auth_event = ('AUTH_LOGIN_SUCCESS', user, 'success')
                login(request, user)
                next_url = request.GET.get('next', 'home')
                if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                    next_url = 'home'
                return redirect(next_url)
            else:
                request.audit_auth_event = ('AUTH_LOGIN_FAILED', None, 'failure')
                messages.error(request, 'Usuario o contraseña incorrectos')
    else:
        form = LoginForm()
    
    return render(request, 'sesiones/login.html', {'form': form})



@require_POST
def logout_view(request):
    if request.user.is_authenticated:
        request.audit_auth_event = ('AUTH_LOGOUT', request.user, 'success')
    logout(request)
    return redirect('login')
