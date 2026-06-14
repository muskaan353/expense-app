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
