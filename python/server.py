import socket

def start_server():
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Use localhost
    host = 'localhost'
    port = 7534

    # Bind to the port
    server_socket.bind((host, port))

    # Start listening for incoming connections (max 5 queued connections)
    server_socket.listen(5)

    print(f"Server is listening on port {port}")

    # Establish a connection
    client_socket, addr = server_socket.accept()

    print(f"Got a connection from {addr}")

    while True:
        # Receive a message (buffer size is 1024 bytes)
        message = client_socket.recv(1024)
        if not message:
            # If no message is received, break the loop
            break
        
        message_str = message.decode('utf-8')
        bytes_received = len(message)
        print(f"Received message: {message_str}")
        print(f"Number of bytes received: {bytes_received}")

    # Close the connection
    client_socket.close()
    print("Connection closed")

if __name__ == "__main__":
    start_server()
