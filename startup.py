import os

import cryptography.fernet as fer

SCRIPT_PATH = os.path.dirname(__file__)
TOKEN_PATH = SCRIPT_PATH + "/credentials/token.tokenfile"
KEY_PATH = SCRIPT_PATH + "/credentials/key.keyfile"

def decrypt_token(token_path: str, key_path: str) -> str:
    """Return the decrypted bot token.

    The function fetches the encrypted token and the key to decrypt it.
    It then decrypts the token and returns the version that the Discord
    API will accept as a valid token.

    Parameters
    ----------
    token_path: `str` The file path that describes the location of the
    encrypted token file.
    key_path: `str` The file path that describes the location of the
    key file.
    """
    # Get token and decryption key
    with open(key_path, "rb") as key_f:
        key = fer.Fernet(key_f.read())
    with open(token_path, "rb") as token_f:
        token_enc = token_f.read()
    
    # Decrypt token and convert to str
    token_dec = key.decrypt(token_enc)  # token_dec is a bytes object
    token_dec = token_dec.decode("utf-8")
    return token_dec

def write_new_key(key_path: str):
    """Generate a new encryption key and write it to the key file."""
    with open(key_path, "wb") as key_f:
        new_key = fer.Fernet.generate_key()
        key_f.write(new_key)

def encrypt_new_token(token: str, token_path: str, key_path: str):
    """Encrypt a new bot token and write it to the token file.

    The function accepts a token (this is mostly for after a token reset),
    encrypts it with the key from the key file and writes it to the token
    file.

    Parameters
    ----------
    token: `str` The Discord API token to encrypt.
    token_path: `str` The file path that describes the location of the
    encrypted token file.
    key_path: `str` The file path that describes the location of the
    key file.
    """
    # Get key for encryption
    with open(key_path, "rb") as key_f:
        key = fer.Fernet(key_f.read())
    
    with open(token_path, "wb") as token_f:
        token = bytes(token, "utf-8")  # Convert to bytes for encryption
        token_enc = key.encrypt(token)
        token_f.write(token_enc)