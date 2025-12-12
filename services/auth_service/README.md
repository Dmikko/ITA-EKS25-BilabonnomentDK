# Auth Service

JWT-auth + bruger/roller.

## Port
5001

## Endpoints
- GET `/health`
- POST `/login`
- GET `/me`
- GET `/users`
- POST `/users`
- PATCH `/users/<int:user_id>/role`

## Default users
- admin/admin
- data/data
- skade/skade
- forret/forret
- ledelse/ledelse

## Roller
`DATAREG`, `SKADE`, `FORRET`, `LEDELSE`, `ADMIN`

## DB
SQLite: `auth.db` (typisk mountet til `/app/auth.db` via docker-compose)
