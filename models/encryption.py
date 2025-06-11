# -*- coding: utf-8 -*-
# pylint: disable=broad-except
"""Dinger RSA Encryption and Decryption Class.
This class provides methods to encrypt and decrypt data using RSA,
generate RSA keys, and create HMAC-SHA256 hashes for secure communication
with the Dinger payment provider.
Attributes:
    public_key (str): The RSA public key used for encryption.
    encoded_data (bytes): The data to be encrypted, encoded as bytes.
Methods:
    encrypt(public_key=None): Encrypts the encoded data using the provided public key.
    generate_rsa_key(): Generates a new RSA key pair.
    generate_hash_value(secret_key): Generates a HMAC-SHA256 hash of the encoded data using the secret key.
    decrypt(encrypted_payload, private_key): Decrypts the given base64 encoded payload using the provided private key.
    pay(baseurl, data, secretkey): Prepares and returns the URL for payment request with encrypted payload and hash value.

Raises:
    ValueError: If the private key is not provided for decryption or if the public key is invalid.
    ValueError: If the secret key is not provided for hash generation.
Usage:
    encryptor = EncryptRSA(**data)
    encrypted_payload = encryptor.encrypt()
    hash_value = encryptor.generate_hash_value(secret_key)
    url, payload, hash_value = EncryptRSA.pay(baseurl, data, secretkey)
    decrypted_data = encryptor.decrypt(encrypted_payload, private_key)
Args:
    public_key (str): The RSA public key used for encryption.
    data (dict): The data to be encrypted, provided as a dictionary.
    secret_key (str): The secret key used for generating HMAC-SHA256 hashes.
    private_key (str): The RSA private key used for decryption.

Returns:
    str: The encrypted payload as a base64 encoded string.
    str: The generated hash value as a hexadecimal string.
    str: The decrypted data as a UTF-8 encoded string.
"""
import base64
import hashlib
import hmac
import json
from urllib.parse import quote_plus, urlencode

from Crypto import Random
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

SIZE = 64
CHUNK_SIZE = 128


class EncryptRSA:
    """Class to handle RSA encryption and decryption for Dinger payment provider."""
    def __init__(self, **data):
        # Get this from Dinger documentation
        self.public_key = RSA.import_key(
            "-----BEGIN PUBLIC KEY-----\n"
            + "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCFD4IL1suUt/"
            +"TsJu6zScnvsEdLPuACgBdjX82QQf8NQlFHu2v/84dztaJEyljv3TGPuEgUftpC9OEOuEG29z7z1uOw7c9T/"
            +"luRhgRrkH7AwOj4U1+eK3T1R+8LVYATtPCkqAAiomkTU+aC5Y2vfMInZMgjX0DdKMctUur8tQtvkwIDAQAB"
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
            return None
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
        # Display the decrypted result as a UTF-8 encoded string
        return decrypted_data.decode("utf-8")

    @staticmethod
    def pay(baseurl, data, secretkey):
        """Prepares and returns the URL for payment request with encrypted payload and hash value.
        Args:
            baseurl (str): The base URL for the payment request.
            data (dict): The data to be encrypted and sent in the payment request.
            secretkey (str): The secret key used for generating HMAC-SHA256 hashes.
        Returns:
            tuple: A tuple containing the final URL, encrypted payload, and hash value.
        Raises:
            ValueError: If the secret key is not provided or if the data is not a dictionary.
        """
        # get from checkout-form page
        # encrypt
        encrypt_rsa = EncryptRSA(**data)
        encrypted_payload, hash_value = (
            encrypt_rsa.encrypt(),
            encrypt_rsa.generate_hash_value(secretkey),
        )
        # calculate hash
        # send GET request to this final url
        return (
            f"{baseurl}?{urlencode({'payload': encrypted_payload, 'hashValue': hash_value}, quote_via=quote_plus)}",
            encrypted_payload,
            hash_value,
        )
