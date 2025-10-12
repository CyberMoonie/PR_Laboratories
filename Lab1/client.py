import socket
import sys
import os

class HTTPClient:
    def __init__(self, server_host, server_port, save_directory):
        self.server_host = server_host
        self.server_port = server_port
        self.save_directory = save_directory
        
        # Create save directory if it doesn't exist
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)
    
    def download_file(self, file_path):
        try:
            # Create TCP socket
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.server_host, self.server_port))
            
            # Send HTTP GET request
            request = f"GET {file_path} HTTP/1.1\r\nHost: {self.server_host}\r\n\r\n"
            client_socket.send(request.encode('utf-8'))
            
            # Receive response
            response = b""
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                response += data
            
            client_socket.close()
            
            # Parse response
            header_end = response.find(b'\r\n\r\n')
            if header_end == -1:
                print("Error: Invalid HTTP response")
                return False
            
            headers = response[:header_end].decode('utf-8')
            body = response[header_end + 4:]
            
            # Check status code
            status_line = headers.split('\r\n')[0]
            if "200 OK" not in status_line:
                print(f"Server error: {status_line}")
                return False
            
            # Get content type
            content_type = "text/html"  # default
            for line in headers.split('\r\n'):
                if line.lower().startswith('content-type:'):
                    content_type = line.split(':', 1)[1].strip()
                    break
            
            # Handle different file types
            if 'text/html' in content_type:
                # HTML (page, directory listing): print the body as-is
                print("=== HTML Response ===")
                print(body.decode('utf-8'))
                return True
            else:
                # PNG, PDF: save the file in the specified directory
                filename = os.path.basename(file_path.rstrip('/'))
                if not filename:
                    filename = "downloaded_file"
                
                save_path = os.path.join(self.save_directory, filename)
                
                with open(save_path, 'wb') as f:
                    f.write(body)
                
                print(f"File saved: {save_path} ({len(body)} bytes)")
                return True
                
        except Exception as e:
            print(f"Error downloading {file_path}: {e}")
            return False

def main():
    if len(sys.argv) != 4:
        print("Usage: python client.py server_host server_port filename")
        print("Example: python client.py localhost 8000 /sample.pdf")
        sys.exit(1)
    
    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    filename = sys.argv[3]
    save_directory = "./downloads"
    
    print(f"Connecting to {server_host}:{server_port}")
    print(f"Requesting: {filename}")
    print(f"Save directory: {save_directory}")
    
    client = HTTPClient(server_host, server_port, save_directory)
    
    if client.download_file(filename):
        print("Download completed successfully!")
    else:
        print("Download failed!")

if __name__ == "__main__":
    main()