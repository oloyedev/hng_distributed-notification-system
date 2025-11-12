import pika
import json
from app.config import settings

# Connect to RabbitMQ
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        credentials=pika.PlainCredentials(
            username=settings.RABBITMQ_USER,
            password=settings.RABBITMQ_PASSWORD
        )
    )
)
channel = connection.channel()

# Make sure the queue exists
channel.queue_declare(queue=settings.RABBITMQ_EMAIL_QUEUE, durable=True)

# Test message
message = {
    "request_id": "test123",
    "user_email": "olatunjinelson06@gmail.com",  # Replace with the email you want to receive
    "template_code": "welcome",             # Must match a template your render_template function can handle
    "variables": {
        "name": "Olayide",
        "app_name": "HNG Notification Service"
    }
}

# Publish the message
channel.basic_publish(
    exchange='',
    routing_key=settings.RABBITMQ_EMAIL_QUEUE,
    body=json.dumps(message),
    properties=pika.BasicProperties(
        delivery_mode=2  # make message persistent
    )
)

print("Test email message sent!")
connection.close()
