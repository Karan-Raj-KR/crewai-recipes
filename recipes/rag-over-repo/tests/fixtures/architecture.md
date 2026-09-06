# Architecture Overview

## Component Structure
The system is built as a microservices architecture using Python 3.12 and FastAPI.
All services communicate asynchronously via NATS message queues.

## Data Layer
Primary data storage is PostgreSQL for relational data and Redis for transient session caching.

## Security Controls
All inter-service API requests are signed using JWT tokens with RSA-256 keys.
