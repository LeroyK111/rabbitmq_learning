#!/usr/bin/python
# -*- coding: utf-8 -*-

import pika
import sys
"""
路由模式说白了，就是传个字典给工人，然后分门别类取键值
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
# 命名交换机，设置类型，使用交换机direct模式，发送定向广播
channel.exchange_declare(exchange='direct_logs', exchange_type='direct')
# 创建队列键名,取第一组第一个字符
severity = sys.argv[1] if len(sys.argv) > 1 else 'info'
# 编辑消息
message = ' '.join(sys.argv[2:]) or 'Hello World!'
# 传入消息
channel.basic_publish(exchange='direct_logs',
                      routing_key=severity,
                      body=message)
print(" [x] Sent %r:%r" % (severity, message))
connection.close()
