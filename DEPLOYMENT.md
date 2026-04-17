# Deployment Information

## Public URL

https://lab12-production-fd80.up.railway.app/

## Platform

Railway

## Build & Deploy Summary

1. Chuẩn bị ứng dụng với cấu hình `railway.toml` và start command dùng biến `PORT`.
2. Deploy service lên Railway và nhận public domain.
3. Cập nhật lại domain production sang URL Railway mới.
4. Sử dụng các lệnh `curl` bên dưới để kiểm tra lại health, auth và rate limit trên domain mới.

## Environment Variables Set

- `PORT`
- `REDIS_URL`
- `AGENT_API_KEY`
- `OPENAI_API_KEY` (hoặc mock setup nếu áp dụng)
- `LOG_LEVEL`
- `RATE_LIMIT_PER_MINUTE`
- `MONTHLY_BUDGET_USD`

## Test Commands

### 1) Health Check

```bash
curl https://lab12-production-fd80.up.railway.app/health
```

Expected:

```json
{ "status": "ok" }
```

Actual:

```json
{ "status": "ok" }
```

### 2) Readiness Check

```bash
curl https://lab12-production-fd80.up.railway.app/ready
```

Expected:

```json
{ "status": "ready" }
```

Actual:

```json
{ "detail": "Not Found" }
```

### 3) API Call Without API key

```bash
curl -X POST https://lab12-production-fd80.up.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"hello","history":[]}'
```

Expected: request được chấp nhận mà không cần API key vì auth đang tắt.

### 4) API Call With API key

```bash
curl -X POST https://lab12-production-fd80.up.railway.app/chat \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message":"hello","history":[]}'
```

Expected: `200 OK` + JSON response nếu service có bật auth

### 5) Rate Limit Check

```bash
for i in {1..15}; do
  curl -X POST https://lab12-production-fd80.up.railway.app/chat \
    -H "X-API-Key: YOUR_KEY" \
    -H "Content-Type: application/json" \
    -d '{"message":"test","history":[]}'
done
```

Expected: eventually `429 Too Many Requests`

## Screenshots

- Deployment dashboard: `screenshots/deploy_bai6.png`
