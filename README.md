# Idempotent Payment Processing & Transaction Reconciliation Engine

A reference implementation of a payment-processing platform focused on **idempotent financial execution, transaction-state integrity, failure handling, reconciliation, transaction ledgering, and ML-based anomaly detection**.

> **Status:** Active development  
> **Architecture:** Locked  
> **Backend:** Python + FastAPI  
> **Frontend:** React  
> **Database:** PostgreSQL

## Overview

The system is designed around one core financial invariant:

> **One logical payment intent → at most one financial execution.**

It protects payment execution against duplicate requests and concurrent requests, explicitly models processor outcomes, reconciles unknown outcomes before re-execution, records successful execution in a transaction ledger, and provides an independent ML pipeline for anomaly/risk analysis.

## Architecture

```text
React Frontend
      |
      v
OAuth2 / JWT Authentication
      |
      v
FastAPI APIs
      |
      v
Transaction Orchestrator
      |
      +----------------------+
      |                      |
      v                      v
Idempotency Engine     Transaction State Engine
      |                      |
      +----------+-----------+
                 |
                 v
       Payment Processor Simulator
                 |
                 v
             PostgreSQL
                 |
        +--------+--------+
        |                 |
        v                 v
Transaction Ledger   Reconciliation


ML Feature Pipeline
        |
        v
Anomaly Detection
        |
        v
Risk / Anomaly Results
        |
        v
MLflow
```

PostgreSQL is the authoritative persistent store. Redpanda provides the local Kafka-compatible event infrastructure.

## Core Payment State Model

```text
CREATED
   |
   v
PROCESSING
   |
   +-----------> SUCCESS
   |
   +-----------> FAILED
   |
   +-----------> UNKNOWN
                    |
                    v
               RECONCILING
                 /                      v        v
             SUCCESS   FAILED
```

`UNKNOWN` is not treated as an ordinary failure. It requires reconciliation because the processor may have executed the transaction even when the original response was unavailable.

## Locked Technology Stack

### Frontend
- React
- JSX / JavaScript
- CSS
- Protected application pages
- Payment interface
- Transaction history
- Payment receipt/status
- Risk/anomaly dashboard
- User profile

### Backend
- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic

### Database
- PostgreSQL

The architecture includes storage for:
- Users
- Accounts
- Recipients
- Payment intents
- Transactions
- Idempotency records
- Transaction ledger
- UTR records
- Transaction events
- Reconciliation records
- ML feature metadata
- Risk scores

### Event Infrastructure
- Redpanda
- Kafka-compatible APIs

Event categories:
- Payment events
- Transaction events
- Retry events
- Processor events
- Reconciliation events
- ML feature events

### Machine Learning
Python + scikit-learn with candidate unsupervised anomaly-detection approaches:
- Isolation Forest
- Local Outlier Factor
- Clustering-based anomaly detection
- Statistical anomaly detection

The final model is selected experimentally rather than by arbitrarily combining models.

### ML Experiment Tracking
- MLflow

Tracks:
- Runs
- Parameters
- Metrics
- Artifacts
- Model versions
- Anomaly-model versions

### Data Processing
- Pandas
- NumPy

### Testing
- Pytest

Testing covers unit, API, idempotency, concurrency, transaction processing, failure handling, reconciliation, authentication, risk, and ML behavior.

### Containerization
- Docker
- Docker Compose

Target local services:

```text
React
FastAPI
PostgreSQL
Redpanda
MLflow
```

No Kubernetes or GPU requirement is part of the locked architecture.

## Backend Structure

```text
backend/
├── app/
│   ├── api/
│   │   ├── auth_api.py
│   │   ├── payment_api.py
│   │   ├── transaction_api.py
│   │   ├── reconciliation_api.py
│   │   ├── risk_api.py
│   │   └── monitoring_api.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── events/
│   │   ├── payment_events.py
│   │   ├── payment_event_producer.py
│   │   ├── payment_event_consumer.py
│   │   └── ml_feature_event_consumer.py
│   ├── models/
│   │   ├── payment.py
│   │   ├── transaction_ledger_model.py
│   │   ├── risk_score_model.py
│   │   ├── user_model.py
│   │   └── refresh_token_model.py
│   ├── processors/
│   │   ├── payment_processor.py
│   │   └── simulator_processor.py
│   ├── schemas/
│   │   ├── payment_schemas.py
│   │   ├── anomaly_schemas.py
│   │   ├── risk_schemas.py
│   │   └── auth_schemas.py
│   ├── services/
│   │   ├── payment_service.py
│   │   ├── idempotency_service.py
│   │   ├── transaction_orchestrator_service.py
│   │   ├── transaction_processing_service.py
│   │   ├── transaction_state_service.py
│   │   ├── reconciliation_service.py
│   │   ├── transaction_ledger_service.py
│   │   ├── risk_assessment_service.py
│   │   ├── risk_persistence_service.py
│   │   ├── risk_assessment_pipeline_service.py
│   │   ├── auth_service.py
│   │   └── token_service.py
│   ├── ml/
│   │   ├── anomaly_detection_service.py
│   │   ├── anomaly_experiment_service.py
│   │   ├── anomaly_model_evaluation_service.py
│   │   ├── feature_engineering_service.py
│   │   └── mlflow_tracking_service.py
│   └── main.py
└── tests/
```

## Idempotency

The system does not depend on an unsafe:

```text
check → process → save
```

pattern.

The idempotency key is protected by a database uniqueness constraint and transaction/concurrency handling.

Conceptually:

```text
Request A ─┐
           ├── Same idempotency key
Request B ─┘
                |
                v
       PostgreSQL uniqueness
                |
                v
       At most one execution
```

