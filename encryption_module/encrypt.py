from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding as crypto_padding
import os


# Constants
BLOCK_SIZE = 16  # AES block size (bytes)
KEY_SIZE = 32    # AES-256
RSA_KEY_SIZE = 2048
PRIVATE_KEY_DIR = os.path.join(os.path.dirname(__file__), "../private_keys")
os.makedirs(PRIVATE_KEY_DIR, exist_ok=True)

def pad(data: bytes) -> bytes:
    padding_length = BLOCK_SIZE - len(data) % BLOCK_SIZE
    return data + bytes([padding_length] * padding_length)

def unpad(data: bytes) -> bytes:
    padding_length = data[-1]
    return data[:-padding_length]

def generate_key() -> bytes:
    return get_random_bytes(KEY_SIZE)

def encrypt_file(input_path: str, output_path: str, key: bytes) -> None:
    cipher = AES.new(key, AES.MODE_CBC)
    iv = cipher.iv

    with open(input_path, 'rb') as f_in:
        plaintext = f_in.read()
    padded = pad(plaintext)
    ciphertext = cipher.encrypt(padded)

    with open(output_path, 'wb') as f_out:
        f_out.write(iv + ciphertext)

def decrypt_file(input_path: str, output_path: str, key: bytes) -> None:
    with open(input_path, 'rb') as f_in:
        iv = f_in.read(BLOCK_SIZE)
        ciphertext = f_in.read()

    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_plaintext = cipher.decrypt(ciphertext)
    plaintext = unpad(padded_plaintext)

    with open(output_path, 'wb') as f_out:
        f_out.write(plaintext)

def generate_rsa_keypair():
    """Generates an RSA private/public key pair."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=RSA_KEY_SIZE,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key

def encrypt_private_key(private_key, aes_key: bytes, filepath: str):
    """Encrypts a private RSA key using AES and writes it to disk."""
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    iv = get_random_bytes(BLOCK_SIZE)
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    padder = crypto_padding.PKCS7(BLOCK_SIZE * 8).padder()
    padded_data = padder.update(pem) + padder.finalize()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    with open(filepath, "wb") as f:
        f.write(iv + ciphertext)

def decrypt_private_key(filepath: str, aes_key: bytes):
    """Decrypts an AES-encrypted private key from file and loads it."""
    with open(filepath, "rb") as f:
        data = f.read()

    iv = data[:BLOCK_SIZE]
    ciphertext = data[BLOCK_SIZE:]

    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_key = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = crypto_padding.PKCS7(BLOCK_SIZE * 8).unpadder()
    pem = unpadder.update(padded_key) + unpadder.finalize()

    private_key = serialization.load_pem_private_key(
        pem,
        password=None,
        backend=default_backend()
    )
    return private_key
