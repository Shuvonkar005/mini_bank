import csv

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from transactions.filters import TransactionFilter
from transactions.models import Transaction

from .models import BankAccount
from .serializers import BankAccountSerializer


class AccountListCreateView(generics.ListCreateAPIView):
    serializer_class = BankAccountSerializer

    def get_queryset(self):
        return BankAccount.objects.filter(owner=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class AccountDetailView(generics.RetrieveAPIView):
    serializer_class = BankAccountSerializer

    def get_queryset(self):
        return BankAccount.objects.filter(owner=self.request.user)


class AccountBalanceView(APIView):
    def get(self, request, pk):
        account = get_object_or_404(BankAccount, pk=pk, owner=request.user)
        return Response(
            {
                'account_number': account.account_number,
                'account_type': account.account_type,
                'balance': account.balance,
            }
        )


class AccountStatementView(APIView):
    """Bonus: download a CSV statement. Optional ?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD"""

    def get(self, request, pk):
        account = get_object_or_404(BankAccount, pk=pk, owner=request.user)
        qs = Transaction.objects.filter(account=account).select_related('related_account')
        qs = TransactionFilter(request.query_params, queryset=qs).qs.order_by('timestamp')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            f'attachment; filename="statement_{account.account_number}.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(['Account', account.account_number])
        writer.writerow(['Current balance', account.balance])
        writer.writerow([])
        writer.writerow(['Date', 'Reference', 'Type', 'Amount', 'Balance after',
                         'Related account', 'Description'])
        for t in qs:
            writer.writerow([
                t.timestamp.strftime('%Y-%m-%d %H:%M:%S'), t.reference, t.transaction_type,
                t.amount, t.balance_after,
                t.related_account.account_number if t.related_account else '',
                t.description,
            ])
        return response
