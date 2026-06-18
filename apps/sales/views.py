from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_POST
from .models import Sale, SaleItem, Return, ReturnItem, DayClosing, Customer
from apps.inventory.models import Drug
from apps.accounts.models import Counter
import json


# ─── POS ────────────────────────────────────────────────
@login_required
def pos(request, counter_id):
    counter   = get_object_or_404(Counter, pk=counter_id)
    customers = Customer.objects.all().order_by('name')
    drugs     = Drug.objects.filter(is_active=True, quantity__gt=0).select_related('category').order_by('brand_name')
    return render(request, 'sales/pos.html', {
        'counter': counter,
        'customers': customers,
        'drugs': drugs,
        'payment_methods': Sale.PAYMENT_CHOICES,
    })


@login_required
def drug_search_api(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'drugs': []})
    drugs = Drug.objects.filter(
        Q(brand_name__icontains=q) | Q(barcode__icontains=q),
        is_active=True, quantity__gt=0
    )[:10]
    data = [{'id': d.pk, 'name': d.brand_name, 'strength': d.strength,
              'generic': d.generic_name, 'barcode': d.barcode or '',
              'price': float(d.sale_price), 'pieces_per_pack': d.pieces_per_pack,
              'pack_price': float(d.pack_price), 'stock': d.quantity} for d in drugs]
    return JsonResponse({'drugs': data})


