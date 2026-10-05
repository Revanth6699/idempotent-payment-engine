# Idempotent Payment Processing & Transaction Reconciliation Engine

A reference implementation of a reliable payment-processing platform designed around **idempotent transaction execution, transaction-state management, processor failure simulation, reconciliation, double-entry-style transaction ledgering, event-driven processing, authentication, and ML-based transaction anomaly detection**.

The system focuses on one core financial correctness guarantee:

> **One logical payment intent must result in at most one financial execution, even when the same request is retried or submitted concurrently.**

---

## Overview

Payment systems must handle much more than simply accepting a payment request.

Real payment infrastructure has to deal with:

- Duplicate requests
- Client retries
- Concurrent requests
- Processor failures
- Unknown processor outcomes
- Transaction state transitions
- Reconciliation
- Transaction ledgering
- Authentication and authorization
- Event-driven processing
- Transaction risk and anomaly detection
- Operational monitoring

This project implements these concerns as a modular payment-engine architecture.

The system contains:

```text
React Frontend
      │
      ▼
OAuth2 / JWT Authentication
      │
      ▼
FastAPI Backend
      │
      ├── Authentication API
      ├── Payment API
      ├── Transaction API
      ├── Reconciliation API
      ├── Risk API
      └── Monitoring API
      │
      ▼
Transaction Orchestrator
      │
      ├── Idempotency Engine
      ├── Transaction State Engine
      └── Payment Processor Simulator
      │
      ├───────────────┐
      ▼               ▼
 PostgreSQL       Redpanda / Kafka
      │               │
      │               ▼
      │        Event-driven processing
      │
      ├── Payment Intents
      ├── Transactions
      ├── Users
      ├── Refresh Tokens
      ├── Reconciliation Records
      ├── Transaction Ledger
      └── Risk Assessments
                      │
                      ▼
              ML Feature Pipeline
                      │
                      ▼
              Anomaly Detection
                      │
                      ▼
                Risk Assessment
                      │
                      ▼
                    MLflow