#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
单消息，发布确认
"""

import sys
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

# TODO 加入发布确认模式,进一步提高数据的安全性，保证生产者的数据百分百到rabbit中
channel.confirm_delivery()

# 创建队列
channel.queue_declare(queue='he2', durable=True, exclusive=False)

message = "".join(sys.argv[1:]) or "Hello World!"

# 将内容放进队列，routing_key=队列名，body=消息内容,exchange=中转交换器,properties=模式设置,mandatory=开启后不用验证错消息
channel.basic_publish(exchange='',
                      routing_key='he2',
                      body=message,
                      properties=None,
                      mandatory=False)
# 获取信道中消息的数量
a = channel.get_waiting_message_count()
print(a)

connection.close()
