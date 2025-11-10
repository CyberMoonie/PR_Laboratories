# No Card = Fails
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from board import Board
@pytest.mark.asyncio
async def test_rule_1a():
    board = Board(2,2,['A','A','B','B'])
    state = await board.flip('player1',0,0)
    state = await board.flip('player1',0,1)
    state = await board.flip('player1',0,0)
    lines = state.split('\n')
    assert 'ValueError' in lines[1], 'Flipping an already matched card should raise ValueError'