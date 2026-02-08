# Testing Strategy

## Overview

**Current Coverage**: 95%+

**Testing Pyramid**:
```
Integration Tests (API endpoints)
Unit Tests (Services, utilities)
```

---

## Test Structure

```
app/tests/
├── conftest.py              # Fixtures & test config
├── test_auth.py             # Authentication tests
├── test_projects.py         # Projects CRUD + business rules
├── test_memberships.py      # RBAC & membership management
├── test_boards.py           # Boards + edge cases
└── test_tasks.py            # Tasks + validations
└── load/
    └── load_tests.py        # Load testing scenarios
```

---

## Types of Tests

### 1. Integration Tests

**What**: Test API endpoints with real database

**Example**:
```python
def test_create_project(client, auth_headers):
    """Test project creation endpoint"""
    response = client.post(
        "/projects",
        json={"name": "Test Project"},
        headers=auth_headers
    )
    
    assert response.status_code == 201
    assert response.json()["name"] == "Test Project"
```

**Characteristics**:
- Slower (~10-50ms per test)
- Uses test database (SQLite in-memory)
- Real HTTP requests (via TestClient)
- Tests entire flow (API → Service → DB)

### 2. Load Tests (Locust)

**What**: Test performance under concurrent load

**Example**:
```python
class AuthenticatedUser(HttpUser):
    @task(5)
    def list_projects(self):
        self.client.get("/projects", headers=self.headers)
    
    @task(3)
    def create_project(self):
        self.client.post("/projects", json={...})
```

**Metrics**:
- RPS (Requests Per Second)
- Response time (P50, P95, P99)
- Error rate

---

## Fixtures (conftest.py)

### Database Fixture

```python
@pytest.fixture(scope="function")
def db_session():
    """Fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
```

**Why `scope="function"`**: Each test gets clean DB

### Test Client

```python
@pytest.fixture(scope="function")
def client(db_session):
    """TestClient with DB override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

### Test User

```python
@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password=hash_password("TestPass123"),
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    return user
```

### Auth Headers

```python
@pytest.fixture
def auth_headers(client, test_user):
    """Get JWT token for test user"""
    response = client.post("/auth/login", data={
        "username": test_user.email,
        "password": "TestPass123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

**Reusability**: Other fixtures can depend on this

---

## Test Categories

### Authentication Tests (`test_auth.py`)

**Covers**:
- ✅ Register: success, duplicate email, weak password
- ✅ Login: success, wrong password, inactive user
- ✅ Refresh: valid token, invalid token

**Example**:
```python
def test_register_duplicate_email(client, test_user):
    """Test that duplicate email fails"""
    response = client.post("/auth/register", json={
        "email": test_user.email,  # Already exists
        "password": "NewPass123",
        "full_name": "New User"
    })
    
    assert response.status_code == 409  # Conflict
    assert "already exists" in response.json()["detail"].lower()
```

### Projects Tests (`test_projects.py`)

**Covers**:
- ✅ CRUD operations
- ✅ Pagination (page, page_size, sorting)
- ✅ Filtering (by name)
- ✅ Max 20 projects limit
- ✅ Unauthorized access

**Example**:
```python
def test_max_projects_limit(client, auth_headers):
    """Test 20 project limit"""
    # Create 20 projects
    for i in range(20):
        client.post("/projects", json={"name": f"P{i}"}, headers=auth_headers)
    
    # 21st should fail
    response = client.post(
        "/projects",
        json={"name": "P21"},
        headers=auth_headers
    )
    
    assert response.status_code == 422
    assert "maximum" in response.json()["detail"].lower()
```

### Memberships Tests (`test_memberships.py`)

**Covers**:
- ✅ Add member (different roles)
- ✅ Remove member (last OWNER protection)
- ✅ Change role (validation)
- ✅ Permission checks (VIEWER can't add members)

**Example**:
```python
def test_remove_last_owner_fails(client, auth_headers, test_project, test_user):
    """Cannot remove last OWNER"""
    response = client.delete(
        f"/projects/{test_project['id']}/members/remove/{test_user.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "last owner" in response.json()["detail"].lower()
```

### Boards Tests (`test_boards.py`)

**Covers**:
- ✅ CRUD operations
- ✅ Position auto-increment
- ✅ Archiving
- ✅ Cascade delete (boards → tasks)
- ✅ VIEWER permissions (can read, can't create)

### Tasks Tests (`test_tasks.py`)

**Covers**:
- ✅ CRUD operations
- ✅ Assignee validation (must be project member)
- ✅ Past due date validation
- ✅ Filtering (status, priority, assignee)
- ✅ Sorting
- ✅ Moving tasks between boards

---

## Coverage Report

```bash
# Run tests with coverage
pytest --cov=app --cov-report=html

# View report
open htmlcov/index.html
```

**Current Coverage**:
```
app/
├── api/          100%   # All endpoints tested
├── core/         95%    # Security, dependencies
├── models/       100%   # Models are simple
├── schemas/      100%   # Pydantic validates itself
└── services/     95%    # Most business logic covered
```
---

## Running Tests

### All Tests

```bash
pytest
```

### Specific File

```bash
pytest app/tests/test_auth.py
```

### Specific Test

```bash
pytest app/tests/test_auth.py::test_register_success
```

### With Coverage

```bash
pytest --cov=app --cov-report=term-missing
```

### Verbose

```bash
pytest -v  # Show each test name
pytest -vv # Very verbose
```

### Stop on First Failure

```bash
pytest -x
```

### Run Only Failed Tests

```bash
pytest --lf  # Last failed
```

---

## Load Testing (Locust)

### Basic Run

```bash
locust -f app/tests/load/load_tests.py --host=http://localhost:8000
```

**Open**: http://localhost:8089

### Headless (CI/CD)

```bash
locust -f app/tests/load/load_tests.py \
  --host=http://localhost:8000 \
  --users 50 \
  --spawn-rate 10 \
  --run-time 2m \
  --headless \
  --html=report.html
```

---

## Future Testing Improvements

1. **Mutation Testing**: Verify tests catch bugs (e.g., `mutmut`)
2. **Property-Based Testing**: Generate random inputs (`hypothesis`)
3. **Contract Testing**: API contract tests (`pact`)
4. **E2E Tests**: Full user flows (`Playwright`, `Cypress`)
5. **Performance Regression**: Track performance over time
6. **Security Testing**: SQL injection, XSS (`bandit`, `safety`)
