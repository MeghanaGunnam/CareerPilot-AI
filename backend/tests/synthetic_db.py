"""Shared opt-in test fixture: no production-row reads or durable fixture writes."""
from contextlib import contextmanager
import uuid


@contextmanager
def synthetic_database(exclude=()):
    from sqlalchemy import text
    from sqlalchemy.orm import Session
    from backend.app.main import app
    from backend.app.auth.dependencies import get_current_user
    from backend.app.auth.models import User
    from backend.app.auth.security import create_access_token
    from backend.app.core.database import Base, engine, get_db
    from backend.tests.test_jobs import request

    assert engine.dialect.name == "postgresql"
    schema = "v1_test_" + uuid.uuid4().hex
    overrides = app.dependency_overrides.copy()
    with engine.connect() as connection:
        outer = connection.begin()
        try:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            Base.metadata.create_all(connection, tables=[table for table in Base.metadata.sorted_tables if table.name not in exclude])
            with Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False) as db:
                users = [User(email=f"synthetic-{i}@example.invalid", password_hash="synthetic-only") for i in range(3)]
                db.add_all(users)
                db.commit()
                app.dependency_overrides[get_db] = lambda: db
                app.dependency_overrides.pop(get_current_user, None)
                tokens = [create_access_token(user.id)[0] for user in users]
                def call(user=0, **kwargs):
                    headers = [] if user is None else [(b"authorization", f"Bearer {tokens[user]}".encode())]
                    return request(headers=headers, **kwargs)
                yield db, users, call, connection
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(overrides)
            outer.rollback()
        assert connection.scalar(text("SELECT to_regnamespace(:schema)"), {"schema": schema}) is None
    engine.dispose()
