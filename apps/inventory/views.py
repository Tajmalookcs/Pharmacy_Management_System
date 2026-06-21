from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Category, Supplier, Drug, Purchase, PurchaseItem, StockAdjustment


@login_required
def drug_list(request):
    q        = request.GET.get('q', '')
    category = request.GET.get('category', '')
    alert    = request.GET.get('alert', '')
    status   = request.GET.get('status', '')
    drugs    = Drug.objects.select_related('category', 'supplier').all()
    if q:
        drugs = drugs.filter(Q(brand_name__icontains=q) | Q(generic_name__icontains=q) | Q(barcode__icontains=q))
    if category:
        drugs = drugs.filter(category_id=category)
    if status == 'active':
        drugs = drugs.filter(is_active=True)
    elif status == 'inactive':
        drugs = drugs.filter(is_active=False)
    today = timezone.now().date()
    if alert == 'low':
        drugs = drugs.filter(quantity__lte=10)
    elif alert == 'expiry':
        drugs = drugs.filter(expiry_date__lte=today + timezone.timedelta(days=30))
    elif alert == 'expired':
        drugs = drugs.filter(expiry_date__lt=today)
    categories = Category.objects.all()
    return render(request, 'inventory/drug_list.html', {
        'drugs': drugs, 'categories': categories, 'q': q,
        'selected_cat': category, 'selected_alert': alert, 'selected_status': status,
    })


@login_required
def drug_toggle_active(request, pk):
    drug = get_object_or_404(Drug, pk=pk)
    drug.is_active = not drug.is_active
    Drug.objects.filter(pk=pk).update(is_active=drug.is_active)
    status = 'activated' if drug.is_active else 'deactivated'
    messages.success(request, f'"{drug.brand_name}" {status}.')
    return redirect('inventory:drug_list')


@login_required
def drug_add(request):
    if request.method == 'POST':
        drug = Drug(
            brand_name      = request.POST.get('brand_name'),
            strength        = request.POST.get('strength', ''),
            generic_name    = request.POST.get('generic_name'),
            barcode         = request.POST.get('barcode') or None,
            sale_price      = request.POST.get('sale_price') or 0,
            cost_price      = request.POST.get('cost_price') or 0,
            pieces_per_pack = request.POST.get('pieces_per_pack') or 1,
            pack_price      = request.POST.get('pack_price') or 0,
            quantity        = request.POST.get('quantity') or 0,
            reorder_level   = request.POST.get('reorder_level') or 10,
            expiry_date     = request.POST.get('expiry_date') or None,
            description     = request.POST.get('description', ''),
        )
        cat_id = request.POST.get('category')
        sup_id = request.POST.get('supplier')
        if cat_id: drug.category  = Category.objects.filter(pk=cat_id).first()
        if sup_id: drug.supplier  = Supplier.objects.filter(pk=sup_id).first()
        if request.FILES.get('image'): drug.image = request.FILES['image']
        drug.save()
        messages.success(request, f'Drug "{drug.brand_name}" added.')
        return redirect('inventory:drug_list')
    return render(request, 'inventory/drug_form.html', {
        'action': 'Add', 'categories': Category.objects.all(), 'suppliers': Supplier.objects.filter(is_active=True),
    })


@login_required
def drug_detail(request, pk):
    drug = get_object_or_404(Drug, pk=pk)
    return render(request, 'inventory/drug_detail.html', {'drug': drug})


@login_required
def drug_edit(request, pk):
    drug = get_object_or_404(Drug, pk=pk)
    if request.method == 'POST':
        drug.brand_name      = request.POST.get('brand_name')
        drug.strength        = request.POST.get('strength', '')
        drug.generic_name    = request.POST.get('generic_name')
        drug.barcode         = request.POST.get('barcode') or None
        drug.sale_price      = request.POST.get('sale_price') or 0
        drug.cost_price      = request.POST.get('cost_price') or 0
        drug.pieces_per_pack = request.POST.get('pieces_per_pack') or 1
        drug.pack_price      = request.POST.get('pack_price') or 0
        drug.quantity        = request.POST.get('quantity') or 0
        drug.reorder_level   = request.POST.get('reorder_level') or 10
        drug.expiry_date     = request.POST.get('expiry_date') or None
        drug.description     = request.POST.get('description', '')
        cat_id = request.POST.get('category')
        sup_id = request.POST.get('supplier')
        drug.category = Category.objects.filter(pk=cat_id).first() if cat_id else None
        drug.supplier = Supplier.objects.filter(pk=sup_id).first() if sup_id else None
        if request.FILES.get('image'): drug.image = request.FILES['image']
        drug.is_active = request.POST.get('is_active') == 'on'
        if int(drug.quantity or 0) > 0:
            drug.is_active = True
        drug.save()
        messages.success(request, 'Drug updated.')
        return redirect('inventory:drug_list')
    return render(request, 'inventory/drug_form.html', {
        'action': 'Edit', 'obj': drug,
        'categories': Category.objects.all(), 'suppliers': Supplier.objects.filter(is_active=True),
    })


