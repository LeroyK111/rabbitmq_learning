#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import pika
from pika.exchange_type import ExchangeType
"""
惰性队列的主要目标之一是能够支持非常长的队列（数百万条消息）。由于各种原因，队列可能会变得很长：

消费者离线/已崩溃/因维护而停机
消息入口突然激增，生产者超过消费者
消费者比平时慢
默认情况下，队列会在内存中保留消息缓存，当消息发布到 RabbitMQ 时，该缓存会被填满。这个缓存的想法是能够尽可能快地将消息传递给消费者。请注意，持久消息可以在进入代理时写入磁盘，同时保存在 RAM 中。

正常情况：消息保存在内存中
惰性队列：消息保存在磁盘中
"""


def callback(ch, method, properties, body):
    print("拒绝消费者%r" % body.decode())
    # 这里选择否定应答
    # ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    # 如果选择肯迪回答
    ch.basic_ack(delivery_tag=method.delivery_tag)


# 构造链接对象
parameters = pika.URLParameters('amqp://admin:123@192.168.1.100:5672/shiyan')
connection = pika.BlockingConnection(parameters)
"""
如果这里的消费者选择拒绝，则传入到死信交换机dead中
'x-dead-letter-exchange': 'dead',
带入信道字典
'x-dead-letter-routing-key': 'DLX'
"""

# 设置死信交换机信息，如果正常消费者被拒绝，则normal队列成为死队列，将exchange和routingkey替换后传个死信消费者
arguments = {
    'x-dead-letter-exchange': 'dead',
    'x-dead-letter-routing-key': 'DLX',
    # 加入队列数量限制，超出的部分传给死信，前提是这里不会消费消息速度过快
    "x-max-length": 3,
    # TODO 这个消费者优先级，参数应为 1 到 255 之间的正整数,越大则该队列消费者级别越高越优先处理，多数情况下channel.basic_qos足够用了
    "x-max-priority": 10,
    # TODO 该队列开启惰性模式，消息被存储在mq上的某个位置，这里要找文档.
    "x-queue-mode": "lazy"
}

# TTL生产者创建队列时的设置：有三种
# 1.使用x-expires属性控制，不管队列中是否还有消息，都将删除该队列,单位为毫秒
# 2.使用x-message-ttl属性控制:单位为毫秒，具备当前属性声明的队列，其中所有的消息都将在指定毫秒数后消失
# arguments = [{'x-expires': 100}, {'x-message-ttl': 10000}]
# 这里就可以通过限制信息数量or大小，来实现让队列超过长度限制而被转入死信
# arguments_xmaxlength = [{"x-max-length": 10}, {"x-max-length-bytes": 1000}]

# 信道也可以设置编号
channel = connection.channel()
# 绑定正常的交换机
channel.exchange_declare(exchange="normal", exchange_type="direct")
# 绑定死信交换机信息,传入死信参数
channel.queue_delete("normal")
channel.queue_declare(queue='normal',
                      durable=False,
                      exclusive=False,
                      arguments=arguments)
channel.queue_bind(queue="normal", exchange="normal", routing_key="normal")

channel.basic_qos(prefetch_count=1)
# 构建死信接收对象
channel.basic_consume(
    queue='normal',
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
