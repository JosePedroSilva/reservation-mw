import os, json
import asyncio
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC = os.getenv("RESERVATIONS_TOPIC", "reservations")
GROUP_ID = os.getenv("KAFKA_CONSUMER_GROUP", "audit-middleware")

async def consume_reservations() -> None:
  consumer = AIOKafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    group_id=GROUP_ID,
    enable_auto_commit=False,
    value_deserializer=lambda raw: json.loads(raw.decode("utf-8"))
  )

  await consumer.start()
  print(f"[consumer] started, listening on topic '{TOPIC}' @ {BOOTSTRAP_SERVERS}")

  try:
    async for msg in consumer:
      print(f"[consumer] Received: partition={msg.partition} offset={msg.offset} -> {msg.value}")

    #Ack immediately for now
    await consumer.commit()
  
  except KafkaError as e:
    print(f"[consumer] Kafka error: {e}")
  finally:
    await consumer.stop()
    print("[consumer] Stopped consuming")