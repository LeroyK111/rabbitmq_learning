#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
死信队列，无法被消费的信息。
produce将消息传递给channel，再由channel传递给exchange，exchange分发给queue，queue在分发给消费者channel，然后消费者就接到消息了。
exchange + queue == broker

当产生的message无法被从queue中取出时，则queue就称为私信队列。
某些特殊情况需要用到死信队列（保护数据不丢失）
当消息称为死信后，可以被重新发送到另外一个交换机，这个交换机被称为DLX(Dead Letter Exchange)

发生死信的来源:
1.消费者使用basic.reject或 basic.nack否定确认消息，并将requeue参数设置为false。
2.消息由于每条消息的 TTL而过期；
3.消息被丢弃，因为它的队列超过了长度限制

TODO 
如果队列和消息均设置了过期时间，遵循短板原则
并且，rabbitmq对于过期消息的检测为懒惰，只有在消息处于队列顶端，即将消费时，才会检测是否过期，如过期则移除

===============================================================================================================================
为了避免惰性的发生，使得存在同一个
打开网页，https://www.rabbitmq.com/community-plugins.html
把 rabbitmq_delayed_message_exchange-3.8.9-0199d11c.ez 文件拷贝到RabbitMQ安装目录下的 plugins 目录
输入rabbitmq-plugins enable rabbitmq_delayed_message_exchange
安装成功
教程https://www.cnblogs.com/yyee/p/14281111.html
===============================================================================================================================
                                        ----------------------------消费者1（未被激活）
                                        |(当全部消费者都没被激活时，死信消费者也不可能去消费消息，这就导致第一个消息被耗在队列中，第二第三等后续消息因为ttl的存在导致存活时间长短不一，本来能激活的消息也被第一个消息卡住了从而导致后续的消息失去有效性，结果就是都前往死信消费者那里)
                                        |(为了避免这种现象，推荐使用x-delayed-message消息延迟交换机，可以异步的被激活，自动的去queue中找那些我们需要的message)
生产者----exchange-------queue(message被放入队列中)--------------------消费者2（未被激活）
                                        |
                                        |---------------------------死信消费者（已经被激活）

安装完后，会增加一个 x-delayed-message 延迟交换机（python-pika库暂时无法操作，作用：可使消息在队列时的顺序发生改变，从而控制产生信息的积压。）
"""

import pika
from pika.exchange_type import ExchangeType
# 构造链接对象
parameters = pika.URLParameters('amqp://admin:123@192.168.1.100:5672/shiyan')
connection = pika.BlockingConnection(parameters)

# 信道也可以设置编号
channel = connection.channel()
# TODO 放入一个带有死信队列的消费者broker里
channel.exchange_declare(exchange="normal", exchange_type=ExchangeType.direct)
message = "Hello World!"

# 在消息发布时则只有这一种，使用expiration参数，注意参数的值为字符串,之类设置的是消息存活时间
channel.basic_publish(exchange="normal",
                      routing_key='normal',
                      body=message,
                      properties=pika.BasicProperties(expiration="1000"))
print("发送消息[%s]" % message)

# 关闭链接
connection.close()
