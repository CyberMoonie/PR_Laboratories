import threading
import time
from collections import defaultdict

# Shared counter (UNSAFE - will have race condition)
unsafe_counter = defaultdict(int)

# Shared counter with lock (SAFE)
safe_counter = defaultdict(int)
counter_lock = threading.Lock()

def unsafe_increment(file_path, iterations):
    """Increment counter WITHOUT lock - demonstrates race condition"""
    for _ in range(iterations):
        # Read current value
        current = unsafe_counter[file_path]
        
        # Add artificial delay to force interlacing
        time.sleep(0.0001)
        
        # Write new value
        unsafe_counter[file_path] = current + 1

def safe_increment(file_path, iterations):
    """Increment counter WITH lock - prevents race condition"""
    for _ in range(iterations):
        with counter_lock:
            current = safe_counter[file_path]
            time.sleep(0.0001)  # Same delay as unsafe version
            safe_counter[file_path] = current + 1

def test_race_condition():
    """Demonstrate race condition with multiple threads"""
    print("="*70)
    print("RACE CONDITION DEMONSTRATION")
    print("="*70)
    
    file_path = "/test_file.html"
    num_threads = 10
    iterations_per_thread = 100
    expected_count = num_threads * iterations_per_thread
    
    # Test 1: WITHOUT lock (race condition)
    print(f"\n1. WITHOUT LOCK (Naive Implementation):")
    print(f"   - Launching {num_threads} threads")
    print(f"   - Each increments counter {iterations_per_thread} times")
    print(f"   - Expected total: {expected_count}")
    print(f"   - Processing...")
    
    unsafe_counter.clear()
    threads = []
    start = time.time()
    
    for _ in range(num_threads):
        thread = threading.Thread(target=unsafe_increment, args=(file_path, iterations_per_thread))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    unsafe_time = time.time() - start
    unsafe_result = unsafe_counter[file_path]
    unsafe_lost = expected_count - unsafe_result
    
    print(f"Result: {unsafe_result} (Lost {unsafe_lost} updates!)")
    print(f"Time: {unsafe_time:.3f}s")
    print(f"RACE CONDITION: Multiple threads overwrote each other's updates!")
    
    # Test 2: WITH lock (no race condition)
    print(f"\n2. WITH LOCK (Thread-Safe Implementation):")
    print(f"   - Launching {num_threads} threads")
    print(f"   - Each increments counter {iterations_per_thread} times")
    print(f"   - Expected total: {expected_count}")
    print(f"   - Processing...")
    
    safe_counter.clear()
    threads = []
    start = time.time()
    
    for _ in range(num_threads):
        thread = threading.Thread(target=safe_increment, args=(file_path, iterations_per_thread))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    safe_time = time.time() - start
    safe_result = safe_counter[file_path]
    
    print(f"Result: {safe_result}")
    print(f"Time: {safe_time:.3f}s")
    print(f"NO RACE CONDITION: Lock prevented concurrent access!")

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════╗
║              RACE CONDITION DEMONSTRATION                          ║
║  Shows why we need synchronization in multithreaded programs       ║
╚════════════════════════════════════════════════════════════════════╝
""")
    
    test_race_condition()
