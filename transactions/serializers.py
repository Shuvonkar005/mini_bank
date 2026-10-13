from decimal import Decimal

from rest_framework import serializers

from accounts.models import BankAccount

from .models import Transaction


class DepositWithdrawSerializer(serializers.Serializer):
    account_number = serializers.CharField()
    amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal('0.01'),
        error_messages={'min_value': 'Amount must be greater than zero.'},
    )
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, attrs):
        user = self.context['request'].user
        try:
            account = BankAccount.objects.get(account_number=attrs['account_number'], owner=user)
        except BankAccount.DoesNotExist:
            raise serializers.ValidationError({'account_number': 'Account not found.'})
        if account.status != BankAccount.Status.ACTIVE:
            raise serializers.ValidationError({'account_number': 'This account is not active.'})
        attrs['account'] = account
        return attrs


class TransferSerializer(serializers.Serializer):
    from_account = serializers.CharField()
    to_account = serializers.CharField()
    amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal('0.01'),
        error_messages={'min_value': 'Amount must be greater than zero.'},
    )
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, attrs):
        user = self.context['request'].user

        if attrs['from_account'] == attrs['to_account']:
            raise serializers.ValidationError(
                {'to_account': 'Cannot transfer money to the same account.'}
            )
        try:
            sender = BankAccount.objects.get(account_number=attrs['from_account'], owner=user)
        except BankAccount.DoesNotExist:
            raise serializers.ValidationError({'from_account': 'Source account not found.'})
        try:
            receiver = BankAccount.objects.get(account_number=attrs['to_account'])
        except BankAccount.DoesNotExist:
            raise serializers.ValidationError({'to_account': 'Destination account not found.'})

        if sender.status != BankAccount.Status.ACTIVE:
            raise serializers.ValidationError({'from_account': 'Source account is not active.'})
        if receiver.status != BankAccount.Status.ACTIVE:
            raise serializers.ValidationError({'to_account': 'Destination account is not active.'})

        attrs['sender'] = sender
        attrs['receiver'] = receiver
        return attrs


class TransactionSerializer(serializers.ModelSerializer):
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    related_account_number = serializers.CharField(
        source='related_account.account_number', read_only=True, default=None
    )

    class Meta:
        model = Transaction
        fields = (
            'id', 'reference', 'transaction_type', 'amount', 'balance_after',
            'account_number', 'related_account_number', 'description', 'timestamp',
        )
