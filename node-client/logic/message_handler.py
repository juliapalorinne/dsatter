import logging
import threading
import queue
import datetime
import json
from state.status import Status
from typing import List, Union


class Message:
    def __init__(self, message: dict) -> 'Message':
        missing_fields = self.__validate_fields(message)
        if len(missing_fields) > 0:
            raise ValueError("Required fields: '" + "', '".join(missing_fields) + "' are missing from the new message")

        self.__message = self.__parse_message(message)
        if len(self.__message.keys()) == 0:
            raise ValueError('Error while parsing the new message')


    @property
    def message(self) -> dict:
        return self.__message


    def __lt__(self, other: 'Message') -> bool:
        return self.__message['dateTime'] < other.__message['dateTime']


    def __parse_message(self, message: dict) -> dict:
        parsed_msg = message
        error = False

        if not isinstance(parsed_msg['messageId'], str):
            logging.warning('parsing new message, messageId is not of type str')
            error = True
        else: # NOTE: This hack can be removed when the node-server is fixed to return messageId as ints
            try:
                parsed_msg['messageId'] = int(parsed_msg['messageId'])
            except Exception as err:
                logging.warning('parsing new message, messageId cannot be casted to int')
                error = True
        if not isinstance(parsed_msg['text'], str):
            logging.warning('parsing new message, text is not of type str')
            error = True
        if not isinstance(parsed_msg['dateTime'], str):
            logging.warning('parsing new message, dateTime is not of type str')
            error = True
        else:
            try:
                parsed_msg['dateTime'] = datetime.datetime.strptime(
                    f'{parsed_msg["dateTime"]}+0000',
                    '%Y-%m-%dT%H:%M:%S.%fZ%z'
                )
            except Exception as err:
                logging.warning(f'Parsing new message, dateTime has invalid format: {err}')
                error = True
        if not isinstance(parsed_msg['sender'], str):
            logging.warning('parsing new message, sender is not of type str')
            error = True

        if not isinstance(parsed_msg['chatId'], int):
            logging.warning('Parsing new message, chatId is not of type int')
            error = True

        return parsed_msg if not error else {}


    def __validate_fields(self, message: dict) -> List[str]:
        fields_expected = ['messageId', 'text', 'dateTime', 'sender', 'chatId']
        # TODO: Check that no additional fields are set (?)
        # TODO: nodeId, id <- fields should be deleted in node-server before broadcasting msg to client

        fields_missing = []

        for f in fields_expected:
            if not f in message.keys():
                fields_missing.append(f)

        return fields_missing


    def __str__(self) -> str:
        return 'Message:\n' + '\n'.join([f'{k}: {v}' for k,v in self.__message.items()])


class MessageHandler(threading.Thread):
    '''
    A class that extends the threading.Thread class. The thread is NOT run
    as a daemon.
    '''


    def __init__(self) -> 'MessageHandler':
        super().__init__()

        # Map different message types to handlers. Intentionally crashes if a message with
        # a unsupported type is received. TODO: log or otherwise handle these message types!
        self.__MSG_TYPES = {
            'clientSyncRequest': None,
            'clientSyncReply': None,
            'newMessageFromClient': None,
            'newMessagesForClient': self.__handle_incoming_new_client_msg,
            'clientMessageResponse': lambda added: print('RESPONSE (added):', added)
        }

        self.__message_queue = queue.Queue()
        self.__on_msg_ui_cb: callable = None
        self.__msg_sender_cb: callable = None
        self.__continue = True


    @property
    def on_msg_ui_cb(self) -> Union[callable, None]:
        return self.__on_msg_ui_cb


    @on_msg_ui_cb.setter
    def on_msg_ui_cb(self, cb: Union[callable, None]) -> None:
        self.__on_msg_ui_cb = cb


    @property
    def msg_sender_cb(self) -> Union[callable, None]:
        return self.__msg_sender_cb


    @msg_sender_cb.setter
    def msg_sender_cb(self, cb: Union[callable, None]) -> None:
        self.__msg_sender_cb = cb


    def run(self) -> None:
        '''
        This method is called by threading.Thread.start method.
        The 'main' function of the thread.
        '''

        logging.debug('Message handler thread started')

        while self.__continue:
            self.__purge_messages()

        logging.debug('Message handler thread stopping')


    def stop(self) -> None:
        self.__message_queue.put(None, block=False)
        self.__on_msg_ui_cb = None
        self.__msg_sender_cb = None


    def handle_new_client_message(self, message: str) -> None:
        # TODO: Use queue for outgoing messages, keep messages in queue until ACK is received

        if len(message) == 0:
            return

        msg = {
            'type': 'newMessageFromClient',
            'payload': {
                'text': message,
                'sender': Status.get_username(),
                'chatId': 11
            }
        }

        if self.msg_sender_cb is None:
            logging.info('WS message sender not installed, discarding new message')
            return

        self.msg_sender_cb(json.dumps(msg))


    def handle_incoming(self, message: str) -> None:
        try:
            msg = json.loads(message)
        except Exception as err:
            logging.error(err)
            logging.error(f'RECEIVED malformed message: {message}, ignoring')
            return

        if not ('type' in msg and 'payload' in msg):
            logging.error(f'RECEIVED incomplete message: {msg}, ignoring')
            return

        if msg['type'] in self.__MSG_TYPES.keys():
            for m in msg['payload']:
                self.__MSG_TYPES[msg['type']](m)
        else:
            logging.info(f'RECEIVED unknown message type, ignoring: {msg}')


    def __handle_incoming_new_client_msg(self, message: dict):
        try:
            msg = Message(message)
        except Exception as err:
            logging.warning(f'Error when handling incoming message: {err}')
            return

        try:
            self.__message_queue.put(msg, block=False)
        except queue.Full as e:
            logging.error(f'Messages queue is full, discarding new message: {e}')
        except Exception as e:
            logging.error(f'Exception happened when attempting to add message to the queue: {e}')


    def __purge_messages(self) -> None:
        msg = self.__message_queue.get()
        self.__message_queue.task_done()

        if msg is None:
            self.__continue = False
            return

        messages = [msg.message]

        while not self.__message_queue.empty() and len(messages) < 50:
            msg = self.__message_queue.get()
            self.__message_queue.task_done()

            if msg is None:
                self.__continue = False
                break

            messages.append(msg.message)

        if self.on_msg_ui_cb is None:
            logging.warning('GUI updating failed, no handler installed. Message(s) are discarded')
        else:
            self.on_msg_ui_cb(messages)
