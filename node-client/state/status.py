import configparser

from threading import Lock
from random    import randrange
from typing    import Union

from util.helpers import urlify, parse_full_url


__DEFAULT_CONFIG = {
    'DISCOVERY': {
        'host': 'http://localhost',
        'port': '8080',
        'path': 'api/clients'
    },
    'USER': {
        'username': f'USER-{randrange(10**4, 10**5)}'
    }
}

__CONFIG = configparser.ConfigParser()
__CONFIG.read_dict(__DEFAULT_CONFIG)


class Settings:

    __node_discovery_addr = None
    __node_discovery_port = None
    __node_discovery_path = None


    @staticmethod
    def get_node_discovery_url() -> str:
        return urlify(
            Settings.__node_discovery_addr,
            Settings.__node_discovery_port,
            Settings.__node_discovery_path
        )


    @staticmethod
    def set_node_discovery_url(host: str, port: Union[str, int], path: str) -> None:
        Settings.__node_discovery_addr = host
        Settings.__node_discovery_port = port
        Settings.__node_discovery_path = path


    staticmethod
    def set_node_discovery_full_url(full_url: str) -> None:
        url_parsed = parse_full_url(full_url)

        Settings.__node_discovery_addr = f'http://{url_parsed["host"]}'
        Settings.__node_discovery_port = url_parsed['port']
        Settings.__node_discovery_path = url_parsed['path']


    staticmethod
    def get_node_discovery_addr() -> Union[str, None]:
        return Settings.__node_discovery_addr


    staticmethod
    def get_node_discovery_port() -> Union[str, None]:
        return Settings.__node_discovery_port


    staticmethod
    def get_node_discovery_path() -> Union[str, None]:
        return Settings.__node_discovery_path


class Status:

    __username = None
    __username_lock = Lock()

    __ws_connection = None
    __ws_connection_lock = Lock()

    __update_gui_cb: callable = None
    __update_gui_cb_lock = Lock()


    @staticmethod
    def get_username() -> str:
        return Status.__username


    @staticmethod
    def set_username(username: str) -> bool:
        if not isinstance(username, str) or len(username) < 4:
            return False

        Status.__username_lock.acquire()
        Status.__username = username
        Status.__username_lock.release()
        Status.update_gui()

        return True


    @staticmethod
    def get_ws_connection() -> str:
        return Status.__ws_connection


    @staticmethod
    def set_ws_connection(address: Union[str, None]) -> None:
        Status.__ws_connection_lock.acquire()
        Status.__ws_connection = address
        Status.__ws_connection_lock.release()
        Status.update_gui()


    @staticmethod
    def is_connected() -> bool:
        return Status.get_ws_connection() != None


    @staticmethod
    def set_update_gui_cb(callback: Union[callable, None]) -> None:
        Status.__update_gui_cb_lock.acquire()
        Status.__update_gui_cb = callback
        Status.__update_gui_cb_lock.release()


    @staticmethod
    def update_gui() -> None:
        Status.__update_gui_cb_lock.acquire()
        if Status.__update_gui_cb is not None:
            Status.__update_gui_cb(Status.get_username(), Status.get_ws_connection())
        Status.__update_gui_cb_lock.release()


def load_config(filepath: str) -> None:
    __CONFIG.read(filepath)
    Settings.set_node_discovery_url(
        __CONFIG['DISCOVERY']['host'],
        __CONFIG['DISCOVERY']['port'],
        __CONFIG['DISCOVERY']['path']
    )

    Status.set_username(__CONFIG['USER']['username'])


def save_config(filepath: str) -> None:
    __CONFIG['DISCOVERY']['host'] = Settings.get_node_discovery_addr()
    __CONFIG['DISCOVERY']['port'] = Settings.get_node_discovery_port()
    __CONFIG['DISCOVERY']['path'] = Settings.get_node_discovery_path()

    __CONFIG['USER']['username'] = Status.get_username()

    with open(filepath, 'w') as configfile:
        __CONFIG.write(configfile)
