import socket

REGISTRY_HOST = '127.0.0.1'
REGISTRY_PORT = 9000

class PeerDiscovery:
    def __init__(self, local_ip='127.0.0.1', local_port=10000):
        self.local_ip = local_ip
        self.local_port = local_port

    def register_with_registry(self, silent=False):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((REGISTRY_HOST, REGISTRY_PORT))
                registration_message = f"REGISTER|{self.local_ip}|{self.local_port}"
                s.send(registration_message.encode())
                response = s.recv(1024).decode()
                if not silent:
                    print(f"[Registry] {response}")
        except Exception as e:
            print(f"[!] Failed to register with registry: {e}")
    def unregister_from_registry(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((REGISTRY_HOST, REGISTRY_PORT))
                message = f"UNREGISTER|{self.local_ip}|{self.local_port}"
                s.send(message.encode())
                response = s.recv(1024).decode()
                if response == "UNREGISTERED":
                    print(f"[Registry] Successfully unregistered {self.local_ip}:{self.local_port}")
                else:
                    print(f"[Registry] Unregister failed: {response}")
        except Exception as e:
            print(f"[!] Failed to unregister from registry: {e}")

    def get_active_peers(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((REGISTRY_HOST, REGISTRY_PORT))
                s.send(b"GETPEERS")
                response = s.recv(2048).decode()
                if response:
                    peers = response.split('|')
                    print(f"[*] Active peers: {peers}")
                    return peers
                else:
                    print("[*] No active peers found.")
                    return []
        except Exception as e:
            print(f"[!] Could not retrieve peer list: {e}")
            return []
