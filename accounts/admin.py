from django.contrib import admin

from .models import BankAccount


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'owner', 'account_type', 'balance', 'status')
    list_filter = ('account_type', 'status')
    search_fields = ('account_number', 'owner__username')
