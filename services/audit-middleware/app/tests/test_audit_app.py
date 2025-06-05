import os
import sys
import pytest
from fastapi.testclient import TestClient

# ——————————————
# 1) Make “app” importable
#
# Folder structure:
#
#   reservation-service/
#     services/
#       audit-middleware/
#         app/
#           __init__.py
#           main.py           ← (FastAPI “app”)
#           db.py
#           consumer.py
#           models.py
#           schemas.py
#           requestMiddleware.py
#           logging_config.py
#           tests/
#             test_audit_app.py  ← (this file)
#
# So we must add “reservation-service/services/audit-middleware” to sys.path.
# ——————————————

this_dir = os.path.dirname(__file__)
parent_folder = os.path.abspath(os.path.join(this_dir, os.pardir, os.pardir))
sys.path.insert(0, parent_folder)

import app.main as main_module
import app.db as db_mod
import app.consumer as consumer_mod


@pytest.fixture(autouse=True)
def patch_init_and_consume(monkeypatch):
    """
    Stub out:
      - db_mod.init_models  (mark a flag)
      - consumer_mod.consume_forever  (mark a flag)
    so that no real database or consumer is started.
    """
    called = {"init_models": False, "consume_forever": False}

    async def fake_init_models():
        called["init_models"] = True

    async def fake_consume_forever():
        called["consume_forever"] = True
        # return immediately

    # Monkey‐patch the real functions
    monkeypatch.setattr(db_mod, "init_models", fake_init_models)
    monkeypatch.setattr(consumer_mod, "consume_forever", fake_consume_forever)

    yield called
    # teardown automatically after each test


@pytest.fixture
def test_client(patch_init_and_consume):
    """
    Create a TestClient for main_module.app in a `with`‐block so that the
    startup “lifespan” actually runs before we return the client.
    """
    with TestClient(main_module.app) as client:
        # Hitting /healthz once to ensure startup already ran
        client.get("/healthz")
        yield client
    # Exiting the `with` block triggers shutdown


def test_startup_triggers_init_and_consumer(patch_init_and_consume):
    """
    Because we have patched init_models() and consume_forever(),
    using `with TestClient(app)` should automatically invoke at least init_models().
    (The consumer is spawned in a background task, so it may not run synchronously here.)
    """
    # Enter a fresh TestClient context to trigger the startup event
    with TestClient(main_module.app):
        pass

    flags = patch_init_and_consume
    assert flags["init_models"] is True, "init_models() was not called on startup"
    # We no longer assert on consume_forever synchronously, because it’s spawned in the background.


def test_healthz_endpoint_returns_ok(test_client):
    """
    GET /healthz → {"status": "ok"} (HTTP 200)
    """
    response = test_client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ——————————————
# DummySession & fake get_db implementations
# ——————————————

class DummySession:
    """
    Simulates an AsyncSession whose .execute(stmt) returns a Result
    whose .scalars().all() yields a predefined list.
    """

    def __init__(self, rows):
        self._rows = rows
        self.closed = False

    class _Result:
        def __init__(self, rows):
            self._rows = rows

        def scalars(self):
            class ScalarList:
                def __init__(self, rows):
                    self._rows = rows

                def all(self):
                    return self._rows

            return ScalarList(self._rows)

    async def execute(self, stmt):
        # Ignore the actual “stmt”; just return our dummy result
        return DummySession._Result(self._rows)

    async def close(self):
        self.closed = True


async def fake_get_db_empty():
    """
    Async‐generator dependency. Yields a DummySession that returns no rows.
    """
    session = DummySession(rows=[])
    try:
        yield session
    finally:
        await session.close()


async def fake_get_db_single_row():
    """
    Async‐generator dependency. Yields a DummySession that returns a single fake row.
    We now include `event_type` and `payload` so that Pydantic’s schemas.ReservationAudit
    validator is satisfied.
    """
    import datetime

    class FakeAudit:
        def __init__(self, id_val, reservation_id_val, created_at_val):
            self.id = id_val
            self.reservation_id = reservation_id_val
            self.created_at = created_at_val
            # Add the two fields that the schema expects:
            self.event_type = "CREATE"
            self.payload = {"example": "data"}

    now = datetime.datetime.utcnow()
    fake_row = FakeAudit(id_val=123, reservation_id_val=456, created_at_val=now)
    session = DummySession(rows=[fake_row])
    try:
        yield session
    finally:
        await session.close()


def test_list_reservations_returns_empty(test_client):
    """
    Override the get_db dependency so it yields a session that returns no rows.
    GET /reservations-audit should return [].
    """
    app = main_module.app
    app.dependency_overrides.clear()
    app.dependency_overrides[db_mod.get_db] = fake_get_db_empty

    response = test_client.get("/reservations-audit")
    assert response.status_code == 200
    assert response.json() == []


def test_list_reservations_returns_data(test_client):
    """
    Override the get_db dependency so it yields a session that returns one fake row.
    GET /reservations-audit should return that record, serialized via schemas.ReservationAudit.
    """
    app = main_module.app
    app.dependency_overrides.clear()
    app.dependency_overrides[db_mod.get_db] = fake_get_db_single_row

    response = test_client.get("/reservations-audit")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list) and len(data) == 1

    item = data[0]
    # We know our FakeAudit sets id=123, reservation_id=456, event_type="CREATE", payload={"example": "data"}
    assert item["id"] == 123
    assert item["reservation_id"] == 456
    assert item["event_type"] == "CREATE"
    assert item["payload"] == {"example": "data"}

    # Verify created_at is a valid ISO‐timestamp
    import datetime
    ts = item["created_at"]
    if ts.endswith("Z"):
        ts = ts[:-1]  # strip trailing Z if necessary
    parsed = datetime.datetime.fromisoformat(ts)
    assert isinstance(parsed, datetime.datetime)


def test_request_middleware_allows_healthz(test_client):
    """
    A simple GET /healthz should still return 200 even with our RequestMiddleware in place.
    If the middleware crashes, we'd get a non‐200.
    """
    response = test_client.get("/healthz")
    assert response.status_code == 200
