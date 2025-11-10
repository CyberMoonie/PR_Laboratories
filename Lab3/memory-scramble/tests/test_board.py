import pytest 
import sys 
from pathlib import Path 
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from board import Board

def test_create_board():
    rows = 2 
    cols = 2 
    cards = ['A', 'A', 'B', 'B']
    board = Board(rows,cols,cards)
    assert board.rows == rows
    assert board.cols == cols
    state = board.get_state("player1")
    lines = state.split("\n")
    assert lines[0] == "2x2"
    for i in range (1,5): 
        assert lines[i] == 'down', f"card {i-1} should be down"