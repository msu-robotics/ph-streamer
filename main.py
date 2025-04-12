import serial
import socket
import time
import serial.tools.list_ports

BAUD_RATE = 9600
TCP_PORT = 69420
ETH_IP = "192.168.77.10"

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

def start_tcp_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ETH_IP, TCP_PORT))
    s.listen(1)
    s.settimeout(1)
    print(f"TCP stream available on {ETH_IP}:{TCP_PORT}")
    return s

if __name__ == "__main__":
    sock = start_tcp_server()

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
