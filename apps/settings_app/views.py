from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import PharmacySettings
from apps.accounts.models import User
import os, signal


def superuser_required(view_func):
    """Decorator: only superusers can access this view."""
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.conf import settings as django_settings
            return redirect(django_settings.LOGIN_URL)
        if not request.user.is_superuser:
            messages.error(request, 'Access denied. Superuser only.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@superuser_required
def settings_view(request):
    s = PharmacySettings.get_settings()
    if request.method == 'POST' and request.POST.get('form') == 'pharmacy':
        s.pharmacy_name       = request.POST.get('pharmacy_name', '')
        s.tagline             = request.POST.get('tagline', '')
        s.address             = request.POST.get('address', '')
        s.phone               = request.POST.get('phone', '')
        s.email               = request.POST.get('email', '')
        s.tax_rate            = request.POST.get('tax_rate') or 0
        s.currency            = request.POST.get('currency', 'Rs')
        s.return_days         = request.POST.get('return_days') or 15
        s.receipt_footer      = request.POST.get('receipt_footer', '')
        s.low_stock_threshold = request.POST.get('low_stock_threshold') or 10
        if request.FILES.get('logo'):
            s.logo = request.FILES['logo']
        s.save()
        messages.success(request, 'Settings saved.')
        return redirect('settings_app:settings')

    users = User.objects.all().order_by('is_superuser', 'role', 'username').reverse()
    return render(request, 'settings_app/settings.html', {'settings': s, 'users': users})


@superuser_required
def create_superuser(request):
    if request.method == 'POST':
        username  = request.POST.get('username', '').strip()
        password  = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        email     = request.POST.get('email', '')
        full_name = request.POST.get('full_name', '').strip()

        if not username or not password:
            messages.error(request, 'Username and password are required.')
        elif password != password2:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" already exists.')
        else:
            first, *last = (full_name.split() or [username])
            u = User.objects.create_superuser(
                username=username, password=password, email=email,
                first_name=first, last_name=' '.join(last),
            )
            u.role = 'superuser'
            u.save()
            messages.success(request, f'Superuser "{username}" created successfully.')
        return redirect('settings_app:settings')
    return redirect('settings_app:settings')


@superuser_required
def delete_user(request, pk):
    if request.method == 'POST':
        user = User.objects.filter(pk=pk).first()
        if not user:
            messages.error(request, 'User not found.')
        elif user == request.user:
            messages.error(request, 'You cannot delete your own account.')
        else:
            name = user.username
            user.delete()
            messages.success(request, f'User "{name}" deleted.')
    return redirect('settings_app:settings')


@superuser_required
def reset_password(request, pk):
    if request.method == 'POST':
        user      = User.objects.filter(pk=pk).first()
        password  = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        if not user:
            messages.error(request, 'User not found.')
        elif not password:
            messages.error(request, 'Password cannot be empty.')
        elif password != password2:
            messages.error(request, 'Passwords do not match.')
        else:
            user.set_password(password)
            user.save()
            messages.success(request, f'Password reset for "{user.username}".')
    return redirect('settings_app:settings')


@superuser_required
def shutdown_server(request):
    if request.method == 'POST':
        # Schedule kill after response is sent
        import threading
        def kill():
            import time
            time.sleep(0.8)
            os.kill(os.getpid(), signal.SIGTERM)
        threading.Thread(target=kill, daemon=True).start()
        return JsonResponse({'ok': True})
    return redirect('settings_app:settings')
