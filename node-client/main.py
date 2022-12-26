#!/usr/bin/env python3
# This app has been tested with python 3.8.10

import argparse
import logging
from time import sleep
from tkinter import Tk
from typing import Union, Tuple

from util.helpers import urlify, parse_addr_and_port_from_url
from state.status import load_config, save_config, Settings

from ui.gui import App
from services.rest_client import RESTClient
from services.websocket import WebsocketClient
from logic.message_handler import MessageHandler

CONFIG_FILEPATH = 'config.ini'


def parse_args() -> Tuple[Union[str, None], bool]:
    desc = ' '.join((
        'Chat client for DSatter.',
        'If the client is run without the optional -s or -d arguments,',
        'then it will attempt to query the discovery service for node-servers using the same url as on the previous time it was run.',
        'Creates a config.ini file, where it saves the settings. Delete this file to use default values.',
        'This app has been developed and tested using python 3.8.10.'
    ))

    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-lv', '--log-verbose',
        help='Enable verbose (debug) logging',
        action='store_true',
        dest='verbose_logging'
    )
    parser.add_argument('-d', '--discovery',
        help=f'Url with port to a running node-discovery server to use. Defaults to `{Settings.get_node_discovery_url()}`',
        default=None,
        dest='node_discovery_url'
    )
    parser.add_argument('-s', '--server',
        help='Url with a port in case you want to connect to a specific node-server. By default queries the discovery service for active node-servers.',
        dest='node_server_url'
    )
    args = parser.parse_args()

    if args.node_discovery_url is not None:
        Settings.set_node_discovery_full_url(args.node_discovery_url)

    return args.node_server_url, args.verbose_logging


def initialize(
    node_server_url: Union[str, None],
    verbose_logging: bool
) -> Tuple[Union[WebsocketClient, None], Union[MessageHandler, None]]:

    # Logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    if verbose_logging:
        formatConfig = '[%(asctime)s] [%(threadName)-10s] [%(levelname)-8s] %(filename)s:%(lineno)d:\n %(message)s'
    else:
        formatConfig = '%(message)s'

    logging.basicConfig(
        level=logging.DEBUG if verbose_logging else logging.INFO,
        format=formatConfig
    )

    if node_server_url is None:
        node_srv_endpoints = RESTClient.get(Settings.get_node_discovery_url())
        if node_srv_endpoints is None:
            logging.info('Discovery node unreachable, exiting')
            return None, None

        if not 'activeNodes' in node_srv_endpoints.keys() \
           or len(node_srv_endpoints['activeNodes']) == 0:
            logging.info('Discovery node failed to suggest node-server WS endpoint, exiting')
            return None, None

        node_srv_endpoints = node_srv_endpoints['activeNodes']
    else:
        try:
            serv_endpoint = parse_addr_and_port_from_url(node_server_url)
        except Exception as e:
            logging.info(f'{e}, exiting')
            return None, None
        node_srv_endpoints = [ serv_endpoint ]


    thread_msg_handler = MessageHandler()

    i = 0
    while True:
        ns_endp = f'ws://{urlify(*node_srv_endpoints[i].values())}'
        logging.info(f'Attempting to open a WS connection to a node-server at url `{ns_endp}`')

        thread_wsclient = WebsocketClient(ns_endp, thread_msg_handler.handle_incoming)
        thread_wsclient.start()

        while not thread_wsclient.is_connected and not thread_wsclient.connection_error:
            logging.info('Waiting for connection establishment..')
            sleep(.5)

        if not thread_wsclient.connection_error:
            logging.info(f'Connected to node-server at url `{ns_endp}`')
            break

        logging.info(f'Connection attempt to node-server at url: `{ns_endp}` failed')
        thread_wsclient.stop()

        i = (i+1) % len(node_srv_endpoints)
        if i == 0:
            logging.info('Could not open a connection to any node-server, exiting')
            return None, None

    thread_msg_handler.msg_sender_cb = thread_wsclient.send_message

    thread_msg_handler.start()

    return thread_wsclient, thread_msg_handler


def main(thread_wsclient: WebsocketClient, thread_msg_handler: MessageHandler) -> None:
    root = Tk()

    app = App('DSatter Chat Client', thread_msg_handler.handle_new_client_message, (1024, 1024), root)

    thread_msg_handler.on_msg_ui_cb = app.append_msgs

    app.mainloop()

    thread_msg_handler.stop()
    thread_wsclient.stop()

    thread_wsclient.join()
    thread_msg_handler.join()


if __name__ == '__main__':
    load_config(CONFIG_FILEPATH)

    node_server_url, verbose_logging = parse_args()
    thread_wsclient, thread_msg_handler = initialize(node_server_url, verbose_logging)

    if thread_wsclient is not None and thread_msg_handler is not None:
        logging.info('DSatter chat client initialized')
        main(thread_wsclient, thread_msg_handler)
        logging.info('DSatter chat client shutting down')

        save_config(CONFIG_FILEPATH)
