# -*- coding: utf-8 -*-
# pylint: disable=C0111,C0103,R0205

import functools
import logging
import json
import pika
from pika.exchange_type import ExchangeType


class ExamplePublisher(object):
    # 交换机名字
    EXCHANGE = 'message'
    # 设定交换机类型,广播
    EXCHANGE_TYPE = ExchangeType.topic
    # 间隔时间
    PUBLISH_INTERVAL = 1
    # 通道名字
    QUEUE = 'text'
    # 键名
    ROUTING_KEY = 'example.text'

    def __init__(self, amqp_url):
        """
        初始化元素
        """
        # 初始化
        self._connection = None
        self._channel = None

        self._deliveries = None
        self._acked = None
        self._nacked = None
        self._message_number = None

        self._stopping = False
        # 值进这里
        self._url = amqp_url

    def connect(self):
        """
        建立链接,返回链接对象
        """
        # 记录日志
        LOGGER.info('Connecting to %s', self._url)
        return pika.SelectConnection(
            # 链接参数导入
            pika.URLParameters(self._url),
            # 开启确认回调
            on_open_callback=self.on_connection_open,
            # 开启错误回调
            on_open_error_callback=self.on_connection_open_error,
            # rabbitmq关闭时的回调
            on_close_callback=self.on_connection_closed)

    def on_connection_open(self, _unused_connection):
        """
        如果要使用正确回调，则我们可以直接调用 _unused_connection
        """
        # 日志打印 链接成功
        LOGGER.info('Connection opened')
        # 调用打开信道
        self.open_channel()

    def on_connection_open_error(self, _unused_connection, err):
        """
        出现错误则等待5s，并且停止异步
        """
        LOGGER.error('Connection open failed, reopening in 5 seconds: %s', err)
        self._connection.ioloop.call_later(5, self._connection.ioloop.stop)

    def on_connection_closed(self, _unused_connection, reason):
        """
        当链接关闭时，停止异步循环
        """
        self._channel = None
        if self._stopping:
            self._connection.ioloop.stop()
        else:
            LOGGER.warning('Connection closed, reopening in 5 seconds: %s',
                           reason)
            self._connection.ioloop.call_later(5, self._connection.ioloop.stop)

    def open_channel(self):
        """
        创建一个新的队列
        """
        LOGGER.info('Creating a new channel')
        # 用select新的管道对象channel
        self._connection.channel(
            channel_number=None,  # 信道号默认空，则自动生成
            on_open_callback=self.on_channel_open)  # 打开信道时的回调，准备放消息进去

    def on_channel_open(self, channel):
        """
        信道打开后，绑定一个exchange
        """
        LOGGER.info('Channel opened')
        # 将信道参数赋值
        self._channel = channel
        # 如果出现异常，则关闭信道
        self.add_on_channel_close_callback()
        # 设置交换机,把交换机名字传入
        self.setup_exchange(self.EXCHANGE)

    def add_on_channel_close_callback(self):
        """
        如果出现异常，则关闭信道
        """
        LOGGER.info('Adding channel close callback')
        # 调用关闭信道方法，channel.add_on_close_callback()
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reason):
        """
        关闭信道后的操作，写错误日志，
        通道置空
        """
        LOGGER.warning('Channel %i was closed: %s', channel, reason)
        self._channel = None
        # 检查开关
        if not self._stopping:
            # 如果开启，则直接关闭链接
            self._connection.close()

    def setup_exchange(self, exchange_name):
        """
        设置交换机
        """
        LOGGER.info('Declaring exchange %s', exchange_name)
        # 调用方法funtools.partial(对象，参数1，参数2)，传递一部分方法
        cb = functools.partial(self.on_exchange_declareok,
                               userdata=exchange_name)
        # 设置交换机参数
        self._channel.exchange_declare(exchange=exchange_name,
                                       exchange_type=self.EXCHANGE_TYPE,
                                       callback=cb)

    def on_exchange_declareok(self, _unused_frame, userdata):
        """
        当交换机成功创建时，调用这里，
        用了一个functools.partial方法，
        当exchange在rabbitmq中构建失败，则_unused_frame成为新的对象
        """
        LOGGER.info('Exchange declared: %s', userdata)
        # 设置队列，把队列名传入
        self.setup_queue(self.QUEUE)

    def setup_queue(self, queue_name):
        """
        设置队列
        """
        LOGGER.info('Declaring queue %s', queue_name)
        # 调用信道的队列创建选项
        self._channel.queue_declare(
            queue=queue_name,  # 给队列名字
            callback=self.on_queue_declareok)  # 调用队列和交换机的绑定

    def on_queue_declareok(self, _unused_frame):
        """
        将队列和交换机绑定到一起
        绑定失败则_unused_frame
        """
        LOGGER.info('Binding %s to %s with %s', self.EXCHANGE, self.QUEUE,
                    self.ROUTING_KEY)
        # 绑定队列和交换机
        self._channel.queue_bind(
            self.QUEUE,
            self.EXCHANGE,
            #  加入键
            routing_key=self.ROUTING_KEY,
            #  调用绑定回调
            callback=self.on_bindok)

    def on_bindok(self, _unused_frame):
        """
        如果绑定失败则调用_unused_frame
        """
        LOGGER.info('Queue bound')
        # 发送消息到rabbitmq中间件
        self.start_publishing()

    def start_publishing(self):
        """
        启动交付确认，确认消息已发送到rabbitmq中
        """
        LOGGER.info('Issuing consumer related RPC commands')
        # 启动交付确认
        self.enable_delivery_confirmations()
        # 启动下一个消息
        self.schedule_next_message()

    def enable_delivery_confirmations(self):
        # TODO 监听队列
        LOGGER.info('Issuing Confirm.Select RPC command')
        # 启动交付确认，并且ack_nack_callback=开启成功or失败都监听的callback
        self._channel.confirm_delivery(
            ack_nack_callback=self.on_delivery_confirmation)

    def on_delivery_confirmation(self, method_frame):
        """
        交付确认失败了的回调
        """
        # 将交付内容分割，让类型赋值
        confirmation_type = method_frame.method.NAME.split('.')[1].lower()
        # 写个日志
        LOGGER.info('Received %s for delivery tag: %i', confirmation_type,
                    method_frame.method.delivery_tag)
        # 成功则成功的数量+1
        if confirmation_type == 'ack':
            self._acked += 1
        # 失败则失败的数量+1
        elif confirmation_type == 'nack':
            self._nacked += 1
        # 列表中移除一个交付标记(无论成功还是失败)
        self._deliveries.remove(method_frame.method.delivery_tag)

    def schedule_next_message(self):
        # 写个info日志记录
        LOGGER.info('Scheduling next message for %0.1f seconds',
                    self.PUBLISH_INTERVAL)
        # 链接传入ioloop，ioloop调用了call_later，异步的发送消息到信道中
        # TODO 这里涉及到tornado底层框架，要注意了
        self._connection.ioloop.call_later(
            self.PUBLISH_INTERVAL,  # 调用函数的间隔时间
            self.publish_message)  # 选择复用的函数

    def publish_message(self):
        """
        发送消息
        """
        # 发送过程中，如果通道关闭，或者信道被置空，则返回NONE给ioloop
        if self._channel is None or not self._channel.is_open:
            return
        # 消息头
        hdrs = {u'مفتاح': u' قيمة', u'键': u'值', u'キー': u'値'}
        # 设置消息的参数(多数没啥用呢)
        properties = pika.BasicProperties(
            app_id='example-publisher',  # 应用的id
            content_type='application/json',  # 消息内容的类型
            headers=hdrs)
        # 消息内容
        message = u'مفتاح قيمة 键 值 キー 値'
        # 向信道送消息
        self._channel.basic_publish(
            self.EXCHANGE,  # 交换机
            self.ROUTING_KEY,  # 队列中键key
            json.dumps(message, ensure_ascii=False),  # 将消息打包成json
            properties)
        # 消息数量+1
        self._message_number += 1
        # 列表中加入消息数量
        self._deliveries.append(self._message_number)
        # 写日志
        LOGGER.info('Published message # %i', self._message_number)
        # 递归调用
        self.schedule_next_message()

    def run(self):
        """
        使用ioloop运行代码？
        """
        # self._stopping=False 默认停止
        while not self._stopping:
            # TODO 这里就是循环器
            self._connection = None
            self._deliveries = []
            self._acked = 0
            self._nacked = 0
            self._message_number = 0

            try:
                self._connection = self.connect()
                self._connection.ioloop.start()
            except KeyboardInterrupt:
                # 停止
                self.stop()
                if (self._connection is not None
                        and not self._connection.is_closed):
                    # Finish closing
                    self._connection.ioloop.start()
        # 记录info,正常运行日志
        LOGGER.info('Stopped')

    def stop(self):
        """
        关闭方法
        """
        LOGGER.info('Stopping')
        # 停止标记置真
        self._stopping = True
        # 关闭信道
        self.close_channel()
        # 关闭链接
        self.close_connection()

    def close_channel(self):
        """
        调用关闭信道的方法
        """
        if self._channel is not None:
            LOGGER.info('Closing the channel')
            self._channel.close()

    def close_connection(self):
        """调用关闭链接的方法"""
        if self._connection is not None:
            LOGGER.info('Closing connection')
            self._connection.close()


# 设置日志格式:(日志等级,日志事件发生时间, 日志器名字)
LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
# 创建一个日志器,用'__main__'做名字
LOGGER = logging.getLogger(__name__)


def main():
    # 设置日志器参数，debug等级，格式为LOG_FORMAT
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)

    # 构造对象链接
    example = ExamplePublisher(
        'amqp://admin:123@localhost:5672/shiyan?connection_attempts=3&heartbeat=3600'
    )
    # 写个执行件
    example.run()


if __name__ == '__main__':
    main()
