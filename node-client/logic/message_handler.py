import logging
import threading
import queue
import datetime
import json
from state.status import Status
from typing import Union, List


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
                    parsed_msg['dateTime'],
                    '%Y-%m-%dT%H:%M:%S.%fZ'
                )
            except Exception as err:
                logging.warning('Parsing new message, dateTime has invalid format:', err)
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

    Websocket_msg_sender = None

    def __init__(self) -> 'MessageHandler':
        super().__init__()

        self.__MSG_TYPES = {
        'clientSyncRequest': None,
        'clientSyncReply': None,
        'newMessageFromClient': None,
        'newMessagesForClient': self.__handle_new_msg,
        'clientMessageResponse': lambda added: print('RESPONSE (added):', added)
        }

        self.__message_queue = queue.Queue()
        self.__on_message_event: callable = None
        self.__continue = True


    def handle_new_client_message(self, message: str):
        # TODO: Use queue for outgoing messages

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

        if MessageHandler.Websocket_msg_sender is None:
            logging.info('WS message sender not installed, discarding new message')
            return

        MessageHandler.Websocket_msg_sender(json.dumps(msg))


    def handle_incoming(self, message: str) -> None:
        try:
            msg = json.loads(message)
        except Exception as err:
            logging.error(err)
            logging.error('Discarding incoming message')
            return

        if not ('type' in msg and 'payload' in msg):
            logging.error('Received incomplete message:', msg)
            return

        if msg['type'] in self.__MSG_TYPES:
            for m in msg['payload']:
                self.__MSG_TYPES[msg['type']](m)
        else:
            logging.info(f'RECEIVED unknown message type, ignoring: {msg}')


    def __handle_new_msg(self, message: dict):
        try:
            msg = Message(message)
        except Exception as err:
            logging.warning(f'Error when handling incoming message: {err}')

        # TODO: Use try/except to catch case if queue is full
        self.__message_queue.put(msg, block=False)


    @property
    def on_message_event(self) -> callable:
        return self.__on_message_event


    @on_message_event.setter
    def on_message_event(self, func: callable) -> None:
        logging.debug('Message handler installed')
        self.__on_message_event = func


    def run(self) -> None:
        '''
        This method is called by threading.Thread.start method.
        The 'main' function of the thread.
        '''

        logging.debug('Message handler thread initialized')

        while self.__continue:
            self.__continue = self.handle_message_event()

        logging.debug('Message handler thread stopping')


    def terminate(self) -> None:
        self.__message_queue.put(None, block=False)
#    def create_message(self, message: Union[str, None]) -> None:
#        '''
#        Append a new message to the queue. This thread will stop
#        if message is None. This function never blocks, only logs
#        error messages if there is any exceptions when attempting to
#        add messages to the queue.
#        '''
#
#        if message is not None:
#            logging.debug(f'Creating message: {message}')
#            if len(message) == 0:
#                return
#
#            ordered_msg = OrderedMessage({
#                'id': uuid.uuid4(),
#                'timestamp': datetime.datetime.now(),
#                'sender': 'Test Tester',
#                'message': message
#            })
#
#            logging.debug(f'ordered message: {ordered_msg.message["message"]}')
#
#        try:
#            self.__message_queue.put(
#                ordered_msg if message is not None else None,
#                block=False
#            )
#        except queue.Full as e:
#            logging.error('Messages queue is full, not handeled:', e)
#        except Exception as e:
#            logging.error('Exception happened when attempting to add message to the queue: ', e)


    def handle_message_event(self) -> bool:
        msg = self.__message_queue.get()
        if msg is None:
            return False


        #self.__messages.put(msg)

        # NOTE: Python priority queues are implemented as binary heap data structure,
        #       so printing the raw elements in the internal queue does not follow the
        #       ordering in the priority queue.
        #logging.debug(f'messages {[ m.message for m in self.__messages.queue ]}')

        if self.__on_message_event is None:
            return

        self.__on_message_event([ msg.message ])

        return True
