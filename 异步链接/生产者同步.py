#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
经过hello world
一个生产者对多个消费者时,消费信息的方式会交替循环
默认情况下，RabbitMQ 会按顺序将每条消息发送给下一个消费者。
平均而言，每个消费者都会收到相同数量的消息。这种分发消息的方式称为轮询。
"""

import sys
import pika
# 加入验证,不加默认user=guser,password=guser
credentials = pika.PlainCredentials(username="admin", password="123")
# credentials = pika.ExternalCredentials() 外部凭证ssl证书
# 构造链接对象
connection = pika.BlockingConnection(
    # pika.ConnectionParameters() 一般链接参数                                %2f编码           ?heartbeat=30
    # pika.URLParameters("amqp://username账户:password密码@host地址:port端口/<virtual_host>主机名[?query-string]")
    # amqps://www-data:rabbit_pwd@rabbit1/web_messages?heartbeat=30
    pika.ConnectionParameters(
        host="192.168.1.100",  # 交换机ip
        port=5672,  # 队列端口
        virtual_host="/test",  # 虚拟对象
        credentials=credentials,  # 导入密码
    ))
# channel信道
channel = connection.channel()
# TODO 加入发布确认模式,进一步提高数据的安全性，保证生产者的数据百分百到rabbit中
channel.confirm_delivery()
# 构建名称为he2的队列,durable=true消息持久化则一个消息可以共享多个生产者
# exclusive=true，一旦队列为空，则该队列自动移除


def nackcallback(ch, method, properties, body):
    # 发送消息失败后调用,一般选择再次发送，或者是记录通知用户
    pass


# 当发送到rabbitmq的过程中出现错误，则调用此方法
channel.add_on_return_callback(callback=nackcallback)
"""
当 RabbitMQ 退出或崩溃时，它会忘记队列和消息，除非你告诉它不要这样做。确保消息不会丢失需要做两件事：我们需要将队列和消息都标记为持久的。
持久化队列    durable=True 创建一个he2的新队列。
消息持久化 - 通过提供具有pika.spec.PERSISTENT_DELIVERY_MODE值的delivery_mode属性

将消息标记为持久性并不能完全保证消息不会丢失。虽然它告诉 RabbitMQ 将消息保存到磁盘，但是当 RabbitMQ 接受消息并且还没有保存它时，仍然有很短的时间窗口。
如果需要更强的确认，则可以使用https://www.rabbitmq.com/confirms.html
"""
channel.queue_declare(queue='he2', durable=True, exclusive=False)
message = "".join(sys.argv[1:]) or "Hello World!"

# 将内容放进队列，routing_key=队列名，body=消息内容,exchange=中转交换器
channel.basic_publish(
    exchange='',
    routing_key='he2',
    body=message,
    properties=pika.BasicProperties(
        delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE),
    #  通过设置强制标志,保证消息传递
    mandatory=True)
print("发送消息[%s]" % message)
# 关闭链接
connection.close()
