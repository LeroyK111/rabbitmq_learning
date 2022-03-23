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
# 设置交换机
channel.exchange_declare(exchange='topic_logs', exchange_type='topic')
# 设置队列
result = channel.queue_declare('', exclusive=True)
queue_name = result.method.queue
# print("随机生成的队列名", queue_name)
# 设置筛选条件，也是以键的形式
binding_keys = sys.argv[1:]
if not binding_keys:
    sys.stderr.write("Usage: %s [binding_key]...\n" % sys.argv[0])
    sys.exit(1)
# 给队列，部署筛选键key
# # TODO python receive_logs_topic.py "#" 接收所有日志
for binding_key in binding_keys:
    channel.queue_bind(exchange='topic_logs',
                       queue=queue_name,
                       routing_key=binding_key)

print(' [*] Waiting for logs. To exit press CTRL+C')


def callback(ch, method, properties, body):
    print(" [x] %r:%r" % (method.routing_key, body))


channel.basic_consume(queue=queue_name,
                      on_message_callback=callback,
                      auto_ack=True)

channel.start_consuming()
