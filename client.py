import platform
import socket
import os
import time

UDP_PORT = 5005

def clear_screen():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')
def discover_server(timeout=10):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(('', UDP_PORT))
        sock.settimeout(timeout)
        try:
            print(f"🔍 Listening for broadcast on UDP port {UDP_PORT}...")
            msg, addr = sock.recvfrom(1024)
            msg = msg.decode()
            if msg.startswith("ESP_STREAM:"):
                port = int(msg.split(":")[1])
                print(f"✅ Found server at {addr[0]}:{port}")
                return addr[0], port
        except socket.timeout:
            print("❌ No broadcast received.")
            return None, None

def main():
    host, port = discover_server()
    if not host or not port:
        return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((host, port))
            print(f"📡 Connected to {host}:{port}")
            while True:
                data = s.recv(1024)
                if not data:
                    break
                clear_screen()
                print(data.decode('utf-8', errors='ignore').strip())
        except Exception as e:
            print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    main()
