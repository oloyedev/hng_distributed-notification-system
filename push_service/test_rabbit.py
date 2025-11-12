# test_rabbit.py
import pika
import time
import sys

def test_connection():
    # Use the same parameters as your application
    HOST = "localhost"
    PORT = 5672
    USER = "guest"
    PASS = "guest"
    VHOST = "/"
    
    print(f"Attempting connection to {HOST}:{PORT}...")

    credentials = pika.PlainCredentials(USER, PASS)
    parameters = pika.ConnectionParameters(
        host=HOST,
        port=PORT,
        virtual_host=VHOST,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300
    )

    try:
        connection = pika.BlockingConnection(parameters)
        connection.close()
        print("\n✅ SUCCESS: Connection established and closed successfully.")
        return True
    except pika.exceptions.AMQPConnectionError as e:
        print(f"\n❌ FAILURE: AMQPConnectionError. RabbitMQ is unreachable.")
        print(f"Details: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return False

# Run the test
if not test_connection():
    sys.exit(1)