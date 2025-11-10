# Rule 1-D: Face up, controlled → wait for availability
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from board import Board
import asyncio
@pytest.mark.asyncio
async def test_rule_1d():
    board_path = Path(__file__).parent.parent / 'boards' / 'ab.txt'
    board = await Board.parse_from_file(str(board_path))
    await board.flip('player1', 0, 0) 
    async def player2_flip():
        state = await board.flip('player2', 0, 0)
        return state
    player2_task = asyncio.create_task(player2_flip())
    await asyncio.sleep(0.5)
    assert not player2_task.done(), "Player2 should be waiting for the card"
    await board.flip('player1', 0, 1)  
    await board.flip('player1', 0, 2)  
    await asyncio.sleep(0.5)
    state = await player2_task
    lines = state.split('\n')
    assert 'my' in lines[1], "Player2 should now control the card at (0,0)"
