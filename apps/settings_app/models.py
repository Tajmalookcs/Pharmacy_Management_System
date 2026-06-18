from django.db import models


class PharmacySettings(models.Model):
    pharmacy_name = models.CharField(max_length=200, default='PharmaPOS')
    tagline = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to='settings/', null=True, blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='Rs')
    return_days = models.IntegerField(default=15)
    receipt_footer = models.TextField(blank=True, default='Thank you for your purchase!')
    low_stock_threshold = models.IntegerField(default=10)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pharmacy Settings'
        verbose_name_plural = 'Pharmacy Settings'

    def __str__(self):
        return self.pharmacy_name

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
