# API Reference — {{PROJECT_NAME}}

> Document all API endpoints here. Update when endpoints are added, modified, or removed.

---

## Authentication

<!-- Describe your authentication method -->
<!-- Example:
### JWT Authentication
- Access token: 15 min expiration
- Refresh token: 7-day expiration
- Header: `Authorization: Bearer <access_token>`
-->

### API Key Authentication

For internal/automation endpoints:
- Header: `X-API-Key: <key>`
- Key must be 32+ characters
- Uses constant-time comparison to prevent timing attacks

---

## Endpoints

### Health Check

```
GET /api/health/
```

**Auth**: None
**Response**:
```json
{
  "status": "ok",
  "timestamp": "2026-01-01T12:00:00-05:00"
}
```

<!-- Add your endpoints here, organized by module -->

<!--
### Module Name

#### List Items
```
GET /api/v1/items/
```
**Auth**: JWT
**Query Params**: `page`, `page_size`, `status`
**Response**: Paginated list of items

#### Create Item
```
POST /api/v1/items/
```
**Auth**: JWT
**Body**:
```json
{
  "name": "string",
  "description": "string"
}
```
**Response**: Created item (201)
-->

---

## Webhook Endpoints

<!-- Document incoming webhook endpoints -->
<!--
### Stripe Webhooks
```
POST /webhooks/stripe/v1/
```
**Auth**: Stripe signature verification (HMAC-SHA256)
**Events handled**: `payment_intent.succeeded`, `charge.refunded`, etc.
-->

---

## Error Responses

All error responses follow this format:
```json
{
  "error": "error_code",
  "message": "Human-readable description",
  "details": {}
}
```

| HTTP Code | Meaning |
|-----------|---------|
| 400 | Bad Request — invalid input |
| 401 | Unauthorized — missing or invalid auth |
| 403 | Forbidden — insufficient permissions |
| 404 | Not Found |
| 429 | Rate Limited |
| 500 | Internal Server Error |

---

**Last Updated**: {{DATE}}
