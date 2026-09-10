"""
This is a test receiver that binds to the IP and port main.py transmits telemetry on, 
verifying that the UDP packets are successfully traveling over the local network.

To test, run main.py in one terminal and test_listener.py (this file) in another.
If everything is correct the printed data will update with joystick movements.
"""

import socket
import main

# Bind to the same IP and port as main.py
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((main.UDP_IP, main.UDP_PORT))

print("INFO [standalone_node.test_listener] Listening for joystick telemetry on port 5005...")

while True:
    data, addr = sock.recvfrom(1024)    # Receiving up to 1024 bytes
    print(f"Received: {data.decode('utf-8')}")