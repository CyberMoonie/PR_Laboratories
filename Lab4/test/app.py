import os
import asyncio
import random
import time
from typing import Dict, Tuple, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# --- Configuration ---
ROLE = os.getenv("ROLE", "follower")
FOLLOWERS_LIST = [f for f in os.getenv("FOLLOWERS", "").split(",") if f]
MIN_DELAY = float(os.getenv("MIN_DELAY", "0.0001"))
MAX_DELAY = float(os.getenv("MAX_DELAY", "0.001"))
current_write_quorum = int(os.getenv("WRITE_QUORUM", "1"))

# --- Storage ---
# Store structure: {key: (value, timestamp)}
store: Dict[str, Tuple[str, float]] = {}

# --- Models ---
class WriteRequest(BaseModel):
    key: str
    value: str
    timestamp: Optional[float] = None


class ConfigRequest(BaseModel):
    quorum: int


# --- HTTP Client ---
client = httpx.AsyncClient()


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up HTTP client on shutdown."""
    await client.aclose()


# --- Common Endpoints ---
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "role": ROLE}


@app.get("/read/{key}")
async def read_key(key: str):
    """Read a single key from the store."""
    if key in store:
        value, timestamp = store[key]
        return {"key": key, "value": value, "timestamp": timestamp}
    raise HTTPException(status_code=404, detail="Key not found")


@app.get("/read_all")
async def read_all():
    """Read all keys from the store."""
    return {key: value for key, (value, _) in store.items()}


@app.delete("/clear")
async def clear_store():
    """Clear all data from the store."""
    store.clear()
    return {"status": "cleared", "role": ROLE}

# --- Follower Logic ---
if ROLE == "follower":
    @app.post("/replication")
    async def replicate(data: WriteRequest):
        """
        Receive replication data from leader.
        Only apply updates with newer timestamps to prevent stale data.
        """
        if data.key in store:
            _, current_timestamp = store[data.key]
            if data.timestamp > current_timestamp:
                store[data.key] = (data.value, data.timestamp)
                return {"status": "ack", "applied": True}
            return {"status": "ack", "applied": False, "reason": "stale_timestamp"}
        
        # New key - apply it
        store[data.key] = (data.value, data.timestamp)
        return {"status": "ack", "applied": True}

# --- Leader Logic ---
if ROLE == "leader":
    @app.post("/config")
    async def update_config(cfg: ConfigRequest):
        """Update the write quorum dynamically."""
        global current_write_quorum
        current_write_quorum = cfg.quorum
        return {"status": "updated", "quorum": current_write_quorum}

    async def send_replication(follower_url: str, data: WriteRequest) -> bool:
        """
        Send replication request to a follower with simulated network delay.
        Returns True if successful, False otherwise.
        """
        try:
            # Simulate network latency
            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            await asyncio.sleep(delay)

            # Send replication request
            response = await client.post(
                f"{follower_url}/replication",
                json=data.model_dump()
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to replicate to {follower_url}: {e}")
            return False

    @app.post("/write")
    async def write_key(data: WriteRequest):
        """
        Write key-value pair with quorum-based replication.
        Leader writes locally first, then replicates to followers.
        Returns success when required number of followers acknowledge.
        """
        # Generate timestamp if not provided
        if data.timestamp is None:
            data.timestamp = time.time()

        # Write locally first
        store[data.key] = (data.value, data.timestamp)

        # Handle case with no followers
        if not FOLLOWERS_LIST:
            return {"status": "written_local_only"}

        # Create replication tasks for all followers
        tasks = [send_replication(url, data) for url in FOLLOWERS_LIST]
        required_acks = current_write_quorum

        # If quorum is 0, fire and forget
        if required_acks == 0:
            asyncio.gather(*tasks)
            return {"status": "success", "quorum_met": True}

        # Wait for required number of acknowledgments
        successful_acks = 0
        for coro in asyncio.as_completed(tasks):
            success = await coro
            if success:
                successful_acks += 1
            
            if successful_acks >= required_acks:
                break

        # Check if quorum was met
        if successful_acks >= required_acks:
            return {"status": "success"}
        
        raise HTTPException(status_code=500, detail="Write quorum not met")
