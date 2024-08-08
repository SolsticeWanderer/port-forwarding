import socket
import sqlite3
import threading


class PortForwarding:
    """Class for setting up port forwarding based on database configurations."""

    def __init__(self, setup, error):
        self.setup = setup
        self.error = error
        self.lock = threading.Lock()

        # Fetch port forwarding settings from the database
        settings = self.fetch_db()

        # Start a new thread for each forwarding rule
        for setting in settings:
            thread = threading.Thread(target=self.server, args=setting)
            thread.daemon = True  # Daemon threads will shut down when the program exits
            thread.start()

        # Block the main thread to keep the program running
        self.lock.acquire()

    def fetch_db(self):
        """Fetch port forwarding rules from the database."""
        con = sqlite3.connect("./test.db")
        cur = con.cursor()
        cur.execute("SELECT ip, port, listen_port FROM test")
        data = cur.fetchall()
        con.close()
        return data

    def parse(self, setup):
        """Parse the configuration file for port forwarding rules."""
        settings = []
        with open(setup, 'r') as f:
            for line in f:
                parts = line.split()
                settings.append((parts[0], int(parts[1]), int(parts[2])))
        return settings

    def server(self, ip, port, listen_port):
        """Set up the server to listen on the specified port and forward traffic."""
        try:
            dock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dock_socket.bind(('', listen_port))
            dock_socket.listen(5)
            print(f"Listening on port {listen_port}...")

            while True:
                client_socket, address = dock_socket.accept()
                print(f"Client {address} connected -> forwarding to {ip}:{port}")
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.connect((ip, port))

                # Start threads to handle the forwarding
                threading.Thread(target=self.forward, args=(client_socket, server_socket)).start()
                threading.Thread(target=self.forward, args=(server_socket, client_socket)).start()

        except Exception as e:
            print(f"Error: {e}")
        finally:
            dock_socket.close()

    def forward(self, source, destination):
        """Forward data between source and destination sockets."""
        try:
            while True:
                data = source.recv(1024)
                if not data:
                    break
                destination.sendall(data)
        except Exception as e:
            print(f"Forwarding error: {e}")
        finally:
            source.close()
            destination.close()


if __name__ == '__main__':
    demon = PortForwarding('proxy.ini', 'error.log')
