from django.contrib import admin
from .models import Category, Supplier, Drug, Purchase, PurchaseItem, StockAdjustment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'contact_person', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'phone']


@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    list_display = ['brand_name', 'generic_name', 'category', 'sale_price', 'quantity', 'expiry_date', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['brand_name', 'generic_name', 'barcode']


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'supplier', 'status', 'total_amount', 'purchase_date']
    list_filter = ['status']
    inlines = [PurchaseItemInline]


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ['drug', 'quantity_change', 'reason', 'adjusted_by', 'created_at']
    list_filter = ['reason']
