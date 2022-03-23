#!/usr/bin/python
# -*- coding: utf-8 -*-
import pika
import os
import sys
import time
"""
on_message_callback(channel, method, properties, body)
             - channel: BlockingChannel
             - method: spec.Basic.Deliver
             - properties: spec.BasicProperties
             - body: bytes

callback(ch, method, properties, body):
该方法有严苛定义
channel=阻塞通道，可以再次调用信道的方法，如: channel.basic_publish()再次发送，channel.queue_declare()重建队列等
method=方法,          手动回复应答时，需要method.delivery_tag标记
properties=属性       人为加入字典属性,可以直接看源码，一堆空值，人为定义
body=消息内容          这里就是字符串
"""


def main():
    # 写一个回调函数
    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body.decode())
        # 字符串中几个点
        time.sleep(body.count(b'.'))
        print(" [x] Done")
        # 选择肯定应答，测试手动消息确认delivery_tag=method.delivery_tag消息标记
        ch.basic_ack(delivery_tag=method.delivery_tag)
        """
        # 应答模式ch=channel
        delivery_tag=消息标记
        multiple=批量处理,可以减少网络堵塞
        requeue=重置队列,
        channel.basic_nack(delivery_tag=0, multiple=False, requeue=True) 
        channel.basic_ack(delivery_tag=0, multiple=False)  肯定应答，rabbitmq可以把消息丢弃
        channel.basic_reject(delivery_tag=0, requeue=True)  否定应答，不处理该消息了直接拒绝，requeue=True可以将其丢弃
        """

    # 构造链接对象
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
    channel = connection.channel()
    # 获取rabbitmq的返回值, 这里会拦截消息，一般用于测试
    # method_frame, header_frame, body = channel.basic_get(queue="he2", auto_ack=False)
    # print(method_frame, header_frame, body)

    # 构建队列，不会重复生成队列
    # # 声明消息队列，消息将在这个队列传递，如不存在，则创建。durable = True 代表消息队列持久化存储，False 非持久化存储
    channel.queue_declare(queue='he2', durable=True, exclusive=False)
    """
    您可能已经注意到调度仍然不能完全按照我们的意愿工作。例如，在有两个工人的情况下，当所有奇数消息很重而偶数消息都很轻时，一个工人将一直很忙，另一个工人几乎不做任何工作。好吧，RabbitMQ 对此一无所知，仍然会均匀地发送消息。
    发生这种情况是因为 RabbitMQ 只是在消息进入队列时分派消息。
    它不查看消费者未确认消息的数量。它只是盲目地将第 n 个消息发送给第 n 个消费者。
    为了解决这个问题，我们可以使用带有prefetch_count=1设置的Channel#basic_qos通道方法 。
    相反，它将把它分派给下一个不忙的工人.
    prefetch_count=1不公平分发
    prefetch_count>=2则开始比列分配

    除了改变channel的调度计划外
    1.加入更多的消费者
    2.使用消息TTL（生存时间和到期时间，消息时效性）
    """
    # TODO prefetch_count也被称作预取值，说白了这就是个比例系数，当有多个消费者时，大家会按照该值的大小分配消息数量，越大抢到活的比例越高
    channel.basic_qos(prefetch_count=1)
    """
    使用此代码，我们可以确定即使您在处理消息时使用 CTRL+C 杀死了一个工人，也不会丢失任何内容。工人死亡后不久，所有未确认的消息将被重新传递。
    """
    # 构建接收对象
    channel.basic_consume(
        queue='he2',
        auto_ack=False,  # 自动确认，并将消息移除队列。。。。关闭后，可以使用手动消息确认。
        # auto_ack=True,  # 一旦开启消息自动确认，则消息立马移除队列，不管消费者是否接收完毕。
        on_message_callback=callback)  # 调用函数

    # 开启循环接收
    print('输入ctrl+c即可停止接收')

    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("终止")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
