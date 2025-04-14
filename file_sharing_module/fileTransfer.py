import os
import socket
import threading

SHARED_DIR = os.path.join(os.path.dirname(__file__), "../shared")
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "../downloads")
BUFFER_SIZE = 4096

# Ensure the directories exist
os.makedirs(SHARED_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def send_file(filename, conn):
    filepath = os.path.join(SHARED_DIR, filename)
    print(f"[DEBUG] Opening file at path: {filepath}")

    if not os.path.exists(filepath):
        conn.send(b"FILE_NOT_FOUND")
        print(f"[!] Requested file not found: {filename}")
        conn.close()
        return

    conn.send(b"FILE_FOUND")
    print(f"[+] Sending file: {filename}")

    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(BUFFER_SIZE):
                conn.send(chunk)
        print(f"[+] File sent successfully: {filename}")
    except Exception as e:
        print(f"[!] Error sending file {filename}: {e}")
    finally:
        conn.close()


def handle_incoming_file_request(filename, conn):
    try:
        print(f"[DEBUG] Preparing to send file: {filename}")
        send_file(filename, conn)
    except Exception as e:
        print(f"[!] Failed to handle file request: {e}")
        conn.close()

def request_file(peer_ip, port, filename):
    save_path = os.path.join(DOWNLOAD_DIR, filename)
    try:
        s = socket.socket()
        s.connect((peer_ip, port))
        s.send(f"GET_FILE|{filename}".encode())

        status = s.recv(BUFFER_SIZE)
        if status == b"FILE_NOT_FOUND":
            print(f"[-] Peer does not have the file: {filename}")
            s.close()
            return

        print(f"[+] Receiving file: {filename}")
        with open(save_path, "wb") as f:
            while True:
                data = s.recv(BUFFER_SIZE)
                if not data:
                    break
                f.write(data)

        print(f"[+] File received and saved to: {save_path}")
    except Exception as e:
        print(f"[!] Failed to download file from peer: {e}")
    finally:
        s.close()
