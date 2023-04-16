#!/usr/bin/python
# -*- coding: utf-8 -*-
import pika
import sys
"""
这个是路由的进阶，路由是按照键匹配给队列。
主题是按照筛选条件，匹配键给队列。
"""
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
# 设置交换机类型,主题筛选模式
channel.exchange_declare(exchange='topic_logs', exchange_type='topic')
# 给队列设置键值
routing_key = sys.argv[1] if len(sys.argv) > 2 else 'anonymous.info'
# 设置内容
message = ' '.join(sys.argv[2:]) or 'Hello World!'
# 发送
channel.basic_publish(exchange='topic_logs',
                      routing_key=routing_key,
                      body=message)
print(" [x] Sent %r:%r" % (routing_key, message))
connection.close()
