import json
import logging
import sys
import io
import pytest

from contextvars import ContextVar

from ..logging_config import JsonFormatter, setup_logging, request_id_ctx


def test_jsonformatter_basic_fields_and_request_id(tmp_path, monkeypatch):
  """
  Given a LogRecord with a simple message, JsonFormatter.format(...) should
  produce a JSON string containing at least the required keys:
    - ts (a timestamp ending with 'Z')
    - level (lowercase)
    - msg
    - logger
    - file (filename)
    - line (lineno)
    - request_id (from the ContextVar)
  """
  token = request_id_ctx.set("test-request-123")

  record = logging.LogRecord(
      name="my.module",
      level=logging.WARNING,
      pathname=__file__,
      lineno=123,
      msg="something happened",
      args=(),
      exc_info=None,
  )

  fmt = JsonFormatter()
  formatted = fmt.format(record)

  payload = json.loads(formatted)

  assert "ts" in payload
  assert payload["ts"].endswith("Z")
  assert payload["level"] == "warning"
  assert payload["msg"] == "something happened"
  assert payload["logger"] == "my.module"
  assert payload["file"].endswith("test_logging_config.py")
  assert payload["line"] == 123
  assert payload["request_id"] == "test-request-123"

  request_id_ctx.reset(token)


def test_jsonformatter_includes_extra_record_attributes():
  """
  If the LogRecord has extra attributes beyond the standard set,
  JsonFormatter.format should include them in the JSON payload.
  """
  token = request_id_ctx.set("another-id")

  record = logging.LogRecord(
      name="extra.test",
      level=logging.INFO,
      pathname=__file__,
      lineno=200,
      msg="testing extra fields",
      args=(),
      exc_info=None,
  )
  record.user_id = 42
  record.session = "abc123"

  fmt = JsonFormatter()
  out = fmt.format(record)
  payload = json.loads(out)

  assert payload["msg"] == "testing extra fields"
  assert payload["user_id"] == 42
  assert payload["session"] == "abc123"

  request_id_ctx.reset(token)


def test_jsonformatter_includes_exception_info():
  """
  If the LogRecord has exc_info set, JsonFormatter.format should add an "exc" key
  containing the formatted exception string.
  """
  token = request_id_ctx.set("exc-id")

  try:
      1 / 0
  except ZeroDivisionError:
      exc_info = sys.exc_info()

  record = logging.LogRecord(
      name="error.test",
      level=logging.ERROR,
      pathname=__file__,
      lineno=300,
      msg="divided by zero",
      args=(),
      exc_info=exc_info,
  )

  fmt = JsonFormatter()
  out = fmt.format(record)
  payload = json.loads(out)

  assert payload["msg"] == "divided by zero"
  assert "exc" in payload
  assert "ZeroDivisionError" in payload["exc"]

  request_id_ctx.reset(token)


def test_setup_logging_replaces_root_handlers_and_sets_formatter(monkeypatch, caplog):
  """
  setup_logging(level=DEBUG) should do the following:
    - Set the root logger's level to DEBUG
    - Replace any existing handlers with exactly one StreamHandler
    - That StreamHandler should be using JsonFormatter()
  """
  root = logging.getLogger()
  root.setLevel(logging.WARNING)
  dummy = logging.StreamHandler(io.StringIO())
  dummy.setFormatter(logging.Formatter("%(message)s"))
  root.handlers = [dummy]

  setup_logging(level=logging.DEBUG)

  assert root.level == logging.DEBUG
  assert len(root.handlers) == 1
  handler = root.handlers[0]
  assert isinstance(handler, logging.StreamHandler)
  assert isinstance(handler.formatter, JsonFormatter)

  cap = io.StringIO()
  handler.stream = cap 

  root.info("hello world", extra={"foo": "bar"})
  output = cap.getvalue().strip()
  payload = json.loads(output)
  assert payload["msg"] == "hello world"
  assert payload["foo"] == "bar"

if __name__ == "__main__":
    pytest.main()
