#!/usr/bin/python
# -*- coding: utf-8 -*-
import pika, os, sys


def main():
    # 写一个回调函数
    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body)

    def cancel_callback(ch, method, properties, body):
        print("信道被mq取消")

    # 构造链接对象
    # 加入验证,不加默认user=guser,password=guser
    credentials = pika.PlainCredentials(username="admin", password="123")
    # 构造链接对象
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host="127.0.0.1",  # 交换机ip
            port=5672,  # 队列端口
            virtual_host="/",  # 虚拟对象
            credentials=credentials,  # 导入密码
        ))
    channel = connection.channel()

    # 构建队列，不会重复生成队列
    # # 声明消息队列，消息将在这个队列传递，如不存在，则创建。durable = True 代表消息队列持久化存储，False 非持久化存储
    channel.queue_declare(queue='he2', durable=False, exclusive=False)
    # 这里只能由mq发送命令取消信道
    # channel.cancel()
    channel.add_on_cancel_callback(cancel_callback)
    # 构建接收对象
    channel.basic_consume(
        queue='he2',
        auto_ack=True,  # 自动确认，并将消息移除队列
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
