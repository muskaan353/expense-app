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
