from base import Base
import json
from common.variables import ACTIONS, MAX_CONNECTIONS, DEFAULT_PORT, ENCODING
from common.utils import convert_to_dict
import argparse
import asyncio
from threading import Thread, Lock


CLIENTS = {}


class Server(Base):
    def __init__(self, connection_port, connection_address):
        super().__init__()
        self.connection_port = connection_port
        self.connection_address = connection_address
        self.message_processor = None
        
    async def run_server(self):
        runner = await asyncio.start_server(self.process_client, self.connection_address, self.connection_port)
        await runner.serve_forever()
        
    async def process_client(self, reader, writer):
        if self.message_processor is None:
            self.message_processor = MessageProcessor(self)
            self.message_processor.start()
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
        message = await reader.read(1000)
        return message
        
        


class MessageProcessor(Thread):
    def __init__(self, server):
        super().__init__()
        self.daemon = True
        self.server = server
        self.message_queue = []
        self.message_sender = None
    
    def run(self):
        if self.message_sender is None:
            self.message_sender = MessageSender()
            self.message_sender.start()
        while True:
            try:
                data = self.message_queue.pop(0)
                data['message'] = convert_to_dict(data['message'])
            except:
                pass
            else:
                self.parse_message(data)
    
    def parse_message(self, data):
        message = data['message']
        if message["action"] == 'presence' and message["time"]:
            CLIENTS[message['user']['account_name']] = (data['reader'], data['writer'])
            self.message_sender.messages_to_send.append({'response': 200, 
                                                         'destination': data['writer'], 
                                                         'action': 'initial'})
            return

        if message['action'] == 'msg' and message['time'] and message['account_name'] \
            and message['message_text'] and message['destination']:
            self.message_sender.messages_to_send.append(message)
            return 

        self.message_sender.messages_to_send.append({"response": 400, 
                                                     "alert": "Wrong message format!",
                                                     'destination': data['writer'],
                                                     'action': 'error'})
        return
        

class MessageSender(Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
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
        
        
        if message['action'] == 'initial' or message['action'] == 'error':
            transport = message['destination'].get_extra_info('socket')
            del message['destination']
            
            message = json.dumps(message).encode(ENCODING)
            try:
                transport.send(message)
            except:
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
        
        
        
        
if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    arg_parser.add_argument('-a', default='127.0.0.1', nargs='?')
    namespace = arg_parser.parse_args()
    
    server = Server(namespace.p, namespace.a)
    asyncio.run(server.run_server())