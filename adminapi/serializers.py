from rest_framework import serializers

from users.models import User


class AdminCustomerSerializer(serializers.ModelSerializer):
    account_count = serializers.IntegerField(source='accounts.count', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'phone',
            'address', 'is_staff', 'is_active', 'date_joined', 'account_count',
        )
