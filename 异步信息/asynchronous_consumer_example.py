# -*- coding: utf-8 -*-
# pylint: disable=C0111,C0103,R0205

import functools
import logging
import time
import pika
from pika.exchange_type import ExchangeType

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)


class ExampleConsumer(object):
    """This is an example consumer that will handle unexpected interactions
    with RabbitMQ such as channel and connection closures.

    If RabbitMQ closes the connection, this class will stop and indicate
    that reconnection is necessary. You should look at the output, as
    there are limited reasons why the connection may be closed, which
    usually are tied to permission related issues or socket timeouts.

    If the channel is closed, it will indicate a problem with one of the
    commands that were issued and that should surface in the output as well.

    """
    EXCHANGE = 'message'
    EXCHANGE_TYPE = ExchangeType.topic
    QUEUE = 'text'
    ROUTING_KEY = 'example.text'

    def __init__(self, amqp_url):
        """Create a new instance of the consumer class, passing in the AMQP
        URL used to connect to RabbitMQ.

        :param str amqp_url: The AMQP url to connect with

        """
        self.should_reconnect = False
        self.was_consuming = False

        self._connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None
        self._url = amqp_url
        self._consuming = False
        # In production, experiment with higher prefetch values
        # for higher consumer throughput
        self._prefetch_count = 1

    def connect(self):
        """This method connects to RabbitMQ, returning the connection handle.
        When the connection is established, the on_connection_open method
        will be invoked by pika.

        :rtype: pika.SelectConnection

        """
        LOGGER.info('Connecting to %s', self._url)
        return pika.SelectConnection(
            parameters=pika.URLParameters(self._url),
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error,
            on_close_callback=self.on_connection_closed)

    def close_connection(self):
        self._consuming = False
        if self._connection.is_closing or self._connection.is_closed:
            LOGGER.info('Connection is closing or already closed')
        else:
            LOGGER.info('Closing connection')
            self._connection.close()

    def on_connection_open(self, _unused_connection):
        """This method is called by pika once the connection to RabbitMQ has
        been established. It passes the handle to the connection object in
        case we need it, but in this case, we'll just mark it unused.

        :param pika.SelectConnection _unused_connection: The connection

        """
        LOGGER.info('Connection opened')
        self.open_channel()

    def on_connection_open_error(self, _unused_connection, err):
        """
        出现链接错误
        """
        LOGGER.error('Connection open failed: %s', err)
        self.reconnect()

    def on_connection_closed(self, _unused_connection, reason):
        # 如果链接关闭则直接停止，异步链接服务器接收消息
        """This method is invoked by pika when the connection to RabbitMQ is
        closed unexpectedly. Since it is unexpected, we will reconnect to
        RabbitMQ if it disconnects.

        :param pika.connection.Connection connection: The closed connection obj
        :param Exception reason: exception representing reason for loss of
            connection.

        """
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            LOGGER.warning('Connection closed, reconnect necessary: %s',
                           reason)
            self.reconnect()

    def reconnect(self):
        """
        标记置true
        """
        self.should_reconnect = True
        # 关闭ioloop
        self.stop()

    def open_channel(self):
        """Open a new channel with RabbitMQ by issuing the Channel.Open RPC
        command. When RabbitMQ responds that the channel is open, the
        on_channel_open callback will be invoked by pika.

        """
        LOGGER.info('Creating a new channel')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        """This method is invoked by pika when the channel has been opened.
        The channel object is passed in so we can make use of it.

        Since the channel is now open, we'll declare the exchange to use.

        :param pika.channel.Channel channel: The channel object

        """
        LOGGER.info('Channel opened')
        self._channel = channel
        self.add_on_channel_close_callback()
        self.setup_exchange(self.EXCHANGE)

    def add_on_channel_close_callback(self):
        """This method tells pika to call the on_channel_closed method if
        RabbitMQ unexpectedly closes the channel.

        """
        LOGGER.info('Adding channel close callback')
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reason):
        """Invoked by pika when RabbitMQ unexpectedly closes the channel.
        Channels are usually closed if you attempt to do something that
        violates the protocol, such as re-declare an exchange or queue with
        different parameters. In this case, we'll close the connection
        to shutdown the object.

        :param pika.channel.Channel: The closed channel
        :param Exception reason: why the channel was closed

        """
        LOGGER.warning('Channel %i was closed: %s', channel, reason)
        self.close_connection()

    def setup_exchange(self, exchange_name):
        """Setup the exchange on RabbitMQ by invoking the Exchange.Declare RPC
        command. When it is complete, the on_exchange_declareok method will
        be invoked by pika.

        :param str|unicode exchange_name: The name of the exchange to declare

        """
        LOGGER.info('Declaring exchange: %s', exchange_name)
        # Note: using functools.partial is not required, it is demonstrating
        # how arbitrary data can be passed to the callback when it is called
        cb = functools.partial(self.on_exchange_declareok,
                               userdata=exchange_name)
        self._channel.exchange_declare(exchange=exchange_name,
                                       exchange_type=self.EXCHANGE_TYPE,
                                       callback=cb)

    def on_exchange_declareok(self, _unused_frame, userdata):
        """Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
        command.

        :param pika.Frame.Method unused_frame: Exchange.DeclareOk response frame
        :param str|unicode userdata: Extra user data (exchange name)

        """
        LOGGER.info('Exchange declared: %s', userdata)
        self.setup_queue(self.QUEUE)

    def setup_queue(self, queue_name):
        """Setup the queue on RabbitMQ by invoking the Queue.Declare RPC
        command. When it is complete, the on_queue_declareok method will
        be invoked by pika.

        :param str|unicode queue_name: The name of the queue to declare.

        """
        LOGGER.info('Declaring queue %s', queue_name)
        cb = functools.partial(self.on_queue_declareok, userdata=queue_name)
        self._channel.queue_declare(queue=queue_name, callback=cb)

    def on_queue_declareok(self, _unused_frame, userdata):
        """Method invoked by pika when the Queue.Declare RPC call made in
        setup_queue has completed. In this method we will bind the queue
        and exchange together with the routing key by issuing the Queue.Bind
        RPC command. When this command is complete, the on_bindok method will
        be invoked by pika.

        :param pika.frame.Method _unused_frame: The Queue.DeclareOk frame
        :param str|unicode userdata: Extra user data (queue name)

        """
        queue_name = userdata
        LOGGER.info('Binding %s to %s with %s', self.EXCHANGE, queue_name,
                    self.ROUTING_KEY)
        cb = functools.partial(self.on_bindok, userdata=queue_name)
        self._channel.queue_bind(queue_name,
                                 self.EXCHANGE,
                                 routing_key=self.ROUTING_KEY,
                                 callback=cb)

    def on_bindok(self, _unused_frame, userdata):
        """Invoked by pika when the Queue.Bind method has completed. At this
        point we will set the prefetch count for the channel.

        :param pika.frame.Method _unused_frame: The Queue.BindOk response frame
        :param str|unicode userdata: Extra user data (queue name)

        """
        LOGGER.info('Queue bound: %s', userdata)
        # 设置队列的分发方式
        self.set_qos()

    def set_qos(self):
        """This method sets up the consumer prefetch to only be delivered
        one message at a time. The consumer must acknowledge this message
        before RabbitMQ will deliver another one. You should experiment
        with different prefetch values to achieve desired performance.

        """
        # self._prefetch_count=1 为不公平分发
        self._channel.basic_qos(prefetch_count=self._prefetch_count,
                                callback=self.on_basic_qos_ok)

    def on_basic_qos_ok(self, _unused_frame):
        """Invoked by pika when the Basic.QoS method has completed. At this
        point we will start consuming messages by calling start_consuming
        which will invoke the needed RPC commands to start the process.

        :param pika.frame.Method _unused_frame: The Basic.QosOk response frame

        """
        LOGGER.info('QOS set to: %d', self._prefetch_count)
        # 如果队列的参数设置失败，则调用_unused_frame
        self.start_consuming()

    def start_consuming(self):
        """This method sets up the consumer by first calling
        add_on_cancel_callback so that the object is notified if RabbitMQ
        cancels the consumer. It then issues the Basic.Consume RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. We keep the value to use it when we want to
        cancel consuming. The on_message method is passed in as a callback pika
        will invoke when a message is fully received.

        """
        LOGGER.info('Issuing consumer related RPC commands')
        # 如果rabbitmq取消了队列，则调用这里
        self.add_on_cancel_callback()
        # 调用信道接收消息，传入队列名称和callback
        self._consumer_tag = self._channel.basic_consume(
            self.QUEUE, self.on_message)
        # 改变标记
        self.was_consuming = True
        self._consuming = True

    def add_on_cancel_callback(self):
        """Add a callback that will be invoked if RabbitMQ cancels the consumer
        for some reason. If RabbitMQ does cancel the consumer,
        on_consumer_cancelled will be invoked by pika.

        """
        LOGGER.info('Adding consumer cancellation callback')
        # 如果信道确认服务器不允许建立队列，则调用
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer
        receiving messages.

        :param pika.frame.Method method_frame: The Basic.Cancel frame

        """
        LOGGER.info('Consumer was cancelled remotely, shutting down: %r',
                    method_frame)
        # 记得关闭信道
        if self._channel:
            self._channel.close()

    def on_message(self, _unused_channel, basic_deliver, properties, body):
        """
        异步接收信道中的消息
        basic_deliver 相当于 method
        """
        LOGGER.info('Received message # %s from %s: %s',
                    basic_deliver.delivery_tag, properties.app_id, body)
        # 传递消息确认标记
        self.acknowledge_message(basic_deliver.delivery_tag)

    def acknowledge_message(self, delivery_tag):
        """Acknowledge the message delivery from RabbitMQ by sending a
        Basic.Ack RPC method for the delivery tag.

        :param int delivery_tag: The delivery tag from the Basic.Deliver frame

        """
        LOGGER.info('Acknowledging message %s', delivery_tag)
        # 信道返回返回确认标记
        self._channel.basic_ack(delivery_tag)

    def stop_consuming(self):
        """Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.

        """
        if self._channel:
            LOGGER.info('Sending a Basic.Cancel RPC command to RabbitMQ')
            cb = functools.partial(self.on_cancelok,
                                   userdata=self._consumer_tag)
            # 当某个消费者死掉时，关闭这个队列
            self._channel.basic_cancel(self._consumer_tag, cb)

    def on_cancelok(self, _unused_frame, userdata):
        """This method is invoked by pika when RabbitMQ acknowledges the
        cancellation of a consumer. At this point we will close the channel.
        This will invoke the on_channel_closed method once the channel has been
        closed, which will in-turn close the connection.

        :param pika.frame.Method _unused_frame: The Basic.CancelOk frame
        :param str|unicode userdata: Extra user data (consumer tag)

        """
        self._consuming = False
        LOGGER.info(
            'RabbitMQ acknowledged the cancellation of the consumer: %s',
            userdata)
        self.close_channel()

    def close_channel(self):
        """Call to close the channel with RabbitMQ cleanly by issuing the
        Channel.Close RPC command.

        """
        LOGGER.info('Closing the channel')
        self._channel.close()

    def run(self):
        """
        设置链接
        """
        self._connection = self.connect()
        # 直接重复链接到rabbitmq
        self._connection.ioloop.start()

    def stop(self):
        """Cleanly shutdown the connection to RabbitMQ by stopping the consumer
        with RabbitMQ. When RabbitMQ confirms the cancellation, on_cancelok
        will be invoked by pika, which will then closing the channel and
        connection. The IOLoop is started again because this method is invoked
        when CTRL-C is pressed raising a KeyboardInterrupt exception. This
        exception stops the IOLoop which needs to be running for pika to
        communicate with RabbitMQ. All of the commands issued prior to starting
        the IOLoop will be buffered but not processed.

        """
        if not self._closing:
            self._closing = True
            LOGGER.info('Stopping')
            if self._consuming:
                # 查看
                self.stop_consuming()
                self._connection.ioloop.start()
            else:
                self._connection.ioloop.stop()
            LOGGER.info('Stopped')


class ReconnectingExampleConsumer(object):
    """This is an example consumer that will reconnect if the nested
    ExampleConsumer indicates that a reconnect is necessary.

    """

    def __init__(self, amqp_url):
        self._reconnect_delay = 0
        self._amqp_url = amqp_url
        self._consumer = ExampleConsumer(self._amqp_url)

    def run(self):
        while True:
            try:
                self._consumer.run()
            except KeyboardInterrupt:
                self._consumer.stop()
                break
            self._maybe_reconnect()

    def _maybe_reconnect(self):
        if self._consumer.should_reconnect:
            self._consumer.stop()
            # 异步间隔时间
            reconnect_delay = self._get_reconnect_delay()
            LOGGER.info('Reconnecting after %d seconds', reconnect_delay)
            # 休眠时间
            time.sleep(reconnect_delay)
            # 再次启动
            self._consumer = ExampleConsumer(self._amqp_url)

    def _get_reconnect_delay(self):
        # 获取异步间隔时间
        if self._consumer.was_consuming:
            # 有队列还存活，间隔时间为0
            self._reconnect_delay = 0
        else:
            # 否则就让ioloop重启间隔+1
            self._reconnect_delay += 1
        if self._reconnect_delay > 30:
            # 当间隔大于30s时，固定间隔时间
            self._reconnect_delay = 30
        # 返回间隔时间 
        return self._reconnect_delay


def main():
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
    amqp_url = 'amqp://guest:guest@localhost:5672/%2F'
    consumer = ReconnectingExampleConsumer(amqp_url)
    consumer.run()


if __name__ == '__main__':
    main()
