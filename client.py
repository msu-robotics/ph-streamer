import platform
import socket
import os

# Fixed server address and port
SERVER_IP = "192.168.77.10"
SERVER_PORT = 42069

def clear_screen():
    os.system('cls' if platform.system() == "Windows" else 'clear')

def main():
    print(f"Connecting to {SERVER_IP}:{SERVER_PORT}...")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((SERVER_IP, SERVER_PORT))
            print(f"Connected to {SERVER_IP}:{SERVER_PORT}")
            while True:
                data = s.recv(1024)
                if not data:
                    break
                clear_screen()
                print(data.decode('utf-8', errors='ignore').strip())
        except Exception as e:
            print(f"Connection error: {e}")

if __name__ == "__main__":
    main()
