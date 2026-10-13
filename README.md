# Mini Bank Management System API

A REST API built with Django REST Framework. Customers can register, manage bank accounts,
deposit, withdraw, transfer money, and view their transaction history. Admin users can view
all customers, accounts, and transactions.

## Features
- Token authentication (register, login, view/update own profile)
- Bank accounts (Savings / Current) with unique auto-generated 10-digit account numbers
- Deposit, withdraw, transfer with full validation
- Paginated transaction history, filter by type, account and date range
- Admin-only endpoints (`is_staff` users)
- Money stored in `DecimalField`; balances can never go negative (validation + DB constraint)
- Atomic operations with row locking (`transaction.atomic` + `select_for_update`)
- **Bonus:** date-range filter, daily withdrawal limit, CSV account statement, unit tests

## Tech stack
Python 3.10+, Django, Django REST Framework, django-filter, SQLite (default)

## Project structure
```
config/        project settings and root urls
users/         custom User model, register, login, profile
accounts/      BankAccount model, account endpoints, statement
transactions/  Transaction model, deposit/withdraw/transfer, history, business logic (services.py)
adminapi/      admin-only read endpoints
```

## Setup
```bash
git clone https://github.com/Shuvonkar005/mini_bank
cd mini_bank

python -m venv venv
# Windows:      venv\Scripts\activate
# Linux / Mac:  source venv/bin/activate

pip install -r requirements.txt

python manage.py makemigrations users accounts transactions
python manage.py migrate
python manage.py createsuperuser      # this user is the admin
python manage.py runserver
```
API base URL: `http://127.0.0.1:8000/api/`

## Environment / settings
No `.env` is required for development (SQLite). Relevant settings in `config/settings.py`:
- `TIME_ZONE = 'Asia/Dhaka'`
- `DAILY_WITHDRAWAL_LIMIT` (default 50,000.00 per account per day)
- `PAGE_SIZE = 10`

## Authentication
Login/register returns a token. Send it on every private request:
```
Authorization: Token <your_token>
```

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/register/` | Register a customer |
| POST | `/api/auth/login/` | Login, returns token |
| GET / PATCH | `/api/profile/` | View / update own profile |
| GET / POST | `/api/accounts/` | List own accounts / create account |
| GET | `/api/accounts/<id>/` | Account details |
| GET | `/api/accounts/<id>/balance/` | Check balance |
| GET | `/api/accounts/<id>/statement/` | Download CSV statement (supports `date_from`, `date_to`) |
| POST | `/api/transactions/deposit/` | Deposit money |
| POST | `/api/transactions/withdraw/` | Withdraw money |
| POST | `/api/transactions/transfer/` | Transfer money |
| GET | `/api/transactions/` | Own transaction history (paginated) |
| GET | `/api/admin-api/customers/` (+ `<id>/`) | Admin: all customers |
| GET | `/api/admin-api/accounts/` (+ `<id>/`) | Admin: all accounts |
| GET | `/api/admin-api/transactions/` (+ `<id>/`) | Admin: all transactions |

### Request examples

**Register**
```json
POST /api/auth/register/
{
  "username": "rahim", "email": "rahim@example.com",
  "password": "StrongPass#123", "password2": "StrongPass#123",
  "first_name": "Rahim", "last_name": "Uddin", "phone": "01700000000", "address": "Dhaka"
}
```

**Create account** `POST /api/accounts/`
```json
{ "account_type": "SAVINGS" }
```

**Deposit / Withdraw** `POST /api/transactions/deposit/` or `/withdraw/`
```json
{ "account_number": "1234567890", "amount": "5000.00", "description": "Salary" }
```

**Transfer** `POST /api/transactions/transfer/`
```json
{ "from_account": "1234567890", "to_account": "0987654321", "amount": "1000.00", "description": "Rent" }
```
A transfer creates two records: `TRANSFER_OUT` on the sender and `TRANSFER_IN` on the receiver.

### Transaction history filters
```
GET /api/transactions/?transaction_type=DEPOSIT
GET /api/transactions/?account=1234567890
GET /api/transactions/?date_from=2026-10-01&date_to=2026-10-31
GET /api/transactions/?page=2
```
Types: `DEPOSIT`, `WITHDRAWAL`, `TRANSFER_OUT`, `TRANSFER_IN`.

## Business rules enforced
- Account numbers are unique
- Amounts must be positive with at most 2 decimal places
- Balance can never become negative
- Only the owner can deposit, withdraw, or transfer from an account
- Customers cannot see other customers' accounts or transactions (they receive 404)
- Cannot transfer to the same account
- Failed operations never change balances (atomic transactions)
- Daily withdrawal limit per account

## HTTP status codes
`200` OK, `201` created, `400` validation error / business rule violation, `401` not authenticated,
`403` not admin, `404` not found.

## Admin
Admin endpoints require a user with `is_staff=True` (e.g. the superuser). Regular customers get `403`.
The Django admin panel is also available at `/admin/`.

## Running tests
```bash
python manage.py test
```
Covers registration/login, account privacy, deposit, withdraw, transfer, failed-transaction safety,
daily limit, history filtering and pagination, and admin permissions.

## Postman
Test flow: register two users, create an account for each, deposit, withdraw, transfer, check
history, then log in as the superuser and call the `/api/admin-api/` endpoints.
