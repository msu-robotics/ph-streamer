import serial
import socket
import time
import serial.tools.list_ports
import random

BAUD_RATE = 9600
MIN_PORT = 10000
MAX_PORT = 60000

def find_esp_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if ('USB' in p.description or 'UART' in p.description) and (
            'CH340' in p.description or 'CP210' in p.description or 'ESP' in p.description):
            return p.device
    return None

def wait_for_port():
    while True:
        port = find_esp_port()
        if port:
            print(f"✅ Found ESP on {port}")
            return port
        print("🔌 Waiting for ESP to be connected....")
        time.sleep(2)

def open_serial(port):
    while True:
        try:
            return serial.Serial(port, BAUD_RATE)
        except Exception as e:
            print(f"❌ Failed to open serial port {port}: {e}")
            time.sleep(2)

def get_free_tcp_port():
    while True:
        port = random.randint(MIN_PORT, MAX_PORT)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue


def broadcast_port(tcp_port, interval=2):
    import threading

    def _broadcast():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            msg = f"ESP_STREAM:{tcp_port}".encode()
            while True:
                sock.sendto(msg, ('255.255.255.255', 5005))
                time.sleep(interval)

    t = threading.Thread(target=_broadcast, daemon=True)
    t.start()


def start_tcp_server(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', port))
    s.listen(1)
    print(f"🌐 TCP stream available on port {port}")
    print(f"📡 Waiting for a client to connect...")
    conn, addr = s.accept()
    print(f"🔌 Client connected: {addr}")
    return conn, s

if __name__ == "__main__":
    while True:
        port = wait_for_port()
        ser = open_serial(port)

        tcp_port = get_free_tcp_port()
        broadcast_port(tcp_port)
        conn, sock = start_tcp_server(tcp_port)

        try:
            while True:
                data = ser.readline()
                if data:
                    conn.sendall(data)
        except (serial.SerialException, OSError, ConnectionResetError) as e:
            print(f"⚠️ Connection lost: {e}. Restarting...")
            try:
                conn.close()
                sock.close()
                ser.close()
            except:
                pass
            time.sleep(2)
