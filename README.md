# AI-Powered Smart Expense Sharing System

Production-oriented Django REST backend for shared expenses, temporal group
membership, multi-currency accounting, reviewed CSV imports, settlements, and
explainable balances.

## Stack

- Django 5 and Django REST Framework
- PostgreSQL in deployed environments
- SimpleJWT authentication
- drf-spectacular OpenAPI and Swagger UI

## Local setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

Set `DATABASE_URL` to a PostgreSQL connection string. If it is omitted, Django
uses SQLite only as a convenient local/test fallback.

Swagger UI is available at `http://127.0.0.1:8000/api/docs/`.

## Project layout

Each domain app keeps transport and business concerns separate through
`models.py`, `serializers.py`, `services.py`, `views.py`, and `urls.py`.

The backend apps are:

- `accounts`
- `groups`
- `expenses`
- `settlements`
- `imports`
- `balances`
- `ai_assistant`

## AI use

Codex was used as the primary development collaborator. See `AI_USAGE.md` for
the prompt log, reviewed mistakes, and corrections.
