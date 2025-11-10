"""
This module provides the string-based commands that interface with the Board ADT.
These functions are called by the HTTP server and should only contain glue code.
"""

from typing import Callable
from board import Board


async def look(board: Board, player_id: str) -> str:
    """
    Look at the current state of the board.
    
    Args:
        board: A Memory Scramble board
        player_id: ID of player looking at the board; must be a nonempty string 
                   of alphanumeric or underscore characters
    
    Returns:
        The state of the board from the perspective of player_id, in the format
        described in the problem set handout
    
    Preconditions:
        - player_id matches [a-zA-Z0-9_]+
    
    Postconditions:
        - Returns board state string in format: ROWxCOLUMN\n(SPOT\n)+
        - Board state is unchanged
    """
    return board.get_state(player_id)


async def flip(board: Board, player_id: str, row: int, column: int) -> str:
    """
    Try to flip over a card on the board, following the game rules.
    
    If another player controls the card, this operation waits until the flip
    either becomes possible or fails.
    
    Args:
        board: A board
        player_id: ID of player making the flip
        row: Row number of card to flip
        column: Column number of card to flip
    
    Returns:
        The state of the board after the flip from the perspective of player_id,
    
    Raises:
        ValueError: If the flip operation fails as described in the game rules
    
    """
    return await board.flip(player_id, row, column)


async def map_command(board: Board, player_id: str, f: Callable[[str], str]) -> str:
    """
    Modify board by replacing every card with f(card), without affecting other game state.
    Args:
        board: Game board
        player_id: ID of player applying the map
        f: Mathematical function from cards to cards 
    
    Returns:
        The state of the board after the replacement from the perspective of player_id,
    """
    return await board.map_cards(player_id, f)


async def watch(board: Board, player_id: str) -> str:
    """
    Watch the board for a change, waiting until any cards change state.
    
    Waits until any cards turn face up or face down, are removed from the board,
    or change from one string to a different string.
    
    Args:
        board: A board
        player_id: ID of player watching the board
    
    Returns:
        The updated state of the board from the perspective of player_id, in the
        format described in the problem set handout
    """
    return await board.watch(player_id)
