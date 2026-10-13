from decimal import Decimal

from django.test import override_settings
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import BankAccount
from transactions.models import Transaction
from users.models import User


class BankTestBase(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user('alice', 'alice@x.com', 'Pass#12345')
        self.bob = User.objects.create_user('bob', 'bob@x.com', 'Pass#12345')
        self.admin = User.objects.create_superuser('boss', 'boss@x.com', 'Pass#12345')
        self.alice_acc = BankAccount.objects.create(
            owner=self.alice, account_type='SAVINGS', balance=Decimal('1000.00')
        )
        self.alice_acc2 = BankAccount.objects.create(
            owner=self.alice, account_type='CURRENT', balance=Decimal('0.00')
        )
        self.bob_acc = BankAccount.objects.create(
            owner=self.bob, account_type='SAVINGS', balance=Decimal('500.00')
        )

    def login(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def balance(self, acc):
        acc.refresh_from_db()
        return acc.balance


class AuthTests(APITestCase):
    def test_register_login_profile(self):
        data = {
            'username': 'newuser', 'email': 'n@x.com',
            'password': 'Str0ng#Pass1', 'password2': 'Str0ng#Pass1',
        }
        r = self.client.post(reverse('register'), data)
        self.assertEqual(r.status_code, 201)
        self.assertIn('token', r.data)

        r = self.client.post(reverse('login'), {'username': 'newuser', 'password': 'Str0ng#Pass1'})
        self.assertEqual(r.status_code, 200)

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {r.data["token"]}')
        r = self.client.patch(reverse('profile'), {'phone': '017'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['phone'], '017')

    def test_password_mismatch(self):
        r = self.client.post(reverse('register'), {
            'username': 'u', 'email': 'u@x.com', 'password': 'Str0ng#Pass1', 'password2': 'nope',
        })
        self.assertEqual(r.status_code, 400)

    def test_profile_requires_auth(self):
        self.assertEqual(self.client.get(reverse('profile')).status_code, 401)


class AccountTests(BankTestBase):
    def test_create_account_ignores_balance_and_number(self):
        self.login(self.alice)
        r = self.client.post(reverse('account-list-create'),
                             {'account_type': 'SAVINGS', 'balance': '99999', 'account_number': '1'})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Decimal(r.data['balance']), 0)
        self.assertEqual(len(r.data['account_number']), 10)

    def test_cannot_see_other_customers_account(self):
        self.login(self.bob)
        self.assertEqual(self.client.get(reverse('account-detail', args=[self.alice_acc.id])).status_code, 404)
        self.assertEqual(self.client.get(reverse('account-balance', args=[self.alice_acc.id])).status_code, 404)
        r = self.client.get(reverse('account-list-create'))
        self.assertEqual(r.data['count'], 1)

    def test_statement_csv(self):
        self.login(self.alice)
        r = self.client.get(reverse('account-statement', args=[self.alice_acc.id]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'text/csv')


class DepositWithdrawTests(BankTestBase):
    def test_deposit(self):
        self.login(self.alice)
        r = self.client.post(reverse('deposit'),
                             {'account_number': self.alice_acc.account_number, 'amount': '250.50'})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.balance(self.alice_acc), Decimal('1250.50'))
        self.assertEqual(Transaction.objects.filter(transaction_type='DEPOSIT').count(), 1)

    def test_withdraw(self):
        self.login(self.alice)
        r = self.client.post(reverse('withdraw'),
                             {'account_number': self.alice_acc.account_number, 'amount': '400'})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.balance(self.alice_acc), Decimal('600.00'))

    def test_invalid_amounts_rejected(self):
        self.login(self.alice)
        for amount in ['0', '-5', '10.555', 'abc']:
            r = self.client.post(reverse('deposit'),
                                 {'account_number': self.alice_acc.account_number, 'amount': amount})
            self.assertEqual(r.status_code, 400, amount)
        self.assertEqual(self.balance(self.alice_acc), Decimal('1000.00'))
        self.assertEqual(Transaction.objects.count(), 0)

    def test_insufficient_balance(self):
        self.login(self.alice)
        r = self.client.post(reverse('withdraw'),
                             {'account_number': self.alice_acc.account_number, 'amount': '1000.01'})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.balance(self.alice_acc), Decimal('1000.00'))
        self.assertEqual(Transaction.objects.count(), 0)

    def test_cannot_use_someone_elses_account(self):
        self.login(self.bob)
        for url in ('deposit', 'withdraw'):
            r = self.client.post(reverse(url),
                                 {'account_number': self.alice_acc.account_number, 'amount': '10'})
            self.assertEqual(r.status_code, 400)
        self.assertEqual(self.balance(self.alice_acc), Decimal('1000.00'))

    @override_settings(DAILY_WITHDRAWAL_LIMIT=Decimal('300.00'))
    def test_daily_limit(self):
        self.login(self.alice)
        url = reverse('withdraw')
        num = self.alice_acc.account_number
        self.assertEqual(self.client.post(url, {'account_number': num, 'amount': '200'}).status_code, 201)
        self.assertEqual(self.client.post(url, {'account_number': num, 'amount': '101'}).status_code, 400)
        self.assertEqual(self.client.post(url, {'account_number': num, 'amount': '100'}).status_code, 201)
        self.assertEqual(self.balance(self.alice_acc), Decimal('700.00'))