@login_required
def drug_delete(request, pk):
    drug = get_object_or_404(Drug, pk=pk)
    if request.method == 'POST':
        drug.is_active = False
        drug.save()
        messages.success(request, f'Drug "{drug.brand_name}" removed.')
        return redirect('inventory:drug_list')
    return render(request, 'inventory/drug_confirm_delete.html', {'drug': drug})


@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'inventory/category_list.html', {'categories': categories})


@login_required
def category_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if Category.objects.filter(name__iexact=name).exists():
            messages.error(request, 'Category already exists.')
        else:
            Category.objects.create(name=name, description=request.POST.get('description', ''))
            messages.success(request, f'Category "{name}" added.')
            return redirect('inventory:category_list')
    return render(request, 'inventory/category_form.html', {'action': 'Add'})


@login_required
def supplier_list(request):
    suppliers = Supplier.objects.filter(is_active=True)
    return render(request, 'inventory/supplier_list.html', {'suppliers': suppliers})


@login_required
def supplier_add(request):
    if request.method == 'POST':
        Supplier.objects.create(
            name           = request.POST.get('name'),
            phone          = request.POST.get('phone', ''),
            email          = request.POST.get('email', ''),
            address        = request.POST.get('address', ''),
            contact_person = request.POST.get('contact_person', ''),
        )
        messages.success(request, 'Supplier added.')
        return redirect('inventory:supplier_list')
    return render(request, 'inventory/supplier_form.html', {'action': 'Add'})


@login_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.name           = request.POST.get('name')
        supplier.phone          = request.POST.get('phone', '')
        supplier.email          = request.POST.get('email', '')
        supplier.address        = request.POST.get('address', '')
        supplier.contact_person = request.POST.get('contact_person', '')
        supplier.save()
        messages.success(request, 'Supplier updated.')
        return redirect('inventory:supplier_list')
    return render(request, 'inventory/supplier_form.html', {'action': 'Edit', 'obj': supplier})


@login_required
def purchase_list(request):
    purchases = Purchase.objects.select_related('supplier', 'pharmacist').all()
    return render(request, 'inventory/purchase_list.html', {'purchases': purchases})


@login_required
def purchase_add(request):
    if request.method == 'POST':
        supplier = get_object_or_404(Supplier, pk=request.POST.get('supplier'))
        purchase = Purchase.objects.create(
            supplier      = supplier,
            pharmacist    = request.user,
            invoice_no    = request.POST.get('invoice_no', ''),
            purchase_date = request.POST.get('purchase_date') or timezone.now().date(),
            notes         = request.POST.get('notes', ''),
        )
        drug_ids   = request.POST.getlist('drug')
        quantities = request.POST.getlist('quantity')
        costs      = request.POST.getlist('cost_price')
        expiries   = request.POST.getlist('expiry_date')
        total = 0
        for i, drug_id in enumerate(drug_ids):
            if not drug_id: continue
            drug = get_object_or_404(Drug, pk=drug_id)
            qty  = int(quantities[i] or 0)
            cost = float(costs[i] or 0)
            exp  = expiries[i] or None
            PurchaseItem.objects.create(purchase=purchase, drug=drug, quantity=qty, cost_price=cost, expiry_date=exp)
            drug.quantity   += qty
            drug.cost_price  = cost
            if exp: drug.expiry_date = exp
            if drug.quantity > 0:
                drug.is_active = True
            drug.save()
            total += qty * cost
        purchase.total_amount = total
        purchase.status       = 'received'
        purchase.save()
        messages.success(request, f'Purchase order created. Stock updated.')
        return redirect('inventory:purchase_list')
    return render(request, 'inventory/purchase_form.html', {
        'action': 'Add',
        'suppliers': Supplier.objects.filter(is_active=True),
        'drugs':     Drug.objects.filter(is_active=True).order_by('brand_name'),
    })


@login_required
def purchase_detail(request, pk):
    purchase = get_object_or_404(Purchase.objects.select_related('supplier', 'pharmacist').prefetch_related('items__drug'), pk=pk)
    return render(request, 'inventory/purchase_detail.html', {'purchase': purchase})


@login_required
def adjustment_list(request):
    adjustments = StockAdjustment.objects.select_related('drug', 'adjusted_by').all()
    return render(request, 'inventory/adjustment_list.html', {'adjustments': adjustments})


@login_required
def adjustment_add(request):
    if request.method == 'POST':
        drug   = get_object_or_404(Drug, pk=request.POST.get('drug'))
        qty    = int(request.POST.get('quantity_change', 0))
        reason = request.POST.get('reason')
        notes  = request.POST.get('notes', '')
        StockAdjustment.objects.create(drug=drug, adjusted_by=request.user, quantity_change=qty, reason=reason, notes=notes)
        drug.quantity += qty
        drug.save()
        messages.success(request, f'Stock adjusted for {drug.brand_name}.')
        return redirect('inventory:adjustment_list')
    return render(request, 'inventory/adjustment_form.html', {
        'drugs': Drug.objects.filter(is_active=True).order_by('brand_name'),
        'reasons': StockAdjustment.REASON_CHOICES,
    })
