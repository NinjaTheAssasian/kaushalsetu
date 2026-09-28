"""
Test fixtures for database isolation.

Every test runs inside a nested database transaction that is rolled back
after the test finishes. This means:
- Tests never pollute the development database.
- Tests are fully repeatable regardless of seed data or prior runs.
- The production `get_db` dependency is unchanged.
"""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import engine as prod_engine
from app.api.deps import get_db
from app.main import app


@pytest.fixture(scope="function")
def db_session():
    """
    Yield a DB session wrapped in a savepoint.
    After the test, we roll back the outer transaction so nothing persists.
    """
    # Connect directly to the existing engine
    connection = prod_engine.connect()
    # Begin an outer (non-committable) transaction
    transaction = connection.begin()
    # Bind a session to this connection
    TestingSessionLocal = sessionmaker(bind=connection)
    session = TestingSessionLocal()

    # When the application code calls session.commit(), we want to flush
    # but NOT actually commit. We use nested (savepoint) transactions for this.
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        nonlocal nested
        if trans.nested and not trans._parent.nested:
            nested = connection.begin_nested()

    yield session

    # Teardown: rollback everything
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """
    Provide a TestClient whose `get_db` dependency returns the
    isolated, rollback-able session created above.
    """
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass  # session lifecycle managed by db_session fixture

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
