import logging
import os
import re
from typing import Union
from time import sleep


def catch_exception_sleep(timeout, retry = 100):
    def decorator(function):
        def wrapper(*args, **kwargs):
            retries = 0
            while True:
                retries += 1
                try:
                    value = function(*args, **kwargs)
                    return value
                except Exception as e:
                    logging.warning(f'Excepetion occurred: {e}')
                    if retries == retry:
                        logging.debug('Retries limit achieved. Stopping')
                        return None
                    logging.debug(f'Sleeping for {timeout} seconds before retry..')
                    sleep(timeout)
        return wrapper
    return decorator


def get_parent_directory(filepath: str, levels: int = 0) -> str:
    '''
    Returns the real absolute path that is levels up from the filepath passed in.

        Parameters:
            filepath (str): The absolute or relative filepath for which to query the parent directory.
            levels (int): How many levels to discard from the returned path.

        Returns:
            dirname (str): The absolute path
    '''

    if levels == 0:
        return os.path.dirname(os.path.realpath(filepath))

    return get_parent_directory(os.path.dirname(os.path.realpath(filepath)), levels-1)


def urlify(url: str, port: Union[int, str], path: str = "") -> str:
    i = url.find('://')

    if i == -1:
        protocol = ''
    else:
        protocol = url[:i+3]
        url = url[i+3:]

    if ":" in url:
        # Assume IPv6 if colon in url
        url = f'[{url}]'

    if len(protocol) > 0:
        url = f'{protocol}{url}'

    return f'{url}:{port}/{path}'

def parse_addr_and_port_from_url(url: str) -> dict:
    full_url = url
    url = url.strip()

    url = re.sub('^(ws://|wss://|http://|https://)', '', url)

    if len(url) == 0:
        raise ValueError(f'Url `{full_url}` could not be parsed.')

    elif url[-1] == '/':
        url = url[:-1]

    i = url.rfind(':')
    if i == -1:
        raise ValueError(f'Url `{full_url}` could not be parsed. The port is missing.')

    port = url[i+1:]
    url = url[:i]

    i = port.find('/')
    if i != -1:
        logging.info(f'Dropping path `{port[i:]}` part from the url `{full_url}`.')
        port = port[:i]

    if len(url[i+1:]) == 0:
        raise ValueError(f'Url `{full_url}` could not be parsed. The port is missing.')

    try:
        port = int(port)
    except:
        raise ValueError(f'Url `{full_url}` could not be parsed. The port must be a number.')

    return {
        'address': url,
        'clientport': port
    }
