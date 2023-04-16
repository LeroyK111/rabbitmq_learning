import pika
"""
可以构造多个链接
parameters = (
    pika.ConnectionParameters(host='rabbitmq.zone1.yourdomain.com'),
    pika.ConnectionParameters(host='rabbitmq.zone2.yourdomain.com',
                              connection_attempts=5, retry_delay=1))
connection = pika.BlockingConnection(parameters)
"""

credentials = pika.PlainCredentials(username="admin", password="123")
# 异步链接很舒服
connection = pika.adapters.tornado_connection.TornadoConnection(
    pika.ConnectionParameters(
        host="192.168.1.100",  # 交换机ip
        port=5672,  # 队列端口
        virtual_host="/test",  # 虚拟对象
        credentials=credentials,  # 导入密码
    ))
# 构造通道
channel = connection.channel()
# 构造队列
