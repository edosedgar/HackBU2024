from encrypt import encrypt, decrypt

""" A codec for converting between plain_text and 2bit or 4bit integers to select top 4 or 16 tokens from LLM, respectively
"""

def encode(plaint_text: str, password: str, mode='2bit'):

    cipher_text = encrypt(plaint_text, password)

    if mode == '2bit':
        tokenizer_ids = _bytes_to_2bits(cipher_text)

    elif mode == '4bit':
        tokenizer_ids = _bytes_to_4bits(cipher_text)

    else:
        raise Exception('Unknown mode {mode} in NaiveStegoEncoder.encode')

    return tokenizer_ids

def decode(tokenizer_ids, password: str, mode='2bit'):
    """ decode from 2bit or 4bit integers
    """

    if mode == '2bit':
        cipher_text = _2bits_to_bytes(tokenizer_ids)

    elif mode == '4bit':
        cipher_text = _4bits_to_bytes(tokenizer_ids)

    else:
        raise Exception('Unknown mode {mode} in NaiveStegoEncoder.decode')

    plain_text = decrypt(cipher_text, password)

    return plain_text

def _bytes_to_2bits(byte_data):

    token_ids = []
    for byte in byte_data:
        for i in [6,4,2,0]: # Extract groups of two bits from left to right
            bits = (byte >> i) & 0b11
            token_ids.append(bits)

    return token_ids

def _2bits_to_bytes(token_ids):

    byte_list = bytearray()
    if len(token_ids) % 4 != 0:
        padding = (4 - len(token_ids) % 4) % 4
        token_ids += ['a'] * padding

    for i in range(0, len(token_ids), 4):
        byte = 0
        for j in range(4):
            byte |= token_ids[i + j] << (6 - j * 2)
        byte_list.append(byte)

    return bytes(byte_list)

def _bytes_to_4bits(byte_data):

    token_ids = []
    for byte in byte_data:
        for i in [4,0]: # Extract groups of two bits from left to right
            bits = (byte >> i) & 0b1111
            token_ids.append(bits)

    return token_ids

def _4bits_to_bytes(token_ids):

    byte_list = bytearray()
    if len(token_ids) % 4 != 0:
        padding = (4 - len(token_ids) % 4) % 4
        token_ids += ['a'] * padding

    for i in range(0, len(token_ids), 2):
        byte = 0
        for j in range(2):
            byte |= token_ids[i + j] << (4 - j * 4)
        byte_list.append(byte)

    return bytes(byte_list)