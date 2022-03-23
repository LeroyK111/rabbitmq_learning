#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
死信队列，无法被消费的信息。
produce将消息传递给channel，再由channel传递给exchange，exchange分发给queue，queue在分发给消费者channel，然后消费者就接到消息了。
exchange + queue == broker

当产生的message无法被从queue中取出时，则queue就称为私信队列。
某些特殊情况需要用到死信队列（保护数据不丢失）
当消息称为死信后，可以被重新发送到另外一个交换机，这个交换机被称为DLX(Dead Letter Exchange)

发生死信的来源:
1.消费者使用basic.reject或 basic.nack否定确认消息，并将requeue参数设置为false。
2.消息由于每条消息的 TTL而过期；
3.消息被丢弃，因为它的队列超过了长度限制

TODO 
如果队列和消息均设置了过期时间，遵循短板原则
并且，rabbitmq对于过期消息的检测为懒惰，只有在消息处于队列顶端，即将消费时，才会检测是否过期，如过期则移除
"""

import pika
from pika.exchange_type import ExchangeType
# 构造链接对象
parameters = pika.URLParameters('amqp://admin:123@192.168.1.100:5672/shiyan')
connection = pika.BlockingConnection(parameters)

# 信道也可以设置编号
channel = connection.channel()
# TODO 放入一个带有死信队列的消费者broker里
channel.exchange_declare(exchange="normal", exchange_type=ExchangeType.direct)
message = "Hello World!"

for i in range(10):
    # 将内容放进队列，routing_key=队列名，body=消息内容,exchange=中转交换器
    channel.basic_publish(exchange="normal",
                          routing_key='normal',
                          body=message)
# 在消息发布时则只有这一种，使用expiration参数，注意参数的值为字符串,之类设置的是消息存活时间
# channel.basic_publish(exchange="normal",
#                       routing_key='normal',
#                       body=message,
#                       properties=pika.BasicProperties(expiration="1000"))
print("发送消息[%s]" % message)

# 关闭链接
connection.close()
