#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
python使用pika库，即可操作rabbitmq
python -m pip install pika --upgrade
"""

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
# 信道也可以设置编号
channel = connection.channel(channel_number=None)
# 移除信道
# channel.queue_delete("he2")
# 构建名称为he2的队列,durable=true消息持久化则一个消息可以共享多个生产者
# exclusive=true，一旦队列为空，则该队列自动移除
channel.queue_declare("he2")
# 这里只能由mq发送命令取消信道
# channel.cancel()
# 将内容放进队列，routing_key=队列名，body=消息内容,exchange=中转交换器
channel.basic_publish(exchange='', routing_key='he2', body='Hello World!')
print("发送helloworld")
# 关闭链接
connection.close()
