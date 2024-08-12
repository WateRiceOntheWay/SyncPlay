import socket

def get_free_port():
    # Create a socket object
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind the socket to any free port
    s.bind(('', 0))
    # Get the port number assigned
    free_port = s.getsockname()[1]
    # Close the socket
    s.close()
    return free_port
