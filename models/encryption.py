import json
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import requests
import hashlib
import hmac
from urllib.parse import urlencode, quote_plus


class EncryptRSA:

    def __init__(self, data: str):
        # Get this from Dinger documentation
        self.public_key = RSA.import_key("-----BEGIN PUBLIC KEY-----\n"
                                    +"MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCFD4IL1suUt/TsJu6zScnvsEdLPuACgBdjX82QQf8NQlFHu2v/84dztaJEyljv3TGPuEgUftpC9OEOuEG29z7z1uOw7c9T/luRhgRrkH7AwOj4U1+eK3T1R+8LVYATtPCkqAAiomkTU+aC5Y2vfMInZMgjX0DdKMctUur8tQtvkwIDAQAB"
                                    + "\n-----END PUBLIC KEY-----"
                                    )
        self.message = data.encode()

    def encrypt(self):
        try:
            cipher_rsa = PKCS1_v1_5.new(self.public_key)
            res = []
            for i in range(0, len(self.message), 64):
                enc_tmp = cipher_rsa.encrypt(self.message[i: i + 64])
                res.append(enc_tmp)
                cipher_text = b"".join(res)
        except Exception as e:
            print(e)
        else:
            return base64.b64encode(cipher_text).decode()

    @staticmethod
    def pay(baseurl, data, secretkey):
        value = json.dumps(data)
        # get from checkout-form page
        secretkey = "1be2e692d3a1d80b8e9e3e665028b6f7"
        # encrypt
        encryptedPayload = EncryptRSA(value).encrypt()
        # calculate hash
        hashValue = hmac.new(secretkey.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()
        # send GET request to this final url
        url = f"https://form.dinger.asia?{urlencode({'payload': encryptedPayload, 'hashValue': hashValue}, quote_via=quote_plus)}"
        return url,encryptedPayload,hashValue
