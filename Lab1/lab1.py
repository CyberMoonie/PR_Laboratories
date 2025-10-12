import socket
import os
import sys
from datetime import datetime

class HTTPFileServer:
    def __init__(self, directory, port=8000):
        self.directory = os.path.abspath(directory)
        self.port = port
        
    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', self.port))
        server_socket.listen(5)
        
        print(f"HTTP Server started on http://localhost:{self.port}")
        print(f"Serving directory: {self.directory}")
        
        try:
            while True:
                # Accept connection
                client_socket, client_address = server_socket.accept()
                print(f"Connection from {client_address}")
                
                # Handle one request at a time
                self.handle_request(client_socket)
                
        except KeyboardInterrupt:
            print("\nServer stopped")
        finally:
            server_socket.close()
    
    def handle_request(self, client_socket):
        try:
            # Receive request
            request_data = client_socket.recv(1024).decode('utf-8')
            if not request_data:
                return
            
            # Parse first line: GET /path HTTP/1.1
            request_line = request_data.split('\n')[0].strip()
            method, path, version = request_line.split()
            
            print(f"Request: {method} {path}")
            
            # Build file path
            if path == '/':
                file_path = self.directory
            else:
                file_path = os.path.join(self.directory, path.lstrip('/'))
            
            # Security check - stay within directory
            file_path = os.path.abspath(file_path)
            if not file_path.startswith(self.directory):
                self.send_error(client_socket, 403, "Forbidden")
                return
            
            # Serve file or directory
            if os.path.isfile(file_path):
                self.serve_file(client_socket, file_path)
            elif os.path.isdir(file_path):
                self.serve_directory(client_socket, file_path, path)
            else:
                self.send_error(client_socket, 404, "Not Found")
                
        except Exception as e:
            print(f"Error: {e}")
            self.send_error(client_socket, 500, "Internal Server Error")
        finally:
            client_socket.close()
    
    def serve_file(self, client_socket, file_path):
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Determine content type based on extension
            if file_path.endswith('.html'):
                content_type = 'text/html'
            elif file_path.endswith('.png'):
                content_type = 'image/png'
            elif file_path.endswith('.pdf'):
                content_type = 'application/pdf'
            else:
                content_type = 'application/octet-stream'
            
            # Send HTTP response
            response_header = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: {content_type}\r\n"
                f"Content-Length: {len(content)}\r\n"
                f"\r\n"
            )
            
            client_socket.send(response_header.encode('utf-8'))
            client_socket.send(content)
            
            print(f"Served file: {os.path.basename(file_path)}")
            
        except Exception as e:
            print(f"Error serving file: {e}")
    
    def serve_directory(self, client_socket, dir_path, url_path):
        try:
            # Get directory contents
            items = []
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                if os.path.isdir(item_path):
                    items.append(f'<li><a href="{url_path.rstrip("/")}/{item}/">{item}/</a></li>')
                else:
                    items.append(f'<li><a href="{url_path.rstrip("/")}/{item}">{item}</a></li>')
            
            # Generate HTML page
            html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>Directory listing for {url_path}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        ul {{ list-style-type: none; }}
        li {{ margin: 5px 0; }}
        a {{ text-decoration: none; color: #0066cc; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>Directory listing for {url_path}</h1>
    <ul>
        {''.join(items)}
    </ul>
</body>
</html>'''
            
            # Send HTTP response
            response_header = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: text/html\r\n"
                f"Content-Length: {len(html_content.encode('utf-8'))}\r\n"
                f"\r\n"
            )
            
            client_socket.send(response_header.encode('utf-8'))
            client_socket.send(html_content.encode('utf-8'))
            
            print(f"Served directory: {dir_path}")
            
        except Exception as e:
            print(f"Error serving directory: {e}")
    
    def send_error(self, client_socket, code, message):
        html_content = f'''<!DOCTYPE html>
<html>
<head><title>{code} {message}</title></head>
<body>
    <h1>{code} {message}</h1>
    <p>The requested resource could not be found.</p>
</body>
</html>'''
        
        response_header = (
            f"HTTP/1.1 {code} {message}\r\n"
            f"Content-Type: text/html\r\n"
            f"Content-Length: {len(html_content.encode('utf-8'))}\r\n"
            f"\r\n"
        )
        
        client_socket.send(response_header.encode('utf-8'))
        client_socket.send(html_content.encode('utf-8'))

def main():
    if len(sys.argv) != 2:
        print("Usage: python lab1.py <directory_to_serve>")
        sys.exit(1)
    
    directory = sys.argv[1]
    
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist")
        sys.exit(1)
    
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a directory")
        sys.exit(1)
    
    # Start server
    server = HTTPFileServer(directory)
    server.start()

if __name__ == "__main__":
    main()