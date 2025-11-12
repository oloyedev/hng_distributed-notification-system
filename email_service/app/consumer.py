import json
import pika
import redis
from .config import settings
from .email import send_email
from .utils import render_template

redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

def process_email(ch, method, properties, body):
    message = json.loads(body)
    request_id = message.get("request_id")

    # Idempotency check
    if redis_client.get(request_id):
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    try:
        
        user_email = message.get("user_email")

        html_body = render_template(message["template_code"], message["variables"])
        send_email(user_email, "Notification", html_body)

        # Save request_id in Redis
        redis_client.set(request_id, "done")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print("Email sending failed:", e)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def start_consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=settings.RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=settings.RABBITMQ_EMAIL_QUEUE, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=settings.RABBITMQ_EMAIL_QUEUE, on_message_callback=process_email)
    print("Email consumer started...")
    channel.start_consuming()
