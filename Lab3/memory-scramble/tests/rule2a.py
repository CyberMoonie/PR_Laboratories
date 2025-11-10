#Flip first card, then flip empty space → error AND first card released
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from board import Board
@pytest.mark.asyncio
async def test_rule_2a():
    board_path = Path(__file__).parent.parent / 'boards' / 'ab.txt'
    board = await Board.parse_from_file(str(board_path))
    await board.flip('player1',0,0)  
    await board.flip('player1',0,2)  
    state = await board.flip('player1',0,1)  
    lines = state.split('\n')
    assert 'my B' in lines[2], 'Player controls the B card'
    with pytest.raises(ValueError):
        await board.flip('player1',0,0)  
    state = await board.flip('player1',0,3) 
    lines = state.split('\n')
    assert lines[2] == 'up B', 'First B card should be released (not controlled)'
    
