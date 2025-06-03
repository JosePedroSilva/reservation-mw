import json, datetime, logging, os
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from typing import Any

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC     = "reservations"

log = logging.getLogger(__name__)
producer: AIOKafkaProducer | None = None


async def start_producer() -> None:
  global producer
  if producer is None:
    producer = AIOKafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=_json_dumps,
    )
    await producer.start()
    log.info("Kafka producer started (bootstrap=%s)", BOOTSTRAP)


async def stop_producer() -> None:
  if producer:
    await producer.stop()
    log.info("Kafka producer stopped")


async def publish(event: dict[str, Any]) -> None:
  if producer is None:
    log.warning("producer not initialised; event skipped")
    return
  try:
    await producer.send_and_wait(TOPIC, event)
    log.info("published reservation event id=%s", event["data"]["id"])
  except KafkaError as exc:
    log.exception("failed to publish to Kafka: %s", exc)
  
def _json_dumps(obj):
  """Serialize, turning date/datetime → ISO strings."""
  return json.dumps(
      obj,
      default=lambda o: (
          o.isoformat()
          if isinstance(o, (datetime.date, datetime.datetime))
          else str(o)
      ),
  ).encode("utf-8")
