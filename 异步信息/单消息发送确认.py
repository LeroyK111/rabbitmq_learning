#!/usr/bin/python
# -*- coding: utf-8 -*-

from time import time
import pika
# 加入验证,不加默认user=guser,password=guser
credentials = pika.PlainCredentials(username="admin", password="123")
# 构造链接对象
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host="192.168.1.100",  # 交换机ip
        port=5672,  # 队列端口
        virtual_host="/test",  # 虚拟对象
        credentials=credentials,  # 导入密码
    ))
# channel信道
channel = connection.channel()

result = channel.queue_declare(queue="")
queuename = result.method.queue

# TODO 加入发布确认模式,进一步提高数据的安全性，保证生产者的数据百分百到rabbit中
channel.confirm_delivery()

start_time = time()
for i in range(1000):
    channel.basic_publish(exchange="", routing_key=queuename, body=str(i))
    method, properties, body = channel.basic_get(queue=queuename)
    if method.delivery_tag:
        print("消息发送成功")

stop_time = time()

print("单消息发布确认模式用时:%2fs" % (stop_time - start_time))

connection.close()
