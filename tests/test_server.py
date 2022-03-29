import sys
import os
sys.path.append(os.getcwd())

from unittest import TestCase, main
from server import Server


class TestServer(TestCase):
    err_msg = {
        "response": 400,
        "alert": "Wrong message format!"
    }
    ok_msg = {
        "response": 200,
        "time": '11111'
    }
    
    def test_build_response_correct(self):
        message = {
            "action": "presence",
            "time": '123',
            "type": "status",
            "user": {
                "account_name": "Guest",
                "status": "status"
            }
        }
        
        response = Server.build_response(message)
        response['time'] = '11111'
        
        self.assertEqual(response, self.ok_msg)
    
    def test_build_response_failure(self):
        message = {
            "action": "wrong action",
            "time": '123',
            "type": "status",
            "user": {
                "account_name": "Guest",
                "status": "status"
            }
        }
        
        response = Server.build_response(message)
        
        self.assertEqual(response, self.err_msg)
        

if __name__ == '__main__':
    main()