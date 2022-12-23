#!/usr/bin/env python3
# This app has been tested with python 3.8.10

import logging
from tkinter import Tk

from util.helpers import urlify
from ui.gui import App
from services.rest_client import RESTClient
from services.websocket import WebsocketClient
from logic.message_handler import MessageHandler


def initialize() -> tuple:
    # Logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    formatConfig = '[%(asctime)s] [%(levelname)s] %(filename)s:%(lineno)d: %(message)s'

    logging.basicConfig(
        level=logging.DEBUG,
        format=formatConfig
    )

    node_srv_endpoints = RESTClient.get(urlify(
        'http://localhost',
        '8080',
        'api/clients'
    ))

    if node_srv_endpoints is None:
        logging.info('Discovery node unreachable, exiting')
        return None, None

    endpoints_all = node_srv_endpoints['activeNodes']

    if len(endpoints_all) == 0:
        logging.info('Discovery node failed to suggest node-server WS endpoint, exiting')
        return None, None

    thread_msg_handler = MessageHandler()
    #WebsocketClient.Msg_handler = thread_msg_handler.handle_incoming

    ns_endp = endpoints_all[0] # TODO: Iterate and try all suggestions if unable to connect
    thread_wsclient    = WebsocketClient(
        f'ws://{urlify(*ns_endp.values())}',
        thread_msg_handler.handle_incoming
    )
    MessageHandler.Websocket_msg_sender = thread_wsclient.send_message

    logging.info('dsatter CLIENT initialized')

    return thread_wsclient, thread_msg_handler


def main() -> None:
    thread_wsclient, thread_msg_handler = initialize()

    if thread_wsclient is None or thread_msg_handler is None:
        return

    root = Tk()

    # TODO: Only pass the needed functions to App (instead of full objects)
    app = App('dsatter Chat Client', thread_msg_handler.handle_new_client_message, (1024, 1024), root)

    thread_msg_handler.on_message_event = app.refresh_msgs
    thread_msg_handler.start()

    thread_wsclient.start()

    app.mainloop()

    thread_msg_handler.terminate()
    thread_wsclient.terminate()

    thread_wsclient.join()
    thread_msg_handler.join()


if __name__ == '__main__':
    main()