class TransferTests(BankTestBase):
    def payload(self, **kw):
        data = {'from_account': self.alice_acc.account_number,
                'to_account': self.bob_acc.account_number, 'amount': '300.00'}
        data.update(kw)
        return data

    def test_transfer_success_updates_both_and_records_two_transactions(self):
        self.login(self.alice)
        r = self.client.post(reverse('transfer'), self.payload())
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.balance(self.alice_acc), Decimal('700.00'))
        self.assertEqual(self.balance(self.bob_acc), Decimal('800.00'))
        self.assertEqual(Transaction.objects.filter(transaction_type='TRANSFER_OUT').count(), 1)
        self.assertEqual(Transaction.objects.filter(transaction_type='TRANSFER_IN').count(), 1)

    def test_transfer_between_own_accounts(self):
        self.login(self.alice)
        r = self.client.post(reverse('transfer'),
                             self.payload(to_account=self.alice_acc2.account_number))
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.balance(self.alice_acc2), Decimal('300.00'))

    def test_failed_transfers_change_nothing(self):
        self.login(self.alice)
        bad = [
            self.payload(to_account=self.alice_acc.account_number),   # same account
            self.payload(amount='0'),
            self.payload(amount='-1'),
            self.payload(amount='5000'),                              # insufficient
            self.payload(to_account='0000000000'),                    # unknown
            self.payload(from_account=self.bob_acc.account_number,    # not owner
                         to_account=self.alice_acc.account_number),
        ]
        for data in bad:
            self.assertEqual(self.client.post(reverse('transfer'), data).status_code, 400, data)
        self.assertEqual(self.balance(self.alice_acc), Decimal('1000.00'))
        self.assertEqual(self.balance(self.bob_acc), Decimal('500.00'))
        self.assertEqual(Transaction.objects.count(), 0)


class HistoryAndAdminTests(BankTestBase):
    def setUp(self):
        super().setUp()
        self.login(self.alice)
        num = self.alice_acc.account_number
        for _ in range(12):
            self.client.post(reverse('deposit'), {'account_number': num, 'amount': '10'})
        self.client.post(reverse('withdraw'), {'account_number': num, 'amount': '5'})

    def test_pagination_and_filter(self):
        r = self.client.get(reverse('transaction-list'))
        self.assertEqual(r.data['count'], 13)
        self.assertEqual(len(r.data['results']), 10)
        r = self.client.get(reverse('transaction-list'), {'transaction_type': 'WITHDRAWAL'})
        self.assertEqual(r.data['count'], 1)
        r = self.client.get(reverse('transaction-list'), {'transaction_type': 'ABC'})
        self.assertEqual(r.status_code, 400)

    def test_history_is_private(self):
        self.login(self.bob)
        r = self.client.get(reverse('transaction-list'))
        self.assertEqual(r.data['count'], 0)

    def test_admin_endpoints_forbidden_for_customers(self):
        for name in ('admin-customers', 'admin-accounts', 'admin-transactions'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 403, name)

    def test_admin_can_view_everything(self):
        self.login(self.admin)
        self.assertEqual(self.client.get(reverse('admin-customers')).data['count'], 3)
        self.assertEqual(self.client.get(reverse('admin-accounts')).data['count'], 3)
        self.assertEqual(self.client.get(reverse('admin-transactions')).data['count'], 13)
