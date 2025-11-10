#If the card is already face up, but not controlled by another player
#then it remains face up, and the player controls the card.
import pytest
import sys 
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from board import Board
@pytest.mark.asyncio
async def test_rule_1c():
    # Load board from file
    board_path = Path(__file__).parent.parent / 'boards' / 'ab.txt'
    board = await Board.parse_from_file(str(board_path))
    # Player1 flips two non-matching cards
    state = await board.flip('player1',0,0)
    state = await board.flip('player1',0,1)
    state = board.get_state('player1')
    lines = state.split('\n')
    # Both cards should be face-up but not controlled
    assert 'up' in lines[1] and 'my' not in lines[1], 'Card should be face-up, not controlled'
    assert 'up' in lines[2] and 'my' not in lines[2], 'Card should be face-up, not controlled'
    # Player2 takes control of face-up card
    state = await board.flip('player2',0,0)
    lines = state.split('\n')
    assert "my" in lines[1], 'player2 should take control of face-up card'