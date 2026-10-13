from rest_framework import generics
from rest_framework.permissions import IsAdminUser

from accounts.models import BankAccount
from accounts.serializers import BankAccountSerializer
from transactions.filters import TransactionFilter
from transactions.models import Transaction
from transactions.serializers import TransactionSerializer
from users.models import User

from .serializers import AdminCustomerSerializer


class AdminBase:
    permission_classes = [IsAdminUser]


class AdminCustomerListView(AdminBase, generics.ListAPIView):
    queryset = User.objects.all().order_by('id')
    serializer_class = AdminCustomerSerializer


class AdminCustomerDetailView(AdminBase, generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = AdminCustomerSerializer


class AdminAccountListView(AdminBase, generics.ListAPIView):
    queryset = BankAccount.objects.select_related('owner').order_by('id')
    serializer_class = BankAccountSerializer
    filterset_fields = ['account_type', 'status', 'owner']


class AdminAccountDetailView(AdminBase, generics.RetrieveAPIView):
    queryset = BankAccount.objects.select_related('owner')
    serializer_class = BankAccountSerializer


class AdminTransactionListView(AdminBase, generics.ListAPIView):
    queryset = Transaction.objects.select_related('account', 'related_account').order_by('-timestamp')
    serializer_class = TransactionSerializer
    filterset_class = TransactionFilter


class AdminTransactionDetailView(AdminBase, generics.RetrieveAPIView):
    queryset = Transaction.objects.select_related('account', 'related_account')
    serializer_class = TransactionSerializer
