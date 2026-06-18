from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count
from .models import User, Partner, Counter


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def dashboard(request):
    from apps.inventory.models import Drug
    from apps.sales.models import Sale, Return

    today = timezone.now().date()

    # Today stats
    today_sales_qs = Sale.objects.filter(sale_date__date=today, status='completed')
    today_revenue  = today_sales_qs.aggregate(t=Sum('total_amount'))['t'] or 0
    today_sales    = today_sales_qs.count()
    today_returns  = Return.objects.filter(return_date__date=today).count()
    total_drugs    = Drug.objects.filter(is_active=True).count()

    # Alerts
    low_stock_drugs  = Drug.objects.filter(is_active=True, quantity__lte=10)
    expiry_threshold = today + timezone.timedelta(days=30)
    near_expiry      = Drug.objects.filter(is_active=True, expiry_date__lte=expiry_threshold, expiry_date__gte=today)
    alert_drugs      = (low_stock_drugs | near_expiry).distinct()[:8]
    low_stock_count  = low_stock_drugs.count()
    expiry_count     = near_expiry.count()

    # Last 7 days chart
    labels, data = [], []
    for i in range(6, -1, -1):
        day = today - timezone.timedelta(days=i)
        rev = Sale.objects.filter(sale_date__date=day, status='completed').aggregate(t=Sum('total_amount'))['t'] or 0
        labels.append(f'"{day.strftime("%a")}"')
        data.append(float(rev))

    # Category breakdown
    from apps.inventory.models import Category
    cat_labels, cat_values = [], []
    for cat in Category.objects.all()[:6]:
        count = Drug.objects.filter(category=cat, is_active=True).count()
        if count:
            cat_labels.append(f'"{cat.name}"')
            cat_values.append(count)
    if not cat_labels:
        cat_labels, cat_values = ['"Uncategorized"'], [total_drugs or 1]

    context = {
        'today_revenue':  today_revenue,
        'today_sales':    today_sales,
        'today_returns':  today_returns,
        'total_drugs':    total_drugs,
        'low_stock_count': low_stock_count,
        'expiry_count':   expiry_count,
        'alert_drugs':    alert_drugs,
        'recent_sales':   Sale.objects.select_related('customer', 'counter').order_by('-sale_date')[:6],
        'counters':       Counter.objects.filter(is_active=True),
        'chart_labels':   '[' + ','.join(labels) + ']',
        'chart_data':     str(data),
        'cat_labels':     '[' + ','.join(cat_labels) + ']',
        'cat_values':     str(cat_values),
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def user_list(request):
    users = User.objects.all().order_by('role', 'username')
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
def user_add(request):
    if request.method == 'POST':
        username   = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name  = request.POST.get('last_name')
        email      = request.POST.get('email')
        phone      = request.POST.get('phone')
        role       = request.POST.get('role')
        password   = request.POST.get('password')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        else:
            user = User.objects.create_user(
                username=username, password=password,
                first_name=first_name, last_name=last_name,
                email=email, phone=phone, role=role
            )
            if role == 'partner':
                ownership = request.POST.get('ownership_percent', 0)
                Partner.objects.create(user=user, ownership_percent=ownership)
            messages.success(request, f'User {username} created.')
            return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'action': 'Add'})


@login_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name')
        user.last_name  = request.POST.get('last_name')
        user.email      = request.POST.get('email')
        user.phone      = request.POST.get('phone')
        user.role       = request.POST.get('role')
        if request.POST.get('password'):
            user.set_password(request.POST.get('password'))
        user.save()
        messages.success(request, 'User updated.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'action': 'Edit', 'obj': user})


@login_required
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted.')
    return redirect('accounts:user_list')


@login_required
def counter_list(request):
    counters = Counter.objects.select_related('cashier').all()
    return render(request, 'accounts/counter_list.html', {'counters': counters})


@login_required
def counter_add(request):
    if request.method == 'POST':
        name     = request.POST.get('name')
        cashier_id = request.POST.get('cashier')
        cashier  = User.objects.filter(pk=cashier_id).first() if cashier_id else None
        Counter.objects.create(name=name, cashier=cashier)
        messages.success(request, f'Counter "{name}" created.')
        return redirect('accounts:counter_list')
    cashiers = User.objects.filter(role='cashier')
    return render(request, 'accounts/counter_form.html', {'action': 'Add', 'cashiers': cashiers})


@login_required
def counter_edit(request, pk):
    counter = get_object_or_404(Counter, pk=pk)
    if request.method == 'POST':
        counter.name      = request.POST.get('name')
        cashier_id        = request.POST.get('cashier')
        counter.cashier   = User.objects.filter(pk=cashier_id).first() if cashier_id else None
        counter.is_active = request.POST.get('is_active') == 'on'
        counter.save()
        messages.success(request, 'Counter updated.')
        return redirect('accounts:counter_list')
    cashiers = User.objects.filter(role='cashier')
    return render(request, 'accounts/counter_form.html', {'action': 'Edit', 'obj': counter, 'cashiers': cashiers})


@login_required
def partner_list(request):
    partners = Partner.objects.select_related('user').all()
    return render(request, 'accounts/partner_list.html', {'partners': partners})


@login_required
def partner_add(request):
    if request.method == 'POST':
        user_id   = request.POST.get('user')
        ownership = request.POST.get('ownership_percent')
        user      = get_object_or_404(User, pk=user_id)
        Partner.objects.create(user=user, ownership_percent=ownership)
        user.role = 'partner'
        user.save()
        messages.success(request, 'Partner added.')
        return redirect('accounts:partner_list')
    users = User.objects.filter(partner_profile__isnull=True)
    return render(request, 'accounts/partner_form.html', {'action': 'Add', 'users': users})


@login_required
def partner_edit(request, pk):
    partner = get_object_or_404(Partner, pk=pk)
    if request.method == 'POST':
        partner.ownership_percent = request.POST.get('ownership_percent')
        partner.notes             = request.POST.get('notes', '')
        partner.save()
        messages.success(request, 'Partner updated.')
        return redirect('accounts:partner_list')
    return render(request, 'accounts/partner_form.html', {'action': 'Edit', 'obj': partner})
