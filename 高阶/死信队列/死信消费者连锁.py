#!/usr/bin/python
# -*- coding: utf-8 -*-

import pika
"""
使用策略配置死信队列   https://www.rabbitmq.com/dlx.html  不常用
"""


def callback(ch, method, properties, body):
    print("死信连锁%r" % body.decode())


# 构造链接对象
parameters = pika.URLParameters('amqp://admin:123@192.168.1.100:5672/shiyan')
connection = pika.BlockingConnection(parameters)

# 信道也可以设置编号
channel = connection.channel()

channel.exchange_declare(exchange="dead_2", exchange_type="direct")
channel.queue_declare(queue='DLX_2', durable=False, exclusive=False)
channel.queue_bind(queue="DLX_2", exchange="dead_2", routing_key="DLX_2")
channel.basic_qos(prefetch_count=1)

# 构建死信接收对象
channel.basic_consume(queue='DLX_2',
                      auto_ack=True,
                      on_message_callback=callback)

# 开启循环接收
try:
    print('输入ctrl+c即可停止接收')
    channel.start_consuming()
except KeyboardInterrupt:
    channel.close()
    connection.close()
