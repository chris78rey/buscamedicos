---
name: buscamedicos-testing
description: 'Testing patterns for BuscaMedicos. Pytest with async support, fixtures, and project-specific test conventions.'
license: MIT
---

# BuscaMedicos Testing Skill

## Overview

Pytest-based testing for the BuscaMedicos backend. Uses `pytest-asyncio` for async tests and `httpx` for async HTTP clients.

## When to Use

Use this skill when:
- Writing new tests
- Running existing tests
- Adding fixtures
- Testing API endpoints

## Quick Commands

```bash
# Run all tests
cd backend_api && pytest tests/ -v

# Run specific test file
cd backend_api && pytest tests/test_step2.py -v

# Run with coverage
cd backend_api && pytest tests/ -v --cov=app

# Run only failed
cd backend_api && pytest tests/ --lf
```

## Test Pattern

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_endpoint(client: AsyncClient):
    response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

## Fixtures Location

Place fixtures in `backend_api/tests/conftest.py` or inline in test files.

## Async Test Requirements

```python
# Always use @pytest.mark.asyncio for async tests
@pytest.mark.asyncio
async def test_async_function(client: AsyncClient):
    # ...
```

## Common Fixtures

```python
@pytest.fixture
async def db_session():
    # Async database session for testing
    async with async_session_maker() as session:
        yield session

@pytest.fixture
async def authenticated_client(client: AsyncClient, test_user):
    # Client with auth header set
    client.headers["Authorization"] = f"Bearer {test_user_token}"
    return client
```

## Testing Protected Endpoints

```python
@pytest.mark.asyncio
async def test_protected_endpoint(client: AsyncClient, auth_token):
    response = await client.get(
        "/api/v1/admin/resource",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
```

## Mocking

```python
from unittest.mock import patch

async def test_with_mock(client: AsyncClient):
    with patch("app.services.SomeService.method") as mock:
        mock.return_value = expected_value
        response = await client.get("/endpoint")
        assert response.json()["data"] == expected_value
```

## Test Directory Structure

```
backend_api/tests/
├── conftest.py          # Shared fixtures
├── test_step2.py        # Step2 model tests
├── test_step3.py        # Payment tests
├── test_step6.py        # Moderation tests
├── test_step7.py        # Privacy tests
└── test_api.py           # API endpoint tests
```

## Notes

- No `pytest.ini` exists - defaults apply
- Tests use async sessions with `async_session_maker`
- Auth tests need mocked JWT tokens
- Database tests should use transactions that rollback
