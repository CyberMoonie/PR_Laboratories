import pytest
import sys 
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))  
from board import Board
def test_create_board_invalid():
    with pytest.raises(ValueError):
        Board(-1, 2, ['A', 'A', 'B'])
        
    with pytest.raises(ValueError):
        Board(0, 2, ['A', 'A'])
    
    with pytest.raises(ValueError):
        Board(2, -1, ['A', 'B'])
        
    with pytest.raises(ValueError):
        Board(2, 0, ['A', 'A'])