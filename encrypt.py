import zlib
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


def encrypt(plain_text: str, password: str):

    compressed_data = zlib.compress(plain_text.encode('utf-8'))
    
    salt = 16 * b'\x00'
    iv = 16 * b'\x00'

    # use the Scrypt KDF to get a private key from the password
    private_key = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)

    cipher = AES.new(private_key, AES.MODE_CBC, iv=iv)
    cipher_text = cipher.encrypt(pad(compressed_data, AES.block_size))

    return cipher_text

def decrypt(cipher_text, password):

    salt = 16 * b'\x00'
    iv = 16 * b'\x00'

    # Fix padding
    mxlen = len(cipher_text) - (len(cipher_text) % AES.block_size)
    cipher_text = cipher_text[:mxlen]

    private_key = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)

    cipher = AES.new(private_key, AES.MODE_CBC, iv=iv)
    decrypted = cipher.decrypt(cipher_text)
    decrypted = unpad(decrypted, AES.block_size)

    plain_text = zlib.decompress(decrypted).decode('utf-8')

    return plain_text