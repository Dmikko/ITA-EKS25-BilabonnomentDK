# Damage Service

Registrering af skader på en lease (og eventuelt vehicle_id).

## Port
5003

## Endpoints
- GET `/health`
- GET `/damages` (+ optional `?status=OPEN` og/eller `?lease_id=<id>`)
- GET `/damages/<int:damage_id>`
- POST `/damages`
- PATCH `/damages/<int:damage_id>/status`

## Fleet integration
Ved oprettelse af skade:
- hvis `vehicle_id` er sendt med, opdateres bilens status i Fleet til `DAMAGED`

ENV:
- `FLEET_BASE_URL` (i docker: typisk `http://fleet_service:5006` eller via gateway depending on setup)

## DB
SQLite: `damage.db` (mountet via docker-compose)
