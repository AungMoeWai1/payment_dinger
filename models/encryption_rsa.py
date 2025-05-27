import base64
import hashlib
import hmac
import json

from Crypto import Random
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

SIZE = 64
CHUNK_SIZE = 128


class EncryptRSA(object):
    def __init__(self, **data):
        # Accepts data as a string
        # Convert dictionary to JSON string
        self.encoded_data = json.dumps(data).encode("utf-8")
        self.public_key = (
            "-----BEGIN PUBLIC KEY-----\n"
            + "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCFD4IL1suUt/TsJu6zScnvsEdL"
            "PuACgBdjX82QQf8NQlFHu2v/84dztaJEyljv3TGPuEgUftpC9OEOuEG29z7z1uOw7c9T/"
            "luRhgRrkH7AwOj4U1+eK3T1R+8LVYATtPCkqAAiomkTU+aC5Y2vfMInZMgjX0DdKMct"
            "Uur8tQtvkwIDAQAB" + "\n-----END PUBLIC KEY-----"
        )

    # Segmentation encryption
    def encrypt(self, public_key=None):
        if not public_key:
            public_key = RSA.import_key(self.public_key)
        elif public_key:
            public_key = RSA.import_key(public_key)
        # Check if public_key is provided
        try:
            cipher_rsa = PKCS1_v1_5.new(public_key)
            res = []
            for i in range(0, len(self.encoded_data), SIZE):
                enc_tmp = cipher_rsa.encrypt(self.encoded_data[i : i + SIZE])
                res.append(enc_tmp)
            cipher_text = b"".join(res)
        except Exception as e:
            # Handle encryption errors
            # For example, if the public key is invalid or encryption fails
            print(e)
            return None
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

    def generate_hash_value(self, secret_key):
        """Generates a HMAC-SHA256 hash of the encrypted payload using the secret key."""
        return hmac.new(
            key=secret_key.encode("utf-8"),
            msg=self.encoded_data,
            digestmod=hashlib.sha256,
        ).hexdigest()

    def generate_hash_value_b64(self, secret_key):
        """Generates a HMAC-SHA256 hash of the encrypted payload using the secret key."""
        digest_value = hmac.new(
            key=secret_key.encode("utf-8"),
            msg=self.encoded_data,
            digestmod=hashlib.sha256,
        ).digest()
        return base64.b64encode(digest_value).decode("utf-8")


if __name__ == "__main__":
    items = [
        {"name": "DiorAct Sandal", "amount": 250, "quantity": 1},
        {"name": "Aime Leon Dore", "amount": 250, "quantity": 1},
    ]
    orderid = "123456"
    data = {
        # items must be string
        "items": json.dumps(items),
        "customerName": "James",
        "totalAmount": 500,
        "merchantOrderId": orderid,
        # get from checkout-form page
        "clientId": "416be2a7-a311-315c-b590-f4372710cb60",
        "publicKey": "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDSL/M1Gl2dLwSrq98C4zynGxwhatYTODAsLTGDwY19rflhmpbACCNKXNxFzYwx+sbcDC5ezkCkqknyuCWG03P8F0AnPpdt05COHJtd/i3YGgfXrIKAPl35aY4hCm9EWmXPNnuyiXmwyi++bJjLSbLx3ctT/Asha0g2vckoPXzsCQIDAQAB",
        # get from data-dashboard page
        "merchantKey": "18rn0n3.g9ggpxI8uakfEiPo47eRU547ick",
        # your project name
        "projectName": "dinger-prebuilt-smei",
        # your account username
        "merchantName": "Wai Yan",
        "email": "waiyankyawsdk1999@gmail.com",
        "billCity": "city",
        "billAddress": "address",
        "state": "state",
        "country": "MM",
        "postalCode": "15015",
    }
    payload = {
        "clientId": "8e284c7d-cli3nt-id-1234",
        "publicKey": "MIG---QIDAQAB",
        "items": json.dumps(
            [
                {"name": "DiorAct Sandal", "amount": 250, "quantity": 1},
                {"name": "Aime Leon Dore", "amount": 250, "quantity": 1},
            ]
        ),
        "customerName": "James",
        "totalAmount": 2200,
        "merchantOrderId": "test-123456",
        "merchantKey": "bvb9jto---",
        "projectName": "smei_prebuilt_form",
        "merchantName": "Wai Yan",
    }
    encryption_rsa = EncryptRSA(**data)
    private_key, public_key = encryption_rsa.generate_rsa_key()
    payload_encrypt = encryption_rsa.encrypt(public_key=public_key)
    print("Encrypted Payload:", payload_encrypt)

    decrypted_data = encryption_rsa.decrypt(
        encrypted_payload=payload_encrypt, private_key=private_key
    )
    # Display the decrypted result as a UTF-8 encoded string
    print("Encrypted vs Decrypted value match :", json.dumps(data) == decrypted_data)
    print("Decrypted:", decrypted_data)
