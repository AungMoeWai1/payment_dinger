import base64
from Crypto.Cipher import AES

def unpad(data):
    """Remove PKCS7 padding from the data."""
    return data[0:-ord(data[-1])]

def decrypt(key, decr_data):
    """Decrypts the given data using AES in ECB mode with PKCS7 padding."""
    res = base64.decodebytes(decr_data.encode("utf8"))
    aes = AES.new(key.encode('utf-8'), AES.MODE_ECB)
    msg = aes.decrypt(res).decode("utf8")
    return unpad(msg)
