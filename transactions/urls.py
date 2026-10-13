from django.urls import path

from .views import DepositView, TransactionListView, TransferView, WithdrawView

urlpatterns = [
    path('transactions/', TransactionListView.as_view(), name='transaction-list'),
    path('transactions/deposit/', DepositView.as_view(), name='deposit'),
    path('transactions/withdraw/', WithdrawView.as_view(), name='withdraw'),
    path('transactions/transfer/', TransferView.as_view(), name='transfer'),
]
