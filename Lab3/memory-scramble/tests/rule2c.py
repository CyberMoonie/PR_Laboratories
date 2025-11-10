# Rule 2-C: Second card is face down → flip it up
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from board import Board
@pytest.mark.asyncio
async def test_rule_2c():
    board_path = Path(__file__).parent.parent / 'boards' / 'ab.txt'
    board = await Board.parse_from_file(str(board_path))
    state = await board.flip('player1', 0, 0)
    lines = state.split('\n')
    assert 'my' in lines[1], "First card should be controlled"
    state = await board.flip('player1', 0, 2)
    lines = state.split('\n')
    assert 'my' in lines[1], "First card should still be controlled"
    assert 'my' in lines[3], "Second card should now be face up and controlled"