@login_required
def sale_submit(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    try:
        payload       = json.loads(request.body)
        counter_id    = payload.get('counter_id')
        customer_id   = payload.get('customer_id')
        items         = payload.get('items', [])
        payment_method= payload.get('payment_method', 'cash')
        discount      = float(payload.get('discount', 0))
        amount_paid   = float(payload.get('amount_paid', 0))

        if not items:
            return JsonResponse({'error': 'No items in sale'}, status=400)

        counter  = Counter.objects.get(pk=counter_id)
        customer = Customer.objects.filter(pk=customer_id).first() if customer_id else None

        subtotal = sum(float(i['price']) * int(i['qty']) for i in items)
        total    = max(subtotal - discount, 0)
        change   = max(amount_paid - total, 0)

        sale = Sale.objects.create(
            counter=counter, cashier=request.user, customer=customer,
            payment_method=payment_method,
            subtotal=subtotal, discount_amount=discount,
            total_amount=total, amount_paid=amount_paid, change_amount=change,
            status='completed',
        )
        for item in items:
            drug = Drug.objects.get(pk=item['id'])
            qty  = int(item['qty'])
            SaleItem.objects.create(sale=sale, drug=drug, quantity=qty, unit_price=item['price'])
            drug.quantity -= qty
            drug.save()

        return JsonResponse({'success': True, 'invoice_no': sale.invoice_no, 'sale_id': sale.pk, 'change': change})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ─── Sales List ──────────────────────────────────────────
@login_required
def sale_list(request):
    q      = request.GET.get('q', '')
    date   = request.GET.get('date', '')
    sales  = Sale.objects.select_related('counter', 'cashier', 'customer').all()
    if q:
        sales = sales.filter(Q(invoice_no__icontains=q) | Q(customer__name__icontains=q))
    if date:
        sales = sales.filter(sale_date__date=date)
    return render(request, 'sales/sale_list.html', {'sales': sales, 'q': q, 'date': date})


@login_required
def sale_detail(request, pk):
    sale = get_object_or_404(Sale.objects.select_related('counter', 'cashier', 'customer').prefetch_related('items__drug'), pk=pk)
    return render(request, 'sales/sale_detail.html', {'sale': sale})


@login_required
def sale_receipt(request, pk):
    sale = get_object_or_404(Sale.objects.prefetch_related('items__drug'), pk=pk)
    from apps.settings_app.models import PharmacySettings
    settings = PharmacySettings.get_settings()
    return render(request, 'sales/sale_receipt.html', {'sale': sale, 'settings': settings})


# ─── Customers ───────────────────────────────────────────
@login_required
def customer_list(request):
    q = request.GET.get('q', '')
    customers = Customer.objects.all()
    if q:
        customers = customers.filter(Q(name__icontains=q) | Q(phone__icontains=q))
    return render(request, 'sales/customer_list.html', {'customers': customers, 'q': q})


@login_required
def customer_add(request):
    if request.method == 'POST':
        Customer.objects.create(
            name    = request.POST.get('name'),
            phone   = request.POST.get('phone', ''),
            email   = request.POST.get('email', ''),
            address = request.POST.get('address', ''),
            notes   = request.POST.get('notes', ''),
        )
        messages.success(request, 'Customer added.')
        return redirect('sales:customer_list')
    return render(request, 'sales/customer_form.html', {'action': 'Add'})


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.name    = request.POST.get('name')
        customer.phone   = request.POST.get('phone', '')
        customer.email   = request.POST.get('email', '')
        customer.address = request.POST.get('address', '')
        customer.notes   = request.POST.get('notes', '')
        customer.save()
        messages.success(request, 'Customer updated.')
        return redirect('sales:customer_list')
    sales = customer.sales.order_by('-sale_date')[:10]
    return render(request, 'sales/customer_detail.html', {'customer': customer, 'sales': sales})


# ─── Returns ─────────────────────────────────────────────
@login_required
def return_list(request):
    returns = Return.objects.select_related('sale', 'processed_by').all()
    return render(request, 'sales/return_list.html', {'returns': returns})


@login_required
def return_new(request, sale_id):
    sale = get_object_or_404(Sale, pk=sale_id)
    if not sale.can_return():
        messages.error(request, 'This sale cannot be returned (either closed or past 15 days).')
        return redirect('sales:sale_detail', pk=sale_id)
    if request.method == 'POST':
        return_type   = request.POST.get('return_type')
        reason        = request.POST.get('reason', '')
        item_ids      = request.POST.getlist('item_id')
        quantities    = request.POST.getlist('return_qty')
        exchange_ids  = request.POST.getlist('exchange_drug')

        refund = 0
        ret = Return.objects.create(
            sale=sale, processed_by=request.user,
            return_type=return_type, reason=reason,
        )
        for i, item_id in enumerate(item_ids):
            qty = int(quantities[i] or 0)
            if qty <= 0: continue
            sale_item = get_object_or_404(SaleItem, pk=item_id)
            exc_drug  = Drug.objects.filter(pk=exchange_ids[i]).first() if exchange_ids[i] else None
            ReturnItem.objects.create(
                return_record=ret, drug=sale_item.drug,
                quantity=qty, unit_price=sale_item.unit_price,
                exchange_drug=exc_drug,
            )
            sale_item.drug.quantity += qty
            sale_item.drug.save()
            refund += qty * float(sale_item.unit_price)
            if exc_drug:
                exc_drug.quantity -= qty
                exc_drug.save()

        ret.refund_amount = refund if return_type == 'cash' else 0
        ret.save()
        messages.success(request, f'Return processed for {sale.invoice_no}.')
        return redirect('sales:return_detail', pk=ret.pk)

    drugs = Drug.objects.filter(is_active=True).order_by('brand_name')
    return render(request, 'sales/return_form.html', {'sale': sale, 'drugs': drugs})


@login_required
def return_detail(request, pk):
    ret = get_object_or_404(Return.objects.select_related('sale', 'processed_by').prefetch_related('items__drug'), pk=pk)
    return render(request, 'sales/return_detail.html', {'ret': ret})


# ─── Day Closing ─────────────────────────────────────────
@login_required
def day_closing_list(request):
    closings = DayClosing.objects.select_related('counter', 'cashier').all()
    return render(request, 'sales/day_closing_list.html', {'closings': closings})


@login_required
def day_closing_new(request):
    from django.db.models import Sum
    today    = timezone.now().date()
    counters = Counter.objects.filter(is_active=True)

    if request.method == 'POST':
        counter_id   = request.POST.get('counter')
        actual_cash  = float(request.POST.get('actual_cash', 0))
        notes        = request.POST.get('notes', '')
        counter      = get_object_or_404(Counter, pk=counter_id)

        if DayClosing.objects.filter(counter=counter, closing_date=today).exists():
            messages.error(request, f'{counter.name} is already closed for today.')
            return redirect('sales:day_closing_list')

        today_sales   = Sale.objects.filter(counter=counter, sale_date__date=today, status='completed')
        total_sales   = today_sales.aggregate(t=Sum('total_amount'))['t'] or 0
        total_returns = Return.objects.filter(sale__counter=counter, return_date__date=today).aggregate(t=Sum('refund_amount'))['t'] or 0
        expected_cash = float(total_sales) - float(total_returns)
        difference    = actual_cash - expected_cash

        DayClosing.objects.create(
            counter=counter, cashier=request.user, closing_date=today,
            total_sales=total_sales, total_returns=total_returns,
            expected_cash=expected_cash, actual_cash=actual_cash,
            difference=difference, status='closed',
            closed_at=timezone.now(), notes=notes,
        )
        messages.success(request, f'{counter.name} closed for today.')
        return redirect('sales:day_closing_list')

    # Pre-calculate for each counter
    counter_data = []
    for counter in counters:
        already_closed = DayClosing.objects.filter(counter=counter, closing_date=today, status='closed').exists()
        sales_total = Sale.objects.filter(counter=counter, sale_date__date=today, status='completed').aggregate(t=Sum('total_amount'))['t'] or 0
        sales_count = Sale.objects.filter(counter=counter, sale_date__date=today, status='completed').count()
        counter_data.append({'counter': counter, 'sales_total': sales_total, 'sales_count': sales_count, 'already_closed': already_closed})

    return render(request, 'sales/day_closing_form.html', {'counter_data': counter_data, 'today': today})


@login_required
def day_closing_detail(request, pk):
    closing = get_object_or_404(DayClosing.objects.select_related('counter', 'cashier'), pk=pk)
    return render(request, 'sales/day_closing_detail.html', {'closing': closing})
