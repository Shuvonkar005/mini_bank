from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .filters import TransactionFilter
from .models import Transaction
from .serializers import (
    DepositWithdrawSerializer,
    TransactionSerializer,
    TransferSerializer,
)


class DepositView(APIView):
    def post(self, request):
        serializer = DepositWithdrawSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        txn = services.deposit(data['account'].id, data['amount'], data.get('description', ''))
        return Response(
            {'message': 'Deposit successful.', 'transaction': TransactionSerializer(txn).data},
            status=status.HTTP_201_CREATED,
        )


class WithdrawView(APIView):
    def post(self, request):
        serializer = DepositWithdrawSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        txn = services.withdraw(data['account'].id, data['amount'], data.get('description', ''))
        return Response(
            {'message': 'Withdrawal successful.', 'transaction': TransactionSerializer(txn).data},
            status=status.HTTP_201_CREATED,
        )


class TransferView(APIView):
    def post(self, request):
        serializer = TransferSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        txn = services.transfer(
            data['sender'].id, data['receiver'].id, data['amount'], data.get('description', '')
        )
        return Response(
            {'message': 'Transfer successful.', 'transaction': TransactionSerializer(txn).data},
            status=status.HTTP_201_CREATED,
        )


class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    filterset_class = TransactionFilter

    def get_queryset(self):
        return (
            Transaction.objects.filter(account__owner=self.request.user)
            .select_related('account', 'related_account')
            .order_by('-timestamp')
        )
