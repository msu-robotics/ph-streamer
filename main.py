import serial
import socket
import time
import serial.tools.list_ports
import random
import threading
import errno

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
            print(f"Found ESP on {port}")
            return port
        print("Waiting for ESP to be connected...")
        time.sleep(2)

def open_serial(port):
    while True:
        try:
            return serial.Serial(port, BAUD_RATE)
        except Exception as e:
            print(f"Failed to open serial port {port}: {e}")
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

def wait_for_network(timeout=30):
    print("Waiting for network to become reachable...")
    start = time.time()
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.sendto(b"ping", ("255.255.255.255", 5005))
                print("Network is up.")
                return
        except OSError as e:
            if e.errno == errno.ENETUNREACH:
                if time.time() - start > timeout:
                    print("Network did not come up in time.")
                    raise
                time.sleep(2)
            else:
                raise

def broadcast_port(tcp_port, interval=2):
    def _broadcast():
        wait_for_network()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            msg = f"ESP_STREAM:{tcp_port}".encode()
            while True:
                try:
                    sock.sendto(msg, ('255.255.255.255', 5005))
                except OSError as e:
                    print(f"Broadcast error: {e}")
                time.sleep(interval)

    t = threading.Thread(target=_broadcast, daemon=True)
    t.start()

def start_tcp_server(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', port))
    s.listen(1)
    s.settimeout(1)
    print(f"TCP stream available on port {port}")
    return s

if __name__ == "__main__":
    tcp_port = get_free_tcp_port()
    broadcast_port(tcp_port)
    sock = start_tcp_server(tcp_port)

    ser = None
    conn = None

    while True:
        try:
            # Ensure serial port is connected
            if not ser or not ser.is_open:
                if ser:
                    try: ser.close()
                    except: pass
                port = wait_for_port()
                ser = open_serial(port)

            # Accept client if none is connected
            if conn is None:
                try:
                    conn, addr = sock.accept()
                    conn.settimeout(1)
                    print(f"Client connected: {addr}")
                except socket.timeout:
                    pass

            # Read from serial and forward to client
            try:
                data = ser.readline()
                if data and conn:
                    try:
                        conn.sendall(data)
                    except (BrokenPipeError, ConnectionResetError, OSError):
                        print("Client disconnected.")
                        conn.close()
                        conn = None
            except serial.SerialException as e:
                print(f"Serial read error: {e}")
                ser.close()
                ser = None
                time.sleep(2)

        except Exception as e:
            print(f"Unhandled error: {e}")
            time.sleep(2)
