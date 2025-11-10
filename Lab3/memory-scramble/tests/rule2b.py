#Player1 holds card, Player2 tries to flip it as second card → error
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from board import Board
@pytest.mark.asyncio
async def test_rule_2b():
    board_path = Path(__file__).parent.parent / 'boards' / 'ab.txt'
    board = await Board.parse_from_file(str(board_path))
    await board.flip('player1',0,0) 
    await board.flip('player2',0,1)  
    with pytest.raises(ValueError):
        await board.flip('player2',0,0)
    