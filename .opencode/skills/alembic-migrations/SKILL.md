---
name: alembic-migrations
description: 'Alembic migration workflow for BuscaMedicos. Create, autogenerate, and run migrations following the step2-step8 architecture.'
license: MIT
---

# Alembic Migrations Skill

## Overview

Alembic migration workflow for the BuscaMedicos project. Uses step-based incremental architecture - each step adds new models/tables.

## When to Use

Use this skill when:
- Adding new models to the database
- Modifying existing table schemas
- Checking migration status
- Resetting the database

## Step Architecture

```
Migrations run in order: step2 → step3 → ... → step8
Each migration file is named: NNN_stepN.py
Migration 007 (007_step8.py) adds audit_events columns
```

## Quick Commands

```bash
# Run all migrations
cd backend_api && alembic upgrade head

# Create new migration
cd backend_api && alembic revision --autogenerate -m "description"

# Check current migration
cd backend_api && alembic current

# Show migration history
cd backend_api && alembic history --verbose

# Downgrade one step
cd backend_api && alembic downgrade -1
```

## Creating New Migrations

```bash
# After modifying models in step7_models.py
alembic revision --autogenerate -m "add new privacy table"
```

## Common Patterns

### Adding columns to existing table
```python
op.add_column('table_name', sa.Column('new_col', sa.String(), nullable=True))
```

### Creating new table
```python
op.create_table('new_table',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
)
```

## Gotchas

- Always run `alembic upgrade head` after model changes
- Migration 007 adds `operational_scope` and `release_code` to `audit_events`
- Do NOT modify existing migration files - create new ones
- `env.py` imports all models for autogenerate to work
- `alembic.ini` must have `sqlalchemy.url` in `[alembic]` section
