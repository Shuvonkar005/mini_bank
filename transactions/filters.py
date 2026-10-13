import django_filters

from .models import Transaction


class TransactionFilter(django_filters.FilterSet):
    transaction_type = django_filters.ChoiceFilter(choices=Transaction.TransactionType.choices)
    account = django_filters.CharFilter(field_name='account__account_number')
    date_from = django_filters.DateFilter(field_name='timestamp', lookup_expr='date__gte')
    date_to = django_filters.DateFilter(field_name='timestamp', lookup_expr='date__lte')

    class Meta:
        model = Transaction
        fields = ['transaction_type', 'account', 'date_from', 'date_to']
