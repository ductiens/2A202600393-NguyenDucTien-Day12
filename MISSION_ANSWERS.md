# Day 12 Lab - Mission Answers

Student Name: Nguyen Duc Tien  
Student ID: 2A202600393  
Date: 2026-04-17

---

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found

1. Hardcode secret trực tiếp trong source code (`OPENAI_API_KEY`, `DATABASE_URL`) là không an toàn vì rất dễ bị lộ qua Git history, log hoặc repository public.
2. Không có cơ chế quản lý cấu hình đúng nghĩa: `DEBUG`, `MAX_TOKENS`, host và port đều bị ghi cứng thay vì đọc từ biến môi trường, nên ứng dụng khó chạy ổn định ở nhiều môi trường khác nhau.
3. Bản develop chưa sẵn sàng cho production vì không có health endpoint, chỉ bind vào `localhost`, và chạy với `reload=True`, nên không phù hợp để deploy cloud/container.

### Exercise 1.3: Develop vs Production comparison

| Feature           | Develop                                           | Production                                                                        | Why Important?                                                   |
| ----------------- | ------------------------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Config management | Ghi cứng trong `app.py`                           | Tập trung ở `config.py`, đọc từ env vars                                          | Giúp cùng một codebase chạy được ở dev/staging/prod              |
| Secrets handling  | Secret bị hardcode và còn có thể in ra log        | Secret đọc từ env vars, production có validate để chặn giá trị mặc định nguy hiểm | Tránh lộ secret và giảm rủi ro bảo mật                           |
| Logging           | Dùng `print()` để debug                           | Structured JSON logging                                                           | Dễ theo dõi, tìm kiếm log và thiết lập cảnh báo                  |
| Error handling    | Validate còn ít, chưa có readiness/liveness chuẩn | Dùng `HTTPException`, có `/health`, `/ready`, startup/shutdown lifecycle          | Giúp hệ thống fail an toàn và dễ vận hành trên cloud             |
| Scalability       | Chạy `localhost`, port cố định, debug reload      | Chạy `0.0.0.0`, lấy `PORT` từ env, graceful shutdown                              | Bắt buộc khi chạy bằng container, load balancer và nhiều replica |

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions

1. Base image: Bản develop dùng `python:3.11`; bản production dùng `python:3.11-slim` trong mô hình multi-stage build.
2. Working directory: `/app`
3. Why copy `requirements.txt` first?: Để tận dụng Docker layer cache tốt hơn, nhờ đó dependencies không phải cài lại mỗi khi source code ứng dụng thay đổi.
4. Why use `.dockerignore`?: Để giảm kích thước build context và tránh đưa các file nhạy cảm hoặc không cần thiết như `.env`, `venv/`, `__pycache__/`, `.git/`, tài liệu và test vào image.

### Exercise 2.3: Image size comparison

- Develop image size: `1.66 GB` disk usage (`424 MB` content size)
- Production image size: `236 MB` disk usage (`56.6 MB` content size)
- Difference: khoảng `85.8%` nhỏ hơn theo disk usage
- Why multi-stage is better: Multi-stage giữ các build tools và dependency tạm thời ở ngoài image runtime cuối cùng, nên image nhỏ hơn, pull nhanh hơn và an toàn hơn.

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment

- Public URL: `https://exemplary-youthfulness-production.up.railway.app/`
- Deployment status: `Success`
- Deployment dashboard: `screenshots/deploy_bai3.png`
- Notes: Mình đã kiểm tra trực tiếp URL Railway. Root endpoint phản hồi bình thường với nội dung:

```json
{ "message": "AI Agent running on Railway!", "docs": "/docs", "health": "/health" }
```

Health check hoạt động tốt:

```json
{ "status": "ok", "uptime_seconds": 19064.0, "platform": "Railway", "timestamp": "2026-04-17T14:14:00.643978+00:00" }
```

Tuy nhiên endpoint `/ready` hiện chưa được triển khai trên bản Railway này và trả về:

```json
{ "detail": "Not Found" }
```

---

## Part 4: API Security

### Exercise 4.1-4.3: Test results

- API key authentication:
  - Không có API key: `401 Unauthorized`
  - Có API key hợp lệ: `200 OK`

```text
Không có API key:
{"detail":"Missing API key. Include header: X-API-Key: <your-key>"}

Có API key hợp lệ:
{"question":"hello","answer":"Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic."}
```

- JWT authentication:
  - Luồng `POST /auth/token` -> `Authorization: Bearer <token>` đã được triển khai trong code.
  - Token hợp lệ mới truy cập được `/ask`.
- Rate limiting:
  - User: `10 req/min`, admin: `100 req/min`
  - Cơ chế: `Sliding Window Counter`
  - Khi vượt ngưỡng sẽ trả về `429 Too Many Requests`

### Exercise 4.4: Cost guard

- Budget config: Repo hiện tại chưa triển khai đúng dạng `$10/month per user`. Cấu hình gần nhất đang có là `$1/day per user + $10/day global` trong `04-api-gateway/production`, và mặc định `DAILY_BUDGET_USD=5.0` trong `06-lab-complete`.
- How usage tracked: Số input/output token được ước lượng trong bộ nhớ và quy đổi sang chi phí USD theo đơn giá cố định trên mỗi 1K token.
- Behavior when budget exceeded: Nếu vượt ngân sách theo user thì trả về `402 Payment Required`; nếu vượt ngân sách toàn cục thì trả về `503 Service temporarily unavailable`.

---

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes

- Health checks:
  - `/health`: `Pass`

```json
{
  "status": "ok",
  "uptime_seconds": 57.9,
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2026-04-17T09:43:29.291436+00:00",
  "checks": { "memory": { "status": "ok", "used_percent": 86.9 } }
}
```

- `/ready`: `Pass`

```json
{ "ready": true, "in_flight_requests": 1 }
```

- Graceful shutdown:
  - Bắt `SIGTERM`/`SIGINT`, ngừng nhận request mới, chờ in-flight requests hoàn thành rồi shutdown.
  - Thời gian chờ tối đa: `30 giây`
- Stateless design:
  - Session data và conversation history được chuyển sang Redis.
  - Cách làm này phù hợp khi scale nhiều replica.
- Load balancing:
  - Nginx đứng trước `3` replica agent và phân phối request qua `agent1`, `agent2`, `agent3`.
  - Redis được dùng làm shared storage.
- Stateless test:

```bash
python 05-scaling-reliability/production/test_stateless.py
```

- `Pass`: 5 request đi qua nhiều instance nhưng vẫn giữ được đầy đủ history nhờ Redis.

---
