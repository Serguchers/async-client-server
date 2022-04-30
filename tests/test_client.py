import sys
import os

sys.path.append(os.getcwd())

from unittest import TestCase, main
from client.client import Client


class TestClient(TestCase):
    def test_presernce_message(self):
        presence_message = {
            "action": "presence",
            "time": "123",
            "type": "status",
            "user": {"account_name": "Sergei", "status": "Doing my homework!"},
        }
        client_message = Client.presence_msg()
        client_message["time"] = "123"

        self.assertEqual(client_message, presence_message)

    def test_process_response_success(self):
        response = {"response": 200, "time": "123"}
        self.assertEqual(Client.process_response(response), "SUCCESS")

    def test_process_response_error(self):
        response = {"response": 400, "time": "123"}
        self.assertEqual(Client.process_response(response), "ERROR")


if __name__ == "__main__":
    main()
