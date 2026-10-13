import uuid

from django.db import models


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        DEPOSIT = 'DEPOSIT', 'Deposit'
        WITHDRAWAL = 'WITHDRAWAL', 'Withdrawal'
        TRANSFER_OUT = 'TRANSFER_OUT', 'Transfer Out'
        TRANSFER_IN = 'TRANSFER_IN', 'Transfer In'

    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    account = models.ForeignKey(
        'accounts.BankAccount', on_delete=models.PROTECT, related_name='transactions'
    )
    related_account = models.ForeignKey(
        'accounts.BankAccount', on_delete=models.PROTECT,
        related_name='related_transactions', null=True, blank=True,
    )
    transaction_type = models.CharField(max_length=15, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    balance_after = models.DecimalField(max_digits=14, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.transaction_type} {self.amount} - {self.account.account_number}'
