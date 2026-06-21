from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('superuser', 'Superuser'),
        ('partner', 'Partner'),
        ('pharmacist', 'Pharmacist'),
        ('cashier', 'Cashier'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='cashier')
    phone = models.CharField(max_length=20, blank=True)

    def is_superuser_role(self):
        return self.role == 'superuser' or self.is_superuser

    def is_partner(self):
        return self.role == 'partner'

    def is_pharmacist(self):
        return self.role == 'pharmacist'

    def is_cashier(self):
        return self.role == 'cashier'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"


class Partner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='partner_profile')
    ownership_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    joined_date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.ownership_percent}%"


class Counter(models.Model):
    name = models.CharField(max_length=100)
    cashier = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_counter',
        limit_choices_to={'role': 'cashier'}
    )
    is_main = models.BooleanField(default=False, help_text='Main counter can receive cash for all pending orders')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} {'(Main)' if self.is_main else ''}"
