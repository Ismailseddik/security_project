import os
import json
import base64
from datetime import datetime
import hashlib
from encryption_module.encrypt import encrypt_file, generate_key
from user_management_module.session_manager import Session
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

MANIFEST_FILE = os.path.join(os.path.dirname(__file__), "../shared/shared_manifest.json")
SHARED_DIR = os.path.join(os.path.dirname(__file__), "../shared")
USER_DATA_FILE = os.path.join(os.path.dirname(__file__), "../user_management_module/userData.json")

# Ensure shared directory exists
os.makedirs(SHARED_DIR, exist_ok=True)

def load_manifest():
    if not os.path.exists(MANIFEST_FILE):
        return []
    with open(MANIFEST_FILE, "r") as f:
        return json.load(f)

def save_manifest(manifest):
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=4)

def compute_file_hash(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(4096):
            sha256.update(chunk)
    return sha256.hexdigest()

def load_users():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE, 'r') as f:
        return json.load(f)

def share_file(filepath, session: Session):
    if not os.path.exists(filepath):
        print("[!] File does not exist.")
        return

    filename = os.path.basename(filepath)
    shared_path = os.path.join(SHARED_DIR, filename)

    # Step 1: Compute hash before encryption (plaintext)
    hash_value = compute_file_hash(filepath)

    # Step 2: Generate random AES key and encrypt the file
    file_key = generate_key()
    encrypt_file(filepath, shared_path, file_key)

    # Step 3: Choose recipients
    users = load_users()
    print("Enter usernames to share this file with (comma-separated):")
    print("Available users:", ", ".join(users.keys()))
    recipients = input("Recipients: ").strip().split(",")
    recipients = [r.strip() for r in recipients if r.strip() in users]

    # Step 4: Encrypt file_key for each recipient
    access = {}
    for recipient in recipients:
        try:
            pub_pem = users[recipient]["public_key"].encode()
            public_key = serialization.load_pem_public_key(pub_pem)

            encrypted_key = public_key.encrypt(
                file_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            access[recipient] = base64.b64encode(encrypted_key).decode()
        except Exception as e:
            print(f"[!] Failed to encrypt file key for {recipient}: {e}")

    # Step 5: Save to manifest
    manifest = load_manifest()
    entry = {
        "filename": filename,
        "original_name": filename,
        "encrypted": True,
        "shared_at": datetime.utcnow().isoformat() + "Z",
        "hash": hash_value,
        "note": "Encrypted with AES, keys shared via RSA",
        "access": access
    }
    manifest.append(entry)
    save_manifest(manifest)
    print(f"[+] File shared securely with: {', '.join(access.keys()) if access else 'no one'}")

def list_shared_files():
    manifest = load_manifest()
    if not manifest:
        print("[!] No files have been shared.")
        return
    print("\nShared Files:")
    for idx, entry in enumerate(manifest):
        print(f"{idx + 1}. {entry['filename']} (shared at {entry['shared_at']})")

def unshare_file():
    manifest = load_manifest()
    if not manifest:
        print("[!] No files to unshare.")
        return

    print("\nShared Files:")
    for idx, entry in enumerate(manifest):
        print(f"{idx + 1}. {entry['filename']} (shared at {entry['shared_at']})")

    try:
        choice = int(input("Enter the number of the file to unshare: "))
        if 1 <= choice <= len(manifest):
            entry = manifest.pop(choice - 1)
            file_path = os.path.join(SHARED_DIR, entry["filename"])

            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"[-] File '{entry['filename']}' has been unshared and deleted.")
            else:
                print(f"[!] File '{entry['filename']}' not found in shared directory.")

            save_manifest(manifest)
        else:
            print("[!] Invalid selection.")
    except ValueError:
        print("[!] Please enter a valid number.")
