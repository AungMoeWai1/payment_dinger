import base64
import hashlib
import hmac
import json
from urllib.parse import quote_plus, urlencode

import requests
from Crypto import Random
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

SIZE = 64
CHUNK_SIZE = 128


class EncryptRSA:

    def __init__(self, **data):
        # Get this from Dinger documentation
        self.public_key = RSA.import_key(
            "-----BEGIN PUBLIC KEY-----\n"
            + "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCFD4IL1suUt/TsJu6zScnvsEdLPuACgBdjX82QQf8NQlFHu2v/84dztaJEyljv3TGPuEgUftpC9OEOuEG29z7z1uOw7c9T/luRhgRrkH7AwOj4U1+eK3T1R+8LVYATtPCkqAAiomkTU+aC5Y2vfMInZMgjX0DdKMctUur8tQtvkwIDAQAB"
            + "\n-----END PUBLIC KEY-----"
        )
        self.encoded_data = json.dumps(data).encode("utf-8")

    def encrypt(self, public_key=None):
        """Encrypts the encoded data using the provided public key."""
        if not public_key:
            public_key = self.public_key
        elif public_key:
            public_key = RSA.import_key(public_key)
        try:
            cipher_rsa = PKCS1_v1_5.new(public_key)
            res = []
            for i in range(0, len(self.encoded_data), SIZE):
                enc_tmp = cipher_rsa.encrypt(self.encoded_data[i : i + SIZE])
                res.append(enc_tmp)
                cipher_text = b"".join(res)
        except Exception as e:
            print(e)
        else:
            return base64.b64encode(cipher_text).decode()

    @staticmethod
    def generate_rsa_key():
        """
        This function creates an RSA key pair with a key size of 1024 bits.
        Returns:
            tuple: A tuple containing the generated private key and its corresponding public key.
        """
        # Derive the public key from the generated key
        # public_key = private_key.publickey()
        private_key = RSA.generate(1024)
        # Return the private key and public key
        return private_key, private_key.export_key().decode("utf-8")

    def generate_hash_value(self, secret_key):
        """Generates a HMAC-SHA256 hash of the encrypted payload using the secret key."""
        return hmac.new(
            key=secret_key.encode("utf-8"),
            msg=self.encoded_data,
            digestmod=hashlib.sha256,
        ).hexdigest()

    def decrypt(self, encrypted_payload, private_key):
        """Decrypts the given base64 encoded payload using the provided private key."""
        # Check if private_key is provided
        if not private_key:
            raise ValueError("Private key is required for decryption.")
        # Convert the private key from PEM format to a usable RSA key object
        # Load the private key
        # Decode the base64 encoded string
        encrypted_payload = base64.b64decode(encrypted_payload)
        sentinel = Random.get_random_bytes(32)
        try:
            # Create a PKCS1_OAEP cipher object with the private key for decryption
            cipher_rsa = PKCS1_v1_5.new(private_key)
            decrypted_chunks = []
            # Decrypt the payload in chunks
            for i in range(0, len(encrypted_payload), CHUNK_SIZE):
                chunk = encrypted_payload[i : i + CHUNK_SIZE]
                decrypted_chunk = cipher_rsa.decrypt(chunk, sentinel)
                decrypted_chunks.append(decrypted_chunk)
            decrypted_data = b"".join(decrypted_chunks)
        except Exception as e:
            # Handle decryption errors
            # For example, if the private key is invalid or decryption fails
            print(e)
            return None
        else:
            # Display the decrypted result as a UTF-8 encoded string
            return decrypted_data.decode("utf-8")

    @staticmethod
    def pay(baseurl, data, secretkey):
        # get from checkout-form page
        # encrypt
        encrypt_rsa = EncryptRSA(**data)
        encryptedPayload, hashValue = (
            encrypt_rsa.encrypt(),
            encrypt_rsa.generate_hash_value(secretkey),
        )
        # calculate hash
        # send GET request to this final url
        return (
            f"{baseurl}?{urlencode({'payload': encryptedPayload, 'hashValue': hashValue}, quote_via=quote_plus)}",
            encryptedPayload,
            hashValue,
        )
