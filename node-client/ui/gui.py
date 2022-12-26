import logging
import tkinter as tk

from datetime           import datetime
from tkinter            import ttk
from tkinter.messagebox import showwarning
from typing             import Tuple, Union

from state.status import Status


class GridFrame(ttk.Frame):
    def __init__(self, master, grid_row, grid_column, grid_columnspan):
        super().__init__(master)
        self.grid(row=grid_row, column=grid_column, columnspan=grid_columnspan, pady=1, padx=1)


class StatusFrame(GridFrame):

    def __init__(self, master, grid_row, grid_column, grid_columnspan):
        super().__init__(master, grid_row, grid_column, grid_columnspan)

        self.__username_var = tk.StringVar(self, Status.get_username())

        active_conn = Status.get_ws_connection()
        self.__ws_connection_var = tk.StringVar(
            self,
            active_conn if active_conn is not None else 'Disconnected'
        )

        self.__node_label = ttk.Label(self, text='Connected to node:')
        self.__node_label.grid(row=0, column=0, pady=1, padx=1)

        self.__node_info = ttk.Label(self, textvariable=self.__ws_connection_var)
        self.__node_info.grid(row=0, column=1, pady=1, padx=1)

        self.__user_label = ttk.Label(self, text='Username:')
        self.__user_label.grid(row=1, column=0, pady=1, padx=1)

        self.__user_info = ttk.Label(self, textvariable=self.__username_var)
        self.__user_info.grid(row=1, column=1, pady=1, padx=1)

        self.__user_entry_label = ttk.Label(self, text='Username:')
        self.__user_entry_label.grid(row=2, column=0, pady=1, padx=1)

        self.__user_entry = ttk.Entry(self, text=self.__username_var.get())
        self.__user_entry.grid(row=2, column=1, pady=1, padx=1)
        self.__user_entry.bind('<Return>', self.__set_username_handler)

        self.__user_set_btn = ttk.Button(self, text='Set username', command=self.__set_username_handler)
        self.__user_set_btn.grid(row=2, column=2, pady=1, padx=1)

        Status.set_update_gui_cb(self.update_labels)


    def __del__(self) -> None:
        Status.set_update_gui_cb(None)


    def update_labels(self, username: str, connection: Union[str, None]) -> None:
        self.__username_var.set(username)
        self.__ws_connection_var.set(connection if connection is not None else 'Disconnected')


    def __set_username_handler(self, key_event = None) -> None:
        username = self.__user_entry.get()
        if len(username) < 4 or not Status.set_username(username):
            showwarning(
                title=f"Could not set username to '{username}'",
                message='Username must be at least 4 characters long'
            )
            return


class MessagesFrame(GridFrame):

    TIME_STR_F = '%Y-%m-%dT%H:%M:%S.%fZ%z'

    def __init__(self, master, grid_row, grid_column, grid_columnspan):
        super().__init__(master, grid_row, grid_column, grid_columnspan)
        self.__message_ids = set()
        self.__init_view()


    def __init_view(self):
        columns = ('dateTime', 'sender', 'text')
        self.__tree = ttk.Treeview(self, columns=columns, show='headings')
        self.__tree.heading('dateTime', text='Time')
        self.__tree.heading('sender', text='Sender')
        self.__tree.heading('text', text='Message text')
        self.__tree.pack(side=tk.LEFT, fill=tk.BOTH)

        self.__tree.bind('<<TreeviewSelect>>', self.__show_selected)

        self.__scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.__tree.yview)
        self.__tree.configure(yscroll=self.__scrollbar.set)
        self.__scrollbar.pack(side=tk.RIGHT, fill=tk.BOTH)


    def __show_selected(self, event):
        for selected_msg in self.__tree.selection():
            item = self.__tree.item(selected_msg)
            logging.debug(f'\nselected: {selected_msg}')
            logging.debug(f'item: {item}')
            logging.debug('-----\n')


    def __insert_message(self, msg):
        def rendered_msg_ts(iid: str) -> datetime:
            return datetime.strptime(iid.split(' ')[1], MessagesFrame.TIME_STR_F)

        def insert_into_tree(indx: int) -> str:
            return self.__tree.insert(
                parent='',
                index=indx,
                iid=(msg['messageId'], msg['dateTime'].strftime(MessagesFrame.TIME_STR_F)),
                values=(msg['dateTime'].astimezone().strftime('%d.%m %H:%M.%S'), msg['sender'], msg['text'])
            )

        if msg['messageId'] in self.__message_ids:
            logging.info('Message is already rendered. Editing or updating edited messages is not supported')
            return

        children = self.__tree.get_children()

        # Select position for inserting
        if len(children) == 0 or \
           msg['dateTime'] < rendered_msg_ts(children[0]):
            i = 0
        elif msg['dateTime'] >= rendered_msg_ts(children[-1]):
            i = len(children)
        else: # Do binary search to set i to equal the position where all the previous rendered messages
              # timestamps preceeds the msg's timestamp.
            n = len(children)
            i = 0
            j = n
            while True:
                j //= 2
                if j < 1: break
                while i+j < n:
                    if rendered_msg_ts(children[i+j]) <= msg['dateTime']: i += j
                    else: break
            # i points to the last rendered message whos timestamp is less than or equal to the new msgs
            i += 1 # advance i to next pos

        if i > len(children):
            logging.warning('binary search error... message not inserted')
            return
        elif i == len(children):
            i = tk.END
        else:
            i = self.__tree.index(children[i])

        # Update status
        insert_into_tree(i)
        self.__message_ids.add(msg['messageId'])


    def _add_messages(self, msgs):
        for m in msgs:
            self.__insert_message(m)


