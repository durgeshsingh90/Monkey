import socket
import time

def send_message(ip, port, hex_msg, wait_after=2):
    # Convert hex string to bytes
    msg_bytes = bytes.fromhex(hex_msg)
    msg_len = str(len(msg_bytes)).zfill(4).encode()  # OMNIPAY-style 4 ASCII digit length

    full_msg = msg_len + msg_bytes

    print(f"Sending to {ip}:{port}...")
    with socket.create_connection((ip, int(port))) as sock:
        sock.sendall(full_msg)
        print("Message sent. Waiting for response...")

        # Optionally wait for server to respond
        time.sleep(wait_after)
        response_len_bytes = sock.recv(4)
        response_len = int(response_len_bytes.decode())
        response = sock.recv(response_len)

    print("Received response (raw bytes):", response)
    print("Response as hex:", response.hex())
    try:
        print("Response as text:", response.decode())
    except UnicodeDecodeError:
        print("Response is not plain text.")

if __name__ == "__main__":
    ip = input("Enter server IP (e.g., localhost): ").strip()
    port = input("Enter server Port (e.g., 7534): ").strip()
    hex_msg = input("Enter hex message to send: ").strip()

    send_message(ip, port, hex_msg)
