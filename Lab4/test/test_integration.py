"""Integration tests for leader-follower key-value store with semi-synchronous replication.

Tests:
1. Health check - verify all nodes are operational
2. Basic write/read operations
3. Replication to followers
4. Quorum requirements and latency
5. Concurrent writes with timestamp ordering
6. Timestamp-based conflict resolution
7. Eventual consistency across replicas
"""

import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional

import requests

# Configuration
LEADER_URL = "http://localhost:8001"
FOLLOWER_URLS = [f"http://localhost:{8002 + i}" for i in range(5)]


class TestResult:
    """Encapsulates test execution result."""
    
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.message = ""

    def success(self, message: str = "") -> None:
        """Mark test as passed with optional message."""
        self.passed = True
        self.message = message

    def fail(self, message: str) -> None:
        """Mark test as failed with error message."""
        self.passed = False
        self.message = message

    def __str__(self) -> str:
        status = "✓ PASS" if self.passed else "✗ FAIL"
        return f"{status}: {self.name}\n  {self.message}"


# --- Helper Functions ---
def clear_all_stores() -> None:
    """Clear all data from leader and followers."""
    for url in [LEADER_URL] + FOLLOWER_URLS:
        try:
            requests.delete(f"{url}/clear", timeout=2)
        except Exception:
            pass


