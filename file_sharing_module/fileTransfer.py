import os
import socket
import base64
from encryption_module.encrypt import decrypt_file
from file_sharing_module.share_manager import load_manifest, compute_file_hash
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

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

def request_file(peer_ip, port, filename, session):
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

        # --- DECRYPTION & INTEGRITY VERIFICATION ---
        manifest = load_manifest()
        entry = next((item for item in manifest if item["filename"] == filename), None)

        if entry and entry.get("encrypted") and "access" in entry:
            if session.username not in entry["access"]:
                print("[!] You are not authorized to decrypt this file.")
                return

            encrypted_file_key_b64 = entry["access"][session.username]
            encrypted_file_key = base64.b64decode(encrypted_file_key_b64)

            try:
                file_key = session.private_key.decrypt(
                    encrypted_file_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
            except Exception as e:
                print(f"[!] Failed to decrypt file key: {e}")
                return

            decrypted_path = os.path.join(DOWNLOAD_DIR, f"decrypted_{filename}")
            decrypt_file(save_path, decrypted_path, file_key)
            print(f"[+] File decrypted and saved to: {decrypted_path}")

            downloaded_hash = compute_file_hash(decrypted_path)
            if downloaded_hash == entry["hash"]:
                print("[+] File integrity verified.")
            else:
                print("[!] WARNING: File integrity check failed.")
        else:
            print("[!] No decryption metadata found for this file.")
    except Exception as e:
        print(f"[!] Failed to download file from peer: {e}")
    finally:
        s.close()
