import hashlib
import json
import os
from user_management_module.session_manager import Session
USER_DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "user_management_module", "userData.json")

# Ensure the user data file exists
os.makedirs(os.path.dirname(USER_DATA_FILE), exist_ok=True)
if not os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump({}, f)

def load_users():
    with open(USER_DATA_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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

    users[username] = {
        "password_hash": hash_password(password)
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

    if users[username]["password_hash"] != hash_password(password):
        print("[!] Incorrect password.")
        return None

    print(f"[+] Logged in as {username}.")
    return Session(username)
