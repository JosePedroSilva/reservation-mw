import json, datetime, logging
from contextvars import ContextVar
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")

class JsonFormatter(logging.Formatter):
  def format(self, record: logging.LogRecord) -> str:
    payload = {
      "ts": datetime.datetime.utcnow()
                        .isoformat(timespec="milliseconds") + "Z",
      "level": record.levelname.lower(),
      "msg":   record.getMessage(),
      "logger": record.name,
      "file":  record.filename,
      "line":  record.lineno,
    }

    payload["request_id"] = request_id_ctx.get()

    standard = set(payload) | {
      "name","msg","args","levelname","levelno","pathname","filename",
      "module","exc_info","exc_text","stack_info","lineno","funcName",
      "created","msecs","relativeCreated","thread","threadName",
      "processName","process",
    }
    for k, v in record.__dict__.items():
      if k not in standard:
          payload[k] = v

    if record.exc_info:
      payload["exc"] = self.formatException(record.exc_info)

    return json.dumps(payload, default=str)

def setup_logging(level: int = logging.INFO) -> None:
  root = logging.getLogger()
  handler = logging.StreamHandler()
  handler.setFormatter(JsonFormatter())
  root.handlers[:] = [handler]
  root.setLevel(level)
