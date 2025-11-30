import time
import statistics
from concurrent.futures import ThreadPoolExecutor
from typing import List
import requests
import matplotlib.pyplot as plt

# Configuration
LEADER_URL = "http://localhost:8001"
FOLLOWER_URLS = [
    f"http://localhost:{8002 + i}" for i in range(5)
]


def set_quorum(quorum_size: int) -> None:
    """Configure the write quorum on the leader."""
    requests.post(f"{LEADER_URL}/config", json={"quorum": quorum_size})


def write_operation(key: str, value: str) -> float:
    """
    Perform a write operation and return latency in seconds.
    Returns None if the operation fails.
    """
    start_time = time.time()
    try:
        response = requests.post(
            f"{LEADER_URL}/write",
            json={"key": key, "value": value}
        )
        response.raise_for_status()
        return time.time() - start_time  # Return in seconds
    except Exception as e:
        print(f"Write error: {e}")
        return None


def clear_all_stores() -> None:
    """Clear data from leader and all followers."""
    print("Clearing all stores...")
    
    # Clear leader
    try:
        requests.delete(f"{LEADER_URL}/clear").raise_for_status()
        print("  Leader cleared")
    except Exception as e:
        print(f"  Failed to clear leader: {e}")
    
    # Clear all followers
    for idx, follower_url in enumerate(FOLLOWER_URLS, 1):
        try:
            requests.delete(f"{follower_url}/clear").raise_for_status()
            print(f"  Follower {idx} cleared")
        except Exception as e:
            print(f"  Failed to clear follower {idx}: {e}")


def check_consistency() -> None:
    """Verify that all followers have consistent data with the leader."""
    print("\n--- Checking Consistency ---")
    leader_data = requests.get(f"{LEADER_URL}/read_all").json()
    print(f"Leader has {len(leader_data)} keys")
    
    all_consistent = True
    for idx, follower_url in enumerate(FOLLOWER_URLS, 1):
        try:
            follower_data = requests.get(f"{follower_url}/read_all").json()
            
            if leader_data == follower_data:
                print(f"Follower {idx}: MATCH ({len(follower_data)} keys)")
            else:
                print(f"Follower {idx}: MISMATCH "
                      f"(has {len(follower_data)} keys, expected {len(leader_data)})")
                
                # Show mismatch details
                missing = set(leader_data.keys()) - set(follower_data.keys())
                extra = set(follower_data.keys()) - set(leader_data.keys())
                
                if missing:
                    print(f"  Missing keys: {list(missing)[:5]}...")
                if extra:
                    print(f"  Extra keys: {list(extra)[:5]}...")
                all_consistent = False
        except Exception as e:
            print(f"Follower {idx}: UNREACHABLE ({e})")
            all_consistent = False
    
    print("SUCCESS: All replicas are consistent with Leader." if all_consistent
          else "FAILURE: Inconsistencies found.")


def run_benchmark(quorum_size: int, total_writes: int = 100, 
                  concurrency: int = 10) -> dict:
    """
    Run benchmark for a specific quorum size.
    Returns dict with mean, median, p95, p99 latencies in seconds.
    """
    print(f"--- Testing Quorum: {quorum_size} ---")
    set_quorum(quorum_size)
    
    keys = [f"key_{i}" for i in range(10)]
    latencies = []
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(write_operation, keys[i % 10], f"val_{i}")
            for i in range(total_writes)
        ]
        
        for future in futures:
            latency = future.result()
            if latency is not None:
                latencies.append(latency)
    
    # Calculate percentiles
    latencies_sorted = sorted(latencies)
    mean_latency = statistics.mean(latencies)
    median_latency = statistics.median(latencies)
    p95_latency = latencies_sorted[int(len(latencies_sorted) * 0.95)]
    p99_latency = latencies_sorted[int(len(latencies_sorted) * 0.99)]
    
    print(f"Mean: {mean_latency:.4f} s, Median: {median_latency:.4f} s")
    print(f"P95: {p95_latency:.4f} s, P99: {p99_latency:.4f} s")
    
    return {
        "mean": mean_latency,
        "median": median_latency,
        "p95": p95_latency,
        "p99": p99_latency
    }


def plot_results(quorums: List[int], results: List[dict]) -> None:
    """Generate and save performance plot with percentiles."""
    plt.figure(figsize=(10, 6))
    
    # Extract metrics
    means = [r["mean"] for r in results]
    medians = [r["median"] for r in results]
    p95s = [r["p95"] for r in results]
    p99s = [r["p99"] for r in results]
    
    # Plot all metrics
    plt.plot(quorums, means, marker='o', linewidth=2, markersize=8, label='mean')
    plt.plot(quorums, medians, marker='s', linewidth=2, markersize=8, label='median')
    plt.plot(quorums, p95s, marker='^', linewidth=2, markersize=8, label='p95')
    plt.plot(quorums, p99s, marker='d', linewidth=2, markersize=8, label='p99')
    
    plt.title('Quorum vs. Latency, random delay in range [0, 1000ms]', fontsize=14)
    plt.xlabel('Quorum value', fontsize=12)
    plt.ylabel('Latency (s)', fontsize=12)
    plt.legend(loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('performance_plot.png', dpi=300)
    print("\nPlot saved to performance_plot.png")
    plt.show()


def main():
    """Main benchmark execution."""
    print("Waiting for services to be ready...")
    time.sleep(5)
    
    quorums = [1, 2, 3, 4, 5]
    results = []
    
    # Run benchmarks for each quorum size
    for quorum in quorums:
        result = run_benchmark(quorum)
        results.append(result)
        
        print("Waiting for background replication to complete...")
        time.sleep(3)
        
        clear_all_stores()
        print()
    
    # Final consistency check
    print("\n=== Running final writes for consistency check ===")
    set_quorum(5)
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(write_operation, f"test_key_{i}", f"test_val_{i}")
            for i in range(50)
        ]
        for future in futures:
            future.result()
    
    print("\nWaiting for all final replications to complete...")
    time.sleep(5)
    
    check_consistency()
    plot_results(quorums, results)


if __name__ == "__main__":
    main()
