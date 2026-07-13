# API Reference - Nexus AI Platform

This document describes the platform infrastructure endpoints.

## 1. Authentication APIs

### Register User
`POST /api/platform/auth/register`
Registers a new user account.

**Request Payload:**
```json
{
  "username": "testuser",
  "password": "secure-password",
  "email": "user@example.com"
}
```

---

### Login User
`POST /api/platform/auth/login`
Verifies credentials and returns access and refresh tokens.

**Request Payload:**
```json
{
  "username": "testuser",
  "password": "secure-password"
}
```

---

### Reset Password
`POST /api/platform/auth/reset-password`
Resets a user's password.

**Request Payload:**
```json
{
  "username": "testuser",
  "new_password": "new-secure-password"
}
```

---

## 2. Operations & Telemetry

### Consolidated Health Checks
`GET /api/platform/health`
Returns aggregate status reports of sub-services.

---

### Metrics
`GET /api/platform/metrics`
Exposes system metrics including total API requests, database queries, and background job counts.
