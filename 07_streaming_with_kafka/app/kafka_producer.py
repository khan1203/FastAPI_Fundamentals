import os
import json
from aiokafka import AIOKafkaProducer
from dotenv import load_dotenv

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "activity_logs")

kafka_producer: AIOKafkaProducer = None


async def start_kafka_producer():
    """Initialize and start Kafka producer"""
    global kafka_producer

    kafka_producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    await kafka_producer.start()
    print(f"Kafka producer started: {KAFKA_BOOTSTRAP_SERVERS}")


async def stop_kafka_producer():
    """Stop Kafka producer gracefully"""
    global kafka_producer
    if kafka_producer:
        await kafka_producer.stop()
        print("Kafka producer stopped")


async def publish_log(log_data: dict):
    """Publish log event to Kafka topic"""
    if not kafka_producer:
        raise RuntimeError("Kafka producer not initialized")

    try:
        # Send message to Kafka
        await kafka_producer.send_and_wait(KAFKA_TOPIC, log_data)
        print(f"Published to Kafka: {log_data}")
    except Exception as e:
        print(f"Failed to publish to Kafka: {e}")
        raise


def get_topic_name():
    """Get configured Kafka topic name"""
    return KAFKA_TOPIC
