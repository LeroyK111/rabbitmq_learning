#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
https://www.rabbitmq.com/ae.html
备份交换机
"""

import pika
from pika.exchange_type import ExchangeType
# 构造链接对象
parameters = pika.URLParameters('amqp://admin:123@192.168.1.100:5672/shiyan')
connection = pika.BlockingConnection(parameters)

# 带入备用交换机的参数
arguments = {"alternate-exchange": "normal_ae"}

# 信道也可以设置编号
channel = connection.channel()
# TODO 放入一个带有死信队列的消费者broker里
channel.exchange_declare(exchange="normal",
                         exchange_type=ExchangeType.direct,
                         arguments=arguments)
channel.exchange_declare(exchange="normal_ae",
                         exchange_type=ExchangeType.fanout)
# 设置normal的队列参数，并绑定
channel.queue_declare(queue="routed")
channel.queue_bind("routed", "normal", "key1")
# 设置normal_ae的队列参数，并绑定
channel.queue_declare(queue="unrouted")
channel.queue_bind("unrouted", "normal_ae", "key2")

message = "Hello World!"

for i in range(10):
    # 将内容放进队列，routing_key=队列名，body=消息内容,exchange=中转交换器
    channel.basic_publish(exchange="normal",
                          routing_key='normal',
                          body=message)

print("发送消息[%s]" % message)

# 关闭链接
connection.close()
