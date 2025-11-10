#Flip two non-matching cards → both released but stay face-up
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from board import Board
@pytest.mark.asyncio
async def test_rule_2e():
    board_path = Path(__file__).parent.parent / 'boards' / 'ab.txt'
    board = await Board.parse_from_file(str(board_path))
    state = await board.flip('player1',0,0)  
    state = await board.flip('player1',0,1)  
    lines = state.split('\n')
    assert lines[1] == 'up A', 'First card (0,0) remains face-up without control'
    assert lines[2] == 'up B', 'Second card (0,1) remains face-up without control'
    
