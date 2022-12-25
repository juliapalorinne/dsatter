from threading import Lock
from typing    import Union

from util.helpers import urlify


class Settings:

    __node_discovery_url = urlify('http://localhost', '8080', 'api/clients')

    @staticmethod
    def get_node_discovery_url() -> str:
        return Settings.__node_discovery_url


class Status:

    __username = 'Anonymous'
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
