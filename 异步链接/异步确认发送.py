import pika
from time import time


def on_open(connection):
    connection.channel(on_open_callback=on_channel_open)


def on_channel_open(channel):
    message = 'message body value' * 100
    start = time()
    for i in range(10000):
        channel.basic_publish(
            '', '', message,
            pika.BasicProperties(content_type='text/plain', delivery_mode=2))
        if i % 1000 == 0:
            print('publish', i)
#         timer.sleep(10)
    end = time() - start
    print(end)


# Step #1: Connect to RabbitMQ
parameters = pika.URLParameters('amqp://admin:123@192.168.1.100:5672/shiyan')

connection = pika.SelectConnection(parameters=parameters,
                                   on_open_callback=on_open)

try:

    # Step #2 - Block on the IOLoop
    connection.ioloop.start()

# Catch a Keyboard Interrupt to make sure that the connection is closed cleanly
except KeyboardInterrupt:

    # Gracefully close the connection
    connection.close()

    # Start the IOLoop again so Pika can communicate, it will stop on its own when the connection is closed
    connection.ioloop.start()
