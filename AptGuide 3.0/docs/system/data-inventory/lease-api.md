# Lease API Endpoints -- AptGuide 3.0

Client: `LeaseClient` | Base URL: `lease_base_url` (default `http://localhost:8081`) | Timeout: `lease_timeout_seconds` (default 5 s)

All endpoints are under the `/internal/ai/tools/` path prefix. Authentication uses the `X-User-Id` header for user-scoped endpoints.

---

## Health / Connectivity

There is no dedicated health endpoint in the client. Connectivity is inferred from successful responses on any endpoint.

---

## Room Endpoints

### GET /internal/ai/tools/room/{room_id}

Retrieve details for a single room.

| Parameter | Source |
|---|---|
| room_id | Path parameter (int) |

Returns: `data` object with room details, or `None` on failure.

---

### POST /internal/ai/tools/room/search

Validate and retrieve multiple rooms by ID with optional filters.

| Parameter | Type | Notes |
|---|---|---|
| room_ids | list[int] | Required |
| (filter fields) | varies | Transformed to camelCase before sending |

Returns: list of room objects matching the filters. Client-side filtering applied for `max_rent` and `payment_type`.

---

## Appointment Endpoints

### POST /internal/ai/tools/appointment/create

Create a new appointment.

| Parameter | Type | Notes |
|---|---|---|
| apartmentId | int | Apartment to visit |
| appointmentTime | str | Requested time |
| remark | str | Optional note |
| X-User-Id | header | User identifier |

Returns: `{"ok": true, "data": ...}` or `{"ok": false, "error": "..."}`.

---

### GET /internal/ai/tools/appointment/list-mine

List all appointments for the authenticated user.

| Parameter | Type | Notes |
|---|---|---|
| X-User-Id | header | User identifier |

Returns: list of appointment objects, or `[]` on failure.

---

## Lease Endpoints

### GET /internal/ai/tools/lease/list-mine

List all leases for the authenticated user.

| Parameter | Type | Notes |
|---|---|---|
| X-User-Id | header | User identifier |

Returns: list of lease objects, or `[]` on failure.

---

## Data Handling Notes

- All request/response bodies use camelCase on the wire; the client converts to snake_case internally.
- No tokens, credentials, or customer payload examples are documented here.
- On HTTP errors, all methods return `None` or `[]` -- no exceptions propagate to callers.
