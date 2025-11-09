import pika
import os
import json
from fastapi import HTTPException

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://api_user:StrongPassword123@localhost:5672/")

def get_rabbitmq_connection():
    try:
        params = pika.URLParameters(RABBITMQ_URL)
        return pika.BlockingConnection(params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to RabbitMQ: {e}")

def publish_message(queue_name: str, message: dict):
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, durable=True)
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2) 
        )
        connection.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish message: {e}")