This is a financial correctness mechanism, not merely a frontend convenience.

## Processor Simulation

The local processor simulator supports:

```text
SUCCESS
FAILED
UNKNOWN
```

This allows controlled testing of normal execution and failure scenarios.

## Reconciliation

Unknown outcomes follow:

```text
PROCESSING
    |
    v
UNKNOWN
    |
    v
RECONCILING
    |
    +----> SUCCESS
    |
    +----> FAILED
```

A successfully reconciled transaction receives its provider transaction ID and can be recorded in the transaction ledger.

This prevents blindly retrying an unknown payment and potentially creating duplicate financial execution.

## Transaction Ledger

Successful transactions are recorded in the transaction ledger.

The ledger is protected against duplicate entries for the same transaction.

The database remains authoritative; Kafka/Redpanda events do not replace the financial ledger.

## Event Pipeline

The event layer supports payment, transaction, retry, processor, reconciliation, and ML feature events.

The ML feature path is:

```text
Transaction
    |
    v
ML Feature Event
    |
    v
Feature Engineering
    |
    v
Anomaly Detection
    |
    v
Risk Assessment
    |
    v
Risk Persistence
    |
    v
MLflow
```

ML processing is deliberately separated from payment correctness.

## Risk and Anomaly Detection

The risk subsystem produces:
- Anomaly score
- Anomaly flag
- Risk score from `0` to `100`
- Risk level

Risk levels:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

The anomaly model does not decide whether money was financially executed. Payment execution remains controlled by the transaction and idempotency layers.

## Authentication

Authentication uses:
- JWT access tokens
- Refresh tokens
- Argon2 password hashing
- OAuth2 bearer-token extraction
- Protected FastAPI endpoints
- Refresh-token rotation
- Active-user validation

Payment, transaction, reconciliation, risk, and monitoring APIs are protected.

Secrets must be provided through environment configuration and must not be committed to source control.

## Database Migrations

Alembic manages database schema changes.

```bash
alembic current
alembic history
alembic upgrade head
```

Always check the current revision before applying migrations.

## Local Development

### Create virtual environment

Windows:

```cmd
python -m venv .venv
.venv\Scripts\activate
```

### Install dependencies

```cmd
pip install -r requirements.txt
```

If the repository is configured through `pyproject.toml`, install according to that configuration.

### Configure environment

Configure the required values such as:

```text
DATABASE_URL
SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES
```

Do not commit real secrets.

### Run migrations

```cmd
alembic upgrade head
```

### Start backend

```cmd
uvicorn backend.app.main:app --reload
```

### Start frontend

From the frontend directory:

```cmd
npm install
npm run dev
```

Use Docker Compose for the local PostgreSQL, Redpanda, and MLflow services when required by the environment.

## Testing

Activate the virtual environment:

```cmd
.venv\Scripts\activate
```

Run the complete test suite:

```cmd
pytest
```

Examples:

```cmd
pytest backend/tests/test_transaction_processing.py
pytest backend/tests/test_idempotency_concurrency.py
pytest backend/tests/test_concurrent_idempotency.py
pytest backend/tests/test_auth_service.py
pytest backend/tests/test_token_service.py
pytest backend/tests/test_auth_api.py
pytest backend/tests/test_anomaly_detection.py
pytest backend/tests/test_mlflow_tracking.py
```

## Frontend

The React application is intended as a visual payment-operations interface rather than a basic CRUD page.

Planned/implemented interface areas include:
- Authentication
- Operations dashboard
- New payment
- Transactions
- Transaction details
- Payment receipt
- Risk intelligence
- User profile
- Account information
- System status

The visual direction uses strong hierarchy, gradients, status indicators, responsive cards, hover states, transitions, and financial-operations styling.

## Important Design Principles

1. **PostgreSQL is authoritative.**
2. **One logical payment intent must have at most one financial execution.**
3. **Idempotency must be database-backed.**
4. **Concurrent requests must be safe.**
5. **UNKNOWN is different from FAILED.**
6. **Unknown outcomes must be reconciled before re-execution.**
7. **Successful execution must be ledgered exactly once.**
8. **Events support asynchronous processing but do not replace the authoritative database.**
9. **ML is independent of financial execution correctness.**
10. **The locked architecture must not be changed without an explicit project decision.**

## Project Constraints

The locked project intentionally excludes:
- Kubernetes
- GPU-dependent processing
- Streamlit as the primary frontend
- Arbitrary ML model combinations
- Production UPI/payment-network integration
- Uncontrolled architectural expansion

The project is a local/reference implementation intended to demonstrate realistic payment-system behavior.

## Current Development Status

The project has progressed beyond a basic CRUD payment application.

Implemented development areas include:
- FastAPI backend
- PostgreSQL persistence
- SQLAlchemy models
- Alembic migrations
- Payment intents
- Transaction processing
- Database-backed idempotency
- Concurrent idempotency protection
- Transaction state machine
- Processor simulation
- Unknown-outcome handling
- Reconciliation
- Transaction ledger
- Redpanda/Kafka event infrastructure
- ML feature event pipeline
- Candidate anomaly detection
- Risk assessment
- Risk persistence
- MLflow tracking infrastructure
- JWT authentication
- Refresh-token handling
- Protected APIs
- Monitoring API
- React frontend foundation
- User/profile functionality under active development

## Repository Layout

```text
idempotent-payment-engine/
├── backend/
├── infrastructure/
│   ├── postgres/
│   │   └── versions/
│   └── redpanda/
├── frontend/
├── docker-compose.yml
├── alembic.ini
├── pyproject.toml
├── README.md
└── .gitignore
```

## License

This project is currently a development/reference implementation. Add the final project license when the repository licensing decision has been finalized.
