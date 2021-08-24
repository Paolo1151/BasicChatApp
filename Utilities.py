from collections import deque
from tkinter import *

import threading
import socket
import json


class API:
    '''
    An Interface to show an API. Each API requires a thread.
    '''
    def communication_thread(self):
        pass

    def start_communication(self):
        thread = threading.Thread(target=self.communication_thread)
        thread.start()


class ApplicationFront(Frame, API):
    '''
    Defines the User Interface for the Chat Room
    '''
    def __init__(self, root=None, port=12345):
        root.geometry('400x300')
        root.title('Chat App')

        super().__init__(root)

        self._create_widgets()

        print('Client Launched!')

        self.host = socket.gethostname()
        self.port = port

        self.socket = socket.socket()
        self.socket.connect((self.host, self.port))

        self.lock = threading.Lock()

        self.messages = []

        self.start_communication()

    def _create_message_labels(self, root=None):
        messages = []
        for i in range(10):
            label = Label(root)
            label.pack(side=TOP)
            messages.append(label)
        self.message_labels = messages

    def _create_widgets(self):
        # TODO: Refactor with better fields.
        title = Label(self.master, text='Welcome to my Chat App!')
        title.config(font=('helvetica', 15))
        title.pack(side=TOP)

        self.message_frame = Frame(self.master)
        self._create_message_labels(self.message_frame)
        self.message_frame.pack()

        self.entry = Entry(self.master, width=55)
        self.entry.pack(side=RIGHT, padx=10, pady=10, anchor=S)

        send_button = Button(self.master, text='Send', command=self.chat)
        send_button.pack(side=RIGHT, padx=5, pady=5, anchor=S)

    def send_message(self, message):
        self.capi.send_message(message)

    def update_messages(self):
        for index, message in enumerate(self.messages):
            self.message_labels[index]['text'] = message

    def chat(self):
        self.send_message(self.entry.get())
        self.update_messages()

    '''
    API for the Client. Meant to handle sending requests and handles its own copy of the messages.
    '''
    def send_message(self, message):
        # Asynchronous
        self.socket.send(message.encode())

    def get_messages(self):
        return self.messages

    def receive_messages(self):
        # Synchronous
        # Main Thread 1
        message_list = json.loads(self.socket.recv(1024).decode())
        with self.lock:
            self.messages = message_list
        print(f'Successfully received_messages {self.messages}')

    def communication_thread(self):
        while True:
            self.receive_messages()
            self.update_messages()

    def __del__(self):
        del self.capi


class ClientMain(API):
    '''
    API for the Client. Meant to handle sending requests and handles its own copy of the messages.
    '''
    def __init__(self, port=12345):
        self.host = socket.gethostname()
        self.port = port

        self.socket = socket.socket()
        self.socket.connect((self.host, self.port))

        self.lock = threading.Lock()

        self.messages = []

        self.updated = False

    def send_message(self, message):
        # Asynchronous
        self.socket.send(message.encode())

    def get_messages(self):
        return self.messages

    def is_updated(self):
        return self.updated

    def toggle_updated(self):
        self.updated = not self.updated

    def receive_messages(self):
        # Synchronous
        # Main Thread 1
        message_list = json.loads(self.socket.recv(1024).decode())
        with self.lock:
            self.messages = message_list
            self.updated = True
        print(f'Successfully received_messages {self.messages}')

    def communication_thread(self):
        while True:
            self.receive_messages()


# Maybe make this inherit thread instead and create a new thread class for the client communication thread
class ServerMain(API):
    '''
    API for communication With Server. Accepts Connections and creates a new thread per connection
    '''
    def __init__(self, port=12345):
        self.host = socket.gethostname()
        self.port = port
        self.clients = []
        self.socket = socket.socket()
        self.lock = threading.Lock()
        self.server_messages = Messages()

    # Connection Thread Handler
    def accept_connection(self):
        # Main Thread 3
        while True:
            client_socket, address = self.socket.accept()
            self.register_client(client_socket)
            print(f'Got connection from {address}. There are now {len(self.clients)} clients.')
            self.start_client(client_socket)

    def register_client(self, client_socket):
        with self.lock:
            self.clients.append(client_socket)

    def communication_thread(self):
        self.socket.listen(5)
        self.accept_connection() # Is this too abstracted?

    # Client thread Handler
    def send_messages(self):
        json_messages = json.dumps(self.server_messages.get_messages()).encode()
        for index, client_socket in enumerate(self.clients):
            client_socket.send(json_messages)
            print(f'Sent to Client {index} Messages.')

    def client_communication(self, client_socket):
        # Main Thread 2
        while True:
            message = client_socket.recv(1024).decode()
            self.server_messages.set_messages(message)
            self.server_messages.validate_messages()
            self.send_messages()

    def start_client(self, client_socket):
        thread = threading.Thread(target=self.client_communication, args=(client_socket,), daemon=True)
        thread.start()

    # Server Handler
    def start_server(self):
        print('Starting Server...')
        self.socket.bind((self.host, self.port))
        self.start_communication()
        print('Socket now bound. Server Started.')


class Messages:
    '''
    The Main Data Structure for handling Messages
    '''
    def __init__(self):
        self.messages = deque(maxlen=10)
        self.lock = threading.Lock()

    def get_messages(self):
        return list(self.messages)

    def set_messages(self, message):
        with self.lock:
            self.messages.append(message)

    def validate_messages(self):
        '''
        Only in DEV. Delete in PROD
        '''
        print('The Messages are:')
        for index, message in enumerate(list(self.messages)):
            print(f'Message {index}: {message}')