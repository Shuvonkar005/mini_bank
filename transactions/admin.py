from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'account', 'transaction_type', 'amount', 'timestamp')
    list_filter = ('transaction_type',)
