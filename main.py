import socket


def start_server():
    host = "127.0.0.1"
    port = 80

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"Server listening on {host}:{port}")

    while True:
        client_socket, address = server_socket.accept()
        print(f"Connection from {address} has been established.")

        request = client_socket.recv(1024).decode()
        print(f"Received request: {request}")

        response = "HTTP/1.1 200 OK\r\n\r\nHello, client!"
        client_socket.send(response.encode())

        client_socket.close()


if __name__ == "__main__":
    start_server()
