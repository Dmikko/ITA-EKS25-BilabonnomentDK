# Lease Service

Håndterer lejeaftaler.

## Port
5002

## Endpoints
- GET `/health`
- GET `/leases` (+ optional `?status=ACTIVE|COMPLETED|...`)
- GET `/leases/<int:lease_id>`
- POST `/leases`
- PATCH `/leases/<int:lease_id>/status`
- PATCH `/leases/<int:lease_id>/end`

## Noter om data
- Leases indeholder `vehicle_id` (tilknytning til flåden)
- Oprettelse beregner end_date ud fra start_date + antal måneder (12/24/36) i frontend (pt.)
- RKI-check sker via rki_service (integreret i create flow)

## DB
SQLite: `lease.db` (mountet via docker-compose)
ENV:
- `LEASE_DB_PATH=/app/lease.db`

## RKI integration
ENV:
- `RKI_BASE_URL=http://rki_service:5005`
