from django.urls import path

from .views import (
    AccountBalanceView,
    AccountDetailView,
    AccountListCreateView,
    AccountStatementView,
)

urlpatterns = [
    path('accounts/', AccountListCreateView.as_view(), name='account-list-create'),
    path('accounts/<int:pk>/', AccountDetailView.as_view(), name='account-detail'),
    path('accounts/<int:pk>/balance/', AccountBalanceView.as_view(), name='account-balance'),
    path('accounts/<int:pk>/statement/', AccountStatementView.as_view(), name='account-statement'),
]
