from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
import base64
import hmac
import hashlib


import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto import Random




def load_public_key(base64_key_str):
    key_der = base64.b64decode(base64_key_str)
    rsa_key = RSA.importKey(key_der)
    return rsa_key


def rsa_encrypt_chunked(data, base64_public_key):
    public_key = load_public_key(base64_public_key)
    cipher = PKCS1_v1_5.new(public_key)

    data_bytes = b"{data}"
    max_chunk_size = 64  # 64 bytes per chunk as in the Java code

    encrypted = b''
    for i in range(0, len(data_bytes), max_chunk_size):
        chunk = data_bytes[i:i + max_chunk_size]
        encrypted += cipher.encrypt(chunk)

    encrypted_b64 = base64.b64encode(encrypted).decode('utf-8')
    return encrypted_b64


def generate_hash_value(encrypted_payload: str, secret_key: str) -> str:
    return hmac.new(
        key=secret_key.encode(),
        msg=encrypted_payload.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()


def decrypt(encrypted_base64_str, private_key_pem):
    encrypted_data = base64.b64decode(encrypted_base64_str)
    private_key = RSA.import_key(private_key_pem)
    cipher_rsa = PKCS1_v1_5.new(private_key)

    sentinel = Random.get_random_bytes(32)
    chunk_size = 128  # 1024 bits = 128 bytes per encrypted block

    decrypted_chunks = []
    for i in range(0, len(encrypted_data), chunk_size):
        chunk = encrypted_data[i:i + chunk_size]
        decrypted_chunk = cipher_rsa.decrypt(chunk, sentinel)
        decrypted_chunks.append(decrypted_chunk)

    decrypted_data = b"".join(decrypted_chunks)
    return decrypted_data.decode('utf-8')


