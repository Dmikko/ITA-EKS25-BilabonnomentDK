# RKI Service

Simuleret kredit-check.

## Port
5005

## Endpoints
- GET `/health`
- POST `/rki/check`

Input:
```json
{ "cpr": "..." }


Output (eksempel):

status: APPROVED / REJECTED / PENDING / SKIPPED

score: float (optional)

reason: string (optional)