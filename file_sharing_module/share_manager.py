import os
import json
from datetime import datetime

MANIFEST_FILE = os.path.join(os.path.dirname(__file__), "../shared/shared_manifest.json")
SHARED_DIR = os.path.join(os.path.dirname(__file__), "../shared")

# Ensure shared directory exists
os.makedirs(SHARED_DIR, exist_ok=True)

# Dummy metadata structure without encryption

def load_manifest():
    if not os.path.exists(MANIFEST_FILE):
        return []
    with open(MANIFEST_FILE, "r") as f:
        return json.load(f)

def save_manifest(manifest):
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=4)

def share_file(filepath):
    if not os.path.exists(filepath):
        print("[!] File does not exist.")
        return

    filename = os.path.basename(filepath)
    shared_path = os.path.join(SHARED_DIR, filename)

    # Simulate sharing (copy file to shared folder)
    with open(filepath, "rb") as src, open(shared_path, "wb") as dst:
        dst.write(src.read())

    manifest = load_manifest()
    entry = {
        "filename": filename,
        "original_name": filename,
        "encrypted": False,
        "shared_at": datetime.utcnow().isoformat() + "Z",
        "note": "This is a placeholder for future encryption metadata."
    }
    manifest.append(entry)
    save_manifest(manifest)
    print(f"[+] File shared: {filename}")

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
