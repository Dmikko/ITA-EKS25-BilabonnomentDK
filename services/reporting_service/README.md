# Reporting Service

Samler data fra gateway og udstiller KPI’er til dashboard.

## Port
5004

## Endpoints
- GET `/health`
- GET `/reporting/kpi/overview`

## Datakilder (via gateway)
- `/leases`
- `/damages`
- `/fleet/vehicles` (hvis relevant for KPI’er)
- `/reservations` (hvis relevant for KPI’er)

ENV:
- `GATEWAY_BASE_URL=http://gateway:8000`

## DB
Ingen egen DB (beregner KPI’er on-demand)
