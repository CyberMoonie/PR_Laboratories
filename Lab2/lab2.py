import socket
import threading
import os
import sys
import time
from collections import defaultdict

class MultithreadedHTTPServer:
    def __init__(self, directory, port=8000):
        self.directory = os.path.abspath(directory)
        self.port = port
        self.request_counts = defaultdict(int)
        self.client_requests = defaultdict(list)
        self.max_requests_per_second = 5
        self.lock = threading.Lock()
        
    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', self.port))
        server_socket.listen(10)
        
        print(f"Multithreaded HTTP Server started on http://localhost:{self.port}")
        print(f"Serving directory: {self.directory}")
        
        try:
            while True:
                client_socket, client_address = server_socket.accept()
                print(f"Connection from {client_address}")
                
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except KeyboardInterrupt:
            print("\nServer stopped")
        finally:
            server_socket.close()
    
    def handle_client(self, client_socket, client_address):
        try:
            if not self.check_rate_limit(client_address[0]):
                self.send_error(client_socket, 429, "Too Many Requests")
                return
            
            request_data = client_socket.recv(1024).decode('utf-8')
            if not request_data:
                return
                
            request_line = request_data.split('\n')[0].strip()
            parts = request_line.split()
            if len(parts) < 3:
                return
                
            method, path, version = parts[0], parts[1], parts[2]
            print(f"[Thread-{threading.current_thread().ident}] {method} {path}")
            
            with self.lock:
                self.request_counts[path] += 1
            
            if path == '/':
                file_path = self.directory
            else:
                file_path = os.path.join(self.directory, path.lstrip('/'))
            
            file_path = os.path.abspath(file_path)
            if not file_path.startswith(self.directory):
                self.send_error(client_socket, 403, "Forbidden")
                return
            
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
    
    def check_rate_limit(self, client_ip):
        current_time = time.time()
        
        with self.lock:
            self.client_requests[client_ip] = [
                req_time for req_time in self.client_requests[client_ip]
                if current_time - req_time < 1.0
            ]
            
            if len(self.client_requests[client_ip]) >= self.max_requests_per_second:
                return False
            
            self.client_requests[client_ip].append(current_time)
            return True
    
    def serve_file(self, client_socket, file_path):
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            if file_path.endswith('.html'):
                content_type = 'text/html'
            elif file_path.endswith('.pdf'):
                content_type = 'application/pdf'
            elif file_path.endswith('.png'):
                content_type = 'image/png'
            else:
                content_type = 'application/octet-stream'
            
            response = f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n"
            client_socket.send(response.encode())
            client_socket.send(content)
            
        except Exception as e:
            print(f"Error serving file: {e}")
    
    def serve_directory(self, client_socket, dir_path, url_path):
        try:
            files = []
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                item_url = f"{url_path.rstrip('/')}/{item}"
                
                with self.lock:
                    if os.path.isdir(item_path):
                        hits = self.request_counts.get(item_url + '/', 0)
                        files.append(f'<tr><td><a href="{item_url}/">{item}/</a></td><td>{hits}</td></tr>')
                    else:
                        hits = self.request_counts.get(item_url, 0)
                        files.append(f'<tr><td><a href="{item_url}">{item}</a></td><td>{hits}</td></tr>')
            
            html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Directory listing for {url_path}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ text-align: left; padding: 12px; border: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
        a {{ text-decoration: none; color: #0066cc; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>Directory listing for {url_path}</h1>
    <table>
        <tr><th>File / Directory</th><th>Hits</th></tr>
        {''.join(files)}
    </table>
    <p><em>Multithreaded HTTP Server - Lab 2</em></p>
</body>
</html>'''
            
            response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: {len(html.encode())}\r\n\r\n"
            client_socket.send(response.encode())
            client_socket.send(html.encode())
            
        except Exception as e:
            print(f"Error serving directory: {e}")
    
    def send_error(self, client_socket, code, message):
        html = f"<html><body><h1>{code} {message}</h1></body></html>"
        response = f"HTTP/1.1 {code} {message}\r\nContent-Type: text/html\r\nContent-Length: {len(html)}\r\n\r\n"
        client_socket.send(response.encode())
        client_socket.send(html.encode())

def main():
    if len(sys.argv) != 2:
        print("Usage: python lab2.py <directory_to_serve>")
        sys.exit(1)
    
    directory = sys.argv[1]
    if not os.path.exists(directory) or not os.path.isdir(directory):
        print(f"Error: Directory '{directory}' does not exist")
        sys.exit(1)
    
    server = MultithreadedHTTPServer(directory)
    server.start()

if __name__ == "__main__":
    main()
