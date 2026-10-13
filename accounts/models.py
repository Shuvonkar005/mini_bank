import random

import django
from django.conf import settings
from django.db import models
from django.db.models import Q


def generate_account_number():
    """Generate a unique 10-digit account number."""
    while True:
        number = str(random.randint(10**9, 10**10 - 1))
        if not BankAccount.objects.filter(account_number=number).exists():
            return number


class BankAccount(models.Model):
    class AccountType(models.TextChoices):
        SAVINGS = 'SAVINGS', 'Savings'
        CURRENT = 'CURRENT', 'Current'

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='accounts'
    )
    account_number = models.CharField(
        max_length=10, unique=True, editable=False, default=generate_account_number
    )
    account_type = models.CharField(max_length=10, choices=AccountType.choices)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # Django 5.1 renamed `check` to `condition` (old name removed in 6.0)
            models.CheckConstraint(
                **{('condition' if django.VERSION >= (5, 1) else 'check'): Q(balance__gte=0)},
                name='balance_never_negative',
            )
        ]

    def __str__(self):
        return f'{self.account_number} ({self.owner})'
