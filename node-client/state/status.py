from threading import Lock
from typing    import Union

class Status:

    __username = 'Anonymous'
    __username_lock = Lock()

    __ws_connection = None
    __ws_connection_lock = Lock()

    __update_gui_cb: callable = None
    __update_gui_cb_lock = Lock()


    @classmethod
    def get_username(cls) -> str:
        return cls.__username


    @classmethod
    def set_username(cls, username: str) -> bool:
        if not isinstance(username, str) or len(username) < 4:
            return False

        cls.__username_lock.acquire()
        cls.__username = username
        cls.__username_lock.release()
        cls.update_gui()

        return True


    @classmethod
    def get_ws_connection(cls) -> str:
        return cls.__ws_connection


    @classmethod
    def set_ws_connection(cls, address: Union[str, None]) -> None:
        cls.__ws_connection_lock.acquire()
        cls.__ws_connection = address
        cls.__ws_connection_lock.release()
        cls.update_gui()


    @classmethod
    def is_connected(cls) -> bool:
        return cls.get_ws_connection() != None


    @classmethod
    def set_update_gui_cb(cls, callback: callable) -> None:
        cls.__update_gui_cb_lock.acquire()
        cls.__update_gui_cb = callback
        cls.__update_gui_cb_lock.release()


    @classmethod
    def update_gui(cls) -> None:
        cls.__update_gui_cb_lock.acquire()
        if cls.__update_gui_cb is not None:
            cls.__update_gui_cb(cls.get_username(), cls.get_ws_connection())
        cls.__update_gui_cb_lock.release()


if __name__ == '__main__':
    print('Name:', Status.get_username())
    Status.set_username('abc')
    print('Name:', Status.get_username())
    Status.set_username('John Does')
    print('Name:', Status.get_username())
