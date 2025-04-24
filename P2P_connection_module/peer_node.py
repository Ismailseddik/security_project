import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import threading
import time
from peer_discovery import PeerDiscovery
from peer_communication import PeerCommunicator
from file_sharing_module.fileTransfer import request_file
from file_sharing_module.share_manager import share_file, list_shared_files, unshare_file
from user_management_module.user_manager import login_user, register_user
from user_management_module.session_manager import Session

LOCAL_IP = '127.0.0.1'
LOCAL_PORT = 10000  # Change manually for each peer
HEARTBEAT_INTERVAL = 30  # seconds

heartbeat_count = 0
running = True

def send_heartbeat(discovery: PeerDiscovery):
    global heartbeat_count
    while running:
        time.sleep(HEARTBEAT_INTERVAL)
        try:
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
    
def monitor_session(session: Session, discovery: PeerDiscovery, communicator: PeerCommunicator):
    while running:
        if session.is_expired():
            print(f"\n[!] Session expired for {session.username}. Logging out.")
            shutdown_peer(discovery, communicator)
            os._exit(0)  # Force exit due to input() blocking
        time.sleep(5)
        
def cli_menu(discovery: PeerDiscovery, communicator: PeerCommunicator, session):
    my_username = session.username
    global running
    while running:
        print("\n========= Peer Menu =========")
        print("1. View active peers")
        print("2. Connect to a peer")
        print("3. Show connected peers")
        print("4. Exit")
        print("5. Respond to pending connection requests")
        print("6. Request a file from a connected peer")
        print("7. Share a file")
        print("8. List shared files")
        print("9. unshare a file")
        print("10. view session details")
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
            communicator.prune_dead_connections()
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

        elif choice == '6':
            if not communicator.active_connections:
                print("[!] No connected peers available to request a file.")
                continue

            print("Connected peers:")
            connected_peers = list(communicator.active_connections.keys())
            for idx, peer in enumerate(connected_peers):
                print(f"{idx + 1}. {peer}")

            selected = input("Enter peer number to request file from: ").strip()
            if selected.isdigit() and 1 <= int(selected) <= len(connected_peers):
                filename = input("Enter the filename to request: ").strip()
                ip, port = connected_peers[int(selected) - 1]
                request_file(ip, port, filename)
            else:
                print("[!] Invalid selection.")

        elif choice == '7':
            filepath = input("Enter full path of the file to share: ").strip()
            share_file(filepath)
            list_shared_files()
            
        elif choice == '8':
            list_shared_files()
            
        elif choice == '9':
            unshare_file()   
        elif choice == '10':
            print(session)
        else:
            print("[!] Invalid option. Try again.")

def auth_menu():
    while True:
        print("\n========= Authentication =========")
        print("1. Login")
        print("2. Register")
        print("3. Exit")
        choice = input("Select an option: ").strip()
        if choice == '1':
            user = login_user()
            if user:
                return user
        elif choice == '2':
            registered = register_user()
            if registered:
                print("[+] You may now log in.")
        elif choice == '3':
            print("Exiting...")
            exit(0)
        else:
            print("[!] Invalid option. Try again.")

if __name__ == "__main__":
    session = auth_menu()
    

    discovery = PeerDiscovery(local_ip=LOCAL_IP, local_port=LOCAL_PORT)
    communicator = PeerCommunicator(local_port=LOCAL_PORT)

    threading.Thread(target=communicator.start_listener, daemon=True).start()
    time.sleep(1)

    discovery.register_with_registry()
    threading.Thread(target=send_heartbeat, args=(discovery,), daemon=True).start()
    threading.Thread(target=monitor_session, args=(session, discovery, communicator), daemon=True).start()
    cli_menu(discovery, communicator, session)
    time.sleep(1)
