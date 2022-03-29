import imp
import socket
import sys
from common.variables import DEFAULT_IP, DEFAULT_PORT, MAX_PACKAGE_LENGTH, ENCODING
import json


class Base:
    def __init__(self):
        pass

    @staticmethod
    def get_message(sender:socket.socket):
        message = sender.recv(MAX_PACKAGE_LENGTH)
        if isinstance(message, bytes):
            decoded_message = message.decode(ENCODING)
            json_message = json.loads(decoded_message)
            if isinstance(json_message, dict):
                return json_message
            else:
                
                raise ValueError
        raise ValueError
        
    @staticmethod
    def send_message(destination:socket.socket, message):
        if isinstance(message, dict):
            message_srt = json.dumps(message)
            message_bytes = message_srt.encode(ENCODING)
            destination.send(message_bytes)
        else:
            raise ValueError
        
    