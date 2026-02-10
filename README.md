# Task Management API

**Complete RESTful API for project management (Trello/Jira style)**

---

## Description

A full backend system for task and project management with a modern architecture, designed following **SOLID** principles and **Clean Architecture**. Includes JWT authentication, role-based access control (RBAC), advanced pagination, rate limiting, and 95%+ test coverage.

## Project Goal

This project was developed as a realistic backend API to simulate a collaborative task management system similar to Trello/Jira, focused on best practices in architecture, security, and testing.

---

## Features

### **Core Features**
- **JWT Authentication** – Access & refresh tokens with Argon2
- **Role-Based Access Control (RBAC)** – OWNER, EDITOR, VIEWER
- **Collaborative Projects** – Team management
- **Kanban Boards** – Flexible organization
- **Complete Tasks** – Priorities, states, assignments
- **Advanced Pagination** – Sorting, filtering
- **Rate Limiting** – Redis-based protection
- **95%+ Test Coverage** – Unit & integration tests
- **Docker Ready** – One-command deployment

---

## Quick Installation

### Prerequisites
- Docker & Docker Compose
- Git

### Docker (Recommended)

```bash
# 1. Clone and configure
git clone https://github.com/tomisaurio09/task-management.git
cd task-management
cp .env.example .env

# 2. Start services
docker-compose up -d

# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Local Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -e .
cp .env.example .env
alembic upgrade head
python main.py
```

---

### First API Call
```bash
# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123",
    "full_name": "John Doe"
  }'

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| DATABASE_URL | PostgreSQL connection string |
| SECRET_KEY | JWT secret |
| ACCESS_TOKEN_EXPIRE_MINUTES | JWT access token TTL |
| REDIS_URL | Redis connection |

---

## Auth Flow

1. User registers or logs in  
2. Receives access token + refresh token  
3. Access token is used in each request  
4. Refresh token generates a new access token  
5. Rate limiting protects sensitive endpoints  

---

## Documentation

Comprehensive documentation is available in the [`app/docs/`](app/docs/) directory:

- **[API Endpoints](app/docs/endpoints.md)** - Complete endpoint documentation with examples
- **[Architecture Guide](app/docs/architecture.md)** - System design, database schema, design decisions
- **[Testing Guide](app/docs/testing.md)** - Unit tests, integration tests, load testing
- **[RBAC Guide](app/docs/rbac.md)** - Complete information about roles and permissions

### Interactive API Documentation

When the server is running:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Main Endpoints

```http
# Auth
POST   /auth/register
POST   /auth/login
POST   /auth/refresh

# Projects
GET    /projects
POST   /projects
GET    /projects/{project_id}
PATCH  /projects/{project_id}
DELETE /projects/{project_id}

# Memberships
GET    /projects/{project_id}/members
POST   /projects/{project_id}/members/add/{user_id}
PATCH  /projects/{project_id}/members/change-role/{user_id}
DELETE /projects/{project_id}/members/remove/{user_id}

# Boards
GET    /projects/{project_id}/boards
POST   /projects/{project_id}/boards
GET    /projects/{project_id}/boards/{board_id}
PATCH  /projects/{project_id}/boards/{board_id}
DELETE /projects/{project_id}/boards/{board_id}

# Tasks
GET    /projects/{project_id}/boards/{board_id}/tasks
POST   /projects/{project_id}/boards/{board_id}/tasks
GET    /projects/{project_id}/boards/{board_id}/tasks/{task_id}
PATCH  /projects/{project_id}/boards/{board_id}/tasks/{task_id}
DELETE /projects/{project_id}/boards/{board_id}/tasks/{task_id}
```

---

## Testing

```bash
# Unit & Integration tests
pytest --cov=app

# Load testing
locust -f load_tests.py --host=http://localhost:8000
```

**Coverage**: 95%+ | **Performance**: ~150–200 RPS  

---

## Architecture

```
app/
├── api/          # Routers (endpoints)
├── core/         # Config, dependencies, exceptions
├── db/           # Sessions, Base
├── models/       # SQLAlchemy models
├── schemas/      # Pydantic schemas
├── services/     # Business logic
└── tests/        # Test suite
```

**Principles**: Clean Architecture, SOLID, Dependency Injection  

---

## Security

- Argon2 password hashing  
- JWT access + refresh tokens  
- Redis rate limiting  
- Role-based access control  
- SQL injection protection (ORM)  

---

## Tech Stack

| Tech | Version |
|------|---------|
| Python | 3.12 |
| FastAPI | 0.128+ |
| PostgreSQL | 15 |
| SQLAlchemy | 2.0+ |
| Redis | 7.1 |
| Docker | latest |

---

## Database Schema

```sql
users → projects → boards → tasks
      → memberships (OWNER/EDITOR/VIEWER)
```

---

## Deployment

```bash
# Development
docker compose up -d

# Production
docker compose -f docker-compose.prod.yml up -d
```

---

## 👤 Author

**Thomas Acevedo**  
- GitHub: [@tomisaurio09](https://github.com/Tomisaurio09)  
- LinkedIn: [Thomas Acevedo](https://www.linkedin.com/in/thomas-acevedo/)  