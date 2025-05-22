# import hashlib
# import hmac
# import json
# import base64
# from Crypto.PublicKey import RSA
#
# from Cryptodome.Cipher import PKCS1_v1_5
#
# # Segmentation encryption
# def encrypt(data,public_key):
#     value = json.dumps(data)
#     message = value.encode()
#     public_key = RSA.import_key(public_key)
#
#     import pdb;pdb.set_trace()
#     try:
#         cipher_rsa = PKCS1_v1_5.new(public_key)
#         res = []
#         for i in range(0, len(message), 64):
#             enc_tmp = cipher_rsa.encrypt(message[i:i + 64])
#             res.append(enc_tmp)
#         cipher_text = b''.join(res)
#     except Exception as e:
#         print(e)
#     else:
#         return base64.b64encode(cipher_text).decode()
#
# def generate_hash_value(payload, secret_key):
#     return hmac.new(secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
