import datetime
import json
import socket
import sys
import threading
import time

# Server configuration
HOST = "127.0.0.1"
PORT = 9999


class LicenseAPI:
    def __init__(self):
        self.server_address = ""

    def start(self, server_address):
        """Start the API by setting the server address"""
        self.server_address = server_address

    def set_license(self, license_user_name, license_key):
        """Set the license for the given license user name (NUL) and license key (KL)"""
        self.license_user_name = license_user_name
        self.license_key = license_key

    def get_license_token(self):
        """Get the license token (TL)"""
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect(self.server_address)
        except ConnectionRefusedError:
            return {
                "LicenceUserName": self.license_user_name,
                "Licence": False,
                "Description": "Failed to connect to MLS server."
            }

        request = {
            "LicenceUserName": self.license_user_name,
            "LicenceKey": self.license_key
        }
        client_socket.sendall(json.dumps(request).encode())
        response_data = client_socket.recv(1024).decode()
        response = json.loads(response_data)
        client_socket.close()

        return response

    def stop(self):
        """Stop the API by resetting the license data"""
        self.license_user_name = ""
        self.license_key = ""

def print_response(response):
    """Print servers respond in human way"""
    print(response["LicenceUserName"] + "'s licence status:")
    if response["Licence"] == True:
        print("Active\n" + response["Expired"])
    else:
        print(response["Description"])

if __name__ == "__main__":
    args = sys.argv[1:]
    api = LicenseAPI()
    api.start((HOST, PORT))
    api.set_license(args[0], args[1])
    
    while(True):
        response = api.get_license_token()
        print_response(response)
        secs = (datetime.datetime.fromisoformat(response['Expired']) - datetime.datetime.now()).total_seconds()
        print(secs)
        time.sleep(secs+1)
