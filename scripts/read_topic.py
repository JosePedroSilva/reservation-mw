import argparse, asyncio, json, os
from aiokafka import AIOKafkaConsumer

DEFAULT_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC             = "reservations"    

async def main(bootstrap_servers: str) -> None:
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=bootstrap_servers,
        group_id="local-viewer",         
        auto_offset_reset="earliest",   
        value_deserializer=lambda b: json.loads(b.decode()),
    )

    await consumer.start()
    print(f"🟢 connected to {bootstrap_servers}, streaming topic '{TOPIC}' …")
    try:
        async for msg in consumer:
            print("↳", json.dumps(msg.value, indent=2))
    finally:
        await consumer.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap", default=DEFAULT_BOOTSTRAP,
                        help=f"host:port (default {DEFAULT_BOOTSTRAP})")
    args = parser.parse_args()
    asyncio.run(main(args.bootstrap))