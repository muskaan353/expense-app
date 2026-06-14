# Scope and Schema

## Current scope

This repository implements the backend architecture for authentication, groups,
membership history, expenses, settlements, exchange rates, reviewed imports,
balances, and an AI-assistant boundary. Frontend and deployment are outside this
phase.

## Import anomaly policy

Import rows are staged before they can affect balances. Every detected problem
becomes an `ImportIssue` with its source row, severity, proposed action, review
state, and resolution notes. Ambiguous corrections are never applied silently.

The exact anomaly catalog will be expanded when the assignment CSV is available
in the repository.

## Database schema

- `accounts.User`: email-based identity
- `groups.Group`: ownership and base currency
- `groups.GroupMembership`: role plus non-overlapping join/leave periods
- `expenses.ExchangeRate`: dated, sourced currency conversion
- `expenses.Expense`: original and converted amount, payer, date, split type
- `expenses.ExpenseSplit`: each participant's converted liability and input value
- `settlements.Settlement`: payment between two members
- `imports.ImportSession`: immutable upload identity and generated report
- `imports.ImportRow`: staged raw and normalized source row
- `imports.ImportIssue`: reviewable anomaly and proposed action

Balances and assistant responses are derived read models rather than stored
tables.

## Supported split types

- Equal
- Exact base-currency amounts
- Percentage
- Weighted shares
