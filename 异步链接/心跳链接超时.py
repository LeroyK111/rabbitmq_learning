import pika


def main():

    # NOTE: These parameters work with all Pika connection types
    params = pika.ConnectionParameters(heartbeat=600,
                                       blocked_connection_timeout=300)

    conn = pika.BlockingConnection(params)

    chan = conn.channel()

    chan.basic_publish('', 'my-alphabet-queue', "abc")

    # If publish causes the connection to become blocked, then this conn.close()
    # would hang until the connection is unblocked, if ever. However, the
    # blocked_connection_timeout connection parameter would interrupt the wait,
    # resulting in ConnectionClosed exception from BlockingConnection (or the
    # on_connection_closed callback call in an asynchronous adapter)
    conn.close()


if __name__ == '__main__':
    main()