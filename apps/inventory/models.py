from django.db import models
from django.utils import timezone
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def total_purchases(self):
        return self.purchases.aggregate(
            total=models.Sum('total_amount')
        )['total'] or 0


class Drug(models.Model):
    brand_name = models.CharField(max_length=200)
    strength = models.CharField(max_length=50, blank=True, help_text='e.g. 500mg, 250ml, 5mg/5ml')
    generic_name = models.CharField(max_length=200, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='drugs')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='drugs')
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pieces_per_pack = models.PositiveIntegerField(default=1, help_text='Number of pieces in one pack/box')
    pack_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Price for a full pack/box')
    quantity = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=10)
    expiry_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='drugs/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['brand_name', 'strength']
        unique_together = [('brand_name', 'strength')]

    def __str__(self):
        return f"{self.brand_name} {self.strength}".strip()

    def is_low_stock(self):
        return self.quantity <= self.reorder_level

    def is_expired(self):
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False

    def is_near_expiry(self, days=30):
        if self.expiry_date:
            delta = self.expiry_date - timezone.now().date()
            return 0 <= delta.days <= days
        return False

    def save(self, *args, **kwargs):
        if self.quantity > 0 and not self.is_active:
            self.is_active = True
        super().save(*args, **kwargs)

    def profit_margin(self):
        if self.sale_price and self.cost_price:
            return self.sale_price - self.cost_price
        return 0


class Purchase(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchases')
    pharmacist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='purchases')
    invoice_no = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    purchase_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-purchase_date']

    def __str__(self):
        return f"PO-{self.id:04d} — {self.supplier.name}"

    def calculate_total(self):
        total = sum(item.subtotal() for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])
        return total


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    drug = models.ForeignKey(Drug, on_delete=models.PROTECT, related_name='purchase_items')
    quantity = models.IntegerField(default=1)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.drug.brand_name} x{self.quantity}"

    def subtotal(self):
        return self.quantity * self.cost_price


class StockAdjustment(models.Model):
    REASON_CHOICES = [
        ('damage', 'Damaged'),
        ('loss', 'Loss / Theft'),
        ('expiry', 'Expired Removal'),
        ('correction', 'Stock Correction'),
        ('other', 'Other'),
    ]
    drug = models.ForeignKey(Drug, on_delete=models.PROTECT, related_name='adjustments')
    adjusted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    quantity_change = models.IntegerField(help_text='Negative to reduce, positive to add')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.drug.brand_name} ({self.quantity_change:+d})"
