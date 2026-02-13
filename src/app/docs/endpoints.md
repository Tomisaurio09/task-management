# API Endpoints

## Base URL

```
Development: http://localhost:8000
```

## Authentication

All the endpoints (except `/auth/*` and `/health`) require autentication:

```http
Authorization: Bearer <access_token>
```

---

## Authentication

### Register

```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe"
}
```

**Response** `201 Created`:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true
}
```

**Validations**:
- Email: Valid format, unique
- Password: Min 8 chars, must contain letters + numbers
- Full name: Max 64 chars, letters only

### Login

```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=SecurePass123
```

**Response** `200 OK`:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Refresh Token

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ..."
}
```

**Response** `200 OK`:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

---

## Projects

### List Projects

```http
GET /projects?page=1&page_size=20&sort_by=name&sort_order=asc&name=search
Authorization: Bearer <token>
```

**Query Parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number (min: 1) |
| `page_size` | int | 20 | Items per page (max: 100) |
| `sort_by` | string | - | `name`, `created_at` |
| `sort_order` | string | asc | `asc`, `desc` |
| `name` | string | - | Filter by name (case-insensitive) |

**Response** `200 OK`:
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "My Project",
      "owner_id": "uuid",
      "created_at": "2024-01-15T10:30:00Z",
      "memberships": [
        {
          "id": 1,
          "user_id": "uuid",
          "project_id": "uuid",
          "role": "OWNER",
          "joined_at": "2024-01-15T10:30:00Z",
          "invited_by": null
        }
      ]
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "has_next": false,
  "has_previous": false
}
```

### Create Project

```http
POST /projects
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "New Project"
}
```

**Response** `201 Created`:
```json
{
  "id": "uuid",
  "name": "New Project",
  "owner_id": "uuid",
  "created_at": "2024-01-15T10:30:00Z",
  "memberships": [...]
}
```

**Business Rules**:
- Max 20 projects per user
- Creator becomes OWNER automatically

### Get Project

```http
GET /projects/{project_id}
Authorization: Bearer <token>
```

**Response** `200 OK`: (same as create)

### Update Project

```http
PATCH /projects/{project_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Updated Name"
}
```

**Permissions**: OWNER or EDITOR

### Delete Project

```http
DELETE /projects/{project_id}
Authorization: Bearer <token>
```

**Response** `204 No Content`

**Permissions**: OWNER only

---

## Memberships

### List Members

```http
GET /projects/{project_id}/members
Authorization: Bearer <token>
```

**Response** `200 OK`:
```json
[
  {
    "user_id": "uuid",
    "role": "OWNER",
    "invited_by": null
  }
]
```

### Add Member

```http
POST /projects/{project_id}/members/add/{user_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "role": "EDITOR"
}
```

**Response** `201 Created`

**Permissions**: OWNER only

**Roles**: `OWNER`, `EDITOR`, `VIEWER`

### Remove Member

```http
DELETE /projects/{project_id}/members/remove/{user_id}
Authorization: Bearer <token>
```

**Response** `204 No Content`

**Permissions**: OWNER only

**Business Rule**: Cannot remove last OWNER

### Change Role

```http
PATCH /projects/{project_id}/members/change-role/{user_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "role": "VIEWER"
}
```

**Response** `200 OK`

**Permissions**: OWNER only

---

## Boards

### List Boards

```http
GET /projects/{project_id}/boards?page=1&page_size=20&sort_by=position&archived=false&name=search
Authorization: Bearer <token>
```

**Query Parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page |
| `sort_by` | string | position | `name`, `position`, `created_at`, `updated_at` |
| `sort_order` | string | asc | `asc`, `desc` |
| `archived` | bool | false | Include archived boards |
| `name` | string | - | Filter by name |

**Response** `200 OK`:
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "To Do",
      "project_id": "uuid",
      "position": 0,
      "archived": false,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 3,
  ...
}
```

### Create Board

```http
POST /projects/{project_id}/boards
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "In Progress"
}
```

**Response** `201 Created`

**Permissions**: OWNER or EDITOR

**Auto-increment**: Position is set automatically

### Update Board

```http
PATCH /projects/{project_id}/boards/{board_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Done",
  "position": 2,
  "archived": false
}
```

**Response** `200 OK`

### Delete Board

```http
DELETE /projects/{project_id}/boards/{board_id}
Authorization: Bearer <token>
```

**Response** `204 No Content`

**Cascade**: Deletes all tasks in the board

---

## Tasks

### List Tasks

```http
GET /projects/{project_id}/boards/{board_id}/tasks?page=1&page_size=20&sort_by=position&status=active&priority=high&assignee_id=uuid&archived=false
Authorization: Bearer <token>
```

**Query Parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page |
| `sort_by` | string | position | `name`, `position`, `created_at`, `updated_at`, `due_date`, `status`, `priority` |
| `sort_order` | string | asc | `asc`, `desc` |
| `archived` | bool | false | Include archived tasks |
| `status` | string | - | `active`, `completed`, `archived` |
| `priority` | string | - | `low`, `medium`, `high` |
| `assignee_id` | uuid | - | Filter by assignee |

**Response** `200 OK`:
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Fix bug",
      "description": "Fix login issue",
      "board_id": "uuid",
      "assignee_id": "uuid",
      "status": "active",
      "priority": "high",
      "position": 0,
      "due_date": "2024-01-20T00:00:00Z",
      "archived": false,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  ...
}
```

### Create Task

```http
POST /projects/{project_id}/boards/{board_id}/tasks
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Implement feature",
  "description": "Add dark mode",
  "priority": "medium",
  "status": "active",
  "assignee_id": "uuid",
  "due_date": "2024-02-01T00:00:00Z"
}
```

**Response** `201 Created`

**Permissions**: OWNER or EDITOR

**Validations**:
- Name: Required, max 256 chars
- Description: Optional, max 512 chars
- Due date: Cannot be in the past
- Assignee: Must be project member

### Update Task

```http
PATCH /projects/{project_id}/boards/{board_id}/tasks/{task_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Updated name",
  "status": "completed",
  "priority": "low",
  "assignee_id": null,
  "board_id": "other_board_uuid"
}
```

**Response** `200 OK`

**Special**: Can move task to another board by changing `board_id`

### Delete Task

```http
DELETE /projects/{project_id}/boards/{board_id}/tasks/{task_id}
Authorization: Bearer <token>
```

**Response** `204 No Content`

---

## Health Check

```http
GET /health
```

**Response** `200 OK`:
```json
{
  "status": "healthy"
}
```

**No authentication required**

---

## HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Successful GET/PATCH |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

---

## Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| `POST /auth/register` | 5 | 1 minute |
| `POST /auth/login` | 10 | 1 minute |
| `POST /projects` | 10 | 1 minute |
| `GET /projects` | 60 | 1 minute |
| `POST /boards` | 20 | 1 minute |
| `GET /boards` | 100 | 1 minute |
| `POST /tasks` | 50 | 1 minute |
| `GET /tasks` | 120 | 1 minute |

**Response** when exceeded:
```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "detail": "Too many requests. Please try again later."
}
```

---

## Pagination Response Format

All paginated endpoints return:

```json
{
  "items": [...],
  "total": 50,
  "page": 2,
  "page_size": 20,
  "total_pages": 3,
  "has_next": true,
  "has_previous": true
}
```
---
## Swagger/OpenAPI

Interactive API docs available at:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`

**Features**:
- Try endpoints directly
- See request/response schemas
- Auto-generated from code