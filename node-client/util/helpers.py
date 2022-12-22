import logging
import os
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
