import json
from common.variables import ENCODING
import socket
import os

def convert_to_dict(message):
    if isinstance(message, bytes):
        decoded_message = message.decode(ENCODING)
        json_message = json.loads(decoded_message)
        if isinstance(json_message, dict):
            return json_message
        else:
            raise ValueError
    raise ValueError
    

def send_message(destination:socket.socket, message):
    if isinstance(message, dict):
        message_srt = json.dumps(message)
        message_bytes = message_srt.encode(ENCODING)
        destination.send(message_bytes)
    else:
        raise ValueError
   
def suppress_qt_warnings():
    os.environ["QT_DEVICE_PIXEL_RATIO"] = "0"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"
   
    
if __name__ == '__main__':
    pass