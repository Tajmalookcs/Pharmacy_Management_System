from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Partner, Counter


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'get_full_name', 'role', 'phone', 'is_active']
    list_filter = ['role', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Contact', {'fields': ('role', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role & Contact', {'fields': ('role', 'phone')}),
    )


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ['user', 'ownership_percent', 'joined_date']


@admin.register(Counter)
class CounterAdmin(admin.ModelAdmin):
    list_display = ['name', 'cashier', 'is_active', 'created_at']
