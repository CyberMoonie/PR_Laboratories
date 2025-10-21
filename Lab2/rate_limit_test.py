"""
Rate Limit Test - Rapid Fire Requests
Sends requests as fast as possible to trigger rate limiting
"""
import socket
import time

def make_quick_request(host, port, path):
    """Make a fast HTTP request"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect((host, port))
        
        request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\n\r\n"
        sock.send(request.encode())
        
        response = sock.recv(1024)
        sock.close()
        
        if b"429" in response or b"Too Many Requests" in response:
            return "BLOCKED"
        elif b"200 OK" in response:
            return "SUCCESS"
        else:
            return "UNKNOWN"
    except Exception as e:
        if "10054" in str(e):
            return "BLOCKED"
        return f"ERROR: {e}"

def test_rate_limit(host='localhost', port=8000, num_requests=20):
    """Test rate limiting with rapid sequential requests"""
    print(f"\n{'='*70}")
    print(f"RATE LIMIT TEST - Sending {num_requests} requests as fast as possible")
    print(f"Server: {host}:{port}")
    print(f"Expected: Only 5 requests succeed per second")
    print(f"{'='*70}\n")
    
    results = []
    start = time.time()
    
    # Send requests as fast as possible in a tight loop
    for i in range(num_requests):
        result = make_quick_request(host, port, '/index.html')
        elapsed = time.time() - start
        results.append((i+1, result, elapsed))
        
        status_icon = "✅" if result == "SUCCESS" else "❌"
        print(f"{status_icon} Request {i+1:3d}: {result:10s} (at {elapsed:.3f}s)")
    
    total_time = time.time() - start
    
    # Summary
    print(f"\n{'='*70}")
    print("RESULTS:")
    print(f"{'='*70}")
    
    success = sum(1 for r in results if r[1] == "SUCCESS")
    blocked = sum(1 for r in results if r[1] == "BLOCKED")
    errors = num_requests - success - blocked
    
    print(f"Total requests: {num_requests}")
    print(f"Successful:     {success}")
    print(f"Rate limited:   {blocked}")
    print(f"Errors:         {errors}")
    print(f"Total time:     {total_time:.3f}s")
    print(f"Rate:           {num_requests/total_time:.2f} requests/second")
    print(f"\n💡 With 5 req/s limit, expect ~{int(total_time * 5)} successful requests")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║              RATE LIMITER TEST - RAPID FIRE                      ║
║  Sends requests sequentially as fast as possible                 ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    input("Make sure server is running on port 8000, then press Enter...")
    
    test_rate_limit('localhost', 8000, num_requests=10)
