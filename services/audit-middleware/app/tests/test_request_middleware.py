import uuid
import time
import logging
import warnings

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from pytest import PytestUnraisableExceptionWarning

warnings.filterwarnings("ignore", category=PytestUnraisableExceptionWarning)

from app.requestMiddleware import RequestIDMiddleware
from app.logging_config import request_id_ctx


@pytest.fixture
def app_with_middleware():
    """
    Build a minimal FastAPI app that uses RequestIDMiddleware.
    """
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/show-id")
    async def show_id(request: Request):
        return {"rid": request_id_ctx.get(None)}

    @app.get("/error-endpoint")
    async def error_endpoint():
        raise RuntimeError("boom!")

    @app.get("/fixed-delay")
    async def fixed_delay():
        time.sleep(0.005)
        return {"status": "slept"}

    return app


def test_each_request_gets_its_own_uuid_and_header(app_with_middleware, caplog):
    caplog.set_level(logging.INFO)
    client = TestClient(app_with_middleware)

    caplog.clear()
    resp1 = client.get("/show-id")
    assert resp1.status_code == 200

    returned1 = resp1.json()["rid"]
    header1 = resp1.headers.get("X-Request-ID")
    assert header1 is not None, "X-Request-ID header was not set"

    uuid.UUID(returned1)
    assert returned1 == header1

    records = [r for r in caplog.records if r.levelno == logging.INFO]
    assert sum(1 for r in records if "request complete" in r.getMessage()) == 1
    rec = next(r for r in records if "request complete" in r.getMessage())
    assert hasattr(rec, "duration_ms"), "duration_ms not found on LogRecord"

    caplog.clear()
    resp2 = client.get("/show-id")
    assert resp2.status_code == 200

    returned2 = resp2.json()["rid"]
    header2 = resp2.headers.get("X-Request-ID")
    assert returned2 == header2
    assert returned1 != returned2

    records2 = [r for r in caplog.records if r.levelno == logging.INFO]
    assert sum(1 for r in records2 if "request complete" in r.getMessage()) == 1


def test_contextvar_is_set_during_handler_and_reset_after(app_with_middleware):
    client = TestClient(app_with_middleware)

    assert request_id_ctx.get(None) is None

    resp = client.get("/show-id")
    assert resp.status_code == 200

    rid = resp.json()["rid"]
    header = resp.headers["X-Request-ID"]
    assert rid == header

    assert request_id_ctx.get(None) is None


def test_request_with_internal_error_logs_exception_and_propagates(app_with_middleware, caplog):
    caplog.set_level(logging.INFO)

    client_raise = TestClient(app_with_middleware)

    caplog.clear()
    with pytest.raises(RuntimeError):
        client_raise.get("/error-endpoint")

    errs = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert any("unhandled error" in r.getMessage() for r in errs)

    infos = [r for r in caplog.records if r.levelno == logging.INFO]
    assert any("request complete" in r.getMessage() for r in infos)

    client_no_raise = TestClient(app_with_middleware, raise_server_exceptions=False)

    caplog.clear()
    response = client_no_raise.get("/error-endpoint")
    assert response.status_code == 500

    assert "X-Request-ID" not in response.headers

    infos2 = [r for r in caplog.records if r.levelno == logging.INFO]
    assert any("request complete" in r.getMessage() for r in infos2)
    rec = next(r for r in infos2 if "request complete" in r.getMessage())
    assert hasattr(rec, "duration_ms")


def test_duration_ms_is_nonzero_for_real_delay(app_with_middleware, caplog):
    caplog.set_level(logging.INFO)
    client = TestClient(app_with_middleware)

    caplog.clear()
    resp = client.get("/fixed-delay")
    assert resp.status_code == 200
    assert resp.json() == {"status": "slept"}

    infos = [r for r in caplog.records if r.levelno == logging.INFO]
    rec = next(r for r in infos if "request complete" in r.getMessage())
    dur = getattr(rec, "duration_ms", None)
    assert isinstance(dur, (float, int))
    assert dur > 0.0
