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
# 建立一个专属队列
channel.queue_declare(queue='rpc_queue')


# 构造斐波那契函数求和
def fib(n):
    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fib(n - 1) + fib(n - 2)


# 回调函数
def on_request(ch, method, props, body):
    # 将字符串转为10进制
    n = int(body)
    """
    服务端和客户端，通过ch.basic_publish
    互相
    """
    # 输出客户端的值
    print("得到值:", str(n))
    # 得到斐波那契
    response = fib(n)
    # 这里还能再发个值返回客户端
    ch.basic_publish(
        exchange='',
        routing_key=props.reply_to,
        properties=pika.BasicProperties(correlation_id=props.correlation_id),
        body=str(response))
    # 手动消息确认
    ch.basic_ack(delivery_tag=method.delivery_tag)


"""
您可能已经注意到调度仍然不能完全按照我们的意愿工作。例如，在有两个工人的情况下，当所有奇数消息很重而偶数消息都很轻时，一个工人将一直很忙，另一个工人几乎不做任何工作。好吧，RabbitMQ 对此一无所知，仍然会均匀地发送消息。
发生这种情况是因为 RabbitMQ 只是在消息进入队列时分派消息。
它不查看消费者未确认消息的数量。它只是盲目地将第 n 个消息发送给第 n 个消费者。
为了解决这个问题，我们可以使用带有prefetch_count=1设置的Channel#basic_qos通道方法 。
相反，它将把它分派给下一个不忙的工人.

除了改变channel的调度计划外
1.加入更多的消费者
2.使用消息TTL（生存时间和到期时间，消息时效性）
"""
channel.basic_qos(prefetch_count=1)
# 信道接收
channel.basic_consume(queue='rpc_queue', on_message_callback=on_request)

print("服务端启动")
# 开始阻塞
channel.start_consuming()
