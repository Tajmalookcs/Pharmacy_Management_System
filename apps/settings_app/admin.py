from django.contrib import admin
from .models import PharmacySettings


@admin.register(PharmacySettings)
class PharmacySettingsAdmin(admin.ModelAdmin):
    list_display = ['pharmacy_name', 'currency', 'tax_rate', 'return_days', 'updated_at']
