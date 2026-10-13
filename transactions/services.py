"""Business logic for money movement. Every function is atomic and locks account rows."""
from django.conf import settings
from django.db import transaction as db_transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from accounts.models import BankAccount

from .models import Transaction


def deposit(account_id, amount, description=''):
    with db_transaction.atomic():
        account = BankAccount.objects.select_for_update().get(pk=account_id)
        account.balance += amount
        account.save(update_fields=['balance'])
        return Transaction.objects.create(
            account=account,
            transaction_type=Transaction.TransactionType.DEPOSIT,
            amount=amount,
            balance_after=account.balance,
            description=description,
        )


def _withdrawn_today(account):
    total = Transaction.objects.filter(
        account=account,
        transaction_type=Transaction.TransactionType.WITHDRAWAL,
        timestamp__date=timezone.localdate(),
    ).aggregate(total=Sum('amount'))['total']
    return total or 0


def withdraw(account_id, amount, description=''):
    with db_transaction.atomic():
        account = BankAccount.objects.select_for_update().get(pk=account_id)
        if account.balance < amount:
            raise ValidationError({'amount': 'Insufficient balance.'})

        limit = settings.DAILY_WITHDRAWAL_LIMIT
        already = _withdrawn_today(account)
        if already + amount > limit:
            remaining = max(limit - already, 0)
            raise ValidationError(
                {'amount': f'Daily withdrawal limit exceeded. Remaining today: {remaining}.'}
            )

        account.balance -= amount
        account.save(update_fields=['balance'])
        return Transaction.objects.create(
            account=account,
            transaction_type=Transaction.TransactionType.WITHDRAWAL,
            amount=amount,
            balance_after=account.balance,
            description=description,
        )


def transfer(sender_id, receiver_id, amount, description=''):
    with db_transaction.atomic():
        # Lock both rows in a fixed order (by pk) so opposite transfers cannot deadlock.
        locked = {
            acc.pk: acc
            for acc in BankAccount.objects.select_for_update()
            .filter(pk__in=[sender_id, receiver_id])
            .order_by('pk')
        }
        sender = locked[sender_id]
        receiver = locked[receiver_id]

        if sender.balance < amount:
            raise ValidationError({'amount': 'Insufficient balance.'})

        sender.balance -= amount
        receiver.balance += amount
        sender.save(update_fields=['balance'])
        receiver.save(update_fields=['balance'])

        out_txn = Transaction.objects.create(
            account=sender, related_account=receiver,
            transaction_type=Transaction.TransactionType.TRANSFER_OUT,
            amount=amount, balance_after=sender.balance, description=description,
        )
        Transaction.objects.create(
            account=receiver, related_account=sender,
            transaction_type=Transaction.TransactionType.TRANSFER_IN,
            amount=amount, balance_after=receiver.balance, description=description,
        )
        return out_txn
