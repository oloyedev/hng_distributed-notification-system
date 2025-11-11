import pika
import json
import uuid
import random
from datetime import datetime

# RabbitMQ connection
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='push.queue')

# Sample data
user_ids = ["user_001", "user_002", "user_003"]
notification_types = ["info", "alert", "reminder"]
template_codes = ["WELCOME_TEMPLATE", "ALERT_TEMPLATE", "REMINDER_TEMPLATE"]

# Send multiple test messages
for i in range(5):  # Change 5 to however many messages you want to test
    user_id = random.choice(user_ids)
    notification_type = random.choice(notification_types)
    template_code = random.choice(template_codes)
    request_id = str(uuid.uuid4())

    message = {
        "notification_type": notification_type,
        "user_id": user_id,
        "template_code": template_code,
        "variables": {
            "title": f"Test Message {i+1}",
            "body": f"Hello {user_id}, this is a {notification_type} message!",
            "timestamp": datetime.now().isoformat()
        },
        "request_id": request_id
    }

    channel.basic_publish(
        exchange='',
        routing_key='push.queue',
        body=json.dumps(message)
    )

    print(f"Sent message {i+1} to queue 'push.queue': {message}")

connection.close()
print("All test messages sent!")
