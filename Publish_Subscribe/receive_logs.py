#!/usr/bin/python
# -*- coding: utf-8 -*-
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
# 构建交换机
channel.exchange_declare(exchange='logs', exchange_type='fanout')
# 定义队列,queue=''为空则给个随机命名的队列,     exclusive=True一旦消费者连接关闭，队列应该被删除。
result = channel.queue_declare(queue='', exclusive=True)
# 对象属性id
queue_name = result.method.queue
"""
缺少channel.queue_bind()这一步的话
如果没有队列绑定到交换器，消息将丢失，但这对我们来说没关系；如果没有消费者在监听，我们可以安全地丢弃消息。
绑定routing_key的含义取决于交换类型。我们之前使用的 fanout扇出交换只是忽略了它的价值。
"""
# 绑定队列
channel.queue_bind(exchange='logs', queue=queue_name, routing_key="")

print('接收消息阻塞')


def callback(ch, method, properties, body):
    print(" [x] %r" % body)


channel.basic_consume(queue=queue_name,
                      on_message_callback=callback,
                      auto_ack=True)

channel.start_consuming()
