# Tjekatjeka Holdings Management System

Tjekatjeka is a standalone Ithute Solutions business-management platform for Tjekatjeka Holdings.

It manages the company as one holding operation with separate operational views for:

- Brick Manufacturing & Brick Sales
- Aluminium, Glass, Doors & Window Frames
- Fleet & Vehicle Operations
- Finance, Expenses, Purchases, Customers and Suppliers

## Foundation stack

- Next.js 16 + React 19 frontend
- FastAPI backend
- PostgreSQL owned exclusively by Tjekatjeka
- Alembic migrations
- Redis owned exclusively by Tjekatjeka for product-local cache/coordination
- Central `!thute Auth` for identity; Tjekatjeka never stores user passwords
- Docker Compose for local and production-style deployment

## Core business controls

The first release is designed around cost and usage control rather than only record keeping. It tracks:

- raw-material stock by unit (tonnes, bags, litres, kWh, m², pieces)
- sand, cement, water, electricity, fuel and other production inputs
- brick production batches and material consumption
- rejected/wasted bricks and cost per good brick
- finished-brick stock and sales
- aluminium/glass jobs, quotations, job costs and profit
- purchases, supplier spend and operating expenses
- trucks and small vehicles, fuel usage and maintenance
- consolidated and branch-level management dashboards

## Local development

1. Copy `.env.example` to `.env`.
2. Set `TJEKATJEKA_DB_PASSWORD` to a strong local value.
3. For local work without central Auth, set `TJEKATJEKA_DEV_AUTH_BYPASS=true`.
4. Run `docker compose up --build`.
5. Frontend: `http://localhost:3204`
6. Backend: `http://localhost:8204`
7. API docs: `http://localhost:8204/docs`

Production must keep `TJEKATJEKA_DEV_AUTH_BYPASS=false` and register the configured production callback with central Ithute Auth.

## Business model

Tjekatjeka is one company with shared customers, suppliers, finance and fleet, while each operational record belongs to a branch when applicable. This avoids splitting the business into disconnected applications while still producing separate Brick and Aluminium profitability reports.
