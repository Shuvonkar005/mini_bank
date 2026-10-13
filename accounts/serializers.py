from rest_framework import serializers

from .models import BankAccount


class BankAccountSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = BankAccount
        fields = (
            'id', 'account_number', 'account_type', 'balance',
            'status', 'owner_username', 'created_at',
        )
        read_only_fields = (
            'id', 'account_number', 'balance', 'status', 'owner_username', 'created_at',
        )
