import json
import hmac
import hashlib
import base64
import rsa

def rsa_encrypt_large_message(data_str, pub_key_str):
    # Load public key from base64 string
    pub_key = rsa.PublicKey.load_pkcs1_openssl_pem(pub_key_str.encode())

    # Convert string to bytes
    data_bytes = data_str.encode()

    # RSA block size depends on key length - 11 bytes for padding
    max_length = rsa.common.byte_size(pub_key.n) - 11

    encrypted = b''
    for i in range(0, len(data_bytes), max_length):
        chunk = data_bytes[i:i+max_length]
        encrypted += rsa.encrypt(chunk, pub_key)

    return base64.b64encode(encrypted).decode()


def generate_hash_value(encrypted_payload: str, secret_key: str) -> str:
    return hmac.new(
        key=secret_key.encode(),
        msg=encrypted_payload.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()

