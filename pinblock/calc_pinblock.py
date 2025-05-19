from Crypto.Cipher import DES3
from binascii import unhexlify, hexlify


def iso0_pin_block(pin: str, pan: str) -> bytes:
    # Format the PIN block
    pin_len = len(pin)
    pin_block_str = f'{pin_len:02d}' + pin + 'F' * (16 - (2 + pin_len))
    pin_block = unhexlify(pin_block_str)

    # Format the PAN block (right 12 digits before the check digit)
    pan_digits = ''.join(filter(str.isdigit, pan))[-13:-1]
    pan_block_str = '0000' + pan_digits
    pan_block = unhexlify(pan_block_str)

    # XOR PIN block and PAN block
    final_block = bytes([a ^ b for a, b in zip(pin_block, pan_block)])
    return final_block


def decrypt_pin_block(encrypted_pin_block: str, zpk_hex: str) -> bytes:
    key = unhexlify(zpk_hex)
    cipher = DES3.new(key, DES3.MODE_ECB)
    return cipher.decrypt(unhexlify(encrypted_pin_block))


def encrypt_pin_block(pin_block: bytes, zpk_hex: str) -> str:
    key = unhexlify(zpk_hex)
    cipher = DES3.new(key, DES3.MODE_ECB)
    encrypted = cipher.encrypt(pin_block)
    return hexlify(encrypted).upper().decode()


# Example data
pan = '1234567890123456'
pin = '1234'

# Zone PIN Keys (double-length 3DES keys, hex-encoded)
zpk_ab = '0123456789ABCDEFFEDCBA9876543210'  # A-B ZPK
zpk_bc = '89ABCDEF01234567FEDCBA9876543210'  # B-C ZPK

# Suppose this is the encrypted PIN block from A (hex string)
# To simulate, we can first calculate it ourselves:
clear_pin_block = iso0_pin_block(pin, pan)
encrypted_from_a = encrypt_pin_block(clear_pin_block, zpk_ab)

print("Encrypted PIN block from A:", encrypted_from_a)

# Now, simulate B decrypting and re-encrypting for C:
decrypted = decrypt_pin_block(encrypted_from_a, zpk_ab)
re_encrypted_for_c = encrypt_pin_block(decrypted, zpk_bc)

print("Encrypted PIN block for C:", re_encrypted_for_c)
