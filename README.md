# Task Management API

**API RESTful completa para gestión de proyectos estilo Trello/Jira**

---

## Descripción

Sistema backend completo de gestión de tareas y proyectos con arquitectura moderna, diseñado siguiendo principios **SOLID** y **Clean Architecture**. Incluye autenticación JWT, sistema de roles (RBAC), paginación avanzada, rate limiting, y cobertura de tests del 95%+.

## Objetivo del Proyecto

Este proyecto fue desarrollado como una API backend realista para simular
un sistema de gestión de tareas colaborativo similar a Trello/Jira,
enfocado en buenas prácticas de arquitectura, seguridad y testing.

---

## Características

### **Core Features**
- **Autenticación JWT** - Access & refresh tokens con Argon2
- **Sistema de Roles (RBAC)** - OWNER, EDITOR, VIEWER
- **Proyectos Colaborativos** - Gestión de equipos
- **Boards Kanban** - Organización flexible
- **Tasks Completas** - Prioridades, estados, asignaciones
- **Paginación Avanzada** - Sorting, filtering
- **Rate Limiting** - Protección con Redis
- **Test Coverage 95%+** - Unit & integration tests
- **Docker Ready** - Deploy con un comando

---

## Instalación Rápida

### Docker (Recomendado)

```bash
# 1. Clonar y configurar
git clone https://github.com/tomisaurio09/task-management.git
cd task-management
cp .env.example .env

# 2. Iniciar servicios
docker-compose up -d

# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Instalación Local

```bash
python -m venv venv
source venv/bin/activate
pip install -e .
cp .env.example .env
alembic upgrade head
python main.py
```

## Variables de Entorno

| Variable | Descripción |
|--------|-------------|
| DATABASE_URL | PostgreSQL connection string |
| SECRET_KEY | JWT secret |
| ACCESS_TOKEN_EXPIRE_MINUTES | JWT access token TTL |
| REDIS_URL | Redis connection |
| ENV | dev / test / prod |

---

## Auth Flow

1. Usuario se registra o loguea
2. Recibe access token + refresh token
3. Access token se usa en cada request
4. Refresh token genera un nuevo access token
5. Rate limiting protege endpoints sensibles


## Documentación de la API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints Principales

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

**Coverage**: 95%+ | **Performance**: ~150-200 RPS

---

## Arquitectura

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

**Principios**: Clean Architecture, SOLID, Dependency Injection

---

## Seguridad

- Argon2 password hashing
- JWT access + refresh tokens
- Redis rate limiting
- Role-based access control
- SQL injection protection (ORM)

---

## Stack

| Tech | Version |
|------|---------|
| Python | 3.12 |
| FastAPI | 0.128+ |
| PostgreSQL | 15 |
| SQLAlchemy | 2.0+ |
| Redis | 7.1 |
| Docker 

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
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

---

## 👤 Autor

**Thomas Acevedo**
- GitHub: [@tomisaurio09](https://github.com/Tomisaurio09)
- LinkedIn: [Thomas Acevedo](https://www.linkedin.com/in/thomas-acevedo/)

---
