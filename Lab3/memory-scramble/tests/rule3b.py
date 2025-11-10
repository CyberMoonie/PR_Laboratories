#After non-matching cards, new turn turns them face-down
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from board import Board
@pytest.mark.asyncio
async def test_rule_3b():
    board_path = Path(__file__).parent.parent / 'boards' / 'ab.txt'
    board = await Board.parse_from_file(str(board_path))
    state = await board.flip('player1',0,0)  
    state = await board.flip('player1',0,1)  
    state = await board.flip('player1',0,3)  
    lines = state.split('\n')
    assert lines[1] == 'down', '0,0 should be face-down after new turn'
    assert lines[2] == 'down', '0,1 should be face-down after new turn'
    assert 'my' in lines[4], 'New card at 0,3 should be controlled'