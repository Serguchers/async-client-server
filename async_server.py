import argparse
import asyncio
import json
from threading import Lock, Thread

from base import Base
from common.utils import convert_to_dict
from common.variables import ACTIONS, DEFAULT_PORT, ENCODING, MAX_CONNECTIONS
from serverstorage import ServerStorage

CLIENTS = {}


class Server:
    def __init__(self, connection_port, connection_address):
        """
        Server initalizator. Starts message processor and message sender subprocesses.
        Args:
            connection_port (int): connection port
            connection_address (str): connection address
        """        
        self.connection_port = connection_port
        self.connection_address = connection_address
        self.server_storage = ServerStorage()
        self.message_processor = MessageProcessor(self)
        self.message_processor.start()
        self.message_sender = MessageSender(self)
        self.message_sender.start()
        
    async def run_server(self):
        """
        Main runner, starts serving clients.
        """
        runner = await asyncio.start_server(self.process_client, self.connection_address, self.connection_port)
        await runner.serve_forever()
        
    async def process_client(self, reader, writer):
        """
        Accepts data from client. 
        Send client message to message processor.
        Args:
            reader : asycnio reader obj
            writer : asyncio writer obj
        """
        while True:
            try:
                message = await self.process_client_message(reader)
            except ConnectionResetError:
                to_remove = tuple(filter(lambda x: x[1] == (reader, writer), CLIENTS.items()))
                del CLIENTS[to_remove[0][0]]
                break
                
            self.message_processor.message_queue.append({'message': message,
                                                         'reader': reader,
                                                         'writer': writer})

                  
    async def process_client_message(self, reader, delimiter=b'\n'):
        """
        Read client message.
        Args:
            reader : asycnio reader obj
            delimiter (bytes, optional): stops reading at delimiter

        Returns:
            bytes: encoded message
        """
        message = await reader.read(1000)
        return message
        
        


class MessageProcessor(Thread):
    def __init__(self, server):
        """
        Processes messages. Message sorting with further transfer to MessageSender.
        Args:
            server (Server): server object
        """
        super().__init__()
        self.daemon = True
        self.server = server
        self.storage = server.server_storage
        self.message_queue = []
        self.message_sender = None
    
    def run(self):
        while True:
            try:
                data = self.message_queue.pop(0)
                data['message'] = convert_to_dict(data['message'])
            except:
                pass
            else:
                self.parse_message(data)
    
    def parse_message(self, data):
        """
        Check message action and message format.
        Args:
            data (dict): usefull data related to message
        """
        message = data['message']
        if message["action"] == 'presence' and message["time"]:
            CLIENTS[message['user']['account_name']] = (data['reader'], data['writer'])
            self.server.message_sender.messages_to_send.append({'response': 200,
                                                                'sender': message['user']['account_name'],
                                                                'destination': data['writer'], 
                                                                'action': 'initial'})
            user_ip, user_port = data['writer'].get_extra_info('peername')
            self.storage.login_user(message['user']['account_name'], user_ip, user_port)

        elif message['action'] == 'msg' and message['time'] and message['account_name'] \
            and message['message_text'] and message['destination']:
            self.storage.write_statistics(message['account_name'], 'sent')
            self.storage.write_statistics(message['account_name'], 'accepted')
            self.server.message_sender.messages_to_send.append(message)
        
        elif message['action'] == 'add_contact' and message['account_name'] and message['destination']:
            try:
                self.storage.add_contact(message['account_name'], message['destination'])
            except:
                self.server.message_sender.messages_to_send.append({'response': 400,
                                                                    'sender': message['account_name'],
                                                                    'action': 'add_contact',
                                                                    'contact': message['destination'],
                                                                    'status': 'failed'})
            else:
               self.server.message_sender.messages_to_send.append({'response': 200,
                                                                    'sender': message['account_name'],
                                                                    'action': 'add_contact',
                                                                    'contact': message['destination'],
                                                                    'status': 'success'}) 
        elif message['action'] == 'del_contact' and message['account_name'] and message['destination']:
            try:
                self.storage.del_contact(message['account_name'], message['destination'])
            except:
                self.server.message_sender.messages_to_send.append({'response': 400,
                                                                    'sender': message['account_name'],
                                                                    'action': 'del_contact',
                                                                    'contact': message['destination'],
                                                                    'status': 'failed'})
            else:
               self.server.message_sender.messages_to_send.append({'response': 200,
                                                                    'sender': message['account_name'],
                                                                    'action': 'del_contact',
                                                                    'contact': message['destination'],
                                                                    'status': 'success'}) 
        elif message['action'] == 'get_contacts' and message['account_name']:
            try:
                contacts = self.storage.get_users_contacts(message['account_name'])
            except:
                pass
            else:
                self.server.message_sender.messages_to_send.append({'response': 200,
                                                                    'destination': message['account_name'],
                                                                    'action': 'get_contacts',
                                                                    'contacts': contacts,
                                                                    'status': 'success'}) 

        else:
            self.server.message_sender.messages_to_send.append({"response": 400, 
                                                                "alert": "Wrong message format!",
                                                                'destination': data['writer'],
                                                                'action': 'error'})
        return
        

class MessageSender(Thread):
    def __init__(self, server):
        """
        Object responsible for sending message to destination.
        """
        super().__init__()
        self.daemon = True
        self.storage = server.server_storage
        self.messages_to_send = []
    
    def run(self):
        while True:
            try:
                message = self.messages_to_send.pop(0)
            except:
                pass
            else:
                self.send_message(message)
        
    def send_message(self, message):
        """
        If message is error or initial send back to owner.
        If message is sent to someone, send to destination.

        Args:
            message (dict): data related to message
        """
        
        if message['action'] == 'initial' or message['action'] == 'error':
            transport = message['destination'].get_extra_info('socket')
            del message['destination']
            
            message = json.dumps(message).encode(ENCODING)
            try:
                transport.send(message)
            except:
                self.storage.logout_user(message['sender'])
                return
            return
        
        if message['action'] == 'msg':
            try:
                transport = CLIENTS[message['destination']][1].get_extra_info('socket')
            except:
                return
            
            message = json.dumps(message).encode(ENCODING)
            transport.send(message)
            return
        
        if message['action'] == 'add_contact':
            try:
                transport = CLIENTS[message['sender']][1].get_extra_info('socket')
            except:
                return
            
            message = json.dumps(message).encode(ENCODING)
            transport.send(message)
            return
        
        if message['action'] == 'del_contact':
            try:
                transport = CLIENTS[message['sender']][1].get_extra_info('socket')
            except:
                return
            
            message = json.dumps(message).encode(ENCODING)
            transport.send(message)
            return

        if message['action'] == 'get_contacts':
            try:
                transport = CLIENTS[message['destination']][1].get_extra_info('socket')
            except:
                return
            
            message = json.dumps(message).encode(ENCODING)
            transport.send(message)
            return
        
        
        
        
if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    arg_parser.add_argument('-a', default='127.0.0.1', nargs='?')
    namespace = arg_parser.parse_args()
    
    server = Server(namespace.p, namespace.a)
    asyncio.run(server.run_server())
