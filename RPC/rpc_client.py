#!/usr/bin/python
# -*- coding: utf-8 -*-
import pika
import uuid


class FibonacciRpcClient(object):

    def __init__(self):
        """
        这里是构造了一个api
        """
        # 传入密码
        self.credentials = pika.PlainCredentials(username="admin",
                                                 password="123")
        # 构造链接
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host="192.168.1.100",  # 交换机ip
                port=5672,  # 队列端口
                virtual_host="/test",  # 虚拟对象
                credentials=self.credentials,  # 导入密码
            ))
        # 构建信道
        self.channel = self.connection.channel()
        # 构建队列，并且exclusive=True,为空则移除队列
        result = self.channel.queue_declare(queue='', exclusive=True)
        # 取名字
        self.callback_queue = result.method.queue
        # 构建接收对象
        self.channel.basic_consume(queue=self.callback_queue,
                                   on_message_callback=self.on_response,
                                   auto_ack=True)

    def on_response(self, ch, method, props, body):
        # 服务器接收到后，会返回一个massage，然后接收到后,将body赋值给response
        if self.corr_id == props.correlation_id:
            self.response = body
            # 这里可以看到识别id一致
            print(self.corr_id, "\n", props.correlation_id)

    def call(self, n):
        self.response = None
        # 生成一个随机数码
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='rpc_queue',
            properties=pika.BasicProperties(
                # 队列名
                reply_to=self.callback_queue,
                # 传个识别id
                correlation_id=self.corr_id,
            ),
            body=str(n))
        while self.response is None:
            # 如果输出值为空，则调用构造链接，并开始阻塞。等待接收数据
            self.connection.process_data_events()
        return int(self.response)


fibonacci_rpc = FibonacciRpcClient()

print("开始传送")
response = fibonacci_rpc.call(30)
print("%r" % response)
