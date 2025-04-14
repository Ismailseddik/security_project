import threading
import time
from peer_discovery import PeerDiscovery
from peer_communication import PeerCommunicator

LOCAL_IP = '127.0.0.1'
LOCAL_PORT = 10000  # Change for each peer manually
HEARTBEAT_INTERVAL = 30  # seconds

heartbeat_count = 0
running = True

def send_heartbeat(discovery: PeerDiscovery):
    global heartbeat_count
    while running:
        time.sleep(HEARTBEAT_INTERVAL)
        try:
            # Heartbeat registration without verbose output
            discovery.register_with_registry(silent=True)
            heartbeat_count += 1
        except Exception as e:
            print(f"[!] Heartbeat failed: {e}")

def connect_to_available_peers(discovery: PeerDiscovery, communicator: PeerCommunicator, my_username):
    peers = discovery.get_active_peers()
    for peer in peers:
        ip, port = peer.split(':')
        port = int(port)
        if port == LOCAL_PORT:
            continue  # Skip self
        communicator.send_connection_request(ip, port, my_username)

def shutdown_peer(discovery: PeerDiscovery, communicator: PeerCommunicator):
    global running
    print("\n[!] Shutting down peer and disconnecting...")
    running = False
    communicator.disconnect_all_peers()
    discovery.unregister_from_registry()
    print("[!] Peer shutdown complete.")

def cli_menu(discovery: PeerDiscovery, communicator: PeerCommunicator, my_username):
    global running
    while running:
        print("\n========= Peer Menu =========")
        print("1. View active peers")
        print("2. Connect to a peer")
        print("3. Show connected peers")
        print("4. Exit")
        print("5. Respond to pending connection requests")
        choice = input("Select an option: ").strip()

        if choice == '1':
            discovery.get_active_peers()

        elif choice == '2':
            peers = discovery.get_active_peers()
            peers = [p for p in peers if int(p.split(":")[1]) != LOCAL_PORT]
            if not peers:
                print("[!] No other peers available.")
                continue

            print("Available peers:")
            for idx, peer in enumerate(peers):
                print(f"{idx + 1}. {peer}")

            selected = input("Enter peer number to connect: ").strip()
            if selected.isdigit() and 1 <= int(selected) <= len(peers):
                ip, port = peers[int(selected) - 1].split(":")
                communicator.send_connection_request(ip, int(port), my_username)
            else:
                print("[!] Invalid selection.")

        elif choice == '3':
            if communicator.active_connections:
                print("Connected peers:")
                for peer_addr in communicator.active_connections:
                    print(f"- {peer_addr}")
            else:
                print("[!] No active connections.")

        elif choice == '4':
            shutdown_peer(discovery, communicator)
            break

        elif choice == '5':
            communicator.respond_to_pending_requests()

        else:
            print("[!] Invalid option. Try again.")


if __name__ == "__main__":
    my_username = input("Enter your username: ").strip()

    discovery = PeerDiscovery(local_ip=LOCAL_IP, local_port=LOCAL_PORT)
    communicator = PeerCommunicator(local_port=LOCAL_PORT)

    # Start listener for incoming peer requests
    threading.Thread(target=communicator.start_listener, daemon=True).start()
    time.sleep(1)

    # Register this peer (only once loudly)
    discovery.register_with_registry()

    # Start heartbeat thread
    threading.Thread(target=send_heartbeat, args=(discovery,), daemon=True).start()

    # Launch interactive CLI
    cli_menu(discovery, communicator, my_username)

    # Grace period before exiting
    time.sleep(1)
