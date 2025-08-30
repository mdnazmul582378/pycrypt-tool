import base64
import zlib
import marshal

# Custom key for encryption/decryption
CUSTOM_KEY = b'super_secret_key_12345'

def xor_encrypt(data, key):
    """Performs XOR encryption/decryption on the data."""
    key = key * (len(data) // len(key) + 1)
    return bytes(a ^ b for a, b in zip(data, key))

def encode_code(original_code):
    """Encodes Python code into a base64 string."""
    try:
        compiled = compile(original_code, '<string>', 'exec')
        marshaled = marshal.dumps(compiled)
        compressed = zlib.compress(marshaled)
        xored = xor_encrypt(compressed, CUSTOM_KEY)
        encoded = base64.b64encode(xored)
        return encoded.decode('utf-8')  # Return as string
    except Exception as e:
        return f"Error during encoding: {e}"

def decode_code(encoded_data):
    """Decodes a base64 string back into Python code."""
    try:
        decoded = base64.b64decode(encoded_data)
        xored = xor_encrypt(decoded, CUSTOM_KEY)
        decompressed = zlib.decompress(xored)
        marshaled = marshal.loads(decompressed)
        # We can't directly return the code string, so we return the marshal object
        return marshaled
    except Exception as e:
        return f"Error during decoding: {e}"
