from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from apps.sales.models import Sale, Return, DayClosing
from apps.inventory.models import Drug, Category
from apps.accounts.models import Partner, Counter
import json


@login_required
def reports_dashboard(request):
    today     = timezone.now().date()
    month_start = today.replace(day=1)

    total_sales_month   = Sale.objects.filter(sale_date__date__gte=month_start, status='completed').aggregate(t=Sum('total_amount'))['t'] or 0
    total_sales_today   = Sale.objects.filter(sale_date__date=today, status='completed').aggregate(t=Sum('total_amount'))['t'] or 0
    total_cost          = sum((i.quantity * float(i.drug.cost_price)) for s in Sale.objects.filter(sale_date__date__gte=month_start, status='completed') for i in s.items.all())
    profit_month        = float(total_sales_month) - total_cost
    low_stock           = Drug.objects.filter(is_active=True, quantity__lte=10).count()
    expired             = Drug.objects.filter(is_active=True, expiry_date__lt=today).count()

    # Last 30 days chart
    labels, revenues, profits = [], [], []
    for i in range(29, -1, -1):
        day = today - timezone.timedelta(days=i)
        rev = Sale.objects.filter(sale_date__date=day, status='completed').aggregate(t=Sum('total_amount'))['t'] or 0
        cst = sum((it.quantity * float(it.drug.cost_price)) for s in Sale.objects.filter(sale_date__date=day, status='completed') for it in s.items.all())
        labels.append(f'"{day.strftime("%d %b")}"')
        revenues.append(float(rev))
        profits.append(round(float(rev) - cst, 2))

    context = {
        'total_sales_month': total_sales_month,
        'total_sales_today': total_sales_today,
        'profit_month':      round(profit_month, 2),
        'low_stock':         low_stock,
        'expired':           expired,
        'chart_labels':      '[' + ','.join(labels) + ']',
        'chart_revenue':     str(revenues),
        'chart_profit':      str(profits),
    }
    return render(request, 'reports/dashboard.html', context)


@login_required
def sales_report(request):
    date_from = request.GET.get('from', '')
    date_to   = request.GET.get('to', '')
    counter   = request.GET.get('counter', '')
    sales     = Sale.objects.select_related('counter', 'cashier', 'customer').filter(status='completed')
    if date_from: sales = sales.filter(sale_date__date__gte=date_from)
    if date_to:   sales = sales.filter(sale_date__date__lte=date_to)
    if counter:   sales = sales.filter(counter_id=counter)
    total = sales.aggregate(t=Sum('total_amount'))['t'] or 0
    counters = Counter.objects.filter(is_active=True)
    return render(request, 'reports/sales.html', {
        'sales': sales[:100], 'total': total,
        'counters': counters, 'date_from': date_from, 'date_to': date_to, 'sel_counter': counter,
    })


@login_required
def stock_report(request):
    drugs = Drug.objects.select_related('category', 'supplier').filter(is_active=True)
    total_value = sum(float(d.quantity) * float(d.cost_price) for d in drugs)
    return render(request, 'reports/stock.html', {'drugs': drugs, 'total_value': total_value})


@login_required
def expiry_report(request):
    today    = timezone.now().date()
    in30     = today + timezone.timedelta(days=30)
    expired  = Drug.objects.filter(is_active=True, expiry_date__lt=today)
    near30   = Drug.objects.filter(is_active=True, expiry_date__gte=today, expiry_date__lte=in30)
    return render(request, 'reports/expiry.html', {'expired': expired, 'near30': near30, 'today': today})


@login_required
def profit_report(request):
    date_from = request.GET.get('from', str(timezone.now().date().replace(day=1)))
    date_to   = request.GET.get('to',   str(timezone.now().date()))
    sales     = Sale.objects.filter(sale_date__date__gte=date_from, sale_date__date__lte=date_to, status='completed')
    total_rev = sales.aggregate(t=Sum('total_amount'))['t'] or 0
    total_ret = Return.objects.filter(return_date__date__gte=date_from, return_date__date__lte=date_to).aggregate(t=Sum('refund_amount'))['t'] or 0
    total_cost = sum((i.quantity * float(i.drug.cost_price)) for s in sales for i in s.items.all())
    net_profit = float(total_rev) - float(total_ret or 0) - total_cost
    return render(request, 'reports/profit.html', {
        'total_rev': total_rev, 'total_ret': total_ret or 0,
        'total_cost': round(total_cost, 2), 'net_profit': round(net_profit, 2),
        'date_from': date_from, 'date_to': date_to,
    })


@login_required
def partner_report(request):
    date_from = request.GET.get('from', str(timezone.now().date().replace(day=1)))
    date_to   = request.GET.get('to',   str(timezone.now().date()))
    sales     = Sale.objects.filter(sale_date__date__gte=date_from, sale_date__date__lte=date_to, status='completed')
    total_rev = float(sales.aggregate(t=Sum('total_amount'))['t'] or 0)
    total_ret = float(Return.objects.filter(return_date__date__gte=date_from, return_date__date__lte=date_to).aggregate(t=Sum('refund_amount'))['t'] or 0)
    total_cost= sum((i.quantity * float(i.drug.cost_price)) for s in sales for i in s.items.all())
    net_profit= total_rev - total_ret - total_cost
    partners  = Partner.objects.select_related('user').all()
    partner_data = []
    for p in partners:
        share = round((float(p.ownership_percent) / 100) * net_profit, 2)
        partner_data.append({'partner': p, 'share': share})
    return render(request, 'reports/partners.html', {
        'partner_data': partner_data, 'net_profit': round(net_profit, 2),
        'date_from': date_from, 'date_to': date_to,
    })


@login_required
def counter_report(request):
    date_from = request.GET.get('from', str(timezone.now().date()))
    date_to   = request.GET.get('to',   str(timezone.now().date()))
    counters  = Counter.objects.filter(is_active=True)
    data = []
    for c in counters:
        sales  = Sale.objects.filter(counter=c, sale_date__date__gte=date_from, sale_date__date__lte=date_to, status='completed')
        rev    = sales.aggregate(t=Sum('total_amount'))['t'] or 0
        count  = sales.count()
        data.append({'counter': c, 'revenue': rev, 'count': count})
    return render(request, 'reports/counters.html', {
        'data': data, 'date_from': date_from, 'date_to': date_to,
    })


@login_required
def export_excel(request, report_type):
    return HttpResponse('Excel export — coming soon')


@login_required
def export_pdf(request, report_type):
    return HttpResponse('PDF export — coming soon')
