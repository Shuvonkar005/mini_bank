from django.urls import path

from .views import (
    AdminAccountDetailView,
    AdminAccountListView,
    AdminCustomerDetailView,
    AdminCustomerListView,
    AdminTransactionDetailView,
    AdminTransactionListView,
)

urlpatterns = [
    path('admin-api/customers/', AdminCustomerListView.as_view(), name='admin-customers'),
    path('admin-api/customers/<int:pk>/', AdminCustomerDetailView.as_view(), name='admin-customer-detail'),
    path('admin-api/accounts/', AdminAccountListView.as_view(), name='admin-accounts'),
    path('admin-api/accounts/<int:pk>/', AdminAccountDetailView.as_view(), name='admin-account-detail'),
    path('admin-api/transactions/', AdminTransactionListView.as_view(), name='admin-transactions'),
    path('admin-api/transactions/<int:pk>/', AdminTransactionDetailView.as_view(), name='admin-transaction-detail'),
]
