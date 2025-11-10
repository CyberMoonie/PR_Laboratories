# Test concurrent access - multiple players making random moves simultaneously
# 4 players 100 moves each with tiny timemouts
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from board import Board
import asyncio
import random
@pytest.mark.asyncio
async def test_concurrent_players():
    board_path = Path(__file__).parent.parent / 'boards' / 'ab.txt'
    board = await Board.parse_from_file(str(board_path))
    results = {
        'player1': {'success': 0, 'failed': 0, 'errors': []},
        'player2': {'success': 0, 'failed': 0, 'errors': []},
        'player3': {'success': 0, 'failed': 0, 'errors': []},
        'player4': {'success': 0, 'failed': 0, 'errors': []},
    }
    
    async def make_random_moves(player_id: str, num_moves: int):
        """One player making random moves."""
        for i in range(num_moves):
            # Small random delay (0.1ms to 2ms)
            await asyncio.sleep(random.uniform(0.001, 0.002))
            # Pick random position
            row = random.randint(0, board.rows - 1)
            col = random.randint(0, board.cols - 1)
            
            try:
                state = await board.flip(player_id, row, col)
                results[player_id]['success'] += 1
            except ValueError as e:
                # Expected errors (no card, controlled, etc.) - this is OK!
                results[player_id]['failed'] += 1
            except Exception as e:
                # Unexpected errors - this is a BUG!
                error_msg = f"{type(e).__name__}: {e}"
                results[player_id]['errors'].append(error_msg)
    
    # Run all 4 players concurrently, each making 100 moves
    await asyncio.gather(
        make_random_moves('player1', 100),
        make_random_moves('player2', 100),
        make_random_moves('player3', 100),
        make_random_moves('player4', 100),
    )
    
    # Check results
    total_errors = sum(len(r['errors']) for r in results.values())
    total_moves = sum(r['success'] + r['failed'] for r in results.values())
    # Summary
    print(f"\nConcurrent test completed: {total_moves} total moves")
    for player_id, data in results.items():
        print(f"{player_id}: {data['success']} success, {data['failed']} failed, {len(data['errors'])} errors")
        if data['errors']:
            for error in data['errors'][:3]: 
                print(f"  - {error}")
    assert total_errors == 0, f"Found {total_errors} unexpected errors in concurrent test!"
    assert total_moves == 400, "Should have made 400 total moves (4 players × 100 moves)"
