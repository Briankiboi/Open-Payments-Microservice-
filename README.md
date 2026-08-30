# Open Payments Microservice

## Overview

Open Payments Microservice is a backend service designed to simplify
payment processing for fintech and eCommerce systems.

It provides:
- REST APIs for payment creation and tracking
- Gateway abstraction for integrating multiple payment providers
- Webhook handling for asynchronous confirmations
- Idempotency protection to prevent duplicate payments
- A modular architecture designed for scalability



## Features

- FastAPI REST API
- Payment transaction management
- Idempotency protection
- Gateway adapter architecture
- Webhook event processing
- PostgreSQL persistence
- Redis caching support
- Docker containerization
- OpenAPI documentation
- Unit testing with Pytest

## Architecture


The project strictly follows clean architecture principles, separating models, schemas, REST endpoints, and gateway integrations (e.g. M-Pesa).

```text
payment-microservice/
 ├── app/
 │   ├── api/
 │   │   └── payments.py            # FastAPI REST routers
 │   ├── models/
 │   │   └── payment.py             # SQLAlchemy DB models
 │   ├── schemas/
 │   │   └── payment_schema.py      # Pydantic validation schemas
 │   ├── services/
 │   │   └── payment_service.py     # Core business logic and idempotency
 │   ├── gateways/
 │   │   ├── base_gateway.py        # Abstract base interface via ABC
 │   │   └── mpesa_gateway.py       # Example gateway adapter
 │   ├── webhooks/
 │   │   └── payment_webhook.py     # Webhook handler
 │   ├── core/
 │   │   ├── config.py              # Environment variables initialization
 │   │   └── database.py            # Async SQLAlchemy engine
 │   └── main.py                    # Entrypoint and app factory
 ├── tests/                         # Pytest test suite
 ├── Dockerfile
 └── docker-compose.yml
```

## Database Schema

Understanding the data model is key to contributing to this microservice.

### payments

| Column | Type | Description |
|------|------|-------------|
| id | UUID | Primary key (UUID v4) |
| transaction_id | String | Unique transaction reference |
| amount | Decimal | Numeric(10, 2) payment amount |
| currency | String | 3-letter currency code (e.g. KES) |
| customer_phone | String | Customer mobile identifier |
| status | Enum | pending / success / failed |
| created_at | Timestamp | Record creation timestamp |
| updated_at | Timestamp | Last record modification timestamp |

### payment_logs

| Column | Type | Description |
|------|------|-------------|
| id | UUID | Primary key |
| payment_id | UUID | Foreign key to payments.id |
| gateway_response| JSON | Raw response/payload from the provider |
| created_at | Timestamp | Log creation time |

## Setup & Running with Docker


This project comes pre-configured with a `docker-compose.yml` for running entirely in containers, including the database and Redis cache.

1. Build and run the docker containers:
```bash
docker-compose up --build
```
2. The FastAPI server will be available at `http://localhost:8000`.



### Local Development (Without Docker)

For contributors who prefer running the service locally:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourname/payment-microservice.git
   cd payment-microservice
   ```

2. **Setup virtual environment:**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ensure PostgreSQL and Redis are running:**
   Update your `.env` file with the correct local coordinates.

5. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

## Environment Variables


Create a `.env` file based on the following variables:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/payments
REDIS_URL=redis://redis:6379
MPESA_CONSUMER_KEY=your_key
MPESA_CONSUMER_SECRET=your_secret
MPESA_SHORTCODE=123456
MPESA_PASSKEY=your_passkey
```

## API Documentation

Once running, you can access the interactive OpenAPI/Swagger documentation generated natively by FastAPI at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Core Features & Usage Examples

### 1. Payment Creation API
Creates a new payment in a `pending` state and returns a unique `transaction_id`. Duplicates are prevented if you include the `Idempotency-Key` header.

```bash
curl -X POST "http://localhost:8000/payments" \
     -H "Content-Type: application/json" \
     -H "Idempotency-Key: my-unique-uuid-key" \
     -d '{
           "amount": 1500,
           "currency": "KES",
           "customer_phone": "254700000000"
         }'
```

### 2. Initiate Payment (Gateway Call)
Triggers the backend service to hit the external payment gateway adapter.

```bash
curl -X POST "http://localhost:8000/payments/{transaction_id}/pay"
```

### 3. Payment Status Request
Fetches the current internal DB status of the payment.

```bash
curl -X GET "http://localhost:8000/payments/{transaction_id}"
```

### 4. Webhook Callback Endpoint
Payment gateways will send their asymmetric confirmations back to our webhook handler.

```bash
curl -X POST "http://localhost:8000/webhooks/payment" \
     -H "Content-Type: application/json" \
     -d '{
           "transaction_id": "{transaction_id}",
           "Body": {
             "stkCallback": { "ResultCode": 0, "ResultDesc": "Success" }
           }
         }'
```

## Testing

Run unit tests via Pytest:
```bash
pip install -r requirements.txt
pytest tests/
```

## How to Contribute

We welcome contributions! To get started:

1. **Fork the repository** on GitHub.
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`).
3. **Commit your changes** (`git commit -m 'Add amazing feature'`).
4. **Push to the branch** (`git push origin feature/amazing-feature`).
5. **Submit a pull request**.

### Contribution Principles:
- **Code Quality**: Ensure code passes all tests and follows the project's styling guidelines.
- **Test Coverage**: New features should include relevant unit or integration tests.
- **Documentation**: Update the README or inline comments if your changes affect the public API or setup process.
- **Schemas**: Ensure new endpoints have proper Pydantic validation.
- **Decoupling**: Keep core business logic separate from gateway-specific implementations.


## Roadmap

Planned improvements and future features:

- [x] Implement API-level rate limiting (Phase 2)
- [x] Add background job processing via ARQ (Phase 2)
- [x] Add webhook signature verification (Phase 2)
- [ ] Add **Paystack** gateway adapter
- [ ] Add **Flutterwave** gateway adapter
- [ ] Add **Stripe** gateway adapter
- [ ] Implement automated payment reconciliation jobs
- [ ] Add support for multiple currency conversions (integration with Exchange Rate APIs)
- [ ] Develop a simple Admin Dashboard for transaction monitoring
- [ ] Add support for GraphQL API endpoints
- [ ] Enhance test coverage with real integration tests (Testcontainers for Postgres/Redis)
