import logging
import threading
import websocket
from typing import Union
from state.status import Status


# websocket library links
# -----------------------
# Official documentation: https://websocket-client.readthedocs.io/en/latest/index.html
# https://pypi.org/project/websocket-client/


class WebsocketClient(threading.Thread):
    '''
    A class that extends the threading.Thread class. Wraps a weboscket.WebSocketApp instance
    and when the thread is started opens the connection and keeps it open. Thread is NOT run
    as a daemon.
    '''


    def __init__(self, url: str, msg_handler: callable) -> 'WebsocketClient':
        super().__init__()
        self.__incoming_msg__handler = msg_handler
        self.__ws = websocket.WebSocketApp(
            url,
            on_message=self.on_message,
            on_error=WebsocketClient.on_error,
            on_close=WebsocketClient.on_close,
            on_open=WebsocketClient.on_open,
            on_ping=WebsocketClient.on_ping,
            on_pong=WebsocketClient.on_pong
        )


    @property
    def incoming_msg_handler(self) -> Union[callable, None]:
        return self.__incoming_msg__handler


    @incoming_msg_handler.setter
    def incoming_msg_handler(self, cb: callable) -> None:
        self.__incoming_msg__handler = cb


    def run(self) -> None:
        '''
        This method is called by threading.Thread.start method.
        The 'main' function of the thread.
        '''

        logging.debug('WS thread initialized')

        try:
            self.__ws.run_forever(
            # Set client to ping the server at intervals
            #
            #    ping_interval=60,
            #    ping_timeout=10,
            #    ping_payload='CLIENT from addr 123.123.123.123:1010'
            )

        except websocket.WebSocketTimeoutException as e:
            logging.error('WS connection terminated (server did not respond to ping?):', e)
        except Exception as e:
            logging.error('WS Thread caught general exception:', e)
        finally:
            self.__ws.close()

        logging.debug('WS Thread stopping')


    def send_message(self, message: str) -> None:
        if not isinstance(message, str):
            logging.error('WS Attempted to send a message that is of wrong type')
            return

        self.__ws.send(message)


    def terminate(self) -> None:
        logging.debug('WS Thread terminate')
        self.__ws.close()


    def __str__(self):
        t = threading.current_thread()
        return '\n'.join((
            super().__str__(),
            f'name={t.name}, alive={t.is_alive()} daemon={t.daemon}, id={t.ident}'
        ))


    def on_message(self, ws: websocket._app.WebSocketApp, message: str) -> None:
        if self.__incoming_msg__handler == None:
            logging.error('Message handler not installed')
            return

        self.__incoming_msg__handler(message)


    @staticmethod
    def on_error(ws: websocket._app.WebSocketApp, error: websocket._exceptions) -> None:
        # Several different exception types are defined in websocket._exceptions."CLASSNAME"
        logging.error(f'Websocket: {error}')


    @staticmethod
    def on_close(ws: websocket._app.WebSocketApp, status_code, message) -> None:
        # This is where to handle the situation where connection is terminated by the server
        logging.debug(f'Websocket: CLOSE: {status_code} {message}')
        Status.set_ws_connection(None)


    @staticmethod
    def on_open(ws: websocket._app.WebSocketApp) -> None:
        logging.debug(f'Websocket: OPEN')
        Status.set_ws_connection(ws.url)
        ws.send('Client connected')


    @staticmethod
    def on_ping(ws: websocket._app.WebSocketApp, message: str) -> None:
        logging.debug(f'Websocket: PING, message: [[{message}]]. PONG has been sent')


    @staticmethod
    def on_pong(ws: websocket._app.WebSocketApp, message: str) -> None:
        logging.debug(f'Websocket: PONG, message: {message}')
