import os, json
import asyncio

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from sqlalchemy.exc import SQLAlchemyError

from .db import get_session
from .models import ReservationAudit, EventType

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC = os.getenv("RESERVATIONS_TOPIC", "reservations")
GROUP_ID = os.getenv("KAFKA_CONSUMER_GROUP", "audit-middleware")

def _json_loads(raw: bytes) -> dict:
  return json.loads(raw.decode("utf-8"))

async def _handle_event(event: dict) -> None:
  reservation_id = event.get("id")
  raw_type = event.get("event_type")
  payload = event.get("data")

  if reservation_id is None or raw_type is None or payload is None:
    print("event_missing_fields")
    return
  
  try:
    evt_type = EventType(raw_type)
  except ValueError:
    print("invalid_event_type")
    return
  
  async for session in get_session():
    try:
      audit_row = ReservationAudit(
        reservation_id=reservation_id,
        event_type=evt_type,
        payload=payload,
      )
      session.add(audit_row)
      await session.commit()
      print("audit_saved")
    except SQLAlchemyError as exc:
      await session.rollback()
      print("db_error", exc)

async def consume_forever() -> None:
  consumer = AIOKafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    group_id=GROUP_ID,
    enable_auto_commit=False,
    value_deserializer=_json_loads,
  )

  await consumer.start()
  print("kafka_consumer_started")

  try:
    async for msg in consumer:
      event = msg.value
      try:
        await _handle_event(event)
        await consumer.commit()
      except Exception as exc:
        print("event_handling_failure")
  except KafkaError as exc:
    print("kafka_consumer_error")
  finally:
    await consumer.stop()
    print("kafka_consumer_stopped")