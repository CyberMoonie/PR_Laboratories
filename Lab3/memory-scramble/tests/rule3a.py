#"When a player starts a new turn after matching cards
# the matched cards should be REMOVED from the board (show as 'none')"
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from board import Board
@pytest.mark.asyncio
async def test_rule_3a():
    board_path = Path(__file__).parent.parent / 'boards' / 'ab.txt'
    board = await Board.parse_from_file(str(board_path))
    state = await board.flip('player1',0,0)
    state = await board.flip('player1',0,2)
    state = await board.flip('player1',0,1)
    lines = state.split('\n')
    assert lines[1]=='none', 'card should be removed from 0,0'
    assert lines[3]=='none', 'card should be removed from 0,2'
    assert 'my B' in lines[2], 'player should control B at 0,1'