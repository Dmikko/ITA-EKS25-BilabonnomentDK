# Reservation Service

Afhentningsflow (pickup) på baggrund af eksisterende lease.

## Port
5007

## Endpoints
- GET `/health`
- GET `/reservations` (+ optional filters fx `?status=PENDING`)
- GET `/reservations/<int:reservation_id>`
- POST `/reservations`
- PATCH `/reservations/<int:reservation_id>/status`

## Lokation
Pickup lokation baseres på flådedata (delivery_location) ud fra vehicle_id.

## Status flow (TO-BE)
- PENDING
- READY
- PICKED_UP
- CANCELLED

## DB
SQLite: `reservation.db` (mount anbefales via docker-compose)

Tip: “unable to open database file” opstår ofte hvis du ikke har oprettet en tom fil,
og Docker derfor laver en folder med samme navn.
