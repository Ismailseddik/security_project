import socket
import threading

# Simple peer communication module

class PeerCommunicator:
    def __init__(self, local_port):
        self.local_port = local_port
        self.active_connections = {}  # {peer_address: socket}
        self.pending_requests = []    # List of (peer_name, addr, conn)
        self.lock = threading.Lock()

    def start_listener(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(('0.0.0.0', self.local_port))
        listener.listen(5)
        print(f"[*] Listening for incoming peer messages on port {self.local_port}...")

        while True:
            conn, addr = listener.accept()
            threading.Thread(target=self.handle_peer_message, args=(conn, addr), daemon=True).start()

    def handle_peer_message(self, conn, addr):
        try:
            message = conn.recv(1024).decode()
            if message.startswith("REQUEST_CONNECT"):
                _, peer_name = message.strip().split('|')
                print(f"[!] Connection request from {peer_name} at {addr} (pending approval)")
                with self.lock:
                    self.pending_requests.append((peer_name, addr, conn))

            elif message.startswith("ACCEPT_CONNECT"):
                _, peer_name = message.strip().split('|')
                print(f"[+] Connection accepted by {peer_name} at {addr}")
                self.log_peer_accepted(peer_name, addr)

            elif message.startswith("DENY_CONNECT"):
                _, peer_name = message.strip().split('|')
                print(f"[-] Connection denied by {peer_name} at {addr}")

            else:
                print(f"[Peer:{addr}] {message}")

        except Exception as e:
            print(f"[!] Error handling message from {addr}: {e}")
        # Do not close connection here if pending

    def respond_to_pending_requests(self):
        with self.lock:
            if not self.pending_requests:
                print("[!] No pending connection requests.")
                return

            for i, (peer_name, addr, conn) in enumerate(self.pending_requests):
                response = input(f"[?] Accept connection from {peer_name} at {addr}? (y/n): ").strip().lower()
                if response == 'y':
                    conn.send(f"ACCEPT_CONNECT|{peer_name}".encode())
                    self.active_connections[addr] = conn
                    print(f"[+] Connection accepted from {peer_name} ({addr})")
                    self.log_peer_accepted(peer_name, addr)
                else:
                    conn.send(f"DENY_CONNECT|{peer_name}".encode())
                    conn.close()
                    print(f"[-] Connection denied from {peer_name} ({addr})")
            self.pending_requests.clear()

    def send_connection_request(self, ip, port, my_username):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            message = f"REQUEST_CONNECT|{my_username}"
            s.send(message.encode())
            response = s.recv(1024).decode()

            if response.startswith("ACCEPT_CONNECT"):
                print(f"[+] Peer at {ip}:{port} accepted your connection.")
                self.active_connections[(ip, port)] = s
                self.log_peer_accepted(ip, port)
            elif response.startswith("DENY_CONNECT"):
                print(f"[-] Peer at {ip}:{port} denied your connection.")
                s.close()
            else:
                print(f"[!] Unexpected response from {ip}:{port}: {response}")
                s.close()

        except Exception as e:
            print(f"[!] Could not send connection request to {ip}:{port} - {e}")

    def disconnect_all_peers(self):
        print("[!] Disconnecting from all peers...")
        for addr, conn in self.active_connections.items():
            try:
                conn.close()
                print(f"[-] Disconnected from {addr}")
            except Exception as e:
                print(f"[!] Failed to close connection with {addr}: {e}")
        self.active_connections.clear()

    def log_peer_accepted(self, peer_name, addr):
        with open("accepted_peers.log", "a") as log_file:
            log_file.write(f"Accepted connection with {peer_name} at {addr}\n")
