#"When a player flips a second card and it matches the first card, the player should keep control of BOTH cards"
import pytest
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / 'src'))
from board import Board
@pytest.mark.asyncio
async def test_rule_2d():
    board_path = pathlib.Path(__file__).parent.parent / 'boards' / 'ab.txt'
    board = await Board.parse_from_file(str(board_path))
    state = await board.flip('player1',0,0)
    state = await board.flip('player1',0,2)
    lines = state.split('\n')
    assert 'my A' in lines[1], 'Player should control first A at (0,0)'
    assert 'my A' in lines[3], 'Player should control second A at (0,2)'