from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import os

# Constants
BLOCK_SIZE = 16  # AES block size
KEY_SIZE = 32    # AES-256

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
