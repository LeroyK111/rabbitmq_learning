#!/usr/bin/python
# -*- coding: utf-8 -*-
import pika
import sys

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
"""
exchange
名称：日志
交换机类型: 
direct    把消息投递到那些binding key与routing key完全匹配的队列中
topic     将消息路由到binding key与routing key模式匹配的队列中
headers   Headers 类型的Exchanges是不处理路由键的,而是根据发送的消息内容中的headers属性进行匹配
fanout    广播到/test中的所有已知队列,发送端无需绑定队列
"""
# 定义交换机
channel.exchange_declare(exchange='logs', exchange_type='fanout')
# 给个输入
message = ' '.join(sys.argv[1:]) or "info: Hello World!"

# 发送消息，队列默认空，队列会自动生成
channel.basic_publish(exchange='logs', routing_key='', body=message)
print(" [x] Sent %r" % message)
connection.close()
