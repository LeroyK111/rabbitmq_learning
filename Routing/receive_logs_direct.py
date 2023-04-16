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
channel.exchange_declare(exchange='direct_logs', exchange_type='direct')
# 设置队列
"""
queue ( str ) -- 队列名称；如果为空字符串，代理将创建一个唯一的队列名称
passive( bool ) -- 只检查队列是否存在
durable（布尔） - 队列是否持久化
exclusive( bool ) -- 只允许当前连接访问
auto_delete ( bool ) – 消费者取消或断开连接后删除
arguments ( dict ) -- 队列的自定义键/值参数
callback( callable ) – 方法 Queue.DeclareOk 的回调(pika.frame.Method)
"""
result = channel.queue_declare(queue='', exclusive=True, passive=False)
queue_name = result.method.queue
# 队列删除
# channel.queue_delete()
# 删除队列中的信息
# channel.queue_purge
# 写入
severities = sys.argv[1:]
# 避免出现空值
if not severities:
    sys.stderr.write("Usage: %s [info] [warning] [error]\n" % sys.argv[0])
    sys.exit(1)
# 创建多个key，绑定交换机和队列
# 路由模式说白了，就是传个字典给工人，然后分门别类取键值
for severity in severities:
    channel.queue_bind(exchange='direct_logs',
                       queue=queue_name,
                       routing_key=severity,
                       arguments=None)
# channel.queue_unbind() 取消绑定
print(' [*] Waiting for logs. To exit press CTRL+C')

# 删除交换机
# channel.exchange_delete()

# 设定交换机
# channel.exchange_declare()

# 接触绑定
# channel.exchange_unbind()
# 交换绑定
# exchange.bind

# 提交交易
# channel.tx_commit()
# 回滚事务。
# channel.tx_rollback()

# 选择标准交易模式。此方法将通道设置为使用标准事务。在使用 Commit 或 Rollback 方法之前，客户端必须在通道上至少使用此方法一次。
# channel.tx_select()

# 回调显示
def callback(ch, method, properties, body):
    print(" [x] %r:%r" % (method.routing_key, body))


# 接收
channel.basic_consume(queue=queue_name,
                      on_message_callback=callback,
                      auto_ack=True)

# 退出循环时，请务必调用 consumer.cancel() 以返回任何未处理的消息
# requeued_messages = channel.cancel()
# print(requeued_messages)

channel.start_consuming()
