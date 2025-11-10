#"When a player flips a face-down card, it should:
#Turn face-up
#Give control to that player
#Show as 'my CARD' to that player"
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from board import Board
@pytest.mark.asyncio
async def test_rule_1b():
    # Load board from file
    board_path = Path(__file__).parent.parent / 'boards' / 'ab.txt'
    board = await Board.parse_from_file(str(board_path))
    state = await board.flip('player1', 0 , 0)
    lines = state.split('\n')
    assert 'my A' in lines[1] or 'my B' in lines[1], 'Player controls the card at position (0,0)'
    