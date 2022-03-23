#!/usr/bin/python
# -*- coding: utf-8 -*-

import pika
from pika.exchange_type import ExchangeType
"""
使用策略配置死信队列   https://www.rabbitmq.com/dlx.html  不常用
"""


def callback(ch, method, properties, body):
    print("死信消费者%r" % body.decode())
    # 这里选择否定应答
    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    # 如果选择确认回答，就先不连锁了
    # ch.basic_ack(delivery_tag=method.delivery_tag)


# 构造链接对象
parameters = pika.URLParameters('amqp://admin:123@192.168.1.100:5672/shiyan')
connection = pika.BlockingConnection(parameters)

# 信道也可以设置编号
channel = connection.channel()
# 传入死信参数
arguments = {
    'x-dead-letter-exchange': 'dead_2',
    'x-dead-letter-routing-key': 'DLX_2'
}

channel.exchange_declare(exchange="dead", exchange_type="direct")
channel.queue_declare(queue='DLX',
                      durable=False,
                      exclusive=False,
                      arguments=arguments)
channel.queue_bind(queue="DLX", exchange="dead", routing_key="DLX")
channel.basic_qos(prefetch_count=1)

# 构建死信接收对象
channel.basic_consume(
    queue='DLX',
    auto_ack=False,  # 自动确认，并将消息移除队列。。。。关闭后，可以使用手动消息确认。
    # auto_ack=True,  # 一旦开启消息自动确认，则消息立马移除队列，不管消费者是否接收完毕。
    on_message_callback=callback)  # 调用函数

# 开启循环接收
try:
    print('输入ctrl+c即可停止接收')
    channel.start_consuming()

except KeyboardInterrupt:
    channel.close()
    connection.close()
