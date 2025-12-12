# Fleet Service

Flådeoversigt og status på biler.

## Port
5006

## Endpoints
- GET `/health`
- GET `/vehicles` (+ optional `?status=AVAILABLE|LEASED|DAMAGED|REPAIR`)
- GET `/vehicles/<int:vehicle_id>`
- POST `/vehicles/allocate`
- PUT `/vehicles/<int:vehicle_id>/status`
- GET `/vehicles/pricing/by-model`

## Datafelter (typisk)
- `model_name`
- `fuel_type`
- `monthly_price`
- `status`
- `current_lease_id`
- `delivery_location`
- `updated_at`

## DB
SQLite: `fleet.db` (mount anbefales via docker-compose)
