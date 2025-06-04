import uuid, time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from .logging_config import request_id_ctx

log = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
  async def dispatch(self, request: Request, call_next):
    rid = str(uuid.uuid4())
    token = request_id_ctx.set(rid) 
    start = time.perf_counter()
    try:
      response = await call_next(request)
    except Exception:
      log.exception("unhandled error")
      raise
    finally:
      duration = time.perf_counter() - start
      log.info("request complete", extra={"duration_ms": round(duration*1000, 1)})
      request_id_ctx.reset(token)

    response.headers["X-Request-ID"] = rid
    return response
