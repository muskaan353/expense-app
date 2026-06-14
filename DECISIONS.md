# Decision Log

## PostgreSQL with a local SQLite fallback

Production uses PostgreSQL for transactional consistency, constraints, and
indexing. SQLite remains the default only when `DATABASE_URL` is absent so
checks and tests can run without hiding the production database choice.

## Thin views and explicit services

Views own HTTP concerns, serializers validate API input, models enforce durable
invariants, and services coordinate multi-model transactions. This makes
balance and import rules testable without invoking HTTP.

## API-first delivery

This phase intentionally contains no frontend. OpenAPI documentation is treated
as the executable interface for a future web or mobile client.

## Store converted base amounts

Every expense and settlement stores both its original amount/currency and the
converted group-base amount plus the exact exchange-rate record used. Historical
balances therefore do not change when a later exchange rate is added.

## Derive balances from the ledger

Balances are calculated from active expenses, splits, and settlements. No
mutable balance table exists, preventing cached totals from drifting away from
their source transactions. Each member summary includes the contributing rows.

## Ground the assistant in deterministic services

The assistant cannot write ledger data and does not invent totals. It translates
questions into responses built from the tested balance service and includes
expense or settlement references when explaining a number. A future LLM provider
can improve language without becoming the accounting authority.
