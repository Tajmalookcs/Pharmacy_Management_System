from django.db import models
from django.utils import timezone
from django.conf import settings
from apps.inventory.models import Drug
from apps.accounts.models import Counter


class Customer(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.phone})" if self.phone else self.name

    def total_purchases(self):
        return self.sales.filter(status='completed').aggregate(
            total=models.Sum('total_amount')
        )['total'] or 0


class Sale(models.Model):
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('partial', 'Partial'),
    ]
    invoice_no = models.CharField(max_length=20, unique=True, editable=False)
    counter = models.ForeignKey(Counter, on_delete=models.SET_NULL, null=True, related_name='sales')
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sales')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    sale_date = models.DateTimeField(default=timezone.now)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='received_sales'
    )
    received_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sale_date']

    def __str__(self):
        return self.invoice_no

    def save(self, *args, **kwargs):
        if not self.invoice_no:
            last = Sale.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.invoice_no = f"INV-{next_id:05d}"
        super().save(*args, **kwargs)

    def can_return(self):
        delta = timezone.now().date() - self.sale_date.date()
        return delta.days <= 15 and self.status == 'completed'


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    drug = models.ForeignKey(Drug, on_delete=models.PROTECT, related_name='sale_items')
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.drug.brand_name} x{self.quantity}"

    def subtotal(self):
        return (self.unit_price * self.quantity) - self.discount


class Return(models.Model):
    TYPE_CHOICES = [
        ('cash', 'Cash Refund'),
        ('exchange', 'Drug Exchange'),
    ]
    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name='returns')
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    return_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reason = models.TextField(blank=True)
    return_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-return_date']

    def __str__(self):
        return f"Return for {self.sale.invoice_no}"


class ReturnItem(models.Model):
    return_record = models.ForeignKey(Return, on_delete=models.CASCADE, related_name='items')
    drug = models.ForeignKey(Drug, on_delete=models.PROTECT)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    exchange_drug = models.ForeignKey(
        Drug, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='exchange_items'
    )

    def __str__(self):
        return f"{self.drug.brand_name} x{self.quantity}"

    def subtotal(self):
        return self.unit_price * self.quantity


class DayClosing(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]
    counter = models.ForeignKey(Counter, on_delete=models.PROTECT, related_name='day_closings')
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='day_closings')
    closing_date = models.DateField(default=timezone.now)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_returns = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    expected_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    difference = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    notes = models.TextField(blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-closing_date']
        unique_together = ['counter', 'closing_date']

    def __str__(self):
        return f"{self.counter.name} — {self.closing_date}"

    def calculate_difference(self):
        self.difference = self.actual_cash - self.expected_cash
        return self.difference