class MessageEntryFrame(GridFrame):

    def __init__(self, master, grid_row, grid_column, grid_columnspan, new_msg_handler: callable):
        super().__init__(master, grid_row, grid_column, grid_columnspan)

        self.__new_msg_handler = new_msg_handler

        self.__label_msg = ttk.Label(self, text='Message:')
        self.__label_msg.grid(row=0, column=0, pady=1, padx=1)

        self.__entry = ttk.Entry(self, width=56)
        self.__entry.grid(row=0, column=1, pady=1, padx=1)
        self.__entry.insert(0, 'Message..')
        self.__entry.configure(state=tk.DISABLED)
        self.__entry.bind('<Return>', self.__on_new_message)
        self.__entry.bind('<Button-1>', self.__on_entry_click)

        self.__button_send = ttk.Button(self, text='Send', command=self.__on_new_message)
        self.__button_send.grid(row=0, column=2, pady=1, padx=1)


    def __on_entry_click(self, event):
        self.__entry.configure(state=tk.NORMAL)
        self.__entry.delete(0, tk.END)
        self.__entry.unbind('<Button-1>')


    def __on_new_message(self, key_event = None):
        message = self.__entry.get()
        if len(message) == 0:
            return

        if self.__new_msg_handler == None:
            logging.error('MessageEntryFrame: Discarding new message, no handler installed')
            return

        self.__new_msg_handler(message)
        self.__entry.delete(0, len(message))


class App(ttk.Frame):
    def __init__(
            self,
            win_title: str,
            new_client_msg_handler,
            win_maxsize: Tuple[int, int] = (1024, 1024),
            master: tk.Tk = None) -> 'App':
        super().__init__(master)

        self.master.title(win_title)
        self.master.protocol('WM_DELETE_WINDOW', self.__on_quit)
        #self.master.minsize(width, height)
        self.master.maxsize(win_maxsize[0], win_maxsize[1])

        self.__new_client_msg_handler = new_client_msg_handler

        self.pack(pady=1, padx=1)

        self.__init_menu()

        self.__status_frame    = StatusFrame(self, grid_row=0, grid_column=0, grid_columnspan=3)
        self.__messages_frame  = MessagesFrame(self, grid_row=1, grid_column=0, grid_columnspan=3)
        self.__msg_entry_frame = MessageEntryFrame(self, grid_row=2, grid_column=0, grid_columnspan=3, new_msg_handler=self.__new_client_msg_handler)


    def __init_menu(self):
        self.__menu = tk.Menu(self.master)
        self.master.config(menu=self.__menu)

        self.__menuFile = tk.Menu(self.__menu)
        self.__menuFile.add_command(label='Exit', command=self.__on_quit)
        self.__menu.add_cascade(label='File', menu=self.__menuFile)

        self.__menuEdit = tk.Menu(self.__menu)
        self.__menu.add_cascade(label='Edit', menu=self.__menuEdit)


    def __on_quit(self):
        Status.set_update_gui_cb(None)
        self.master.quit()


    def append_msgs(self, messages: list) -> None:
        self.__messages_frame._add_messages(messages)
