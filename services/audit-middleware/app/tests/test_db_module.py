import os
import sys
import asyncio
import pytest
from sqlalchemy.exc import SQLAlchemyError

this_dir = os.path.dirname(__file__)
parent_folder = os.path.abspath(os.path.join(this_dir, os.pardir, os.pardir))
sys.path.insert(0, parent_folder)

import app.db as db
import app.models as models
from app.db import get_session, init_models, get_db


class FakeSession:
    """
    Fake AsyncSession that tracks whether rollback() and close() are called.
    """
    def __init__(self):
        self.rolled_back = False
        self.closed = False

    async def rollback(self):
        self.rolled_back = True

    async def close(self):
        self.closed = True


class DummyContext:
    """
    An async‐context‐manager that yields the given fake session every time,
    and ensures that close() is called in __aexit__.
    """
    def __init__(self, fake_sess: FakeSession):
        self._fake = fake_sess

    async def __aenter__(self):
        return self._fake

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._fake.close()
        return False


@pytest.mark.asyncio
async def test_get_session_yields_and_closes():
    """
    Monkey-patch db.async_session so that get_session() yields our FakeSession.
    Then verify it gets closed when the async generator is exhausted normally.
    """
    fake = FakeSession()
    db.async_session = lambda: DummyContext(fake)

    agen = get_session()
    session = await agen.__anext__() 
    assert isinstance(session, FakeSession)

    await agen.aclose()

    assert fake.closed is True
    assert fake.rolled_back is False


@pytest.mark.asyncio
async def test_get_session_rolls_back_and_closes_on_error():
    """
    Monkey-patch db.async_session so get_session() yields FakeSession.
    Then inject a SQLAlchemyError into the generator—get_session should catch it,
    call rollback(), then re-raise, and still close() in finally.
    """
    fake = FakeSession()
    db.async_session = lambda: DummyContext(fake)

    agen = get_session()
    session = await agen.__anext__() 
    assert isinstance(session, FakeSession)

    with pytest.raises(SQLAlchemyError):
        await agen.athrow(SQLAlchemyError("trigger rollback"))

    assert fake.rolled_back is True
    assert fake.closed is True


@pytest.mark.asyncio
async def test_init_models_does_not_raise_when_tables_creation_is_stubbed(monkeypatch):
    """
    Replace db.engine with a dummy whose .begin() returns a DummyConnection.
    Replace models.Base.metadata.create_all so that it does nothing.
    Then call init_models()—it should complete without errors.
    """
    original_create_all = models.Base.metadata.create_all
    monkeypatch.setattr(
        models.Base.metadata,
        "create_all",
        lambda bind=None: None
    )

    class DummyConnection:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return False

        async def run_sync(self, fn):
            fn() 

    class DummyEngine:
        def begin(self):
            return DummyConnection()

    db.engine = DummyEngine()

    await init_models()

    monkeypatch.setattr(
        models.Base.metadata,
        "create_all",
        original_create_all
    )


@pytest.mark.asyncio
async def test_get_db_yields_and_closes():
    """
    Similar to test_get_session, but for get_db(). Verify that get_db yields the session
    and then closes it on normal exit.
    """
    fake = FakeSession()
    db.async_session = lambda: DummyContext(fake)

    agen = get_db()
    session = await agen.__anext__()
    assert isinstance(session, FakeSession)

    await agen.aclose()
    assert fake.closed is True
