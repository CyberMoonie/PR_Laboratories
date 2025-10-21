import socket
import threading
import time

def make_request(server_host, server_port, path, request_num, results):
    """Make a single HTTP request and record the time"""
    start_time = time.time()
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_host, server_port))
        
        request = f"GET {path} HTTP/1.1\r\nHost: {server_host}\r\n\r\n"
        client_socket.send(request.encode('utf-8'))
        
        response = b""
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            response += data
        
        client_socket.close()
        elapsed = time.time() - start_time
        results.append((request_num, elapsed, "Success"))
        print(f"Request {request_num}: {elapsed:.3f}s")
        
    except Exception as e:
        elapsed = time.time() - start_time
        results.append((request_num, elapsed, f"Error: {e}"))
        print(f"Request {request_num}: Failed - {e}")

def test_server(server_host, server_port, num_requests=10):
    """Test server with concurrent requests"""
    print(f"\n{'='*60}")
    print(f"Testing server at {server_host}:{server_port}")
    print(f"Making {num_requests} concurrent requests...")
    print(f"{'='*60}\n")
    
    results = []
    threads = []
    
    overall_start = time.time()
    
    # Launch all requests simultaneously
    for i in range(num_requests):
        thread = threading.Thread(
            target=make_request,
            args=(server_host, server_port, '/index.html', i+1, results)
        )
        threads.append(thread)
        thread.start()
    
    # Wait for all to complete
    for thread in threads:
        thread.join()
    
    overall_time = time.time() - overall_start
    
    print(f"\n{'='*60}")
    print(f"RESULTS:")
    print(f"{'='*60}")
    print(f"Total time: {overall_time:.3f}s")
    print(f"Successful requests: {sum(1 for r in results if r[2] == 'Success')}/{num_requests}")
    
    if results:
        avg_time = sum(r[1] for r in results) / len(results)
        print(f"Average request time: {avg_time:.3f}s")
        print(f"Throughput: {num_requests/overall_time:.2f} requests/second")
    
    return overall_time

if __name__ == "__main__":

    
    input("Press Enter when your server is ready...")
    
    test_server('localhost', 8000, num_requests=10)

