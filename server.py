import threading
import json
import hashlib
import socket
import datetime
import time

#sroda 8-10 -> 15-17


# Licenses file
LICENSES_FILE = "licenses.json"

# Server configuration
HOST = "127.0.0.1"
PORT = 9999

# Global variables
licenses = []
licenses_lock = threading.Lock()
active_licenses = {}
active_licenses_lock = threading.Lock() 
quit_server = False
quit_server_lock = threading.Lock() 

def load_licenses():
    """Load licenses from the licenses file"""
    global licenses
    try:
        with open(LICENSES_FILE) as file:
            licenses_data = json.load(file)
            licenses = licenses_data["payload"]
    except FileNotFoundError:
        print("Licenses file not found.")
        exit(1)
    except json.JSONDecodeError:
        print("Invalid licenses file format.")
        exit(1)


def generate_license_key(license_user_name):
    """Generate a license key (KL) for the given license user name (NUL)"""
    hash_object = hashlib.md5(license_user_name.encode())
    return hash_object.hexdigest()


def check_license(license_user_name, license_key):
    """Check if the license is valid for the given license user name (NUL) and license key (KL)"""
    with licenses_lock:
        for license_data in licenses:
            # print("Checking time for " + license_data["LicenceUserName"] + " " + license_user_name)
            if license_data["LicenceUserName"] == license_user_name:
                if license_data["ValidationTime"] == 0 or license_key == generate_license_key(license_user_name):
                    return True, license_data["ValidationTime"]
                else:
                    return False, "No license available for user '{}'.".format(license_user_name)
    return False, "License user name '{}' not found.".format(license_user_name)


def update_licenses():
    """Update licences"""
    while True:
        with quit_server_lock:
            if quit_server:
                break
        current_time = datetime.datetime.now()
        expired_licenses = []
        with active_licenses_lock:
            for license_user_name, expiration_time in active_licenses.items():
                expiration_datetime = datetime.datetime.fromisoformat(expiration_time)
                if current_time > expiration_datetime:
                    expired_licenses.append(license_user_name)
            for license_user_name in expired_licenses:
                del active_licenses[license_user_name]
        time.sleep(0.1)


def handle_client_request(client_socket):
    """Handle a client request"""
    request_data = client_socket.recv(1024).decode()
    request = json.loads(request_data)
    license_user_name = request["LicenceUserName"]
    license_key = request["LicenceKey"]

    license_valid, response_data = check_license(license_user_name, license_key)

    if license_valid and license_user_name not in active_licenses:
        current_time = datetime.datetime.now()
        expiration_time = current_time + datetime.timedelta(seconds=response_data)
        expiration_time = expiration_time.isoformat()
        active_licenses[license_user_name] = expiration_time
        #expiration_time = active_licenses[license_user_name]
        response = {
            "LicenceUserName": license_user_name,
            "Licence": True,
            "Expired": expiration_time
        }
    else:
        response = {
            "LicenceUserName": license_user_name,
            "Licence": False,
            "Description": response_data
        }

    client_socket.sendall(json.dumps(response).encode())
    client_socket.close()
    if response["Licence"] == False:
        return
    if license_valid:
        with active_licenses_lock:
            active_licenses[license_user_name] = expiration_time


def start_server():
    """Start the MLS server"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print(f"MLS server listening on {HOST}:{PORT}")

    while True:
        with quit_server_lock:
            if quit_server:
                break
        try:
            client_socket, _ = server_socket.accept()
        except:
            break
        client_thread = threading.Thread(target=handle_client_request, daemon=True, args=(client_socket,))
        client_thread.start()


def user_input_thread():
    """Thread to take input from the user"""
    global quit_server

    while True:
        user_input = input("Enter command (quit/print): ")
        if user_input.lower() == "quit":
            with quit_server_lock:
                quit_server = True
            break
        elif user_input.lower() == "print":
            print_active_licenses()


def print_active_licenses():
    """Print all currently active licenses"""
    with active_licenses_lock:
        print("Active Licenses:")
        for license_user_name, expiration_time in active_licenses.items():
            print(f"License User Name: {license_user_name}")
            print(f"Expiration Time: {expiration_time}")
            print()


if __name__ == "__main__":
    load_licenses()

    mls_server = threading.Thread(target=start_server, daemon=True)
    mls_server.start()

    update_licenses_thread = threading.Thread(target=update_licenses, daemon=True)
    update_licenses_thread.start()

    user_input_thread = threading.Thread(target=user_input_thread, daemon=True)
    user_input_thread.start()

    update_licenses_thread.join()
    user_input_thread.join()
    print("Exiting...")
