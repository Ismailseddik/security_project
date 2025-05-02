import os
import json
from datetime import datetime
import hashlib
from encryption_module.encrypt import encrypt_file, generate_key

MANIFEST_FILE = os.path.join(os.path.dirname(__file__), "../shared/shared_manifest.json")
SHARED_DIR = os.path.join(os.path.dirname(__file__), "../shared")

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

def share_file(filepath):
    if not os.path.exists(filepath):
        print("[!] File does not exist.")
        return

    filename = os.path.basename(filepath)
    shared_path = os.path.join(SHARED_DIR, filename)

    # Step 1: Compute the hash before encryption (on original file)
    hash_value = compute_file_hash(filepath)

    # Step 2: Generate encryption key and encrypt the file
    key = generate_key()
    encrypt_file(filepath, shared_path, key)

    # Step 3: Save metadata to manifest
    manifest = load_manifest()
    entry = {
        "filename": filename,
        "original_name": filename,
        "encrypted": True,
        "shared_at": datetime.utcnow().isoformat() + "Z",
        "hash": hash_value,  # This is the plaintext hash used after decryption
        "note": "AES-256-CBC encryption with padding",
        "key": key.hex()  # TEMPORARY – for Phase 3 only
    }
    manifest.append(entry)
    save_manifest(manifest)
    print(f"[+] File shared securely: {filename}")

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
