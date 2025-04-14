import socket
import threading
import time

# Stores peer information: { (ip, port): last_seen_timestamp }
connected_peers = {}
heartbeat_counter = {}  # Track heartbeat counts per peer
lock = threading.Lock()
print_lock = threading.Lock()

HOST = '0.0.0.0'
PORT = 9000
HEARTBEAT_INTERVAL = 30  # seconds
PEER_TIMEOUT = 90  # seconds

def safe_print(*args, end='\n', pad=100):
    with print_lock:
        msg = ' '.join(str(arg) for arg in args)
        print(msg.ljust(pad), end=end)

def remove_stale_peers():
    global connected_peers, heartbeat_counter
    while True:
        time.sleep(10)
        with lock:
            now = time.time()
            stale_peers = [peer for peer, ts in connected_peers.items() if now - ts > PEER_TIMEOUT]
            for peer in stale_peers:
                safe_print(f"[-] Peer timed out: {peer[0]}:{peer[1]}")
                connected_peers.pop(peer, None)
                heartbeat_counter.pop(peer, None)
            safe_print(f"[*] Active peers: {len(connected_peers)}", end='\r')

def handle_client(client_socket, client_address):
    global connected_peers, heartbeat_counter
    try:
        data = client_socket.recv(1024).decode()
        if data.startswith("REGISTER"):
            _, peer_ip, peer_port = data.strip().split('|')
            peer_id = (peer_ip, int(peer_port))
            now = time.time()

            with lock:
                is_new_peer = peer_id not in connected_peers
                connected_peers[peer_id] = now
                heartbeat_counter[peer_id] = heartbeat_counter.get(peer_id, 0) + 1

            if is_new_peer:
                safe_print(f"[+] New peer registered: {peer_ip}:{peer_port}")
            else:
                safe_print(f"[{heartbeat_counter[peer_id]}] Heartbeat received from {peer_ip}:{peer_port} | Active peers: {len(connected_peers)}", end='\r')

            client_socket.send(b"REGISTERED")

        elif data.startswith("UNREGISTER"):
            _, peer_ip, peer_port = data.strip().split('|')
            peer_id = (peer_ip, int(peer_port))

            with lock:
                if peer_id in connected_peers:
                    connected_peers.pop(peer_id, None)
                    heartbeat_counter.pop(peer_id, None)
                    safe_print(f"[-] Peer unregistered: {peer_ip}:{peer_port}")
                    client_socket.send(b"UNREGISTERED")
                else:
                    client_socket.send(b"PEER_NOT_FOUND")

        elif data.startswith("GETPEERS"):
            with lock:
                now = time.time()
                connected_peers = {
                    k: v for k, v in connected_peers.items()
                    if now - v < PEER_TIMEOUT
                }
                peers = [f"{ip}:{port}" for (ip, port) in connected_peers.keys()]
                response = '|'.join(peers)
            client_socket.send(response.encode())

        else:
            client_socket.send(b"UNKNOWN_COMMAND")

    except Exception as e:
        safe_print(f"[!] Error handling client {client_address}: {e}")
    finally:
        client_socket.close()

def start_server():
    safe_print(f"[*] Starting Connection Registry Server on port {PORT}...")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)

    threading.Thread(target=remove_stale_peers, daemon=True).start()

    while True:
        client_socket, client_address = server_socket.accept()
        client_thread = threading.Thread(
            target=handle_client, args=(client_socket, client_address), daemon=True
        )
        client_thread.start()

if __name__ == "__main__":
    start_server()