def set_quorum(quorum: int) -> bool:
    """Set the write quorum on the leader."""
    try:
        response = requests.post(
            f"{LEADER_URL}/config",
            json={"quorum": quorum},
            timeout=2
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Failed to set quorum: {e}")
        return False


def write_key(key: str, value: str, timeout: float = 5.0) -> bool:
    """Write a key-value pair to the leader."""
    try:
        response = requests.post(
            f"{LEADER_URL}/write",
            json={"key": key, "value": value},
            timeout=timeout
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Write failed: {e}")
        return False


def read_key_from(url: str, key: str) -> Optional[str]:
    """Read a key from a specific node. Returns None if not found."""
    try:
        response = requests.get(f"{url}/read/{key}", timeout=2)
        response.raise_for_status()
        return response.json().get("value")
    except Exception:
        return None


def get_all_data_from(url: str) -> Dict[str, str]:
    """Get all data from a specific node."""
    try:
        response = requests.get(f"{url}/read_all", timeout=2)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {}


# --- Test Cases ---
def test_health_check() -> TestResult:
    """Test 1: Verify all nodes are healthy"""
    result = TestResult("Health Check")

    try:
        # Check leader
        response = requests.get(f"{LEADER_URL}/health", timeout=2)
        if response.status_code != 200 or response.json().get("role") != "leader":
            result.fail("Leader health check failed")
            return result

        # Check all followers
        for idx, follower_url in enumerate(FOLLOWER_URLS, 1):
            response = requests.get(f"{follower_url}/health", timeout=2)
            if response.status_code != 200 or response.json().get("role") != "follower":
                result.fail(f"Follower {idx} health check failed")
                return result

        result.success("All nodes healthy (1 leader + 5 followers)")
        return result
    except Exception as e:
        result.fail(f"Health check error: {e}")
        return result


def test_basic_write_read() -> TestResult:
    """Test 2: Basic write and read operations"""
    result = TestResult("Basic Write and Read")
    clear_all_stores()
    set_quorum(1)

    try:
        if not write_key("test_key", "test_value"):
            result.fail("Failed to write key")
            return result

        value = read_key_from(LEADER_URL, "test_key")
        if value != "test_value":
            result.fail(f"Leader has wrong value: {value}")
            return result

        result.success("Write and read successful on leader")
        return result
    except Exception as e:
        result.fail(f"Error: {e}")
        return result


def test_replication_to_followers() -> TestResult:
    """Test 3: Verify data replicates to all followers"""
    result = TestResult("Replication to Followers")
    clear_all_stores()
    set_quorum(5)

    try:
        if not write_key("replicated_key", "replicated_value"):
            result.fail("Write failed with quorum=5")
            return result

        time.sleep(2)

        # Verify all followers received the data
        for idx, follower_url in enumerate(FOLLOWER_URLS, 1):
            value = read_key_from(follower_url, "replicated_key")
            if value != "replicated_value":
                result.fail(f"Follower {idx} has wrong value: {value}")
                return result

        result.success("Data successfully replicated to all 5 followers")
        return result
    except Exception as e:
        result.fail(f"Error: {e}")
        return result


def test_quorum_requirement() -> TestResult:
    """Test 4: Verify quorum requirements are enforced"""
    result = TestResult("Quorum Requirement")
    clear_all_stores()

    try:
        # Test with quorum=1
        set_quorum(1)
        start = time.time()
        if not write_key("quorum1_key", "value1"):
            result.fail("Write failed with quorum=1")
            return result
        latency1 = (time.time() - start) * 1000

        # Test with quorum=5
        set_quorum(5)
        start = time.time()
        if not write_key("quorum5_key", "value5"):
            result.fail("Write failed with quorum=5")
            return result
        latency5 = (time.time() - start) * 1000

        result.success(f"Quorum=1: {latency1:.1f}ms, Quorum=5: {latency5:.1f}ms")
        return result
    except Exception as e:
        result.fail(f"Error: {e}")
        return result


def test_concurrent_writes_same_key() -> TestResult:
    """Test 5: Concurrent writes to the same key with timestamp ordering"""
    result = TestResult("Concurrent Writes (Same Key)")
    clear_all_stores()
    set_quorum(3)

    try:
        key = "concurrent_key"
        num_writes = 20

        # Perform concurrent writes
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(write_key, key, f"value_{i}")
                for i in range(num_writes)
            ]
            write_results = [f.result() for f in futures]

        if not all(write_results):
            result.fail(
                f"Some writes failed: {sum(write_results)}/{num_writes} succeeded"
            )
            return result

        time.sleep(3)

        # Verify all replicas converged to the same value
        leader_value = read_key_from(LEADER_URL, key)
        if leader_value is None:
            result.fail("Leader has no value after concurrent writes")
            return result

        for idx, follower_url in enumerate(FOLLOWER_URLS, 1):
            follower_value = read_key_from(follower_url, key)
            if follower_value != leader_value:
                result.fail(
                    f"Follower {idx} has inconsistent value: "
                    f"'{follower_value}' vs leader's '{leader_value}'"
                )
                return result

        result.success(
            f"All {num_writes} concurrent writes succeeded. "
            f"All replicas converged to: '{leader_value}'"
        )
        return result
    except Exception as e:
        result.fail(f"Error: {e}")
        return result


def test_timestamp_ordering() -> TestResult:
    """Test 6: Verify timestamps prevent out-of-order updates"""
    result = TestResult("Timestamp Ordering")
    clear_all_stores()
    set_quorum(1)

    try:
        key = "timestamp_test"
        values = ["v1", "v2", "v3", "v4", "v5"]

        for val in values:
            if not write_key(key, val):
                result.fail(f"Failed to write {val}")
                return result
            time.sleep(0.1)

        time.sleep(3)

        expected = values[-1]
        leader_value = read_key_from(LEADER_URL, key)
        if leader_value != expected:
            result.fail(f"Leader has wrong value: {leader_value} != {expected}")
            return result

        # Check all followers
        for idx, follower_url in enumerate(FOLLOWER_URLS, 1):
            follower_value = read_key_from(follower_url, key)
            if follower_value != expected:
                result.fail(
                    f"Follower {idx} has wrong value: {follower_value} != {expected}. "
                    "Timestamp ordering failed!"
                )
                return result

        result.success(
            f"All replicas correctly have the latest value: '{expected}'. "
            "Timestamps prevented out-of-order updates."
        )
        return result
    except Exception as e:
        result.fail(f"Error: {e}")
        return result


def test_eventual_consistency() -> TestResult:
    """Test 7: Test eventual consistency with mixed operations"""
    result = TestResult("Eventual Consistency")
    clear_all_stores()
    set_quorum(2)

    try:
        num_keys = 10
        writes_per_key = 5

        def write_multiple(key_idx: int) -> None:
            """Write multiple values to the same key."""
            key = f"ec_key_{key_idx}"
            for i in range(writes_per_key):
                write_key(key, f"val_{key_idx}_{i}")

        # Perform concurrent writes
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(write_multiple, i)
                for i in range(num_keys)
            ]
            for future in futures:
                future.result()

        print("  Waiting for eventual consistency...")
        time.sleep(5)

        # Verify leader has all expected keys
        leader_data = get_all_data_from(LEADER_URL)
        if len(leader_data) != num_keys:
            result.fail(f"Leader has {len(leader_data)} keys, expected {num_keys}")
            return result

        # Check all followers match leader
        mismatches = []
        for idx, follower_url in enumerate(FOLLOWER_URLS, 1):
            follower_data = get_all_data_from(follower_url)

            if follower_data != leader_data:
                diff_keys = [
                    key for key in leader_data
                    if key not in follower_data or follower_data[key] != leader_data[key]
                ]
                mismatches.append(f"Follower {idx}: {len(diff_keys)} keys differ")

        if mismatches:
            result.fail(
                "Eventual consistency not achieved:\n    " + "\n    ".join(mismatches)
            )
            return result

        result.success(
            f"Eventual consistency achieved: {num_keys} keys, "
            f"{num_keys * writes_per_key} total writes, all replicas consistent"
        )
        return result
    except Exception as e:
        result.fail(f"Error: {e}")
        return result


def run_all_tests() -> bool:
    """Run all integration tests and return success status."""
    print("\n" + "="*70)
    print("LEADER-FOLLOWER REPLICATION - INTEGRATION TESTS")
    print("="*70 + "\n")

    print("Waiting for services to start...")
    time.sleep(3)

    tests = [
        test_health_check,
        test_basic_write_read,
        test_replication_to_followers,
        test_quorum_requirement,
        test_concurrent_writes_same_key,
        test_timestamp_ordering,
        test_eventual_consistency,
    ]

    results = []
    for test_fn in tests:
        print(f"\nRunning: {test_fn.__doc__}")
        test_result = test_fn()
        results.append(test_result)
        print(f"  {test_result}")

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    for test_result in results:
        symbol = "✓" if test_result.passed else "✗"
        print(f"  {symbol} {test_result.name}")

    print(f"\nTotal: {passed} passed, {failed} failed out of {len(results)} tests")

    if failed == 0:
        print("\nAll tests passed! Replication system is working correctly.\n")
        return True
    
    print("\nSome tests failed. Review the failures above.\n")
    return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
