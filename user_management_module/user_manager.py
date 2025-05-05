import json
import os
import base64
from argon2 import PasswordHasher
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from user_management_module.session_manager import Session
from encryption_module.encrypt import (
    generate_rsa_keypair,
    encrypt_private_key,
    decrypt_private_key
)

USER_DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "user_management_module", "userData.json")
PRIVATE_KEY_DIR = os.path.join(os.path.dirname(__file__), "..", "private_keys")
os.makedirs(PRIVATE_KEY_DIR, exist_ok=True)

# Ensure the user data file exists
os.makedirs(os.path.dirname(USER_DATA_FILE), exist_ok=True)
if not os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump({}, f)

ph = PasswordHasher()

def load_users():
    with open(USER_DATA_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def derive_key_from_password(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

def register_user():
    users = load_users()
    username = input("Enter a new username: ").strip()
    if username in users:
        print("[!] Username already exists.")
        return False

    password = input("Enter a password: ").strip()
    confirm = input("Confirm password: ").strip()
    if password != confirm:
        print("[!] Passwords do not match.")
        return False

    salt = os.urandom(16)
    derived_key = derive_key_from_password(password, salt)
    password_hash = ph.hash(password)
    salt_b64 = base64.b64encode(salt).decode()

    # 🔐 Generate RSA keypair
    private_key, public_key = generate_rsa_keypair()

    # 🔐 Save encrypted private key
    priv_path = os.path.join(PRIVATE_KEY_DIR, f"{username}_private.pem.enc")
    encrypt_private_key(private_key, derived_key, priv_path)

    # 🔐 Serialize and save public key
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()

    users[username] = {
        "password_hash": password_hash,
        "salt": salt_b64,
        "public_key": public_pem
    }

    save_users(users)
    print(f"[+] User '{username}' registered successfully.")
    return True

def login_user():
    users = load_users()
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    if username not in users:
        print("[!] Username not found.")
        return None

    stored_hash = users[username]["password_hash"]
    salt = base64.b64decode(users[username]["salt"])

    try:
        ph.verify(stored_hash, password)
    except Exception:
        print("[!] Incorrect password.")
        return None

    derived_key = derive_key_from_password(password, salt)

    # 🔐 Decrypt private key
    priv_path = os.path.join(PRIVATE_KEY_DIR, f"{username}_private.pem.enc")
    if not os.path.exists(priv_path):
        print("[!] Private key file missing.")
        return None
    private_key = decrypt_private_key(priv_path, derived_key)

    print(f"[+] Logged in as {username}.")
    return Session(username=username, derived_key=derived_key, private_key=private_key)
