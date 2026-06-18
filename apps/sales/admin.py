from django.contrib import admin
from .models import Customer, Sale, SaleItem, Return, ReturnItem, DayClosing


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'created_at']
    search_fields = ['name', 'phone']


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['invoice_no', 'counter', 'cashier', 'customer', 'total_amount', 'payment_method', 'status', 'sale_date']
    list_filter = ['status', 'payment_method', 'counter']
    search_fields = ['invoice_no']
    inlines = [SaleItemInline]
    readonly_fields = ['invoice_no']


class ReturnItemInline(admin.TabularInline):
    model = ReturnItem
    extra = 0


@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'return_type', 'refund_amount', 'processed_by', 'return_date']
    list_filter = ['return_type']
    inlines = [ReturnItemInline]


@admin.register(DayClosing)
class DayClosingAdmin(admin.ModelAdmin):
    list_display = ['counter', 'cashier', 'closing_date', 'total_sales', 'expected_cash', 'actual_cash', 'difference', 'status']
    list_filter = ['status', 'counter']
