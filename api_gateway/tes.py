import pika

connection = pika.BlockingConnection(pika.URLParameters("amqp://guest:guest@localhost:5672/"))
channel = connection.channel()
channel.queue_declare(queue="test.queue", durable=True)
channel.basic_publish(exchange="", routing_key="test.queue", body="Hello RabbitMQ")
connection.close()
print("Message sent!")
